"""Synthetic demonstration of a caller-sampled Rosenthal cooling interval."""

from matintegrity.contracts import RunContext
from matintegrity.models.fabrication import RosenthalCoolingIntervalLink, RosenthalPointSource3D
from matintegrity.registry import default_registry


def build_request() -> RosenthalCoolingIntervalLink:
    speed = 0.005
    times = tuple(index / 10 for index in range(61))
    # The material point is fixed. Its moving-frame x coordinate decreases at the declared source speed.
    relative_x = tuple(0.01 - speed * time_s for time_s in times)
    history = RosenthalPointSource3D(
        absorbed_power_W=500.0,
        travel_speed_m_s=speed,
        thermal_conductivity_W_m_K=45.0,
        density_kg_m3=7850.0,
        specific_heat_J_kg_K=600.0,
        initial_temperature_K=300.0,
        source_relative_x_m=relative_x,
        transverse_y_m=(0.005,) * len(times),
        depth_z_m=(0.002,) * len(times),
        time_s=times,
        semi_infinite_half_space_reviewed=True,
        constant_properties_reviewed=True,
        phase_change_and_latent_heat_neglected_reviewed=True,
        convection_radiation_and_pool_flow_neglected_reviewed=True,
        point_source_and_steady_moving_frame_reviewed=True,
    )
    return RosenthalCoolingIntervalLink(
        thermal_history=history,
        upper_temperature_K=400.0,
        lower_temperature_K=380.0,
        cooling_branch_start_index=30,
        cooling_branch_end_index=60,
    )


if __name__ == "__main__":
    assessment = default_registry().run(
        "welding.rosenthal_cooling_interval",
        build_request(),
        RunContext(asset_id="synthetic-demo", location_id="point-1", time_basis="elapsed_seconds"),
    )
    print(assessment.model_dump_json(indent=2))
