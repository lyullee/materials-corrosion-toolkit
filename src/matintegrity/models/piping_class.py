"""Caller-defined piping class compatibility without bundled specification tables."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..component_matching import material_membership_findings, required_attribute_findings
from ..contracts import Calculation, Contract, Nonnegative
from ..registry import ModelSpec
from .engineering_correlations import CorrelationRequest
from .mechanics import PressureTemperatureEnvelope, pressure_temperature_envelope


class PipingComponentRule(Contract):
    component_kind: str = Field(min_length=1)
    allowed_material_condition_ids: tuple[str, ...] = Field(min_length=1)
    minimum_corrosion_allowance_m: Nonnegative
    required_attributes: dict[str, str]

    @model_validator(mode="after")
    def exact_labels(self):
        labels = self.allowed_material_condition_ids
        if len(set(labels)) != len(labels) or any(not value.strip() for value in labels):
            raise ValueError("unique nonblank material-condition IDs required")
        if any(not key.strip() or not value.strip() for key, value in self.required_attributes.items()):
            raise ValueError("attribute keys and requirements must be nonblank")
        return self


class PipingComponentRecord(Contract):
    component_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    component_kind: str = Field(min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    corrosion_allowance_m: Nonnegative | None = None
    attributes: dict[str, str | None]


class PipingClassAssessment(CorrelationRequest):
    class_id: str = Field(min_length=1)
    class_revision: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    allowed_service_ids: tuple[str, ...] = Field(min_length=1)
    rating_label: str = Field(min_length=1)
    gauge_reference_id: str = Field(min_length=1)
    pressure_envelope: PressureTemperatureEnvelope
    component_rules: tuple[PipingComponentRule, ...] = Field(min_length=1)
    required_component_kinds: tuple[str, ...] = Field(min_length=1)
    components: tuple[PipingComponentRecord, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unambiguous_scope(self):
        for label, values in (
            ("service", self.allowed_service_ids),
            ("rule kind", tuple(row.component_kind for row in self.component_rules)),
            ("required kind", self.required_component_kinds),
            ("component", tuple(row.component_id for row in self.components)),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"unique nonblank {label} identifiers required")
        rules = {row.component_kind for row in self.component_rules}
        if not set(self.required_component_kinds) <= rules:
            raise ValueError("each required component kind needs a declared rule")
        if any(row.physical_scope_id != self.physical_scope_id for row in self.components):
            raise ValueError("every component must belong to the declared physical scope")
        return self


def piping_class_assessment(x: PipingClassAssessment) -> Calculation:
    if x.service_id not in x.allowed_service_ids:
        return Calculation(status="out_of_scope", values={"unsupported_service_id": x.service_id})
    pressure = pressure_temperature_envelope(x.pressure_envelope)
    if pressure.status != "computed":
        return Calculation(
            status=pressure.status, values={"pressure_envelope": pressure.model_dump(mode="json")}
        )
    rules = {row.component_kind: row for row in x.component_rules}
    findings = []
    for item in x.components:
        rule = rules.get(item.component_kind)
        missing, mismatches = [], []
        if rule is None:
            missing.append("component_kind_rule")
        else:
            missing, mismatches = material_membership_findings(
                item.material_condition_id, rule.allowed_material_condition_ids
            )
            if item.corrosion_allowance_m is None:
                missing.append("corrosion_allowance_m")
            elif item.corrosion_allowance_m < rule.minimum_corrosion_allowance_m:
                mismatches.append("corrosion_allowance_m")
            attribute_missing, attribute_mismatches = required_attribute_findings(
                item.attributes, rule.required_attributes
            )
            missing.extend(attribute_missing)
            mismatches.extend(attribute_mismatches)
        findings.append(
            dict(
                component_id=item.component_id,
                component_kind=item.component_kind,
                missing_fields=missing,
                mismatched_fields=mismatches,
                outcome="not_satisfied" if mismatches else "unknown" if missing else "satisfied",
            )
        )
    observed = {row.component_kind for row in x.components}
    missing_kinds = [kind for kind in x.required_component_kinds if kind not in observed]
    missing_data = bool(missing_kinds or any(row["missing_fields"] for row in findings))
    failed = not pressure.values["all_within_supplied_envelope"] or any(
        row["mismatched_fields"] for row in findings
    )
    outcome = "not_satisfied" if failed else "unknown" if missing_data else "satisfied"
    return Calculation(
        status="needs_data" if missing_data else "computed",
        values=dict(
            class_id=x.class_id,
            class_revision=x.class_revision,
            rating_label=x.rating_label,
            gauge_reference_id=x.gauge_reference_id,
            physical_scope_id=x.physical_scope_id,
            declared_class_outcome=outcome,
            missing_component_kinds=missing_kinds,
            component_findings=findings,
            pressure_envelope=pressure.model_dump(mode="json"),
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "All labels, materials, component requirements and pressure-temperature limits are caller supplied. Rating labels are never converted to pressure.",
            "Exact material-condition IDs do not establish designation equivalence, compatibility, strength, weld qualification or regulatory acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("piping-class asset and location must match run context")

    return [
        ModelSpec(
            "design.piping_class_assessment",
            PipingClassAssessment,
            piping_class_assessment,
            {
                "declared_class_outcome": "1",
                "component_findings": "structured_record",
                "pressure_envelope": "structured_record",
                "missing_component_kinds": "1",
                "class_id": "1",
                "class_revision": "1",
                "rating_label": "1",
                "gauge_reference_id": "1",
                "physical_scope_id": "1",
                "record_sha256": "1",
            },
            (
                "Caller-reviewed common gauge-pressure basis, piecewise-linear supported pressure-temperature envelope and exact component/material labels.",
            ),
            ("caller_piping_class_component_envelope_composition",),
            version="0.1.0",
            qualification="user_model",
            context_validator=same_identity,
        )
    ]
