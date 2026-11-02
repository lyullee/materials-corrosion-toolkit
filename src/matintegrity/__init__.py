"""Composable engineering models with explicit assumptions and evidence."""

__version__ = "0.1.0a1"


def evaluate(model_id, inputs, context, *, runtime_dependencies=None):
    """Evaluate a built-in model through the versioned result contract."""
    from .registry import default_registry

    return default_registry().run(
        model_id, inputs, context, runtime_dependencies=runtime_dependencies
    )


def make_spatial_wet_co2_candidate_solver(spatial_request_template):
    """Build a digest-bound spatial BV callback for wet-CO2 geometry iteration."""
    from .wet_co2_geometry_fixed_point import make_spatial_wet_co2_candidate_solver as build

    return build(spatial_request_template)


def bind_planar_slit_hydraulic_snapshot(
    transport_request,
    hydraulic_history_result,
    hydraulic_history_result_sha256,
    snapshot_index,
):
    """Return a transport request bound to one verified hydraulic snapshot."""
    from .restricted_transport import bind_planar_slit_hydraulic_snapshot as bind

    return bind(
        transport_request,
        hydraulic_history_result,
        hydraulic_history_result_sha256,
        snapshot_index,
    )


def bind_planar_slit_hydraulic_history_series(
    transport_segment_requests,
    hydraulic_history_result,
    hydraulic_history_result_sha256,
):
    """Bind exact hydraulic-history knots to adjacent local-clock transport requests."""
    from .restricted_transport import bind_planar_slit_hydraulic_history_series as bind

    return bind(
        transport_segment_requests,
        hydraulic_history_result,
        hydraulic_history_result_sha256,
    )


def bind_planar_slit_transient_hydraulic_interval(
    transport_request,
    hydraulic_history_result,
    hydraulic_history_result_sha256,
    interval_index,
    *,
    face_aperture_interpolation_reviewed,
):
    """Bind one transient slit-flow interval as a runtime transport velocity callback."""
    from .restricted_transport import bind_planar_slit_transient_hydraulic_interval as bind

    return bind(
        transport_request,
        hydraulic_history_result,
        hydraulic_history_result_sha256,
        interval_index,
        face_aperture_interpolation_reviewed=face_aperture_interpolation_reviewed,
    )


def bind_planar_slit_transient_hydraulic_history_series(
    transport_segment_requests,
    hydraulic_history_result,
    hydraulic_history_result_sha256,
    *,
    face_aperture_interpolation_reviewed,
):
    """Bind ordered transient slit-flow intervals to transport velocity callbacks."""
    from .restricted_transport import bind_planar_slit_transient_hydraulic_history_series as bind

    return bind(
        transport_segment_requests,
        hydraulic_history_result,
        hydraulic_history_result_sha256,
        face_aperture_interpolation_reviewed=face_aperture_interpolation_reviewed,
    )


def build_bdot_transport_activity_callback(
    request,
    *,
    transport_species_ids,
    temperature_K,
):
    """Build a caller-parameterized aqueous B-dot callback for transport."""
    from .models.aqueous_activity_iteration import build_bdot_transport_activity_callback as build

    return build(
        request,
        transport_species_ids=transport_species_ids,
        temperature_K=temperature_K,
    )


def build_bdot_transport_saturation_callback(
    request,
    *,
    screen_template,
    transport_species_ids,
    saturation_provider_id,
    saturation_provider_revision,
):
    """Build a B-dot activity and caller-Ksp callback for solid-kinetic transport."""
    from .models.aqueous_activity_iteration import build_bdot_transport_saturation_callback as build

    return build(
        request,
        screen_template=screen_template,
        transport_species_ids=transport_species_ids,
        saturation_provider_id=saturation_provider_id,
        saturation_provider_revision=saturation_provider_revision,
    )


def bind_external_crevice_velocity(transport_request, solver_receipt):
    """Bind a reviewed CFD crevice velocity receipt to a transport request."""
    from .models.external_crevice_solver import bind_external_crevice_velocity as bind

    return bind(transport_request, solver_receipt)


def aqueous_external_activity_self_consistent_speciation(request, activity_provider):
    """Couple a mass-action request to a caller-owned composition activity provider."""
    from .models.aqueous_external_activity import (
        aqueous_external_activity_self_consistent_speciation as solve,
    )

    return solve(request, activity_provider=activity_provider)


def bind_thermal_temperature_profile(
    stress_request,
    thermal_result,
    thermal_result_sha256,
    time_index,
    *,
    temperature_to_section_mapping_reviewed,
):
    """Return an elastic section request bound to one exact thermal output row."""
    from .models.thermal_transient import bind_thermal_temperature_profile as bind

    return bind(
        stress_request,
        thermal_result,
        thermal_result_sha256,
        time_index,
        temperature_to_section_mapping_reviewed=temperature_to_section_mapping_reviewed,
    )


def aqueous_external_activity_speciation_history(request, activity_provider):
    """Solve exact aqueous time/temperature knots with a caller activity provider."""
    from .models.aqueous_external_activity_history import (
        aqueous_external_activity_speciation_history as solve,
    )

    return solve(request, activity_provider=activity_provider)


def build_external_aqueous_transport_activity_callback(request, activity_provider):
    """Build a reviewed provider callback for restricted aqueous transport."""
    from .models.aqueous_external_activity import (
        build_external_aqueous_transport_activity_callback as build_callback,
    )

    return build_callback(request, activity_provider=activity_provider)
