"""Screen caller-selected solid saturation across a digest-pinned van't Hoff history."""

from __future__ import annotations

import math

from pydantic import Field, ValidationError, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..models.aqueous_saturation_screening import (
    CandidateSolid,
    screen_mass_action_calculation,
)
from ..registry import ModelSpec


class TemperatureSupportedCandidate(Contract):
    candidate: CandidateSolid
    minimum_valid_temperature_K: Positive
    maximum_valid_temperature_K: Positive

    @model_validator(mode="after")
    def ordered_support(self):
        if self.minimum_valid_temperature_K >= self.maximum_valid_temperature_K:
            raise ValueError("solubility temperature support must be strictly increasing")
        return self


class AqueousSolubilityKnot(Contract):
    time_s: float
    provider_id: str = Field(min_length=1)
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidates: tuple[TemperatureSupportedCandidate, ...] = Field(min_length=1, max_length=100)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def candidate_evidence(self):
        ids = [row.candidate.solid_id for row in self.candidates]
        record_ids = [row.candidate.solubility_record_id for row in self.candidates]
        sources = [row.source_id for row in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("solid IDs must be unique within each temperature knot")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("solubility source-record IDs must be unique within each temperature knot")
        if len(sources) != len(set(sources)):
            raise ValueError("solubility Evidence source IDs must be unique within each temperature knot")
        by_id = {row.source_id: row for row in self.evidence}
        for candidate in self.candidates:
            source_id = candidate.candidate.solubility_evidence_source_id
            if source_id not in by_id:
                raise ValueError("each solubility record must bind to supplied Evidence")
            evidence = by_id[source_id]
            if evidence.origin in {"measured", "open_dataset"} and evidence.sha256 is None:
                raise ValueError("measured/open solubility data require a source-file SHA-256")
            if evidence.origin == "open_dataset" and not evidence.license_id:
                raise ValueError("open solubility data require a declared license identifier")
        expected_digest = canonical_digest({
            "provider_id": self.provider_id,
            "candidates": [row.model_dump(mode="json") for row in self.candidates],
            "evidence": [row.model_dump(mode="json") for row in self.evidence],
        })
        if self.data_sha256 != expected_digest:
            raise ValueError("solubility knot digest does not match its provider, candidate records and Evidence")
        return self


class AqueousVanTHoffSaturationHistory(Contract):
    assessment_id: str = Field(min_length=1)
    equilibrium_history: AssessmentResult
    equilibrium_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solubility_by_knot: tuple[AqueousSolubilityKnot, ...] = Field(min_length=2, max_length=1000)
    activity_log10_absolute_bounds_by_knot: tuple[dict[str, float], ...] | None = None
    complete_species_inventory_reviewed: bool
    compatible_standard_states_reviewed: bool
    equilibrium_constants_temperature_reviewed: bool
    activity_interval_bounds_reviewed: bool = False
    solubility_product_interval_bounds_reviewed: bool = False

    @model_validator(mode="after")
    def pinned_history_and_support(self):
        upstream = self.equilibrium_history
        if upstream.model_id != "integration.aqueous_mass_action_vant_hoff_history":
            raise ValueError("a registered aqueous van't Hoff history result is required")
        payload_digest = canonical_digest({
            "model_id": upstream.model_id,
            "model_version": upstream.model_version,
            "inputs": upstream.inputs,
            "context": upstream.context.model_dump(mode="json"),
        })
        if upstream.input_digest != payload_digest:
            raise ValueError("upstream registry input/context digest does not verify")
        if canonical_digest(upstream.model_dump(mode="json")) != self.equilibrium_history_sha256:
            raise ValueError("upstream aqueous history result digest does not match")
        values = upstream.values
        times = values.get("times_s")
        temperatures = values.get("temperatures_K")
        rows = values.get("equilibrium_history")
        history_id = values.get("history_id")
        if not isinstance(times, list) or not isinstance(temperatures, list) or not isinstance(rows, list):
            raise ValueError("upstream aqueous history must expose aligned times, temperatures and knot results")
        if not isinstance(history_id, str) or not history_id.strip():
            raise ValueError("upstream aqueous history ID is required")
        if not (len(times) == len(temperatures) == len(rows) == len(self.solubility_by_knot)):
            raise ValueError("each aqueous history knot requires one aligned solubility-data knot")
        if not times or times[0] != 0 or any(
            not isinstance(left, (int, float)) or isinstance(left, bool)
            or not isinstance(right, (int, float)) or isinstance(right, bool)
            or right <= left
            for left, right in zip(times[:-1], times[1:], strict=True)
        ):
            raise ValueError("upstream history clock must be zero-based and strictly increasing")
        if self.activity_log10_absolute_bounds_by_knot is not None and len(self.activity_log10_absolute_bounds_by_knot) != len(rows):
            raise ValueError("activity interval bounds must have exactly one mapping per history knot")
        expected_solid_ids = None
        expected_terms = None
        for index, (time_s, temperature_K, row, solubility) in enumerate(
            zip(times, temperatures, rows, self.solubility_by_knot, strict=True)
        ):
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s):
                raise ValueError("upstream history time knot is invalid")
            if isinstance(temperature_K, bool) or not isinstance(temperature_K, (int, float)) or not math.isfinite(temperature_K) or temperature_K <= 0:
                raise ValueError("upstream history temperature knot is invalid")
            if solubility.time_s != time_s:
                raise ValueError("solubility and aqueous history clocks must match exactly")
            solids = solubility.candidates
            solid_ids = tuple(item.candidate.solid_id for item in solids)
            terms = tuple(
                (item.candidate.solid_id, tuple((term.species_id, term.stoichiometric_exponent) for term in item.candidate.terms))
                for item in solids
            )
            if expected_solid_ids is None:
                expected_solid_ids, expected_terms = solid_ids, terms
            elif solid_ids != expected_solid_ids or terms != expected_terms:
                raise ValueError("candidate solid identities/order and activity-product terms must stay fixed across the history")
            if any(not item.minimum_valid_temperature_K <= temperature_K <= item.maximum_valid_temperature_K for item in solids):
                raise ValueError("a knot temperature is outside a candidate solubility record's stated support")
            if upstream.status == "computed" and (
                not isinstance(row, dict) or row.get("status") != "computed" or not isinstance(row.get("calculation"), dict)
            ):
                raise ValueError(f"computed upstream history contains a noncomputed or incomplete knot at index {index}")
            if isinstance(row, dict):
                if row.get("time_s") != time_s or row.get("temperature_K") != temperature_K:
                    raise ValueError(f"upstream knot metadata does not match the declared history axes at index {index}")
                calculation = row.get("calculation")
                if calculation is not None:
                    try:
                        parsed_calculation = Calculation.model_validate(calculation)
                    except ValidationError as exc:
                        raise ValueError(f"upstream calculation contract is invalid at knot {index}") from exc
                    if row.get("status") != parsed_calculation.status:
                        raise ValueError(f"upstream history summary and calculation status differ at knot {index}")
                calculation_values = calculation.get("values") if isinstance(calculation, dict) else None
                if isinstance(calculation_values, dict) and calculation_values.get("temperature_K") != temperature_K:
                    raise ValueError(f"upstream mass-action state temperature differs from its history knot at index {index}")
            if self.activity_log10_absolute_bounds_by_knot is not None and isinstance(row, dict):
                calculation = row.get("calculation")
                species = calculation.get("values", {}).get("species", []) if isinstance(calculation, dict) else []
                expected_species = {item.get("species_id") for item in species if isinstance(item, dict)}
                bounds = self.activity_log10_absolute_bounds_by_knot[index]
                if set(bounds) != expected_species or any(
                    isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
                    for value in bounds.values()
                ):
                    raise ValueError("each activity bound mapping must cover exactly the knot species with finite nonnegative bounds")
        return self


def _validate_context(x: AqueousVanTHoffSaturationHistory, context: RunContext) -> None:
    source = x.equilibrium_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("saturation-history RunContext must match the upstream equilibrium history")


def screen_aqueous_vant_hoff_history(x: AqueousVanTHoffSaturationHistory) -> Calculation:
    upstream = x.equilibrium_history
    digest = x.equilibrium_history_sha256
    if upstream.status != "computed":
        return Calculation(status=upstream.status, values={
            "assessment_id": x.assessment_id,
            "equilibrium_history_sha256": digest,
            "upstream_status": upstream.status,
            "saturation_history": [],
            "phase_selection_performed": False,
        }, notes=("The upstream temperature-dependent equilibrium history is incomplete; no saturation screens were calculated.",))
    rows = upstream.values["equilibrium_history"]
    temperatures = upstream.values["temperatures_K"]
    results = []
    for index, (row, temperature, solubility) in enumerate(
        zip(rows, temperatures, x.solubility_by_knot, strict=True)
    ):
        upstream_knot = Calculation.model_validate(row["calculation"])
        screen = screen_mass_action_calculation(
            upstream_knot,
            assessment_id=f"{x.assessment_id}:{index}",
            solution_id=f"{upstream.values['history_id']}:{index}",
            candidate_solids=tuple(item.candidate for item in solubility.candidates),
            activity_log10_absolute_bounds=(
                None if x.activity_log10_absolute_bounds_by_knot is None
                else x.activity_log10_absolute_bounds_by_knot[index]
            ),
            solubility_data_provider_id=solubility.provider_id,
            solubility_data_digest=solubility.data_sha256,
            complete_species_inventory_reviewed=x.complete_species_inventory_reviewed,
            compatible_standard_states_reviewed=x.compatible_standard_states_reviewed,
            equilibrium_constants_temperature_reviewed=x.equilibrium_constants_temperature_reviewed,
            activity_interval_bounds_reviewed=x.activity_interval_bounds_reviewed,
            solubility_product_interval_bounds_reviewed=x.solubility_product_interval_bounds_reviewed,
            evidence=solubility.evidence,
        )
        results.append({
            "time_s": solubility.time_s,
            "temperature_K": temperature,
            "upstream_knot_sha256": canonical_digest(upstream_knot.model_dump(mode="json")),
            "solubility_data_sha256": solubility.data_sha256,
            "status": screen.status,
            "screen": screen.model_dump(mode="json"),
        })
    statuses = [row["status"] for row in results]
    status = "computed" if all(value == "computed" for value in statuses) else (
        "needs_data" if "needs_data" in statuses else "out_of_scope"
    )
    return Calculation(status=status, values={
        "assessment_id": x.assessment_id,
        "equilibrium_history_sha256": digest,
        "history_id": upstream.values["history_id"],
        "times_s": list(upstream.values["times_s"]),
        "temperatures_K": list(temperatures),
        "saturation_history": results,
        "candidate_solid_ids": [item.candidate.solid_id for item in x.solubility_by_knot[0].candidates],
        "phase_selection_performed": False,
        "precipitated_amount_predicted": False,
    }, notes=(
        "Each equilibrium knot is screened independently with caller-supplied, temperature-supported solubility records and exact upstream activity lineage.",
        "Saturation indices do not select phases, predict precipitation amount or kinetics, establish scale protection, or validate corrosion rates.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_vant_hoff_saturation_history",
        AqueousVanTHoffSaturationHistory,
        screen_aqueous_vant_hoff_history,
        {"times_s": "s", "temperatures_K": "K", "saturation_history[].screen.values.candidate_results.log10_saturation_ratio": "1"},
        (
            "Screens only caller-selected candidate solids using the exact computed species activities at each digest-pinned van't Hoff history knot.",
            "Solubility products are provided per knot with source Evidence and explicit temperature support; no interpolation, phase selection, precipitation amount, kinetics or corrosion rate is inferred.",
        ),
        ("caller_aqueous_candidate_saturation_screen",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
