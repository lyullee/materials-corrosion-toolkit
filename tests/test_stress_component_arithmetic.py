import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredShellCharacteristicLengths,
    MeanShearStress,
    PlanarStressLinearization,
    declared_shell_characteristic_lengths,
    mean_shear_stress,
    planar_stress_linearization,
)
from matintegrity.registry import default_registry


def bind(cls, raw):
    digest = canonical_digest(raw)
    return cls(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored stress arithmetic.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def profile(**updates):
    raw = dict(
        physical_scope_id="section",
        load_case_id="case",
        coordinate_frame_id="frame",
        stress_component_definition_id="signed-normal-xx",
        position_m=(0.0, 0.25, 1.0),
        signed_stress_Pa=(0.0, 4.0, 0.0),
        section_model="constant_width_planar_piecewise_linear_component",
    )
    raw.update(updates)
    return bind(PlanarStressLinearization, raw)


def shear(**updates):
    raw = dict(
        physical_scope_id="section",
        force_direction_id="positive-y",
        signed_shear_force_N=-12.0,
        effective_shear_area_m2=0.25,
    )
    raw.update(updates)
    return bind(MeanShearStress, raw)


def lengths(**updates):
    raw = dict(
        physical_scope_id="shell",
        radius_definition_id="declared-mean-radius",
        radius_m=4.0,
        wall_thickness_m=0.25,
        declared_length_multipliers={"a": 1.0, "b": 3.0},
    )
    raw.update(updates)
    return bind(DeclaredShellCharacteristicLengths, raw)


def test_asymmetric_triangle_has_exact_section_resultants():
    values = planar_stress_linearization(profile()).values
    assert values["membrane_stress_Pa"] == 2.0
    assert values["bending_stress_at_start_Pa"] == 1.0
    assert values["bending_stress_at_end_Pa"] == -1.0
    assert values["membrane_force_per_unit_width_N_m"] == 2.0
    assert values["bending_moment_per_unit_width_N"] == pytest.approx(-1 / 6)
    assert [r["residual_stress_Pa"] for r in values["profile"]] == [-3.0, 1.5, -1.0]


def test_linear_signed_component_has_no_residual():
    values = planar_stress_linearization(profile(signed_stress_Pa=(-2.0, -1.0, 2.0))).values
    assert values["membrane_stress_Pa"] == 0.0
    assert values["bending_stress_at_start_Pa"] == -2.0
    assert values["bending_stress_at_end_Pa"] == 2.0
    assert values["maximum_absolute_residual_stress_Pa"] == 0.0


def test_constant_signed_component_has_only_membrane():
    values = planar_stress_linearization(profile(signed_stress_Pa=(-7.0, -7.0, -7.0))).values
    assert values["membrane_stress_Pa"] == -7.0
    assert values["bending_moment_per_unit_width_N"] == 0.0
    assert values["maximum_absolute_residual_stress_Pa"] == 0.0


def test_translation_and_thickness_scaling_preserve_stresses():
    values = planar_stress_linearization(profile(position_m=(-10.0, -9.5, -8.0))).values
    assert values["thickness_m"] == 2.0
    assert values["membrane_stress_Pa"] == 2.0
    assert values["bending_stress_at_start_Pa"] == 1.0
    assert values["membrane_force_per_unit_width_N_m"] == 4.0
    assert values["bending_moment_per_unit_width_N"] == pytest.approx(-2 / 3)


@pytest.mark.parametrize(
    "updates",
    [
        dict(position_m=(0.0, 0.0, 1.0)),
        dict(position_m=(1.0, 0.25, 0.0)),
        dict(signed_stress_Pa=(1.0, 2.0)),
    ],
)
def test_invalid_stress_profile_is_rejected(updates):
    with pytest.raises(ValueError):
        profile(**updates)


@pytest.mark.parametrize(
    "updates",
    [
        dict(position_m=(0.0, 0.5e308, 1e308), signed_stress_Pa=(1e308, 1e308, 1e308)),
        dict(position_m=(0.0, 0.5e-300, 1e-300), signed_stress_Pa=(1e-100, 1e-100, 1e-100)),
    ],
)
def test_unrepresentable_section_resultants_are_withheld(updates):
    assert planar_stress_linearization(profile(**updates)).status == "out_of_scope"


def test_mean_shear_retains_force_direction_and_zero():
    assert mean_shear_stress(shear()).values["signed_mean_shear_stress_Pa"] == -48.0
    assert mean_shear_stress(shear(signed_shear_force_N=0.0)).values["signed_mean_shear_stress_Pa"] == 0.0


@pytest.mark.parametrize("force,area", [(1e308, 1e-308), (5e-324, 1e308)])
def test_shear_numeric_range(force, area):
    assert (
        mean_shear_stress(shear(signed_shear_force_N=force, effective_shear_area_m2=area)).status
        == "out_of_scope"
    )


def test_shell_lengths_use_caller_multipliers():
    result = declared_shell_characteristic_lengths(lengths())
    assert result.values["sqrt_radius_thickness_m"] == 1.0
    assert result.values["declared_lengths_m"] == {"a": 1.0, "b": 3.0}


def test_shell_root_avoids_intermediate_product_overflow():
    result = declared_shell_characteristic_lengths(
        lengths(radius_m=1e308, wall_thickness_m=1e308, declared_length_multipliers={"a": 1.0})
    )
    assert result.status == "computed"
    assert result.values["sqrt_radius_thickness_m"] == pytest.approx(1e308)


def test_shell_multiplier_overflow_is_withheld():
    assert (
        declared_shell_characteristic_lengths(
            lengths(declared_length_multipliers={"a": 1e308}, radius_m=4.0, wall_thickness_m=1.0)
        ).status
        == "out_of_scope"
    )


@pytest.mark.parametrize(
    "builder,cls,field,value",
    [
        (profile, PlanarStressLinearization, "load_case_id", "changed"),
        (shear, MeanShearStress, "signed_shear_force_N", 1.0),
        (lengths, DeclaredShellCharacteristicLengths, "radius_m", 1.0),
    ],
)
def test_input_change_breaks_digest(builder, cls, field, value):
    raw = builder().model_dump()
    raw[field] = value
    with pytest.raises(ValueError, match="pin the complete"):
        cls.model_validate(raw)


@pytest.mark.parametrize(
    "builder,identifier",
    [
        (profile, "structural.planar_stress_linearization"),
        (shear, "structural.mean_shear_stress"),
        (lengths, "structural.declared_shell_characteristic_lengths"),
    ],
)
def test_public_python_json_exchange(builder, identifier):
    x = builder()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="section", time_basis="instant")
    a = registry.run(identifier, x, context)
    b = registry.run_json(identifier, x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
