"""Bridge near-wall transient cylindrical species states to one caller scale-kinetics law."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .models.surface_scale_kinetics import (
    CallerSurfaceScaleKinetics,
    caller_surface_scale_kinetics,
)
from .wet_co2_cylindrical_transient_transport import (
    WetCo2CylindricalTransientTransport,
    WetCo2TransientSpecies,
    evaluate_wet_co2_cylindrical_transient_transport,
)
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_cylindrical_wall_saturation_scale_kinetics"
SOURCE_ID = "caller_cylindrical_wall_activity_product_to_scale_kinetics"
TRANSPORT_SOURCE_ID = "caller_cylindrical_transient_species_history_for_wall_saturation"
KINETICS_SOURCE_ID = "caller_surface_scale_kinetics"


class WetCo2CylindricalActivityProductTerm(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    exponent: Positive


class WetCo2CylindricalPhaseActivityKnot(Contract):
    time_s: float = Field(ge=0.0)
    temperature_K: Positive
    activity_standard_state: Literal["molarity_1_mol_L"] = "molarity_1_mol_L"
    log10_solubility_product: float
    equilibrium_solid_id: str = Field(min_length=1, max_length=160)
    activity_coefficients: dict[str, Positive]
    activity_provider_id: str = Field(min_length=1, max_length=160)
    activity_provider_revision: str = Field(min_length=1, max_length=160)
    activity_source_record_id: str = Field(min_length=1, max_length=160)
    activity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_evidence: Evidence
    equilibrium_provider_id: str = Field(min_length=1, max_length=160)
    equilibrium_provider_revision: str = Field(min_length=1, max_length=160)
    equilibrium_source_record_id: str = Field(min_length=1, max_length=160)
    equilibrium_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    equilibrium_evidence: Evidence

    @model_validator(mode="after")
    def bind_activity_and_equilibrium_records(self):
        activity_payload = {
            "time_s": self.time_s,
            "temperature_K": self.temperature_K,
            "activity_standard_state": self.activity_standard_state,
            "activity_coefficients": self.activity_coefficients,
            "provider_id": self.activity_provider_id,
            "provider_revision": self.activity_provider_revision,
            "source_record_id": self.activity_source_record_id,
        }
        equilibrium_payload = {
            "time_s": self.time_s,
            "temperature_K": self.temperature_K,
            "solid_id": self.equilibrium_solid_id,
            "log10_solubility_product": self.log10_solubility_product,
            "provider_id": self.equilibrium_provider_id,
            "provider_revision": self.equilibrium_provider_revision,
            "source_record_id": self.equilibrium_source_record_id,
        }
        if canonical_digest(activity_payload) != self.activity_record_sha256:
            raise ValueError("activity record digest must bind coefficients and exact knot/provider")
        if canonical_digest(equilibrium_payload) != self.equilibrium_record_sha256:
            raise ValueError("equilibrium record digest must bind Ksp and exact knot/provider")
        if (self.activity_evidence.source_id != self.activity_provider_id
                or self.activity_evidence.sha256 != self.activity_record_sha256
                or not self.activity_evidence.license_id):
            raise ValueError("activity Evidence must pin its provider record digest and usage license")
        if (self.equilibrium_evidence.source_id != self.equilibrium_provider_id
                or self.equilibrium_evidence.sha256 != self.equilibrium_record_sha256
                or not self.equilibrium_evidence.license_id):
            raise ValueError("Ksp Evidence must pin its provider record digest and usage license")
        if not math.isfinite(self.log10_solubility_product):
            raise ValueError("log10 solubility product must be finite")
        return self


class WetCo2CylindricalWallSaturationScaleKinetics(Contract):
    """Compute a selected candidate-solid saturation history and caller scale kinetics."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics.v1"] = (
        "matintegrity.wet_co2_cylindrical_wall_saturation_scale_kinetics.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    physical_scope_id: str = Field(min_length=1, max_length=160)
    asset_id: str = Field(min_length=1, max_length=160)
    location_id: str = Field(min_length=1, max_length=160)
    time_basis_id: str = Field(min_length=1, max_length=160)
    transport_request: WetCo2CylindricalTransientTransport
    transport_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_adjacent_cell_index: int = Field(default=0, ge=0, le=199)
    candidate_solid_id: str = Field(min_length=1, max_length=160)
    solid_elemental_composition: dict[str, Positive]
    activity_product_terms: tuple[WetCo2CylindricalActivityProductTerm, ...] = Field(min_length=1, max_length=32)
    dissolution_stoichiometry_provider_id: str = Field(min_length=1, max_length=160)
    dissolution_stoichiometry_provider_revision: str = Field(min_length=1, max_length=160)
    dissolution_stoichiometry_source_record_id: str = Field(min_length=1, max_length=160)
    dissolution_stoichiometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dissolution_stoichiometry_evidence: Evidence
    phase_activity_history: tuple[WetCo2CylindricalPhaseActivityKnot, ...] = Field(min_length=2, max_length=2000)
    kinetics_request: CallerSurfaceScaleKinetics
    linear_saturation_path_interpolation_reviewed: bool
    interval_temperature_mapping_reviewed: bool = False
    cylindrical_wall_state_and_standard_state_reviewed: bool

    @model_validator(mode="after")
    def validate_cross_model_contracts(self):
        if canonical_digest(self.transport_request.model_dump(mode="json")) != self.transport_request_sha256:
            raise ValueError("nested cylindrical transport request digest differs")
        if not self.solid_elemental_composition:
            raise ValueError("candidate solid needs an explicit elemental formula")
        term_ids = [row.species_id for row in self.activity_product_terms]
        if len(term_ids) != len(set(term_ids)):
            raise ValueError("activity-product species IDs must be unique")
        dissolution_payload = {
            "solid_id": self.candidate_solid_id,
            "solid_elemental_composition": self.solid_elemental_composition,
            "activity_product_terms": [row.model_dump(mode="json") for row in self.activity_product_terms],
            "activity_standard_state": "molarity_1_mol_L",
            "provider_id": self.dissolution_stoichiometry_provider_id,
            "provider_revision": self.dissolution_stoichiometry_provider_revision,
            "source_record_id": self.dissolution_stoichiometry_source_record_id,
        }
        if canonical_digest(dissolution_payload) != self.dissolution_stoichiometry_record_sha256:
            raise ValueError("dissolution stoichiometry digest must bind the selected solid and activity product")
        if (self.dissolution_stoichiometry_evidence.source_id != self.dissolution_stoichiometry_provider_id
                or self.dissolution_stoichiometry_evidence.sha256 != self.dissolution_stoichiometry_record_sha256
                or not self.dissolution_stoichiometry_evidence.license_id):
            raise ValueError("stoichiometry Evidence must pin the phase reaction and usage license")
        transport_species = {row.species_id: row for row in self.transport_request.species}
        if not set(term_ids) <= set(transport_species):
            raise ValueError("activity-product terms must refer to declared transient transport species")
        for knot in self.phase_activity_history:
            if set(knot.activity_coefficients) != set(term_ids):
                raise ValueError("each activity knot must supply a coefficient for every product species and no others")
        phase_charge = math.fsum(
            transport_species[row.species_id].charge_number * row.exponent
            for row in self.activity_product_terms
        )
        if not math.isclose(phase_charge, 0.0, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError("neutral solid dissolution product must be charge balanced")
        phase_elements = set(self.solid_elemental_composition)
        term_elements = set().union(*(transport_species[key].elemental_composition for key in term_ids))
        for element in phase_elements | term_elements:
            aqueous_formula = math.fsum(
                row.exponent * transport_species[row.species_id].elemental_composition.get(element, 0.0)
                for row in self.activity_product_terms
            )
            solid_formula = self.solid_elemental_composition.get(element, 0.0)
            if not math.isclose(aqueous_formula, solid_formula, rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(f"candidate dissolution formula is not element balanced for {element}")
        expected_times = tuple(row.time_s for row in self.transport_request.knots)
        actual_times = tuple(row.time_s for row in self.phase_activity_history)
        if actual_times != expected_times:
            raise ValueError("phase activity records must match every transient transport knot exactly and in order")
        if any(row.equilibrium_solid_id != self.candidate_solid_id for row in self.phase_activity_history):
            raise ValueError("each Ksp record must explicitly identify the selected candidate solid")
        if len(self.kinetics_request.intervals) != len(expected_times) - 1:
            raise ValueError("scale kinetics request must span every adjacent cylindrical history knot")
        if tuple(row.start_time_s for row in self.kinetics_request.intervals) != expected_times[:-1] or tuple(
            row.end_time_s for row in self.kinetics_request.intervals
        ) != expected_times[1:]:
            raise ValueError("scale kinetics intervals must match the cylindrical transport clock exactly")
        phase_records = {row.phase_id: row for row in self.transport_request.geometry.phases}
        if self.candidate_solid_id not in phase_records:
            raise ValueError("candidate solid must match a declared phase in the cylindrical geometry record")
        if not math.isclose(self.kinetics_request.scale_molar_volume_m3_mol,
                            phase_records[self.candidate_solid_id].molar_volume_m3_mol,
                            rel_tol=1e-10, abs_tol=1e-15):
            raise ValueError("scale kinetics molar volume must match the selected cylindrical geometry phase")
        if (self.kinetics_request.physical_scope_id != self.physical_scope_id
                or self.transport_request.geometry.asset_id != self.asset_id
                or self.transport_request.geometry.location_id != self.location_id
                or self.transport_request.geometry.time_basis_id != self.time_basis_id):
            raise ValueError("transport geometry and scale kinetics must share the declared physical/time context")
        kinetic_scale_phase = self.kinetics_request.scale_phase_id
        if kinetic_scale_phase != self.candidate_solid_id:
            raise ValueError("selected solid ID must match the caller scale-kinetic phase ID")
        radial_cell_count = len(self.transport_request.initial_species[0].cell_concentrations_mol_m3)
        if self.wall_adjacent_cell_index >= radial_cell_count:
            raise ValueError("selected wall-adjacent radial cell is outside the transient transport grid")
        temperatures = tuple(row.temperature_K for row in self.phase_activity_history)
        if not self.interval_temperature_mapping_reviewed and any(
            value != self.kinetics_request.temperature_K for value in temperatures
        ):
            raise ValueError("temperature changes require explicit knot-to-interval mapping review")
        return self


def evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics(
    request: WetCo2CylindricalWallSaturationScaleKinetics,
) -> Calculation:
    """Compose transient radial transport, explicit activity-product saturation and scale inventory kinetics."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": digest,
        "candidate_solid_id": request.candidate_solid_id,
        "physical_scope_id": request.physical_scope_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis_id": request.time_basis_id,
        "transport_request_sha256": request.transport_request_sha256,
        "activity_standard_state": "molarity_1_mol_L",
        "automatic_speciation_performed": False,
        "phase_discovery_performed": False,
        "feedback_to_cylindrical_transport_performed": False,
    }
    if not request.cylindrical_wall_state_and_standard_state_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "wall_cell_interpretation_and_activity_standard_state_review_required",
        })
    transport = evaluate_wet_co2_cylindrical_transient_transport(request.transport_request)
    if transport.status != "computed":
        return Calculation(status=transport.status, values=base | {
            "reason": "nested_cylindrical_transient_transport_not_computed",
            "transport_result": transport.model_dump(mode="json"),
        })
    transport_digest = canonical_digest(transport.model_dump(mode="json"))
    histories = transport.values["history"]
    terms = tuple(request.activity_product_terms)
    saturation_rows = []
    ratios = []
    for index, (history_row, phase_knot) in enumerate(zip(
        histories, request.phase_activity_history, strict=True
    )):
        concentrations = history_row["cell_concentration_mol_m3_by_species"]
        log_product = 0.0
        zero_product = False
        for term in terms:
            try:
                concentration_mol_l = float(concentrations[term.species_id][request.wall_adjacent_cell_index]) / 1000.0
                gamma = phase_knot.activity_coefficients[term.species_id]
            except (KeyError, IndexError, TypeError, ValueError):
                return Calculation(status="needs_data", values=base | {
                    "reason": "wall_cell_species_or_activity_coefficient_missing",
                    "completed_knot_count": len(saturation_rows),
                    "failed_knot_index": index,
                })
            if not math.isfinite(concentration_mol_l) or concentration_mol_l < 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "wall_cell_concentration_outside_nonnegative_finite_support",
                    "completed_knot_count": len(saturation_rows),
                    "failed_knot_index": index,
                    "species_id": term.species_id,
                })
            if concentration_mol_l == 0.0:
                zero_product = True
            elif not zero_product:
                log_product += term.exponent * (math.log10(gamma) + math.log10(concentration_mol_l))
        log_ratio = -math.inf if zero_product else log_product - phase_knot.log10_solubility_product
        if zero_product:
            ratio = 0.0
        elif not math.isfinite(log_ratio) or not -300.0 <= log_ratio <= 300.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "saturation_ratio_outside_supported_log10_range",
                "completed_knot_count": len(saturation_rows),
                "failed_knot_index": index,
                "log10_saturation_ratio": log_ratio if math.isfinite(log_ratio) else None,
            })
        else:
            ratio = 10.0 ** log_ratio
        if not math.isfinite(ratio):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "saturation_ratio_not_representable",
                "completed_knot_count": len(saturation_rows),
                "failed_knot_index": index,
            })
        ratios.append(ratio)
        saturation_rows.append({
            "time_s": phase_knot.time_s,
            "temperature_K": phase_knot.temperature_K,
            "activity_standard_state": phase_knot.activity_standard_state,
            "wall_adjacent_cell_index": request.wall_adjacent_cell_index,
            "wall_adjacent_cell_concentration_mol_m3_by_species": {
                term.species_id: concentrations[term.species_id][request.wall_adjacent_cell_index]
                for term in terms
            },
            "activity_coefficients": phase_knot.activity_coefficients,
            "log10_ion_activity_product": None if zero_product else log_product,
            "log10_solubility_product": phase_knot.log10_solubility_product,
            "log10_saturation_ratio": None if zero_product else log_ratio,
            "saturation_ratio": ratio,
            "activity_record_sha256": phase_knot.activity_record_sha256,
            "equilibrium_record_sha256": phase_knot.equilibrium_record_sha256,
            "equilibrium_solid_id": phase_knot.equilibrium_solid_id,
        })
    varying = any(left != right for left, right in zip(ratios, ratios[1:]))
    has_constant = any(left == right for left, right in zip(ratios, ratios[1:]))
    if varying and not request.linear_saturation_path_interpolation_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "computed_endpoint_saturation_changes_require_explicit_linear_path_review",
            "saturation_history": saturation_rows,
        })
    if any(not math.isclose(knot.temperature_K, request.kinetics_request.temperature_K, rel_tol=0.0, abs_tol=0.0)
           for knot in request.phase_activity_history) and not request.interval_temperature_mapping_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "varying_temperature_requires_explicit_scale_kinetics_interval_mapping",
            "saturation_history": saturation_rows,
        })
    request_data = request.kinetics_request.model_dump(mode="json")
    interval_rows = []
    for index, interval in enumerate(request.kinetics_request.intervals):
        row = interval.model_dump(mode="json") | {
            "saturation_ratio": ratios[index],
            "saturation_ratio_end": ratios[index + 1],
        }
        if request.interval_temperature_mapping_reviewed:
            row["temperature_K"] = request.phase_activity_history[index].temperature_K
        interval_rows.append(row)
    request_data["intervals"] = interval_rows
    request_data["linearly_varying_saturation_reviewed"] = bool(varying)
    request_data["interval_constant_saturation_reviewed"] = bool(has_constant)
    if request.interval_temperature_mapping_reviewed:
        request_data["interval_temperature_profile_reviewed"] = True
    try:
        bound_kinetics = CallerSurfaceScaleKinetics.model_validate(request_data)
    except (TypeError, ValueError) as exc:
        return Calculation(status="needs_data", values=base | {
            "reason": "computed_cylindrical_saturation_did_not_bind_to_scale_kinetics_contract",
            "validation_detail": str(exc),
            "saturation_history": saturation_rows,
        })
    kinetics = caller_surface_scale_kinetics(bound_kinetics)
    return Calculation(status=kinetics.status, values={
        **base,
        "transport_result_sha256": transport_digest,
        "transport_model_id": transport.values.get("model_id"),
        "transport_geometry_result_sha256": transport.values.get("geometry_result_sha256"),
        "saturation_history": saturation_rows,
        "saturation_history_sha256": canonical_digest(saturation_rows),
        "surface_scale_kinetics": kinetics.model_dump(mode="json"),
        "linear_saturation_path_interpolation_reviewed": request.linear_saturation_path_interpolation_reviewed,
        "interval_temperature_mapping_reviewed": request.interval_temperature_mapping_reviewed,
        "scale_growth_updates_transport_geometry": False,
    }, notes=(
        "Only caller-selected wall-adjacent cell concentrations, caller activity coefficients and a caller Ksp record enter the ion activity product.",
        "The selected saturation path drives a separate caller-calibrated scale inventory law; it does not update the already-computed transport or geometry.",
        "Saturation ratio is a thermodynamic screening quantity under the declared activity convention, not an automatic phase selection or precipitation-rate law.",
        *kinetics.notes,
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalWallSaturationScaleKinetics,
        evaluator=evaluate_wet_co2_cylindrical_wall_saturation_scale_kinetics,
        units={
            "saturation_history[].time_s": "s",
            "saturation_history[].temperature_K": "K",
            "saturation_history[].wall_adjacent_cell_concentration_mol_m3_by_species.*": "mol/m^3",
            "saturation_history[].saturation_ratio": "1",
            "surface_scale_kinetics.values.scale_history[].scale_thickness_m": "m",
        },
        assumptions=(
            "Exact wall-adjacent cylindrical transport concentrations are paired with caller activity coefficients and a caller-supplied log10 Ksp at the same time and temperature knots.",
            "The activity product is calculated using molarity standard state and a caller-declared neutral solid dissolution formula.",
            "A caller-calibrated single-phase scale inventory model receives the exact knot saturation ratios; no coefficient is inferred.",
            "No automatic speciation, phase selection, scale-to-transport feedback or corrosion qualification is performed.",
        ),
        source_ids=(SOURCE_ID, TRANSPORT_SOURCE_ID, KINETICS_SOURCE_ID),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    )]
