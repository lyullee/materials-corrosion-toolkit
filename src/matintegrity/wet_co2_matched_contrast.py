"""Exact matched contrasts from provider model-output rows for wet-CO2 screening."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec
from .wet_co2_data import WetCo2SimulationGridRow

INTERFACE_ID = "degradation.wet_co2_simulation_matched_contrast"
SOURCE_ID = "caller_wet_co2_simulation_matched_contrast"
FACTOR_FIELDS = {
    "temperature_K": "K",
    "flow_velocity_m_s": "m/s",
    "co2_pressure_Pa": "Pa",
    "internal_pressure_Pa": "Pa",
    "corrosion_inhibitor_efficiency_fraction": "1",
    "shear_stress_Pa": "Pa",
    "ph": "1",
}
CONTROL_FIELDS = tuple(FACTOR_FIELDS)


class WetCo2MatchedContrastRequest(Contract):
    """Compare exactly two provider simulation rows differing in one factor."""

    schema_version: Literal["matintegrity.wet_co2_matched_contrast.v1"] = "matintegrity.wet_co2_matched_contrast.v1"
    lower_factor_row: WetCo2SimulationGridRow
    upper_factor_row: WetCo2SimulationGridRow
    varied_factor: Literal[
        "temperature_K", "flow_velocity_m_s", "co2_pressure_Pa", "internal_pressure_Pa",
        "corrosion_inhibitor_efficiency_fraction", "shear_stress_Pa", "ph",
    ]
    provider_pairing_and_ceteris_paribus_reviewed: bool
    simulation_output_scope_reviewed: bool

    @model_validator(mode="after")
    def validate_pair(self):
        low, high = self.lower_factor_row, self.upper_factor_row
        if low.dataset_id != high.dataset_id or low.source_group_id != high.source_group_id:
            raise ValueError("matched contrast rows must share the exact dataset and source group")
        if low.source_archive_sha256 != high.source_archive_sha256:
            raise ValueError("matched contrast rows must share a source archive digest")
        if low.provider_row == high.provider_row:
            raise ValueError("matched contrast requires two distinct provider rows")
        for field in CONTROL_FIELDS:
            a, b = getattr(low, field), getattr(high, field)
            if field == self.varied_factor:
                if not b > a:
                    raise ValueError("upper-factor row must have a strictly larger varied factor")
            elif a != b:
                raise ValueError("all nonvaried model inputs must match exactly")
        return self


def wet_co2_matched_contrast(request: WetCo2MatchedContrastRequest) -> Calculation:
    """Report a paired finite difference without interpreting it as causality or an experiment."""
    low, high = request.lower_factor_row, request.upper_factor_row
    factor = request.varied_factor
    x0, x1 = float(getattr(low, factor)), float(getattr(high, factor))
    y0, y1 = float(low.corrosion_rate_m_s), float(high.corrosion_rate_m_s)
    dx, dy = x1 - x0, y1 - y0
    base = {
        "model_id": INTERFACE_ID,
        "dataset_id": low.dataset_id,
        "dataset_doi": low.dataset_doi,
        "source_group_id": low.source_group_id,
        "source_archive_sha256": low.source_archive_sha256,
        "provider_rows": [low.provider_row, high.provider_row],
        "row_pair_sha256": canonical_digest([low.model_dump(mode="json"), high.model_dump(mode="json")]),
        "varied_factor": factor,
        "factor_unit": FACTOR_FIELDS[factor],
        "response_unit": "m/s",
        "lower_factor_value": x0,
        "upper_factor_value": x1,
        "lower_rate_m_s": y0,
        "upper_rate_m_s": y1,
        "provider_output_is_simulation": True,
        "independent_physical_observation": False,
        "causal_effect_inferred": False,
        "failure_probability_inferred": False,
    }
    if not request.provider_pairing_and_ceteris_paribus_reviewed or not request.simulation_output_scope_reviewed:
        missing = []
        if not request.provider_pairing_and_ceteris_paribus_reviewed:
            missing.append("provider_pairing_and_ceteris_paribus_reviewed")
        if not request.simulation_output_scope_reviewed:
            missing.append("simulation_output_scope_reviewed")
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    slope = dy / dx
    if not math.isfinite(slope):
        return Calculation(status="out_of_scope", values=base | {"reason": "finite_difference_overflow"})
    rate_ratio = (y1 / y0) if y0 > 0 else None
    if rate_ratio is not None and not math.isfinite(rate_ratio):
        rate_ratio = None
    elasticity = None
    if x0 > 0 and y0 > 0 and y1 > 0:
        log_x = math.log(x1) - math.log(x0)
        if log_x != 0:
            elasticity = (math.log(y1) - math.log(y0)) / log_x
            if not math.isfinite(elasticity):
                elasticity = None
    result = base | {
        "factor_difference": dx,
        "rate_difference_m_s": dy,
        "finite_difference_m_s_per_factor_unit": slope,
        "rate_ratio_upper_over_lower": rate_ratio,
        "log_log_secant_elasticity": elasticity,
        "interpretation": "paired contrast among provider-generated model rows; not physical causal evidence",
    }
    return Calculation(values=result, notes=(
        "Only an exact two-row contrast is calculated; all other declared model inputs must match exactly.",
        "The source rows are model-generated output and do not establish experimental sensitivity, causal response, corrosion kinetics, or qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=INTERFACE_ID,
        input_type=WetCo2MatchedContrastRequest,
        evaluator=wet_co2_matched_contrast,
        units={"factor_difference": "mixed", "rate_difference_m_s": "m/s", "finite_difference_m_s_per_factor_unit": "mixed", "rate_ratio_upper_over_lower": "1", "log_log_secant_elasticity": "1"},
        assumptions=("Rows are provider-generated NORSOK M-506 simulation output with matched nonvaried inputs.", "The contrast describes the provider grid only and is not an experimental or causal estimate."),
        source_ids=(SOURCE_ID,),
        qualification="engineering_screening",
    )]
