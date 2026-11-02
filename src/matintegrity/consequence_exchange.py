"""Provider-neutral integrity-event to process-consequence exchange contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Fraction, Nonnegative, Positive, ProbabilityMeaning, canonical_digest

ConsequenceStage = Literal["source", "release", "dispersion", "effect"]


class CompositionComponent(Contract):
    component_id: str = Field(min_length=1)
    fraction: Fraction
    fraction_basis: Literal["mole_fraction", "mass_fraction"]
    unit_token: Literal["1"] = "1"
    source_id: str = Field(min_length=1)


class ProcessStateBasis(Contract):
    pressure_pa: Nonnegative
    pressure_unit_token: Literal["Pa"] = "Pa"
    pressure_basis: Literal["absolute", "gauge"]
    temperature_k: Positive
    temperature_unit_token: Literal["K"] = "K"
    temperature_basis: str = Field(min_length=1)
    composition: tuple[CompositionComponent, ...] = Field(min_length=1)
    composition_basis_description: str = Field(min_length=1)
    state_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_composition(self):
        component_ids = [row.component_id for row in self.composition]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("process-state component identifiers must be unique")
        bases = {row.fraction_basis for row in self.composition}
        if len(bases) != 1:
            raise ValueError("one process-state composition must use one fraction basis")
        if abs(sum(row.fraction for row in self.composition) - 1.0) > 1e-9:
            raise ValueError("process-state composition fractions must sum to one")
        return self


class IntegrityEventBasis(Contract):
    event_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    event_probability: Fraction
    probability_semantics: ProbabilityMeaning
    probability_conditioning: str = Field(min_length=1)
    integrity_model_id: str = Field(min_length=1)
    integrity_model_version: str = Field(min_length=1)
    integrity_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    integrity_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def ordered_horizon(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("integrity-event horizon must have positive duration")
        return self


class ReleaseScenarioBasis(Contract):
    release_scenario_id: str = Field(min_length=1)
    inventory_id: str = Field(min_length=1)
    release_location_id: str = Field(min_length=1)
    release_phase_basis: Literal["gas", "liquid", "two_phase", "provider_to_determine"]
    release_geometry_basis: Literal["caller_defined", "provider_defined"]
    release_geometry_description: str = Field(min_length=1)
    opening_area_m2: Positive | None = None
    release_direction_basis: str = Field(min_length=1)
    release_duration_s: Positive | None = None
    isolation_basis: str = Field(min_length=1)
    source_boundary_basis: str = Field(min_length=1)
    wall_loss_to_opening_conversion_performed: Literal[False] = False
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def caller_geometry_is_complete(self):
        if self.release_geometry_basis == "caller_defined" and self.opening_area_m2 is None:
            raise ValueError("caller-defined release geometry requires an opening area")
        return self


class RequestedConsequenceModel(Contract):
    stage: ConsequenceStage
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ConsequenceScenarioHandoff(Contract):
    schema_version: Literal["matintegrity.consequence_scenario_handoff.v1"] = (
        "matintegrity.consequence_scenario_handoff.v1"
    )
    handoff_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    event: IntegrityEventBasis
    process_state: ProcessStateBasis
    release: ReleaseScenarioBasis
    requested_models: tuple[RequestedConsequenceModel, ...] = Field(min_length=4, max_length=4)
    handoff_status: Literal["ready", "needs_data", "out_of_scope"]
    missing_items: tuple[str, ...] = ()
    limitations: tuple[str, ...] = Field(min_length=1)
    consequence_to_failure_probability_conversion_performed: Literal[False] = False
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def complete_and_bound(self, info: ValidationInfo):
        stages = [row.stage for row in self.requested_models]
        if set(stages) != {"source", "release", "dispersion", "effect"} or len(stages) != len(set(stages)):
            raise ValueError("handoff requires one requested model for every consequence stage")
        if self.handoff_status == "ready" and self.missing_items:
            raise ValueError("a ready consequence handoff cannot have missing items")
        if self.handoff_status != "ready" and not self.missing_items:
            raise ValueError("a non-ready consequence handoff must identify missing or unsupported items")
        if any(not row.strip() for row in (*self.missing_items, *self.limitations)):
            raise ValueError("handoff missing items and limitations must be nonempty statements")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("consequence handoff payload digest does not match its content")
        return self


class ConsequenceQuantity(Contract):
    quantity_id: str = Field(min_length=1)
    quantity_definition: str = Field(min_length=1)
    value: float
    unit_token: str = Field(min_length=1)
    standard_uncertainty: Nonnegative | None = None
    receptor_id: str = Field(min_length=1)
    receptor_type: str = Field(min_length=1)
    receptor_location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    time_s: Nonnegative
    time_basis: str = Field(min_length=1)


class ConsequenceStageResult(Contract):
    stage: ConsequenceStage
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    status: Literal["computed", "needs_data", "out_of_scope", "not_run"]
    quantities: tuple[ConsequenceQuantity, ...] = ()
    missing_items: tuple[str, ...] = ()
    notes: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_matches_payload(self):
        quantity_ids = [row.quantity_id for row in self.quantities]
        if len(quantity_ids) != len(set(quantity_ids)):
            raise ValueError("consequence quantity identifiers must be unique within a stage")
        if self.status == "computed" and not self.quantities:
            raise ValueError("a computed consequence stage requires at least one quantity")
        if self.status == "computed" and self.missing_items:
            raise ValueError("a computed consequence stage cannot retain missing items")
        if self.status != "computed" and self.quantities:
            raise ValueError("a non-computed consequence stage cannot carry result quantities")
        if self.status in {"needs_data", "not_run"} and not self.missing_items:
            raise ValueError("needs-data and not-run stages must identify missing items")
        if any(not row.strip() for row in (*self.missing_items, *self.notes)):
            raise ValueError("stage missing items and notes must be nonempty statements")
        return self


class ConsequenceScenarioResultRecord(Contract):
    schema_version: Literal["matintegrity.consequence_scenario_result.v1"] = (
        "matintegrity.consequence_scenario_result.v1"
    )
    result_record_id: str = Field(min_length=1)
    handoff_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    handoff_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_id: str = Field(min_length=1)
    event_probability: Fraction
    probability_semantics: ProbabilityMeaning
    probability_conditioning: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    requested_models: tuple[RequestedConsequenceModel, ...] = Field(min_length=4, max_length=4)
    stage_results: tuple[ConsequenceStageResult, ...] = Field(min_length=4, max_length=4)
    scenario_status: Literal["complete", "needs_data", "out_of_scope", "incomplete"]
    scenario_missing_items: tuple[str, ...] = ()
    consequence_to_failure_probability_conversion_performed: Literal[False] = False
    limitations: tuple[str, ...] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def complete_and_bound(self, info: ValidationInfo):
        stages = [row.stage for row in self.stage_results]
        if set(stages) != {"source", "release", "dispersion", "effect"} or len(stages) != len(set(stages)):
            raise ValueError("result requires one record for every consequence stage")
        requested = {row.stage: row for row in self.requested_models}
        if set(requested) != {"source", "release", "dispersion", "effect"}:
            raise ValueError("result must preserve one requested model for every consequence stage")
        for row in self.stage_results:
            model = requested[row.stage]
            if (
                row.provider_id,
                row.model_id,
                row.model_revision,
                row.configuration_digest,
            ) != (
                model.provider_id,
                model.model_id,
                model.model_revision,
                model.configuration_digest,
            ):
                raise ValueError("stage result provider model identity differs from the handoff request")
            if any(quantity.clock_id != self.clock_id for quantity in row.quantities):
                raise ValueError("consequence quantity clock differs from the integrity-event clock")
        all_computed = all(row.status == "computed" for row in self.stage_results)
        if self.scenario_status == "complete" and not all_computed:
            raise ValueError("a complete consequence scenario requires all stages to be computed")
        if self.scenario_status == "complete" and self.scenario_missing_items:
            raise ValueError("a complete consequence scenario cannot have missing items")
        if self.scenario_status != "complete" and not self.scenario_missing_items:
            raise ValueError("an incomplete consequence scenario must identify missing items")
        if any(not row.strip() for row in (*self.scenario_missing_items, *self.limitations)):
            raise ValueError("scenario missing items and limitations must be nonempty statements")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("consequence result payload digest does not match its content")
        return self


def consequence_scenario_handoff(**values) -> ConsequenceScenarioHandoff:
    """Bind a handoff without deriving a release opening from integrity damage."""

    unsigned = ConsequenceScenarioHandoff.model_validate(
        {**values, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return ConsequenceScenarioHandoff.model_validate(
        {**values, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )


def consequence_scenario_result_record(
    *,
    handoff: ConsequenceScenarioHandoff,
    result_record_id: str,
    stage_results,
    scenario_status,
    limitations,
    scenario_missing_items=(),
) -> ConsequenceScenarioResultRecord:
    """Bind provider stage results while preserving the integrity-event probability semantics."""

    values = {
        "result_record_id": result_record_id,
        "handoff_id": handoff.handoff_id,
        "scenario_id": handoff.scenario_id,
        "handoff_payload_digest": handoff.payload_digest,
        "event_id": handoff.event.event_id,
        "event_probability": handoff.event.event_probability,
        "probability_semantics": handoff.event.probability_semantics,
        "probability_conditioning": handoff.event.probability_conditioning,
        "clock_id": handoff.event.clock_id,
        "requested_models": handoff.requested_models,
        "stage_results": stage_results,
        "scenario_status": scenario_status,
        "scenario_missing_items": scenario_missing_items,
        "limitations": limitations,
    }
    unsigned = ConsequenceScenarioResultRecord.model_validate(
        {**values, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return ConsequenceScenarioResultRecord.model_validate(
        {**values, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )
