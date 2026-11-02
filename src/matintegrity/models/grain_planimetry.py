"""Observed planar grain counts with an explicit caller calibration."""

from __future__ import annotations

import math
from fractions import Fraction

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest


class GrainCountField(Contract):
    field_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    image_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    counting_region_id: str = Field(min_length=1)
    specimen_plane_area_m2: Positive
    effective_grain_count: Nonnegative


class GrainPlanimetrySummary(CorrelationRequest):
    physical_specimen_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    phase_id: str = Field(min_length=1)
    counting_procedure_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    reference_number: float
    reference_areal_density_per_m2: Positive
    number_increment_per_density_doubling: Positive
    fields: tuple[GrainCountField, ...] = Field(min_length=1, max_length=10000)
    specimen_area_boundary_counting_and_nonoverlap_reviewed: bool
    population_and_number_calibration_reviewed: bool

    @model_validator(mode="after")
    def unique_fields(self):
        if any(row.physical_specimen_id != self.physical_specimen_id for row in self.fields):
            raise ValueError("grain fields must belong to the same physical specimen")
        if len({row.field_id for row in self.fields}) != len(self.fields):
            raise ValueError("grain counting field identities must be unique")
        if len({(row.image_sha256, row.counting_region_id) for row in self.fields}) != len(self.fields):
            raise ValueError("the same physical image counting region cannot be counted twice")
        return self


def grain_planimetry_summary(x: GrainPlanimetrySummary) -> Calculation:
    base = dict(
        physical_specimen_id=x.physical_specimen_id,
        material_condition_id=x.material_condition_id,
        phase_id=x.phase_id,
        counting_procedure_id=x.counting_procedure_id,
        calibration_id=x.calibration_id,
        record_sha256=x.basis.record_sha256,
    )
    if not (
        x.specimen_area_boundary_counting_and_nonoverlap_reviewed
        and x.population_and_number_calibration_reviewed
    ):
        return Calculation(
            status="needs_data",
            values=base,
            notes=(
                "Specimen-plane area, effective boundary counts, disjoint fields and calibration require review.",
            ),
        )
    count = sum((Fraction(row.effective_grain_count) for row in x.fields), Fraction(0))
    area = sum((Fraction(row.specimen_plane_area_m2) for row in x.fields), Fraction(0))
    if count == 0:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Zero observed effective grains do not define a positive grain density or number.",),
        )
    density = count / area
    ratio = density / Fraction(x.reference_areal_density_per_m2)
    try:
        if Fraction(1, 2) <= ratio <= 2:
            difference = ratio - 1
            delta = float(difference)
            if difference and delta == 0:
                raise ArithmeticError("density contrast is not representable")
            logarithm = math.log1p(delta) / math.log(2)
        else:
            logarithm = math.log2(ratio.numerator) - math.log2(ratio.denominator)
        exact_number = Fraction(x.reference_number) + Fraction(
            x.number_increment_per_density_doubling
        ) * Fraction(logarithm)
        number = float(exact_number)
        if exact_number and number == 0:
            raise ArithmeticError("nonzero calibrated number is not representable")
        exact = dict(
            total_effective_count=count,
            total_specimen_area_m2=area,
            areal_grain_density_per_m2=density,
            mean_planar_area_per_grain_m2=area / count,
        )
        values = {key: float(value) for key, value in exact.items()}
        if not math.isfinite(number) or any(
            not math.isfinite(values[key]) or values[key] == 0 for key in exact
        ):
            raise ArithmeticError("required grain summary output is not representable")
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Required planar grain outputs exceed numeric support.",),
        )
    return Calculation(
        values=base | values | dict(calibrated_grain_number=number),
        notes=(
            "Pooled effective counts divided by pooled specimen-plane area; fields are not weighted equally unless their areas match.",
            "Caller effective boundary counting and number calibration only. No image segmentation, twin exclusion, grain-size distribution, 3-D size, property prediction, method qualification or acceptance is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "testing.grain_planimetry_summary",
            GrainPlanimetrySummary,
            grain_planimetry_summary,
            {
                "total_effective_count": "1",
                "total_specimen_area_m2": "m^2",
                "areal_grain_density_per_m2": "1/m^2",
                "mean_planar_area_per_grain_m2": "m^2",
                "calibrated_grain_number": "1",
            },
            (
                "Caller-reviewed specimen-plane areas, effective boundary counts and logarithmic number calibration are explicit.",
            ),
            (SOURCE_ID,),
            version="1.0.1",
            qualification="user_model",
        )
    ]
