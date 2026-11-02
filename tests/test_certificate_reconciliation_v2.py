from matintegrity.certificate_reconciliation import (
    CertificateMeasurementRecord,
    CertificateReconciliationInput,
    CertificateRequirement,
    CertificateUnitRule,
    MaterialCertificateEvidence,
    reconcile_material_certificates,
)
from matintegrity.specification_aliases import (
    SpecificationAlias,
    SpecificationDesignation,
    SpecificationProfile,
)

E = {"source_id": "caller", "origin": "user_declared", "citation": "caller evidence"}
D = "b" * 64


def designation(name):
    return SpecificationDesignation(
        namespace="caller",
        designation=name,
        edition="2026",
        product_form="plate",
        condition="normalized",
    )


def profile():
    return SpecificationProfile(
        profile_id="profile-a",
        canonical_designation=designation("A"),
        aliases=(
            SpecificationAlias(
                alias_id="local-a",
                designation=designation("LOCAL-A"),
                mapping_basis="caller mapping",
                evidence=(E,),
            ),
        ),
        profile_revision="1",
        profile_authority_id="caller-authority",
        profile_source_digest=D,
        evidence=(E,),
    )


def measurement(mid, kind, quantity, value, unit):
    return CertificateMeasurementRecord(
        measurement_id=mid,
        quantity_kind=kind,
        quantity_id=quantity,
        reported_value=value,
        reported_unit=unit,
        expanded_uncertainty=0.0,
        method_id="reported-test",
        measurement_digest=D,
        evidence=(E,),
    )


def payload(**updates):
    value = {
        "reconciliation_id": "recon-1",
        "expected_heat_id": "heat-1",
        "expected_lot_id": "lot-1",
        "expected_profile_id": "profile-a",
        "profiles": (profile(),),
        "requirements": (
            CertificateRequirement(
                requirement_id="carbon",
                quantity_kind="chemistry",
                quantity_id="C",
                canonical_unit="dimensionless",
                minimum=0.001,
                maximum=0.003,
                requirement_basis="caller-owned profile",
                evidence=(E,),
            ),
            CertificateRequirement(
                requirement_id="yield",
                quantity_kind="mechanical",
                quantity_id="yield_strength",
                canonical_unit="Pa",
                minimum=200e6,
                requirement_basis="caller-owned profile",
                evidence=(E,),
            ),
        ),
        "unit_rules": (
            CertificateUnitRule(
                rule_id="percent-to-fraction",
                quantity_id="C",
                source_unit="percent",
                canonical_unit="dimensionless",
                rule_basis="caller-reviewed dimensional conversion",
                evidence=(E,),
            ),
            CertificateUnitRule(
                rule_id="mpa-to-pa",
                quantity_id="yield_strength",
                source_unit="MPa",
                canonical_unit="Pa",
                rule_basis="caller-reviewed dimensional conversion",
                evidence=(E,),
            ),
        ),
        "certificates": (
            MaterialCertificateEvidence(
                certificate_id="cert-1",
                heat_id="heat-1",
                lot_id="lot-1",
                reported_designation=designation("LOCAL-A"),
                issuer_id="mill",
                issuer_revision="1",
                certificate_digest=D,
                measurements=(
                    measurement("c", "chemistry", "C", 0.2, "percent"),
                    measurement("ys", "mechanical", "yield_strength", 250.0, "MPa"),
                ),
                evidence=(E,),
            ),
        ),
        "evidence": (E,),
    }
    value.update(updates)
    return CertificateReconciliationInput(**value)


def test_alias_units_chemistry_and_mechanical_reconcile_deterministically():
    result = reconcile_material_certificates(payload())
    assert result.state == "consistent"
    assert result.matched_certificate_ids == ("cert-1",)
    normalized = {row.measurement_id: row.normalized_value for row in result.evidence_rows}
    assert normalized["c"] == 0.002
    assert normalized["ys"] == 250e6
    assert result == reconcile_material_certificates(payload())
    assert result.qualification_claim is False


def test_heat_mismatch_and_unknown_unit_are_preserved():
    original = payload().certificates[0]
    mismatched = original.model_copy(update={"heat_id": "other-heat"})
    mismatch = reconcile_material_certificates(payload(certificates=(mismatched,)))
    assert mismatch.state == "mismatch"
    no_rules = reconcile_material_certificates(payload(unit_rules=()))
    assert no_rules.state == "unknown"
    assert no_rules.unknown_certificate_ids == ("cert-1",)


def test_missing_mechanical_result_is_unknown_not_invented():
    original = payload().certificates[0]
    chemistry_only = original.model_copy(update={"measurements": (original.measurements[0],)})
    result = reconcile_material_certificates(payload(certificates=(chemistry_only,)))
    assert result.state == "unknown"
    assert any(row.requirement_id == "yield" and row.state == "unknown" for row in result.evidence_rows)
