"""Mean gasket contact pressure from a caller-supplied force and area basis."""

from __future__ import annotations

import math
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

MODEL_ID = "mechanics.gasket_nominal_contact_pressure"
SOURCE_ID = "caller_reviewed_gasket_mean_contact_pressure"


class GasketNominalContactPressureRequest(Contract):
    """Inputs for a uniform-area mean-pressure calculation.

    Supply either an already reviewed effective area or the inner and outer
    diameters of a circular annulus. The force must be the compressive gasket
    reaction for the same load state and boundary basis as the selected area.
    """

    assessment_id: str = Field(min_length=1)
    compressive_gasket_force_N: Nonnegative
    gasket_force_evidence: Evidence
    effective_contact_area_m2: Positive | None = None
    inner_diameter_m: Nonnegative | None = None
    outer_diameter_m: Positive | None = None
    geometry_evidence: Evidence
    force_area_scope_reviewed: bool
    uniform_mean_pressure_interpretation_reviewed: bool

    @model_validator(mode="after")
    def coherent_geometry(self):
        explicit_area = self.effective_contact_area_m2 is not None
        annulus_fields_present = self.inner_diameter_m is not None and self.outer_diameter_m is not None
        if explicit_area == annulus_fields_present:
            raise ValueError(
                "provide exactly one area basis: effective_contact_area_m2 or both annulus diameters"
            )
        if (self.inner_diameter_m is None) != (self.outer_diameter_m is None):
            raise ValueError("annulus geometry requires both inner and outer diameters")
        if annulus_fields_present:
            if self.outer_diameter_m is None or self.inner_diameter_m is None:
                raise ValueError("annulus geometry requires both inner and outer diameters")
            if self.outer_diameter_m <= self.inner_diameter_m:
                raise ValueError("outer diameter must be greater than inner diameter")
        if not self.force_area_scope_reviewed:
            raise ValueError("force and area must be reviewed as one physical load/contact scope")
        if not self.uniform_mean_pressure_interpretation_reviewed:
            raise ValueError("uniform-area mean-pressure interpretation must be reviewed")
        return self


def calculate_gasket_nominal_contact_pressure(
    request: GasketNominalContactPressureRequest,
) -> Calculation:
    """Calculate mean contact pressure ``force / effective area`` in pascals.

    For annular geometry, area is calculated as pi/4 times the difference of
    squared outer and inner diameters. No empirical gasket factor is applied.
    """
    if request.effective_contact_area_m2 is not None:
        area_m2 = request.effective_contact_area_m2
        area_basis = "caller_supplied_effective_contact_area"
    else:
        # The request validator ensures both values are present and ordered.
        inner_diameter_m = request.inner_diameter_m
        outer_diameter_m = request.outer_diameter_m
        if inner_diameter_m is None or outer_diameter_m is None:
            raise ValueError("annulus diameters are required when no effective area is supplied")
        area_m2 = math.pi * 0.25 * (outer_diameter_m**2 - inner_diameter_m**2)
        area_basis = "circular_annulus_from_caller_diameters"
    pressure_pa = request.compressive_gasket_force_N / area_m2
    if not math.isfinite(area_m2) or area_m2 <= 0 or not math.isfinite(pressure_pa):
        raise ValueError("computed area and mean pressure must be finite and physically positive/nonnegative")
    return Calculation(
        values={
            "assessment_id": request.assessment_id,
            "model_id": MODEL_ID,
            "compressive_gasket_force_N": request.compressive_gasket_force_N,
            "effective_contact_area_m2": area_m2,
            "area_basis": area_basis,
            "mean_contact_pressure_Pa": pressure_pa,
            "force_evidence": request.gasket_force_evidence.model_dump(mode="json"),
            "geometry_evidence": request.geometry_evidence.model_dump(mode="json"),
            "uniform_pressure_assumption": True,
        },
        notes=(
            "Mean pressure only; spatial contact-pressure distribution is not calculated.",
            "No leakage, seal qualification, code acceptance, flange flexibility, or gasket factor is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            MODEL_ID,
            GasketNominalContactPressureRequest,
            calculate_gasket_nominal_contact_pressure,
            {
                "compressive_gasket_force_N": "N",
                "effective_contact_area_m2": "m^2",
                "mean_contact_pressure_Pa": "Pa",
            },
            (
                "The compressive force and effective contact area refer to the same reviewed physical load state and scope.",
                "The returned pressure is a uniform-area mean descriptor and not a local contact solution.",
            ),
            (SOURCE_ID,),
        )
    ]
