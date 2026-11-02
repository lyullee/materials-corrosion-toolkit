"""Caller-supplied design-property tables with exact condition and edition matching."""

from __future__ import annotations

from typing import Protocol

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive, canonical_digest
from .data import TabulatedProperty
from .units import convert


class PropertyIdentity(Contract):
    material_id: str = Field(min_length=1)
    product_form: str = Field(min_length=1)
    material_condition: str = Field(min_length=1)
    orientation: str = Field(min_length=1)
    property_id: str = Field(min_length=1)
    basis_id: str = Field(min_length=1)
    basis_edition: str = Field(min_length=1)


class PropertyQuery(Contract):
    identity: PropertyIdentity
    temperature_K: Positive
    requested_unit: str = Field(min_length=1)


class DesignPropertyTable(Contract):
    identity: PropertyIdentity
    temperature_table: TabulatedProperty
    evidence: Evidence
    permitted_use_note: str = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        table = self.temperature_table
        if table.x_unit != "K" or min(table.x) <= 0:
            raise ValueError("design-property temperature coordinates must be absolute kelvin")
        if table.property_id != self.identity.property_id or table.source_id != self.evidence.source_id:
            raise ValueError(
                "table property/source identifiers must match the declared identity and evidence"
            )
        if not self.evidence.license_id:
            raise ValueError("a caller-declared license or entitlement identifier is required")
        return self


class PropertyProvider(Protocol):
    def resolve(self, query: PropertyQuery) -> dict: ...


class TabulatedPropertyProvider:
    def __init__(self, tables: list[DesignPropertyTable]):
        self._tables = {}
        for table in tables:
            snapshot = table.model_copy(deep=True)
            key = canonical_digest(snapshot.identity.model_dump(mode="json"))
            if key in self._tables:
                raise ValueError(
                    "duplicate property identity; reconcile temperature ranges and revisions explicitly"
                )
            self._tables[key] = snapshot

    def resolve(self, query: PropertyQuery) -> dict:
        if not isinstance(query, PropertyQuery):
            raise TypeError("an explicit PropertyQuery is required")
        key = canonical_digest(query.identity.model_dump(mode="json"))
        if key not in self._tables:
            return dict(
                status="needs_data",
                value=None,
                unit=query.requested_unit,
                reason="No exact material, product, condition, orientation and basis-edition match.",
            )
        table = self._tables[key]
        curve = table.temperature_table
        if not curve.x[0] <= query.temperature_K <= curve.x[-1]:
            return dict(
                status="out_of_scope",
                value=None,
                unit=query.requested_unit,
                reason="Temperature is outside the supplied property domain.",
            )
        try:
            original = curve.at(query.temperature_K)
            value = convert(original, curve.y_unit, query.requested_unit)
            if original != 0 and value == 0 and convert(0, curve.y_unit, query.requested_unit) == 0:
                raise ArithmeticError("nonzero property conversion underflows")
        except (ArithmeticError, ValueError):
            return dict(
                status="out_of_scope",
                value=None,
                unit=query.requested_unit,
                reason="Property interpolation or numeric unit conversion exceeds support.",
            )
        return dict(
            schema_version="matintegrity.property.v1",
            status="computed",
            value=value,
            unit=query.requested_unit,
            query=query.model_dump(mode="json"),
            evidence=table.evidence.model_dump(mode="json"),
            permitted_use_note=table.permitted_use_note,
            table_digest=canonical_digest(table.model_dump(mode="json")),
            query_digest=canonical_digest(query.model_dump(mode="json")),
        )
