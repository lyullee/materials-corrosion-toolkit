"""Couple reviewed fire-protection flux records to a thermal boundary.

The transfer fractions and their support are supplied by the caller.  This
module performs bookkeeping and integration only; it does not supply a fire
curve, protection properties, degradation law or an acceptance criterion.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class FireProtectionTransferSupport(Contract):
    support_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    incident_flux_min_W_m2: Nonnegative
    incident_flux_max_W_m2: Nonnegative
    supported_protection_state_ids: list[str] = Field(min_length=1)
    calibration_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.incident_flux_max_W_m2 < self.incident_flux_min_W_m2:
            raise ValueError("fire-protection incident-flux support must be ordered")
        if len(set(self.supported_protection_state_ids)) != len(self.supported_protection_state_ids):
            raise ValueError("supported protection-state IDs must be unique")
        return self


class FireProtectionBoundaryHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    thermal_boundary_id: str = Field(min_length=1)
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=5000)
    incident_heat_flux_W_m2: list[Nonnegative] = Field(min_length=2, max_length=5000)
    transmitted_flux_fraction: list[Fraction] = Field(min_length=2, max_length=5000)
    protection_state_ids: list[str] = Field(min_length=2, max_length=5000)
    transfer_record_digests: list[str] = Field(min_length=2, max_length=5000)
    exposed_area_m2: Positive
    transfer_support: FireProtectionTransferSupport
    clock_alignment_reviewed: bool
    incident_flux_basis_reviewed: bool
    protection_state_history_reviewed: bool
    transfer_provider_and_calibration_reviewed: bool
    thermal_boundary_orientation_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_history(self):
        count = len(self.elapsed_time_s)
        vectors = (
            self.incident_heat_flux_W_m2,
            self.transmitted_flux_fraction,
            self.protection_state_ids,
            self.transfer_record_digests,
        )
        if any(len(values) != count for values in vectors):
            raise ValueError("fire-protection histories must align to the clock")
        if any(
            right <= left for left, right in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)
        ):
            raise ValueError("fire-protection clock must strictly increase")
        if any(not value for value in self.protection_state_ids):
            raise ValueError("protection-state IDs cannot be empty")
        if any(
            len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
            for value in self.transfer_record_digests
        ):
            raise ValueError("transfer-record digests must be lowercase SHA-256 values")
        return self


def _product_linear_integral(q0: float, q1: float, f0: float, f1: float, dt: float) -> float:
    """Integrate the product of two linearly interpolated endpoint histories."""

    return dt * (2 * q0 * f0 + q0 * f1 + q1 * f0 + 2 * q1 * f1) / 6


def fire_protection_boundary_history(x: FireProtectionBoundaryHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "clock_alignment_reviewed",
            "incident_flux_basis_reviewed",
            "protection_state_history_reviewed",
            "transfer_provider_and_calibration_reviewed",
            "thermal_boundary_orientation_reviewed",
        )
        if not getattr(x, name)
    ]
    support = x.transfer_support
    outside_flux_indices = [
        index
        for index, flux in enumerate(x.incident_heat_flux_W_m2)
        if not support.incident_flux_min_W_m2 <= flux <= support.incident_flux_max_W_m2
    ]
    supported_states = set(support.supported_protection_state_ids)
    unsupported_state_indices = [
        index for index, state in enumerate(x.protection_state_ids) if state not in supported_states
    ]
    diagnostics = {
        "outside_incident_flux_support_indices": outside_flux_indices,
        "unsupported_protection_state_indices": unsupported_state_indices,
        "missing_reviews": missing_reviews,
        "support_id": support.support_id,
        "provider_id": support.provider_id,
        "provider_version": support.provider_version,
        "provider_digest": support.provider_digest,
        "transfer_record_digests": x.transfer_record_digests,
    }
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={"history_id": x.history_id, **diagnostics},
            notes=("No thermal boundary is emitted until all review gates are complete.",),
        )
    if outside_flux_indices or unsupported_state_indices:
        return Calculation(
            status="out_of_scope",
            values={"history_id": x.history_id, **diagnostics},
            notes=("No thermal boundary is emitted outside the declared transfer support.",),
        )

    transmitted = [
        flux * fraction
        for flux, fraction in zip(x.incident_heat_flux_W_m2, x.transmitted_flux_fraction, strict=True)
    ]
    interval_incident_energy = []
    interval_transmitted_energy = []
    for index, (start, end) in enumerate(zip(x.elapsed_time_s, x.elapsed_time_s[1:], strict=False)):
        dt = end - start
        q0 = x.incident_heat_flux_W_m2[index]
        q1 = x.incident_heat_flux_W_m2[index + 1]
        f0 = x.transmitted_flux_fraction[index]
        f1 = x.transmitted_flux_fraction[index + 1]
        interval_incident_energy.append(0.5 * (q0 + q1) * dt)
        interval_transmitted_energy.append(_product_linear_integral(q0, q1, f0, f1, dt))

    incident_energy_per_area = sum(interval_incident_energy)
    transmitted_energy_per_area = sum(interval_transmitted_energy)
    return Calculation(
        values={
            "history_id": x.history_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "clock_id": x.clock_id,
            "elapsed_time_s": x.elapsed_time_s,
            "incident_heat_flux_W_m2": x.incident_heat_flux_W_m2,
            "transmitted_heat_flux_into_solid_W_m2": transmitted,
            "interval_incident_energy_J_m2": interval_incident_energy,
            "interval_transmitted_energy_J_m2": interval_transmitted_energy,
            "total_incident_energy_J_m2": incident_energy_per_area,
            "total_transmitted_energy_J_m2": transmitted_energy_per_area,
            "total_incident_energy_J": incident_energy_per_area * x.exposed_area_m2,
            "total_transmitted_energy_J": transmitted_energy_per_area * x.exposed_area_m2,
            "thermal_boundary_contract": {
                "boundary_id": x.thermal_boundary_id,
                "kind": "prescribed_heat_flux",
                "heat_flux_into_solid_W_m2": transmitted,
            },
            **diagnostics,
        },
        notes=(
            "The emitted boundary matches the prescribed-heat-flux contract used by the transient conduction model.",
            "Incident flux and transfer fractions are linearly interpolated; their product is integrated exactly on each interval.",
            "Fire definition, protection degradation, spalling, temperature-dependent properties, failure and acceptance remain external.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fabrication.fire_protection_boundary_history",
            FireProtectionBoundaryHistory,
            fire_protection_boundary_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "clock_id": "1",
                "elapsed_time_s": "s",
                "incident_heat_flux_W_m2": "W/m^2",
                "transmitted_heat_flux_into_solid_W_m2": "W/m^2",
                "interval_incident_energy_J_m2": "J/m^2",
                "interval_transmitted_energy_J_m2": "J/m^2",
                "total_incident_energy_J_m2": "J/m^2",
                "total_transmitted_energy_J_m2": "J/m^2",
                "total_incident_energy_J": "J",
                "total_transmitted_energy_J": "J",
                "thermal_boundary_contract": "mixed",
                "outside_incident_flux_support_indices": "1",
                "unsupported_protection_state_indices": "1",
                "missing_reviews": "1",
                "support_id": "1",
                "provider_id": "1",
                "provider_version": "1",
                "provider_digest": "1",
                "transfer_record_digests": "1",
            },
            (
                "The caller supplies the incident flux, protection states, transfer fractions and their reviewed support.",
                "Heat flux is positive into the solid and the caller reviews boundary orientation.",
                "The transfer history is not extrapolated beyond declared flux or state support.",
            ),
            ("reviewed_fire_protection_flux_coupling",),
        )
    ]
