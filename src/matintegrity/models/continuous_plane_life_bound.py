"""Map a certified sampled-cycle plane-factor bound to a conservative life interval."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive, canonical_digest
from ..critical_plane_life import CriticalPlaneFsLife, evaluate_critical_plane_fs_life
from ..multiaxial_life_campaign import FsLifeCalibration


class ContinuousPlaneFsLifeBound(Contract):
    """Convert an FS continuous-plane factor bracket into a cycle-life bracket."""

    analysis_id: str = Field(min_length=1)
    factor_bound_result: Calculation
    factor_bound_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration: FsLifeCalibration
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    continuous_plane_factor_to_life_monotonicity_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_bound(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("cycle support must be a nonempty interval")
        if canonical_digest(self.factor_bound_result.model_dump(mode="json")) != self.factor_bound_result_sha256:
            raise ValueError("factor_bound_result_sha256 must match the supplied bound result")
        if canonical_digest(self.calibration.model_dump(mode="json")) != self.calibration_sha256:
            raise ValueError("calibration_sha256 must match the complete supplied calibration")
        values = self.factor_bound_result.values
        required = (
            "bound_is_certified_for_continuous_plane_over_supplied_sampled_cycle",
            "fatemi_socie_coefficient",
            "normalization_stress_Pa",
            "sampled_maximum_fatemi_socie_factor",
            "fatemi_socie_continuous_upper_bound",
            "fatemi_socie_bound_gap",
        )
        if self.factor_bound_result.status != "computed" or any(key not in values for key in required):
            raise ValueError("a computed FS continuous-plane bound result is required")
        if values["bound_is_certified_for_continuous_plane_over_supplied_sampled_cycle"] is not True:
            raise ValueError("the supplied factor result does not certify the declared continuous-plane bound")
        lower = values["sampled_maximum_fatemi_socie_factor"]
        upper = values["fatemi_socie_continuous_upper_bound"]
        gap = values["fatemi_socie_bound_gap"]
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (lower, upper, gap)):
            raise ValueError("factor bounds and gap must be numeric")
        if lower <= 0 or upper < lower or gap < 0:
            raise ValueError("factor bound must be finite, positive, and ordered")
        if not all(math.isfinite(value) for value in (lower, upper, gap)):
            raise ValueError("factor bounds and gap must be finite")
        if values["fatemi_socie_coefficient"] != self.calibration.calibrated_fatemi_socie_coefficient:
            raise ValueError("the FS factor bound coefficient must match the life calibration")
        if values["normalization_stress_Pa"] != self.calibration.calibrated_normalization_stress_Pa:
            raise ValueError("the FS factor bound normalization stress must match the life calibration")
        if abs((upper - lower) - gap) > 1e-10 * max(1.0, abs(upper), abs(lower)):
            raise ValueError("reported FS bound gap is inconsistent with its endpoints")
        return self


def map_continuous_plane_fs_bound_to_life(request: ContinuousPlaneFsLifeBound) -> Calculation:
    """Return a life interval induced by the certified FS factor interval.

    For the caller power-law strain-life calibration with negative exponents,
    life is monotonically decreasing in the positive FS factor. The factor upper
    bound therefore maps to a lower life bound and the sampled maximum maps to
    an upper life bound. Both roots must remain inside the declared support.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    values = request.factor_bound_result.values
    lower_factor = values["sampled_maximum_fatemi_socie_factor"]
    upper_factor = values["fatemi_socie_continuous_upper_bound"]
    base = dict(
        analysis_id=request.analysis_id,
        input_sha256=digest,
        factor_bound_result_sha256=request.factor_bound_result_sha256,
        calibration_sha256=request.calibration_sha256,
        sampled_maximum_fatemi_socie_factor=lower_factor,
        certified_continuous_plane_factor_upper_bound=upper_factor,
        factor_bound_gap=values["fatemi_socie_bound_gap"],
    )
    if not request.continuous_plane_factor_to_life_monotonicity_reviewed:
        return Calculation(status="needs_data", values=base | {"missing_review": "continuous_plane_factor_to_life_monotonicity_reviewed"})

    def life_at(factor: float) -> dict:
        return evaluate_critical_plane_fs_life(
            CriticalPlaneFsLife(
                analysis_id=request.analysis_id,
                plane_id="continuous-plane-bound",
                plane_factor_result_sha256=request.factor_bound_result_sha256,
                fatemi_socie_factor=factor,
                shear_modulus_Pa=request.calibration.shear_modulus_Pa,
                shear_fatigue_strength_coefficient_Pa=request.calibration.shear_fatigue_strength_coefficient_Pa,
                shear_fatigue_strength_exponent=request.calibration.shear_fatigue_strength_exponent,
                shear_fatigue_ductility_coefficient=request.calibration.shear_fatigue_ductility_coefficient,
                shear_fatigue_ductility_exponent=request.calibration.shear_fatigue_ductility_exponent,
                minimum_valid_cycles=request.minimum_valid_cycles,
                maximum_valid_cycles=request.maximum_valid_cycles,
                engineering_shear_amplitude_and_calibration_reviewed=True,
            )
        )

    minimum_life = life_at(upper_factor)
    maximum_life = life_at(lower_factor)
    if minimum_life["status"] != "computed" or maximum_life["status"] != "computed":
        return Calculation(
            status="out_of_scope",
            values=base | {
                "out_of_scope_reason": "the factor bracket endpoints do not both map to life roots inside declared cycle support",
                "life_at_factor_upper_bound": minimum_life,
                "life_at_sampled_factor_lower_bound": maximum_life,
            },
        )
    low_cycles = minimum_life["cycles_to_failure"]
    high_cycles = maximum_life["cycles_to_failure"]
    return Calculation(
        status="computed",
        values=base | {
            "minimum_cycles_to_failure_bound": low_cycles,
            "maximum_cycles_to_failure_bound": high_cycles,
            "life_interval_width_cycles": high_cycles - low_cycles,
            "factor_bound_within_requested_gap_tolerance": values.get("fatemi_socie_bound_within_tolerance"),
            "bound_is_conditional_on_supplied_sampled_tensor_cycle": True,
        },
        notes=(
            "The life interval follows from the certified FS factor bracket and the monotonically decreasing caller-calibrated FS life relation over the declared cycle support.",
            "The result does not include unsampled time behavior, calibration uncertainty, material transfer, cycle extraction error, or physical model error.",
        ),
    )
