"""Portable material, fabrication, weld and inspection evidence records."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import AwareDatetime, Field, model_validator

from .contracts import Contract, Evidence, Fraction, Nonnegative, Positive, check_finite


class MaterialRecord(Contract):
    schema_version: Literal["matintegrity.material.v1"] = "matintegrity.material.v1"
    material_id: str = Field(min_length=1)
    specification: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    product_form: str = Field(min_length=1)
    heat_id: str | None = None
    condition: str = Field(min_length=1)
    composition_mass_fraction: dict[str, Fraction] = Field(default_factory=dict)
    property_table_ids: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def composition(self):
        if sum(self.composition_mass_fraction.values()) > 1 + 1e-12:
            raise ValueError("composition mass fractions cannot exceed one")
        return self


class FlawRecord(Contract):
    id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    kind: Literal["thinning", "pit", "crack", "blister", "lamination", "misalignment", "other"]
    depth_m: Nonnegative | None = None
    length_m: Nonnegative | None = None
    width_m: Nonnegative | None = None
    wall_thickness_m: Positive | None = None
    orientation: str | None = None
    sizing_uncertainty_m: Nonnegative | None = None


class InspectionRecord(Contract):
    schema_version: Literal["matintegrity.inspection.v1"] = "matintegrity.inspection.v1"
    inspection_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    measured_at: AwareDatetime
    method: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    examined_fraction: Fraction | None = None
    outcome: Literal["indication", "no_indication", "inconclusive"]
    flaws: tuple[FlawRecord, ...] = ()
    probability_of_detection_model_id: str | None = None
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def identities(self):
        if any(f.asset_id != self.asset_id or f.location_id != self.location_id for f in self.flaws):
            raise ValueError("inspection flaw identity must match the inspected physical location")
        if self.outcome == "no_indication" and self.flaws:
            raise ValueError("a no-indication record cannot include reported flaws")
        return self


class WeldProcedureRecord(Contract):
    schema_version: Literal["matintegrity.weld_procedure.v1"] = "matintegrity.weld_procedure.v1"
    procedure_id: str = Field(min_length=1)
    qualification_record_id: str | None = None
    process: str = Field(min_length=1)
    base_material_ids: tuple[str, ...] = Field(min_length=1)
    filler_material_id: str | None = None
    parameters_si: dict[str, Any]
    qualified_domain: dict[str, Any]
    qualification_ruleset_id: str | None = None
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def finite(self):
        check_finite(self.parameters_si)
        check_finite(self.qualified_domain)
        return self


class HeatTreatmentRecord(Contract):
    schema_version: Literal["matintegrity.heat_treatment.v1"] = "matintegrity.heat_treatment.v1"
    record_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    time_s: list[Nonnegative] = Field(min_length=2)
    temperature_K: list[Positive] = Field(min_length=2)
    sensor_location: str = Field(min_length=1)
    acceptance_ruleset_id: str | None = None
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def align(self):
        if len(self.time_s) != len(self.temperature_K) or any(
            b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)
        ):
            raise ValueError("heat-treatment vectors require one increasing clock")
        return self
