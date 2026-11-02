"""Bind exact fixed-fugacity carbonate states to a caller scale law through activity/Ksp data."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from .models.aqueous_saturation_screening import (
    AqueousSaturationScreen,
    CandidateSolid,
    SaturationScreenSpecies,
    SaturationScreenTerm,
    aqueous_saturation_screen,
)
from .models.surface_scale_kinetics import (
    CallerSurfaceScaleKinetics,
    caller_surface_scale_kinetics,
)
from .registry import ModelSpec


class CarbonateActivityCoefficientRecord(Contract):
    """Caller activity coefficient for one carbonate species at one exact knot."""

    value: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def record_is_evidenced(self):
        if not any(row.source_id == self.record_id and row.sha256 == self.sha256 for row in self.evidence):
            raise ValueError("activity-coefficient record ID and digest must match Evidence")
        return self


class CallerSpeciesActivityRecord(Contract):
    """Explicit dimensionless activity for a non-carbonate species at one knot."""

    species_id: str = Field(min_length=1)
    dimensionless_activity: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def record_is_evidenced(self):
        if not any(row.source_id == self.record_id and row.sha256 == self.sha256 for row in self.evidence):
            raise ValueError("aqueous species-activity record ID and digest must match Evidence")
        return self


class CarbonateKspKnotRecord(Contract):
    """Caller-supplied temperature-supported solubility product at one source knot."""

    log10_solubility_product: float
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_support_min_K: Positive
    temperature_support_max_K: Positive
    temperature_applicability_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        if not math.isfinite(self.log10_solubility_product):
            raise ValueError("log10 solubility product must be finite")
        if self.temperature_support_max_K < self.temperature_support_min_K:
            raise ValueError("solubility-product temperature support is reversed")
        if not any(row.source_id == self.record_id and row.sha256 == self.sha256 for row in self.evidence):
            raise ValueError("solubility-product record ID and digest must match Evidence")
        return self


class FixedFugacityCarbonateScaleKnot(Contract):
    """Supporting caller activity and Ksp records aligned to one exact carbonate knot."""

    time_s: float = Field(ge=0, allow_inf_nan=False)
    carbonate_activity_coefficient: CarbonateActivityCoefficientRecord
    other_species_activities: tuple[CallerSpeciesActivityRecord, ...] = Field(min_length=1, max_length=100)
    solubility_product: CarbonateKspKnotRecord

    @model_validator(mode="after")
    def unique_auxiliary_species(self):
        ids = [row.species_id for row in self.other_species_activities]
        if len(set(ids)) != len(ids):
            raise ValueError("auxiliary aqueous activity species IDs must be unique")
        return self


class FixedFugacityCarbonateScaleKinetics(Contract):
    """Evaluate a caller scale law using exact carbonate-history saturation screens."""

    schema_version: Literal["matintegrity.fixed_fugacity_carbonate_scale_kinetics.v1"] = (
        "matintegrity.fixed_fugacity_carbonate_scale_kinetics.v1"
    )
    assessment_id: str = Field(min_length=1)
    fixed_fugacity_carbonate_history: AssessmentResult
    fixed_fugacity_carbonate_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    carbonate_species_id: str = Field(min_length=1)
    selected_solid_id: str = Field(min_length=1)
    scale_phase_mapping_reviewed: bool
    solid_terms: tuple[SaturationScreenTerm, ...] = Field(min_length=1, max_length=100)
    knots: tuple[FixedFugacityCarbonateScaleKnot, ...] = Field(min_length=2, max_length=100000)
    carbonate_activity_and_standard_state_reviewed: bool
    complete_knot_species_inventory_reviewed: bool
    solubility_temperature_support_reviewed: bool
    saturation_path_interpolation_reviewed: bool
    caller_kinetic_law_scope_and_coefficients_reviewed: bool
    computational_use_authorized: bool
    kinetics_template: CallerSurfaceScaleKinetics

    @model_validator(mode="after")
    def exact_history_alignment(self):
        result = self.fixed_fugacity_carbonate_history
        if result.model_id != "chemistry.fixed_fugacity_carbonate_history" or result.status != "computed":
            raise ValueError("a computed fixed-fugacity carbonate-history AssessmentResult is required")
        if canonical_digest(result.model_dump(mode="json")) != self.fixed_fugacity_carbonate_history_sha256:
            raise ValueError("carbonate history result digest does not match")
        if result.values.get("input_sha256") != canonical_digest(result.inputs):
            raise ValueError("carbonate history source input digest does not match its request")
        if result.input_digest != canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        }):
            raise ValueError("carbonate history registry input digest does not match")
        values = result.values
        times = values.get("time_s")
        temperatures = values.get("temperature_K_history")
        carbonate = values.get("co3_mol_L_history")
        if not all(isinstance(rows, list) and len(rows) == len(self.knots) for rows in (times, temperatures, carbonate)):
            raise ValueError("carbonate history time, temperature and CO3 arrays must align with caller activity/Ksp knots")
        if values.get("all_points_computed") is not True or values.get("chemistry_interpolation_performed") is not False:
            raise ValueError("only complete non-interpolated carbonate histories are supported")
        if any(not isinstance(t, (int, float)) or not math.isfinite(t) for t in times) or any(
            right <= left for left, right in zip(times, times[1:])
        ):
            raise ValueError("carbonate time knots must be finite and strictly increasing")
        if len(self.knots) != len(self.kinetics_template.intervals) + 1:
            raise ValueError("one activity/Ksp input knot is required at each scale-kinetic interval endpoint")
        for index, knot in enumerate(self.knots):
            if knot.time_s != times[index]:
                raise ValueError("caller activity/Ksp knot time must exactly match the carbonate history")
            temperature = temperatures[index]
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature):
                raise ValueError("carbonate temperatures must be finite at every exact knot")
            support = knot.solubility_product
            if not support.temperature_support_min_K <= temperature <= support.temperature_support_max_K:
                raise ValueError("each caller Ksp record must support its exact carbonate-history temperature")
        if len({term.species_id for term in self.solid_terms}) != len(self.solid_terms):
            raise ValueError("solid activity terms must use unique species IDs")
        if self.kinetics_template.scale_phase_id != self.selected_solid_id:
            raise ValueError("selected saturation solid and caller scale phase IDs must match exactly")
        if self.kinetics_template.physical_scope_id != values.get("physical_scope_id"):
            raise ValueError("caller scale kinetics physical scope must match the carbonate-history result")
        if not self.kinetics_template.linearly_varying_saturation_reviewed:
            raise ValueError("carbonate saturation path requires reviewed piecewise-linear interval interpretation")
        for index, interval in enumerate(self.kinetics_template.intervals):
            if interval.start_time_s != times[index] or interval.end_time_s != times[index + 1]:
                raise ValueError("caller kinetic intervals must match adjacent exact carbonate history knots")
            if interval.temperature_K != temperatures[index]:
                raise ValueError("caller kinetic interval temperature must equal its exact left carbonate-history knot")
        return self


def _merge_evidence(rows: tuple[Evidence, ...]) -> tuple[Evidence, ...]:
    by_id: dict[str, Evidence] = {}
    for row in rows:
        previous = by_id.get(row.source_id)
        if previous is not None and previous != row:
            raise ValueError("the same source ID has conflicting Evidence records within one knot")
        by_id[row.source_id] = row
    return tuple(by_id[key] for key in sorted(by_id))


def _carbonate_context(request: FixedFugacityCarbonateScaleKinetics, context: RunContext) -> None:
    upstream = request.fixed_fugacity_carbonate_history.context
    for field in ("asset_id", "location_id", "time_basis"):
        if getattr(context, field) != getattr(upstream, field):
            raise ValueError(f"outer RunContext {field} must match the carbonate-history assessment")


def evaluate_fixed_fugacity_carbonate_scale_kinetics(
    request: FixedFugacityCarbonateScaleKinetics,
) -> Calculation:
    """Screen exact carbonate knots for one caller solid, then run its empirical scale law."""
    result = request.fixed_fugacity_carbonate_history
    source_digest = request.fixed_fugacity_carbonate_history_sha256
    values = result.values
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "carbonate_history_result_sha256": source_digest,
        "carbonate_history_input_sha256": values["input_sha256"],
        "physical_scope_id": values.get("physical_scope_id"),
        "solution_id": values.get("history_id"),
        "asset_id": result.context.asset_id,
        "location_id": result.context.location_id,
        "time_basis": result.context.time_basis,
        "carbonate_species_id": request.carbonate_species_id,
        "selected_solid_id": request.selected_solid_id,
        "input_sha256": input_digest,
    }
    reviews = {
        "scale_phase_mapping_reviewed": request.scale_phase_mapping_reviewed,
        "carbonate_activity_and_standard_state_reviewed": request.carbonate_activity_and_standard_state_reviewed,
        "complete_knot_species_inventory_reviewed": request.complete_knot_species_inventory_reviewed,
        "solubility_temperature_support_reviewed": request.solubility_temperature_support_reviewed,
        "saturation_path_interpolation_reviewed": request.saturation_path_interpolation_reviewed,
        "caller_kinetic_law_scope_and_coefficients_reviewed": request.caller_kinetic_law_scope_and_coefficients_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, reviewed in reviews.items() if not reviewed]
    missing_ksp_temperature_reviews = [
        {
            "knot_index": index,
            "time_s": knot.time_s,
            "solubility_record_id": knot.solubility_product.record_id,
            "solubility_record_sha256": knot.solubility_product.sha256,
        }
        for index, knot in enumerate(request.knots)
        if not knot.solubility_product.temperature_applicability_reviewed
    ]
    if missing or missing_ksp_temperature_reviews:
        return Calculation(status="needs_data", values=base | {
            "completed_saturation_knot_count": 0,
            "saturation_knot_results": [],
            "missing_reviews": missing,
            "missing_ksp_temperature_applicability_reviews": missing_ksp_temperature_reviews,
        })

    saturation_rows = []
    ratios = []
    for index, knot in enumerate(request.knots):
        temperature = values["temperature_K_history"][index]
        co3 = values["co3_mol_L_history"][index]
        gamma = knot.carbonate_activity_coefficient.value
        carbonate_activity = co3 * gamma
        if not math.isfinite(carbonate_activity) or carbonate_activity <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "unsupported_knot_index": index,
                "unsupported_knot_time_s": knot.time_s,
                "reason": "carbonate_activity_is_zero_or_outside_positive_finite_screen_support",
            })
        species_ids = [request.carbonate_species_id, *(row.species_id for row in knot.other_species_activities)]
        if len(species_ids) != len(set(species_ids)):
            return Calculation(status="needs_data", values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "unsupported_knot_index": index,
                "reason": "caller_species_activity_duplicates_carbonate_species_id",
            })
        evidence = _merge_evidence((
            *knot.carbonate_activity_coefficient.evidence,
            *(item for row in knot.other_species_activities for item in row.evidence),
            *knot.solubility_product.evidence,
        ))
        activity_state = {
            "carbonate_species_id": request.carbonate_species_id,
            "carbonate_concentration_mol_L": co3,
            "carbonate_activity_coefficient": gamma,
            "carbonate_dimensionless_activity": carbonate_activity,
            "other_species_activities": [row.model_dump(mode="json") for row in knot.other_species_activities],
            "activity_evidence": [row.model_dump(mode="json") for row in evidence],
            "temperature_K": temperature,
        }
        screen = AqueousSaturationScreen(
            assessment_id=f"{request.assessment_id}:knot:{index}",
            solution_id=str(values["history_id"]),
            temperature_K=temperature,
            activity_standard_state="molarity_1_mol_L",
            species=(
                SaturationScreenSpecies(
                    species_id=request.carbonate_species_id,
                    dimensionless_activity=carbonate_activity,
                ),
                *(SaturationScreenSpecies(
                    species_id=row.species_id,
                    dimensionless_activity=row.dimensionless_activity,
                ) for row in knot.other_species_activities),
            ),
            candidate_solids=(CandidateSolid(
                solid_id=request.selected_solid_id,
                log10_solubility_product=knot.solubility_product.log10_solubility_product,
                solubility_record_id=knot.solubility_product.record_id,
                solubility_evidence_source_id=knot.solubility_product.record_id,
                terms=request.solid_terms,
            ),),
            activity_state_provider_id="caller_composed_fixed_fugacity_carbonate_and_auxiliary_species",
            activity_state_digest=canonical_digest(activity_state),
            solubility_data_provider_id=knot.solubility_product.provider_id,
            solubility_data_digest=knot.solubility_product.sha256,
            complete_species_inventory_reviewed=True,
            compatible_standard_states_reviewed=True,
            equilibrium_constants_temperature_reviewed=True,
            evidence=evidence,
        )
        calculation = aqueous_saturation_screen(screen)
        calc_digest = canonical_digest(calculation.model_dump(mode="json"))
        row = {
            "index": index,
            "time_s": knot.time_s,
            "temperature_K": temperature,
            "carbonate_concentration_mol_L": co3,
            "carbonate_activity_coefficient": gamma,
            "carbonate_dimensionless_activity": carbonate_activity,
            "activity_coefficient_record_id": knot.carbonate_activity_coefficient.record_id,
            "activity_coefficient_record_sha256": knot.carbonate_activity_coefficient.sha256,
            "solubility_record_id": knot.solubility_product.record_id,
            "solubility_record_sha256": knot.solubility_product.sha256,
            "saturation_screen_input_sha256": canonical_digest(screen.model_dump(mode="json")),
            "saturation_screen_result_sha256": calc_digest,
            "saturation_screen_result": calculation.model_dump(mode="json"),
            "status": calculation.status,
        }
        if calculation.status != "computed":
            return Calculation(status=calculation.status, values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "first_incomplete_knot": row,
                "scale_kinetics_result": None,
            }, notes=("Scale kinetics are withheld unless every exact carbonate-history knot produces one computed selected-solid saturation screen.",))
        candidate_rows = calculation.values.get("candidate_results")
        if not isinstance(candidate_rows, list) or len(candidate_rows) != 1:
            return Calculation(status="out_of_scope", values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "first_incomplete_knot": row,
                "reason": "saturation_screen_did_not_return_exactly_one_selected_solid",
            })
        log_ratio = candidate_rows[0].get("log10_saturation_ratio")
        if isinstance(log_ratio, bool) or not isinstance(log_ratio, (int, float)) or not math.isfinite(log_ratio) or not -300.0 <= log_ratio <= 300.0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "first_incomplete_knot": row,
                "reason": "saturation_ratio_outside_finite_scale_kinetics_support",
            })
        ratio = 10.0 ** log_ratio
        if not math.isfinite(ratio) or ratio <= 0:
            return Calculation(status="out_of_scope", values=base | {
                "completed_saturation_knot_count": len(saturation_rows),
                "completed_saturation_knots": saturation_rows,
                "first_incomplete_knot": row,
                "reason": "saturation_ratio_not_representable_as_positive_finite_value",
            })
        row["log10_saturation_ratio"] = log_ratio
        row["saturation_ratio"] = ratio
        saturation_rows.append(row)
        ratios.append(ratio)

    kinetics_data = request.kinetics_template.model_dump(mode="python")
    kinetic_intervals = []
    for index, interval in enumerate(request.kinetics_template.intervals):
        kinetic_intervals.append(interval.model_dump(mode="python") | {
            "saturation_ratio": ratios[index],
            "saturation_ratio_end": ratios[index + 1],
        })
    kinetics_data["intervals"] = tuple(kinetic_intervals)
    resolved_kinetics = CallerSurfaceScaleKinetics.model_validate(kinetics_data)
    scale_result = caller_surface_scale_kinetics(resolved_kinetics)
    return Calculation(status=scale_result.status, values=base | {
        "completed_saturation_knot_count": len(saturation_rows),
        "saturation_knot_results": saturation_rows,
        "resolved_scale_kinetics_request_sha256": canonical_digest(resolved_kinetics.model_dump(mode="json")),
        "scale_kinetics_request_input_sha256": canonical_digest(request.kinetics_template.model_dump(mode="json")),
        "scale_kinetics_result": scale_result.model_dump(mode="json"),
        "saturation_path_basis": "exact_selected_solid_ratio_at_source_knots; caller-reviewed piecewise-linear ratio between adjacent knots",
        "phase_selection_performed": False,
        "temperature_interpolation_performed": False,
        "not_inferred": ["solid_phase_selection", "kinetic_coefficients", "corrosion_rate", "wall_loss", "protection_factor", "acceptance", "failure_probability"],
    }, notes=(
        "Carbonate concentrations are converted to dimensionless activities using only caller-supplied per-knot activity coefficients and the declared 1 mol/L standard state.",
        "Each exact knot uses a caller-supplied temperature-supported Ksp record; no temperature interpolation or automatic phase discovery is performed.",
        "The existing caller scale law is evaluated only after all knots screen successfully; the scale result remains conditional on its caller-supplied empirical coefficients and applicability reviews.",
    ) + scale_result.notes)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.fixed_fugacity_carbonate_to_scale_kinetics",
        input_type=FixedFugacityCarbonateScaleKinetics,
        evaluator=evaluate_fixed_fugacity_carbonate_scale_kinetics,
        units={
            "knots[].time_s": "s",
            "knots[].temperature_K": "K",
            "knots[].carbonate_concentration_mol_L": "mol/L",
            "knots[].carbonate_activity_coefficient": "1",
            "knots[].carbonate_dimensionless_activity": "1",
            "knots[].log10_saturation_ratio": "1",
            "knots[].saturation_ratio": "1",
            "scale_kinetics_result.values.final_scale_thickness_m": "m",
            "scale_kinetics_result.values.scale_history[].scale_thickness_m": "m",
        },
        assumptions=(
            "Use the exact computed fixed-fugacity carbonate history CO3 concentration, multiply by a caller-provided activity coefficient under the declared 1 mol/L standard state, add explicitly supplied activities for all other candidate-solid species, and screen one caller-selected phase with per-knot Ksp records.",
            "Every temperature/Ksp point must match an exact carbonate history knot; no thermodynamic constant or activity coefficient is inferred or interpolated.",
            "Only after all saturation screens compute, transfer their positive finite saturation ratios at exact time knots to the existing caller surface-scale law, which linearly reconstructs saturation only under its explicit review.",
            "No phase discovery, saturation equilibrium beyond the selected candidate, kinetic-coefficient derivation, corrosion/protection prediction or qualification is provided.",
        ),
        source_ids=("caller_fixed_fugacity_carbonate_to_scale_kinetics",),
        qualification="user_model",
        context_validator=_carbonate_context,
    )]
