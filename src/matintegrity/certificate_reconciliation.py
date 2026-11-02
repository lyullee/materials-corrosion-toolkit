"""Unit-normalized reconciliation of caller-owned material certificate evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, canonical_digest
from .specification_aliases import (
    SpecificationDesignation,
    SpecificationProfile,
    resolve_specification_alias,
)
from .units import convert


class CertificateUnitRule(Contract):
    rule_id: str = Field(min_length=1)
    quantity_id: str = Field(min_length=1)
    source_unit: str = Field(min_length=1)
    canonical_unit: str = Field(min_length=1)
    rule_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CertificateRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    quantity_kind: Literal["chemistry", "mechanical"]
    quantity_id: str = Field(min_length=1)
    canonical_unit: str = Field(min_length=1)
    minimum: float | None = None
    maximum: float | None = None
    requirement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.minimum is None and self.maximum is None:
            raise ValueError("certificate requirement needs at least one caller bound")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("certificate requirement bounds must be ordered")
        if self.quantity_kind == "chemistry":
            if self.canonical_unit != "dimensionless":
                raise ValueError("chemistry requirements use canonical dimensionless mass fraction")
            if any(value is not None and not 0 <= value <= 1 for value in (self.minimum, self.maximum)):
                raise ValueError("chemistry requirement bounds must be mass fractions")
        return self


class CertificateMeasurementRecord(Contract):
    measurement_id: str = Field(min_length=1)
    quantity_kind: Literal["chemistry", "mechanical"]
    quantity_id: str = Field(min_length=1)
    reported_value: float
    reported_unit: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    method_id: str = Field(min_length=1)
    measurement_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class MaterialCertificateEvidence(Contract):
    certificate_id: str = Field(min_length=1)
    heat_id: str | None = None
    lot_id: str | None = None
    reported_designation: SpecificationDesignation
    issuer_id: str = Field(min_length=1)
    issuer_revision: str = Field(min_length=1)
    certificate_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    measurements: tuple[CertificateMeasurementRecord, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_measurements(self):
        ids = [row.measurement_id for row in self.measurements]
        if len(set(ids)) != len(ids):
            raise ValueError("certificate measurement identifiers must be unique")
        return self


class CertificateReconciliationInput(Contract):
    reconciliation_id: str = Field(min_length=1)
    expected_heat_id: str = Field(min_length=1)
    expected_lot_id: str = Field(min_length=1)
    expected_profile_id: str = Field(min_length=1)
    profiles: tuple[SpecificationProfile, ...] = Field(min_length=1)
    requirements: tuple[CertificateRequirement, ...] = Field(min_length=1)
    unit_rules: tuple[CertificateUnitRule, ...] = ()
    certificates: tuple[MaterialCertificateEvidence, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_configuration(self):
        for values, label in (
            ([row.requirement_id for row in self.requirements], "requirement identifiers"),
            ([row.certificate_id for row in self.certificates], "certificate identifiers"),
            ([row.rule_id for row in self.unit_rules], "unit-rule identifiers"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{label} must be unique")
        requirement_keys = [(row.quantity_kind, row.quantity_id) for row in self.requirements]
        if len(set(requirement_keys)) != len(requirement_keys):
            raise ValueError("certificate requirement quantity keys must be unique")
        rule_keys = [(row.quantity_id, row.source_unit, row.canonical_unit) for row in self.unit_rules]
        if len(set(rule_keys)) != len(rule_keys):
            raise ValueError("unit normalization mappings must be unique")
        return self


class ReconciledEvidenceRow(Contract):
    certificate_id: str
    measurement_id: str | None = None
    requirement_id: str | None = None
    state: Literal["match", "mismatch", "unknown", "uncertainty_overlap"]
    basis: str
    normalized_value: float | None = None
    normalized_uncertainty: float | None = None
    canonical_unit: str | None = None
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class CertificateReconciliationReport(Contract):
    reconciliation_id: str
    state: Literal["consistent", "mismatch", "unknown"]
    profile_id: str
    profile_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_rows: tuple[ReconciledEvidenceRow, ...]
    matched_certificate_ids: tuple[str, ...]
    mismatched_certificate_ids: tuple[str, ...]
    unknown_certificate_ids: tuple[str, ...]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_claim: Literal[False] = False


def _normalize(
    measurement: CertificateMeasurementRecord,
    requirement: CertificateRequirement,
    rules: tuple[CertificateUnitRule, ...],
) -> tuple[float, float] | None:
    if measurement.reported_unit == requirement.canonical_unit:
        return measurement.reported_value, measurement.expanded_uncertainty
    matching = [
        row
        for row in rules
        if row.quantity_id == measurement.quantity_id
        and row.source_unit == measurement.reported_unit
        and row.canonical_unit == requirement.canonical_unit
    ]
    if len(matching) != 1:
        return None
    try:
        value = convert(measurement.reported_value, measurement.reported_unit, requirement.canonical_unit)
        upper = convert(
            measurement.reported_value + measurement.expanded_uncertainty,
            measurement.reported_unit,
            requirement.canonical_unit,
        )
        lower = convert(
            measurement.reported_value - measurement.expanded_uncertainty,
            measurement.reported_unit,
            requirement.canonical_unit,
        )
    except (ValueError, TypeError):
        return None
    return value, abs(upper - lower) / 2


def reconcile_material_certificates(x: CertificateReconciliationInput) -> CertificateReconciliationReport:
    """Reconcile evidence without asserting specification or code qualification."""

    profile_matches = [row for row in x.profiles if row.profile_id == x.expected_profile_id]
    if len(profile_matches) != 1:
        raise ValueError("expected specification profile must identify exactly one caller profile")
    profile = profile_matches[0]
    requirements = {(row.quantity_kind, row.quantity_id): row for row in x.requirements}
    rows: list[ReconciledEvidenceRow] = []
    per_certificate: dict[str, set[str]] = {row.certificate_id: set() for row in x.certificates}

    for certificate in x.certificates:
        identity = resolve_specification_alias(certificate.reported_designation, x.profiles)
        identity_ok = (
            identity.status in {"exact", "resolved_alias"} and identity.profile_id == profile.profile_id
        )
        identity_state = "match" if identity_ok else "unknown" if identity.status == "unknown" else "mismatch"
        identity_basis = (
            "Heat, lot and caller specification profile match."
            if identity_ok
            and certificate.heat_id == x.expected_heat_id
            and certificate.lot_id == x.expected_lot_id
            else "Certificate identity is missing, conflicting, or differs from the expected heat/lot/profile."
        )
        if certificate.heat_id is None or certificate.lot_id is None or identity.status == "unknown":
            identity_state = "unknown"
        elif (
            certificate.heat_id != x.expected_heat_id
            or certificate.lot_id != x.expected_lot_id
            or not identity_ok
        ):
            identity_state = "mismatch"
        rows.append(
            ReconciledEvidenceRow(
                certificate_id=certificate.certificate_id,
                state=identity_state,
                basis=identity_basis,
                source_digest=certificate.certificate_digest,
            )
        )
        per_certificate[certificate.certificate_id].add(identity_state)

        seen_keys: set[tuple[str, str]] = set()
        for measurement in certificate.measurements:
            key = (measurement.quantity_kind, measurement.quantity_id)
            seen_keys.add(key)
            requirement = requirements.get(key)
            if requirement is None:
                state, basis, normalized = "unknown", "No caller requirement exists for this quantity.", None
            else:
                normalized = _normalize(measurement, requirement, x.unit_rules)
                if normalized is None:
                    state, basis = "unknown", "No unique reviewed unit normalization is available."
                else:
                    value, uncertainty = normalized
                    lower, upper = value - uncertainty, value + uncertainty
                    inside = (requirement.minimum is None or lower >= requirement.minimum) and (
                        requirement.maximum is None or upper <= requirement.maximum
                    )
                    outside = (requirement.minimum is not None and upper < requirement.minimum) or (
                        requirement.maximum is not None and lower > requirement.maximum
                    )
                    state = "match" if inside else "mismatch" if outside else "uncertainty_overlap"
                    basis = "Normalized uncertainty interval compared with caller-owned bounds."
            rows.append(
                ReconciledEvidenceRow(
                    certificate_id=certificate.certificate_id,
                    measurement_id=measurement.measurement_id,
                    requirement_id=requirement.requirement_id if requirement else None,
                    state=state,
                    basis=basis,
                    normalized_value=normalized[0] if normalized else None,
                    normalized_uncertainty=normalized[1] if normalized else None,
                    canonical_unit=requirement.canonical_unit if requirement else None,
                    source_digest=measurement.measurement_digest,
                )
            )
            per_certificate[certificate.certificate_id].add(state)
        for key, requirement in requirements.items():
            if key not in seen_keys:
                rows.append(
                    ReconciledEvidenceRow(
                        certificate_id=certificate.certificate_id,
                        requirement_id=requirement.requirement_id,
                        state="unknown",
                        basis="Required certificate quantity was not reported.",
                        canonical_unit=requirement.canonical_unit,
                        source_digest=certificate.certificate_digest,
                    )
                )
                per_certificate[certificate.certificate_id].add("unknown")

    mismatched = tuple(sorted(key for key, states in per_certificate.items() if "mismatch" in states))
    unknown = tuple(
        sorted(
            key
            for key, states in per_certificate.items()
            if "mismatch" not in states and ({"unknown", "uncertainty_overlap"} & states)
        )
    )
    matched = tuple(sorted(set(per_certificate) - set(mismatched) - set(unknown)))
    state = "mismatch" if mismatched else "unknown" if unknown else "consistent"
    input_digest = canonical_digest(x.model_dump(mode="json"))
    payload = {
        "reconciliation_id": x.reconciliation_id,
        "state": state,
        "profile_id": profile.profile_id,
        "profile_digest": profile.deterministic_digest,
        "evidence_rows": tuple(rows),
        "matched_certificate_ids": matched,
        "mismatched_certificate_ids": mismatched,
        "unknown_certificate_ids": unknown,
        "input_digest": input_digest,
        "qualification_claim": False,
    }
    digest_payload = {
        **payload,
        "evidence_rows": [row.model_dump(mode="json") for row in payload["evidence_rows"]],
    }
    return CertificateReconciliationReport(**payload, report_digest=canonical_digest(digest_payload))
