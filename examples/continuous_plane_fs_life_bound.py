"""Synthetic wiring example for continuous-plane factor-to-life bounds."""

from matintegrity.contracts import Calculation, canonical_digest
from matintegrity.models.continuous_plane_life_bound import ContinuousPlaneFsLifeBound


factor_bound = Calculation(
    status="computed",
    values={
        "bound_is_certified_for_continuous_plane_over_supplied_sampled_cycle": True,
        "fatemi_socie_coefficient": 0.5,
        "normalization_stress_Pa": 300_000_000.0,
        "sampled_maximum_fatemi_socie_factor": 0.20,
        "fatemi_socie_continuous_upper_bound": 0.22,
        "fatemi_socie_bound_gap": 0.02,
        "fatemi_socie_bound_within_tolerance": False,
    },
)
calibration = {
    "criterion": "fatemi_socie",
    "calibrated_fatemi_socie_coefficient": 0.5,
    "calibrated_normalization_stress_Pa": 300_000_000.0,
    "shear_modulus_Pa": 80_000_000_000.0,
    "shear_fatigue_strength_coefficient_Pa": 100_000_000.0,
    "shear_fatigue_strength_exponent": -0.1,
    "shear_fatigue_ductility_coefficient": 0.5,
    "shear_fatigue_ductility_exponent": -0.5,
}
request = ContinuousPlaneFsLifeBound(
    analysis_id="synthetic-continuous-plane-life-bound",
    factor_bound_result=factor_bound,
    factor_bound_result_sha256=canonical_digest(factor_bound.model_dump(mode="json")),
    calibration=calibration,
    calibration_sha256=canonical_digest(calibration),
    minimum_valid_cycles=1.0,
    maximum_valid_cycles=1_000_000_000_000.0,
    continuous_plane_factor_to_life_monotonicity_reviewed=True,
)

# Pass `request` to ModelRegistry.run("fatigue.continuous_plane_fs_life_bound", request).
# Example inputs illustrate contracts only; they do not represent measured fatigue data.
