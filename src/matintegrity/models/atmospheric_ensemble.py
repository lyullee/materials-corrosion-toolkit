"""Combine caller-supplied first-year atmospheric corrosion scenarios."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .atmospheric import AtmosphericFirstYearPrediction, atmospheric_first_year_prediction


class AtmosphericScenario(Contract):
    scenario_id: str = Field(min_length=1)
    weight: Positive
    prediction_input: AtmosphericFirstYearPrediction


class AtmosphericScenarioEnsemble(Contract):
    ensemble_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    scenarios: tuple[AtmosphericScenario, ...] = Field(min_length=1)
    quantile_probabilities: tuple[float, ...] = (0.05, 0.5, 0.95)
    independence_assumption_reviewed: bool
    scenario_weights_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scenarios(self):
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(set(ids)) != len(ids):
            raise ValueError("scenario identifiers must be unique")
        contexts = {
            (
                scenario.prediction_input.asset_id,
                scenario.prediction_input.location_id,
                scenario.prediction_input.physical_scope_id,
                scenario.prediction_input.material_condition_id,
                scenario.prediction_input.exposure_environment_id,
                scenario.prediction_input.time_basis,
                scenario.prediction_input.exposure_start_s,
                scenario.prediction_input.exposure_duration_s,
            )
            for scenario in self.scenarios
        }
        if any(
            (scenario.prediction_input.asset_id, scenario.prediction_input.location_id)
            != (self.asset_id, self.location_id)
            for scenario in self.scenarios
        ):
            raise ValueError("scenario asset and location must match the ensemble identity")
        if len(contexts) != 1:
            raise ValueError("scenarios must share physical scope, material, environment and exposure clock")
        if abs(sum(item.weight for item in self.scenarios) - 1.0) > 1e-10:
            raise ValueError("scenario weights must sum to one")
        if any(not 0.0 < q < 1.0 for q in self.quantile_probabilities):
            raise ValueError("quantile probabilities must lie strictly between zero and one")
        if tuple(sorted(set(self.quantile_probabilities))) != self.quantile_probabilities:
            raise ValueError("quantile probabilities must be unique and ascending")
        return self


def atmospheric_scenario_ensemble(x: AtmosphericScenarioEnsemble) -> Calculation:
    """Produce weighted descriptive summaries from separately evaluated inputs."""
    base = {
        "ensemble_id": x.ensemble_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "scenario_count": len(x.scenarios),
        "scenario_rows": [],
        "summary": None,
        "independence_assumption_used": False,
        "remaining_life_or_probability_generated": False,
    }
    if not (x.independence_assumption_reviewed and x.scenario_weights_reviewed):
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Review scenario weights and their interpretation before aggregation.",),
        )

    evaluated = []
    for scenario in x.scenarios:
        prediction = atmospheric_first_year_prediction(scenario.prediction_input)
        values = prediction.values
        row = {
            "scenario_id": scenario.scenario_id,
            "weight": scenario.weight,
            "status": prediction.status,
            "prediction_digest": canonical_digest(values),
            "first_year_loss_m": values.get("predicted_first_year_loss_m"),
            "equivalent_rate_m_s": values.get("equivalent_first_year_rate_m_s"),
            "inside_calibration_support": not bool(values.get("outside_support_fields")),
            "transfer_criteria_met": scenario.prediction_input.model.transfer_criteria_met
            or scenario.prediction_input.limited_transfer_override_reviewed,
        }
        base["scenario_rows"].append(row)
        if prediction.status != "computed" or row["first_year_loss_m"] is None:
            return Calculation(
                status="needs_data" if prediction.status == "needs_data" else "out_of_scope",
                values=base | {"unresolved_scenario_id": scenario.scenario_id},
                notes=("Every scenario must yield a transferable first-year prediction before summarizing.",),
            )
        if not row["inside_calibration_support"]:
            return Calculation(
                status="out_of_scope",
                values=base | {"unresolved_scenario_id": scenario.scenario_id},
                notes=("An ensemble cannot override a scenario's support or transfer gate.",),
            )
        evaluated.append((scenario.weight, float(row["first_year_loss_m"])))

    ordered = sorted(evaluated, key=lambda item: item[1])

    def weighted_quantile(q: float) -> float:
        cumulative = 0.0
        for weight, value in ordered:
            cumulative += weight
            if cumulative + 1e-12 >= q:
                return value
        return ordered[-1][1]

    losses = [value for _, value in evaluated]
    base["summary"] = {
        "weighted_mean_first_year_loss_m": sum(weight * value for weight, value in evaluated),
        "minimum_first_year_loss_m": min(losses),
        "maximum_first_year_loss_m": max(losses),
        "weighted_quantiles_first_year_loss_m": {
            f"{q:g}": weighted_quantile(q) for q in x.quantile_probabilities
        },
    }
    base["report_digest"] = canonical_digest(base)
    return Calculation(
        status="computed",
        values=base,
        notes=(
            "Weighted summaries describe the caller-defined scenario set, not a probability distribution unless its weights have that justified meaning.",
            "First-year atmospheric carbon-steel loss does not establish multi-year rate, localized penetration, remaining life, acceptance or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "degradation.atmospheric_scenario_ensemble",
            AtmosphericScenarioEnsemble,
            atmospheric_scenario_ensemble,
            {
                "ensemble_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "input_digest": "1",
                "scenario_count": "count",
                "scenario_rows": "mixed",
                "summary": "mixed",
                "independence_assumption_used": "1",
                "remaining_life_or_probability_generated": "1",
                "report_digest": "1",
            },
            (
                "Each scenario is independently passed to the registered first-year atmospheric prediction model.",
                "Scenario weights and transfer applicability require caller review; no dependence model is introduced.",
            ),
            ("authored_atmospheric_scenario_ensemble",),
        )
    ]
