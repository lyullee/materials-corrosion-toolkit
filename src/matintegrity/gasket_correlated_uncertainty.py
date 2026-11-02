"""Correlation-preserving finite scenario envelope for calibrated gasket leakage."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .models.gasket_leakage_calibration import (
    GasketLeakageCalibrationMap,
    _bracket,
)


class GasketLeakageCorrelatedScenario(Contract):
    """One joint realization; dependence is preserved by keeping all fields together."""

    scenario_id: str = Field(min_length=1)
    node_contact_pressure_Pa: tuple[Nonnegative, ...] = Field(min_length=1, max_length=100000)
    common_differential_pressure_Pa: Nonnegative
    node_area_m2: tuple[Positive, ...] = Field(min_length=1, max_length=100000)
    calibration_flux_by_contact_pressure_and_delta: tuple[tuple[Nonnegative, ...], ...] = Field(
        min_length=2, max_length=10000
    )


class GasketLeakageCorrelatedScenarioEnvelope(Contract):
    """Evaluate a finite caller-supplied joint scenario set with no invented distributions."""

    schema_version: Literal["matintegrity.gasket_leakage_correlated_scenario_envelope.v1"] = (
        "matintegrity.gasket_leakage_correlated_scenario_envelope.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: Nonnegative
    node_ids: tuple[str, ...] = Field(min_length=1, max_length=100000)
    calibration: GasketLeakageCalibrationMap
    calibration_provider_id: str = Field(min_length=1)
    calibration_provider_revision: str = Field(min_length=1)
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_provider_id: str = Field(min_length=1)
    scenario_provider_revision: str = Field(min_length=1)
    scenario_set_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenarios: tuple[GasketLeakageCorrelatedScenario, ...] = Field(min_length=1, max_length=100000)
    maximum_scenario_node_evaluations: int = Field(default=2_000_000, ge=1, le=10_000_000)
    maximum_scenario_grid_cells: int = Field(default=2_000_000, ge=1, le=20_000_000)
    evidence: tuple[Evidence, ...] = Field(min_length=2)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    joint_scenario_correlation_reviewed: bool
    scenario_coverage_and_bounds_reviewed: bool
    calibration_and_joint_match_reviewed: bool
    area_partition_and_units_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_joint_scenarios(self):
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("node IDs must be unique")
        scenario_ids = [row.scenario_id for row in self.scenarios]
        if len(set(scenario_ids)) != len(scenario_ids):
            raise ValueError("scenario IDs must be unique")
        if canonical_digest([row.model_dump(mode="json") for row in self.scenarios]) != self.scenario_set_sha256:
            raise ValueError("joint scenario set digest mismatch")
        if not any(row.source_id == self.calibration_provider_id and row.sha256 == self.calibration_record_sha256
                   for row in self.evidence):
            raise ValueError("calibration record digest must be linked to matching Evidence")
        if not any(row.source_id == self.scenario_provider_id and row.sha256 == self.scenario_set_sha256
                   for row in self.evidence):
            raise ValueError("scenario set digest must be linked to matching Evidence")
        if not self.usage_rights_evidence:
            raise ValueError("scenario, calibration and license-use lineage must be documented")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license/rights basis")
        node_count = len(self.node_ids)
        pressure_count = len(self.calibration.rows)
        delta_count = len(self.calibration.differential_pressure_Pa)
        if len(self.scenarios) * node_count > self.maximum_scenario_node_evaluations:
            raise ValueError("joint scenario by node evaluation budget exceeded")
        if len(self.scenarios) * pressure_count * delta_count > self.maximum_scenario_grid_cells:
            raise ValueError("scenario-specific calibration grid budget exceeded")
        for row in self.scenarios:
            if len(row.node_contact_pressure_Pa) != node_count or len(row.node_area_m2) != node_count:
                raise ValueError("each joint scenario must provide pressure and area for every ordered node")
            if len(row.calibration_flux_by_contact_pressure_and_delta) != pressure_count or any(
                len(values) != delta_count for values in row.calibration_flux_by_contact_pressure_and_delta
            ):
                raise ValueError("scenario calibration flux perturbation must match the base calibration grid")
            try:
                area_sum = math.fsum(row.node_area_m2)
            except OverflowError as error:
                raise ValueError("scenario contact area sum must be finite") from error
            if not math.isfinite(area_sum):
                raise ValueError("scenario contact area sum must be finite")
        return self


class GasketLeakageWeightedScenarioMoments(Contract):
    """Descriptive weighted moments over a complete finite joint scenario set."""

    schema_version: Literal["matintegrity.gasket_leakage_weighted_scenario_moments.v1"] = (
        "matintegrity.gasket_leakage_weighted_scenario_moments.v1"
    )
    scenario_envelope: GasketLeakageCorrelatedScenarioEnvelope
    scenario_weights: tuple[Positive, ...] = Field(min_length=1, max_length=100000)
    weight_semantics: Literal["empirical_frequency", "quadrature_weight", "user_declared_weight"]
    weight_provider_id: str = Field(min_length=1)
    weight_provider_revision: str = Field(min_length=1)
    weight_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    weight_evidence: Evidence
    weight_usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    weight_usage_license_id: str = Field(min_length=1)
    weight_meaning_reviewed: bool
    weight_usage_rights_reviewed: bool
    weight_computational_use_authorized: bool

    @model_validator(mode="after")
    def complete_weight_contract(self):
        if len(self.scenario_weights) != len(self.scenario_envelope.scenarios):
            raise ValueError("one strictly positive weight is required for each ordered scenario")
        try:
            weight_sum = math.fsum(self.scenario_weights)
        except OverflowError as error:
            raise ValueError("scenario weight sum must be finite") from error
        if not math.isfinite(weight_sum) or not math.isclose(weight_sum, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("scenario weights must already sum to one; silent normalization is not applied")
        if (self.weight_evidence.source_id, self.weight_evidence.sha256) != (
            self.weight_provider_id, self.weight_record_sha256
        ):
            raise ValueError("weight provider and source digest must match the selected Evidence record")
        if not any(
            row.license_id == self.weight_usage_license_id
            for row in self.weight_usage_rights_evidence
        ):
            raise ValueError("weight usage-rights Evidence must identify the declared license/rights basis")
        return self


class GasketLeakageCovariancePropagation(Contract):
    """First-order uncertainty propagation for one caller-defined joint state."""

    schema_version: Literal["matintegrity.gasket_leakage_covariance_propagation.v1"] = (
        "matintegrity.gasket_leakage_covariance_propagation.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: Nonnegative
    node_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    node_contact_pressure_Pa: tuple[Nonnegative, ...]
    common_differential_pressure_Pa: Nonnegative
    node_area_m2: tuple[Positive, ...]
    calibration: GasketLeakageCalibrationMap
    calibration_provider_id: str = Field(min_length=1)
    input_covariance: tuple[tuple[float, ...], ...] = Field(min_length=1, max_length=2049)
    input_covariance_order: Literal[
        "node_contact_pressure_Pa_then_common_differential_pressure_Pa_then_node_area_m2_then_row_major_flux"
    ] = "node_contact_pressure_Pa_then_common_differential_pressure_Pa_then_node_area_m2_then_row_major_flux"
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scenario_provider_id: str = Field(min_length=1)
    scenario_provider_revision: str = Field(min_length=1)
    scenario_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    covariance_provider_id: str = Field(min_length=1)
    covariance_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=3)
    calibration_scope_and_units_reviewed: bool
    covariance_order_units_and_estimation_reviewed: bool
    local_linearization_and_support_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_covariance(self):
        n = len(self.node_ids)
        if len(set(self.node_ids)) != n or len(self.node_contact_pressure_Pa) != n or len(self.node_area_m2) != n:
            raise ValueError("node IDs, pressures and areas must be unique/aligned")
        m, k = len(self.calibration.rows), len(self.calibration.differential_pressure_Pa)
        dimension = 2 * n + 1 + m * k
        if dimension > 2049 or len(self.input_covariance) != dimension or any(
            len(row) != dimension for row in self.input_covariance
        ):
            raise ValueError("covariance matrix dimensions do not match the declared input ordering")
        if not any(e.source_id == self.scenario_provider_id and e.sha256 == self.scenario_record_sha256 for e in self.evidence):
            raise ValueError("scenario state digest must be linked to Evidence")
        if not any(e.sha256 == self.calibration_record_sha256 for e in self.evidence):
            raise ValueError("calibration record digest must be linked to Evidence")
        if not any(e.source_id == self.calibration_provider_id and e.sha256 == self.calibration_record_sha256 for e in self.evidence):
            raise ValueError("calibration provider and digest must be linked to the same Evidence record")
        if not any(e.source_id == self.covariance_provider_id and e.sha256 == self.covariance_record_sha256 for e in self.evidence):
            raise ValueError("covariance provider and digest must be linked to the same Evidence record")
        if not any(e.license_id == self.usage_license_id for e in self.evidence):
            raise ValueError("usage license must be linked to Evidence")
        matrix = self.input_covariance
        if any(not math.isfinite(v) for row in matrix for v in row):
            raise ValueError("covariance entries must be finite")
        if any(not math.isclose(matrix[i][j], matrix[j][i], rel_tol=1e-10, abs_tol=1e-18)
               for i in range(dimension) for j in range(i + 1, dimension)):
            raise ValueError("covariance matrix must be symmetric")
        import numpy as np
        covariance = np.asarray(matrix, dtype=float)
        variances = np.diag(covariance)
        if np.any(variances < 0):
            raise ValueError("covariance diagonal variances must be nonnegative")
        standard_deviations = np.sqrt(variances)
        correlation = np.zeros_like(covariance)
        active = standard_deviations > 0
        scale_matrix = np.outer(standard_deviations, standard_deviations)
        correlation[active[:, None] & active[None, :]] = (
            covariance[active[:, None] & active[None, :]] / scale_matrix[active[:, None] & active[None, :]]
        )
        if np.any(covariance[~(active[:, None] & active[None, :])] != 0.0):
            raise ValueError("zero-variance inputs must have zero covariance with all variables")
        eigenvalues = np.linalg.eigvalsh(correlation)
        if float(np.min(eigenvalues)) < -1e-10:
            raise ValueError("input covariance matrix must be positive semidefinite")
        return self


def evaluate_gasket_leakage_covariance(request: GasketLeakageCovariancePropagation) -> Calculation:
    """Propagate caller covariance through the local bilinear leakage map."""
    base = {
        "assessment_id": request.assessment_id, "asset_id": request.asset_id,
        "joint_id": request.joint_id, "physical_scope_id": request.physical_scope_id,
        "time_s": request.time_s, "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "covariance_sha256": request.covariance_record_sha256,
        "covariance_provider_id": request.covariance_provider_id,
        "calibration_provider_id": request.calibration_provider_id,
        "calibration_sha256": request.calibration_record_sha256,
        "usage_license_id": request.usage_license_id,
        "input_covariance_order": request.input_covariance_order,
        "uncertainty_semantics": "first_order_delta_method_at_one_nominal_state",
    }
    reviews = (request.calibration_scope_and_units_reviewed, request.covariance_order_units_and_estimation_reviewed,
               request.local_linearization_and_support_reviewed, request.usage_rights_reviewed,
               request.computational_use_authorized)
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {"reason": "Required review and use gates are incomplete"})
    n = len(request.node_ids)
    contact_knots = tuple(row.contact_pressure_Pa for row in request.calibration.rows)
    delta_knots = request.calibration.differential_pressure_Pa
    delta = request.common_differential_pressure_Pa
    jacobian = [0.0] * len(request.input_covariance)
    node_rows = []
    try:
        for i, (node_id, pressure, area) in enumerate(zip(
            request.node_ids, request.node_contact_pressure_Pa, request.node_area_m2, strict=True
        )):
            pi, pf = _bracket(contact_knots, pressure)
            di, df = _bracket(delta_knots, delta)
            if pressure in contact_knots or delta in delta_knots:
                raise ValueError("nominal state lies on a calibration knot or support boundary; local uncertainty may leave support")
            grid = tuple(row.molar_leak_flux_by_delta_pressure_mol_s_m2 for row in request.calibration.rows)
            q00, q01, q10, q11 = grid[pi][di], grid[pi][di+1], grid[pi+1][di], grid[pi+1][di+1]
            qlow = q00 + df * (q01-q00); qhigh = q10 + df * (q11-q10)
            flux = qlow + pf * (qhigh-qlow)
            dp = contact_knots[pi+1]-contact_knots[pi]; dd = delta_knots[di+1]-delta_knots[di]
            dflux_dp = ((1-df)*(q10-q00) + df*(q11-q01))/dp
            dflux_dd = ((1-pf)*(q01-q00) + pf*(q11-q10))/dd
            jacobian[i] = area*dflux_dp
            jacobian[n] += area*dflux_dd
            jacobian[n+1+i] = flux
            g0 = 2*n + 1 + pi*len(delta_knots) + di
            weights = ((1-pf)*(1-df), (1-pf)*df, pf*(1-df), pf*df)
            for offset, weight in zip((0, 1, len(delta_knots), len(delta_knots)+1), weights, strict=True):
                jacobian[g0+offset] += area*weight
            node_rows.append({"node_id": node_id, "nominal_flux_mol_s_m2": flux,
                              "nominal_leak_rate_mol_s": area*flux,
                              "contact_pressure_derivative_mol_s_Pa": area*dflux_dp,
                              "area_derivative_mol_s_m2": flux,
                              "interpolation_cell": {"contact_pressure_lower_index": pi,
                                                     "differential_pressure_lower_index": di}})
        nominal = math.fsum(row["nominal_leak_rate_mol_s"] for row in node_rows)
        variance = math.fsum(jacobian[i]*request.input_covariance[i][j]*jacobian[j]
                             for i in range(len(jacobian)) for j in range(len(jacobian)))
        if variance < -1e-10*max(1.0, abs(nominal)):
            raise ValueError("propagated variance is materially negative")
        variance = max(0.0, variance)
        if not math.isfinite(nominal) or not math.isfinite(variance):
            raise ValueError("nominal leakage or propagated variance is non-finite")
    except (ValueError, OverflowError, IndexError) as error:
        return Calculation(status="out_of_scope", values=base | {"reason": str(error)})
    return Calculation(values=base | {
        "nominal_molar_leak_rate_mol_s": nominal,
        "first_order_variance_mol2_s2": variance,
        "first_order_standard_uncertainty_mol_s": math.sqrt(variance),
        "jacobian": jacobian,
        "node_responses": node_rows,
        "jacobian_sha256": canonical_digest(jacobian),
    }, notes=(
        "Uses the caller-provided joint covariance in the documented vector order and a local first-order delta method.",
        "Nominal values must lie strictly inside calibration cells; this is not a probability interval or nonlinear uncertainty bound.",
    ))


def evaluate_gasket_leakage_correlated_scenarios(
    request: GasketLeakageCorrelatedScenarioEnvelope,
) -> Calculation:
    """Return min/max among complete joint scenarios; values are not probabilities or continuous bounds."""
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "joint_id": request.joint_id,
        "physical_scope_id": request.physical_scope_id,
        "time_s": request.time_s,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "calibration_record_sha256": request.calibration_record_sha256,
        "calibration_map_sha256": canonical_digest(request.calibration.model_dump(mode="json")),
        "scenario_set_sha256": request.scenario_set_sha256,
        "scenario_provider_id": request.scenario_provider_id,
        "scenario_provider_revision": request.scenario_provider_revision,
        "usage_license_id": request.usage_license_id,
        "calibration_provider_id": request.calibration_provider_id,
        "calibration_provider_revision": request.calibration_provider_revision,
        "node_ids": list(request.node_ids),
        "usage_rights_evidence_sha256": canonical_digest(
            [row.model_dump(mode="json") for row in request.usage_rights_evidence]
        ),
        "maximum_scenario_node_evaluations": request.maximum_scenario_node_evaluations,
        "maximum_scenario_grid_cells": request.maximum_scenario_grid_cells,
        "uncertainty_semantics": "finite_caller_supplied_joint_scenarios_without_probability_weights",
    }
    reviews = {
        "joint_scenario_correlation_reviewed": request.joint_scenario_correlation_reviewed,
        "scenario_coverage_and_bounds_reviewed": request.scenario_coverage_and_bounds_reviewed,
        "calibration_and_joint_match_reviewed": request.calibration_and_joint_match_reviewed,
        "area_partition_and_units_reviewed": request.area_partition_and_units_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, passed in reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    contact_knots = tuple(row.contact_pressure_Pa for row in request.calibration.rows)
    scenario_rows = []
    try:
        for scenario in request.scenarios:
            contributions = []
            node_results = []
            for index, node_id in enumerate(request.node_ids):
                contact_pressure = scenario.node_contact_pressure_Pa[index]
                differential_pressure = scenario.common_differential_pressure_Pa
                contact_index, contact_fraction = _bracket(contact_knots, contact_pressure)
                delta_index, delta_fraction = _bracket(
                    request.calibration.differential_pressure_Pa, differential_pressure
                )
                grid = scenario.calibration_flux_by_contact_pressure_and_delta
                q00 = grid[contact_index][delta_index]
                q01 = grid[contact_index][delta_index + 1]
                q10 = grid[contact_index + 1][delta_index]
                q11 = grid[contact_index + 1][delta_index + 1]
                low = q00 + delta_fraction * (q01 - q00)
                high = q10 + delta_fraction * (q11 - q10)
                flux = low + contact_fraction * (high - low)
                rate = flux * scenario.node_area_m2[index]
                if not math.isfinite(rate):
                    raise ValueError("scenario node leakage contribution exceeded finite support")
                contributions.append(rate)
                node_results.append({
                    "node_id": node_id,
                    "contact_pressure_Pa": contact_pressure,
                    "contact_area_m2": scenario.node_area_m2[index],
                    "calibrated_molar_leak_flux_mol_s_m2": flux,
                    "molar_leak_rate_contribution_mol_s": rate,
                    "interpolation_cell": {
                        "contact_pressure_lower_index": contact_index,
                        "differential_pressure_lower_index": delta_index,
                    },
                })
            total = math.fsum(contributions)
            if not math.isfinite(total):
                raise ValueError("scenario total leakage rate exceeded finite support")
            scenario_rows.append({
                "scenario_id": scenario.scenario_id,
                "common_differential_pressure_Pa": scenario.common_differential_pressure_Pa,
                "molar_leak_rate_mol_s": total,
                "node_responses": node_results,
                "calibration_flux_sha256": canonical_digest(scenario.calibration_flux_by_contact_pressure_and_delta),
            })
    except (ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error),
            "completed_scenario_count": len(scenario_rows),
            "completed_scenarios": scenario_rows,
        }, notes=("A joint scenario outside calibrated pressure or finite numeric support is not extrapolated.",))

    minimum = min(scenario_rows, key=lambda row: row["molar_leak_rate_mol_s"])
    maximum = max(scenario_rows, key=lambda row: row["molar_leak_rate_mol_s"])
    return Calculation(values=base | {
        "scenario_results": scenario_rows,
        "scenario_results_sha256": canonical_digest(scenario_rows),
        "minimum_scenario_molar_leak_rate_mol_s": minimum["molar_leak_rate_mol_s"],
        "minimum_witness_scenario_id": minimum["scenario_id"],
        "maximum_scenario_molar_leak_rate_mol_s": maximum["molar_leak_rate_mol_s"],
        "maximum_witness_scenario_id": maximum["scenario_id"],
        "scenario_count": len(scenario_rows),
        "calibration_uncertainty_included": True,
        "node_area_uncertainty_included": True,
        "pressure_correlation_preserved": True,
        "meaning": "exact extrema over the finite supplied joint scenario set only; not a probability, confidence interval, or continuous uncertainty-set bound",
    }, notes=(
        "Each scenario jointly supplies all node pressures, shared differential pressure, node areas and calibration-grid fluxes; these correlated values are never independently recombined.",
        "Piecewise-bilinear interpolation is evaluated only inside the fixed calibration axes. Reported extrema cover the enumerated scenarios only.",
        "No probability weights, Gaussian assumptions, covariance extrapolation, temporal integration or seal acceptance are inferred.",
    ))


def evaluate_gasket_leakage_weighted_scenario_moments(
    request: GasketLeakageWeightedScenarioMoments,
) -> Calculation:
    """Evaluate exact scenario leakage first, then summarize supplied finite weights descriptively."""
    base = {
        "assessment_id": request.scenario_envelope.assessment_id,
        "asset_id": request.scenario_envelope.asset_id,
        "joint_id": request.scenario_envelope.joint_id,
        "physical_scope_id": request.scenario_envelope.physical_scope_id,
        "time_s": request.scenario_envelope.time_s,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "scenario_set_sha256": request.scenario_envelope.scenario_set_sha256,
        "scenario_count": len(request.scenario_weights),
        "scenario_weights": list(request.scenario_weights),
        "weight_semantics": request.weight_semantics,
        "weight_provider_id": request.weight_provider_id,
        "weight_provider_revision": request.weight_provider_revision,
        "weight_record_sha256": request.weight_record_sha256,
        "weight_usage_license_id": request.weight_usage_license_id,
        "uncertainty_semantics": "descriptive_weighted_moments_over_the_finite_caller_supplied_joint_scenario_set",
        "probability_or_confidence_claim": False,
    }
    missing = [
        name for name, passed in (
            ("weight_meaning_reviewed", request.weight_meaning_reviewed),
            ("weight_usage_rights_reviewed", request.weight_usage_rights_reviewed),
            ("weight_computational_use_authorized", request.weight_computational_use_authorized),
        ) if not passed
    ]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    scenario_result = evaluate_gasket_leakage_correlated_scenarios(request.scenario_envelope)
    if scenario_result.status != "computed":
        return Calculation(
            status=scenario_result.status,
            values=base | {"scenario_evaluation": scenario_result.model_dump(mode="json")},
        )
    try:
        rows = scenario_result.values["scenario_results"]
        if len(rows) != len(request.scenario_weights) or [
            row["scenario_id"] for row in rows
        ] != [row.scenario_id for row in request.scenario_envelope.scenarios]:
            raise ValueError("computed scenario results do not match the ordered weighted manifest")
        rates = [float(row["molar_leak_rate_mol_s"]) for row in rows]
        mean = math.fsum(weight * rate for weight, rate in zip(request.scenario_weights, rates, strict=True))
        variance = math.fsum(
            weight * (rate - mean) ** 2
            for weight, rate in zip(request.scenario_weights, rates, strict=True)
        )
        standard_deviation = math.sqrt(variance)
        if not all(math.isfinite(value) for value in (mean, variance, standard_deviation)):
            raise ValueError("weighted scenario moments exceed finite numeric support")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error)})
    minimum_index = min(range(len(rates)), key=rates.__getitem__)
    maximum_index = max(range(len(rates)), key=rates.__getitem__)
    return Calculation(values=base | {
        "scenario_results_sha256": scenario_result.values["scenario_results_sha256"],
        "weighted_mean_molar_leak_rate_mol_s": mean,
        "weighted_population_variance_mol2_s2": variance,
        "weighted_standard_deviation_mol_s": standard_deviation,
        "minimum_molar_leak_rate_mol_s": rates[minimum_index],
        "minimum_witness_scenario_id": rows[minimum_index]["scenario_id"],
        "maximum_molar_leak_rate_mol_s": rates[maximum_index],
        "maximum_witness_scenario_id": rows[maximum_index]["scenario_id"],
        "scenario_results": rows,
        "correlation_preserved_within_each_scenario": True,
        "scenario_results_are_finite_caller_support_only": True,
        "moment_definition": "weighted_population_moments_of_the_ordered_finite_scenario_rates; no Bessel correction",
    }, notes=(
        "Leakage is evaluated for each complete joint scenario before applying its matched caller weight.",
        "Weights summarize only the supplied finite scenario set; they are not converted into failure probability, confidence, or a continuous bound.",
    ))



class GasketLeakageBoxNode(Contract):
    node_id: str = Field(min_length=1)
    minimum_contact_pressure_Pa: Nonnegative
    maximum_contact_pressure_Pa: Nonnegative
    minimum_area_m2: Positive
    maximum_area_m2: Positive

    @model_validator(mode="after")
    def ordered_node_bounds(self):
        if self.maximum_contact_pressure_Pa < self.minimum_contact_pressure_Pa:
            raise ValueError("contact-pressure bounds must be ordered")
        if self.maximum_area_m2 < self.minimum_area_m2:
            raise ValueError("contact-area bounds must be ordered")
        return self


class GasketLeakageBoxEnvelope(Contract):
    """Deterministic total-leak bounds over a caller-declared rectangular input set."""

    schema_version: Literal["matintegrity.gasket_leakage_box_envelope.v1"] = (
        "matintegrity.gasket_leakage_box_envelope.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: Nonnegative
    calibration: GasketLeakageCalibrationMap
    nodes: tuple[GasketLeakageBoxNode, ...] = Field(min_length=1, max_length=256)
    minimum_differential_pressure_Pa: Nonnegative
    maximum_differential_pressure_Pa: Nonnegative
    calibration_flux_lower_bound_mol_s_m2: tuple[tuple[Nonnegative, ...], ...] = Field(min_length=2, max_length=10000)
    calibration_flux_upper_bound_mol_s_m2: tuple[tuple[Nonnegative, ...], ...] = Field(min_length=2, max_length=10000)
    calibration_provider_id: str = Field(min_length=1)
    calibration_provider_revision: str = Field(min_length=1)
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bound_provider_id: str = Field(min_length=1)
    bound_provider_revision: str = Field(min_length=1)
    bound_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_candidate_evaluations: int = Field(default=2_000_000, ge=1, le=10_000_000)
    evidence: tuple[Evidence, ...] = Field(min_length=2)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    calibration_and_bound_records_reviewed: bool
    box_uncertainty_set_and_independence_scope_reviewed: bool
    pressure_area_units_and_physical_mapping_reviewed: bool
    box_covers_intended_operating_uncertainty_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_box_contract(self):
        if len({node.node_id for node in self.nodes}) != len(self.nodes):
            raise ValueError("box node identifiers must be unique")
        if self.maximum_differential_pressure_Pa < self.minimum_differential_pressure_Pa:
            raise ValueError("differential-pressure bounds must be ordered")
        row_count = len(self.calibration.rows)
        delta_count = len(self.calibration.differential_pressure_Pa)
        for matrix_name, matrix in (("lower", self.calibration_flux_lower_bound_mol_s_m2),
                                    ("upper", self.calibration_flux_upper_bound_mol_s_m2)):
            if len(matrix) != row_count or any(len(row) != delta_count for row in matrix):
                raise ValueError(f"calibration {matrix_name} flux bound must match the complete table shape")
        for i in range(row_count):
            for j in range(delta_count):
                lower = self.calibration_flux_lower_bound_mol_s_m2[i][j]
                nominal = self.calibration.rows[i].molar_leak_flux_by_delta_pressure_mol_s_m2[j]
                upper = self.calibration_flux_upper_bound_mol_s_m2[i][j]
                if lower > nominal or nominal > upper:
                    raise ValueError("every flux interval must contain its pinned calibration value")
        evidence = {(row.source_id, row.sha256) for row in self.evidence}
        if (self.calibration_provider_id, self.calibration_record_sha256) not in evidence:
            raise ValueError("calibration record must match Evidence")
        if (self.bound_provider_id, self.bound_record_sha256) not in evidence:
            raise ValueError("box-bound record must match Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage rights Evidence must match the declared license identifier")
        contact_candidates = sum(
            2 + sum(node.minimum_contact_pressure_Pa < row.contact_pressure_Pa < node.maximum_contact_pressure_Pa
                    for row in self.calibration.rows)
            for node in self.nodes
        )
        delta_candidates = 2 + sum(
            self.minimum_differential_pressure_Pa < value < self.maximum_differential_pressure_Pa
            for value in self.calibration.differential_pressure_Pa
        )
        if contact_candidates * delta_candidates > self.maximum_candidate_evaluations:
            raise ValueError("box-envelope candidate evaluation budget is insufficient")
        return self


def _interpolate_grid(grid, contact_knots, delta_knots, contact_pressure, differential_pressure):
    i, pf = _bracket(contact_knots, contact_pressure)
    j, df = _bracket(delta_knots, differential_pressure)
    q00, q01 = grid[i][j], grid[i][j + 1]
    q10, q11 = grid[i + 1][j], grid[i + 1][j + 1]
    low = q00 + df * (q01 - q00)
    high = q10 + df * (q11 - q10)
    return low + pf * (high - low), {"contact_pressure_lower_index": i, "differential_pressure_lower_index": j}


def evaluate_gasket_leakage_box_envelope(request: GasketLeakageBoxEnvelope) -> Calculation:
    """Compute exact extrema for the independent rectangular box and bilinear map."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id, "asset_id": request.asset_id,
        "joint_id": request.joint_id, "physical_scope_id": request.physical_scope_id,
        "time_s": request.time_s, "input_sha256": input_sha,
        "calibration_provider_id": request.calibration_provider_id,
        "calibration_provider_revision": request.calibration_provider_revision,
        "calibration_record_sha256": request.calibration_record_sha256,
        "bound_provider_id": request.bound_provider_id,
        "bound_provider_revision": request.bound_provider_revision,
        "bound_record_sha256": request.bound_record_sha256,
        "usage_license_id": request.usage_license_id,
        "uncertainty_semantics": "deterministic_extrema_over_declared_independent_rectangular_box",
        "probability_or_confidence_claim": False,
    }
    reviews = {
        "calibration_and_bound_records_reviewed": request.calibration_and_bound_records_reviewed,
        "box_uncertainty_set_and_independence_scope_reviewed": request.box_uncertainty_set_and_independence_scope_reviewed,
        "pressure_area_units_and_physical_mapping_reviewed": request.pressure_area_units_and_physical_mapping_reviewed,
        "box_covers_intended_operating_uncertainty_reviewed": request.box_covers_intended_operating_uncertainty_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, passed in reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    contact_knots = tuple(row.contact_pressure_Pa for row in request.calibration.rows)
    delta_knots = request.calibration.differential_pressure_Pa
    pressure_bounds = [(node.minimum_contact_pressure_Pa, node.maximum_contact_pressure_Pa) for node in request.nodes]
    if (request.minimum_differential_pressure_Pa < delta_knots[0]
            or request.maximum_differential_pressure_Pa > delta_knots[-1]
            or any(lo < contact_knots[0] or hi > contact_knots[-1] for lo, hi in pressure_bounds)):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "declared_box_exceeds_calibration_support_no_extrapolation",
            "calibration_contact_pressure_support_Pa": [contact_knots[0], contact_knots[-1]],
            "calibration_differential_pressure_support_Pa": [delta_knots[0], delta_knots[-1]],
        })

    delta_candidates = sorted({
        request.minimum_differential_pressure_Pa, request.maximum_differential_pressure_Pa,
        *(value for value in delta_knots if request.minimum_differential_pressure_Pa < value < request.maximum_differential_pressure_Pa),
    })
    lower_grid = request.calibration_flux_lower_bound_mol_s_m2
    upper_grid = request.calibration_flux_upper_bound_mol_s_m2
    evaluations = 0
    minimum_witnesses = []
    maximum_witnesses = []
    minimum_rate_by_delta = []
    maximum_rate_by_delta = []
    try:
        for differential_pressure in delta_candidates:
            low_total_terms = []
            high_total_terms = []
            low_nodes = []
            high_nodes = []
            for node in request.nodes:
                pressure_candidates = sorted({
                    node.minimum_contact_pressure_Pa, node.maximum_contact_pressure_Pa,
                    *(value for value in contact_knots if node.minimum_contact_pressure_Pa < value < node.maximum_contact_pressure_Pa),
                })
                candidates = []
                for pressure in pressure_candidates:
                    lower_flux, lower_cell = _interpolate_grid(
                        lower_grid, contact_knots, delta_knots, pressure, differential_pressure
                    )
                    upper_flux, upper_cell = _interpolate_grid(
                        upper_grid, contact_knots, delta_knots, pressure, differential_pressure
                    )
                    candidates.append((pressure, lower_flux, upper_flux, lower_cell, upper_cell))
                    evaluations += 1
                    if evaluations > request.maximum_candidate_evaluations:
                        raise ValueError("box-envelope evaluation budget exceeded")
                low_choice = min(candidates, key=lambda item: item[1])
                high_choice = max(candidates, key=lambda item: item[2])
                low_total_terms.append(node.minimum_area_m2 * low_choice[1])
                high_total_terms.append(node.maximum_area_m2 * high_choice[2])
                low_nodes.append({
                    "node_id": node.node_id, "contact_pressure_Pa": low_choice[0],
                    "area_m2": node.minimum_area_m2, "leak_flux_mol_s_m2": low_choice[1],
                    "rate_mol_s": node.minimum_area_m2 * low_choice[1], "interpolation_cell": low_choice[3],
                })
                high_nodes.append({
                    "node_id": node.node_id, "contact_pressure_Pa": high_choice[0],
                    "area_m2": node.maximum_area_m2, "leak_flux_mol_s_m2": high_choice[2],
                    "rate_mol_s": node.maximum_area_m2 * high_choice[2], "interpolation_cell": high_choice[4],
                })
            low_total = math.fsum(low_total_terms)
            high_total = math.fsum(high_total_terms)
            if not math.isfinite(low_total) or not math.isfinite(high_total):
                raise ValueError("box leakage extrema exceeded finite numeric support")
            minimum_rate_by_delta.append({"differential_pressure_Pa": differential_pressure, "rate_mol_s": low_total})
            maximum_rate_by_delta.append({"differential_pressure_Pa": differential_pressure, "rate_mol_s": high_total})
            minimum_witnesses.append({"differential_pressure_Pa": differential_pressure, "rate_mol_s": low_total, "node_responses": low_nodes})
            maximum_witnesses.append({"differential_pressure_Pa": differential_pressure, "rate_mol_s": high_total, "node_responses": high_nodes})
    except (ValueError, OverflowError, IndexError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error), "completed_candidate_count": evaluations,
        })

    minimum = min(minimum_witnesses, key=lambda row: row["rate_mol_s"])
    maximum = max(maximum_witnesses, key=lambda row: row["rate_mol_s"])
    return Calculation(values=base | {
        "minimum_molar_leak_rate_mol_s": minimum["rate_mol_s"],
        "maximum_molar_leak_rate_mol_s": maximum["rate_mol_s"],
        "minimum_witness": minimum, "maximum_witness": maximum,
        "minimum_rate_by_common_differential_pressure": minimum_rate_by_delta,
        "maximum_rate_by_common_differential_pressure": maximum_rate_by_delta,
        "candidate_evaluation_count": evaluations,
        "candidate_pressure_rule": "node_bounds_and_all_contact_pressure_knots_inside_each_node_interval",
        "candidate_differential_pressure_rule": "box_endpoints_and_all_calibration_knots_inside_box",
        "calibration_flux_interval_semantics": "independent_entrywise_bounds_with_nominal_table_inside_each_interval",
        "bound_exactness": "exact_for_the_declared_independent_box_and_piecewise_bilinear_table",
    }, notes=(
        "Extrema are attained over the declared rectangular set by evaluating contact-pressure endpoints/table knots and common differential-pressure endpoints/table knots; nonnegative bilinear weights make entrywise calibration limits monotone.",
        "The rectangular-set independence assumption is explicit and supplies no probability, confidence, covariance, physical seal acceptance or extrapolation claim.",
    ))

