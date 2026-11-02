import pytest
from pydantic import ValidationError
from test_declared_pressure_relation import request

from matintegrity.contracts import canonical_digest
from matintegrity.models.component_pressure_reference import (
    ComponentPressureReference,
    component_pressure_reference,
)
from matintegrity.models.pressure_limit_binding import (
    PressureLimitBinding,
    PressureLimitReferenceContext,
    bind_pressure_relation_component_limit,
    verify_pressure_reference_bindings,
)


def reference(**updates):
    raw = dict(
        asset_id="asset",
        location_id="location",
        physical_scope_id="vessel",
        condition_id="hot-corroded",
        coordinate_frame_id="survey",
        component_elevation_m=0.0,
        pressure_basis="gauge_common_reference",
        common_pressure_reference_id="ambient",
        external_absolute_pressure_Pa=100000.0,
        common_reference_absolute_pressure_Pa=100000.0,
        external_pressure_and_common_reference_reviewed=True,
        component_scenario_and_coordinate_mapping_reviewed=True,
        evidence=(
            dict(source_id="authored", origin="synthetic", citation="Authored reference", sha256="a" * 64),
        ),
    )
    raw.update(updates)
    return PressureLimitReferenceContext(**raw)


def test_explicit_external_and_gauge_conversion():
    result = bind_pressure_relation_component_limit(
        request(), reference(external_absolute_pressure_Pa=100100.0)
    )
    assert result.component_limit.pressure_limit_Pa == 164.0
    assert result.component_limit.capacity_input_digest != request().basis.record_sha256
    absolute = bind_pressure_relation_component_limit(
        request(), reference(pressure_basis="absolute", common_reference_absolute_pressure_Pa=0.0)
    )
    assert absolute.component_limit.pressure_limit_Pa == 100064.0


def test_inverse_design_pressure_is_not_capacity():
    with pytest.raises(ValueError, match="forward"):
        bind_pressure_relation_component_limit(
            request(
                direction="thickness_from_pressure", effective_thickness_m=None, pressure_difference_Pa=64.0
            ),
            reference(),
        )


@pytest.mark.parametrize(
    "updates",
    [
        dict(asset_id="other"),
        dict(external_pressure_and_common_reference_reviewed=False),
        dict(component_scenario_and_coordinate_mapping_reviewed=False),
        dict(external_absolute_pressure_Pa=0.0),
    ],
)
def test_invalid_mapping_or_nonpositive_converted_limit_rejected(updates):
    with pytest.raises(ValueError):
        bind_pressure_relation_component_limit(request(), reference(**updates))


def test_uncomputed_relation_rejected():
    with pytest.raises(ValueError, match="uncomputed"):
        bind_pressure_relation_component_limit(request(maximum_supported_pressure_Pa=1.0), reference())


def test_recomputed_digest_cannot_hide_altered_component_limit():
    binding = bind_pressure_relation_component_limit(request(), reference())
    raw = binding.model_dump(mode="python")
    raw["component_limit"]["pressure_limit_Pa"] = 999.0
    raw["binding_digest"] = canonical_digest({k: v for k, v in raw.items() if k != "binding_digest"})
    with pytest.raises(ValidationError, match="does not match"):
        PressureLimitBinding(**raw)


def aggregation(binding, **updates):
    raw = dict(
        asset_id="asset",
        location_id="location",
        physical_scope_id="vessel",
        condition_id="hot-corroded",
        coordinate_frame_id="survey",
        pressure_basis="gauge_common_reference",
        common_pressure_reference_id="ambient",
        reference_elevation_m=0.0,
        uniform_density_kg_m3=1000.0,
        gravity_m_s2=10.0,
        components=(binding.component_limit,),
        static_connected_uniform_fluid_reviewed=True,
        component_scope_complete_reviewed=True,
        common_pressure_and_elevation_reference_reviewed=True,
        component_capacity_and_condition_reviewed=True,
    )
    raw.update(updates)
    return ComponentPressureReference(**raw)


def test_full_relation_binding_aggregation_chain():
    binding = bind_pressure_relation_component_limit(request(), reference())
    combined = aggregation(binding)
    verify_pressure_reference_bindings(combined, (binding,))
    assert component_pressure_reference(combined).values["governing_reference_pressure_limit_Pa"] == 64.0
    recovered = PressureLimitBinding.model_validate_json(binding.model_dump_json())
    assert recovered == binding


@pytest.mark.parametrize(
    "updates",
    [
        dict(coordinate_frame_id="other"),
        dict(physical_scope_id="other"),
        dict(common_pressure_reference_id="other"),
    ],
)
def test_aggregation_scope_mismatch_rejected(updates):
    binding = bind_pressure_relation_component_limit(request(), reference())
    with pytest.raises(ValueError):
        verify_pressure_reference_bindings(aggregation(binding, **updates), (binding,))


def test_model_copy_cannot_bypass_relation_evidence_binding():
    invalid = request().model_copy(update={"numerator_factor": 3.0})
    with pytest.raises(ValidationError, match="pin"):
        bind_pressure_relation_component_limit(invalid, reference())


def test_same_reference_id_cannot_hide_different_absolute_reference_values():
    first = bind_pressure_relation_component_limit(request(), reference())
    second = bind_pressure_relation_component_limit(
        request(component_id="other"), reference(common_reference_absolute_pressure_Pa=100010.0)
    )
    combined = aggregation(first, components=(first.component_limit, second.component_limit))
    with pytest.raises(ValueError, match="same absolute"):
        verify_pressure_reference_bindings(combined, (first, second))


def test_missing_binding_and_changed_component_cannot_be_aggregated():
    binding = bind_pressure_relation_component_limit(request(), reference())
    combined = aggregation(binding)
    with pytest.raises(ValueError, match="one binding"):
        verify_pressure_reference_bindings(combined, ())
    changed = binding.component_limit.model_copy(update={"pressure_limit_Pa": 999.0})
    with pytest.raises(ValueError, match="does not match"):
        verify_pressure_reference_bindings(aggregation(binding, components=(changed,)), (binding,))
