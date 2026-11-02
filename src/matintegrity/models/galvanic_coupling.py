"""Bounded galvanic-coupling assessment over caller-owned polarization evidence."""

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .electrochemistry import MixedPotential, PolarizationCurve, PolarizedElectrode, mixed_potential


class GalvanicEnvironment(Contract):
    environment_id: str = Field(min_length=1)
    electrolyte_id: str = Field(min_length=1)
    electrolyte_description: str = Field(min_length=1)
    temperature_K: Positive
    reference_electrode_id: str = Field(min_length=1)
    condition_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class PartialDissolutionObservation(Contract):
    observation_id: str = Field(min_length=1)
    electrode_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    partial_dissolution_current_density_A_m2: Nonnegative
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class GalvanicElectrodeEvidence(Contract):
    electrode_id: str = Field(min_length=1)
    metal_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    exposed_area_m2: Positive
    polarization_curve: PolarizationCurve
    curve_provider_id: str = Field(min_length=1)
    curve_provider_revision: str = Field(min_length=1)
    curve_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_support_reviewed: bool


class ElectricalConnection(Contract):
    connection_id: str = Field(min_length=1)
    state: Literal["connected", "open"]
    total_resistance_ohm: Nonnegative
    resistance_basis: str = Field(min_length=1)
    resistance_reviewed: bool
    maximum_negligible_resistance_ohm: Nonnegative


class GalvanicCouplingAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    environment: GalvanicEnvironment
    electrodes: tuple[GalvanicElectrodeEvidence, ...] = Field(min_length=2, max_length=32)
    connection: ElectricalConnection
    partial_dissolution_observations: tuple[PartialDissolutionObservation, ...] = ()
    solver_id: Literal["matintegrity.corrosion.mixed_potential.v1"]
    solver_revision: str = Field(min_length=1)
    quasi_steady_reviewed: bool
    condition_compatibility_reviewed: bool
    anodic_positive_net_current_reviewed: bool
    caller_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_evidence(self):
        electrode_ids = [item.electrode_id for item in self.electrodes]
        if len(electrode_ids) != len(set(electrode_ids)):
            raise ValueError("galvanic electrode identities must be unique")
        curve_ids = [item.polarization_curve.curve_id for item in self.electrodes]
        if len(curve_ids) != len(set(curve_ids)):
            raise ValueError("polarization curve identities must be unique")
        observation_ids = [item.observation_id for item in self.partial_dissolution_observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("partial dissolution observation identities must be unique")
        if any(item.electrode_id not in electrode_ids for item in self.partial_dissolution_observations):
            raise ValueError("partial dissolution observations must reference an electrode")
        return self


def galvanic_coupling(x: GalvanicCouplingAssessment) -> Calculation:
    """Delegate a reviewed negligible-resistance case to the mixed-potential solver."""
    input_digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "environment_id": x.environment.environment_id,
        "solver_id": x.solver_id,
        "solver_revision": x.solver_revision,
        "input_digest": input_digest,
        "mixed_potential_V": None,
        "signed_net_electrode_current_A": None,
        "partial_dissolution_observations": [
            item.model_dump(mode="json") for item in x.partial_dissolution_observations
        ],
    }
    notes = (
        "Signed net external electrode current is not a partial metal-dissolution current; caller-supplied partial dissolution observations remain separate.",
        "The delegated solver interpolates only within common supplied curve support and does not model a non-negligible connection or electrolyte voltage drop.",
        "No corrosion rate, remaining life, acceptance decision, dynamic stability, or failure probability is inferred.",
    )

    def result(status: Literal["computed", "needs_data", "out_of_scope"], reason: str, **values):
        return Calculation(status=status, values=base | {"reason": reason} | values, notes=notes)

    reviews = {
        "caller_reviewed": x.caller_reviewed,
        "quasi_steady_reviewed": x.quasi_steady_reviewed,
        "condition_compatibility_reviewed": x.condition_compatibility_reviewed,
        "anodic_positive_net_current_reviewed": x.anodic_positive_net_current_reviewed,
        "resistance_reviewed": x.connection.resistance_reviewed,
        "curve_support_reviewed": all(item.curve_support_reviewed for item in x.electrodes),
    }
    unreviewed = [name for name, reviewed in reviews.items() if not reviewed]
    if unreviewed:
        return result("needs_data", "unreviewed_applicability", unreviewed=unreviewed)
    if x.connection.state != "connected":
        return result("out_of_scope", "electrical_connection_open")
    if x.connection.total_resistance_ohm > x.connection.maximum_negligible_resistance_ohm:
        return result(
            "out_of_scope",
            "connection_resistance_not_negligible",
            total_resistance_ohm=x.connection.total_resistance_ohm,
            maximum_negligible_resistance_ohm=x.connection.maximum_negligible_resistance_ohm,
        )

    for electrode in x.electrodes:
        curve = electrode.polarization_curve
        expected = (
            x.environment.electrolyte_id,
            x.environment.reference_electrode_id,
            x.environment.temperature_K,
        )
        observed = (curve.electrolyte_id, curve.reference_electrode_id, curve.temperature_K)
        if any(value is None for value in observed):
            return result("needs_data", "missing_curve_environment", electrode_id=electrode.electrode_id)
        if observed != expected:
            return result("out_of_scope", "curve_environment_mismatch", electrode_id=electrode.electrode_id)

    delegated = mixed_potential(
        MixedPotential(
            electrodes=[
                PolarizedElectrode(
                    electrode_id=item.electrode_id,
                    exposed_area_m2=item.exposed_area_m2,
                    curve=item.polarization_curve,
                )
                for item in x.electrodes
            ],
            quasi_steady_reviewed=x.quasi_steady_reviewed,
            negligible_ohmic_drop_reviewed=True,
            condition_compatibility_reviewed=x.condition_compatibility_reviewed,
            anodic_positive_reviewed=x.anodic_positive_net_current_reviewed,
        )
    )
    details = {
        "connection": x.connection.model_dump(mode="json"),
        "curve_provenance": [
            {
                "electrode_id": item.electrode_id,
                "curve_id": item.polarization_curve.curve_id,
                "provider_id": item.curve_provider_id,
                "provider_revision": item.curve_provider_revision,
                "input_digest": item.curve_input_digest,
                "result_digest": item.curve_result_digest,
                "support_V": [
                    item.polarization_curve.potential_V[0],
                    item.polarization_curve.potential_V[-1],
                ],
            }
            for item in x.electrodes
        ],
        "delegated_result": delegated.model_dump(mode="json"),
    }
    if delegated.status != "computed":
        return result(delegated.status, f"mixed_potential:{delegated.values['reason']}", **details)
    return result(
        "computed",
        "bounded_negligible_resistance_coupling",
        **details,
        mixed_potential_V=delegated.values["mixed_potential_V"],
        signed_net_electrode_current_A=delegated.values["electrode_net_current_A"],
        current_meaning="signed_net_external_current_not_partial_dissolution",
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "degradation.galvanic_coupling",
            GalvanicCouplingAssessment,
            galvanic_coupling,
            {
                "mixed_potential_V": "V",
                "signed_net_electrode_current_A": "A",
                "partial_dissolution_observations": "A/m2",
            },
            (
                "Caller-reviewed, condition-compatible signed polarization curves are solved only on their common measured support.",
                "Connection resistance must remain within the caller-declared negligible-resistance bound; otherwise this model is out of scope.",
                "Net current and separately supplied partial dissolution evidence are not interchangeable, and no rate, life, acceptance, or probability is produced.",
            ),
            ("authored_bounded_galvanic_coupling_assessment",),
        )
    ]
