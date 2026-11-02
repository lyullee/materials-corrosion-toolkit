"""Provider-neutral API-581-style damage result exchange without probability relabelling."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest


class Api581WallFlawMaterialState(Contract):
    state_id: str = Field(min_length=1)
    wall_thickness_value: Positive
    wall_thickness_unit_token: str = Field(min_length=1)
    wall_thickness_basis: str = Field(min_length=1)
    flaw_definition_id: str = Field(min_length=1)
    flaw_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    material_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    state_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class Api581InspectionLineage(Contract):
    inspection_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    inspection_time_s: Nonnegative
    physical_scope_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    inspection_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class Api581DamageExchangeRecord(Contract):
    schema_version: Literal["matintegrity.api581_damage_exchange.v1"] = (
        "matintegrity.api581_damage_exchange.v1"
    )
    exchange_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    survival_conditioning: str = Field(min_length=1)
    damage_mechanism_id: str = Field(min_length=1)
    damage_mechanism_definition: str = Field(min_length=1)
    wall_flaw_material_state: Api581WallFlawMaterialState
    inspection_lineage: tuple[Api581InspectionLineage, ...]
    status: Literal["computed", "needs_data", "out_of_scope"]
    status_basis: str = Field(min_length=1)
    damage_factor: Nonnegative | None = None
    damage_factor_definition: str | None = None
    damage_factor_unit_token: str | None = None
    probability_of_failure: Fraction | None = None
    probability_semantics: Literal["conditional_first_failure_in_period"] | None = None
    probability_event_definition: str | None = None
    inspection_pod: Fraction | None = None
    inspection_pod_semantics: Literal["detection_given_flaw_and_procedure"] | None = None
    spatial_exceedance_probability: Fraction | None = None
    spatial_probability_semantics: Literal["spatial_size_exceedance_at_one_exposure"] | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = Field(min_length=1)
    acceptance_claim: Literal[False] = False
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def semantics_and_binding(self, info: ValidationInfo):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("API 581 exchange horizon must have positive duration")
        if self.wall_flaw_material_state.state_id == self.exchange_id:
            raise ValueError("state and exchange identifiers must remain distinct")
        if any(row.physical_scope_id != self.physical_scope_id for row in self.inspection_lineage):
            raise ValueError("inspection lineage physical scope must match the exchange")
        inspection_ids = [row.inspection_id for row in self.inspection_lineage]
        if len(set(inspection_ids)) != len(inspection_ids):
            raise ValueError("inspection lineage IDs must be unique")
        damage_fields = (
            self.damage_factor,
            self.damage_factor_definition,
            self.damage_factor_unit_token,
        )
        if any(value is not None for value in damage_fields) and any(
            value is None for value in damage_fields
        ):
            raise ValueError("damage factor value, definition and unit must be supplied together")
        pof_fields = (
            self.probability_of_failure,
            self.probability_semantics,
            self.probability_event_definition,
        )
        if any(value is not None for value in pof_fields) and any(value is None for value in pof_fields):
            raise ValueError("PoF value, semantics and event definition must be supplied together")
        if (self.inspection_pod is None) != (self.inspection_pod_semantics is None):
            raise ValueError("POD value and detection semantics must be supplied together")
        if (self.spatial_exceedance_probability is None) != (self.spatial_probability_semantics is None):
            raise ValueError("spatial probability value and semantics must be supplied together")
        result_values = (
            self.damage_factor,
            self.probability_of_failure,
            self.inspection_pod,
            self.spatial_exceedance_probability,
        )
        if self.status == "computed":
            if self.provider_result_digest is None or not any(value is not None for value in result_values):
                raise ValueError("computed API 581 exchange requires a result digest and reported result")
        elif self.provider_result_digest is not None or any(value is not None for value in result_values):
            raise ValueError("needs-data or out-of-scope exchange cannot carry computed result values")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("API 581 exchange limitations must be nonempty")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("API 581 exchange payload digest does not match its content")
        return self


def api581_damage_exchange_record(**payload) -> Api581DamageExchangeRecord:
    """Bind one external damage result without converting damage, POD or spatial metrics to PoF."""

    unsigned = Api581DamageExchangeRecord.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return Api581DamageExchangeRecord.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )
