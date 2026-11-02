"""Fixed-fugacity gas-liquid CO2 equilibrium with carbonate-only alkalinity closure."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .carbonate_alkalinity import ACTIVITY_STANDARD_CONCENTRATION_MOL_L, CarbonateActivityConstants

SOURCE_IDS = ("usgs_phreeqc_gas_liquid_equilibrium", "usgs_advanced_carbonate_speciation")
LN10 = math.log(10.0)


class Co2HenrySolubilityRecord(Contract):
    """Caller-provided Henry solubility coefficient with explicit convention and lineage."""

    temperature_K: Positive
    coefficient_mol_L_Pa: Positive
    convention: Literal["aqueous_CO2star_concentration_over_gas_fugacity"]
    solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FixedFugacityCarbonateEquilibrium(Contract):
    """Solve carbonate-only aqueous pH at caller-supplied fixed CO2 fugacity."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    temperature_K: Positive
    co2_fugacity_Pa: Positive
    gas_fugacity_provider_id: str = Field(min_length=1)
    gas_fugacity_provider_revision: str = Field(min_length=1)
    gas_fugacity_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    gas_fugacity_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    henry: Co2HenrySolubilityRecord
    constants: CarbonateActivityConstants
    measured_total_alkalinity_mol_L: float
    alkalinity_provider_id: str = Field(min_length=1)
    alkalinity_provider_revision: str = Field(min_length=1)
    alkalinity_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    alkalinity_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expanded_total_alkalinity_uncertainty_mol_L: Nonnegative
    alkalinity_uncertainty_basis: str = Field(min_length=1)
    ph_search_lower: float = Field(ge=-20.0, le=20.0)
    ph_search_upper: float = Field(ge=-20.0, le=20.0)
    ph_tolerance: Positive
    alkalinity_closure_tolerance_mol_L: Positive
    temperature_match_tolerance_K: Nonnegative = 0.0
    maximum_iterations: int = Field(default=256, ge=8, le=512)
    carbonate_only_alkalinity_reviewed: bool
    gas_fugacity_reviewed: bool
    fixed_fugacity_reservoir_reviewed: bool
    henry_convention_reviewed: bool
    solvent_composition_match_reviewed: bool
    activity_scales_reviewed: bool
    constants_temperature_basis_reviewed: bool
    alkalinity_measurement_reviewed: bool
    gas_equilibrium_review_id: str = Field(min_length=1)
    henry_record_review_id: str = Field(min_length=1)
    alkalinity_record_review_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self):
        if self.ph_search_lower >= self.ph_search_upper:
            raise ValueError("pH search bounds must be strictly increasing")
        for field_name in (
            "assessment_id",
            "asset_id",
            "location_id",
            "sample_id",
            "gas_fugacity_provider_id",
            "gas_fugacity_provider_revision",
            "alkalinity_provider_id",
            "alkalinity_provider_revision",
            "alkalinity_uncertainty_basis",
            "gas_equilibrium_review_id",
            "henry_record_review_id",
            "alkalinity_record_review_id",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} cannot be blank")
        return self


class FixedFugacityCarbonateHistory(Contract):
    """Ordered pointwise carbonate equilibria with explicit, non-interpolated time support."""

    schema_version: Literal["matintegrity.fixed_fugacity_carbonate_history.v1"] = (
        "matintegrity.fixed_fugacity_carbonate_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=20000)
    equilibria: tuple[FixedFugacityCarbonateEquilibrium, ...] = Field(min_length=1, max_length=20000)
    history_clock_and_sample_alignment_reviewed: bool
    maximum_point_evaluations: int = Field(default=20000, ge=1, le=20000)

    @model_validator(mode="after")
    def aligned_history(self):
        if len(self.time_s) != len(self.equilibria):
            raise ValueError("one carbonate equilibrium request is required for each declared time point")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("history times must be strictly increasing")
        sample_ids = [row.sample_id for row in self.equilibria]
        assessment_ids = [row.assessment_id for row in self.equilibria]
        if len(set(sample_ids)) != len(sample_ids) or len(set(assessment_ids)) != len(assessment_ids):
            raise ValueError("history sample and assessment identifiers must be unique")
        if any((row.asset_id, row.location_id) != (self.asset_id, self.location_id) for row in self.equilibria):
            raise ValueError("all point equilibria must match the history asset and location")
        return self


class FixedFugacityCarbonateScenario(Contract):
    scenario_id: str = Field(min_length=1)
    normalized_weight: Nonnegative
    equilibrium: FixedFugacityCarbonateEquilibrium


class FixedFugacityCarbonateEnsemble(Contract):
    ensemble_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    exposure_interval_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    scenarios: tuple[FixedFugacityCarbonateScenario, ...] = Field(min_length=1, max_length=100_000)
    scenario_weights_reviewed: bool
    common_sample_scope_reviewed: bool
    weight_meaning: Literal[
        "caller_scenario_mass_not_event_probability",
        "caller_distribution_weights_model_implied_uncertainty",
    ]
    input_distribution_id: str = Field(min_length=1)
    input_distribution_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_ensemble(self):
        ids = [row.scenario_id for row in self.scenarios]
        if any(not value.strip() for value in ids) or len(ids) != len(set(ids)):
            raise ValueError("scenario identifiers must be nonblank and unique")
        total = math.fsum(row.normalized_weight for row in self.scenarios)
        if not math.isfinite(total) or abs(total - 1.0) > 1e-10:
            raise ValueError("scenario weights must be normalized to one")
        for row in self.scenarios:
            x = row.equilibrium
            if (x.asset_id, x.location_id, x.sample_id) != (self.asset_id, self.location_id, self.sample_id):
                raise ValueError("scenario asset, location and sample identities must match the ensemble")
        return self


def _carbonate_state(
    ph_activity: float,
    co2star_mol_L: float,
    constants: CarbonateActivityConstants,
) -> dict[str, float]:
    h_activity = 10.0**-ph_activity
    h_mol_L = h_activity / constants.gamma_h_plus * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    oh_mol_L = (
        constants.Kw_activity / h_activity / constants.gamma_oh_minus * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    )
    co2_activity = co2star_mol_L / ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    hco3_activity = constants.K1_activity * co2_activity / h_activity
    hco3_mol_L = hco3_activity / constants.gamma_hco3_minus * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    co3_activity = constants.K2_activity * hco3_activity / h_activity
    co3_mol_L = co3_activity / constants.gamma_co3_double_minus * ACTIVITY_STANDARD_CONCENTRATION_MOL_L
    alkalinity = hco3_mol_L + 2.0 * co3_mol_L + oh_mol_L - h_mol_L
    derivative = LN10 * (hco3_mol_L + 4.0 * co3_mol_L + oh_mol_L + h_mol_L)
    return {
        "h_activity": h_activity,
        "h_mol_L": h_mol_L,
        "oh_mol_L": oh_mol_L,
        "co2star_mol_L": co2star_mol_L,
        "hco3_activity": hco3_activity,
        "hco3_mol_L": hco3_mol_L,
        "co3_activity": co3_activity,
        "co3_mol_L": co3_mol_L,
        "calculated_alkalinity_mol_L": alkalinity,
        "d_alkalinity_d_pH_mol_L": derivative,
    }


def fixed_fugacity_carbonate_equilibrium(x: FixedFugacityCarbonateEquilibrium) -> Calculation:
    review_fields = (
        "carbonate_only_alkalinity_reviewed",
        "gas_fugacity_reviewed",
        "fixed_fugacity_reservoir_reviewed",
        "henry_convention_reviewed",
        "solvent_composition_match_reviewed",
        "activity_scales_reviewed",
        "constants_temperature_basis_reviewed",
        "alkalinity_measurement_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "missing_reviews": missing_reviews,
            },
            notes=("Gas, Henry-law, solvent, activity and analytical-alkalinity review gates are required.",),
        )

    if x.henry.convention != "aqueous_CO2star_concentration_over_gas_fugacity":
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "missing_reviews": ["reviewed_Henry_convention"],
            },
            notes=(
                "The supplied Henry coefficient must use the declared concentration-over-fugacity convention.",
            ),
        )
    if x.sample_solvent_composition_sha256 != x.henry.solvent_composition_sha256:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "missing_reviews": ["Henry_record_matches_sample_solvent_composition"],
            },
            notes=(
                "The Henry coefficient must be qualified for the supplied sample solvent-composition digest.",
            ),
        )
    for label, temperature in (
        ("Henry_solubility_record", x.henry.temperature_K),
        ("carbonate_constants_record", x.constants.temperature_K),
    ):
        if abs(temperature - x.temperature_K) > x.temperature_match_tolerance_K:
            return Calculation(
                status="needs_data",
                values={
                    "assessment_id": x.assessment_id,
                    "sample_id": x.sample_id,
                    "missing_reviews": [f"temperature_matched_{label}"],
                },
                notes=(
                    "No temperature correction or extrapolation of Henry or equilibrium constants is performed.",
                ),
            )

    co2star = x.henry.coefficient_mol_L_Pa * x.co2_fugacity_Pa
    if not math.isfinite(co2star) or co2star <= 0.0:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "reason": "invalid_Henry_product",
            },
            notes=(
                "The supplied Henry coefficient and fugacity did not produce a finite positive dissolved CO2* concentration.",
            ),
        )

    def residual(ph: float) -> float:
        return (
            _carbonate_state(ph, co2star, x.constants)["calculated_alkalinity_mol_L"]
            - x.measured_total_alkalinity_mol_L
        )

    low, high = x.ph_search_lower, x.ph_search_upper
    f_low, f_high = residual(low), residual(high)
    if not math.isfinite(f_low) or not math.isfinite(f_high) or f_low > 0.0 or f_high < 0.0:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "reason": "measured_alkalinity_not_bracketed",
                "pH_search_bounds": [low, high],
                "alkalinity_residual_at_bounds_mol_L": [f_low, f_high],
            },
            notes=("The declared pH interval does not bracket an aqueous carbonate alkalinity root.",),
        )

    iterations = 0
    if f_low == 0.0:
        ph = low
    elif f_high == 0.0:
        ph = high
    else:
        ph = (low + high) / 2.0
        for iteration in range(1, x.maximum_iterations + 1):
            iterations = iteration
            ph = (low + high) / 2.0
            f_mid = residual(ph)
            if not math.isfinite(f_mid):
                break
            if abs(f_mid) <= x.alkalinity_closure_tolerance_mol_L:
                break
            # Continue past the requested pH bracket width when needed so the
            # independently declared alkalinity closure tolerance is also met.
            if ph == low or ph == high:
                break
            if f_mid < 0.0:
                low = ph
            else:
                high = ph

    state = _carbonate_state(ph, co2star, x.constants)
    closure = state["calculated_alkalinity_mol_L"] - x.measured_total_alkalinity_mol_L
    derivative = state["d_alkalinity_d_pH_mol_L"]
    if not math.isfinite(closure) or abs(closure) > x.alkalinity_closure_tolerance_mol_L:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "sample_id": x.sample_id,
                "reason": "alkalinity_closure_tolerance_not_met",
                "pH_activity": ph,
                "closure_residual_mol_L": closure,
                "iterations": iterations,
            },
            notes=(
                "The requested pH and alkalinity tolerances were not met by the bounded bisection solver.",
            ),
        )

    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "sample_id": x.sample_id,
            "temperature_K": x.temperature_K,
            "co2_fugacity_Pa": x.co2_fugacity_Pa,
            "gas_fugacity_provider_id": x.gas_fugacity_provider_id,
            "gas_fugacity_provider_revision": x.gas_fugacity_provider_revision,
            "gas_fugacity_configuration_digest": x.gas_fugacity_configuration_digest,
            "gas_fugacity_record_digest": x.gas_fugacity_record_digest,
            "sample_solvent_composition_sha256": x.sample_solvent_composition_sha256,
            "henry_coefficient_mol_L_Pa": x.henry.coefficient_mol_L_Pa,
            "henry_provider_id": x.henry.provider_id,
            "henry_provider_revision": x.henry.provider_revision,
            "henry_record_digest": x.henry.record_digest,
            "solvent_composition_sha256": x.henry.solvent_composition_sha256,
            "constants_provider_id": x.constants.constants_provider_id,
            "constants_provider_revision": x.constants.constants_provider_revision,
            "constants_record_digest": x.constants.constants_record_digest,
            "gas_equilibrium_review_id": x.gas_equilibrium_review_id,
            "henry_record_review_id": x.henry_record_review_id,
            "alkalinity_record_review_id": x.alkalinity_record_review_id,
            "ph_activity": ph,
            "co2star_mol_L": state["co2star_mol_L"],
            "hco3_activity": state["hco3_activity"],
            "hco3_mol_L": state["hco3_mol_L"],
            "co3_activity": state["co3_activity"],
            "co3_mol_L": state["co3_mol_L"],
            "h_mol_L": state["h_mol_L"],
            "oh_mol_L": state["oh_mol_L"],
            "measured_total_alkalinity_mol_L": x.measured_total_alkalinity_mol_L,
            "alkalinity_provider_id": x.alkalinity_provider_id,
            "alkalinity_provider_revision": x.alkalinity_provider_revision,
            "alkalinity_configuration_digest": x.alkalinity_configuration_digest,
            "alkalinity_record_digest": x.alkalinity_record_digest,
            "calculated_total_alkalinity_mol_L": state["calculated_alkalinity_mol_L"],
            "alkalinity_closure_residual_mol_L": closure,
            "d_alkalinity_d_pH_mol_L": derivative,
            "expanded_pH_uncertainty_from_alkalinity_only": (
                x.expanded_total_alkalinity_uncertainty_mol_L / derivative if derivative > 0.0 else None
            ),
            "alkalinity_uncertainty_basis": x.alkalinity_uncertainty_basis,
            "iterations": iterations,
            "solver_method": "monotone_bracketed_bisection",
        },
        notes=(
            "A fixed supplied CO2 fugacity and caller-provided Henry solubility coefficient determine aqueous CO2*; a carbonate-only alkalinity balance then determines pH and carbonate species.",
            "The Henry coefficient, gas fugacity, solvent composition, activity coefficients and equilibrium constants are caller-owned and must be valid for the same state.",
            "The alkalinity-only pH uncertainty is a first-order local sensitivity; it excludes gas, Henry, activity, equilibrium-constant and model uncertainties and is not a probability interval.",
            "This fixed-fugacity reservoir model does not conserve a finite gas inventory, calculate a fugacity coefficient, include non-carbonate buffers, or predict corrosion rate, scale, damage, life or acceptance.",
        ),
    )


