"""Weld consumable records compared with caller-owned compatibility declarations."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class ConsumableCompatibilityDeclaration(Contract):
    declaration_id: str = Field(min_length=1)
    base_material_condition_ids: tuple[str, str]
    consumable_lot_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    service_environment_id: str = Field(min_length=1)
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    declaration_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if any(not identifier.strip() for identifier in self.base_material_condition_ids):
            raise ValueError("both base-material condition identifiers are required")
        if self.maximum_supported_temperature_K < self.minimum_supported_temperature_K:
            raise ValueError("compatibility temperature support must be ordered")
        return self


class ProductionConsumableRecord(Contract):
    weld_id: str = Field(min_length=1)
    base_material_condition_ids: tuple[str, str]
    consumable_lot_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    service_environment_id: str = Field(min_length=1)
    minimum_service_temperature_K: Positive
    maximum_service_temperature_K: Positive
    record_valid: bool
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_service(self):
        if any(not identifier.strip() for identifier in self.base_material_condition_ids):
            raise ValueError("both production base-material condition identifiers are required")
        if self.maximum_service_temperature_K < self.minimum_service_temperature_K:
            raise ValueError("service temperature range must be ordered")
        if not self.record_valid and not self.missing_basis:
            raise ValueError("an invalid production record requires a missing-data basis")
        return self


class WeldConsumableCompatibility(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    production_records: tuple[ProductionConsumableRecord, ...] = Field(min_length=1)
    compatibility_declarations: tuple[ConsumableCompatibilityDeclaration, ...] = Field(min_length=1)
    production_identity_reviewed: bool
    material_identity_reviewed: bool
    consumable_traceability_reviewed: bool
    service_conditions_reviewed: bool
    declaration_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_identifiers(self):
        weld_ids = [record.weld_id for record in self.production_records]
        declaration_ids = [item.declaration_id for item in self.compatibility_declarations]
        if len(weld_ids) != len(set(weld_ids)):
            raise ValueError("production weld identifiers must be unique")
        if len(declaration_ids) != len(set(declaration_ids)):
            raise ValueError("compatibility declaration identifiers must be unique")
        keys = [_declaration_key(item) for item in self.compatibility_declarations]
        if len(keys) != len(set(keys)):
            raise ValueError("compatibility declarations must have unique exact identity keys")
        return self


def _material_pair(identifiers: tuple[str, str]) -> tuple[str, str]:
    return tuple(sorted(identifiers))


def _declaration_key(item: ConsumableCompatibilityDeclaration) -> tuple:
    return (
        _material_pair(item.base_material_condition_ids),
        item.consumable_lot_id,
        item.welding_process_id,
        item.service_environment_id,
    )


def _record_key(item: ProductionConsumableRecord) -> tuple:
    return (
        _material_pair(item.base_material_condition_ids),
        item.consumable_lot_id,
        item.welding_process_id,
        item.service_environment_id,
    )


def weld_consumable_compatibility(x: WeldConsumableCompatibility) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "production_identity_reviewed",
            "material_identity_reviewed",
            "consumable_traceability_reviewed",
            "service_conditions_reviewed",
            "declaration_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_records = [record.weld_id for record in x.production_records if not record.record_valid]
    declarations = {_declaration_key(item): item for item in x.compatibility_declarations}
    rows = []
    unmatched = []
    outside = []
    for record in x.production_records:
        declaration = declarations.get(_record_key(record))
        if declaration is None:
            unmatched.append(record.weld_id)
            rows.append(
                {
                    "weld_id": record.weld_id,
                    "declaration_id": None,
                    "exact_identity_match": False,
                    "service_range_within_declaration": None,
                }
            )
            continue
        within = (
            record.minimum_service_temperature_K >= declaration.minimum_supported_temperature_K
            and record.maximum_service_temperature_K <= declaration.maximum_supported_temperature_K
        )
        if not within:
            outside.append(record.weld_id)
        rows.append(
            {
                "weld_id": record.weld_id,
                "declaration_id": declaration.declaration_id,
                "exact_identity_match": True,
                "service_range_within_declaration": within,
                "lower_temperature_margin_K": record.minimum_service_temperature_K
                - declaration.minimum_supported_temperature_K,
                "upper_temperature_margin_K": declaration.maximum_supported_temperature_K
                - record.maximum_service_temperature_K,
            }
        )

    status = "needs_data" if missing_reviews or invalid_records or unmatched else "computed"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "comparison_rows": rows,
            "unmatched_weld_ids": unmatched,
            "invalid_record_weld_ids": invalid_records,
            "outside_declared_temperature_support_weld_ids": outside,
            "missing_reviews": missing_reviews,
            "all_records_within_declared_compatibility": (not outside if status == "computed" else None),
        },
        notes=(
            "Declarations and their authority are caller-owned; no consumable classification, substitution or welding-code rule is bundled.",
            "An identity and temperature-range match does not establish weldability, mechanical properties, corrosion resistance or production acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("consumable-assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.consumable_compatibility",
            WeldConsumableCompatibility,
            weld_consumable_compatibility,
            {
                "assessment_id": "1",
                "comparison_rows": "mixed",
                "unmatched_weld_ids": "1",
                "invalid_record_weld_ids": "1",
                "outside_declared_temperature_support_weld_ids": "1",
                "missing_reviews": "1",
                "all_records_within_declared_compatibility": "1",
            },
            (
                "Base-material pair order is non-directional, while all material-condition, consumable-lot, process and service-environment identities must match exactly.",
                "Temperature support and declaration authority are supplied and reviewed by the caller.",
            ),
            ("declared_weld_consumable_compatibility",),
            context_validator=same_identity,
        )
    ]
