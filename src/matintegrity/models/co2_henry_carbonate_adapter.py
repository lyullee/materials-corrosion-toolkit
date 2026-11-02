"""Digest-checked handoff from corrected CO2 Henry solubility to carbonate equilibrium."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from .co2_fixed_fugacity_equilibrium import (
    SOURCE_IDS as CARBONATE_SOURCE_IDS,
    Co2HenrySolubilityRecord,
    FixedFugacityCarbonateEquilibrium,
    fixed_fugacity_carbonate_equilibrium,
)
from .co2_henry_vant_hoff import (
    GAS_CONSTANT_SOURCE_ID as HENRY_GAS_CONSTANT_SOURCE_ID,
    METHOD_SOURCE_ID as HENRY_METHOD_SOURCE_ID,
    MODEL_ID as HENRY_CORRECTION_MODEL_ID,
    SOURCE_ID as HENRY_CORRECTION_SOURCE_ID,
    Co2HenryTemperatureCorrectionRequest,
)

MODEL_ID = "integration.co2_henry_temperature_to_fixed_fugacity_carbonate"
SOURCE_ID = "caller_reviewed_co2_henry_carbonate_handoff"
HENRY_PROVIDER_ID = "matintegrity.co2_henry_vant_hoff_temperature_correction"


class FixedFugacityCarbonateEquilibriumTemplate(FixedFugacityCarbonateEquilibrium):
    """Strict carbonate-equilibrium input with the Henry record supplied by this adapter."""

    henry: Co2HenrySolubilityRecord | None = None

    @model_validator(mode="after")
    def no_caller_henry_override(self):
        if self.henry is not None:
            raise ValueError("the adapter builds Henry data only from its digest-pinned correction result")
        return self


class Co2HenryCarbonateAdapterRequest(Contract):
    henry_temperature_correction_request: Co2HenryTemperatureCorrectionRequest
    henry_temperature_correction_result: AssessmentResult
    carbonate_equilibrium: FixedFugacityCarbonateEquilibriumTemplate
    corrected_henry_result_reviewed: bool
    adapter_review_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_no_temperature_or_composition_override(self):
        request = self.henry_temperature_correction_request
        equilibrium = self.carbonate_equilibrium
        if abs(equilibrium.temperature_K - request.target_temperature_K) > equilibrium.temperature_match_tolerance_K:
            raise ValueError("carbonate equilibrium temperature must match the corrected Henry temperature")
        if equilibrium.sample_solvent_composition_sha256 != request.sample_solvent_composition_sha256:
            raise ValueError("carbonate equilibrium and Henry correction must use the same solvent-composition digest")
        return self


def _upstream_result_problem(request: Co2HenryCarbonateAdapterRequest) -> str | None:
    result = request.henry_temperature_correction_result
    source_request = request.henry_temperature_correction_request
    if result.model_id != HENRY_CORRECTION_MODEL_ID:
        return "upstream_model_id_mismatch"
    if result.status != "computed":
        return "upstream_henry_correction_not_computed"
    expected_inputs = source_request.model_dump(mode="json")
    if result.inputs != expected_inputs:
        return "upstream_result_inputs_do_not_match_declared_request"
    expected_input_digest = canonical_digest(
        {
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": expected_inputs,
            "context": result.context.model_dump(mode="json"),
        }
    )
    if result.input_digest != expected_input_digest:
        return "upstream_assessment_input_digest_mismatch"
    values = result.values
    target = source_request.target_temperature_K
    coefficient = values.get("coefficient_mol_L_Pa")
    result_digest = values.get("result_digest")
    reference = source_request.reference
    if (
        values.get("model_id") != HENRY_CORRECTION_MODEL_ID
        or values.get("assessment_id") != source_request.assessment_id
        or values.get("target_temperature_K") != target
        or values.get("reference_record_sha256") != reference.record_sha256
        or values.get("solvent_composition_sha256") != source_request.sample_solvent_composition_sha256
        or values.get("provider_id") != reference.provider_id
        or values.get("provider_revision") != reference.provider_revision
        or values.get("provider_configuration_sha256") != reference.provider_configuration_sha256
        or values.get("coefficient_convention")
        != "aqueous_CO2star_concentration_over_gas_fugacity_mol_L_Pa"
        or result.units.get("coefficient_mol_L_Pa") != "mol/L/Pa"
        or not isinstance(coefficient, (int, float))
        or not math.isfinite(coefficient)
        or coefficient <= 0.0
        or not isinstance(result_digest, str)
        or len(result_digest) != 64
    ):
        return "upstream_corrected_henry_record_incomplete_or_inconsistent"
    expected_result_digest = canonical_digest(
        {
            "assessment_id": source_request.assessment_id,
            "target_temperature_K": target,
            "coefficient_mol_L_Pa": coefficient,
            "reference_record_sha256": reference.record_sha256,
            "model_id": HENRY_CORRECTION_MODEL_ID,
        }
    )
    if result_digest != expected_result_digest:
        return "upstream_henry_result_digest_mismatch"
    return None


def co2_henry_temperature_to_fixed_fugacity_carbonate(
    request: Co2HenryCarbonateAdapterRequest,
) -> Calculation:
    """Build a target-temperature Henry record and run the bounded carbonate solver."""
    problem = _upstream_result_problem(request)
    if problem:
        return Calculation(
            status="needs_data",
            values={
                "model_id": MODEL_ID,
                "reason": problem,
                "upstream_result_input_digest": request.henry_temperature_correction_result.input_digest,
            },
            notes=("A verified computed Henry-correction AssessmentResult is required.",),
        )
    if not request.corrected_henry_result_reviewed:
        return Calculation(
            status="needs_data",
            values={
                "model_id": MODEL_ID,
                "missing_reviews": ["corrected_henry_result_reviewed"],
                "adapter_review_id": request.adapter_review_id,
            },
            notes=("The caller must review the corrected coefficient and its source/temperature scope before use.",),
        )

    assessment = request.henry_temperature_correction_result
    correction = request.henry_temperature_correction_request
    values = assessment.values
    derived_evidence = Evidence(
        source_id=HENRY_PROVIDER_ID,
        origin="model_prediction",
        citation=(
            "Digest-pinned AssessmentResult from the caller-parameterized CO2 Henry temperature-correction API; "
            f"result digest {values['result_digest']}"
        ),
        sha256=values["result_digest"],
    )
    henry_evidence = tuple(correction.reference.evidence) + (derived_evidence,)
    henry = Co2HenrySolubilityRecord(
        temperature_K=correction.target_temperature_K,
        coefficient_mol_L_Pa=values["coefficient_mol_L_Pa"],
        convention="aqueous_CO2star_concentration_over_gas_fugacity",
        solvent_composition_sha256=correction.sample_solvent_composition_sha256,
        provider_id=HENRY_PROVIDER_ID,
        provider_revision=assessment.model_version,
        configuration_digest=assessment.input_digest,
        record_digest=values["result_digest"],
        evidence=henry_evidence,
    )
    payload = request.carbonate_equilibrium.model_dump(mode="python", exclude={"henry"})
    payload["henry"] = henry
    merged_evidence = [
        Evidence.model_validate(row) if isinstance(row, dict) else row for row in payload["evidence"]
    ]
    known_evidence = {(row.source_id, row.sha256) for row in merged_evidence}
    for evidence in henry_evidence:
        identity = (evidence.source_id, evidence.sha256)
        if identity not in known_evidence:
            merged_evidence.append(evidence)
            known_evidence.add(identity)
    payload["evidence"] = tuple(merged_evidence)
    equilibrium = FixedFugacityCarbonateEquilibrium.model_validate(payload)
    carbonate = fixed_fugacity_carbonate_equilibrium(equilibrium)
    output = dict(carbonate.values)
    output.update(
        {
            "model_id": MODEL_ID,
            "source_id": SOURCE_ID,
            "adapter_review_id": request.adapter_review_id,
            "henry_correction_model_id": HENRY_CORRECTION_MODEL_ID,
            "henry_correction_model_version": assessment.model_version,
            "henry_correction_input_digest": assessment.input_digest,
            "henry_correction_result_digest": values["result_digest"],
            "henry_temperature_factor": values["temperature_factor"],
            "henry_reference_record_sha256": correction.reference.record_sha256,
            "henry_corrected_record_sha256": henry.record_digest,
            "carbonate_equilibrium_input_digest": canonical_digest(equilibrium.model_dump(mode="json")),
            "full_aqueous_composition_solved": False,
            "carbonate_only_species_solved": True,
        }
    )
    return Calculation(
        status=carbonate.status,
        values=output,
        notes=carbonate.notes
        + (
            "The adapter forwards a digest-pinned, same-temperature and same-solvent Henry coefficient into the existing carbonate-only alkalinity solver.",
            "The result solves CO2*, bicarbonate and carbonate with the supplied carbonate constants and total-alkalinity constraint; it does not solve full aqueous composition, other ions, or charge-balanced reaction-network speciation.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            Co2HenryCarbonateAdapterRequest,
            co2_henry_temperature_to_fixed_fugacity_carbonate,
            {
                "temperature_K": "K",
                "co2_fugacity_Pa": "Pa",
                "henry_coefficient_mol_L_Pa": "mol/L/Pa",
                "ph_activity": "1",
                "co2star_mol_L": "mol/L",
                "hco3_mol_L": "mol/L",
                "co3_mol_L": "mol/L",
                "calculated_total_alkalinity_mol_L": "mol/L",
                "alkalinity_closure_residual_mol_L": "mol/L",
                "henry_temperature_factor": "1",
                "full_aqueous_composition_solved": "1",
                "carbonate_only_species_solved": "1",
            },
            (
                "A completed Henry-temperature AssessmentResult is reconstructed and verified against its exact request, input digest, unit, solvent, temperature and output digest before handoff.",
                "A derived Henry record uses the corrected coefficient in mol/L/Pa, the same solvent-composition digest and target temperature, and lineage to both source Evidence and the derived result digest.",
                "The downstream solver computes carbonate-only aqueous species and alkalinity closure; complete solution composition and arbitrary aqueous reaction-network speciation are not computed.",
                "No Henry data, thermochemistry, gas fugacity, alkalinity, equilibrium constants or activity parameters are inferred or bundled.",
            ),
            (
                SOURCE_ID,
                HENRY_CORRECTION_SOURCE_ID,
                HENRY_METHOD_SOURCE_ID,
                HENRY_GAS_CONSTANT_SOURCE_ID,
                *CARBONATE_SOURCE_IDS,
            ),
        )
    ]
