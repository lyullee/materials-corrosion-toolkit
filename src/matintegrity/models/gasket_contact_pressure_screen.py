"""Caller-declared gasket contact-pressure margin screening."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, canonical_digest
from ..registry import ModelSpec


_STATIC_CONTACT_MODELS = {
    "fabrication.flange_contact_field",
    "fabrication.flange_nonlinear_contact_field",
}
_HISTORY_CONTACT_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactPressureScreen(Contract):
    """Compare a computed contact-pressure field to a caller-defined screening window."""

    schema_version: Literal["matintegrity.gasket_contact_pressure_screen.v1"] = (
        "matintegrity.gasket_contact_pressure_screen.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_result: AssessmentResult
    contact_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_time_s: Nonnegative | None = None
    node_ids: tuple[str, ...] | None = Field(default=None, min_length=1, max_length=100000)
    minimum_contact_pressure_Pa: Nonnegative
    maximum_contact_pressure_Pa: Nonnegative | None = None
    criterion_provider_id: str = Field(min_length=1)
    criterion_provider_revision: str = Field(min_length=1)
    criterion_record_id: str = Field(min_length=1)
    criterion_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    criterion_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    physical_scope_and_load_basis_reviewed: bool
    criterion_applicability_reviewed: bool
    pressure_basis_and_units_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_screening_request(self):
        result = self.contact_result
        if canonical_digest(result.model_dump(mode="json")) != self.contact_result_sha256:
            raise ValueError("contact result digest does not match the supplied AssessmentResult")
        if result.status != "computed":
            raise ValueError("only a computed contact AssessmentResult can be screened")
        if result.context.asset_id != self.asset_id or result.context.location_id != self.location_id:
            raise ValueError("contact result asset/location does not match this screening scope")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("contact result physical scope does not match this screening scope")
        if result.model_id in _STATIC_CONTACT_MODELS and self.selected_time_s is not None:
            raise ValueError("static contact fields do not accept a selected time")
        if result.model_id in _HISTORY_CONTACT_MODELS and self.selected_time_s is None:
            raise ValueError("contact histories require an exact selected output time")
        if result.model_id not in _STATIC_CONTACT_MODELS | _HISTORY_CONTACT_MODELS:
            raise ValueError("unsupported upstream model; an explicit pressure-field adapter is required")
        if self.maximum_contact_pressure_Pa is not None and self.maximum_contact_pressure_Pa < self.minimum_contact_pressure_Pa:
            raise ValueError("caller pressure window maximum must not be below its minimum")
        criterion_basis = {
            "criterion_provider_id": self.criterion_provider_id,
            "criterion_provider_revision": self.criterion_provider_revision,
            "criterion_record_id": self.criterion_record_id,
            "physical_scope_id": self.physical_scope_id,
            "minimum_contact_pressure_Pa": self.minimum_contact_pressure_Pa,
            "maximum_contact_pressure_Pa": self.maximum_contact_pressure_Pa,
        }
        if canonical_digest(criterion_basis) != self.criterion_sha256:
            raise ValueError("criterion digest does not match its declared scope and pressure bounds")
        if not any(
            evidence.source_id == self.criterion_provider_id and evidence.sha256 == self.criterion_sha256
            for evidence in self.criterion_evidence
        ):
            raise ValueError("criterion provider and digest must match the same Evidence record")
        if not any(evidence.license_id == self.usage_license_id for evidence in self.usage_rights_evidence):
            raise ValueError("rights Evidence must identify the declared usage license")
        if self.node_ids is not None and len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("selected node IDs must be unique")
        return self


def screen_gasket_contact_pressure(request: GasketContactPressureScreen) -> Calculation:
    """Return margins against caller limits; no seal pass/fail or qualification is inferred."""
    result = request.contact_result
    values = result.values
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "contact_result_model_id": result.model_id,
        "contact_result_sha256": request.contact_result_sha256,
        "contact_result_input_digest": result.input_digest,
        "contact_result_source_ids": list(result.source_ids),
        "selected_time_s": request.selected_time_s,
        "criterion_provider_id": request.criterion_provider_id,
        "criterion_provider_revision": request.criterion_provider_revision,
        "criterion_record_id": request.criterion_record_id,
        "criterion_sha256": request.criterion_sha256,
        "usage_license_id": request.usage_license_id,
        "screening_semantics": "caller_declared_contact_pressure_window_margin_only",
        "seal_acceptance_or_qualification_claim": False,
    }
    required_reviews = (
        request.physical_scope_and_load_basis_reviewed,
        request.criterion_applicability_reviewed,
        request.pressure_basis_and_units_reviewed,
        request.usage_rights_reviewed,
        request.computational_use_authorized,
    )
    if not all(required_reviews):
        return Calculation(status="needs_data", values=base | {"required_reviews_complete": False})

    unit_key = (
        "response_field.mean_contact_pressure_Pa"
        if result.model_id in _STATIC_CONTACT_MODELS
        else "time_history[].response_field[].mean_contact_pressure_Pa"
    )
    if result.units.get(unit_key) != "Pa":
        return Calculation(status="out_of_scope", values=base | {
            "reason": "upstream_contact_pressure_unit_is_not_explicitly_pascal",
            "expected_unit_key": unit_key,
            "declared_unit": result.units.get(unit_key),
        })

    if result.model_id in _STATIC_CONTACT_MODELS:
        field = values.get("response_field")
    else:
        history = values.get("time_history")
        if not isinstance(history, list):
            return Calculation(status="out_of_scope", values=base | {"reason": "upstream_contact_history_missing"})
        selected = next((row for row in history if row.get("time_s") == request.selected_time_s), None)
        if selected is None:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "selected_time_is_not_an_exact_computed_output_knot",
                "available_time_s": [row.get("time_s") for row in history],
            })
        field = selected.get("response_field")
    if not isinstance(field, list) or not field:
        return Calculation(status="out_of_scope", values=base | {"reason": "upstream_contact_field_missing_or_empty"})

    selected_ids = set(request.node_ids) if request.node_ids is not None else None
    observed_ids: set[str] = set()
    rows = []
    for row in field:
        if not isinstance(row, dict) or not isinstance(row.get("node_id"), str):
            return Calculation(status="out_of_scope", values=base | {"reason": "upstream_contact_node_record_is_malformed"})
        node_id = row["node_id"]
        if selected_ids is not None and node_id not in selected_ids:
            continue
        if node_id in observed_ids:
            return Calculation(status="out_of_scope", values=base | {"reason": "duplicate_upstream_node_id", "node_id": node_id})
        observed_ids.add(node_id)
        pressure = row.get("mean_contact_pressure_Pa")
        if isinstance(pressure, bool) or not isinstance(pressure, (int, float)) or pressure < 0:
            return Calculation(status="out_of_scope", values=base | {"reason": "invalid_contact_pressure", "node_id": node_id})
        entry = {
            "node_id": node_id,
            "mean_contact_pressure_Pa": float(pressure),
            "minimum_pressure_margin_Pa": float(pressure - request.minimum_contact_pressure_Pa),
        }
        if request.maximum_contact_pressure_Pa is not None:
            entry["maximum_pressure_margin_Pa"] = float(request.maximum_contact_pressure_Pa - pressure)
            entry["controlling_margin_Pa"] = min(entry["minimum_pressure_margin_Pa"], entry["maximum_pressure_margin_Pa"])
        else:
            entry["controlling_margin_Pa"] = entry["minimum_pressure_margin_Pa"]
        rows.append(entry)

    if selected_ids is not None and observed_ids != selected_ids:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "requested_node_set_does_not_match_upstream_field",
            "missing_node_ids": sorted(selected_ids - observed_ids),
        })
    if not rows:
        return Calculation(status="out_of_scope", values=base | {"reason": "no_nodes_selected_from_upstream_field"})

    controlling = min(rows, key=lambda row: row["controlling_margin_Pa"])
    return Calculation(values=base | {
        "minimum_contact_pressure_Pa": request.minimum_contact_pressure_Pa,
        "maximum_contact_pressure_Pa": request.maximum_contact_pressure_Pa,
        "node_count": len(rows),
        "node_margins": rows,
        "minimum_controlling_margin_Pa": controlling["controlling_margin_Pa"],
        "controlling_node_id": controlling["node_id"],
        "criterion_outcome": "within_declared_screening_window" if controlling["controlling_margin_Pa"] >= 0 else "outside_declared_screening_window",
        "criterion_outcome_is_engineering_acceptance": False,
    }, notes=(
        "Pressure margins compare an upstream calculated contact-pressure field to caller-declared bounds only.",
        "The result is not a gasket leak prediction, sealing acceptance criterion, code check, probability, or material qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_contact_pressure_screen",
        GasketContactPressureScreen,
        screen_gasket_contact_pressure,
        {
            "minimum_contact_pressure_Pa": "Pa",
            "maximum_contact_pressure_Pa": "Pa",
            "node_margins[].mean_contact_pressure_Pa": "Pa",
            "node_margins[].minimum_pressure_margin_Pa": "Pa",
            "node_margins[].maximum_pressure_margin_Pa": "Pa",
            "node_margins[].controlling_margin_Pa": "Pa",
            "minimum_controlling_margin_Pa": "Pa",
        },
        (
            "Compare a digest-pinned upstream gasket contact-pressure field with a caller-declared screening window at an exact declared output knot.",
            "This is a pressure-margin screen only; no seal criterion, acceptance, leakage or qualification is inferred.",
        ),
        ("caller_gasket_contact_pressure_screen_window",),
        qualification="user_model",
    )]
