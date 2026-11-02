import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.nonisothermal_oxidation import (
    NonisothermalParabolicOxidation,
    nonisothermal_parabolic_oxidation,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def qualification(record_id, specimen, group, partition):
    return {
        "evidence_record_id": record_id,
        "physical_specimen_id": specimen,
        "source_group_id": group,
        "partition": partition,
        "method_id": "method-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "supports_declared_table": True,
        "evidence": (EVIDENCE,),
    }


def table():
    return {
        "table_id": "table-1",
        "material_condition_id": "material-1",
        "surface_condition_id": "surface-1",
        "environment_id": "environment-1",
        "rate_unit_token": "m^2/s",
        "interpolation_policy": "linear_rate_vs_temperature",
        "points": (
            {
                "point_id": "point-300",
                "temperature_K": 300.0,
                "parabolic_rate_m2_s": 1e-12,
                "result_digest": DIGEST_A,
                "evidence": (EVIDENCE,),
            },
            {
                "point_id": "point-400",
                "temperature_K": 400.0,
                "parabolic_rate_m2_s": 3e-12,
                "result_digest": DIGEST_B,
                "evidence": (EVIDENCE,),
            },
            {
                "point_id": "point-500",
                "temperature_K": 500.0,
                "parabolic_rate_m2_s": 7e-12,
                "result_digest": DIGEST_C,
                "evidence": (EVIDENCE,),
            },
        ),
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "provider_configuration_digest": DIGEST_B,
        "data_digest": DIGEST_C,
        "result_digest": DIGEST_D,
        "qualification_evidence": (
            qualification("q-cal", "specimen-cal", "source-cal", "calibration"),
            qualification("q-hold", "specimen-hold", "source-hold", "holdout"),
        ),
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }


def knot(knot_id, time_s, temperature_K):
    return {
        "knot_id": knot_id,
        "elapsed_time_s": time_s,
        "temperature_K": temperature_K,
        "record_digest": DIGEST_D,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    value = {
        "history_id": "history-1",
        "asset_id": "asset-1",
        "location_id": "surface-location-1",
        "physical_scope_id": "surface-scope-1",
        "clock_id": "clock-1",
        "material_condition_id": "material-1",
        "surface_condition_id": "surface-1",
        "environment_id": "environment-1",
        "initial_oxide_thickness_m": 1e-6,
        "temperature_history": (
            knot("knot-1", 0.0, 300.0),
            knot("knot-2", 100.0, 500.0),
        ),
        "rate_table": table(),
        "material_surface_and_environment_identity_reviewed": True,
        "temperature_clock_and_interpolation_reviewed": True,
        "rate_units_and_temperature_support_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "calibration_holdout_and_source_groups_reviewed": True,
        "retained_parabolic_scale_regime_reviewed": True,
        "rate_table_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return NonisothermalParabolicOxidation(**value)


def test_piecewise_nonisothermal_integration_splits_at_rate_knot():
    result = nonisothermal_parabolic_oxidation(payload())
    expected_increment = 50.0 * (1e-12 + 3e-12) / 2 + 50.0 * (3e-12 + 7e-12) / 2
    assert result.status == "computed"
    assert result.values["cumulative_thickness_squared_increment_m2"] == pytest.approx(
        expected_increment, rel=1e-12, abs=0.0
    )
    assert result.values["final_oxide_thickness_m"] == pytest.approx(math.sqrt(1e-12 + expected_increment))


def test_isothermal_history_matches_constant_parabolic_increment():
    assessment = payload(
        temperature_history=(
            knot("knot-1", 0.0, 400.0),
            knot("knot-2", 20.0, 400.0),
        )
    )
    result = nonisothermal_parabolic_oxidation(assessment)
    assert result.values["cumulative_thickness_squared_increment_m2"] == pytest.approx(
        3e-12 * 20.0, rel=1e-12, abs=0.0
    )


def test_reversing_the_same_temperature_path_preserves_integrated_rate():
    heating = nonisothermal_parabolic_oxidation(payload())
    cooling = nonisothermal_parabolic_oxidation(
        payload(temperature_history=(knot("knot-1", 0.0, 500.0), knot("knot-2", 100.0, 300.0)))
    )
    assert cooling.values["cumulative_thickness_squared_increment_m2"] == pytest.approx(
        heating.values["cumulative_thickness_squared_increment_m2"], rel=1e-12, abs=0.0
    )


def test_unreviewed_or_outside_temperature_is_not_silently_used():
    assert (
        nonisothermal_parabolic_oxidation(payload(retained_parabolic_scale_regime_reviewed=False)).status
        == "needs_data"
    )
    outside = payload(
        temperature_history=(
            knot("knot-1", 0.0, 290.0),
            knot("knot-2", 100.0, 400.0),
        )
    )
    result = nonisothermal_parabolic_oxidation(outside)
    assert result.status == "out_of_scope"
    assert result.values["outside_support_temperature_knot_ids"] == ["knot-1"]


def test_partition_leakage_and_context_identity_are_enforced():
    bad_table = table()
    bad_table["qualification_evidence"] = (
        qualification("q-cal", "specimen-cal", "same-source", "calibration"),
        qualification("q-hold", "specimen-hold", "same-source", "holdout"),
    )
    with pytest.raises(ValueError, match="disjoint"):
        payload(rate_table=bad_table)
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.nonisothermal_parabolic_oxidation",
            payload(),
            RunContext(asset_id="other", location_id="surface-location-1", time_basis="authored"),
        )