def fixed_fugacity_carbonate_history(x: FixedFugacityCarbonateHistory) -> Calculation:
    """Evaluate caller-supplied fixed-fugacity carbonate states at exact ordered times."""
    history_digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "history_id": x.history_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "time_basis": x.time_basis,
        "input_sha256": history_digest,
        "time_s": list(x.time_s),
        "point_count": len(x.equilibria),
        "interpolation_performed": False,
        "gas_inventory_conserved": False,
    }
    if len(x.equilibria) > x.maximum_point_evaluations:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "point_evaluation_budget_exceeded",
            "maximum_point_evaluations": x.maximum_point_evaluations,
        })
    if not x.history_clock_and_sample_alignment_reviewed:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": ["history_clock_and_sample_alignment_reviewed"],
        })

    rows = []
    for index, (time_s, request) in enumerate(zip(x.time_s, x.equilibria, strict=True)):
        point = fixed_fugacity_carbonate_equilibrium(request)
        row = {
            "index": index,
            "time_s": time_s,
            "sample_id": request.sample_id,
            "point_input_sha256": canonical_digest(request.model_dump(mode="json")),
            "status": point.status,
            "values": point.values,
            "notes": list(point.notes),
        }
        if point.status != "computed":
            return Calculation(status=point.status, values=base | {
                "completed_sample_count": len(rows),
                "completed_time_s": [item["time_s"] for item in rows],
                "sample_results": rows,
                "failed_sample_index": index,
                "failed_sample_time_s": time_s,
                "failed_sample_id": request.sample_id,
                "failed_sample_status": point.status,
                "failed_sample_values": point.values,
            }, notes=point.notes)
        rows.append(row)

    def column(name: str) -> list:
        return [row["values"][name] for row in rows]

    return Calculation(values=base | {
        "sample_results": rows,
        "sample_ids": [row["sample_id"] for row in rows],
        "temperature_K_history": column("temperature_K"),
        "co2_fugacity_Pa_history": column("co2_fugacity_Pa"),
        "ph_activity_history": column("ph_activity"),
        "co2star_mol_L_history": column("co2star_mol_L"),
        "hco3_mol_L_history": column("hco3_mol_L"),
        "co3_mol_L_history": column("co3_mol_L"),
        "calculated_total_alkalinity_mol_L_history": column("calculated_total_alkalinity_mol_L"),
        "alkalinity_closure_residual_mol_L_history": column("alkalinity_closure_residual_mol_L"),
        "all_points_computed": True,
        "chemistry_interpolation_performed": False,
        "corrosion_rate_inferred": False,
    }, notes=(
        "Each exact caller time point is solved independently using its supplied gas fugacity, Henry coefficient, carbonate constants and measured alkalinity.",
        "No temporal interpolation, gas inventory balance, kinetic coupling, corrosion rate, scale growth or integrity acceptance is inferred.",
        "A failed point stops the history and returns only the fully computed prefix plus the failing point status.",
    ))


