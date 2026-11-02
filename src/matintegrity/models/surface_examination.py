"""Procedure-bound surface-examination records without embedded acceptance rules."""

from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class SurfaceExaminationArea(Contract):
    area_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    target_area_m2: Positive
    examined_area_m2: Nonnegative
    unexamined_basis: str | None = None

    @model_validator(mode="after")
    def valid_coverage(self):
        if self.examined_area_m2 > self.target_area_m2:
            raise ValueError("examined surface area cannot exceed target area")
        if self.examined_area_m2 < self.target_area_m2 and not self.unexamined_basis:
            raise ValueError("incomplete surface coverage requires an unexamined basis")
        return self


class SurfaceIndication(Contract):
    indication_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    location_description: str = Field(min_length=1)
    measured_length_m: Nonnegative | None = None
    measured_width_m: Nonnegative | None = None
    evidence: list[Evidence] = Field(min_length=1)


def _validate_surface_identities(areas, indications):
    area_ids = [area.area_id for area in areas]
    if len(set(area_ids)) != len(area_ids):
        raise ValueError("surface examination area IDs must be unique")
    indication_ids = [item.indication_id for item in indications]
    if len(set(indication_ids)) != len(indication_ids):
        raise ValueError("surface indication IDs must be unique")
    if {item.area_id for item in indications} - set(area_ids):
        raise ValueError("every surface indication must reference a declared area")


def _surface_values(areas, indications):
    target = sum(area.target_area_m2 for area in areas)
    examined = sum(area.examined_area_m2 for area in areas)
    lengths = [item.measured_length_m for item in indications if item.measured_length_m is not None]
    widths = [item.measured_width_m for item in indications if item.measured_width_m is not None]
    return {
        "target_area_m2": target,
        "examined_area_m2": examined,
        "unexamined_area_m2": target - examined,
        "coverage_fraction": examined / target,
        "area_count": len(areas),
        "incomplete_area_ids": [
            area.area_id for area in areas if area.examined_area_m2 < area.target_area_m2
        ],
        "indication_count": len(indications),
        "indication_counts_by_reported_type": dict(
            Counter(item.reported_indication_type for item in indications)
        ),
        "indication_ids": [item.indication_id for item in indications],
        "measured_length_count": len(lengths),
        "maximum_reported_indication_length_m": max(lengths, default=None),
        "measured_width_count": len(widths),
        "maximum_reported_indication_width_m": max(widths, default=None),
    }


class LiquidPenetrantExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    penetrant_type: Literal["visible", "fluorescent"]
    removal_method: Literal[
        "water_washable", "post_emulsifiable_lipophilic", "solvent_removable", "post_emulsifiable_hydrophilic"
    ]
    cleaner_batch_id: str = Field(min_length=1)
    penetrant_batch_id: str = Field(min_length=1)
    remover_or_emulsifier_batch_id: str = Field(min_length=1)
    developer_batch_id: str = Field(min_length=1)
    surface_material_id: str = Field(min_length=1)
    surface_condition: str = Field(min_length=1)
    precleaning_basis: str = Field(min_length=1)
    drying_basis: str = Field(min_length=1)
    examination_temperature_K: Positive
    penetrant_dwell_s: Positive
    excess_removal_basis: str = Field(min_length=1)
    developer_application_basis: str = Field(min_length=1)
    development_time_s: Positive
    observation_lighting_basis: str = Field(min_length=1)
    final_cleaning_basis: str = Field(min_length=1)
    areas: list[SurfaceExaminationArea] = Field(min_length=1)
    indications: list[SurfaceIndication] = Field(default_factory=list)
    areas_mutually_exclusive_reviewed: bool
    material_and_consumables_compatibility_reviewed: bool
    process_sequence_reviewed: bool
    temperature_and_times_reviewed: bool
    surface_condition_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities(self):
        _validate_surface_identities(self.areas, self.indications)
        return self


def liquid_penetrant_summary(x: LiquidPenetrantExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "areas_mutually_exclusive_reviewed",
            "material_and_consumables_compatibility_reviewed",
            "process_sequence_reviewed",
            "temperature_and_times_reviewed",
            "surface_condition_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    return Calculation(
        status="needs_data" if missing_reviews else "computed",
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "penetrant_type": x.penetrant_type,
            "removal_method": x.removal_method,
            "examination_temperature_K": x.examination_temperature_K,
            "penetrant_dwell_s": x.penetrant_dwell_s,
            "development_time_s": x.development_time_s,
            **_surface_values(x.areas, x.indications),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Process fields preserve the caller-controlled penetrant record and do not establish procedure compliance.",
            "Reported indications are not automatically relevant discontinuities, rejectable flaws or defect dimensions.",
            "A negative record does not establish flaw absence, probability of detection, life or failure probability.",
        ),
    )


