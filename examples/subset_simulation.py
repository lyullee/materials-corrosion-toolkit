"""Synthetic one-dimensional pCN subset simulation via a caller limit-state function."""

from matintegrity.reliability_sampling import SubsetSimulationRequest, run_subset_simulation


def build_request():
    return SubsetSimulationRequest(
        estimate_id="authored-standard-normal-tail",
        event_id="latent-coordinate-exceeds-two",
        event_definition="g(z) = 2 - z[0] <= 0",
        failure_mode="synthetic first-failure mode",
        asset_id="synthetic-asset",
        location_id="synthetic-location",
        physical_scope_id="synthetic-scope",
        time_basis="authored synthetic interval",
        horizon_start_s=0.0,
        horizon_end_s=10.0,
        conditioning="asset survived to interval start",
        latent_variable_ids=("standard-normal-load-coordinate",),
        evaluator_id="example-linear-limit-state",
        evaluator_revision="1",
        evaluator_configuration_sha256="d" * 64,
        random_seed=20261029,
        samples_per_level=2000,
        conditional_probability=0.1,
        pcn_beta=0.6,
        maximum_levels=8,
        latent_mapping_reviewed=True,
        event_semantics_reviewed=True,
        event_is_first_failure_in_period_reviewed=True,
        deterministic_evaluator_declared=True,
    )


def main():
    request = build_request()
    result = run_subset_simulation(lambda latent: 2.0 - latent[0], request)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
