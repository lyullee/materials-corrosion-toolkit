import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.certificate_reconciliation import (
    MaterialCertificateReconciliation,
    certificate_reconciliation,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def measurement(identifier, kind, quantity, value, uncertainty, unit_basis, unit):
    return {
        "measurement_id": identifier,
        "quantity_kind": kind,
        "quantity_id": quantity,
        "unit_basis": unit_basis,
        "unit_token": unit,
        "reported_value": value,
        "expanded_uncertainty": uncertainty,
        "uncertainty_coverage_factor": 2.0,
        "method_id": "method-1",
        "result_digest": DIGEST_B,
        "evidence": (EVIDENCE,),
    }


def record(identifier, role, sample, source, measurements, **updates):
    value = {
        "record_id": identifier,
        "record_role": role,
        "heat_id": "heat-1",
        "lot_id": "lot-1",
        "reported_material_identity_id": "reported-grade-1",
        "alias_resolution_status": "exact",
        "resolved_material_condition_id": "material-1",
        "alias_resolution_basis": "authored exact identity",
        "physical_sample_id": sample,
        "source_group_id": source,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "record_digest": DIGEST_A,
        "measurements": measurements,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def requirements():
    return (
        {
            "requirement_id": "req-C",
            "quantity_kind": "chemistry_mass_fraction",
            "quantity_id": "C",
            "unit_basis": "mass_fraction",
            "unit_token": "mass_fraction",
            "minimum_allowed_value": 0.001,
            "maximum_allowed_value": 0.003,
            "comparison_policy": "reported_uncertainty_interval_against_requirement",
            "requirement_basis": "authored caller requirement",
            "evidence": (EVIDENCE,),
        },
        {
            "requirement_id": "req-yield",
            "quantity_kind": "property_si",
            "quantity_id": "yield_strength",
            "unit_basis": "SI",
            "unit_token": "Pa",
            "minimum_allowed_value": 200e6,
            "maximum_allowed_value": 300e6,
            "comparison_policy": "reported_uncertainty_interval_against_requirement",
            "requirement_basis": "authored caller requirement",
            "evidence": (EVIDENCE,),
        },
        {
            "requirement_id": "req-elongation",
            "quantity_kind": "property_si",
            "quantity_id": "elongation_fraction",
            "unit_basis": "SI",
            "unit_token": "1",
            "minimum_allowed_value": 0.2,
            "comparison_policy": "reported_uncertainty_interval_against_requirement",
            "requirement_basis": "authored caller requirement",
            "evidence": (EVIDENCE,),
        },
    )


def records():
    return (
        record(
            "certificate-1",
            "certificate",
            "sample-certificate",
            "source-certificate",
            (
                measurement(
                    "cert-C-1",
                    "chemistry_mass_fraction",
                    "C",
                    0.002,
                    0.0001,
                    "mass_fraction",
                    "mass_fraction",
                ),
                measurement(
                    "cert-C-2",
                    "chemistry_mass_fraction",
                    "C",
                    0.0021,
                    0.0001,
                    "mass_fraction",
                    "mass_fraction",
                ),
                measurement("cert-yield", "property_si", "yield_strength", 250e6, 5e6, "SI", "Pa"),
            ),
        ),
        record(
            "test-1",
            "independent_test",
            "sample-test",
            "source-test",
            (
                measurement(
                    "test-C",
                    "chemistry_mass_fraction",
                    "C",
                    0.00205,
                    0.00015,
                    "mass_fraction",
                    "mass_fraction",
                ),
                measurement("test-yield", "property_si", "yield_strength", 252e6, 5e6, "SI", "Pa"),
            ),
        ),
    )


def payload(**updates):
    value = {
        "reconciliation_id": "reconciliation-1",
        "asset_id": "asset-1",
        "location_id": "material-location-1",
        "physical_scope_id": "heat-lot-scope-1",
        "heat_id": "heat-1",
        "lot_id": "lot-1",
        "material_condition_id": "material-1",
        "requirement_set_id": "caller-requirements-1",
        "requirement_authority_digest": DIGEST_C,
        "requirements": requirements(),
        "records": records(),
        "heat_lot_and_material_condition_reviewed": True,
        "alias_resolution_status_and_mapping_reviewed": True,
        "requirement_authority_and_bounds_reviewed": True,
        "chemistry_mass_fraction_basis_reviewed": True,
        "property_si_units_reviewed": True,
        "physical_samples_and_source_groups_reviewed": True,
        "methods_uncertainties_and_coverage_factors_reviewed": True,
        "provider_lineage_and_result_digests_reviewed": True,
        "duplicate_contradiction_and_missingness_policy_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return MaterialCertificateReconciliation(**value)


def test_duplicate_missing_and_satisfied_rows_are_preserved():
    result = certificate_reconciliation(payload())
    assert result.status == "computed"
    assert result.values["declared_requirement_outcome"] == "unknown"
    assert result.values["missing_requirement_ids"] == ["req-elongation"]
    assert result.values["duplicate_measurement_rows"][0]["measurement_ids"] == [
        "cert-C-1",
        "cert-C-2",
    ]
    states = {row["requirement_id"]: row["comparison_state"] for row in result.values["requirement_results"]}
    assert states["req-C"] == "within_requirement"
    assert states["req-yield"] == "within_requirement"


def test_contradictory_records_remain_unknown_instead_of_being_averaged():
    conflicting = list(records())
    conflicting.append(
        record(
            "test-2",
            "supplemental_test",
            "sample-test-2",
            "source-test-2",
            (measurement("test-yield-2", "property_si", "yield_strength", 400e6, 2e6, "SI", "Pa"),),
        )
    )
    result = certificate_reconciliation(payload(records=tuple(conflicting)))
    assert result.status == "computed"
    assert result.values["contradictory_requirement_ids"] == ["req-yield"]
    assert result.values["declared_requirement_outcome"] == "unknown"


def test_unresolved_alias_or_unit_mismatch_needs_data():
    unresolved = list(records())
    unresolved[0] = {
        **unresolved[0],
        "alias_resolution_status": "unresolved",
        "resolved_material_condition_id": None,
    }
    result = certificate_reconciliation(payload(records=tuple(unresolved)))
    assert result.status == "needs_data"
    assert result.values["unresolved_or_ambiguous_record_ids"] == ["certificate-1"]

    mismatched = list(records())
    first_measurements = list(mismatched[0]["measurements"])
    first_measurements[2] = {**first_measurements[2], "unit_token": "MPa"}
    mismatched[0] = {**mismatched[0], "measurements": tuple(first_measurements)}
    result = certificate_reconciliation(payload(records=tuple(mismatched)))
    assert result.status == "needs_data"
    assert result.values["unit_mismatch_measurement_ids"] == ["cert-yield"]


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.multi_record_certificate_reconciliation",
            payload(),
            RunContext(asset_id="other", location_id="material-location-1", time_basis="authored"),
        )
