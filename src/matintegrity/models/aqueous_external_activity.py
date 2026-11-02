"""Composition-coupled aqueous activity interface for caller-owned libraries.

The module deliberately has no import-time dependency on Pitzer or another
thermodynamic package.  A caller supplies a provider callback that evaluates
molality-standard-state activity coefficients for one exact composition.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Mapping
from typing import Any, Literal

import numpy as np
from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .aqueous_activity_iteration import molality_gamma_to_molarity_standard_state
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation


class ExternalAqueousTransportActivity(Contract):
    """Provenance and species map for external gamma evaluation in transport."""

    schema_version: Literal["matintegrity.external_aqueous_transport_activity.v1"] = (
        "matintegrity.external_aqueous_transport_activity.v1"
    )
    temperature_K: Positive
    species_ids: tuple[str, ...] = Field(min_length=2, max_length=100)
    charge_numbers: tuple[StrictInt, ...] = Field(min_length=2, max_length=100)
    water_mass_per_solution_volume_kg_L: Positive
    ionic_strength_limit_mol_kg: Positive = Field(le=100.0)
    ionic_strength_consistency_tolerance_mol_kg: Positive = Field(default=1e-8, le=0.1)
    activity_provider_id: str = Field(min_length=1)
    activity_provider_revision: str = Field(min_length=1)
    activity_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    single_ion_activity_convention_id: str = Field(min_length=1)
    water_mass_and_molality_conversion_reviewed: bool
    species_order_charge_and_inventory_reviewed: bool
    temperature_solvent_and_parameter_coverage_reviewed: bool
    single_ion_convention_and_transport_chemical_potential_reviewed: bool
    no_precipitation_or_phase_change_reviewed: bool
    deterministic_provider_re_evaluation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_transport_activity_contract(self):
        if len(self.species_ids) != len(set(self.species_ids)) or any(not item.strip() for item in self.species_ids):
            raise ValueError("transport provider species identifiers must be unique and nonempty")
        if len(self.charge_numbers) != len(self.species_ids) or any(abs(value) > 8 for value in self.charge_numbers):
            raise ValueError("transport provider charges must align exactly with species order")
        if not any(row.source_id == self.activity_provider_id
                   and row.sha256 == self.activity_parameter_record_sha256 for row in self.evidence):
            raise ValueError("external transport parameter record must match declared Evidence")
        return self


def build_external_aqueous_transport_activity_callback(
    request: ExternalAqueousTransportActivity, *, activity_provider
):
    """Build a molality-gamma callback for restricted transport's mouth/cell states."""
    reviews = (
        request.water_mass_and_molality_conversion_reviewed,
        request.species_order_charge_and_inventory_reviewed,
        request.temperature_solvent_and_parameter_coverage_reviewed,
        request.single_ion_convention_and_transport_chemical_potential_reviewed,
        request.no_precipitation_or_phase_change_reviewed,
        request.deterministic_provider_re_evaluation_reviewed,
    )
    if not all(reviews):
        raise ValueError("all external activity transport applicability reviews are required")
    if not callable(activity_provider):
        raise ValueError("a caller-owned external activity provider callback is required")
    for attribute, expected in (
        ("provider_id", request.activity_provider_id),
        ("provider_revision", request.activity_provider_revision),
        ("configuration_sha256", request.activity_configuration_sha256),
        ("parameter_record_sha256", request.activity_parameter_record_sha256),
    ):
        actual = getattr(activity_provider, attribute, expected)
        if actual != expected:
            raise ValueError(f"external provider {attribute} differs from the reviewed transport contract")

    charges = np.asarray(request.charge_numbers, dtype=float)
    species_ids = list(request.species_ids)
    water_mass = float(request.water_mass_per_solution_volume_kg_L)
    request_digest = canonical_digest(request.model_dump(mode="json"))

    runtime_trace = {"provider_evaluation_count": 0, "transcript_sha256": request_digest}

    def activity_coefficients(time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
        if not math.isfinite(float(time_s)):
            raise ValueError("transport provider time must be finite")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.ndim != 2 or concentration.shape[0] != len(species_ids):
            raise ValueError("external provider expects species by mouth-plus-cell concentrations")
        if not np.isfinite(concentration).all() or np.any(concentration < 0.0):
            raise ValueError("transport concentration state must be finite and nonnegative")
        molality = concentration / (1000.0 * water_mass)
        ionic_strength = 0.5 * np.sum(charges[:, None] ** 2 * molality, axis=0)
        if not np.isfinite(ionic_strength).all() or np.any(ionic_strength > request.ionic_strength_limit_mol_kg):
            raise ValueError("transport composition exceeds external activity provider ionic-strength support")
        gamma = np.empty_like(concentration, dtype=float)
        for state_index in range(concentration.shape[1]):
            provider_request = {
                "time_s": float(time_s),
                "spatial_state_index": state_index,
                "temperature_K": float(request.temperature_K),
                "species_ids": species_ids,
                "charge_numbers": list(request.charge_numbers),
                "molality_mol_kg_water": molality[:, state_index].tolist(),
                "ionic_strength_mol_kg_water": float(ionic_strength[state_index]),
                "water_mass_per_solution_volume_kg_L": water_mass,
                "activity_standard_state": "molality_1_mol_kg_water",
                "single_ion_activity_convention_id": request.single_ion_activity_convention_id,
                "transport_callback_request_sha256": request_digest,
            }
            provider_request_sha256 = canonical_digest(provider_request)
            response = activity_provider(provider_request)
            if not isinstance(response, Mapping):
                raise ValueError("external transport activity provider must return a mapping")
            response = dict(response)
            try:
                provider_result_sha256 = canonical_digest(response)
            except (TypeError, ValueError) as error:
                raise ValueError("provider response must contain only JSON-compatible digestible values") from error
            expected = {
                "status": "computed",
                "provider_id": request.activity_provider_id,
                "provider_revision": request.activity_provider_revision,
                "configuration_sha256": request.activity_configuration_sha256,
                "parameter_record_sha256": request.activity_parameter_record_sha256,
                "request_sha256": provider_request_sha256,
                "activity_standard_state": "molality_1_mol_kg_water",
                "single_ion_activity_convention_id": request.single_ion_activity_convention_id,
                "species_ids": species_ids,
            }
            if any(response.get(key) != value for key, value in expected.items()):
                raise ValueError("external transport activity provider returned mismatched lineage or species mapping")
            try:
                returned_ionic_strength = float(response["ionic_strength_mol_kg_water"])
                values = np.asarray(response["activity_coefficients_molality_standard_state"], dtype=float)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("external transport provider response is missing required numeric fields") from error
            if (not math.isfinite(returned_ionic_strength) or returned_ionic_strength < 0.0
                    or abs(returned_ionic_strength - ionic_strength[state_index]) > request.ionic_strength_consistency_tolerance_mol_kg):
                raise ValueError("external provider ionic strength differs from the complete transport species inventory")
            if values.shape != (len(species_ids),) or not np.isfinite(values).all() or np.any(values <= 0.0):
                raise ValueError("external provider gamma vector must be finite, positive and match species order")
            gamma[:, state_index] = values
            runtime_trace["provider_evaluation_count"] += 1
            runtime_trace["transcript_sha256"] = hashlib.sha256((
                runtime_trace["transcript_sha256"] + provider_request_sha256 + provider_result_sha256
            ).encode("ascii")).hexdigest()
        return gamma

    activity_coefficients.runtime_trace = runtime_trace
    activity_coefficients.provider_id = request.activity_provider_id
    activity_coefficients.provider_revision = request.activity_provider_revision
    activity_coefficients.configuration_sha256 = canonical_digest({
        "adapter": "matintegrity.external_aqueous_transport_activity.v1",
        "request_sha256": request_digest,
        "provider_configuration_sha256": request.activity_configuration_sha256,
        "species_ids": species_ids,
        "temperature_K": float(request.temperature_K),
        "concentration_unit": "mol/m3",
        "provider_activity_standard_state": "molality_1_mol_kg_water",
        "transport_uses_molality_gamma_for_chemical_potential_gradient": True,
    })
    activity_coefficients.record_sha256 = request.activity_parameter_record_sha256
    activity_coefficients.source_request_sha256 = request_digest
    activity_coefficients.species_ids = request.species_ids
    activity_coefficients.temperature_K = float(request.temperature_K)
    activity_coefficients.single_ion_activity_convention_id = request.single_ion_activity_convention_id
    return activity_coefficients


class ExternalAqueousActivityIteration(Contract):
    """Inputs and lineage for a caller-supplied composition-dependent gamma law."""

    schema_version: Literal["matintegrity.external_aqueous_activity_iteration.v1"] = (
        "matintegrity.external_aqueous_activity_iteration.v1"
    )
    system: AqueousMassActionSystem
    water_mass_per_solution_volume_kg_L: Positive
    ionic_strength_limit_mol_kg: Positive = Field(le=100.0)
    ionic_strength_consistency_tolerance_mol_kg: Positive = Field(default=1e-8, le=0.1)
    charge_balance_tolerance_mol_kg: Positive
    activity_provider_id: str = Field(min_length=1)
    activity_provider_revision: str = Field(min_length=1)
    activity_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    molality_activity_standard_state: Literal["molality_1_mol_kg_water"] = "molality_1_mol_kg_water"
    single_ion_activity_convention_id: str = Field(min_length=1)
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    temperature_and_parameter_support_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    provider_species_order_and_unit_mapping_reviewed: bool
    single_ion_activity_convention_reviewed: bool
    provider_parameter_coverage_and_applicability_reviewed: bool
    deterministic_provider_re_evaluation_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_provider_contract(self):
        if self.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("external molality activity providers require a molarity-standard-state mass-action system")
        if not any(
            row.source_id == self.activity_provider_id
            and row.sha256 == self.activity_parameter_record_sha256
            for row in self.evidence
        ):
            raise ValueError("provider parameter record must be linked to matching Evidence")
        if len({row.species_id for row in self.system.species}) != len(self.system.species):
            raise ValueError("mass-action species identifiers must be unique")
        finite = (
            self.system.temperature_K,
            self.water_mass_per_solution_volume_kg_L,
            self.ionic_strength_limit_mol_kg,
            self.ionic_strength_consistency_tolerance_mol_kg,
            self.charge_balance_tolerance_mol_kg,
            self.log_gamma_tolerance,
            self.damping_fraction,
        )
        if any(not math.isfinite(value) for value in finite):
            raise ValueError("external activity conditions and tolerances must be finite")
        return self


def aqueous_external_activity_self_consistent_speciation(
    request: ExternalAqueousActivityIteration,
    *,
    activity_provider: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> Calculation:
    """Iterate caller-defined aqueous mass action with an external gamma provider.

    The callback receives one JSON-compatible composition mapping. It must
    return the exact request digest, provider identity and an ordered vector of
    molality-standard-state activity coefficients. Response values must use
    JSON-native scalars, lists, strings and mappings so the recorded digest is
    portable and deterministic. No third-party package is imported or executed
    by this module itself.
    """
    system = request.system
    species = system.species
    species_ids = [row.species_id for row in species]
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "activity_standard_state": "dimensionless_molarity_1_mol_L",
        "provider_activity_standard_state": request.molality_activity_standard_state,
        "activity_coefficient_mapping": "gamma_c=gamma_m/w; w=kg_water_per_L_solution",
        "water_mass_per_solution_volume_kg_L": request.water_mass_per_solution_volume_kg_L,
        "ionic_strength_limit_mol_kg": request.ionic_strength_limit_mol_kg,
        "activity_provider_id": request.activity_provider_id,
        "activity_provider_revision": request.activity_provider_revision,
        "activity_configuration_sha256": request.activity_configuration_sha256,
        "activity_parameter_record_sha256": request.activity_parameter_record_sha256,
        "single_ion_activity_convention_id": request.single_ion_activity_convention_id,
        "input_sha256": input_digest,
    }
    reviews = {
        "water_mass_conversion_reviewed": request.water_mass_conversion_reviewed,
        "molarity_to_molality_standard_state_mapping_reviewed": request.molarity_to_molality_standard_state_mapping_reviewed,
        "temperature_and_parameter_support_reviewed": request.temperature_and_parameter_support_reviewed,
        "complete_inventory_and_charge_scope_reviewed": request.complete_inventory_and_charge_scope_reviewed,
        "provider_species_order_and_unit_mapping_reviewed": request.provider_species_order_and_unit_mapping_reviewed,
        "single_ion_activity_convention_reviewed": request.single_ion_activity_convention_reviewed,
        "provider_parameter_coverage_and_applicability_reviewed": request.provider_parameter_coverage_and_applicability_reviewed,
        "deterministic_provider_re_evaluation_reviewed": request.deterministic_provider_re_evaluation_reviewed,
        "fixed_point_solver_settings_reviewed": request.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": request.single_liquid_no_precipitation_scope_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0})
    if not callable(activity_provider):
        return Calculation(status="needs_data", values=base | {
            "reason": "external_activity_provider_callback_is_unavailable",
            "outer_iterations": 0,
        })
    for attribute, expected in (
        ("provider_id", request.activity_provider_id),
        ("provider_revision", request.activity_provider_revision),
        ("configuration_sha256", request.activity_configuration_sha256),
        ("parameter_record_sha256", request.activity_parameter_record_sha256),
    ):
        actual = getattr(activity_provider, attribute, expected)
        if actual != expected:
            return Calculation(status="needs_data", values=base | {
                "reason": "external_activity_provider_object_lineage_mismatch",
                "mismatched_provider_attribute": attribute,
                "outer_iterations": 0,
            })

    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    history: list[dict[str, Any]] = []
    last_solution = None
    try:
        for iteration in range(1, request.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(
                    row.model_copy(update={"activity_coefficient": float(gamma[index])})
                    for index, row in enumerate(species)
                ),
                "activity_provider_id": request.activity_provider_id,
                "activity_provider_revision": request.activity_provider_revision,
                "activity_configuration_digest": request.activity_configuration_sha256,
                "activity_record_digest": request.activity_parameter_record_sha256,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(status=solved.status, values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "inner_solver_status": solved.status,
                    "inner_solver_values": solved.values,
                }, notes=("The fixed-activity mass-action solve did not produce a computed state; no coupled result is reported.",))
            concentration_mol_L = np.asarray(
                [row["concentration_mol_L"] for row in solved.values["species"]], dtype=float
            )
            molality = concentration_mol_L / request.water_mass_per_solution_volume_kg_L
            ionic_strength = 0.5 * float(np.dot(molality, charges**2))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > request.ionic_strength_limit_mol_kg:
                return Calculation(status="out_of_scope", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "out_of_scope_reason": "speciation_ionic_strength_exceeds_provider_support",
                    "fixed_point_history": history,
                })
            if not math.isfinite(charge_residual) or abs(charge_residual) > request.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "reason": "complete_speciation_inventory_charge_balance_exceeds_tolerance",
                    "fixed_point_history": history,
                })
            provider_request = {
                "temperature_K": float(system.temperature_K),
                "species_ids": species_ids,
                "charge_numbers": [int(row.charge_number) for row in species],
                "molality_mol_kg_water": molality.tolist(),
                "ionic_strength_mol_kg_water": ionic_strength,
                "water_mass_per_solution_volume_kg_L": float(request.water_mass_per_solution_volume_kg_L),
                "activity_standard_state": request.molality_activity_standard_state,
                "single_ion_activity_convention_id": request.single_ion_activity_convention_id,
            }
            provider_request_sha256 = canonical_digest(provider_request)
            raw_response = activity_provider(provider_request)
            if not isinstance(raw_response, Mapping):
                raise ValueError("external activity provider must return a mapping")
            response = dict(raw_response)
            provider_result_sha256 = canonical_digest(response)
            expected_metadata = {
                "status": "computed",
                "provider_id": request.activity_provider_id,
                "provider_revision": request.activity_provider_revision,
                "configuration_sha256": request.activity_configuration_sha256,
                "parameter_record_sha256": request.activity_parameter_record_sha256,
                "request_sha256": provider_request_sha256,
                "activity_standard_state": request.molality_activity_standard_state,
                "single_ion_activity_convention_id": request.single_ion_activity_convention_id,
            }
            mismatched = [key for key, value in expected_metadata.items() if response.get(key) != value]
            if mismatched:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "provider_request_sha256": provider_request_sha256,
                    "provider_result_sha256": provider_result_sha256,
                    "mismatched_provider_response_fields": mismatched,
                    "fixed_point_history": history,
                })
            required_response_fields = {
                "species_ids",
                "ionic_strength_mol_kg_water",
                "activity_coefficients_molality_standard_state",
            }
            missing_response_fields = sorted(required_response_fields.difference(response))
            if missing_response_fields:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "provider_request_sha256": provider_request_sha256,
                    "provider_result_sha256": provider_result_sha256,
                    "missing_provider_response_fields": missing_response_fields,
                    "fixed_point_history": history,
                })
            if response.get("species_ids") != species_ids:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "provider_request_sha256": provider_request_sha256,
                    "provider_result_sha256": provider_result_sha256,
                    "reason": "provider_species_order_or_coverage_mismatch",
                    "fixed_point_history": history,
                })
            provider_ionic_strength = float(response["ionic_strength_mol_kg_water"])
            if (not math.isfinite(provider_ionic_strength)
                    or provider_ionic_strength < 0.0
                    or abs(provider_ionic_strength - ionic_strength)
                    > request.ionic_strength_consistency_tolerance_mol_kg):
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "provider_ionic_strength_mol_kg": provider_ionic_strength,
                    "provider_request_sha256": provider_request_sha256,
                    "provider_result_sha256": provider_result_sha256,
                    "reason": "provider_ionic_strength_does_not_match_complete_species_inventory",
                    "fixed_point_history": history,
                })
            target_gamma_molality = np.asarray(
                response["activity_coefficients_molality_standard_state"], dtype=float
            )
            if (target_gamma_molality.shape != (len(species),)
                    or not np.isfinite(target_gamma_molality).all()
                    or np.any(target_gamma_molality <= 0.0)):
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "provider_request_sha256": provider_request_sha256,
                    "provider_result_sha256": provider_result_sha256,
                    "reason": "provider_activity_coefficient_vector_is_invalid",
                    "fixed_point_history": history,
                })
            target_gamma_molarity = molality_gamma_to_molarity_standard_state(
                target_gamma_molality, float(request.water_mass_per_solution_volume_kg_L)
            )
            log_residual = float(np.max(np.abs(np.log(target_gamma_molarity) - np.log(gamma))))
            optional_properties = {}
            for key in ("osmotic_coefficient", "water_activity"):
                if key in response:
                    value = float(response[key])
                    if not math.isfinite(value) or (key == "water_activity" and not 0.0 < value <= 1.0):
                        return Calculation(status="needs_data", values=base | {
                            "outer_iterations": iteration,
                            "provider_request_sha256": provider_request_sha256,
                            "provider_result_sha256": provider_result_sha256,
                            "reason": f"provider_{key}_is_invalid",
                            "fixed_point_history": history,
                        })
                    optional_properties[key] = value
            history_row = {
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "provider_request_sha256": provider_request_sha256,
                "provider_result_sha256": provider_result_sha256,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                "mass_action_input_sha256": solved.values["input_digest"],
                "mass_action_activity_coefficients_molarity_standard_state": gamma.tolist(),
            }
            history.append(history_row)
            if not math.isfinite(log_residual):
                raise ArithmeticError("external activity fixed-point residual is nonfinite")
            if log_residual <= request.log_gamma_tolerance:
                output_species = []
                for index, row in enumerate(solved.values["species"]):
                    output_species.append({
                        **row,
                        "molality_mol_kg_water": float(molality[index]),
                        "ionic_strength_contribution_mol_kg_water": float(
                            0.5 * molality[index] * charges[index] ** 2
                        ),
                        "activity_coefficient_molality_standard_state": float(target_gamma_molality[index]),
                        "activity_coefficient_molarity_standard_state": float(target_gamma_molarity[index]),
                        "activity_coefficient_fixed_point_residual_ln": float(
                            math.log(target_gamma_molarity[index] / gamma[index])
                        ),
                    })
                return Calculation(values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": log_residual,
                    "fixed_point_history": history,
                    "mass_action_input_sha256": solved.values["input_digest"],
                    "mass_action_activity_coefficients_molarity_standard_state": gamma.tolist(),
                    "species": output_species,
                    "constraint_closure": solved.values["constraint_closure"],
                    "reaction_closure": solved.values["reaction_closure"],
                    "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                    "converged": True,
                    "provider_result_sha256": provider_result_sha256,
                    "provider_ionic_strength_mol_kg_water": provider_ionic_strength,
                    "provider_thermodynamic_properties": optional_properties,
                    "aqueous_liquid_only": True,
                }, notes=(
                    "Composition-dependent activity coefficients were supplied by a caller-owned external provider and coupled to the declared mass-action system by a bounded damped fixed-point iteration.",
                    "The provider is not included, invoked through a package dependency, or qualified by this interface; no gas/solid phase, precipitation, kinetics or corrosion rate is inferred.",
                ))
            log_gamma_next = np.log(gamma) + request.damping_fraction * (
                np.log(target_gamma_molarity) - np.log(gamma)
            )
            gamma = np.exp(log_gamma_next)
            if not np.isfinite(gamma).all() or np.any(gamma <= 0.0):
                raise ArithmeticError("damped external activity update is not finite and positive")
    except Exception as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": "external_activity_provider_or_iteration_failed",
            "provider_error_type": type(error).__name__,
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        }, notes=("The external-provider iteration failed closed; no partial or unconverged state is returned.",))
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history),
        "out_of_scope_reason": "external_activity_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history,
        "inner_solver_status": last_solution.status if last_solution is not None else None,
    }, notes=("The declared outer-iteration budget ended before activity coefficients converged; the last iterate is not promoted as a thermodynamic solution.",))
