"""Map an explicitly selected SWT critical-plane parameter to caller-calibrated life."""

import math

from pydantic import Field, model_validator

from .contracts import Contract, Positive, canonical_digest
from .models.constitutive import SWTStrainLife, swt_strain_life


class CriticalPlaneFsLife(Contract):
    analysis_id: str = Field(min_length=1)
    plane_id: str = Field(min_length=1)
    plane_factor_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fatemi_socie_factor: Positive
    shear_modulus_Pa: Positive
    shear_fatigue_strength_coefficient_Pa: Positive
    shear_fatigue_strength_exponent: float = Field(lt=0)
    shear_fatigue_ductility_coefficient: Positive
    shear_fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    engineering_shear_amplitude_and_calibration_reviewed: bool

    @model_validator(mode="after")
    def interval(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("FS life support must be a nonempty cycle interval")
        return self


def evaluate_critical_plane_fs_life(request: CriticalPlaneFsLife) -> dict:
    base = dict(
        analysis_id=request.analysis_id,
        plane_id=request.plane_id,
        plane_factor_result_sha256=request.plane_factor_result_sha256,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        cycles_to_failure=None,
    )
    if not request.engineering_shear_amplitude_and_calibration_reviewed:
        return base
    from scipy.optimize import brentq

    elastic = math.log(request.shear_fatigue_strength_coefficient_Pa) - math.log(request.shear_modulus_Pa)
    plastic = math.log(request.shear_fatigue_ductility_coefficient)
    target = math.log(request.fatemi_socie_factor)

    def residual(log_cycles):
        reversals = math.log(2) + log_cycles
        first = elastic + request.shear_fatigue_strength_exponent * reversals
        second = plastic + request.shear_fatigue_ductility_exponent * reversals
        maximum = max(first, second)
        return maximum + math.log(math.exp(first - maximum) + math.exp(second - maximum)) - target

    low, high = math.log(request.minimum_valid_cycles), math.log(request.maximum_valid_cycles)
    if residual(low) < 0 or residual(high) > 0:
        return base | dict(
            status="out_of_scope", reason="FS parameter has no root within calibrated cycle support"
        )
    cycles = math.exp(brentq(residual, low, high, xtol=1e-12))
    return base | dict(
        status="computed",
        cycles_to_failure=cycles,
        reversals_to_failure=2 * cycles,
        basis="Caller-calibrated engineering-shear life relation applied to an identified FS factor. No plane search, load counting or nonproportional material calibration is inferred.",
    )


class CriticalPlaneSwtLife(Contract):
    analysis_id: str = Field(min_length=1)
    plane_id: str = Field(min_length=1)
    plane_factor_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_normal_stress_Pa: Positive
    normal_strain_amplitude: Positive
    elastic_modulus_Pa: Positive
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    plane_measure_range_and_material_calibration_reviewed: bool


def evaluate_critical_plane_swt_life(request: CriticalPlaneSwtLife) -> dict:
    inputs = SWTStrainLife(
        strain_amplitude=request.normal_strain_amplitude,
        maximum_stress_Pa=request.maximum_normal_stress_Pa,
        elastic_modulus_Pa=request.elastic_modulus_Pa,
        fatigue_strength_coefficient_Pa=request.fatigue_strength_coefficient_Pa,
        fatigue_strength_exponent=request.fatigue_strength_exponent,
        fatigue_ductility_coefficient=request.fatigue_ductility_coefficient,
        fatigue_ductility_exponent=request.fatigue_ductility_exponent,
        minimum_valid_cycles=request.minimum_valid_cycles,
        maximum_valid_cycles=request.maximum_valid_cycles,
        stress_and_strain_measurement_basis_reviewed=request.plane_measure_range_and_material_calibration_reviewed,
        material_applicability_reviewed=request.plane_measure_range_and_material_calibration_reviewed,
    )
    result = swt_strain_life(inputs)
    return dict(
        analysis_id=request.analysis_id,
        plane_id=request.plane_id,
        plane_factor_result_sha256=request.plane_factor_result_sha256,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status=result.status,
        values=result.values,
        notes=result.notes,
    )
