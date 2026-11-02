"""Self-consistent aqueous mass action with caller-parameterized extended Debye-Huckel activity."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_activity_iteration import molality_gamma_to_molarity_standard_state
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation


MODEL_ID = "chemistry.aqueous_extended_debye_huckel_self_consistent_speciation"
PARAMETER_SOURCE_ID = "caller_extended_debye_huckel_activity_parameters"
METHOD_SOURCE_ID = "usgs_phreeqc_extended_debye_huckel_method"


class ExtendedDebyeHuckelSpeciesParameter(Contract):
    """Caller-owned ion-size parameter for one mass-action species."""

    species_id: str = Field(min_length=1)
    ion_size_parameter_nm: Positive | None = None
    evidence_source_id: str = Field(min_length=1)
    evidence_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class AqueousExtendedDebyeHuckelIteration(Contract):
    """Close a caller mass-action system against composition-dependent ionic strength.

    A and B are the caller's temperature- and solvent-specific extended
    Debye-Huckel constants. The mass-action core uses a 1 mol/L standard state;
    molality-basis activity coefficients are mapped as gamma_c = gamma_m / w,
    where ``w`` is kilograms of water per litre of solution.
    """

    schema_version: Literal["matintegrity.aqueous_extended_debye_huckel_iteration.v1"] = (
        "matintegrity.aqueous_extended_debye_huckel_iteration.v1"
    )
    system: AqueousMassActionSystem
    water_mass_per_solution_volume_kg_L: Positive
    debye_huckel_A_at_temperature: Positive
    debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm: Positive
    parameter_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0.0, le=5.0)
    parameter_provider_id: str = Field(min_length=1)
    parameter_provider_revision: str = Field(min_length=1)
    parameter_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_supported_ionic_strength_mol_kg: Positive
    charge_balance_tolerance_mol_kg: Positive
    species_parameters: tuple[ExtendedDebyeHuckelSpeciesParameter, ...] = Field(min_length=1, max_length=100)
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    temperature_solvent_parameter_basis_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    species_parameter_completeness_and_applicability_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_parameter_support(self):
        if self.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("extended Debye-Huckel coupling requires the molarity 1 mol/L activity standard state")
        if abs(self.system.temperature_K - self.parameter_temperature_K) > self.temperature_match_tolerance_K:
            raise ValueError("A/B parameters may only be used within the declared temperature tolerance")
        species_ids = tuple(row.species_id for row in self.system.species)
        parameter_ids = tuple(row.species_id for row in self.species_parameters)
        if parameter_ids != species_ids:
            raise ValueError("ion-size parameter rows must exactly match mass-action species order")
        charges = {row.species_id: row.charge_number for row in self.system.species}
        if any(charges[row.species_id] != 0 and (row.ion_size_parameter_nm is None or row.ion_size_parameter_nm <= 0.0)
               for row in self.species_parameters):
            raise ValueError("each charged species requires a positive caller-supplied ion-size parameter")
        evidence_pairs = {(row.source_id, row.sha256) for row in self.evidence}
        if len({row.source_id for row in self.evidence}) != len(self.evidence):
            raise ValueError("Evidence source IDs must be unique")
        if (self.parameter_provider_id, self.parameter_record_sha256) not in evidence_pairs:
            raise ValueError("A/B parameter record must match the declared provider Evidence digest")
        for parameter in self.species_parameters:
            if (parameter.evidence_source_id, parameter.evidence_record_sha256) not in evidence_pairs:
                raise ValueError("every ion-size record must match declared Evidence and SHA-256")
        return self


def aqueous_extended_debye_huckel_self_consistent_speciation(
    request: AqueousExtendedDebyeHuckelIteration,
) -> Calculation:
    """Solve the caller's mass-action system while updating gamma from ionic strength.

    This wrapper does not create species or reactions, choose a phase, infer
    A/B or ion sizes, or add a precipitation or corrosion law.
    """
    system = request.system
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    parameter_sha256 = canonical_digest([row.model_dump(mode="json") for row in request.species_parameters])
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "parameter_temperature_K": request.parameter_temperature_K,
        "water_mass_per_solution_volume_kg_L": request.water_mass_per_solution_volume_kg_L,
        "debye_huckel_A_at_temperature": request.debye_huckel_A_at_temperature,
        "debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm": request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm,
        "parameter_provider_id": request.parameter_provider_id,
        "parameter_provider_revision": request.parameter_provider_revision,
        "parameter_configuration_sha256": request.parameter_configuration_sha256,
        "parameter_record_sha256": request.parameter_record_sha256,
        "species_parameter_sha256": parameter_sha256,
        "maximum_supported_ionic_strength_mol_kg": request.maximum_supported_ionic_strength_mol_kg,
        "maximum_outer_iterations": request.maximum_outer_iterations,
        "log_gamma_tolerance": request.log_gamma_tolerance,
        "damping_fraction": request.damping_fraction,
        "input_sha256": input_sha256,
        "source_evidence": [row.model_dump(mode="json") for row in request.evidence],
        "activity_standard_state": "dimensionless_molarity_1_mol_L",
        "molality_to_molarity_mapping": "gamma_c=gamma_m/w",
    }
    reviews = {
        "water_mass_conversion_reviewed": request.water_mass_conversion_reviewed,
        "molarity_to_molality_standard_state_mapping_reviewed": request.molarity_to_molality_standard_state_mapping_reviewed,
        "temperature_solvent_parameter_basis_reviewed": request.temperature_solvent_parameter_basis_reviewed,
        "complete_inventory_and_charge_scope_reviewed": request.complete_inventory_and_charge_scope_reviewed,
        "species_parameter_completeness_and_applicability_reviewed": request.species_parameter_completeness_and_applicability_reviewed,
        "fixed_point_solver_settings_reviewed": request.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": request.single_liquid_no_precipitation_scope_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0})
    if system.activity_standard_state != "molarity_1_mol_L":
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "unsupported_mass_action_activity_standard_state",
            "outer_iterations": 0,
        })

    charges = np.asarray([row.charge_number for row in system.species], dtype=float)
    ion_sizes = [row.ion_size_parameter_nm for row in request.species_parameters]
    gamma_c = np.asarray([row.activity_coefficient for row in system.species], dtype=float)
    history: list[dict[str, float | int]] = []
    last_solution = None
    try:
        for iteration in range(1, request.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(
                    row.model_copy(update={"activity_coefficient": float(gamma_c[index])})
                    for index, row in enumerate(system.species)
                ),
                "activity_provider_id": request.parameter_provider_id,
                "activity_provider_revision": request.parameter_provider_revision,
                "activity_configuration_digest": request.parameter_configuration_sha256,
                "activity_record_digest": request.parameter_record_sha256,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(status=solved.status, values=base | {
                    "outer_iterations": iteration,
                    "fixed_point_history": history,
                    "inner_solver_status": solved.status,
                    "inner_solver_values": solved.values,
                }, notes=("The fixed-activity mass-action subproblem did not converge; no outer equilibrium is reported.", *solved.notes))

            concentration = np.asarray([row["concentration_mol_L"] for row in solved.values["species"]], dtype=float)
            molality = concentration / request.water_mass_per_solution_volume_kg_L
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > request.maximum_supported_ionic_strength_mol_kg:
                return Calculation(status="out_of_scope", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "out_of_scope_reason": "ionic_strength_exceeds_caller_parameter_support",
                    "fixed_point_history": history,
                })
            if not math.isfinite(charge_residual) or abs(charge_residual) > request.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "speciation_charge_balance_tolerance_exceeded",
                    "fixed_point_history": history,
                })

            root_strength = math.sqrt(ionic_strength)
            target_log10_gamma_m = np.zeros(len(system.species), dtype=float)
            for index, species in enumerate(system.species):
                if species.charge_number == 0:
                    continue
                size_nm = ion_sizes[index]
                if size_nm is None:
                    raise ArithmeticError("charged species lacks its checked ion-size parameter")
                denominator = 1.0 + request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm * size_nm * root_strength
                if not math.isfinite(denominator) or denominator <= 0.0:
                    raise ArithmeticError("extended Debye-Huckel denominator is unsupported")
                target_log10_gamma_m[index] = (
                    -request.debye_huckel_A_at_temperature * species.charge_number**2 * root_strength / denominator
                )
            target_log_gamma_m = target_log10_gamma_m * math.log(10.0)
            lower_log = math.log(np.nextafter(0.0, 1.0))
            upper_log = math.log(np.finfo(float).max)
            if np.any(target_log_gamma_m < lower_log) or np.any(target_log_gamma_m > upper_log):
                raise ArithmeticError("extended Debye-Huckel coefficient is outside finite binary64 support")
            target_gamma_m = np.exp(target_log_gamma_m)
            target_gamma_c = molality_gamma_to_molarity_standard_state(
                target_gamma_m, request.water_mass_per_solution_volume_kg_L
            )
            log_residual = float(np.max(np.abs(np.log(target_gamma_c) - np.log(gamma_c))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
            })
            if not math.isfinite(log_residual):
                raise ArithmeticError("activity fixed-point residual is not finite")
            if log_residual <= request.log_gamma_tolerance:
                target_species = []
                for index, row in enumerate(solved.values["species"]):
                    target_species.append({
                        **row,
                        "molality_mol_kg": float(molality[index]),
                        "ionic_strength_contribution_mol_kg": float(0.5 * molality[index] * charges[index] ** 2),
                        "ion_size_parameter_nm": ion_sizes[index],
                        "target_log10_gamma_molality": float(target_log10_gamma_m[index]),
                        "target_gamma_molality": float(target_gamma_m[index]),
                        "target_gamma_molarity_standard_state": float(target_gamma_c[index]),
                        "activity_coefficient_fixed_point_residual_ln": float(math.log(target_gamma_c[index] / gamma_c[index])),
                    })
                return Calculation(values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": log_residual,
                    "fixed_point_history": history,
                    "species": target_species,
                    "constraint_closure": solved.values["constraint_closure"],
                    "reaction_closure": solved.values["reaction_closure"],
                    "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                    "converged": True,
                    "aqueous_liquid_only": True,
                }, notes=(
                    "Caller-defined aqueous mass action is iterated with the extended Debye-Huckel expression and caller-supplied ionic inventory, A/B coefficients and ion sizes.",
                    "The calculation is limited to one liquid phase and declared parameter support; no species, reactions, phases, kinetic laws or corrosion rates are inferred.",
                ))
            gamma_c = np.exp(np.log(gamma_c) + request.damping_fraction * (np.log(target_gamma_c) - np.log(gamma_c)))
            if np.any(~np.isfinite(gamma_c)) or np.any(gamma_c <= 0.0):
                raise ArithmeticError("damped activity update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": str(error),
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        }, notes=("An unsupported or non-finite state occurred; no unconverged partial composition is promoted as equilibrium.",))
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history),
        "out_of_scope_reason": "extended_debye_huckel_activity_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history,
        "inner_solver_status": last_solution.status if last_solution is not None else None,
    }, notes=("The declared outer-iteration budget ended before the activity fixed point converged; no partial composition is returned.",))


def build_extended_debye_huckel_transport_activity_callback(
    request: AqueousExtendedDebyeHuckelIteration,
    *,
    transport_species_ids: tuple[str, ...],
    temperature_K: float,
):
    """Build a digest-bound gamma-m callback for a caller-owned transport solve.

    The callback evaluates the declared expression at each supplied spatial
    composition. It does not solve local speciation or alter transport fluxes.
    """
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the reviewed mass-action species order")
    if not math.isfinite(float(temperature_K)) or abs(
        float(temperature_K) - request.system.temperature_K
    ) > request.temperature_match_tolerance_K:
        raise ValueError("transport temperature is outside the exact reviewed A/B parameter support")
    required_reviews = (
        request.water_mass_conversion_reviewed,
        request.molarity_to_molality_standard_state_mapping_reviewed,
        request.temperature_solvent_parameter_basis_reviewed,
        request.complete_inventory_and_charge_scope_reviewed,
        request.species_parameter_completeness_and_applicability_reviewed,
        request.single_liquid_no_precipitation_scope_reviewed,
    )
    if not all(required_reviews):
        raise ValueError("all water-mass, species, parameter-support and single-liquid reviews are required")
    species = request.system.species
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    ion_sizes = [row.ion_size_parameter_nm for row in request.species_parameters]
    evidence_digest = canonical_digest([row.model_dump(mode="json") for row in request.evidence])
    parameter_rows = [row.model_dump(mode="json") for row in request.species_parameters]
    request_digest = canonical_digest(request.model_dump(mode="json"))
    water_mass = float(request.water_mass_per_solution_volume_kg_L)

    def activity_coefficients(time_s: float, concentration_mol_m3):
        if not math.isfinite(float(time_s)) or time_s < 0.0:
            raise ValueError("transport time must be finite and nonnegative")
        concentration = np.asarray(concentration_mol_m3, dtype=float)
        if concentration.ndim != 2 or concentration.shape[0] != len(species) or concentration.shape[1] < 1:
            raise ValueError("transport concentration matrix must be species-by-location in exact declared order")
        if not np.isfinite(concentration).all() or np.any(concentration < 0.0):
            raise ValueError("transport concentrations must be finite and nonnegative")
        molality = concentration / 1000.0 / water_mass
        ionic_strength = 0.5 * np.sum(molality * np.square(charges)[:, None], axis=0)
        charge_residual = np.sum(molality * charges[:, None], axis=0)
        if not np.isfinite(ionic_strength).all() or np.any(
            ionic_strength > request.maximum_supported_ionic_strength_mol_kg
        ):
            raise ValueError("a local transport composition exceeds caller-declared ionic-strength support")
        if not np.isfinite(charge_residual).all() or np.any(
            np.abs(charge_residual) > request.charge_balance_tolerance_mol_kg
        ):
            raise ValueError("a local transport composition exceeds the caller charge-balance tolerance")
        root_strength = np.sqrt(ionic_strength)
        result = np.ones_like(molality)
        for index, item in enumerate(species):
            if item.charge_number == 0:
                continue
            size_nm = ion_sizes[index]
            if size_nm is None:
                raise ValueError("a charged transport species has no validated ion-size parameter")
            denominator = 1.0 + request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm * size_nm * root_strength
            if not np.isfinite(denominator).all() or np.any(denominator <= 0.0):
                raise ValueError("a local extended Debye-Huckel denominator is unsupported")
            log10_gamma = (
                -request.debye_huckel_A_at_temperature * item.charge_number**2 * root_strength / denominator
            )
            log_gamma = log10_gamma * math.log(10.0)
            if not np.isfinite(log_gamma).all() or np.any(log_gamma < math.log(np.nextafter(0.0, 1.0))):
                raise ValueError("a local extended Debye-Huckel coefficient is outside finite binary64 support")
            result[index] = np.exp(log_gamma)
        if not np.isfinite(result).all() or np.any(result <= 0.0):
            raise ValueError("transport activity coefficients must be finite and positive")
        return result

    activity_coefficients.provider_id = request.parameter_provider_id
    activity_coefficients.provider_revision = request.parameter_provider_revision
    activity_coefficients.configuration_sha256 = canonical_digest({
        "adapter": "matintegrity.extended_debye_huckel_transport_activity_callback.v1",
        "request_sha256": request_digest,
        "parameter_configuration_sha256": request.parameter_configuration_sha256,
        "parameter_record_sha256": request.parameter_record_sha256,
        "species_parameter_sha256": canonical_digest(parameter_rows),
        "species_ids": list(expected_species),
        "temperature_K": float(temperature_K),
        "concentration_unit": "mol/m3",
        "returned_coefficient_basis": "molality_relative_to_1_mol_per_kg_water",
    })
    activity_coefficients.record_sha256 = request.parameter_record_sha256
    activity_coefficients.source_request_sha256 = request_digest
    activity_coefficients.activity_standard_state = "molality_relative_to_1_mol_per_kg_water"
    activity_coefficients.species_ids = expected_species
    activity_coefficients.temperature_K = float(temperature_K)
    activity_coefficients.parameter_sha256 = canonical_digest(parameter_rows)
    activity_coefficients.evidence_sha256 = evidence_digest
    activity_coefficients.water_mass_per_solution_volume_kg_L = water_mass
    activity_coefficients.debye_huckel_A_at_temperature = float(request.debye_huckel_A_at_temperature)
    activity_coefficients.debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm = float(
        request.debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm
    )
    return activity_coefficients


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            AqueousExtendedDebyeHuckelIteration,
            aqueous_extended_debye_huckel_self_consistent_speciation,
            {
                "ionic_strength_mol_kg": "mol/kg",
                "charge_balance_residual_mol_kg": "mol/kg",
                "water_mass_per_solution_volume_kg_L": "kg/L",
                "species.activity_coefficient": "1",
                "species.target_gamma_molality": "1",
                "species.target_gamma_molarity_standard_state": "1",
                "species.concentration_mol_L": "mol/L",
                "species.molality_mol_kg": "mol/kg",
                "maximum_log_gamma_fixed_point_residual": "1",
                "inner_normalized_residual_norm": "1",
                "outer_iterations": "1",
            },
            (
                "Caller-defined square mass-action constraints are solved repeatedly while extended Debye-Huckel gamma is updated from speciation-derived ionic strength.",
                "A, B, ion-size records, parameter support, water-mass conversion, standard-state mapping and all reaction/equilibrium data are caller-supplied and Evidence-bound.",
                "Requires a complete reviewed ionic inventory, acceptable charge closure and a single aqueous liquid phase without precipitation.",
                "Does not generate reactions or species, select phases, model precipitation kinetics, estimate corrosion or establish material qualification.",
            ),
            (
                "caller_general_aqueous_mass_action_speciation",
                PARAMETER_SOURCE_ID,
                METHOD_SOURCE_ID,
                "molality_to_molarity_activity_standard_state_bridge",
            ),
            qualification="user_model",
        )
    ]
