import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.bonded_layer_integrity import (
    BondedLayerDisposition,
    BondedLayerIntegrityAssessment,
    BondedLayerObservation,
    BondedLayerRegion,
    BondedLayerRequirement,
    bonded_layer_integrity_assessment,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def observation(**updates):
    payload = {
        "observation_id": "obs-1",
        "region_id": "region-1",
        "observation_kind": "bond_strength",
        "metric_id": "bond-strength",
        "method_id": "caller-method",
        "value": 12.0,
        "expanded_uncertainty": 1.0,
        "unit_token": "MPa",
        "measurement_valid": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return BondedLayerObservation(**payload)


def request(**updates):
    payload = {
        "assessment_id": "bond-1",
        "asset_id": "asset-1",
        "location_id": "lining-1",
        "substrate_material_id": "substrate-A",
        "substrate_lot_id": "substrate-lot-1",
        "bonded_layer_material_id": "layer-A",
        "bonded_layer_lot_id": "layer-lot-1",
        "interface_system_id": "interface-A",
        "bonding_process_id": "process-1",
        "bonding_process_revision": "A",
        "regions": [
            BondedLayerRegion(
                region_id="region-1",
                physical_location_id="shell-zone-1",
                target_area_m2=5.0,
                examined_area_m2=5.0,
                evidence=[EVIDENCE],
            )
        ],
        "observations": [observation()],
        "declared_requirements": [
            BondedLayerRequirement(
                requirement_id="strength-min",
                region_id="region-1",
                metric_id="bond-strength",
                comparator="minimum",
                limit_value=10.0,
                unit_token="MPa",
                requirement_basis="caller requirement",
                evidence=[EVIDENCE],
            )
        ],
        "declared_dispositions": [
            BondedLayerDisposition(
                requirement_id="strength-min",
                satisfied_disposition="caller: retain record",
                not_satisfied_disposition="caller: engineering review",
                indeterminate_disposition="caller: obtain data",
                disposition_authority_basis="caller workflow",
                evidence=[EVIDENCE],
            )
        ],
        "material_lot_and_process_identity_reviewed": True,
        "regions_mutually_exclusive_reviewed": True,
        "examination_coverage_reviewed": True,
        "method_and_calibration_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "observation_mapping_reviewed": True,
        "requirement_and_disposition_authority_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return BondedLayerIntegrityAssessment(**payload)


def test_uncertainty_and_caller_disposition_are_applied():
    result = bonded_layer_integrity_assessment(request())
    row = result.values["requirement_rows"][0]
    assert result.status == "computed"
    assert row["governing_conservative_value"] == pytest.approx(11.0)
    assert row["declared_requirement_satisfied"] is True
    assert row["caller_declared_disposition"] == "caller: retain record"


def test_unmapped_or_invalid_observation_is_preserved_as_needs_data():
    unmapped = observation(
        region_id=None,
        missing_invalid_or_unmapped_basis="location mapping unavailable",
    )
    result = bonded_layer_integrity_assessment(request(observations=[unmapped]))
    assert result.status == "needs_data"
    assert result.values["unmapped_observation_ids"] == ["obs-1"]
    assert result.values["requirement_rows"][0]["caller_declared_disposition"] == "caller: obtain data"


def test_unit_mismatch_and_missing_disposition_are_rejected():
    with pytest.raises(ValueError, match="units must match"):
        request(observations=[observation(unit_token="Pa")])
    with pytest.raises(ValueError, match="requires one caller disposition"):
        request(declared_dispositions=[])


def test_missing_review_needs_data_without_changing_observation():
    result = bonded_layer_integrity_assessment(request(method_and_calibration_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["requirement_rows"][0]["governing_conservative_value"] == pytest.approx(11.0)