def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_correlated_scenario_envelope",
        GasketLeakageCorrelatedScenarioEnvelope,
        evaluate_gasket_leakage_correlated_scenarios,
        {
            "minimum_scenario_molar_leak_rate_mol_s": "mol/s",
            "maximum_scenario_molar_leak_rate_mol_s": "mol/s",
            "scenario_results[].molar_leak_rate_mol_s": "mol/s",
        },
        (
            "Evaluate leakage only over complete caller-supplied joint scenarios that preserve dependence among node pressure, common differential pressure, area and calibration-grid variation.",
            "Bounds are exact only over the finite scenario set, use no probability weights, and do not establish a continuous uncertainty bound or seal acceptance.",
        ),
        ("caller_correlated_gasket_leakage_joint_scenario_envelope",),
        qualification="user_model",
    ), ModelSpec(
        "fabrication.gasket_leakage_covariance_propagation",
        GasketLeakageCovariancePropagation,
        evaluate_gasket_leakage_covariance,
        {"nominal_molar_leak_rate_mol_s": "mol/s",
         "first_order_standard_uncertainty_mol_s": "mol/s",
         "first_order_variance_mol2_s2": "mol^2/s^2"},
        ("A caller-supplied symmetric positive-semidefinite covariance is propagated through the local piecewise-bilinear calibrated leakage map.",
         "This is a first-order local uncertainty estimate, not a nonlinear interval or probability guarantee."),
        ("caller_joint_gasket_leakage_covariance_delta_method",),
        qualification="user_model",
    ), ModelSpec(
        "fabrication.gasket_leakage_box_envelope",
        GasketLeakageBoxEnvelope,
        evaluate_gasket_leakage_box_envelope,
        {"minimum_molar_leak_rate_mol_s": "mol/s", "maximum_molar_leak_rate_mol_s": "mol/s"},
        (
            "Returns deterministic extrema over caller-specified independent pressure, area and calibration-flux intervals using the piecewise-bilinear map without extrapolation.",
            "Exactness applies only to the declared rectangular input set; no probability, covariance, correlated uncertainty or seal acceptance is inferred.",
        ),
        ("caller_gasket_leakage_independent_box_envelope",),
        qualification="user_model",
    ), ModelSpec(
        "fabrication.gasket_leakage_weighted_scenario_moments",
        GasketLeakageWeightedScenarioMoments,
        evaluate_gasket_leakage_weighted_scenario_moments,
        {
            "weighted_mean_molar_leak_rate_mol_s": "mol/s",
            "weighted_population_variance_mol2_s2": "mol^2/s^2",
            "weighted_standard_deviation_mol_s": "mol/s",
        },
        (
            "Evaluate the calibrated leakage response within each complete correlated scenario, then compute descriptive finite-set moments using caller-supplied ordered weights.",
            "Weights are not converted into event probabilities, confidence intervals or continuous uncertainty bounds; use only the explicitly reviewed weight semantics and finite scenario manifest.",
        ),
        ("caller_weighted_gasket_leakage_joint_scenario_moments",),
        qualification="user_model",
    )]
