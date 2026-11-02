"""Map finite wet-CO2 provider simulation rows to caller-defined wall-loss scenarios."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .wet_co2_data import WetCo2SimulationGridRow


SOURCE_ID = "caller_wet_co2_simulation_rows_to_wall_loss_scenarios"
MODEL_ID = "integration.wet_co2_simulation_wall_loss_envelope"
SECONDS_PER_JULIAN_YEAR = 365.25 * 24.0 * 60.0 * 60.0


class WetCo2SimulationWallLossScenario(Contract):
    """A provider row retained as one distinct model-output scenario."""

    provider_row: StrictInt = Field(ge=2)
    row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    corrosion_rate_m_s: float = Field(ge=0)


class WetCo2SimulationWallLossEnvelopeRequest(Contract):
    """Finite row-derived wall-loss range under an explicit constant-rate mapping."""

    schema_version: Literal["matintegrity.wet_co2_simulation_wall_loss_envelope.v1"] = (
        "matintegrity.wet_co2_simulation_wall_loss_envelope.v1"
    )
    scenarios: tuple[WetCo2SimulationWallLossScenario, ...] = Field(min_length=1, max_length=243)
    rows: tuple[WetCo2SimulationGridRow, ...] = Field(min_length=1, max_length=243)
    exposure_duration_s: float = Field(gt=0)
    baseline_wall_thickness_m: float = Field(gt=0)
    required_wall_thickness_m: float = Field(ge=0)
    baseline_evidence: Evidence
    required_thickness_evidence: Evidence
    scenario_mapping_reviewed: bool
    constant_rate_over_exposure_reviewed: bool
    baseline_location_material_time_scope_reviewed: bool
    finite_scenario_set_interpretation_reviewed: bool

    @model_validator(mode="after")
    def row_scenario_coherence(self):
        if len(self.scenarios) != len(self.rows):
            raise ValueError("each scenario must map to exactly one source row")
        if len({row.provider_row for row in self.rows}) != len(self.rows):
            raise ValueError("provider row identities must be unique")
        pairs = list(zip(self.scenarios, self.rows, strict=True))
        if any(
            scenario.provider_row != row.provider_row
            or scenario.row_sha256 != canonical_digest(row.model_dump(mode="json"))
            or scenario.corrosion_rate_m_s != row.corrosion_rate_m_s
            for scenario, row in pairs
        ):
            raise ValueError("scenario values and digests must match their exact source rows")
        for field in ("dataset_id", "dataset_doi", "source_group_id", "source_archive_sha256"):
            if len({getattr(row, field) for row in self.rows}) != 1:
                raise ValueError(f"all provider simulation rows must share {field}")
        if not any(
            item.source_id == self.rows[0].dataset_id
            and item.origin == "open_dataset"
            and item.license_id == "CC-BY-4.0"
            and item.sha256 == self.rows[0].source_archive_sha256
            for row in self.rows
            for item in row.evidence
        ):
            raise ValueError("source rows need the matching licensed archive Evidence")
        if self.required_wall_thickness_m >= self.baseline_wall_thickness_m:
            raise ValueError("required thickness must be below the measured baseline")
        if self.baseline_evidence.origin != "measured":
            raise ValueError("baseline evidence must identify a measured wall-thickness source")
        if self.required_thickness_evidence.origin not in {"user_declared", "open_dataset"}:
            raise ValueError("required-thickness evidence must identify a caller-declared or open-dataset limit")
        return self


def evaluate_wet_co2_simulation_wall_loss_envelope(
    request: WetCo2SimulationWallLossEnvelopeRequest,
) -> Calculation:
    """Calculate conditional uniform wall-loss scenarios; no distribution is inferred."""
    reviews = {
        "scenario_mapping_reviewed": request.scenario_mapping_reviewed,
        "constant_rate_over_exposure_reviewed": request.constant_rate_over_exposure_reviewed,
        "baseline_location_material_time_scope_reviewed": request.baseline_location_material_time_scope_reviewed,
        "finite_scenario_set_interpretation_reviewed": request.finite_scenario_set_interpretation_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "missing_reviews": missing})

    duration_years = request.exposure_duration_s / SECONDS_PER_JULIAN_YEAR
    result_rows = []
    for scenario, row in zip(request.scenarios, request.rows, strict=True):
        loss_m = scenario.corrosion_rate_m_s * request.exposure_duration_s
        remaining_m = request.baseline_wall_thickness_m - loss_m
        margin_m = remaining_m - request.required_wall_thickness_m
        if not all(math.isfinite(value) for value in (duration_years, loss_m, remaining_m, margin_m)):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID,
                "reason": "scenario_wall_loss_exceeds_finite_numeric_support",
                "provider_row": row.provider_row,
                "completed_scenarios": result_rows,
            })
        if loss_m > request.baseline_wall_thickness_m:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID,
                "reason": "uniform_loss_exceeds_measured_baseline_before_exposure_end",
                "provider_row": row.provider_row,
                "uniform_wall_loss_m": loss_m,
                "baseline_wall_thickness_m": request.baseline_wall_thickness_m,
                "completed_scenarios": result_rows,
            })
        crossing_time = None
        if scenario.corrosion_rate_m_s > 0.0:
            candidate = (request.baseline_wall_thickness_m - request.required_wall_thickness_m) / scenario.corrosion_rate_m_s
            if math.isfinite(candidate) and 0.0 <= candidate <= request.exposure_duration_s:
                crossing_time = candidate
        result_rows.append({
            "provider_row": row.provider_row,
            "source_row_sha256": scenario.row_sha256,
            "source_archive_sha256": row.source_archive_sha256,
            "source_data_type": "provider_simulation_output",
            "corrosion_rate_m_s": scenario.corrosion_rate_m_s,
            "uniform_wall_loss_m": loss_m,
            "remaining_thickness_m": remaining_m,
            "required_thickness_margin_m": margin_m,
            "threshold_crossing_time_within_exposure_s": crossing_time,
        })

    minimum = min(result_rows, key=lambda item: item["remaining_thickness_m"])
    maximum = max(result_rows, key=lambda item: item["remaining_thickness_m"])
    return Calculation(values={
        "model_id": MODEL_ID,
        "dataset_id": request.rows[0].dataset_id,
        "dataset_doi": request.rows[0].dataset_doi,
        "source_group_id": request.rows[0].source_group_id,
        "source_archive_sha256": request.rows[0].source_archive_sha256,
        "provider_row_count": len(result_rows),
        "exposure_duration_s": request.exposure_duration_s,
        "exposure_duration_julian_year": duration_years,
        "baseline_wall_thickness_m": request.baseline_wall_thickness_m,
        "required_wall_thickness_m": request.required_wall_thickness_m,
        "baseline_evidence": request.baseline_evidence.model_dump(mode="json"),
        "required_thickness_evidence": request.required_thickness_evidence.model_dump(mode="json"),
        "minimum_remaining_thickness_m": minimum["remaining_thickness_m"],
        "minimum_remaining_provider_row": minimum["provider_row"],
        "maximum_remaining_thickness_m": maximum["remaining_thickness_m"],
        "maximum_remaining_provider_row": maximum["provider_row"],
        "finite_provider_simulation_scenarios": result_rows,
        "scenario_weights_used": False,
        "probability_inferred": False,
        "field_corrosion_prediction": False,
        "qualification_inferred": False,
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "interpretation_limit": "conditional uniform-loss scenario arithmetic from provider-generated rows; not field calibration, acceptance, or risk",
    }, notes=(
        "The result spans only the exact finite provider rows supplied; no weights or probability semantics are assigned.",
        "A constant corrosion rate and uniform area-average wall loss are caller assumptions over the declared exposure duration.",
        "Provider-generated model output is not an independent physical observation or qualified field corrosion forecast.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2SimulationWallLossEnvelopeRequest,
        evaluator=evaluate_wet_co2_simulation_wall_loss_envelope,
        units={
            "provider_row_count": "1",
            "exposure_duration_s": "s",
            "exposure_duration_julian_year": "year",
            "baseline_wall_thickness_m": "m",
            "required_wall_thickness_m": "m",
            "minimum_remaining_thickness_m": "m",
            "maximum_remaining_thickness_m": "m",
            "finite_provider_simulation_scenarios[].corrosion_rate_m_s": "m/s",
            "finite_provider_simulation_scenarios[].uniform_wall_loss_m": "m",
            "finite_provider_simulation_scenarios[].remaining_thickness_m": "m",
            "finite_provider_simulation_scenarios[].required_thickness_margin_m": "m",
            "finite_provider_simulation_scenarios[].threshold_crossing_time_within_exposure_s": "s",
        },
        assumptions=(
            "Each provider simulation scenario is bound to exactly one CC BY source row, row digest and archive evidence digest.",
            "Baseline evidence must be measured; required thickness must be supported by a caller-declared or open-dataset limit. Uniform corrosion rate over the full exposure and uniform wall-loss mapping require explicit caller review.",
            "The output describes only the finite provider simulation rows, without scenario weights, probability, field calibration, acceptance or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
