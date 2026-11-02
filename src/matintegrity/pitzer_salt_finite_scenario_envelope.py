"""Summarize a finite caller-declared set of pure-salt Pitzer scenarios.

The output is a descriptive envelope over exactly the supplied requests. It is
not a continuous parameter bound, uncertainty distribution, or mixed-electrolyte
model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .models.pitzer_single_salt import PitzerSingleSaltActivity, pitzer_single_salt_activity
from .registry import ModelSpec


MODEL_ID = "chemistry.pitzer_salt_finite_scenario_envelope"
SOURCE_ID = "caller_pitzer_salt_finite_scenario_envelope"


class PitzerSaltFiniteScenarioEnvelope(Contract):
    """Evaluate an ordered finite collection of comparable single-salt cases."""

    schema_version: Literal["matintegrity.pitzer_salt_finite_scenario_envelope.v1"] = (
        "matintegrity.pitzer_salt_finite_scenario_envelope.v1"
    )
    envelope_id: str = Field(min_length=1)
    scenarios: tuple[PitzerSingleSaltActivity, ...] = Field(min_length=2, max_length=200)
    shared_salt_and_temperature_scope_reviewed: bool
    scenario_order_reviewed: bool
    finite_set_interpretation_reviewed: bool

    @model_validator(mode="after")
    def comparable_scenarios(self):
        ids = [row.assessment_id for row in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario assessment IDs must be unique")
        first = self.scenarios[0]
        shared = (
            "salt_id",
            "cation_id",
            "anion_id",
            "cation_charge_number",
            "anion_charge_number",
            "cation_stoichiometric_number",
            "anion_stoichiometric_number",
            "temperature_K",
        )
        for row in self.scenarios[1:]:
            if any(getattr(row, name) != getattr(first, name) for name in shared):
                raise ValueError("finite scenarios must describe the same salt formula and solution temperature")
        return self


def evaluate_pitzer_salt_finite_scenario_envelope(
    request: PitzerSaltFiniteScenarioEnvelope,
) -> Calculation:
    """Evaluate all explicit cases and report extrema only after full completion.

    The exact input order is preserved. If a case does not compute, the result
    reports the completed prefix and first failure without presenting prefix
    extrema as though they covered the declared finite set.
    """

    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    reviews = {
        "shared_salt_and_temperature_scope_reviewed": request.shared_salt_and_temperature_scope_reviewed,
        "scenario_order_reviewed": request.scenario_order_reviewed,
        "finite_set_interpretation_reviewed": request.finite_set_interpretation_reviewed,
    }
    missing_reviews = [name for name, accepted in reviews.items() if not accepted]
    base = {
        "envelope_id": request.envelope_id,
        "input_sha256": input_sha256,
        "scenario_ids": [row.assessment_id for row in request.scenarios],
        "scenario_count": len(request.scenarios),
        "scenario_order_preserved": True,
        "probability_assigned": False,
        "continuous_or_global_bound_claimed": False,
        "mixed_electrolyte_model": False,
    }
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    rows: list[dict] = []
    for index, scenario in enumerate(request.scenarios):
        result = pitzer_single_salt_activity(scenario)
        row = {
            "scenario_id": scenario.assessment_id,
            "scenario_request_sha256": canonical_digest(scenario.model_dump(mode="json")),
            "result_sha256": canonical_digest(result.model_dump(mode="json")),
            "status": result.status,
            "values": result.values,
        }
        rows.append(row)
        if result.status != "computed":
            return Calculation(
                status=result.status,
                values=base
                | {
                    "completed_prefix": rows[:-1],
                    "first_failure": row,
                    "first_failure_index": index,
                    "partial_envelope_returned": False,
                },
                notes=(
                    "No scenario extrema are returned because the declared finite set did not fully compute.",
                    "The failed prefix and first failed case are records of execution order, not missing-value imputation or a partial uncertainty bound.",
                ),
            )

    extrema = {}
    for field in (
        "ionic_strength_mol_kg",
        "mean_ionic_activity_coefficient",
        "mean_ionic_activity_mol_kg_water",
        "osmotic_coefficient",
        "water_activity",
    ):
        values = [row["values"][field] for row in rows]
        low_index = min(range(len(values)), key=values.__getitem__)
        high_index = max(range(len(values)), key=values.__getitem__)
        extrema[field] = {
            "minimum": values[low_index],
            "minimum_scenario_id": rows[low_index]["scenario_id"],
            "maximum": values[high_index],
            "maximum_scenario_id": rows[high_index]["scenario_id"],
        }
    return Calculation(
        status="computed",
        values=base
        | {
            "evaluated_scenarios": rows,
            "finite_scenario_extrema": extrema,
            "finite_set_complete": True,
            "extrema_interpretation": "minimum and maximum over only the caller-listed, fully computed scenarios",
        },
        notes=(
            "This is a deterministic summary of a finite caller-selected scenario set. It is not a probability distribution, confidence interval, continuous parameter envelope, global uncertainty bound, or qualification result.",
            "Each scenario retains its own parameter record, Evidence, authorization flags, request digest and result digest. The underlying Pitzer calculator is restricted to one pure electrolyte per scenario.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=PitzerSaltFiniteScenarioEnvelope,
        evaluator=evaluate_pitzer_salt_finite_scenario_envelope,
        units={
            "finite_scenario_extrema.ionic_strength_mol_kg.minimum": "mol/kg",
            "finite_scenario_extrema.ionic_strength_mol_kg.maximum": "mol/kg",
            "finite_scenario_extrema.mean_ionic_activity_coefficient.minimum": "1",
            "finite_scenario_extrema.mean_ionic_activity_coefficient.maximum": "1",
            "finite_scenario_extrema.mean_ionic_activity_mol_kg_water.minimum": "mol/kg",
            "finite_scenario_extrema.mean_ionic_activity_mol_kg_water.maximum": "mol/kg",
            "finite_scenario_extrema.osmotic_coefficient.minimum": "1",
            "finite_scenario_extrema.osmotic_coefficient.maximum": "1",
            "finite_scenario_extrema.water_activity.minimum": "1",
            "finite_scenario_extrema.water_activity.maximum": "1",
        },
        assumptions=(
            "All scenarios share one caller-reviewed pure-salt formula and temperature and retain their supplied order.",
            "Only extrema over the fully computed caller-listed finite set are reported; no distribution or continuous/global bound is inferred.",
            "Each scenario reuses the existing single-salt Pitzer implementation and its own parameter Evidence and rights review.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
