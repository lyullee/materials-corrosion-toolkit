"""Unexecuted local example. Replace density and evidence with reviewed inputs."""

from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.ti12mo5zr_mass_balance import (
    Ti12Mo5ZrMassBalanceRequest,
    calculate_mass_balance,
)


def caller_approved_conversion(archive_path: Path, reviewed_density_kg_m3: float):
    request = Ti12Mo5ZrMassBalanceRequest(
        local_archive_path=str(archive_path),
        density_kg_m3=reviewed_density_kg_m3,
        density_evidence=Evidence(
            source_id="caller-material-density",
            origin="user_declared",
            citation="Replace with the reviewed density source and specimen applicability.",
        ),
        alloy_label="Ti-12Mo-5Zr",
        analyzed_elements=("Ti", "Mo", "Zr"),
        computational_use_authorized=True,
        local_only_authorized=True,
        source_time_axis_is_valid_for_interval_integration=True,
        provider_positive_rate_means_outward_loss_reviewed=True,
        analyzed_element_coverage_is_complete_for_this_conversion=True,
        uniform_area_and_density_equivalent_penetration_reviewed=True,
        linear_interpolation_between_time_rows_reviewed=True,
        missing_values_are_not_imputed=True,
    )
    return calculate_mass_balance(request)


if __name__ == "__main__":
    # Synthetic unit example only; this block is intentionally not run here.
    # For real local use, provide an independently reviewed density and Evidence.
    synthetic_rates_ng_s_cm2 = (1.0, 2.0, 3.0)
    synthetic_density_kg_m3 = 6000.0
    synthetic_velocity_m_s = sum(synthetic_rates_ng_s_cm2) * 1.0e-8 / synthetic_density_kg_m3
    synthetic_10s_penetration_m = synthetic_velocity_m_s * 10.0
    print(synthetic_velocity_m_s, synthetic_10s_penetration_m)