class MagnetizationPass(Contract):
    pass_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    technique: str = Field(min_length=1)
    current_mode: Literal["ac", "dc", "half_wave_dc", "permanent_magnet", "other"]
    field_direction_rad: float = Field(ge=0, lt=math.pi)
    field_adequacy_basis: str = Field(min_length=1)
    equipment_id: str = Field(min_length=1)
    magnetizing_current_A: Positive | None = None


class MagneticParticleExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    surface_material_id: str = Field(min_length=1)
    surface_condition: str = Field(min_length=1)
    particle_medium: Literal["dry", "wet_visible", "wet_fluorescent"]
    particle_batch_id: str = Field(min_length=1)
    carrier_batch_id: str | None = None
    observation_lighting_basis: str = Field(min_length=1)
    minimum_direction_separation_rad: float = Field(gt=0, le=math.pi / 2)
    directional_coverage_requirement_basis: str = Field(min_length=1)
    areas: list[SurfaceExaminationArea] = Field(min_length=1)
    magnetization_passes: list[MagnetizationPass] = Field(min_length=1)
    indications: list[SurfaceIndication] = Field(default_factory=list)
    areas_mutually_exclusive_reviewed: bool
    ferromagnetic_applicability_reviewed: bool
    equipment_and_media_reviewed: bool
    field_adequacy_reviewed: bool
    directional_requirement_reviewed: bool
    surface_condition_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities(self):
        _validate_surface_identities(self.areas, self.indications)
        area_ids = {area.area_id for area in self.areas}
        pass_ids = [item.pass_id for item in self.magnetization_passes]
        if len(set(pass_ids)) != len(pass_ids):
            raise ValueError("magnetization pass IDs must be unique")
        if {item.area_id for item in self.magnetization_passes} - area_ids:
            raise ValueError("every magnetization pass must reference a declared area")
        return self


def _maximum_unoriented_separation(directions: list[float]) -> float:
    if len(directions) < 2:
        return 0.0
    return max(
        min(abs(left - right), math.pi - abs(left - right))
        for index, left in enumerate(directions)
        for right in directions[index + 1 :]
    )


def magnetic_particle_summary(x: MagneticParticleExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "areas_mutually_exclusive_reviewed",
            "ferromagnetic_applicability_reviewed",
            "equipment_and_media_reviewed",
            "field_adequacy_reviewed",
            "directional_requirement_reviewed",
            "surface_condition_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    directions_by_area = {
        area.area_id: [
            item.field_direction_rad for item in x.magnetization_passes if item.area_id == area.area_id
        ]
        for area in x.areas
    }
    maximum_separation = {
        area_id: _maximum_unoriented_separation(directions)
        for area_id, directions in directions_by_area.items()
    }
    insufficient = [
        area_id
        for area_id, separation in maximum_separation.items()
        if separation < x.minimum_direction_separation_rad
    ]
    return Calculation(
        status="needs_data" if missing_reviews or insufficient else "computed",
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "particle_medium": x.particle_medium,
            **_surface_values(x.areas, x.indications),
            "magnetization_pass_count": len(x.magnetization_passes),
            "magnetization_pass_count_by_area": {
                area_id: len(directions) for area_id, directions in directions_by_area.items()
            },
            "maximum_unoriented_direction_separation_rad_by_area": maximum_separation,
            "minimum_direction_separation_rad": x.minimum_direction_separation_rad,
            "insufficient_direction_area_ids": insufficient,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Directional coverage is compared only with the caller-declared reviewed separation requirement.",
            "Field direction and adequacy records do not establish subsurface sensitivity or procedure compliance.",
            "Reported indications are not automatically relevant discontinuities, rejectable flaws, defect dimensions, life or failure probability.",
        ),
    )


def specifications():
    common_units = {
        "target_area_m2": "m^2",
        "examined_area_m2": "m^2",
        "unexamined_area_m2": "m^2",
        "coverage_fraction": "1",
        "maximum_reported_indication_length_m": "m",
        "maximum_reported_indication_width_m": "m",
    }
    return [
        ModelSpec(
            "inspection.liquid_penetrant_summary",
            LiquidPenetrantExamination,
            liquid_penetrant_summary,
            {
                **common_units,
                "examination_temperature_K": "K",
                "penetrant_dwell_s": "s",
                "development_time_s": "s",
            },
            (
                "Caller-controlled material, consumables, sequence, temperature, time, lighting, coverage and indication records; no embedded acceptance rule.",
            ),
            ("liquid_penetrant_examination_definition",),
        ),
        ModelSpec(
            "inspection.magnetic_particle_summary",
            MagneticParticleExamination,
            magnetic_particle_summary,
            {
                **common_units,
                "maximum_unoriented_direction_separation_rad_by_area": "rad",
                "minimum_direction_separation_rad": "rad",
            },
            (
                "Caller-reviewed ferromagnetic applicability, media, equipment, field adequacy, directional requirement, coverage and indication records; no embedded acceptance rule.",
            ),
            ("magnetic_particle_examination_definition",),
        ),
    ]
