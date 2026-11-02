"""Descriptive input/response dependence over a complete finite gasket scenario set."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, canonical_digest
from ..gasket_correlated_uncertainty import (
    GasketLeakageWeightedScenarioMoments,
    evaluate_gasket_leakage_weighted_scenario_moments,
)
from ..registry import ModelSpec

SOURCE_ID = "caller_finite_gasket_joint_scenario_dependence"


class GasketFiniteScenarioDependence(Contract):
    schema_version: Literal["matintegrity.gasket_finite_scenario_dependence.v1"] = (
        "matintegrity.gasket_finite_scenario_dependence.v1"
    )
    weighted_scenarios: GasketLeakageWeightedScenarioMoments
    selected_node_ids: tuple[str, ...] = Field(min_length=1, max_length=16)
    maximum_scenario_variable_pairs: int = Field(default=5000000, ge=1, le=100000000)
    finite_set_dependence_and_variable_units_reviewed: bool
    descriptive_covariance_not_causal_or_population_inference_reviewed: bool

    @model_validator(mode="after")
    def aligned_selection_and_budget(self):
        selected = self.selected_node_ids
        if len(set(selected)) != len(selected) or any(not value.strip() for value in selected):
            raise ValueError("selected node IDs must be nonempty and unique")
        if not set(selected).issubset(self.weighted_scenarios.scenario_envelope.node_ids):
            raise ValueError("every selected node must occur in the scenario envelope")
        dimension = 3 + 3 * len(selected)
        pairs = dimension * (dimension + 1) // 2
        if pairs * len(self.weighted_scenarios.scenario_weights) > self.maximum_scenario_variable_pairs:
            raise ValueError("finite scenario/variable-pair budget exceeded")
        return self


def gasket_finite_scenario_dependence(x: GasketFiniteScenarioDependence) -> Calculation:
    weighted = x.weighted_scenarios
    envelope = weighted.scenario_envelope
    base = {"assessment_id": envelope.assessment_id, "asset_id": envelope.asset_id,
            "joint_id": envelope.joint_id, "physical_scope_id": envelope.physical_scope_id,
            "time_s": envelope.time_s, "input_sha256": canonical_digest(x.model_dump(mode="json")),
            "weighted_scenario_input_sha256": canonical_digest(weighted.model_dump(mode="json")),
            "scenario_set_sha256": envelope.scenario_set_sha256,
            "weight_record_sha256": weighted.weight_record_sha256,
            "selected_node_ids": list(x.selected_node_ids), "probability_or_causal_inference": False}
    if not (x.finite_set_dependence_and_variable_units_reviewed and
            x.descriptive_covariance_not_causal_or_population_inference_reviewed):
        return Calculation(status="needs_data", values=base)
    upstream = evaluate_gasket_leakage_weighted_scenario_moments(weighted)
    base["weighted_scenario_result_sha256"] = canonical_digest(upstream.model_dump(mode="json"))
    if upstream.status != "computed":
        return Calculation(status=upstream.status, values=base | {"upstream": upstream.model_dump(mode="json")})
    rows = upstream.values["scenario_results"]
    expected_ids = [s.scenario_id for s in envelope.scenarios]
    if [r["scenario_id"] for r in rows] != expected_ids:
        return Calculation(status="out_of_scope", values=base | {"reason": "upstream_scenario_order_mismatch"})
    indices = [envelope.node_ids.index(node_id) for node_id in x.selected_node_ids]
    variables = [
        {"variable_id": "common_differential_pressure", "unit": "Pa"},
        {"variable_id": "total_contact_area", "unit": "m2"},
        {"variable_id": "total_molar_leak_rate", "unit": "mol/s"},
    ]
    for node_id in x.selected_node_ids:
        variables.extend([
            {"variable_id": f"node_contact_pressure:{node_id}", "unit": "Pa"},
            {"variable_id": f"node_area:{node_id}", "unit": "m2"},
            {"variable_id": f"node_molar_leak_rate:{node_id}", "unit": "mol/s"},
        ])
    vectors = []
    try:
        for scenario, row in zip(envelope.scenarios, rows, strict=True):
            responses = row["node_responses"]
            if [n["node_id"] for n in responses] != list(envelope.node_ids):
                raise ValueError("upstream node response order mismatch")
            vector = [scenario.common_differential_pressure_Pa, math.fsum(scenario.node_area_m2), row["molar_leak_rate_mol_s"]]
            for index in indices:
                vector.extend([scenario.node_contact_pressure_Pa[index], scenario.node_area_m2[index], responses[index]["molar_leak_rate_contribution_mol_s"]])
            if any(not math.isfinite(value) for value in vector):
                raise ValueError("scenario response exceeds finite support")
            vectors.append(vector)
        count = len(variables)
        weights = weighted.scenario_weights
        constant = [all(row[i] == vectors[0][i] for row in vectors) for i in range(count)]
        means = [vectors[0][i] if constant[i] else math.fsum(w * row[i] for w, row in zip(weights, vectors, strict=True)) for i in range(count)]
        centered = [[row[i] - means[i] for i in range(count)] for row in vectors]
        scales = [max(abs(row[i]) for row in centered) for i in range(count)]
        if any(not math.isfinite(value) for value in means + scales):
            raise ValueError("weighted centering exceeds finite support")
        normalized = [[0.0 if scales[i] == 0.0 else row[i] / scales[i] for i in range(count)] for row in centered]
        normalized_cov = [[0.0] * count for _ in range(count)]
        covariance = [[0.0] * count for _ in range(count)]
        for i in range(count):
            for j in range(i, count):
                value = math.fsum(w * row[i] * row[j] for w, row in zip(weights, normalized, strict=True))
                if i == j and scales[i] > 0.0 and value <= 0.0:
                    raise ValueError("nonconstant-column variance lost through numeric underflow")
                physical = (value * scales[i]) * scales[j]
                if not math.isfinite(physical) or (value != 0.0 and physical == 0.0):
                    raise ValueError("covariance exceeds finite nonzero numeric support")
                normalized_cov[i][j] = normalized_cov[j][i] = value
                covariance[i][j] = covariance[j][i] = physical
        correlation = [[None] * count for _ in range(count)]
        for i in range(count):
            for j in range(i, count):
                vi, vj = normalized_cov[i][i], normalized_cov[j][j]
                if vi > 0.0 and vj > 0.0:
                    if i == j or all(row[i] == row[j] for row in normalized):
                        value = 1.0
                    elif all(row[i] == -row[j] for row in normalized):
                        value = -1.0
                    else:
                        value = normalized_cov[i][j] / math.sqrt(vi) / math.sqrt(vj)
                    if not math.isfinite(value) or abs(value) > 1.0:
                        raise ValueError("correlation exceeds finite unit-interval numeric support")
                    correlation[i][j] = correlation[j][i] = value
    except (ValueError, KeyError, TypeError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {"reason": str(error)})
    return Calculation(values=base | {
        "scenario_ids": expected_ids, "scenario_weights": list(weights),
        "weight_semantics": weighted.weight_semantics, "variable_order": variables,
        "weighted_means": means, "weighted_centered_second_moment_matrix": covariance,
        "covariance_unit_rule": "entry(i,j) has variable_order[i].unit multiplied by variable_order[j].unit",
        "weighted_correlation_matrix": correlation,
        "undefined_correlation_variable_ids": [variables[i]["variable_id"] for i in range(count) if normalized_cov[i][i] == 0.0],
        "scenario_results_sha256": upstream.values["scenario_results_sha256"],
        "meaning": "descriptive finite joint-scenario centered moments; no unbiased covariance estimate, distribution, confidence interval, causal sensitivity or unseen-scenario bound",
    }, notes=("Scenario identity and caller weights are retained; marginal variables are never independently resampled or paired across rows.",
              "The covariance describes the declared finite set and its weights only. Constant columns have undefined correlation (null), not zero correlation.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec("fabrication.gasket_finite_scenario_dependence", GasketFiniteScenarioDependence,
        gasket_finite_scenario_dependence,
        {
            "weighted_means": "variable_order_units",
            "weighted_centered_second_moment_matrix": "row_column_variable_unit_product",
            "weighted_correlation_matrix": "1",
        },
        ("Caller-provided complete finite joint gasket scenarios and positive weights already summing to one.",
         "Existing calibrated leakage evaluator is reused; this module reports cross-variable descriptive centered moments and correlations.",
         "No new distribution/covariance estimate, stochastic independence, causal effect, sealing acceptance or material qualification is inferred."),
        (SOURCE_ID,), qualification="user_model")]
