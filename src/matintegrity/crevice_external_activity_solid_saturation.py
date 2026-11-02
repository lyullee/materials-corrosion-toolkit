"""Digest-bound solid saturation screens from cellwise external-activity crevice results."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_local_speciation_ledger import (
    CreviceLocalExternalActivityProjectionRequest,
    EXTERNAL_PROJECTION_MODEL_ID,
)
from .models.aqueous_saturation_screening import CandidateSolid, screen_mass_action_calculation
from .registry import ModelSpec

MODEL_ID = "integration.crevice_external_activity_local_solid_saturation"
SOURCE_ID = "caller_external_activity_crevice_cell_saturation_handoff"
MAX_CELLS = 200


def _sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


class CreviceExternalActivitySolidSaturationRequest(Contract):
    """Screen a chosen exact transport knot using exposed cell activity coefficients."""

    schema_version: Literal["matintegrity.crevice_external_activity_solid_saturation.v1"] = (
        "matintegrity.crevice_external_activity_solid_saturation.v1"
    )
    assessment_id: str = Field(min_length=1)
    projection_request: CreviceLocalExternalActivityProjectionRequest
    projection_result: dict
    projection_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knot_index: int = Field(ge=0)
    candidate_solids: tuple[CandidateSolid, ...] = Field(min_length=1, max_length=100)
    solubility_data_provider_id: str = Field(min_length=1)
    solubility_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    complete_species_inventory_reviewed: bool
    compatible_standard_states_reviewed: bool
    equilibrium_constants_temperature_reviewed: bool
    spatial_cell_mapping_and_candidate_support_reviewed: bool
    no_phase_selection_or_precipitation_inference_reviewed: bool

    @model_validator(mode="after")
    def bind_projection_and_candidate_set(self):
        if canonical_digest(self.projection_result) != self.projection_result_sha256:
            raise ValueError("external-activity projection result digest mismatch")
        result = self.projection_result
        values = result.get("values", {})
        if result.get("status") != "computed" or result.get("model_id") not in (
            None, EXTERNAL_PROJECTION_MODEL_ID
        ):
            raise ValueError("a computed external-activity projection result is required")
        if values.get("model_id") != EXTERNAL_PROJECTION_MODEL_ID:
            raise ValueError("upstream result is not the declared external-activity projection")
        if values.get("projection_input_sha256") != canonical_digest(
            self.projection_request.model_dump(mode="json")
        ):
            raise ValueError("projection result does not bind the supplied typed request")
        if values.get("transport_binding_result_sha256") != self.projection_request.transport_binding_result_sha256:
            raise ValueError("projection result and request refer to different transport bindings")
        knots = values.get("knots")
        if (
            not isinstance(knots, list)
            or len(knots) != len(self.projection_request.knots)
            or values.get("committed_knot_count") != len(knots)
            or self.knot_index >= len(knots)
        ):
            raise ValueError("selected exact knot is absent from the computed projection result")
        projection_knot = self.projection_request.knots[self.knot_index]
        result_knot = knots[self.knot_index]
        if (
            not isinstance(result_knot, dict)
            or result_knot.get("knot_summary_index") != self.knot_index
            or result_knot.get("time_s") != projection_knot.time_s
            or result_knot.get("geometry_side") != projection_knot.geometry_side
            or not isinstance(result_knot.get("cells"), list)
            or len(result_knot["cells"]) != len(projection_knot.cells)
        ):
            raise ValueError("selected projection knot/cell output differs from its typed exact-knot input")
        if len(projection_knot.cells) > MAX_CELLS:
            raise ValueError("one saturation request is limited to 200 cells")
        solid_ids = [row.solid_id for row in self.candidate_solids]
        if len(solid_ids) != len(set(solid_ids)):
            raise ValueError("candidate solid IDs must be unique")
        evidence_ids = [row.source_id for row in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Evidence source IDs must be unique")
        if {row.solubility_evidence_source_id for row in self.candidate_solids} - set(evidence_ids):
            raise ValueError("every candidate solid solubility source must be represented in Evidence")
        known_species = {row.species_id for row in projection_knot.cells[0].system_template.species}
        if any({term.species_id for term in solid.terms} - known_species for solid in self.candidate_solids):
            raise ValueError("candidate saturation terms must refer only to declared aqueous species")
        return self


def evaluate_crevice_external_activity_solid_saturation(
    request: CreviceExternalActivitySolidSaturationRequest,
) -> Calculation:
    """Apply the existing aqueous saturation screen independently to exact cells."""
    projection_request = request.projection_request
    projection_values = request.projection_result["values"]
    knot = projection_values["knots"][request.knot_index]
    projection_input_knot = projection_request.knots[request.knot_index]
    template = request.projection_request.activity_iteration_template
    expected_provider = {
        "provider_id": template.activity_provider_id,
        "provider_revision": template.activity_provider_revision,
        "configuration_sha256": template.activity_configuration_sha256,
        "parameter_record_sha256": template.activity_parameter_record_sha256,
    }
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "projection_model_id": EXTERNAL_PROJECTION_MODEL_ID,
        "projection_result_sha256": request.projection_result_sha256,
        "projection_input_sha256": projection_values["projection_input_sha256"],
        "transport_binding_result_sha256": projection_values["transport_binding_result_sha256"],
        "physical_scope_id": projection_request.transport_binding.campaign.physical_scope_id,
        "knot_index": request.knot_index,
        "time_s": knot["time_s"],
        "elapsed_time_s": knot["time_s"],
        "geometry_side": knot["geometry_side"],
        "solubility_data_provider_id": request.solubility_data_provider_id,
        "solubility_data_digest": request.solubility_data_digest,
        "candidate_solid_ids": [row.solid_id for row in request.candidate_solids],
        "phase_selection_performed": False,
        "precipitated_amount_predicted": False,
    }
    review_names = (
        "complete_species_inventory_reviewed",
        "compatible_standard_states_reviewed",
        "equilibrium_constants_temperature_reviewed",
        "spatial_cell_mapping_and_candidate_support_reviewed",
        "no_phase_selection_or_precipitation_inference_reviewed",
    )
    missing = [name for name in review_names if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "completed_cell_count": 0, "completed_cells": [],
        })

    species_ids = [row.species_id for row in projection_input_knot.cells[0].system_template.species]
    expected_contexts = projection_request.transport_binding_result["values"]["knot_summaries"][request.knot_index]
    committed: list[dict] = []
    common_temperature: float | None = None
    for input_cell, result_cell in zip(projection_input_knot.cells, knot["cells"], strict=True):
        cell_index = input_cell.cell_index
        if not isinstance(result_cell, dict) or result_cell.get("cell_index") != cell_index:
            return Calculation(status="out_of_scope", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "upstream exact cell order/identity does not match the typed projection input",
            })
        context_digest = canonical_digest({
            "knot_summary": expected_contexts,
            "cell_index": cell_index,
            "cell_volume_m3": expected_contexts["cell_volume_m3"][cell_index],
            "cell_concentration_mol_m3": [
                row[cell_index] for row in expected_contexts["cell_concentration_mol_m3"]
            ],
        })
        activity = result_cell.get("activity_coefficient_molarity_standard_state_by_species")
        concentrations = result_cell.get("species_concentration_mol_L")
        activity_iterations = result_cell.get("external_activity_fixed_point_iteration_count")
        activity_residual = result_cell.get("external_activity_fixed_point_residual_ln")
        provider_result_digest = result_cell.get("external_activity_provider_result_sha256")
        provider_transcript_digest = result_cell.get("external_activity_provider_transcript_sha256")
        if (
            result_cell.get("transport_cell_context_sha256") != context_digest
            or not isinstance(activity, dict) or set(activity) != set(species_ids)
            or not isinstance(concentrations, dict) or set(concentrations) != set(species_ids)
            or result_cell.get("activity_standard_state") != "molarity_1_mol_L"
            or isinstance(activity_iterations, bool) or not isinstance(activity_iterations, int)
            or activity_iterations < 1
            or not isinstance(activity_residual, (int, float)) or isinstance(activity_residual, bool)
            or not math.isfinite(activity_residual)
            or activity_residual > template.log_gamma_tolerance
            or not _sha256(provider_result_digest)
            or not _sha256(provider_transcript_digest)
        ):
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "cell activity state, converged fixed-point evidence, or transport context digest is incomplete",
            })
        if any(
            result_cell.get(key) != value
            for key, value in (
                ("activity_provider_id", expected_provider["provider_id"]),
                ("activity_provider_revision", expected_provider["provider_revision"]),
                ("activity_configuration_sha256", expected_provider["configuration_sha256"]),
                ("activity_parameter_record_sha256", expected_provider["parameter_record_sha256"]),
            )
        ):
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "cell activity-provider lineage differs from the reviewed provider template",
            })
        temperature = result_cell.get("temperature_K")
        if not isinstance(temperature, (int, float)) or isinstance(temperature, bool) or not math.isfinite(temperature):
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "cell temperature is missing or nonfinite",
            })
        if common_temperature is None:
            common_temperature = float(temperature)
        elif float(temperature) != common_temperature:
            return Calculation(status="out_of_scope", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "one shared candidate Ksp record set requires a common exact cell temperature",
            })
        species_rows = []
        try:
            for species_id in species_ids:
                concentration = float(concentrations[species_id])
                gamma = float(activity[species_id])
                dimensionless_activity = concentration * gamma
                if (
                    not math.isfinite(concentration) or concentration <= 0.0
                    or not math.isfinite(gamma) or gamma <= 0.0
                    or not math.isfinite(dimensionless_activity) or dimensionless_activity <= 0.0
                ):
                    raise ValueError("cell concentration/gamma does not define a positive finite activity")
                species_rows.append({
                    "species_id": species_id,
                    "concentration_mol_L": concentration,
                    "activity_coefficient": gamma,
                    "dimensionless_activity": dimensionless_activity,
                })
        except (TypeError, ValueError, OverflowError) as error:
            return Calculation(status="needs_data", values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": f"invalid cell activity state: {error}",
            })
        upstream_cell = Calculation(status="computed", values={
            "assessment_id": f"{request.assessment_id}:cell:{cell_index}",
            "solution_id": result_cell["solution_id"],
            "temperature_K": float(temperature),
            "activity_standard_state": "molarity_1_mol_L",
            "activity_provider_id": expected_provider["provider_id"],
            "activity_provider_revision": expected_provider["provider_revision"],
            "activity_record_digest": expected_provider["parameter_record_sha256"],
            "species": species_rows,
        })
        screened = screen_mass_action_calculation(
            upstream_cell,
            assessment_id=f"{request.assessment_id}:cell:{cell_index}",
            solution_id=result_cell["solution_id"],
            candidate_solids=request.candidate_solids,
            solubility_data_provider_id=request.solubility_data_provider_id,
            solubility_data_digest=request.solubility_data_digest,
            complete_species_inventory_reviewed=request.complete_species_inventory_reviewed,
            compatible_standard_states_reviewed=request.compatible_standard_states_reviewed,
            equilibrium_constants_temperature_reviewed=request.equilibrium_constants_temperature_reviewed,
            evidence=request.evidence,
        )
        if screened.status != "computed":
            return Calculation(status=screened.status, values=base | {
                "completed_cell_count": len(committed), "completed_cells": committed,
                "failed_cell_index": cell_index,
                "failure_reason": "existing aqueous saturation screen did not compute this cell",
                "upstream_status": screened.status,
                "upstream_values": screened.values,
            })
        committed.append({
            "cell_index": cell_index,
            "transport_cell_context_sha256": context_digest,
            "activity_state_digest": canonical_digest({
                "projection_result_sha256": request.projection_result_sha256,
                "activity_configuration_sha256": expected_provider["configuration_sha256"],
                "activity_parameter_record_sha256": expected_provider["parameter_record_sha256"],
                "provider_transcript_sha256": result_cell.get("external_activity_provider_transcript_sha256"),
            }),
            "activity_provider_result_sha256": result_cell.get("external_activity_provider_result_sha256"),
            "activity_transcript_sha256": result_cell.get("external_activity_provider_transcript_sha256"),
            "temperature_K": float(temperature),
            "saturation_result_sha256": canonical_digest(screened.model_dump(mode="json")),
            "candidate_results": screened.values.get("candidate_results", []),
        })
    return Calculation(values=base | {
        "status": "computed",
        "temperature_K": common_temperature,
        "activity_standard_state": "molarity_1_mol_L",
        "completed_cell_count": len(committed),
        "completed_cells": committed,
        "phase_selection_performed": False,
        "precipitated_amount_predicted": False,
        "interpretation_boundary": "Existing candidate-solid saturation screening is applied independently to each exact cell from the external-activity projection. No phase selection, precipitation extent, spatial mixing, nucleation, kinetics, geometry change or corrosion rate is inferred.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceExternalActivitySolidSaturationRequest,
        evaluator=evaluate_crevice_external_activity_solid_saturation,
        units={
            "time_s": "s",
            "elapsed_time_s": "s",
            "temperature_K": "K",
            "completed_cells[].candidate_results[].log10_saturation_ratio": "1",
            "completed_cells[].candidate_results[].log10_saturation_absolute_bound": "1",
            "completed_cells[].candidate_results[].log10_saturation_ratio_lower_bound": "1",
            "completed_cells[].candidate_results[].log10_saturation_ratio_upper_bound": "1",
        },
        assumptions=(
            "The computed external-activity projection result must match its typed input, transport binding, exact knot and all cell context digests.",
            "Cell dimensionless activities are formed as gamma at the molarity 1 mol/L standard state times concentration in mol/L.",
            "The caller supplies a complete candidate-solid list, Ksp records, compatible temperature/standard state, Evidence and all review decisions.",
            "The existing aqueous saturation calculation is evaluated independently per cell; saturation is not phase selection, precipitation amount, kinetics, wall deposition, corrosion rate or qualification.",
        ),
        source_ids=(SOURCE_ID, "caller_crevice_cell_local_candidate_saturation_screen",
                    "caller_external_aqueous_activity_provider"),
        qualification="user_model",
    )]
