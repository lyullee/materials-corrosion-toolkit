"""Caller-evidenced Nernst potential history from dimensionless activities."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..electrode_kinetics import ButlerVolmerReaction, electrode_reaction_flux
from ..registry import ModelSpec


class CreviceNernstProfile(Contract):
    """Evaluate a supplied redox half-reaction along a local crevice history.

    The caller supplies dimensionless species activities, standard-potential
    history and their evidence. This contract evaluates the Nernst relation;
    it does not infer speciation, reaction direction, mixed potential or rate.
    """

    schema_version: Literal["matintegrity.crevice_nernst_profile.v1"] = "matintegrity.crevice_nernst_profile.v1"
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    source_inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reaction_id: str = Field(min_length=1)
    standard_potential_reference_id: str = Field(min_length=1)
    reaction_quotient_stoichiometry: dict[str, float] = Field(min_length=1)
    electron_number: int = Field(ge=1, le=32)
    elapsed_time_s: tuple[float, ...] = Field(min_length=2, max_length=5000)
    temperature_K: tuple[Positive, ...] = Field(min_length=2, max_length=5000)
    standard_potential_V: tuple[float, ...] = Field(min_length=2, max_length=5000)
    species_activity_history: dict[str, tuple[Positive, ...]] = Field(min_length=1)
    activity_provider_id: str = Field(min_length=1)
    activity_provider_revision: str = Field(min_length=1)
    activity_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standard_potential_provider_id: str = Field(min_length=1)
    standard_potential_provider_revision: str = Field(min_length=1)
    standard_potential_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standard_potential_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    redox_reaction_direction_and_electron_number_reviewed: bool
    activity_standard_state_and_species_mapping_reviewed: bool
    standard_potential_temperature_history_reviewed: bool
    local_activity_history_applicability_reviewed: bool
    potential_only_no_rate_or_acceptance_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_profile(self):
        count = len(self.elapsed_time_s)
        if len(self.temperature_K) != count or len(self.standard_potential_V) != count:
            raise ValueError("time, temperature and standard-potential histories must align")
        if any(not math.isfinite(t) or t < 0.0 for t in self.elapsed_time_s):
            raise ValueError("elapsed times must be finite and nonnegative")
        if any(right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)):
            raise ValueError("elapsed times must strictly increase")
        if any(not math.isfinite(value) for value in self.standard_potential_V):
            raise ValueError("standard-potential history must be finite")
        if any(not key or not math.isfinite(value) or value == 0.0 for key, value in self.reaction_quotient_stoichiometry.items()):
            raise ValueError("reaction quotient terms require finite nonzero signed coefficients")
        if set(self.reaction_quotient_stoichiometry) != set(self.species_activity_history):
            raise ValueError("activity history species must exactly match reaction quotient species")
        if any(len(history) != count for history in self.species_activity_history.values()):
            raise ValueError("every species activity series must align with the time history")
        evidence_ids = {item.source_id for item in self.evidence}
        if self.activity_provider_id not in evidence_ids or self.standard_potential_provider_id not in evidence_ids:
            raise ValueError("activity and standard-potential providers must each map to declared Evidence")
        return self


class NernstDrivenButlerVolmerHistory(Contract):
    """Couple one supplied half-cell potential history to caller BV parameters."""

    schema_version: Literal["matintegrity.nernst_driven_butler_volmer_history.v1"] = (
        "matintegrity.nernst_driven_butler_volmer_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    nernst_result: AssessmentResult
    nernst_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reaction_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    equilibrium_potential_reference_id: str = Field(min_length=1)
    electrode_potential_reference_id: str = Field(min_length=1)
    electrode_potential_difference_history_V: tuple[float, ...] = Field(min_length=2, max_length=5000)
    exchange_current_density_A_m2: Nonnegative
    electron_number: int = Field(ge=1, le=32)
    anodic_transfer_coefficient: Positive = Field(le=1.0)
    cathodic_transfer_coefficient: Positive = Field(le=1.0)
    minimum_overpotential_V: float
    maximum_overpotential_V: float
    stoichiometric_species_coefficients: dict[str, float] = Field(min_length=1)
    kinetics_provider_id: str = Field(min_length=1)
    kinetics_provider_revision: str = Field(min_length=1)
    kinetics_calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    redox_to_kinetics_mapping_reviewed: bool
    reference_electrode_and_potential_basis_reviewed: bool
    rate_parameter_and_temperature_applicability_reviewed: bool
    reaction_direction_and_species_flux_basis_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_upstream_history(self):
        result = self.nernst_result
        if result.model_id not in {
            "degradation.crevice_nernst_potential_history",
            "integration.aqueous_mass_action_to_crevice_nernst_history",
        } or result.status != "computed":
            raise ValueError("a computed, supported crevice Nernst potential-history AssessmentResult is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if expected_input_digest != result.input_digest:
            raise ValueError("upstream Nernst assessment digest does not match its request and context")
        if canonical_digest(result.model_dump(mode="json")) != self.nernst_result_sha256:
            raise ValueError("nernst_result_sha256 must match the complete upstream assessment")
        potential_history = result.values.get("potential_history")
        if not isinstance(potential_history, list) or len(potential_history) != len(self.electrode_potential_difference_history_V):
            raise ValueError("surface and Nernst potential histories must have the same knot count")
        if result.values.get("potential_history_sha256") != canonical_digest(potential_history):
            raise ValueError("upstream potential-history digest does not match the supplied history")
        if result.inputs.get("reaction_id") != self.reaction_id:
            raise ValueError("kinetic reaction ID must match the Nernst half-reaction")
        if result.inputs.get("clock_id") != self.clock_id:
            raise ValueError("kinetic and Nernst histories must use the same declared clock ID")
        if result.inputs.get("standard_potential_reference_id") != self.equilibrium_potential_reference_id:
            raise ValueError("electrode potential reference must match the upstream standard-potential reference")
        if self.equilibrium_potential_reference_id != self.electrode_potential_reference_id:
            raise ValueError("Nernst and electrode potential reference identifiers must match")
        time_values = [row.get("time_s") for row in potential_history]
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in time_values):
            raise ValueError("upstream Nernst time knots must be finite")
        if tuple(time_values) != tuple(result.inputs.get("elapsed_time_s", ())):
            raise ValueError("upstream potential-history knots do not match its original input clock")
        if self.maximum_overpotential_V < self.minimum_overpotential_V:
            raise ValueError("Butler-Volmer overpotential support must be ordered")
        if not self.stoichiometric_species_coefficients or any(
            not species.strip() or not math.isfinite(value) or value == 0.0
            for species, value in self.stoichiometric_species_coefficients.items()
        ):
            raise ValueError("reaction species flux coefficients must be finite and nonzero")
        return self


def crevice_nernst_profile(x: CreviceNernstProfile) -> Calculation:
    """Calculate E = E0 - RT/(nF) ln(Q) at each supplied history knot."""

    input_digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "clock_id": x.clock_id,
        "source_inventory_sha256": x.source_inventory_sha256,
        "reaction_id": x.reaction_id,
        "clock_id": x.clock_id,
        "reaction_quotient_stoichiometry": x.reaction_quotient_stoichiometry,
        "electron_number": x.electron_number,
        "activity_provider_id": x.activity_provider_id,
        "activity_provider_revision": x.activity_provider_revision,
        "activity_configuration_sha256": x.activity_configuration_sha256,
        "activity_record_sha256": x.activity_record_sha256,
        "standard_potential_provider_id": x.standard_potential_provider_id,
        "standard_potential_provider_revision": x.standard_potential_provider_revision,
        "standard_potential_configuration_sha256": x.standard_potential_configuration_sha256,
        "standard_potential_record_sha256": x.standard_potential_record_sha256,
        "input_digest": input_digest,
    }
    reviews = {
        "redox_reaction_direction_and_electron_number_reviewed": x.redox_reaction_direction_and_electron_number_reviewed,
        "activity_standard_state_and_species_mapping_reviewed": x.activity_standard_state_and_species_mapping_reviewed,
        "standard_potential_temperature_history_reviewed": x.standard_potential_temperature_history_reviewed,
        "local_activity_history_applicability_reviewed": x.local_activity_history_applicability_reviewed,
        "potential_only_no_rate_or_acceptance_reviewed": x.potential_only_no_rate_or_acceptance_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing},
            notes=("The potential profile is withheld until reaction, activity, temperature and scope reviews are complete.",),
        )

    gas_constant_J_mol_K = 8.31446261815324
    faraday_C_mol = 96485.33212331002
    reaction_terms = x.reaction_quotient_stoichiometry
    profile = []
    for index, time_s in enumerate(x.elapsed_time_s):
        try:
            ln_q = math.fsum(
                coefficient * math.log(x.species_activity_history[species_id][index])
                for species_id, coefficient in reaction_terms.items()
            )
            potential = x.standard_potential_V[index] - (
                gas_constant_J_mol_K * x.temperature_K[index]
                / (x.electron_number * faraday_C_mol)
            ) * ln_q
        except (OverflowError, ValueError) as error:
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "failed_time_index": index,
                    "failed_time_s": time_s,
                    "failure_reason": str(error),
                    "computed_prefix": profile,
                },
                notes=("The reaction quotient could not be evaluated for the declared positive dimensionless activities.",),
            )
        if not math.isfinite(ln_q) or not math.isfinite(potential):
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "failed_time_index": index,
                    "failed_time_s": time_s,
                    "failure_reason": "nonfinite_nernst_potential",
                    "computed_prefix": profile,
                },
                notes=("A finite potential profile is not reported beyond the numerical support of the input activities.",),
            )
        profile.append({
            "time_s": time_s,
            "temperature_K": x.temperature_K[index],
            "standard_potential_V": x.standard_potential_V[index],
            "ln_reaction_quotient": ln_q,
            "potential_V": potential,
        })

    return Calculation(
        values=base | {
            "potential_history": profile,
            "potential_history_sha256": canonical_digest(profile),
            "reaction_quotient_definition": "lnQ=sum(nu_i*ln(a_i)); products positive, reactants negative; electrons excluded",
            "standard_potential_interpretation": "caller_supplied_knotwise_history",
            "missing_reviews": [],
        },
        notes=(
            "This is a Nernst half-cell potential calculated from caller-supplied dimensionless activities and standard-potential history.",
            "It does not determine mixed potential, corrosion current, reaction kinetics, pH, activity coefficients, phase state, susceptibility, life or acceptance.",
        ),
    )


def evaluate_nernst_driven_butler_volmer_history(x: NernstDrivenButlerVolmerHistory) -> Calculation:
    """Apply one caller BV reaction at aligned surface/half-cell potential knots."""
    result = x.nernst_result
    nernst_history = result.values["potential_history"]
    upstream_digest = x.nernst_result_sha256
    base = {
        "assessment_id": x.assessment_id,
        "reaction_id": x.reaction_id,
        "physical_scope_id": result.inputs["physical_scope_id"],
        "source_inventory_sha256": result.values["source_inventory_sha256"],
        "nernst_assessment_sha256": upstream_digest,
        "nernst_input_digest": result.input_digest,
        "nernst_potential_history_sha256": result.values["potential_history_sha256"],
        "kinetics_provider_id": x.kinetics_provider_id,
        "kinetics_provider_revision": x.kinetics_provider_revision,
        "kinetics_calibration_sha256": x.kinetics_calibration_sha256,
        "electrode_potential_reference_id": x.electrode_potential_reference_id,
        "electrode_potential_history_sha256": canonical_digest(x.electrode_potential_difference_history_V),
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
    }
    reviews = {
        "redox_to_kinetics_mapping_reviewed": x.redox_to_kinetics_mapping_reviewed,
        "reference_electrode_and_potential_basis_reviewed": x.reference_electrode_and_potential_basis_reviewed,
        "rate_parameter_and_temperature_applicability_reviewed": x.rate_parameter_and_temperature_applicability_reviewed,
        "reaction_direction_and_species_flux_basis_reviewed": x.reaction_direction_and_species_flux_basis_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    history = []
    for index, (nernst_row, surface_potential) in enumerate(
        zip(nernst_history, x.electrode_potential_difference_history_V, strict=True)
    ):
        reaction = ButlerVolmerReaction(
            reaction_id=x.reaction_id,
            calibration_sha256=x.kinetics_calibration_sha256,
            exchange_current_density_A_m2=x.exchange_current_density_A_m2,
            electron_count=x.electron_number,
            anodic_transfer_coefficient=x.anodic_transfer_coefficient,
            cathodic_transfer_coefficient=x.cathodic_transfer_coefficient,
            equilibrium_potential_V=nernst_row["potential_V"],
            temperature_K=nernst_row["temperature_K"],
            minimum_overpotential_V=x.minimum_overpotential_V,
            maximum_overpotential_V=x.maximum_overpotential_V,
            stoichiometric_species_coefficients=x.stoichiometric_species_coefficients,
            calibration_and_reaction_direction_reviewed=True,
        )
        try:
            flux = electrode_reaction_flux(reaction, surface_potential)
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "failed_time_index": index,
                "failed_time_s": nernst_row["time_s"],
                "failure_reason": str(error),
                "computed_prefix": history,
            })
        if flux.get("status") != "computed":
            return Calculation(status="out_of_scope", values=base | {
                "failed_time_index": index,
                "failed_time_s": nernst_row["time_s"],
                "failure_reason": flux.get("reason", "overpotential_outside_declared_support"),
                "computed_prefix": history,
            })
        overpotential = surface_potential - nernst_row["potential_V"]
        history.append({
            "time_s": nernst_row["time_s"],
            "temperature_K": nernst_row["temperature_K"],
            "equilibrium_potential_V": nernst_row["potential_V"],
            "electrode_potential_difference_V": surface_potential,
            "overpotential_V": overpotential,
            "signed_current_density_A_m2": flux["signed_current_density_A_m2"],
            "gross_anodic_current_density_A_m2": flux["gross_anodic_current_density_A_m2"],
            "gross_cathodic_current_density_A_m2": flux["gross_cathodic_current_density_A_m2"],
            "signed_reaction_extent_mol_m2_s": flux["signed_reaction_extent_mol_m2_s"],
            "species_flux_mol_m2_s": flux["inward_species_flux_mol_m2_s"],
        })
    return Calculation(values=base | {
        "reaction_flux_history": history,
        "reaction_flux_history_sha256": canonical_digest(history),
        "history_policy": "caller_values_at_exact_Nernst_time_knots; no interpolation_or_time_integration",
        "current_interpretation": "caller-calibrated_single-reaction_signed_partial_current_density",
    }, notes=(
        "The caller-supplied Butler-Volmer reaction is evaluated at each aligned knot using the upstream Nernst half-cell potential as its equilibrium-potential history.",
        "This does not solve mixed potential, infer activity or kinetics, integrate charge, infer total corrosion loss, establish protection, life or acceptance.",
    ))


def build_crevice_nernst_request_from_inventory(
    inventory_result: AssessmentResult,
    *,
    assessment_id: str,
    reaction_id: str,
    standard_potential_reference_id: str,
    reaction_quotient_stoichiometry: dict[str, float],
    electron_number: int,
    standard_potential_V: tuple[float, ...],
    standard_concentration_mol_m3: dict[str, Positive],
    activity_coefficient_history: dict[str, tuple[Positive, ...]],
    activity_provider_id: str,
    activity_provider_revision: str,
    activity_configuration_sha256: str,
    activity_record_sha256: str,
    standard_potential_provider_id: str,
    standard_potential_provider_revision: str,
    standard_potential_configuration_sha256: str,
    standard_potential_record_sha256: str,
    redox_reaction_direction_and_electron_number_reviewed: bool,
    activity_standard_state_and_species_mapping_reviewed: bool,
    standard_potential_temperature_history_reviewed: bool,
    local_activity_history_applicability_reviewed: bool,
    potential_only_no_rate_or_acceptance_reviewed: bool,
    computational_use_authorized: bool,
    evidence: tuple[Evidence, ...],
) -> CreviceNernstProfile:
    """Bind inventory concentrations to a Nernst request using caller gamma/E0.

    Only a computed inventory result is accepted. Activity coefficients,
    standard concentrations and standard-potential values remain caller-owned.
    """

    if inventory_result.status != "computed":
        raise ValueError("only a computed crevice inventory result can be bound")
    values = inventory_result.values
    required = (
        "elapsed_time_s", "condition_knot_history",
        "species_concentration_history_mol_m3", "physical_scope_id", "clock_id", "asset_id", "location_id",
    )
    if any(name not in values for name in required):
        raise ValueError("inventory result lacks time, condition or species concentration history")
    elapsed = tuple(values["elapsed_time_s"])
    knots = values["condition_knot_history"]
    concentration_history = values["species_concentration_history_mol_m3"]
    if len(knots) != len(elapsed) or len(standard_potential_V) != len(elapsed):
        raise ValueError("temperature and standard-potential profiles must align with inventory time")
    temperatures = tuple(row["temperature_K"] for row in knots)
    species = set(reaction_quotient_stoichiometry)
    if set(standard_concentration_mol_m3) != species or set(activity_coefficient_history) != species:
        raise ValueError("standard states and activity coefficients must exactly cover reaction species")
    activities = {}
    for species_id in sorted(species):
        if species_id not in concentration_history:
            raise ValueError(f"reaction species {species_id!r} is absent from inventory output")
        concentrations = concentration_history[species_id]
        gammas = activity_coefficient_history[species_id]
        standard = float(standard_concentration_mol_m3[species_id])
        if len(concentrations) != len(elapsed) or len(gammas) != len(elapsed):
            raise ValueError("concentration and activity-coefficient histories must align with inventory time")
        if not math.isfinite(standard) or standard <= 0.0:
            raise ValueError("activity standard concentration must be finite and positive")
        values_at_knots = tuple(float(c) * float(gamma) / standard for c, gamma in zip(concentrations, gammas, strict=True))
        if any(not math.isfinite(value) or value <= 0.0 for value in values_at_knots):
            raise ValueError("all reaction species activities must be finite and positive at every knot")
        activities[species_id] = values_at_knots
    return CreviceNernstProfile(
        assessment_id=assessment_id,
        asset_id=values["asset_id"],
        location_id=values["location_id"],
        physical_scope_id=values["physical_scope_id"],
        clock_id=values["clock_id"],
        source_inventory_sha256=canonical_digest(inventory_result.model_dump(mode="json")),
        reaction_id=reaction_id,
        standard_potential_reference_id=standard_potential_reference_id,
        reaction_quotient_stoichiometry=reaction_quotient_stoichiometry,
        electron_number=electron_number,
        elapsed_time_s=elapsed,
        temperature_K=temperatures,
        standard_potential_V=standard_potential_V,
        species_activity_history=activities,
        activity_provider_id=activity_provider_id,
        activity_provider_revision=activity_provider_revision,
        activity_configuration_sha256=activity_configuration_sha256,
        activity_record_sha256=activity_record_sha256,
        standard_potential_provider_id=standard_potential_provider_id,
        standard_potential_provider_revision=standard_potential_provider_revision,
        standard_potential_configuration_sha256=standard_potential_configuration_sha256,
        standard_potential_record_sha256=standard_potential_record_sha256,
        redox_reaction_direction_and_electron_number_reviewed=redox_reaction_direction_and_electron_number_reviewed,
        activity_standard_state_and_species_mapping_reviewed=activity_standard_state_and_species_mapping_reviewed,
        standard_potential_temperature_history_reviewed=standard_potential_temperature_history_reviewed,
        local_activity_history_applicability_reviewed=local_activity_history_applicability_reviewed,
        potential_only_no_rate_or_acceptance_reviewed=potential_only_no_rate_or_acceptance_reviewed,
        computational_use_authorized=computational_use_authorized,
        evidence=evidence,
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "degradation.crevice_nernst_potential_history",
        CreviceNernstProfile,
        crevice_nernst_profile,
        {
            "source_inventory_sha256": "1",
            "elapsed_time_s": "s",
            "temperature_K": "K",
            "standard_potential_V": "V",
            "potential_history[].time_s": "s",
            "potential_history[].temperature_K": "K",
            "potential_history[].standard_potential_V": "V",
            "potential_history[].potential_V": "V",
            "potential_history[].ln_reaction_quotient": "1",
            "electron_number": "1",
            "potential_history_sha256": "1",
        },
        (
            "Apply the Nernst equation at supplied time knots using caller-provided dimensionless activities and standard-potential history.",
            "Reaction direction, activity standard state, species mapping and temperature applicability are reviewed caller inputs; this half-cell potential is not a mixed-potential or corrosion-rate calculation.",
        ),
        ("crevice_nernst_activity_potential",),
        qualification="user_model",
    ), ModelSpec(
        "electrochemistry.nernst_driven_butler_volmer_history",
        NernstDrivenButlerVolmerHistory,
        evaluate_nernst_driven_butler_volmer_history,
        {
            "time_s": "s",
            "temperature_K": "K",
            "equilibrium_potential_V": "V",
            "electrode_potential_difference_V": "V",
            "overpotential_V": "V",
            "signed_current_density_A_m2": "A/m2",
            "gross_anodic_current_density_A_m2": "A/m2",
            "gross_cathodic_current_density_A_m2": "A/m2",
            "signed_reaction_extent_mol_m2_s": "mol/m2/s",
            "species_flux_mol_m2_s.*": "mol/m2/s",
        },
        (
            "Evaluate one caller-calibrated Butler-Volmer reaction at exact common time knots using an upstream digest-bound Nernst equilibrium-potential history.",
            "Caller must match the potential reference, redox/kinetic direction, reaction identity and temperature support. The API does not interpolate or integrate time and does not determine mixed potential or total corrosion rate.",
        ),
        ("nernst_driven_butler_volmer_history",),
        qualification="user_model",
    )]
