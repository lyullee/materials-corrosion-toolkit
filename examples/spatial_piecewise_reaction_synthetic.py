"""Synthetic-only request template; not executed and contains no fitted kinetics."""

from matintegrity.contracts import Evidence
from matintegrity.spatial_piecewise_reaction import (
    SpatialMassActionReaction,
    SpatialPiecewiseMassAction,
    SpatialReactionInterval,
    build_spatial_reaction_callback,
)

network = SpatialPiecewiseMassAction(
    provider_id="example.synthetic.interval_reaction",
    provider_revision="1",
    network_id="synthetic-A-to-B",
    species_ids=("A", "B"),
    charge_numbers=(0, 0),
    elemental_composition={"A": {"X": 1}, "B": {"X": 1}},
    intervals=(
        SpatialReactionInterval(start_time_s=0.0, end_time_s=10.0),
        SpatialReactionInterval(start_time_s=10.0, end_time_s=20.0),
    ),
    reactions=(SpatialMassActionReaction(
        reaction_id="A_to_B",
        reactants={"A": 1},
        products={"B": 1},
        forward_rate_constants=(0.01, 0.02),
        reverse_rate_constants=(0.0, 0.0),
        forward_rate_constant_unit="1/s",
        reverse_rate_constant_unit="1/s",
        calibration_record_id="synthetic-calibration-record",
        calibration_sha256="a" * 64,
        calibration_evidence=(Evidence(
            source_id="synthetic-calibration-record",
            origin="synthetic",
            citation="Synthetic placeholder only; not a measured or fitted rate source.",
            sha256="a" * 64,
        ),),
    ),),
    concentration_activity_approximation_reviewed=True,
    usage_license_id="CC0-1.0",
    usage_rights_evidence=(Evidence(
        source_id="synthetic-example",
        origin="synthetic",
        citation="Synthetic example values; no external dataset is included.",
        license_id="CC0-1.0",
    ),),
    computational_use_authorized=True,
    local_only_authorized=True,
)

# Construction pattern only. The callback is not evaluated in this example.
callback = build_spatial_reaction_callback(network)