def _validate_history_context(request: FixedFugacityCarbonateHistory, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("carbonate-history RunContext must match its asset, location and time basis")


def fixed_fugacity_carbonate_scenario_ensemble(x: FixedFugacityCarbonateEnsemble) -> Calculation:
    missing = [
        name for name in ("scenario_weights_reviewed", "common_sample_scope_reviewed") if not getattr(x, name)
    ]
    if missing:
        return Calculation(
            status="needs_data",
            values={"ensemble_id": x.ensemble_id, "missing_reviews": missing},
        )
    rows = []
    failed = []
    for scenario in x.scenarios:
        result = fixed_fugacity_carbonate_equilibrium(scenario.equilibrium)
        row = {
            "scenario_id": scenario.scenario_id,
            "normalized_weight": scenario.normalized_weight,
            "assessment_status": result.status,
            "scenario_input_digest": canonical_digest(scenario.equilibrium.model_dump(mode="json")),
            "values": result.values,
            "notes": list(result.notes),
        }
        rows.append(row)
        if result.status != "computed":
            failed.append(scenario.scenario_id)
    common = {
        "ensemble_id": x.ensemble_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "sample_id": x.sample_id,
        "exposure_interval_id": x.exposure_interval_id,
        "source_group_id": x.source_group_id,
        "input_distribution_id": x.input_distribution_id,
        "input_distribution_digest": x.input_distribution_digest,
        "weight_meaning": x.weight_meaning,
        "scenario_results": rows,
    }
    if failed:
        return Calculation(
            status=(
                "out_of_scope"
                if all(row["assessment_status"] == "out_of_scope" for row in rows)
                else "needs_data"
            ),
            values={**common, "failed_scenario_ids": failed, "aggregate_returned": False},
            notes=(
                "No partial ensemble statistic is returned when any scenario is unresolved or outside scope.",
            ),
        )
    summaries = {}
    for field in ("ph_activity", "co2star_mol_L", "hco3_mol_L", "co3_mol_L"):
        ordered = sorted((row["values"][field], row["normalized_weight"], row["scenario_id"]) for row in rows)
        cumulative = 0.0
        q05 = q95 = None
        for value, weight, _ in ordered:
            cumulative += weight
            if q05 is None and cumulative >= 0.05:
                q05 = value
            if cumulative >= 0.95:
                q95 = value
                break
        summaries[field] = {
            "minimum": ordered[0][0],
            "maximum": ordered[-1][0],
            "weighted_mean": math.fsum(row["values"][field] * row["normalized_weight"] for row in rows),
            "weighted_quantile_05": q05,
            "weighted_quantile_95": q95,
        }
    return Calculation(
        values={
            **common,
            "scenario_count": len(rows),
            "aggregate_returned": True,
            "summaries": summaries,
            "event_probability_inferred": False,
            "corrosion_rate_inferred": False,
        },
        notes=(
            "Weighted summaries describe only the caller-provided scenario rows and normalized weights.",
            "Weighted quantiles use the smallest observed scenario value whose cumulative mass reaches the requested level; no interpolation is performed.",
            "Scenario weights are not period failure probabilities or corrosion-rate distributions.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "chemistry.fixed_fugacity_carbonate_history",
            FixedFugacityCarbonateHistory,
            fixed_fugacity_carbonate_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "time_basis": "1",
                "time_s[]": "s",
                "temperature_K_history[]": "K",
                "co2_fugacity_Pa_history[]": "Pa",
                "ph_activity_history[]": "1",
                "co2star_mol_L_history[]": "mol/L",
                "hco3_mol_L_history[]": "mol/L",
                "co3_mol_L_history[]": "mol/L",
                "calculated_total_alkalinity_mol_L_history[]": "mol/L",
                "alkalinity_closure_residual_mol_L_history[]": "mol/L",
                "point_count": "count",
            },
            (
                "Solves each caller-supplied fixed-fugacity carbonate/alkalinity state at one exact ordered time point; no interpolation or kinetics are added.",
                "Each point retains independent gas, Henry, solvent, activity-constant and alkalinity lineage; the first failed point stops evaluation and preserves the computed prefix.",
                "The history does not close a finite gas inventory, discover species/phases, predict corrosion, scale, life, failure probability or acceptance.",
            ),
            SOURCE_IDS,
            qualification="user_model",
            context_validator=_validate_history_context,
        ),
        ModelSpec(
            "chemistry.fixed_fugacity_carbonate_scenario_ensemble",
            FixedFugacityCarbonateEnsemble,
            fixed_fugacity_carbonate_scenario_ensemble,
            {
                "ensemble_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "sample_id": "1",
                "exposure_interval_id": "1",
                "source_group_id": "1",
                "input_distribution_id": "1",
                "input_distribution_digest": "1",
                "weight_meaning": "1",
                "scenario_count": "1",
                "aggregate_returned": "1",
                "summaries": "mixed",
                "scenario_results": "mixed",
                "event_probability_inferred": "1",
                "corrosion_rate_inferred": "1",
            },
            (
                "Each row is a complete reviewed fixed-fugacity carbonate-equilibrium case with common sample identity and caller-normalized weights.",
                "All rows must compute before weighted summaries are returned; summaries are descriptive and do not infer probability or corrosion rate.",
            ),
            ("caller_weighted_fixed_fugacity_carbonate_equilibrium_scenarios",),
        ),
        ModelSpec(
            "chemistry.fixed_fugacity_carbonate_equilibrium",
            FixedFugacityCarbonateEquilibrium,
            fixed_fugacity_carbonate_equilibrium,
            {
                "temperature_K": "K",
                "co2_fugacity_Pa": "Pa",
                "henry_coefficient_mol_L_Pa": "mol/L/Pa",
                "ph_activity": "1",
                "co2star_mol_L": "mol/L",
                "hco3_mol_L": "mol/L",
                "co3_mol_L": "mol/L",
                "h_mol_L": "mol/L",
                "oh_mol_L": "mol/L",
                "measured_total_alkalinity_mol_L": "mol/L",
                "calculated_total_alkalinity_mol_L": "mol/L",
                "alkalinity_closure_residual_mol_L": "mol/L",
                "expanded_pH_uncertainty_from_alkalinity_only": "1",
                "iterations": "1",
            },
            (
                "Fixed caller-supplied CO2 fugacity reservoir and Henry coefficient at the sample temperature; carbonate-only aqueous activity equilibrium and total-alkalinity closure.",
                "Caller supplies reviewed fugacity, Henry coefficient, solvent composition, activity constants and all source lineage; no fitted universal corrosion or solubility parameters are bundled.",
            ),
            SOURCE_IDS,
        ),
    ]
