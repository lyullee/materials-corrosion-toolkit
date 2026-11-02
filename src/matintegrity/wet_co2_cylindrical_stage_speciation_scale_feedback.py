"""Stage-coupled activity-driven scale kinetics in cylindrical BV transport."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .models.aqueous_mass_action import (
    AqueousActivitySpecies,
    AqueousLinearConstraint,
    AqueousMassActionSystem,
    aqueous_mass_action_speciation,
)
from .models.aqueous_activity_iteration import (
    AqueousBdotIteration,
    aqueous_bdot_self_consistent_speciation,
    AqueousDaviesIteration,
    aqueous_davies_self_consistent_speciation,
    AqueousSITIteration,
    aqueous_sit_self_consistent_speciation,
)
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import evaluate_wet_co2_cylindrical_scale_geometry_history
from .wet_co2_cylindrical_spatial_mixed_potential import (
    WetCo2CylindricalSpatialMixedPotential,
    _transport_fluxes,
)
from .wet_co2_cylindrical_transient_transport import (
    FARADAY_C_MOL,
    _cell_volumes_per_axial_metre,
    _edges,
    _remap_species,
)

MODEL_ID = "integration.wet_co2_cylindrical_stage_speciation_scale_feedback"
KINETICS_SOURCE_ID = "caller_mass_action_activities_for_stage_scale_kinetics"
SUPPLY_SOURCE_ID = "multireactant_cylindrical_supply_and_inventory_limiter_at_bdf_stages"
SPECIATION_SOURCE_ID = "aqueous_mass_action_recomputed_from_stage_wall_composition"


class WetCo2StageSpeciationProductTerm(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    exponent: Positive


class WetCo2StageSpeciationKineticPhase(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    species_moles_per_mole_solid: dict[str, float]
    phase_element_composition: dict[str, Positive]
    activity_product_terms: tuple[WetCo2StageSpeciationProductTerm, ...] = Field(min_length=1, max_length=64)
    log_solubility_activity_product: float
    precipitation_rate_constant_mol_m2_s: Nonnegative
    precipitation_log_supersaturation_exponent: Positive
    dissolution_rate_constant_mol_m2_s: Nonnegative
    dissolution_log_undersaturation_exponent: Positive
    maximum_absolute_flux_mol_m2_s: Positive
    kinetic_law_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_law_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    chemistry_and_rate_law_reviewed: bool

    @model_validator(mode="after")
    def bind_law(self):
        if not math.isfinite(self.log_solubility_activity_product):
            raise ValueError("log solubility activity product must be finite")
        if not self.species_moles_per_mole_solid or any(not math.isfinite(v) or v == 0.0
                for v in self.species_moles_per_mole_solid.values()):
            raise ValueError("phase reaction requires finite nonzero signed aqueous stoichiometry")
        if len({row.species_id for row in self.activity_product_terms}) != len(self.activity_product_terms):
            raise ValueError("activity-product species terms must be unique")
        payload = {"phase_id": self.phase_id,
            "species_moles_per_mole_solid": self.species_moles_per_mole_solid,
            "phase_element_composition": self.phase_element_composition,
            "activity_product_terms": [row.model_dump(mode="json") for row in self.activity_product_terms],
            "log_solubility_activity_product": self.log_solubility_activity_product,
            "precipitation_rate_constant_mol_m2_s": self.precipitation_rate_constant_mol_m2_s,
            "precipitation_log_supersaturation_exponent": self.precipitation_log_supersaturation_exponent,
            "dissolution_rate_constant_mol_m2_s": self.dissolution_rate_constant_mol_m2_s,
            "dissolution_log_undersaturation_exponent": self.dissolution_log_undersaturation_exponent,
            "maximum_absolute_flux_mol_m2_s": self.maximum_absolute_flux_mol_m2_s}
        if canonical_digest(payload) != self.kinetic_law_sha256:
            raise ValueError("kinetic-law digest must bind phase, formula, activity terms and all rate parameters")
        if not any(row.sha256 == self.kinetic_law_sha256 and row.license_id for row in self.kinetic_law_evidence):
            raise ValueError("licensed Evidence must pin the complete caller kinetic law")
        return self


class WetCo2StageDaviesActivity(Contract):
    """Optional caller-owned Davies fixed-point configuration for BDF-stage chemistry."""

    water_mass_per_solution_volume_kg_L: Positive
    davies_A_at_temperature: Positive
    parameter_temperature_K: Positive
    temperature_match_tolerance_K: float = Field(default=0.01, ge=0.0, le=5.0)
    davies_A_provider_id: str = Field(min_length=1, max_length=160)
    davies_A_provider_revision: str = Field(min_length=1, max_length=160)
    davies_A_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    davies_A_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    ionic_strength_limit_mol_kg: Positive = Field(le=0.5)
    charge_balance_tolerance_mol_kg: Positive
    maximum_outer_iterations: int = Field(default=30, ge=1, le=100)
    log_gamma_tolerance: Positive = Field(default=1e-8, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    water_mass_conversion_reviewed: bool
    Davies_A_temperature_solvent_basis_reviewed: bool
    molarity_to_molality_standard_state_mapping_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def evidence_binds_temperature_parameter(self):
        if not any(
            row.source_id == self.davies_A_provider_id and row.sha256 == self.davies_A_record_digest
            for row in self.evidence
        ):
            raise ValueError("Davies A provider record digest must match a declared Evidence source")
        return self


class WetCo2StageShearKnot(Contract):
    """Caller-supplied wall shear stress bound to an exact model knot."""

    time_s: Nonnegative
    wall_shear_stress_Pa: Nonnegative
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_shear_record(self):
        payload = {"time_s": self.time_s, "wall_shear_stress_Pa": self.wall_shear_stress_Pa}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("stage shear digest must bind exact knot time and stress")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each caller stage shear knot")
        return self


class WetCo2StageShearDetachmentLaw(Contract):
    """Caller-calibrated phase-specific threshold shear detachment law."""

    phase_id: str = Field(min_length=1, max_length=160)
    critical_shear_stress_Pa: Positive
    detachment_velocity_scale_m_s: Positive
    stress_exponent: Positive
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_law(self):
        payload = {"phase_id": self.phase_id,
                   "critical_shear_stress_Pa": self.critical_shear_stress_Pa,
                   "detachment_velocity_scale_m_s": self.detachment_velocity_scale_m_s,
                   "stress_exponent": self.stress_exponent}
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("stage detachment digest must bind phase, threshold, velocity and exponent")
        if not any(row.sha256 == self.record_sha256 and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin each caller stage detachment law")
        return self


class WetCo2StageShearRemoval(Contract):
    """Opt-in exact-knot wall shear records and caller phase detachment laws."""

    shear_history: tuple[WetCo2StageShearKnot, ...] = Field(min_length=2, max_length=5000)
    phase_laws: tuple[WetCo2StageShearDetachmentLaw, ...] = Field(min_length=1, max_length=32)
    exact_knot_left_hold_reviewed: bool
    detached_solid_export_and_inner_area_reviewed: bool
    phase_law_applicability_reviewed: bool


class WetCo2CylindricalStageSpeciationScaleFeedback(Contract):
    schema_version: Literal[
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v1",
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v2",
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v3",
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v4",
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5",
    ] = (
        "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v2"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_request: WetCo2CylindricalSpatialMixedPotential
    mass_action_system_template: AqueousMassActionSystem
    davies_activity: WetCo2StageDaviesActivity | None = None
    sit_activity: AqueousSITIteration | None = None
    bdot_activity: AqueousBdotIteration | None = None
    shear_removal: WetCo2StageShearRemoval | None = None
    phases: tuple[WetCo2StageSpeciationKineticPhase, ...] = Field(min_length=1, max_length=32)
    maximum_feedback_iterations: int = Field(default=20, ge=1, le=60)
    relaxation_factor: float = Field(default=0.5, gt=0, le=1)
    absolute_radius_tolerance_m: Positive = Field(default=1e-9)
    relative_radius_tolerance: Positive = Field(default=1e-7, le=1e-2)
    absolute_inventory_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_inventory_tolerance: Positive = Field(default=1e-8, le=1e-2)
    maximum_work_units: int = Field(default=30_000_000, ge=10_000, le=300_000_000)
    mass_action_network_and_standard_state_reviewed: bool
    phase_identity_and_balanced_reaction_reviewed: bool
    cylindrical_supply_map_reviewed: bool
    exact_knot_left_hold_and_geometry_reviewed: bool
    no_qualification_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_composition_and_budget(self):
        req = self.spatial_request
        mass_action=self.mass_action_system_template
        if self.davies_activity is not None and self.schema_version == "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v1":
            raise ValueError("stage Davies activity coupling requires schema version v2 or later")
        if self.sit_activity is not None and self.schema_version not in (
            "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v3",
            "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5",
        ):
            raise ValueError("stage SIT activity coupling requires schema version v3 or v5")
        if self.bdot_activity is not None and self.schema_version not in (
            "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v4",
            "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5",
        ):
            raise ValueError("stage B-dot activity coupling requires schema version v4 or v5")
        if self.shear_removal is not None and self.schema_version != "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5":
            raise ValueError("stage shear removal requires schema version v5")
        if self.schema_version == "matintegrity.wet_co2_cylindrical_stage_speciation_scale_feedback.v5" and self.shear_removal is None:
            raise ValueError("schema version v5 requires a caller-bound stage shear-removal configuration")
        if sum(value is not None for value in (self.davies_activity, self.sit_activity, self.bdot_activity)) > 1:
            raise ValueError("select at most one stage activity model")
        if self.sit_activity is not None and canonical_digest(
            self.sit_activity.system.model_dump(mode="json")
        ) != canonical_digest(mass_action.model_dump(mode="json")):
            raise ValueError("stage SIT activity system must exactly match the mass-action template")
        if self.bdot_activity is not None and canonical_digest(
            self.bdot_activity.system.model_dump(mode="json")
        ) != canonical_digest(mass_action.model_dump(mode="json")):
            raise ValueError("stage B-dot activity system must exactly match the mass-action template")
        if req.geometry_trial_mode:
            raise ValueError("stage kinetics requires an ordinary spatial request")
        times = tuple(row.time_s for row in req.knots)
        if times != tuple(row.time_s for row in req.geometry.history):
            raise ValueError("BV and geometry knots must exactly align")
        species = {row.species_id: row for row in req.species}
        ma_species={row.species_id:row for row in mass_action.species}
        if set(species)!=set(ma_species):
            raise ValueError("transport and aqueous mass-action species identities must match exactly")
        if mass_action.activity_standard_state!="molarity_1_mol_L":
            raise ValueError("stage mass action requires the declared molarity standard state")
        if self.davies_activity is not None and abs(
            self.davies_activity.parameter_temperature_K - mass_action.temperature_K
        ) > self.davies_activity.temperature_match_tolerance_K:
            raise ValueError("stage Davies A temperature must match the mass-action temperature support")
        if self.bdot_activity is not None and abs(
            self.bdot_activity.parameter_temperature_K - mass_action.temperature_K
        ) > self.bdot_activity.temperature_match_tolerance_K:
            raise ValueError("stage B-dot parameter temperature must match the mass-action temperature support")
        if self.shear_removal is not None:
            shear = self.shear_removal
            if tuple(row.time_s for row in shear.shear_history) != times:
                raise ValueError("stage wall-shear records must exactly match every transport knot")
            phase_ids = {row.phase_id for row in self.phases}
            law_ids = [row.phase_id for row in shear.phase_laws]
            if len(law_ids) != len(set(law_ids)) or set(law_ids) != phase_ids:
                raise ValueError("stage detachment laws must cover each kinetic phase exactly once")
            if not all((shear.exact_knot_left_hold_reviewed,
                        shear.detached_solid_export_and_inner_area_reviewed,
                        shear.phase_law_applicability_reviewed)):
                raise ValueError("stage shear, detachment export and law applicability review gates must be complete")
        for sid,transport_species in species.items():
            equilibrium_species=ma_species[sid]
            if equilibrium_species.charge_number!=transport_species.charge_number:
                raise ValueError("mass-action and transported charge numbers differ")
            if any(not math.isclose(v,round(v),rel_tol=0.0,abs_tol=1e-12)
                   for v in transport_species.elemental_composition.values()):
                raise ValueError("mass-action schema requires integer formula counts matching transport species")
            transport_formula={e:int(round(v)) for e,v in transport_species.elemental_composition.items()}
            if equilibrium_species.elemental_composition is None or transport_formula!=equilibrium_species.elemental_composition:
                raise ValueError("mass-action and transported elemental formulae must match exactly")
        if not all((mass_action.complete_aqueous_species_inventory_reviewed,
                    mass_action.reaction_stoichiometry_and_constant_reviewed,
                    mass_action.balance_constraints_and_charge_scope_reviewed,
                    mass_action.fixed_activity_coefficients_and_standard_state_reviewed,
                    mass_action.temperature_and_provider_lineage_reviewed,
                    mass_action.initial_activity_guess_and_solver_tolerance_reviewed,
                    mass_action.single_liquid_phase_and_no_precipitation_reviewed,
                    mass_action.elemental_formula_and_reaction_balance_reviewed)):
            raise ValueError("every mass-action chemistry/provider review gate must be complete")
        if any(not math.isclose(knot.reactions[0].temperature_K,mass_action.temperature_K,rel_tol=0.0,abs_tol=1e-8)
               or any(not math.isclose(r.temperature_K,mass_action.temperature_K,rel_tol=0.0,abs_tol=1e-8) for r in knot.reactions)
               for knot in req.knots):
            raise ValueError("mass-action temperature must match every BV exact-knot temperature")
        for constraint in mass_action.constraints:
            if {term.species_id for term in constraint.terms}-set(species):
                raise ValueError("dynamic linear constraints must map to transported aqueous species")
        geometry_phases = {row.phase_id: row for row in req.geometry.phases}
        if len(geometry_phases) != len(req.geometry.phases) or len({p.phase_id for p in self.phases}) != len(self.phases):
            raise ValueError("phase identifiers must be unique")
        if set(geometry_phases) != {p.phase_id for p in self.phases}:
            raise ValueError("kinetic phase set must equal the geometry phase set")
        for phase in self.phases:
            if set(phase.species_moles_per_mole_solid) - set(species):
                raise ValueError("phase reaction species must be present in the spatial aqueous species list")
            term_ids = {row.species_id for row in phase.activity_product_terms}
            if not term_ids <= set(species):
                raise ValueError("activity product terms must refer to declared aqueous species")
            expected_q_terms={sid:coef for sid,coef in phase.species_moles_per_mole_solid.items() if coef>0.0}
            actual_q_terms={row.species_id:row.exponent for row in phase.activity_product_terms}
            if set(actual_q_terms)!=set(expected_q_terms) or any(not math.isclose(actual_q_terms[sid],expected_q_terms[sid],
                    rel_tol=1e-10,abs_tol=1e-10) for sid in expected_q_terms):
                raise ValueError("Q activity terms/exponents must equal positive aqueous reactant stoichiometry")
            reaction_charge = math.fsum(coef*species[sid].charge_number
                for sid,coef in phase.species_moles_per_mole_solid.items())
            if not math.isclose(reaction_charge,0.0,rel_tol=1e-10,abs_tol=1e-10):
                raise ValueError("scale formation/dissolution stoichiometry must be electrically neutral")
            reaction_elements: dict[str,float] = {}
            for sid,coef in phase.species_moles_per_mole_solid.items():
                for element,count in species[sid].elemental_composition.items():
                    reaction_elements[element]=reaction_elements.get(element,0.0)+coef*count
            all_elements=set(reaction_elements)|set(phase.phase_element_composition)
            if any(not math.isclose(reaction_elements.get(e,0.0),phase.phase_element_composition.get(e,0.0),
                    rel_tol=1e-10,abs_tol=1e-10) for e in all_elements):
                raise ValueError("aqueous stoichiometry and solid element formula do not balance")
        nr=len(req.initial_species[0].cell_concentrations_mol_m3)
        reaction_count=max(len(k.reactions) for k in req.knots)
        state_count=(nr*len(species)+3*len(species)+len(req.wall_elements)+reaction_count+
            len(self.phases)+(len(self.phases) if self.shear_removal is not None else 0)+1)
        mass_action_weight=len(mass_action.species)*(mass_action.maximum_iterations+1)*33+3*len(mass_action.species)**3
        activity_iteration_limit = (
            self.davies_activity.maximum_outer_iterations
            if self.davies_activity is not None
            else self.sit_activity.maximum_outer_iterations
            if self.sit_activity is not None
            else self.bdot_activity.maximum_outer_iterations
            if self.bdot_activity is not None
            else 1
        )
        mass_action_weight *= activity_iteration_limit
        rhs_budget=self.maximum_work_units//(self.maximum_feedback_iterations*(len(times)-1)*(state_count+mass_action_weight))
        if rhs_budget<20:
            raise ValueError("work budget leaves fewer than 20 stage evaluations per interval")
        if not req.axisymmetric_reaction_area_and_material_mapping_reviewed or not req.boundary_transport_and_chemistry_reviewed or not req.element_charge_and_reaction_direction_reviewed:
            raise ValueError("underlying BV/spatial review gates must be complete")
        return self


def _solve_stage_mass_action(
    template,
    wall_concentrations_mol_m3,
    activity_guess,
    template_sha256,
    davies_activity=None,
    sit_activity=None,
    bdot_activity=None,
):
    """Re-solve fixed caller chemistry with stage-derived component totals."""
    constraints=[]
    for constraint in template.constraints:
        target=math.fsum(term.coefficient*wall_concentrations_mol_m3[term.species_id]*1e-3
            for term in constraint.terms)
        constraints.append(constraint.model_dump(mode="python")|{"target_mol_L":target})
    stage_sha=canonical_digest({"template_sha256":template_sha256,
        "wall_composition_mol_m3":wall_concentrations_mol_m3,"dynamic_constraints":constraints})
    payload=template.model_dump(mode="python");payload["constraints"]=tuple(constraints)
    for row in payload["species"]:
        row["initial_activity"]=activity_guess.get(row["species_id"],row["initial_activity"])
    try:
        stage_system = AqueousMassActionSystem.model_validate(payload)
        if davies_activity is None:
            if sit_activity is None:
                if bdot_activity is None:
                    result = aqueous_mass_action_speciation(stage_system)
                else:
                    bdot_request = bdot_activity.model_copy(update={"system": stage_system})
                    result = aqueous_bdot_self_consistent_speciation(bdot_request)
            else:
                sit_request = sit_activity.model_copy(update={"system": stage_system})
                result = aqueous_sit_self_consistent_speciation(sit_request)
        else:
            activity_request=AqueousDaviesIteration.model_validate(
                {"system":stage_system,**davies_activity.model_dump(mode="python")}
            )
            result=aqueous_davies_self_consistent_speciation(activity_request)
    except (TypeError,ValueError,OverflowError) as exc:
        raise ArithmeticError(f"stage mass-action input rejected; stage_digest={stage_sha}: {exc}") from exc
    if result.status!="computed":
        reason=result.values.get("out_of_scope_reason",result.values.get("reason",result.status))
        raise ArithmeticError(f"stage mass-action equilibrium did not close; stage_digest={stage_sha}: {reason}")
    rows=result.values.get("species");expected=[row.species_id for row in template.species]
    if not isinstance(rows,list) or [row.get("species_id") for row in rows if isinstance(row,dict)]!=expected:
        raise ArithmeticError("stage mass-action species output identity/order mismatch")
    activities={row["species_id"]:float(row["dimensionless_activity"]) for row in rows}
    if any(not math.isfinite(v) or v<=0.0 for v in activities.values()):
        raise ArithmeticError("stage mass-action returned nonpositive or nonfinite activity")
    concentrations = (
        {row["species_id"]:float(row["concentration_mol_L"]) for row in rows}
        if all("concentration_mol_L" in row for row in rows) else None
    )
    activity_coefficients = (
        {row["species_id"]:float(row["activity_coefficient"]) for row in rows}
        if all("activity_coefficient" in row for row in rows) else None
    )
    if concentrations is not None and any(not math.isfinite(v) or v<0.0 for v in concentrations.values()):
        raise ArithmeticError("stage mass-action returned invalid concentration")
    if activity_coefficients is not None and any(not math.isfinite(v) or v<=0.0 for v in activity_coefficients.values()):
        raise ArithmeticError("stage mass-action returned invalid concentration or activity coefficient")
    return activities,{"input_digest":result.values.get("input_digest"),"stage_wall_composition_sha256":stage_sha,
        "normalized_residual_norm":result.values.get("normalized_residual_norm",result.values.get("inner_normalized_residual_norm")),
        "iterations":result.values.get("iterations",result.values.get("outer_iterations")),
        "activity_model_id": (
            "chemistry.aqueous_davies_self_consistent_speciation"
            if davies_activity is not None
            else "chemistry.aqueous_sit_self_consistent_speciation"
            if sit_activity is not None
            else "chemistry.aqueous_bdot_self_consistent_speciation"
            if bdot_activity is not None
            else "caller_fixed_activity_coefficients"
        ),
        "ionic_strength_mol_kg":result.values.get("ionic_strength_mol_kg"),
        "maximum_log_gamma_fixed_point_residual":result.values.get("maximum_log_gamma_fixed_point_residual"),
        "activity_provider_id": (
            davies_activity.davies_A_provider_id if davies_activity is not None
            else sit_activity.sit_provider_id if sit_activity is not None
            else bdot_activity.parameter_provider_id if bdot_activity is not None
            else template.activity_provider_id
        ),
        "activity_provider_revision": (
            davies_activity.davies_A_provider_revision if davies_activity is not None
            else sit_activity.sit_provider_revision if sit_activity is not None
            else bdot_activity.parameter_provider_revision if bdot_activity is not None
            else template.activity_provider_revision
        ),
        "activity_provider_configuration_digest": (
            bdot_activity.parameter_configuration_sha256 if bdot_activity is not None else None
        ),
        "activity_provider_record_digest": (
            bdot_activity.parameter_record_sha256 if bdot_activity is not None else None
        ),
        **({"concentrations_mol_L_by_species":concentrations} if concentrations is not None else {}),
        **({"activity_coefficients_by_species":activity_coefficients} if activity_coefficients is not None else {}),
        "activities_by_species":activities}


def _activity_log_ratio(phase, activities):
    log_q=0.0
    for term in phase.activity_product_terms:
        activity=activities[term.species_id]
        if not math.isfinite(activity) or activity<=0.0:
            raise ArithmeticError("stage mass-action activity left positive finite support")
        log_q+=term.exponent*math.log(activity)
    return log_q-phase.log_solubility_activity_product


def _bounded_power_rate(constant, driving, exponent, cap):
    if constant<=0.0 or driving<=0.0:
        return 0.0
    log_rate=math.log(constant)+exponent*math.log(driving)
    if log_rate>=math.log(cap):
        return cap
    return math.exp(log_rate)


def _radial_supply(request, knot_index, sid, concentration, radius, edges, boundary):
    nr=len(edges)-1; centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]
    d=boundary.radial_cell_diffusivity_m2_s
    resistance=math.log(centers[0]/radius)/d[0]
    for j in range(1,nr):
        resistance+=math.log(edges[j]/centers[j-1])/d[j-1]+math.log(centers[j]/edges[j])/d[j]
    resistance+=math.log((radius+request.knots[knot_index].solution_film_thickness_m)/centers[-1])/d[-1]
    return max(0.0,boundary.bulk_concentration_mol_m3-concentration)/(radius*resistance)


def _stage_fluxes(request, phases, knot_index, time_s, y, nr, sids, boundaries, edges, radius,
                  interval_end_s, dt, phase_offsets, activities):
    sidx={sid:i for i,sid in enumerate(sids)}
    stage_profiles={sid:y[sidx[sid]*nr:(sidx[sid]+1)*nr] for sid in sids}
    wall_concentrations={sid:max(0.0,float(stage_profiles[sid][0])) for sid in sids}
    raw=[]; saturation=[]
    for p,phase in enumerate(phases):
        log_si=_activity_log_ratio(phase,activities)
        saturation.append(log_si)
        if log_si>0.0:
            rate=_bounded_power_rate(phase.precipitation_rate_constant_mol_m2_s,log_si,
                phase.precipitation_log_supersaturation_exponent,phase.maximum_absolute_flux_mol_m2_s)
        elif log_si<0.0:
            rate=-_bounded_power_rate(phase.dissolution_rate_constant_mol_m2_s,-log_si,
                phase.dissolution_log_undersaturation_exponent,phase.maximum_absolute_flux_mol_m2_s)
        else:
            rate=0.0
        raw.append(max(-phase.maximum_absolute_flux_mol_m2_s,
                       min(phase.maximum_absolute_flux_mol_m2_s,rate)))
    # Cap each phase's dissolution by its live inventory and remaining interval time.
    remaining=max(interval_end_s-time_s,dt*1e-12)
    for p,phase in enumerate(phases):
        inv=max(0.0,float(y[phase_offsets[p]]))
        if raw[p]<0.0:
            raw[p]=max(raw[p],-inv/(2*math.pi*radius*remaining))
    # Apply a joint cylindrical diffusion supply cap for every aqueous reactant consumed
    # by simultaneous precipitation phases.
    for sid in sids:
        demand=math.fsum(max(phase.species_moles_per_mole_solid.get(sid,0.0),0.0)*max(raw[p],0.0)
            for p,phase in enumerate(phases))
        if demand<=0.0: continue
        supply=_radial_supply(request,knot_index,sid,wall_concentrations[sid],radius,edges,boundaries[sid])
        factor=min(1.0,supply/demand)
        for p,phase in enumerate(phases):
            if raw[p]>0 and phase.species_moles_per_mole_solid.get(sid,0.0)>0:
                raw[p]*=factor
    return raw,saturation


def _run_stage_coupled_intervals(
    request,
    mass_action_template,
    phases,
    geometry_states,
    rhs_budget,
    davies_activity=None,
    sit_activity=None,
    bdot_activity=None,
    shear_removal=None,
    *, absolute_inventory_tolerance_mol_m=1e-12, relative_inventory_tolerance=1e-8,
):
    from scipy.integrate import solve_ivp
    species=list(request.species); sids=[s.species_id for s in species]; sidx={sid:i for i,sid in enumerate(sids)}
    nr=len(request.initial_species[0].cell_concentrations_mol_m3); nsp=len(sids); ne=len(request.wall_elements)
    phase_molar_volumes={row.phase_id:row.molar_volume_m3_mol for row in request.geometry.phases}
    profiles={row.species_id:list(row.cell_concentrations_mol_m3) for row in request.initial_species}
    template_sha256=canonical_digest(mass_action_template.model_dump(mode="json"))
    scale0={row.phase_id:row.moles_per_axial_metre_mol_m for row in request.geometry.history[0].phase_inventories}
    phase_inventory={p.phase_id:scale0[p.phase_id] for p in phases}
    metal_release={row.element_id:0.0 for row in request.wall_elements}; intervals=[]; history=[]
    for k,(knot,nxt) in enumerate(zip(request.knots,request.knots[1:],strict=False)):
        dt=nxt.time_s-knot.time_s; radius=float(geometry_states[k]["bore_radius_m"]); area=2*math.pi*radius
        edges=_edges(radius,knot.solution_film_thickness_m,nr); volumes=_cell_volumes_per_axial_metre(edges)
        centers=[math.sqrt(edges[j]*edges[j+1]) for j in range(nr)]
        bound_rows={row.species_id:row for row in knot.species_boundaries}; boundaries={sid:bound_rows[sid] for sid in sids}
        reactions=knot.reactions; nre=len(reactions); np=len(phases); csize=nsp*nr
        off_outer=csize; off_bv=off_outer+nsp; off_scale=off_bv+nsp; off_wall=off_scale+nsp
        off_extent=off_wall+ne; off_charge=off_extent+nre; off_inventory=off_charge+1
        phase_offsets=[off_inventory+p for p in range(np)]
        detachment_offsets=[off_inventory+np+p for p in range(np)] if shear_removal is not None else []
        start_moles={sid:math.fsum(c*v for c,v in zip(profiles[sid],volumes,strict=True)) for sid in sids}
        y0=[profiles[sid][j] for sid in sids for j in range(nr)]+[0.0]*(3*nsp+ne+nre+1)+[phase_inventory[p.phase_id] for p in phases]
        atol=[request.concentration_absolute_tolerance_mol_m3]*csize+[request.inventory_absolute_tolerance_mol_m]*(3*nsp+ne+nre+1+np)
        if shear_removal is not None:
            y0 += [0.0]*np
            atol += [request.inventory_absolute_tolerance_mol_m]*np
        evals=[0]; mass_action_solves=[0]; max_mass_action_residual=[0.0]
        activity_guess={row.species_id:row.initial_activity for row in mass_action_template.species}
        stage_first=[None];stage_last=[None]
        def rhs(time_s,y):
            evals[0]+=1
            if evals[0]>=rhs_budget: raise ArithmeticError("bounded BDF stage-equilibrium work budget exceeded")
            cs=[list(y[p*nr:(p+1)*nr]) for p in range(nsp)]
            if any(not math.isfinite(c) or c < -request.concentration_absolute_tolerance_mol_m3 for row in cs for c in row):
                raise ArithmeticError("aqueous stage concentration became negative or nonfinite")
            potential,bv_rows,_=_transport_fluxes(cs,boundaries,edges,radius,reactions,
                request.potential_absolute_tolerance_V,request.maximum_bisection_iterations)
            wall_composition={sid:max(0.0,float(cs[sidx[sid]][0])) for sid in sids}
            mass_action_solves[0]+=1
            activities,stage_diag=_solve_stage_mass_action(
                mass_action_template,
                wall_composition,
                activity_guess,
                template_sha256,
                davies_activity,
                sit_activity,
                bdot_activity,
            )
            activity_guess.update(activities)
            residual=stage_diag.get("normalized_residual_norm")
            if not isinstance(residual,(int,float)) or not math.isfinite(float(residual)):
                raise ArithmeticError("mass-action stage residual is missing or nonfinite")
            max_mass_action_residual[0]=max(max_mass_action_residual[0],float(residual))
            if stage_first[0] is None:stage_first[0]=stage_diag
            stage_last[0]=stage_diag
            fluxes,log_si=_stage_fluxes(request,phases,k,time_s,y,nr,sids,boundaries,edges,radius,
                nxt.time_s,dt,phase_offsets,activities)
            chemical_fluxes=list(fluxes)
            requested_detachment_fluxes={phase.phase_id:0.0 for phase in phases}
            actual_detachment_fluxes={phase.phase_id:0.0 for phase in phases}
            if shear_removal is not None:
                shear_stress=shear_removal.shear_history[k].wall_shear_stress_Pa
                laws={law.phase_id:law for law in shear_removal.phase_laws}
                remaining=max(nxt.time_s-time_s,dt*1e-12)
                for p,phase in enumerate(phases):
                    law=laws[phase.phase_id]
                    excess=max(0.0,shear_stress/law.critical_shear_stress_Pa-1.0)
                    try:
                        requested_velocity=law.detachment_velocity_scale_m_s*excess**law.stress_exponent
                    except OverflowError as exc:
                        raise ArithmeticError("stage shear detachment velocity exceeded finite support") from exc
                    if not math.isfinite(requested_velocity):
                        raise ArithmeticError("stage shear detachment velocity is nonfinite")
                    requested=requested_velocity/phase_molar_volumes[phase.phase_id]
                    if not math.isfinite(requested):
                        raise ArithmeticError("stage shear detachment flux is nonfinite")
                    available=max(0.0,float(y[phase_offsets[p]]))
                    inventory_limited_rate=available/(2.0*math.pi*radius*remaining)
                    if fluxes[p] < 0.0:
                        inventory_limited_rate=max(0.0,inventory_limited_rate+fluxes[p])
                    actual=min(requested,inventory_limited_rate)
                    requested_detachment_fluxes[phase.phase_id]=requested
                    actual_detachment_fluxes[phase.phase_id]=actual
                    fluxes[p]-=actual
            bv_species={sid:0.0 for sid in sids}; wall={e.element_id:0.0 for e in request.wall_elements}
            extent_rate={r.reaction_id:0.0 for r in reactions}
            for reaction in reactions:
                row=bv_rows[reaction.reaction_id];extent=row["extent_mol_m2_s"]
                extent_rate[reaction.reaction_id]=extent*area
                for sid,coefficient in reaction.stoichiometric_species_coefficients.items():bv_species[sid]+=coefficient*extent*area
                for element in wall:
                    gain=math.fsum(coefficient*species[sidx[sid]].elemental_composition.get(element,0.0)
                        for sid,coefficient in reaction.stoichiometric_species_coefficients.items())
                    if gain>0:wall[element]+=gain*extent*area
            scale_species={sid:0.0 for sid in sids}
            for p,phase in enumerate(phases):
                for sid,coefficient in phase.species_moles_per_mole_solid.items():
                    scale_species[sid]-=coefficient*chemical_fluxes[p]*area
            dy=[0.0]*len(y)
            for pos,sid in enumerate(sids):
                c=cs[pos];d=boundaries[sid].radial_cell_diffusivity_m2_s;balance=[0.0]*nr
                for f in range(1,nr):
                    resistance=math.log(edges[f]/centers[f-1])/d[f-1]+math.log(centers[f]/edges[f])/d[f]
                    flow=2*math.pi/resistance*(c[f-1]-c[f]);balance[f-1]-=flow;balance[f]+=flow
                resistance=math.log(edges[-1]/centers[-1])/d[-1]
                outer_flow=2*math.pi/resistance*(boundaries[sid].bulk_concentration_mol_m3-c[-1])
                balance[-1]+=outer_flow;balance[0]+=bv_species[sid]+scale_species[sid]
                for j in range(nr):dy[pos*nr+j]=balance[j]/volumes[j]
                dy[off_outer+pos]=outer_flow;dy[off_bv+pos]=bv_species[sid];dy[off_scale+pos]=scale_species[sid]
            for p,element in enumerate(wall):dy[off_wall+p]=wall[element]
            for p,reaction in enumerate(reactions):dy[off_extent+p]=extent_rate[reaction.reaction_id]
            dy[off_charge]=-FARADAY_C_MOL*math.fsum(reaction.electron_count*bv_rows[reaction.reaction_id]["extent_mol_m2_s"]*area for reaction in reactions)
            for p in range(np):
                detachment=actual_detachment_fluxes[phases[p].phase_id]
                dy[phase_offsets[p]]=fluxes[p]*area
                if shear_removal is not None:
                    dy[detachment_offsets[p]]=detachment*area
            return dy
        try:
            sol=solve_ivp(rhs,(knot.time_s,nxt.time_s),y0,method="BDF",t_eval=[nxt.time_s],
                rtol=request.relative_tolerance,atol=atol,max_step=min(request.maximum_step_s,dt))
        except (ArithmeticError,ValueError,RuntimeError) as exc:
            return {"failure":{"failed_interval_index":k,"detail":str(exc),"partial_interval_rhs_evaluations":evals[0],
                "rhs_evaluation_budget":rhs_budget,"completed_intervals":intervals},"history":history}
        if not sol.success or sol.y.shape[1]!=1 or sol.t[-1]!=nxt.time_s:
            return {"failure":{"failed_interval_index":k,"detail":str(sol.message),"completed_intervals":intervals},"history":history}
        y=[float(v) for v in sol.y[:,-1]]
        for pos,sid in enumerate(sids):
            values=y[pos*nr:(pos+1)*nr]
            if min(values)<-request.concentration_absolute_tolerance_mol_m3:
                return {"failure":{"failed_interval_index":k,"reason":"negative_aqueous_inventory","species_id":sid,"completed_intervals":intervals},"history":history}
            profiles[sid]=[max(0.0,v) for v in values]
        outer={sid:y[off_outer+p] for p,sid in enumerate(sids)};bv={sid:y[off_bv+p] for p,sid in enumerate(sids)}
        scale={sid:y[off_scale+p] for p,sid in enumerate(sids)}
        inventory={sid:math.fsum(c*v for c,v in zip(profiles[sid],volumes,strict=True)) for sid in sids}
        species_residual={sid:inventory[sid]-start_moles[sid]-outer[sid]-bv[sid]-scale[sid] for sid in sids}
        charge_residual=math.fsum(species[sidx[sid]].charge_number*r for sid,r in species_residual.items())
        elements=sorted({e for sp in species for e in sp.elemental_composition})
        element_residual={e:math.fsum(species[sidx[sid]].elemental_composition.get(e,0.0)*r for sid,r in species_residual.items()) for e in elements}
        electronic=FARADAY_C_MOL*math.fsum(species[sidx[sid]].charge_number*bv[sid] for sid in sids)+y[off_charge]
        phase_inventory_start=dict(phase_inventory)
        if any(abs(r)>absolute_inventory_tolerance_mol_m+relative_inventory_tolerance*max(abs(inventory[sid]),1e-30)
                for sid,r in species_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_species_closure_failed","residual_mol_m_by_species":species_residual,"completed_intervals":intervals},"history":history}
        if abs(electronic)>request.charge_absolute_tolerance_C_m+relative_inventory_tolerance*max(abs(y[off_charge]),1e-30):
            return {"failure":{"failed_interval_index":k,"reason":"bv_electronic_charge_closure_failed","residual_C_m":electronic,"completed_intervals":intervals},"history":history}
        if abs(charge_residual)>(request.charge_absolute_tolerance_C_m/FARADAY_C_MOL+
                relative_inventory_tolerance*max(1e-30,math.fsum(abs(species[sidx[sid]].charge_number*inventory[sid]) for sid in sids))):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_charge_closure_failed","residual_mol_charge_m":charge_residual,"completed_intervals":intervals},"history":history}
        if any(abs(value)>absolute_inventory_tolerance_mol_m+relative_inventory_tolerance*
                max(1e-30,math.fsum(abs(species[sidx[sid]].elemental_composition.get(e,0.0)*inventory[sid]) for sid in sids))
                for e,value in element_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_element_closure_failed","residual_mol_m_by_element":element_residual,"completed_intervals":intervals},"history":history}
        scale_transfer_element={e:math.fsum(species[sidx[sid]].elemental_composition.get(e,0.0)*scale[sid] for sid in sids)
            for e in elements}
        phase_inventory_end={phase.phase_id:y[phase_offsets[p]] for p,phase in enumerate(phases)}
        detached_inventory={phase.phase_id:(float(y[detachment_offsets[p]]) if shear_removal is not None else 0.0)
            for p,phase in enumerate(phases)}
        if any(not math.isfinite(value) or value < -absolute_inventory_tolerance_mol_m
               for value in detached_inventory.values()):
            return {"failure":{"failed_interval_index":k,"reason":"invalid_detached_solid_export_inventory",
                "detached_mol_m_by_phase":detached_inventory,"completed_intervals":intervals},"history":history}
        detached_inventory={phase_id:max(0.0,value) for phase_id,value in detached_inventory.items()}
        solid_element_delta={e:math.fsum((phase_inventory_end[p.phase_id]-phase_inventory_start[p.phase_id])*
            p.phase_element_composition.get(e,0.0) for p in phases) for e in sorted(set(elements)|
            set().union(*(set(p.phase_element_composition) for p in phases)))}
        detached_solid_element_export={e:math.fsum(detached_inventory[p.phase_id]*p.phase_element_composition.get(e,0.0)
            for p in phases) for e in sorted(set(elements)|set().union(*(set(p.phase_element_composition) for p in phases)))}
        solid_aqueous_element_residual={e:scale_transfer_element.get(e,0.0)+solid_element_delta.get(e,0.0)+
            detached_solid_element_export.get(e,0.0)
            for e in sorted(set(scale_transfer_element)|set(solid_element_delta)|set(detached_solid_element_export))}
        if any(abs(v)>absolute_inventory_tolerance_mol_m+relative_inventory_tolerance*
                max(abs(scale_transfer_element.get(e,0.0)),abs(solid_element_delta.get(e,0.0)),
                    abs(detached_solid_element_export.get(e,0.0)),1e-30)
                for e,v in solid_aqueous_element_residual.items()):
            return {"failure":{"failed_interval_index":k,"reason":"aqueous_solid_element_closure_failed",
                "residual_mol_m_by_element":solid_aqueous_element_residual,"completed_intervals":intervals},"history":history}
        endpoint_composition={sid:max(0.0,float(profiles[sid][0])) for sid in sids}
        mass_action_solves[0]+=1
        try:
            endpoint_activities,endpoint_mass_action=_solve_stage_mass_action(
                mass_action_template,
                endpoint_composition,
                activity_guess,
                template_sha256,
                davies_activity,
                sit_activity,
                bdot_activity,
            )
        except ArithmeticError as exc:
            return {"failure":{"failed_interval_index":k,"detail":str(exc),"partial_interval_rhs_evaluations":evals[0],
                "partial_mass_action_solve_count":mass_action_solves[0],"completed_intervals":intervals},"history":history}
        if mass_action_solves[0]>rhs_budget:
            return {"failure":{"failed_interval_index":k,"reason":"mass_action_stage_solve_budget_exceeded",
                "partial_interval_rhs_evaluations":evals[0],"partial_mass_action_solve_count":mass_action_solves[0],
                "completed_intervals":intervals},"history":history}
        max_mass_action_residual[0]=max(max_mass_action_residual[0],float(endpoint_mass_action["normalized_residual_norm"]))
        endpoint_flux,endpoint_log_si=_stage_fluxes(request,phases,k,nxt.time_s,y,nr,sids,boundaries,edges,radius,
            nxt.time_s,dt,phase_offsets,endpoint_activities)
        endpoint_log_si={phase.phase_id:(value if math.isfinite(value) else None)
            for phase,value in zip(phases,endpoint_log_si,strict=True)}
        endpoint_flux={phase.phase_id:value for phase,value in zip(phases,endpoint_flux,strict=True)}
        requested_shear_flux_by_phase={}
        if shear_removal is not None:
            shear_stress=shear_removal.shear_history[k].wall_shear_stress_Pa
            for law in shear_removal.phase_laws:
                excess=max(0.0,shear_stress/law.critical_shear_stress_Pa-1.0)
                velocity=law.detachment_velocity_scale_m_s*excess**law.stress_exponent
                requested_shear_flux_by_phase[law.phase_id]=velocity/phase_molar_volumes[law.phase_id]
            if any(not math.isfinite(value) for value in requested_shear_flux_by_phase.values()):
                return {"failure":{"failed_interval_index":k,"reason":"stage_shear_detachment_flux_nonfinite",
                    "completed_intervals":intervals},"history":history}
        intervals.append({"interval_index":k,"start_time_s":knot.time_s,"end_time_s":nxt.time_s,"geometry_radius_left_m":radius,
            "mass_action_network_constants_held_fixed":True,"stage_equilibrium_recomputed_from_current_wall_composition":True,
            "bv_and_stage_scale_sources_share_bdf_rhs":True,
            "rhs_evaluations":evals[0],"mass_action_stage_solve_count":mass_action_solves[0],
            "mass_action_stage_solve_budget":rhs_budget,"maximum_mass_action_normalized_residual":max_mass_action_residual[0],
            "first_stage_mass_action_digest":stage_first[0]["input_digest"] if stage_first[0] else None,
            "last_stage_mass_action_digest":endpoint_mass_action["input_digest"],
            "first_stage_activity_diagnostics":stage_first[0] if stage_first[0] else None,
            "last_stage_activity_diagnostics":endpoint_mass_action,
            "endpoint_mass_action_activity_by_species":endpoint_activities,
            "first_stage_wall_composition_sha256":stage_first[0]["stage_wall_composition_sha256"] if stage_first[0] else None,
            "last_stage_wall_composition_sha256":endpoint_mass_action["stage_wall_composition_sha256"],
            **({"detached_solid_inventory_export_mol_m_by_phase":detached_inventory,
                "detached_solid_element_export_mol_m_by_element":detached_solid_element_export}
                if shear_removal is not None else {}),
            **({"wall_shear_stress_Pa":shear_removal.shear_history[k].wall_shear_stress_Pa,
                "requested_shear_detachment_flux_mol_m2_s_by_phase":requested_shear_flux_by_phase}
                if shear_removal is not None else {}),
            "time_averaged_scale_flux_mol_m2_s_by_phase":{p.phase_id:(y[phase_offsets[j]]-phase_inventory[p.phase_id])/(area*dt) for j,p in enumerate(phases)},
            "solid_inventory_end_mol_m_by_phase":dict(phase_inventory_end),
            "solid_element_increment_mol_m_by_element":solid_element_delta,
            "endpoint_log_saturation_ratio_by_phase":endpoint_log_si,
            "endpoint_supply_limited_flux_mol_m2_s_by_phase":endpoint_flux,
            "aqueous_outer_exchange_mol_m_by_species":outer,"aqueous_bv_transfer_mol_m_by_species":bv,
            "aqueous_scale_transfer_mol_m_by_species":scale,"aqueous_inventory_residual_mol_m_by_species":species_residual,
            "aqueous_charge_residual_mol_charge_m":charge_residual,"aqueous_element_residual_mol_m_by_element":element_residual,
            "bv_electronic_charge_residual_C_m":electronic,"solid_inventory_start_mol_m_by_phase":phase_inventory_start,
            "aqueous_scale_transfer_element_mol_m_by_element":scale_transfer_element,
            "solid_phase_element_increment_mol_m_by_element":solid_element_delta,
            "scale_aqueous_solid_element_residual_mol_m_by_element":solid_aqueous_element_residual})
        for p,phase in enumerate(phases):
            phase_inventory[phase.phase_id]=y[phase_offsets[p]]
            if phase_inventory[phase.phase_id]<-absolute_inventory_tolerance_mol_m:
                return {"failure":{"failed_interval_index":k,"reason":"solid_inventory_depleted","phase_id":phase.phase_id,"completed_intervals":intervals},"history":history}
            phase_inventory[phase.phase_id]=max(0.0,phase_inventory[phase.phase_id])
        for p,element in enumerate(metal_release):metal_release[element]+=y[off_wall+p]
        next_edges=_edges(float(geometry_states[k+1]["bore_radius_m"]),nxt.solution_film_thickness_m,nr)
        next_boundaries={row.species_id:row for row in nxt.species_boundaries};sweep={}
        for sid in sids:
            profiles[sid],sweep[sid]=_remap_species(edges,next_edges,profiles[sid],next_boundaries[sid].bulk_concentration_mol_m3,next_boundaries[sid].bulk_concentration_mol_m3)
        intervals[-1]["moving_mesh_sweep_by_species"]=sweep
        post_volume=_cell_volumes_per_axial_metre(next_edges)
        post_inventory={sid:math.fsum(c*v for c,v in zip(profiles[sid],post_volume,strict=True)) for sid in sids}
        solid_elements={}
        for phase in phases:
            for element,count in phase.phase_element_composition.items():solid_elements[element]=solid_elements.get(element,0.0)+phase_inventory[phase.phase_id]*count
        history.append({"time_s":nxt.time_s,"species_profile_mol_m3_by_species":{sid:list(v) for sid,v in profiles.items()},
            "aqueous_inventory_after_mesh_remap_mol_m_by_species":post_inventory,
            "phase_inventory_mol_m_by_phase":dict(phase_inventory),"solid_element_inventory_mol_m_by_element":solid_elements,
            "cumulative_wall_release_mol_m_by_element":dict(metal_release)})
    return {"failure":None,"intervals":intervals,"history":history,
        "final_phase_inventory_mol_m_by_phase":phase_inventory,"cumulative_wall_release_mol_m_by_element":metal_release}


def evaluate_wet_co2_cylindrical_stage_speciation_scale_feedback(request: WetCo2CylindricalStageSpeciationScaleFeedback) -> Calculation:
    req=request.spatial_request;input_digest=canonical_digest(request.model_dump(mode="json"))
    base={"assessment_id":request.assessment_id,"model_id":MODEL_ID,"input_sha256":input_digest,
          "spatial_input_sha256":canonical_digest(req.model_dump(mode="json")),
          "mass_action_template_sha256":canonical_digest(request.mass_action_system_template.model_dump(mode="json")),
          "source_ids":[KINETICS_SOURCE_ID,SUPPLY_SOURCE_ID,SPECIATION_SOURCE_ID]
              +(["usgs_phreeqc_davies_activity_coefficients", "usgs_davies_ionic_strength_approximation",
                 "molality_to_molarity_activity_standard_state_bridge"] if request.davies_activity is not None else [])
              +(["nea_thermochemical_database_sit_method", "usgs_phreeqc_sit_model_documentation",
                 "molality_to_molarity_activity_standard_state_bridge"] if request.sit_activity is not None else [])
              +(["usgs_phreeqc_llnl_bdot_activity", "molality_to_molarity_activity_standard_state_bridge"]
                if request.bdot_activity is not None else [])
              +(["caller_wall_shear_history", "caller_calibrated_shear_scale_detachment_law"]
                if request.shear_removal is not None else [])}
    missing=[name for name in ("mass_action_network_and_standard_state_reviewed","phase_identity_and_balanced_reaction_reviewed",
        "cylindrical_supply_map_reviewed","exact_knot_left_hold_and_geometry_reviewed","no_qualification_claim_reviewed",
        "computational_use_authorized") if not getattr(request,name)]
    missing.extend(f"phase:{p.phase_id}:chemistry_and_rate_law_reviewed" for p in request.phases if not p.chemistry_and_rate_law_reviewed)
    if missing:return Calculation(status="needs_data",values=base|{"reason":"review_gates_incomplete","missing_reviews":missing})
    geometry=evaluate_wet_co2_cylindrical_scale_geometry_history(req.geometry)
    if geometry.status!="computed":return Calculation(status=geometry.status,values=base|{"reason":"geometry_not_computed"})
    geom_states=[dict(row) for row in geometry.values["history"]];initial_radii=[float(row["bore_radius_m"]) for row in geom_states]
    nr=len(req.initial_species[0].cell_concentrations_mol_m3);nsp=len(req.species);nint=len(req.knots)-1
    state_count=(nr*nsp+3*nsp+len(req.wall_elements)+max(len(k.reactions) for k in req.knots)+
        len(request.phases)+(len(request.phases) if request.shear_removal is not None else 0)+1)
    ma=request.mass_action_system_template
    mass_action_weight=len(ma.species)*(ma.maximum_iterations+1)*33+3*len(ma.species)**3
    activity_iteration_limit = (
        request.davies_activity.maximum_outer_iterations
        if request.davies_activity is not None
        else request.sit_activity.maximum_outer_iterations
        if request.sit_activity is not None
        else request.bdot_activity.maximum_outer_iterations
        if request.bdot_activity is not None
        else 1
    )
    mass_action_weight *= activity_iteration_limit
    rhs_budget=request.maximum_work_units//(request.maximum_feedback_iterations*nint*(state_count+mass_action_weight))
    iterations=[];final=None;geometry_path=[]
    phase_volumes={p.phase_id:p.molar_volume_m3_mol for p in req.geometry.phases}
    for iteration in range(1,request.maximum_feedback_iterations+1):
        trial=_run_stage_coupled_intervals(
            req,
            ma,
            request.phases,
            geom_states,
            rhs_budget,
            request.davies_activity,
            request.sit_activity,
            request.bdot_activity,
            request.shear_removal,
            absolute_inventory_tolerance_mol_m=request.absolute_inventory_tolerance_mol_m,
            relative_inventory_tolerance=request.relative_inventory_tolerance,
        )
        if trial["failure"]:
            return Calculation(status="out_of_scope",values=base|{"reason":"stage_kinetic_interval_failed","failure_prefix":trial["failure"],
                "completed_iterations":iterations,"failed_iteration":iteration})
        target_radii=[initial_radii[0]]
        geometry_path=[{"time_s":req.knots[0].time_s,"bore_radius_m":initial_radii[0],"steel_inner_radius_m":req.geometry.initial_inner_radius_m,
            "wall_recession_m":0.0,"phase_inventory_mol_m_by_phase":{r.phase_id:r.moles_per_axial_metre_mol_m for r in req.geometry.history[0].phase_inventories},
            "cumulative_wall_release_mol_m_by_element":{e.element_id:0.0 for e in req.wall_elements}}]
        for h in trial["history"]:
            release=h["cumulative_wall_release_mol_m_by_element"]
            mass=math.fsum(release[e.element_id]*e.atomic_molar_mass_kg_mol for e in req.wall_elements)
            steel_r2=req.geometry.initial_inner_radius_m**2+mass/(req.wall_density_kg_m3*math.pi)
            inventory=h["phase_inventory_mol_m_by_phase"]
            annulus=math.fsum(inventory[p]*phase_volumes[p] for p in phase_volumes)/math.pi
            bore_r2=steel_r2-annulus
            if not math.isfinite(bore_r2) or bore_r2<=0:
                return Calculation(status="out_of_scope",values=base|{"reason":"nonpositive_bore_from_stage_speciation_kinetics",
                    "completed_iterations":iterations,"failure_prefix":trial["intervals"]})
            steel_radius=math.sqrt(steel_r2);bore_radius=math.sqrt(bore_r2)
            if steel_radius>=req.geometry.outer_radius_m or bore_radius>steel_radius:
                return Calculation(status="out_of_scope",values=base|{"reason":"stage_speciation_kinetics_exceeds_wall_geometry",
                    "failed_time_s":h["time_s"],"completed_iterations":iterations,"failure_prefix":trial["intervals"]})
            expected={e.element_id:math.pi*(steel_r2-req.geometry.initial_inner_radius_m**2)*req.wall_density_kg_m3*
                e.alloy_mass_fraction/e.atomic_molar_mass_kg_mol for e in req.wall_elements}
            wall_res={e.element_id:expected[e.element_id]-release[e.element_id] for e in req.wall_elements}
            if any(abs(v)>request.absolute_inventory_tolerance_mol_m+request.relative_inventory_tolerance*max(abs(expected[e]),1e-30)
                   for e,v in wall_res.items()):
                return Calculation(status="out_of_scope",values=base|{"reason":"wall_element_geometry_closure_failed",
                    "failed_time_s":h["time_s"],"residual_mol_m_by_element":wall_res,"completed_iterations":iterations,
                    "failure_prefix":trial["intervals"]})
            target_radii.append(bore_radius)
            geometry_path.append({"time_s":h["time_s"],"bore_radius_m":bore_radius,"steel_inner_radius_m":steel_radius,
                "wall_recession_m":steel_radius-req.geometry.initial_inner_radius_m,
                "phase_inventory_mol_m_by_phase":inventory,"solid_element_inventory_mol_m_by_element":h["solid_element_inventory_mol_m_by_element"],
                "cumulative_wall_release_mol_m_by_element":release,"wall_element_geometry_residual_mol_m_by_element":wall_res})
        residual=max(abs(a-b) for a,b in zip(initial_radii,target_radii,strict=True))
        iterations.append({"iteration":iteration,"geometry_radius_residual_m":residual,"geometry_path_m":target_radii,
            "geometry_history_sha256":canonical_digest(geometry_path),"interval_count":nint})
        final=trial
        if residual<=request.absolute_radius_tolerance_m+request.relative_radius_tolerance*max(req.geometry.outer_radius_m,1e-30):break
        relax=request.relaxation_factor
        initial_radii=[(1-relax)*a+relax*b for a,b in zip(initial_radii,target_radii,strict=True)]
        geom_states=[dict(row)|{"bore_radius_m":initial_radii[i]} for i,row in enumerate(geom_states)]
    else:
        return Calculation(status="out_of_scope",values=base|{"reason":"geometry_feedback_not_converged","completed_iterations":iterations,
            "failure_prefix":final["intervals"] if final else []})
    return Calculation(status="computed",values=base|{"iteration_count":len(iterations),"iteration_history":iterations,
        "geometry_history":geometry_path,"geometry_history_sha256":canonical_digest(geometry_path),
        "history":final["history"],"interval_ledger":final["intervals"],
        "final_phase_inventory_mol_m_by_phase":final["final_phase_inventory_mol_m_by_phase"],
        "final_wall_release_mol_m_by_element":final["cumulative_wall_release_mol_m_by_element"],
        **({"shear_removal_lineage":{
            "shear_record_sha256_by_knot":[row.record_sha256 for row in request.shear_removal.shear_history],
            "shear_evidence_source_ids":sorted({row.source_id for knot in request.shear_removal.shear_history
                for row in knot.evidence}),
            "phase_laws":[{"phase_id":law.phase_id,"record_sha256":law.record_sha256,
                "evidence_source_ids":[row.source_id for row in law.evidence]} for law in request.shear_removal.phase_laws]}}
            if request.shear_removal is not None else {}),
        "seed_geometry_result_sha256":canonical_digest(geometry.model_dump(mode="json")),
        "mass_action_lineage":{"template_input_sha256":base["mass_action_template_sha256"],
            "activity_model_id": (
                "chemistry.aqueous_davies_self_consistent_speciation"
                if request.davies_activity is not None
                else "chemistry.aqueous_sit_self_consistent_speciation"
                if request.sit_activity is not None
                else "chemistry.aqueous_bdot_self_consistent_speciation"
                if request.bdot_activity is not None
                else "caller_fixed_activity_coefficients"
            ),
            "activity_provider_id": (
                request.davies_activity.davies_A_provider_id
                if request.davies_activity is not None
                else request.sit_activity.sit_provider_id
                if request.sit_activity is not None
                else request.bdot_activity.parameter_provider_id
                if request.bdot_activity is not None
                else ma.activity_provider_id
            ),
            "activity_provider_revision": (
                request.davies_activity.davies_A_provider_revision
                if request.davies_activity is not None
                else request.sit_activity.sit_provider_revision
                if request.sit_activity is not None
                else request.bdot_activity.parameter_provider_revision
                if request.bdot_activity is not None
                else ma.activity_provider_revision
            ),
            "activity_configuration_digest": (
                request.davies_activity.davies_A_configuration_digest
                if request.davies_activity is not None
                else request.sit_activity.sit_configuration_sha256
                if request.sit_activity is not None
                else request.bdot_activity.parameter_configuration_sha256
                if request.bdot_activity is not None
                else ma.activity_configuration_digest
            ),
            "activity_record_digest": (
                request.davies_activity.davies_A_record_digest
                if request.davies_activity is not None
                else request.sit_activity.sit_record_sha256
                if request.sit_activity is not None
                else request.bdot_activity.parameter_record_sha256
                if request.bdot_activity is not None
                else ma.activity_record_digest
            ),
            "equilibrium_provider_id":ma.equilibrium_provider_id,"equilibrium_provider_revision":ma.equilibrium_provider_revision,
            "equilibrium_configuration_digest":ma.equilibrium_configuration_digest,"equilibrium_record_digest":ma.equilibrium_record_digest,
            "activity_standard_state":ma.activity_standard_state,"temperature_K":ma.temperature_K},
        "phase_lineage":[{"phase_id":p.phase_id,"kinetic_law_sha256":p.kinetic_law_sha256,
            "kinetic_law_evidence_source_ids":[e.source_id for e in p.kinetic_law_evidence],
            "log_solubility_activity_product":p.log_solubility_activity_product} for p in request.phases],
        "model_scope":"caller mass-action topology and constants are fixed; the aqueous equilibrium provider is reevaluated at each BDF stage from wall-cell component totals; activities feed phase saturation kinetics and the resulting source/sink is added to that same BV RHS; phase supply and inventory caps are stage-local; optional caller shear removes phase inventory in the BDF state and exports detached solid without adding it to aqueous species"})


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalStageSpeciationScaleFeedback,
        evaluator=evaluate_wet_co2_cylindrical_stage_speciation_scale_feedback,
        units={
            "time_s[]": "s",
            "geometry_history[].bore_radius_m": "m",
            "geometry_history[].steel_inner_radius_m": "m",
            "history[].phase_inventory_mol_m_by_phase.*": "mol/m",
            "interval_ledger[].detached_solid_inventory_export_mol_m_by_phase.*": "mol/m",
            "interval_ledger[].detached_solid_element_export_mol_m_by_element.*": "mol/m",
            "interval_ledger[].wall_shear_stress_Pa": "Pa",
            "interval_ledger[].requested_shear_detachment_flux_mol_m2_s_by_phase.*": "mol/m^2/s",
            "interval_ledger[].time_averaged_scale_flux_mol_m2_s_by_phase.*": "mol/m^2/s",
            "interval_ledger[].aqueous_inventory_residual_mol_m_by_species.*": "mol/m",
            "interval_ledger[].last_stage_activity_diagnostics.ionic_strength_mol_kg": "mol/kg",
            "interval_ledger[].last_stage_activity_diagnostics.maximum_log_gamma_fixed_point_residual": "1",
            "interval_ledger[].first_stage_activity_diagnostics.concentrations_mol_L_by_species.*": "mol/L",
            "interval_ledger[].last_stage_activity_diagnostics.concentrations_mol_L_by_species.*": "mol/L",
            "interval_ledger[].first_stage_activity_diagnostics.activity_coefficients_by_species.*": "1",
            "interval_ledger[].last_stage_activity_diagnostics.activity_coefficients_by_species.*": "1",
            "shear_removal.shear_history[].time_s": "s",
            "shear_removal.shear_history[].wall_shear_stress_Pa": "Pa",
            "shear_removal.phase_laws[].critical_shear_stress_Pa": "Pa",
            "shear_removal.phase_laws[].detachment_velocity_scale_m_s": "m/s",
        },
        assumptions=(
            "Caller supplies a complete finite aqueous mass-action network, activity and equilibrium provider lineage, reaction formulae, natural-log Ksp and kinetic parameters with bound Evidence.",
            "Optionally, a caller-supplied, evidence-bound Davies A parameter and water-mass conversion are iterated self-consistently with each BDF-stage wall-composition mass-action solve; Davies support and single-liquid limits are enforced.",
            "Alternatively, a caller-supplied, evidence-bound SIT parameter/interaction set can be iterated at each BDF stage; its embedded aqueous template must exactly match the fixed stage-speciation template and only one optional activity model may be selected.",
            "Schema v4 or v5 enables caller-supplied, evidence-bound B-dot parameters at each BDF stage; the embedded aqueous template must exactly match, and activity modes are mutually exclusive.",
            "Schema v5 optionally applies exact-knot caller shear and per-phase evidence-bound threshold detachment within the BDF phase-inventory state; detached solid is recorded as an element export, not returned to the aqueous solution.",
            "Mass-action component constraints are rebuilt from stage wall concentrations and solved in log-activity coordinates at every BDF evaluation.",
            "The caller power law uses the current stage activities; radial supply, phase inventory and common geometry are bounded and updated in the coupled calculation.",
        ),
        source_ids=(KINETICS_SOURCE_ID, SUPPLY_SOURCE_ID, SPECIATION_SOURCE_ID,
            "caller_general_aqueous_mass_action_speciation", "usgs_phreeqc_davies_activity_coefficients",
            "usgs_davies_ionic_strength_approximation", "molality_to_molarity_activity_standard_state_bridge",
            "nea_thermochemical_database_sit_method", "usgs_phreeqc_sit_model_documentation",
            "usgs_phreeqc_llnl_bdot_activity", "caller_wall_shear_history",
            "caller_calibrated_shear_scale_detachment_law"),
        qualification="user_model",
    ),)
