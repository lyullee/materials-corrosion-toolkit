"""Synthetic tube pressure example; not a design-code acceptance check."""

from matintegrity.assembly_calculations import TubeCondition
from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.tube_bundle_lame_stress_history import (
    TubeBundleLameStressHistory, TubePressureKnot, TubePressureStressHistory,
    evaluate_tube_bundle_lame_stress_history,
)

scope = dict(asset_id="synthetic-exchanger", location_id="shell-side",
             exchanger_id="E-TEST", bundle_id="B-TEST")
geometry = {"tube_id": "T-001", "inner_diameter_m": 0.018,
            "current_minimum_wall_m": 0.0015, "reference_wall_m": 0.0018}
geometry_sha = canonical_digest(geometry)
geometry_evidence = (Evidence(
    source_id="synthetic_tube_geometry", origin="synthetic",
    citation="Illustrative tube dimensions", license_id="CC0-1.0", sha256=geometry_sha,
),)
pressure_rows = []
for index, (time_s, internal, external) in enumerate(((0.0, 2.0e6, 0.1e6), (60.0, 2.2e6, 0.1e6))):
    record = {**scope, "tube_id": "T-001", "time_basis_id": "example-clock",
              "pressure_reference_basis_id": "absolute-Pa", "time_s": time_s,
              "internal_pressure_Pa": internal, "external_pressure_Pa": external}
    digest = canonical_digest(record)
    pressure_rows.append(TubePressureKnot(
        knot_id=f"k{index}", **scope, tube_id="T-001",
        time_basis_id="example-clock", pressure_reference_basis_id="absolute-Pa",
        time_s=time_s, internal_pressure_Pa=internal, external_pressure_Pa=external,
        source_id="synthetic_pressure_record", source_record_id=f"p{index}",
        source_record_sha256=digest, evidence=(Evidence(
            source_id="synthetic_pressure_record", origin="synthetic",
            citation="Illustrative absolute pressures", license_id="CC0-1.0", sha256=digest,
        ),),
    ))
request = TubeBundleLameStressHistory(
    assessment_id="synthetic-tube-pressure", **scope,
    time_basis_id="example-clock", pressure_reference_basis_id="absolute-Pa",
    tube_histories=(TubePressureStressHistory(
        tube_condition=TubeCondition(tube_id="T-001", inner_diameter_m=geometry["inner_diameter_m"],
            reference_wall_m=geometry["reference_wall_m"],
            minimum_wall_m=geometry["current_minimum_wall_m"], plugged=False),
        **scope, material_condition_id="synthetic-steel-state", closed_ends=True,
        geometry_source_id="synthetic_tube_geometry", geometry_record_id="g1",
        geometry_record_sha256=geometry_sha, geometry_evidence=geometry_evidence,
        pressure_knots=tuple(pressure_rows),
    ),),
    tube_bundle_and_material_identity_reviewed=True,
    current_bore_and_minimum_wall_mapping_reviewed=True,
    wall_is_uniform_and_axisymmetric_reviewed=True,
    absolute_pressure_units_and_common_reference_reviewed=True,
    pressure_history_clock_and_record_lineage_reviewed=True,
    elastic_isotropic_axisymmetric_lame_applicability_reviewed=True,
    axial_end_condition_reviewed=True,
    no_acceptance_capacity_or_life_claim_reviewed=True,
    computational_use_authorized=True,
)
print(evaluate_tube_bundle_lame_stress_history(request).model_dump(mode="json"))
