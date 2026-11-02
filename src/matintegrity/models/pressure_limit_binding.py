"""Explicit pressure-difference to common-pressure component-limit binding."""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Contract, Evidence, Nonnegative, canonical_digest
from .component_pressure_reference import ComponentPressureLimit, ComponentPressureReference
from .declared_pressure_relation import (
    DeclaredPressureThicknessRelation,
    declared_pressure_thickness_relation,
)


class PressureLimitReferenceContext(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    component_elevation_m: float
    pressure_basis: Literal["absolute", "gauge_common_reference"]
    common_pressure_reference_id: str = Field(min_length=1)
    external_absolute_pressure_Pa: Nonnegative
    common_reference_absolute_pressure_Pa: Nonnegative
    external_pressure_and_common_reference_reviewed: bool
    component_scenario_and_coordinate_mapping_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def absolute_zero_reference(self):
        if self.pressure_basis == "absolute" and self.common_reference_absolute_pressure_Pa != 0:
            raise ValueError("absolute output requires zero absolute reference pressure")
        return self


def _derive(relation, reference):
    relation = DeclaredPressureThicknessRelation.model_validate_json(relation.model_dump_json())
    reference = PressureLimitReferenceContext.model_validate_json(reference.model_dump_json())
    if (relation.asset_id, relation.location_id) != (reference.asset_id, reference.location_id):
        raise ValueError("relation and pressure-reference asset/location must match")
    if relation.direction != "pressure_from_thickness":
        raise ValueError("only forward capacity evaluation can supply a component upper limit")
    if not (
        reference.external_pressure_and_common_reference_reviewed
        and reference.component_scenario_and_coordinate_mapping_reviewed
    ):
        raise ValueError("pressure-reference conversion and physical mapping require review")
    calculation = declared_pressure_thickness_relation(relation)
    if calculation.status != "computed":
        raise ValueError("uncomputed pressure relations cannot supply component limits")
    pressure = (
        Fraction(calculation.values["pressure_difference_Pa"])
        + Fraction(reference.external_absolute_pressure_Pa)
        - Fraction(reference.common_reference_absolute_pressure_Pa)
    )
    try:
        converted = float(pressure)
        if converted <= 0 or not math.isfinite(converted):
            raise ArithmeticError
    except ArithmeticError as exc:
        raise ValueError("converted component upper limit must be positive and representable") from exc
    input_digest = canonical_digest(
        dict(relation=relation.model_dump(mode="json"), reference=reference.model_dump(mode="json"))
    )
    result_digest = canonical_digest(
        dict(
            calculation=calculation.model_dump(mode="json"),
            reference=reference.model_dump(mode="json"),
            converted_pressure_limit_Pa=converted,
        )
    )
    return ComponentPressureLimit(
        component_id=relation.component_id,
        pressure_limit_Pa=converted,
        elevation_m=reference.component_elevation_m,
        condition_id=reference.condition_id,
        temperature_K=relation.temperature_K,
        capacity_input_digest=input_digest,
        capacity_result_digest=result_digest,
        evidence=relation.basis.evidence + reference.evidence,
    )


class PressureLimitBinding(Contract):
    relation: DeclaredPressureThicknessRelation
    reference: PressureLimitReferenceContext
    component_limit: ComponentPressureLimit
    binding_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_binding(self):
        if self.component_limit != _derive(self.relation, self.reference):
            raise ValueError("component limit does not match bound relation and pressure conversion")
        if self.binding_digest != canonical_digest(self.model_dump(mode="json", exclude={"binding_digest"})):
            raise ValueError("pressure-limit binding digest mismatch")
        return self


def bind_pressure_relation_component_limit(
    relation: DeclaredPressureThicknessRelation,
    reference: PressureLimitReferenceContext,
) -> PressureLimitBinding:
    """Keep this complete binding alongside the aggregation component_limit."""
    component = _derive(relation, reference)
    values = dict(
        relation=relation.model_dump(mode="json"),
        reference=reference.model_dump(mode="json"),
        component_limit=component.model_dump(mode="json"),
    )
    return PressureLimitBinding(
        relation=relation,
        reference=reference,
        component_limit=component,
        binding_digest=canonical_digest(values),
    )


def verify_pressure_reference_bindings(
    aggregation: ComponentPressureReference, bindings: tuple[PressureLimitBinding, ...]
) -> None:
    """Validate complete, one-to-one binding scope before running aggregation."""
    if len(bindings) != len(aggregation.components):
        raise ValueError("one binding is required per aggregation component")
    indexed = {binding.component_limit.component_id: binding for binding in bindings}
    if len(indexed) != len(bindings):
        raise ValueError("binding component identities must be unique")
    reference_values = set()
    for component in aggregation.components:
        binding = indexed.get(component.component_id)
        if binding is None or binding.component_limit != component:
            raise ValueError("aggregation component does not match its complete binding")
        # Revalidate serialized content as model_copy can bypass validators.
        binding = PressureLimitBinding.model_validate_json(binding.model_dump_json())
        for field in (
            "asset_id",
            "location_id",
            "physical_scope_id",
            "condition_id",
            "coordinate_frame_id",
            "pressure_basis",
            "common_pressure_reference_id",
        ):
            if getattr(binding.reference, field) != getattr(aggregation, field):
                raise ValueError(f"aggregation and binding {field} must match")
        reference_values.add(binding.reference.common_reference_absolute_pressure_Pa)
    if len(reference_values) != 1:
        raise ValueError("all bindings must use the same absolute common-reference pressure")
