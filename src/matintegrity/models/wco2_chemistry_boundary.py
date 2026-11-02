"""Audit typed chemistry/speciation/transport handoffs without inferring chemistry."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, RunContext, canonical_digest
from ..registry import ModelSpec


class ChemistryBoundaryStage(Contract):
    """One computed result plus caller-reviewed paths to its physical state metadata."""

    stage_id: str = Field(min_length=1)
    expected_model_id: str = Field(min_length=1)
    result: AssessmentResult
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    elapsed_time_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    temperature_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    solvent_id_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    standard_state_id_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    material_condition_id_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    output_species_ids_path: tuple[str, ...] = Field(min_length=2, max_length=12)
    input_species_ids_path: tuple[str, ...] | None = Field(default=None, min_length=2, max_length=12)

    @model_validator(mode="after")
    def result_is_pinned(self):
        if self.result.status != "computed" or self.result.model_id != self.expected_model_id:
            raise ValueError("each boundary stage must be a computed result of its declared model")
        expected_input = canonical_digest({
            "model_id": self.result.model_id,
            "model_version": self.result.model_version,
            "inputs": self.result.inputs,
            "context": self.result.context.model_dump(mode="json"),
        })
        if self.result.input_digest != expected_input:
            raise ValueError("boundary stage input digest does not match its request and context")
        if canonical_digest(self.result.model_dump(mode="json")) != self.result_sha256:
            raise ValueError("boundary stage result digest mismatch")
        if not self.result.context.asset_id or not self.result.context.location_id or not self.result.context.time_basis:
            raise ValueError("boundary stage lacks asset, location or clock identity")
        return self


class SpeciesHandoff(Contract):
    """Reviewed disposition for one upstream species at a stage boundary."""

    source_species_id: str = Field(min_length=1)
    target_species_id: str | None = None
    mapping_kind: Literal["identity", "renamed", "reaction_transformed", "intentionally_excluded"]
    mapping_record_id: str = Field(min_length=1)
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def explicit_disposition(self):
        if not any(row.sha256 == self.mapping_sha256 for row in self.evidence):
            raise ValueError("species mapping digest must be represented by Evidence")
        if self.mapping_kind == "intentionally_excluded":
            if self.target_species_id is not None:
                raise ValueError("excluded species cannot name a downstream species")
        elif not self.target_species_id:
            raise ValueError("mapped species require a downstream species identity")
        elif self.mapping_kind == "identity" and self.target_species_id != self.source_species_id:
            raise ValueError("identity mapping must preserve the species ID")
        elif self.mapping_kind == "renamed" and self.target_species_id == self.source_species_id:
            raise ValueError("renamed mapping must declare a distinct target species ID")
        if not self.reviewed:
            raise ValueError("every species handoff or exclusion must be reviewed")
        return self


class ChemistryBoundaryLink(Contract):
    from_stage_id: str = Field(min_length=1)
    to_stage_id: str = Field(min_length=1)
    species_handoffs: tuple[SpeciesHandoff, ...] = Field(min_length=1, max_length=10000)
    solvent_and_standard_state_mapping_reviewed: bool


class ElectrochemicalChemistryBoundaryAudit(Contract):
    """Digest-bound one-way state continuity audit across caller-selected chemistry stages."""

    schema_version: Literal["matintegrity.electrochemical_chemistry_boundary_audit.v1"] = (
        "matintegrity.electrochemical_chemistry_boundary_audit.v1"
    )
    assessment_id: str = Field(min_length=1)
    stages: tuple[ChemistryBoundaryStage, ...] = Field(min_length=2, max_length=32)
    links: tuple[ChemistryBoundaryLink, ...] = Field(min_length=1, max_length=31)
    exact_time_alignment_reviewed: bool
    exact_temperature_alignment_reviewed: bool
    material_state_mapping_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def ordered_complete_chain(self):
        ids = tuple(stage.stage_id for stage in self.stages)
        if len(set(ids)) != len(ids) or len(self.links) != len(ids) - 1:
            raise ValueError("stage IDs must be unique with exactly one link per adjacent stage pair")
        for index, link in enumerate(self.links):
            if (link.from_stage_id, link.to_stage_id) != (ids[index], ids[index + 1]):
                raise ValueError("boundary links must preserve the declared stage order")
            if self.stages[index + 1].input_species_ids_path is None:
                raise ValueError("every downstream stage must declare the path to its consumed species IDs")
            if not link.solvent_and_standard_state_mapping_reviewed:
                raise ValueError("solvent and activity standard-state handoff requires explicit review")
        if not all((self.exact_time_alignment_reviewed, self.exact_temperature_alignment_reviewed,
                    self.material_state_mapping_reviewed, self.computational_use_authorized)):
            raise ValueError("time, temperature, material-state and computational-use reviews are required")
        return self


def _resolve_path(root, path: tuple[str, ...]):
    values = [root]
    for token in path:
        next_values = []
        for value in values:
            if token == "*":
                if not isinstance(value, list):
                    raise ValueError("wildcard result path token requires an array")
                next_values.extend(value)
            else:
                if not isinstance(value, dict) or token not in value:
                    raise ValueError(f"declared boundary result path is absent at token {token!r}")
                next_values.append(value[token])
        values = next_values
    if len(values) == 1 and isinstance(values[0], list):
        return values[0]
    return values


def _scalar(stage: ChemistryBoundaryStage, path: tuple[str, ...], name: str) -> str:
    value = _resolve_path(stage.result.model_dump(mode="json"), path)
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
        value = value[0]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must resolve to one nonempty string in stage {stage.stage_id}")
    return value


def _string_vector(stage: ChemistryBoundaryStage, path: tuple[str, ...], name: str) -> tuple[str, ...]:
    values = _resolve_path(stage.result.model_dump(mode="json"), path)
    if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item for item in values):
        raise ValueError(f"{name} must resolve to a nonempty string array in stage {stage.stage_id}")
    result = tuple(values)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} must not contain duplicate IDs in stage {stage.stage_id}")
    return result


def _numeric_vector(stage: ChemistryBoundaryStage, path: tuple[str, ...], name: str) -> tuple[float, ...]:
    values = _resolve_path(stage.result.model_dump(mode="json"), path)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{name} must resolve to a nonempty numeric array in stage {stage.stage_id}")
    result = tuple(values)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in result):
        raise ValueError(f"{name} contains a nonnumeric or nonfinite value in stage {stage.stage_id}")
    return result


def audit_electrochemical_chemistry_boundary(x: ElectrochemicalChemistryBoundaryAudit) -> Calculation:
    records = []
    reference = None
    for stage in x.stages:
        result = stage.result
        times = _numeric_vector(stage, stage.elapsed_time_path, "elapsed time")
        temperatures = _numeric_vector(stage, stage.temperature_path, "temperature")
        if len(times) != len(temperatures) or times[0] != 0 or any(
            right <= left for left, right in zip(times[:-1], times[1:], strict=True)
        ) or any(value <= 0 for value in temperatures):
            raise ValueError(f"stage {stage.stage_id} time/temperature vectors are invalid or misaligned")
        material_id = _scalar(stage, stage.material_condition_id_path, "material condition ID")
        solvent_id = _scalar(stage, stage.solvent_id_path, "solvent ID")
        standard_state_id = _scalar(stage, stage.standard_state_id_path, "activity standard-state ID")
        output_species = _string_vector(stage, stage.output_species_ids_path, "output species IDs")
        input_species = (
            _string_vector(stage, stage.input_species_ids_path, "input species IDs")
            if stage.input_species_ids_path is not None else ()
        )
        context_identity = (result.context.asset_id, result.context.location_id, result.context.time_basis)
        identity = (context_identity, times, temperatures, material_id, solvent_id, standard_state_id)
        if reference is None:
            reference = identity
        elif identity != reference:
            raise ValueError("stages disagree on asset/location/clock, exact knots, temperature, material, solvent or standard state")
        records.append({
            "stage_id": stage.stage_id,
            "model_id": result.model_id,
            "model_version": result.model_version,
            "result_sha256": stage.result_sha256,
            "input_digest": result.input_digest,
            "context_sha256": canonical_digest(result.context.model_dump(mode="json")),
            "field_paths": {
                "elapsed_time": list(stage.elapsed_time_path),
                "temperature": list(stage.temperature_path),
                "material_condition": list(stage.material_condition_id_path),
                "solvent": list(stage.solvent_id_path),
                "standard_state": list(stage.standard_state_id_path),
                "input_species": list(stage.input_species_ids_path) if stage.input_species_ids_path else None,
                "output_species": list(stage.output_species_ids_path),
            },
            "elapsed_time_s": list(times),
            "temperature_K": list(temperatures),
            "material_condition_id": material_id,
            "solvent_id": solvent_id,
            "activity_standard_state_id": standard_state_id,
            "input_species_ids": list(input_species),
            "output_species_ids": list(output_species),
            "resolved_state_sha256": canonical_digest({
                "times": times, "temperatures": temperatures, "material": material_id,
                "solvent": solvent_id, "standard_state": standard_state_id,
                "input_species": input_species, "output_species": output_species,
            }),
        })
    stage_by_id = {row["stage_id"]: row for row in records}
    links = []
    for link in x.links:
        upstream, downstream = stage_by_id[link.from_stage_id], stage_by_id[link.to_stage_id]
        upstream_ids = set(upstream["output_species_ids"])
        downstream_inputs = set(downstream["input_species_ids"])
        source_ids = [row.source_species_id for row in link.species_handoffs]
        if len(source_ids) != len(set(source_ids)) or set(source_ids) != upstream_ids:
            raise ValueError("every upstream species needs exactly one explicit downstream mapping or reviewed exclusion")
        mapped_targets = [row.target_species_id for row in link.species_handoffs if row.target_species_id is not None]
        if not downstream_inputs <= set(mapped_targets):
            raise ValueError("every downstream consumed species must be covered by an explicit upstream handoff")
        links.append({
            "from_stage_id": link.from_stage_id,
            "to_stage_id": link.to_stage_id,
            "source_species_ids": source_ids,
            "target_species_ids": mapped_targets,
            "excluded_species_ids": [row.source_species_id for row in link.species_handoffs
                                     if row.mapping_kind == "intentionally_excluded"],
            "mapping_records": [row.model_dump(mode="json") for row in link.species_handoffs],
            "mapping_sha256": canonical_digest([row.model_dump(mode="json") for row in link.species_handoffs]),
        })
    return Calculation(values={
        "assessment_id": x.assessment_id,
        "status": "computed",
        "stage_count": len(records),
        "stages": records,
        "handoffs": links,
        "chain_sha256": canonical_digest({"stages": records, "handoffs": links}),
        "scope": "lineage_and_state-boundary audit only; no activity, speciation, equilibrium, transport, kinetics, metal loss or corrosion qualification is calculated",
    }, notes=(
        "Only caller-declared field paths are read; no chemistry state is inferred from model names or prose.",
        "Every upstream species is mapped to one unique downstream identity or explicitly excluded with evidence; this audit does not prove reaction or elemental conservation.",
        "Exact solvent and standard-state equality is required across stages. A conversion must be performed and recorded upstream before this boundary audit.",
    ))


def _validate_context(x: ElectrochemicalChemistryBoundaryAudit, context: RunContext) -> None:
    for stage in x.stages:
        if (stage.result.context.asset_id, stage.result.context.location_id, stage.result.context.time_basis) != (
            context.asset_id, context.location_id, context.time_basis
        ):
            raise ValueError("boundary stage asset/location/time identity must match the audit RunContext")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.electrochemical_chemistry_boundary_audit",
        ElectrochemicalChemistryBoundaryAudit,
        audit_electrochemical_chemistry_boundary,
        {"stages[].elapsed_time_s": "s", "stages[].temperature_K": "K"},
        (
            "Digest-pinned computed chemistry/speciation/transport stages must align on asset, location, clock, exact times, temperatures, material condition, solvent and activity standard state.",
            "Caller-declared JSON field paths and evidence-linked species mappings make boundary losses/renames visible; no chemical or physical closure is inferred.",
        ),
        ("electrochemical_chemistry_state_boundary_audit",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
