import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredInverseSqrtDensityVelocity,
    DevicePressureDropCavitationIndex,
    HomogeneousNoSlipMixtureDensity,
    NoSlipPhaseFlow,
    declared_inverse_sqrt_density_velocity,
    device_pressure_drop_cavitation_index,
    homogeneous_no_slip_mixture_density,
)
from matintegrity.registry import default_registry


def bind(cls, raw):
    digest = canonical_digest(cls.model_construct(**raw).model_dump(mode="json", exclude={"basis"}))
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
                    citation="Authored flow arithmetic.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def mixture(flows=(("liquid", 2.0, 1000.0), ("gas", 1.0, 10.0))):
    return bind(
        HomogeneousNoSlipMixtureDensity,
        dict(
            physical_scope_id="pipe",
            condition_id="authored-state",
            phases=tuple(NoSlipPhaseFlow(phase_id=i, mass_flow_kg_s=m, density_kg_m3=d) for i, m, d in flows),
        ),
    )


def velocity(**updates):
    raw = dict(
        physical_scope_id="pipe",
        coefficient_basis_id="authored-SI",
        coefficient_SI=20.0,
        coefficient_unit="m/s*sqrt(kg/m^3)",
        mixture_density_kg_m3=100.0,
    )
    raw.update(updates)
    return bind(DeclaredInverseSqrtDensityVelocity, raw)


def cavitation(**updates):
    raw = dict(
        device_id="valve",
        condition_id="authored-state",
        inlet_pressure_location_id="tap-in",
        outlet_pressure_location_id="tap-out",
        vapor_pressure_basis_id="authored-property",
        inlet_absolute_pressure_Pa=500000.0,
        outlet_absolute_pressure_Pa=300000.0,
        vapor_pressure_Pa=100000.0,
    )
    raw.update(updates)
    return bind(DevicePressureDropCavitationIndex, raw)


def test_mixture_mass_and_volume_balance():
    values = homogeneous_no_slip_mixture_density(mixture()).values
    assert values["total_mass_flow_kg_s"] == 3.0
    assert values["total_volume_flow_m3_s"] == pytest.approx(0.102)
    assert values["mixture_density_kg_m3"] == pytest.approx(3.0 / 0.102)
    assert [r["phase_id"] for r in values["phase_volume_flows"]] == ["liquid", "gas"]


def test_zero_flow_phase_is_preserved_without_changing_density():
    values = homogeneous_no_slip_mixture_density(mixture((("a", 0.0, 1.0), ("b", 2.0, 900.0)))).values
    assert values["mixture_density_kg_m3"] == 900.0
    assert values["phase_volume_flows"][0]["volume_flow_m3_s"] == 0.0


def test_density_survives_unrepresentable_flow_totals():
    values = homogeneous_no_slip_mixture_density(mixture((("a", 1e308, 0.1), ("b", 1e308, 0.1)))).values
    assert values["mixture_density_kg_m3"] == 0.1
    assert values["total_mass_flow_kg_s"] is None
    assert values["total_volume_flow_m3_s"] is None


@pytest.mark.parametrize("flows", [(("a", 0.0, 1.0),), (("a", 1.0, 1.0), ("a", 2.0, 2.0))])
def test_invalid_phase_flow_group(flows):
    with pytest.raises(ValueError):
        mixture(flows)


def test_velocity_inverse_square_root_scaling_and_zero_coefficient():
    assert declared_inverse_sqrt_density_velocity(velocity()).values["velocity_descriptor_m_s"] == 2.0
    assert (
        declared_inverse_sqrt_density_velocity(velocity(mixture_density_kg_m3=400.0)).values[
            "velocity_descriptor_m_s"
        ]
        == 1.0
    )
    assert (
        declared_inverse_sqrt_density_velocity(velocity(coefficient_SI=0.0)).values["velocity_descriptor_m_s"]
        == 0.0
    )


@pytest.mark.parametrize(
    "updates",
    [
        dict(coefficient_SI=1e308, mixture_density_kg_m3=1e-300),
        dict(coefficient_SI=5e-324, mixture_density_kg_m3=1e308),
    ],
)
def test_velocity_numeric_range(updates):
    assert declared_inverse_sqrt_density_velocity(velocity(**updates)).status == "out_of_scope"


def test_velocity_rejects_customary_coefficient_unit():
    with pytest.raises(ValueError):
        velocity(coefficient_unit="ft/s*sqrt(lb/ft^3)")


@pytest.mark.parametrize("vapor,expected", [(100000.0, 2.0), (500000.0, 0.0), (600000.0, -0.5)])
def test_device_index_preserves_signed_margin(vapor, expected):
    result = device_pressure_drop_cavitation_index(cavitation(vapor_pressure_Pa=vapor))
    assert result.status == "computed"
    assert result.values["device_pressure_drop_cavitation_index"] == expected


@pytest.mark.parametrize("outlet", [500000.0, 600000.0])
def test_device_requires_positive_pressure_drop(outlet):
    result = device_pressure_drop_cavitation_index(cavitation(outlet_absolute_pressure_Pa=outlet))
    assert result.status == "out_of_scope"
    assert "device_pressure_drop_cavitation_index" not in result.values


def test_device_unrepresentable_ratio_is_withheld():
    result = device_pressure_drop_cavitation_index(
        cavitation(
            inlet_absolute_pressure_Pa=1e-300,
            outlet_absolute_pressure_Pa=5e-301,
            vapor_pressure_Pa=1e308,
        )
    )
    assert result.status == "out_of_scope"


@pytest.mark.parametrize(
    "builder,cls,field,value",
    [
        (mixture, HomogeneousNoSlipMixtureDensity, "condition_id", "changed"),
        (velocity, DeclaredInverseSqrtDensityVelocity, "coefficient_SI", 2.0),
        (cavitation, DevicePressureDropCavitationIndex, "vapor_pressure_Pa", 200000.0),
    ],
)
def test_changed_inputs_break_digest(builder, cls, field, value):
    raw = builder().model_dump()
    raw[field] = value
    with pytest.raises(ValueError, match="pin the complete"):
        cls.model_validate(raw)


@pytest.mark.parametrize(
    "builder,identifier",
    [
        (mixture, "flow.homogeneous_no_slip_mixture_density"),
        (velocity, "flow.declared_inverse_sqrt_density_velocity"),
        (cavitation, "degradation.device_pressure_drop_cavitation_index"),
    ],
)
def test_public_python_json_exchange(builder, identifier):
    x = builder()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="test", time_basis="instant")
    a = registry.run(identifier, x, context)
    b = registry.run_json(identifier, x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
