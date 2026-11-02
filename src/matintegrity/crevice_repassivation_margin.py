"""Evidence-bound comparison of caller measured crevice potentials and repassivation thresholds."""

from __future__ import annotations

import math

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, canonical_digest
from .registry import ModelSpec

MODEL_ID = "validation.crevice_repassivation_margin_history"
THRESHOLD_SOURCE_ID = "caller_crevice_repassivation_threshold_history"
OPERATING_SOURCE_ID = "caller_measured_crevice_operating_potential_history"
METHOD_SOURCE_ID = "exact_knot_uncertainty_aware_potential_margin_screen"
EXCURSION_SOURCE_ID = "exact_knot_sample_supported_threshold_excursion_duration"


class CreviceRepassivationThresholdKnot(Contract):
    time_s: Nonnegative
    material_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    electrolyte_record_id: str = Field(min_length=1)
    electrolyte_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: float = Field(gt=0.0)
    chloride_molality_mol_kg: Nonnegative
    reference_electrode_id: str = Field(min_length=1)
    potential_convention_id: str = Field(min_length=1)
    repassivation_potential_mV: float
    standard_uncertainty_mV: Nonnegative
    specimen_count: StrictInt = Field(ge=1, le=100000)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_threshold(self):
        if not math.isfinite(self.temperature_K) or not math.isfinite(self.repassivation_potential_mV):
            raise ValueError("threshold temperature and potential must be finite")
        payload = {
            "time_s": self.time_s, "material_id": self.material_id, "condition_id": self.condition_id,
            "electrolyte_record_id": self.electrolyte_record_id, "electrolyte_sha256": self.electrolyte_sha256,
            "temperature_K": self.temperature_K, "chloride_molality_mol_kg": self.chloride_molality_mol_kg,
            "reference_electrode_id": self.reference_electrode_id,
            "potential_convention_id": self.potential_convention_id,
            "repassivation_potential_mV": self.repassivation_potential_mV,
            "standard_uncertainty_mV": self.standard_uncertainty_mV, "specimen_count": self.specimen_count,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("threshold record digest must bind its complete material/environment/potential state")
        if not any(row.source_id == self.electrolyte_record_id and row.sha256 == self.electrolyte_sha256
                   and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin the declared electrolyte/condition record")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin the measured threshold record")
        return self


class CreviceOperatingPotentialKnot(Contract):
    time_s: Nonnegative
    material_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    electrolyte_record_id: str = Field(min_length=1)
    electrolyte_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: float = Field(gt=0.0)
    chloride_molality_mol_kg: Nonnegative
    reference_electrode_id: str = Field(min_length=1)
    potential_convention_id: str = Field(min_length=1)
    operating_potential_mV: float
    standard_uncertainty_mV: Nonnegative
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_operating(self):
        if not math.isfinite(self.temperature_K) or not math.isfinite(self.operating_potential_mV):
            raise ValueError("operating temperature and potential must be finite")
        payload = {
            "time_s": self.time_s, "material_id": self.material_id, "condition_id": self.condition_id,
            "electrolyte_record_id": self.electrolyte_record_id, "electrolyte_sha256": self.electrolyte_sha256,
            "temperature_K": self.temperature_K, "chloride_molality_mol_kg": self.chloride_molality_mol_kg,
            "reference_electrode_id": self.reference_electrode_id,
            "potential_convention_id": self.potential_convention_id,
            "operating_potential_mV": self.operating_potential_mV,
            "standard_uncertainty_mV": self.standard_uncertainty_mV,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("operating potential digest must bind exact material/environment/reference state")
        if not any(row.source_id == self.electrolyte_record_id and row.sha256 == self.electrolyte_sha256
                   and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin the exact operating electrolyte record")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each operating potential record")
        return self


class CreviceRepassivationMarginHistoryRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    threshold_history: tuple[CreviceRepassivationThresholdKnot, ...] = Field(min_length=1, max_length=5000)
    operating_history: tuple[CreviceOperatingPotentialKnot, ...] = Field(min_length=1, max_length=5000)
    uncertainty_multiplier: Nonnegative = 2.0
    exact_material_condition_and_reference_match_reviewed: bool
    threshold_measurement_and_interpretation_reviewed: bool
    measurement_uncertainty_basis_reviewed: bool
    no_extrapolation_or_probability_interpretation_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_exact_matching(self):
        if len(self.threshold_history) != len(self.operating_history):
            raise ValueError("threshold and operating histories must have the same exact knot count")
        if not all((self.exact_material_condition_and_reference_match_reviewed,
                    self.threshold_measurement_and_interpretation_reviewed,
                    self.measurement_uncertainty_basis_reviewed,
                    self.no_extrapolation_or_probability_interpretation_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all material/condition/reference, measurement and interpretation reviews are required")
        for left, right in zip(self.threshold_history, self.operating_history, strict=True):
            exact_fields = (
                "time_s", "material_id", "condition_id", "electrolyte_record_id", "electrolyte_sha256",
                "temperature_K", "chloride_molality_mol_kg", "reference_electrode_id", "potential_convention_id",
            )
            if any(getattr(left, name) != getattr(right, name) for name in exact_fields):
                raise ValueError("each threshold must exactly match operating material, condition, electrolyte, temperature and reference")
        times = tuple(row.time_s for row in self.operating_history)
        if any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("potential knots must be in strictly increasing time order")
        return self


def evaluate_crevice_repassivation_margin_history(request: CreviceRepassivationMarginHistoryRequest) -> Calculation:
    """Compare measured operating potential with exact condition-matched repassivation observations."""
    digest = canonical_digest(request.model_dump(mode="json"))
    rows = []
    for threshold, operating in zip(request.threshold_history, request.operating_history, strict=True):
        margin = operating.operating_potential_mV - threshold.repassivation_potential_mV
        combined_uncertainty = math.hypot(operating.standard_uncertainty_mV, threshold.standard_uncertainty_mV)
        band = request.uncertainty_multiplier * combined_uncertainty
        if margin > band:
            classification = "operating_potential_above_threshold_band"
        elif margin < -band:
            classification = "operating_potential_below_threshold_band"
        else:
            classification = "uncertainty_bands_overlap"
        rows.append({
            "time_s": threshold.time_s,
            "material_id": threshold.material_id,
            "condition_id": threshold.condition_id,
            "reference_electrode_id": threshold.reference_electrode_id,
            "operating_potential_mV": operating.operating_potential_mV,
            "repassivation_potential_mV": threshold.repassivation_potential_mV,
            "signed_operating_minus_repassivation_margin_mV": margin,
            "combined_standard_uncertainty_mV": combined_uncertainty,
            "uncertainty_multiplier": request.uncertainty_multiplier,
            "classification": classification,
            "threshold_record_sha256": threshold.record_sha256,
            "operating_record_sha256": operating.record_sha256,
            "threshold_specimen_count": threshold.specimen_count,
        })
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": digest,
        "exact_knot_count": len(rows),
        "potential_margin_history": rows,
        "interpretation": "exact_condition_matched_repassivation_potential_margin_screen",
        "limitations": [
            "The API compares caller-measured potentials only at exact matched material/condition/temperature/electrolyte/reference knots; it does not interpolate or extrapolate.",
            "The signed numerical margin and uncertainty band are not an electrochemical prediction, corrosion rate, event probability or acceptance criterion.",
            "Potential polarity, iR correction, reference-electrode conversion, surface state, specimen representativeness and threshold test method remain caller-reviewed.",
            "No pH/speciation, phase equilibrium, pit initiation, repassivation kinetics, wall loss, life or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceRepassivationMarginHistoryRequest,
        evaluator=evaluate_crevice_repassivation_margin_history,
        units={
            "potential_margin_history[].time_s": "s",
            "potential_margin_history[].operating_potential_mV": "mV",
            "potential_margin_history[].repassivation_potential_mV": "mV",
            "potential_margin_history[].signed_operating_minus_repassivation_margin_mV": "mV",
            "potential_margin_history[].combined_standard_uncertainty_mV": "mV",
        },
        assumptions=(
            "Threshold and operating potentials refer to the same exact material, test condition, electrolyte record, temperature, reference electrode and sign convention.",
            "Classification compares signed potential margin with a caller-selected multiple of the root-sum-square standard uncertainty; it carries no probability meaning.",
            "The tool evaluates caller measurements only and does not predict corrosion or electrochemical kinetics.",
        ),
        source_ids=(THRESHOLD_SOURCE_ID, OPERATING_SOURCE_ID, METHOD_SOURCE_ID),
    ), ModelSpec(
        model_id="validation.crevice_repassivation_excursion_duration_history",
        input_type=CreviceRepassivationExcursionDurationRequest,
        evaluator=evaluate_crevice_repassivation_excursion_duration_history,
        units={
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].duration_s": "s",
            "definite_sample_supported_above_band_duration_s": "s",
            "possible_sample_supported_above_band_duration_s": "s",
            "unresolved_transition_duration_s": "s",
        },
        assumptions=(
            "Each reported duration covers only an interval bounded by two measured exact knots; no within-interval crossing time is inferred.",
            "An interval is definitely above the uncertainty band only when both endpoint classifications are above; any other interval remains unresolved or possible.",
            "The result is a descriptive sampled-history summary, not a continuous-time prediction, probability, corrosion rate or acceptance decision.",
        ),
        source_ids=(THRESHOLD_SOURCE_ID, OPERATING_SOURCE_ID, METHOD_SOURCE_ID, EXCURSION_SOURCE_ID),
    )]


class CreviceRepassivationExcursionDurationRequest(Contract):
    """Request a sample-supported duration summary from exact matched measurements."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    margin_request: CreviceRepassivationMarginHistoryRequest
    interval_interpretation_reviewed: bool

    @model_validator(mode="after")
    def require_interval_review(self):
        if not self.interval_interpretation_reviewed:
            raise ValueError("review that each interval is only an endpoint-supported sampled summary")
        return self


def evaluate_crevice_repassivation_excursion_duration_history(
    request: CreviceRepassivationExcursionDurationRequest,
) -> Calculation:
    """Summarize intervals supported by adjacent exact measurements, without inferring crossings."""
    margin_result = evaluate_crevice_repassivation_margin_history(request.margin_request)
    knots = margin_result.values["potential_margin_history"]
    intervals = []
    definite_duration = 0.0
    possible_duration = 0.0
    unresolved_duration = 0.0
    for left, right in zip(knots, knots[1:]):
        duration = right["time_s"] - left["time_s"]
        left_above = left["classification"] == "operating_potential_above_threshold_band"
        right_above = right["classification"] == "operating_potential_above_threshold_band"
        left_possible = left["signed_operating_minus_repassivation_margin_mV"] + (
            request.margin_request.uncertainty_multiplier * left["combined_standard_uncertainty_mV"]
        ) > 0.0
        right_possible = right["signed_operating_minus_repassivation_margin_mV"] + (
            request.margin_request.uncertainty_multiplier * right["combined_standard_uncertainty_mV"]
        ) > 0.0
        if left_above and right_above:
            classification = "both_measured_endpoints_above_uncertainty_band"
            definite_duration += duration
            possible_duration += duration
        elif left_possible or right_possible:
            classification = "at_least_one_endpoint_allows_above_band_but_duration_unresolved"
            possible_duration += duration
            unresolved_duration += duration
        else:
            classification = "endpoint_supported_above_band_excursion_not_established"
            unresolved_duration += duration
        intervals.append({
            "start_time_s": left["time_s"],
            "end_time_s": right["time_s"],
            "duration_s": duration,
            "start_margin_mV": left["signed_operating_minus_repassivation_margin_mV"],
            "end_margin_mV": right["signed_operating_minus_repassivation_margin_mV"],
            "start_classification": left["classification"],
            "end_classification": right["classification"],
            "interval_classification": classification,
        })
    digest = canonical_digest(request.model_dump(mode="json"))
    return Calculation(status="computed", values={
        "model_id": "validation.crevice_repassivation_excursion_duration_history",
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": digest,
        "interval_count": len(intervals),
        "intervals": intervals,
        "definite_sample_supported_above_band_duration_s": definite_duration,
        "possible_sample_supported_above_band_duration_s": possible_duration,
        "unresolved_transition_duration_s": unresolved_duration,
        "duration_semantics": "endpoint-supported interval sums only; no interpolation or continuous-time crossing claim",
        "limitations": [
            "A duration is counted as definitely above only when both measured endpoints exceed their uncertainty bands.",
            "If both endpoints permit an above-band state but do not establish it, the interval is reported as possible and unresolved; this is not a probability.",
            "Intervals with endpoint states that do not support an above-band excursion remain unresolved; sparse sampling can hide crossings or short events.",
            "No interpolation, extrapolation, continuous-time trajectory, corrosion kinetics, event probability or acceptance decision is computed.",
        ],
    })
