import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence
from matintegrity.models.hydrogen_kinetics import HydrogenSlab, LatticeBoundary, slab_kinetic
from matintegrity.models.welding import HydrogenBakeoutSlab, hydrogen_bakeout_slab


def request(**changes):
    return HydrogenBakeoutSlab(
        **(
            {
                "procedure_id": "authored-bakeout",
                "material_condition_id": "authored-steel",
                "diffusivity_source_id": "authored-diffusivity",
                "thickness_source_id": "authored-thickness",
                "elapsed_time_s": [0.0, 1000.0],
                "temperature_K": [473.15, 473.15],
                "effective_diffusivity_m2_s": [1e-8, 1e-8],
                "slab_thickness_m": 0.01,
                "initial_diffusible_hydrogen_atoms_mol_m3": 100.0,
                "both_faces_exposed_reviewed": True,
                "uniform_initial_concentration_reviewed": True,
                "diffusion_limited_surface_reviewed": True,
                "diffusivity_history_reviewed": True,
                "temperature_history_reviewed": True,
            }
            | changes
        )
    )


def test_characteristic_time_matches_finite_slab_eigenfunction_value():
    thickness, diffusivity = 0.01, 1e-8
    characteristic_time = thickness**2 / (math.pi**2 * diffusivity)
    result = hydrogen_bakeout_slab(
        request(elapsed_time_s=[0.0, characteristic_time], effective_diffusivity_m2_s=[diffusivity] * 2)
    )
    expected = sum(8 / math.pi**2 * math.exp(-((2 * n + 1) ** 2)) / (2 * n + 1) ** 2 for n in range(20))
    assert result.status == "computed"
    assert result.values["remaining_diffusible_fraction"][0] == 1.0
    assert result.values["remaining_diffusible_fraction"][-1] == pytest.approx(expected, abs=1e-10)
    assert result.values["series_tail_bound"][-1] <= 1e-10


def test_piecewise_diffusivity_histories_with_same_integral_have_same_release():
    first = hydrogen_bakeout_slab(
        request(
            elapsed_time_s=[0.0, 500.0, 1000.0],
            temperature_K=[400.0, 500.0, 400.0],
            effective_diffusivity_m2_s=[0.5e-8, 1.5e-8, 0.5e-8],
        )
    )
    second = hydrogen_bakeout_slab(request())
    assert first.values["diffusion_time_m2"][-1] == pytest.approx(second.values["diffusion_time_m2"][-1])
    assert first.values["remaining_diffusible_fraction"][-1] == pytest.approx(
        second.values["remaining_diffusible_fraction"][-1], abs=1e-13
    )


def test_finite_volume_no_trap_limit_agrees_after_mesh_refinement():
    authored = Evidence(source_id="authored", origin="synthetic", citation="authored cross-check")
    concentration = 100.0
    analytical = hydrogen_bakeout_slab(request())
    numerical = slab_kinetic(
        HydrogenSlab(
            material_condition_id="authored-steel",
            reference_lattice_id="authored-lattice",
            elapsed_time_origin_id="authored-clock",
            thickness_m=0.01,
            cell_count=80,
            lattice_site_density_mol_m3=1e6,
            initial_lattice_hydrogen_atoms_mol_m3=[concentration] * 80,
            elapsed_time_s=[0.0, 1000.0],
            uniform_temperature_K=[473.15, 473.15],
            lattice_diffusivity_m2_s=[1e-8, 1e-8],
            left_boundary=LatticeBoundary(
                boundary_id="left",
                kind="prescribed_lattice_concentration",
                lattice_hydrogen_atoms_mol_m3=[0.0, 0.0],
                evidence=(authored,),
            ),
            right_boundary=LatticeBoundary(
                boundary_id="right",
                kind="prescribed_lattice_concentration",
                lattice_hydrogen_atoms_mol_m3=[0.0, 0.0],
                evidence=(authored,),
            ),
            maximum_supported_lattice_occupancy=0.01,
            maximum_supported_total_trap_to_lattice_site_ratio=0.1,
            planar_geometry_reviewed=True,
            fixed_populations_and_uniform_temperature_reviewed=True,
            independent_single_occupancy_and_dilute_trap_regime_reviewed=True,
            negligible_stress_gradient_reviewed=True,
            detailed_balance_rate_ratio_reviewed=True,
            relative_tolerance=1e-5,
            maximum_relative_mass_balance_error=1e-6,
        )
    )
    assert numerical.status == "computed"
    numerical_fraction = numerical.values["lattice_mean_hydrogen_atoms_mol_m3"][-1] / concentration
    assert numerical_fraction == pytest.approx(
        analytical.values["remaining_diffusible_fraction"][-1], rel=0.003
    )


def test_missing_reviews_withhold_bakeout_claim():
    result = hydrogen_bakeout_slab(request(diffusivity_history_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["diffusivity_history_reviewed"]


def test_invalid_clock_alignment_and_unresolved_series_are_rejected_or_withheld():
    with pytest.raises(ValidationError):
        request(elapsed_time_s=[1.0, 2.0])
    with pytest.raises(ValidationError):
        request(temperature_K=[473.15])
    result = hydrogen_bakeout_slab(
        request(
            elapsed_time_s=[0.0, 1e-12],
            effective_diffusivity_m2_s=[1e-20, 1e-20],
            slab_thickness_m=1.0,
            maximum_series_terms=10,
        )
    )
    assert result.status == "out_of_scope"
