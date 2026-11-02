"""Sequential spatial handoff from activity transport and caller solid kinetics to aperture."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_activity_corrected_transport import (
    CreviceActivityReactiveTransportRequest,
    REACTIVE_MODEL_ID,
)
from .multiphase_kinetic_transport import CompetingSolidKineticTransport
from .registry import ModelSpec

MODEL_ID = "integration.crevice_activity_transport_spatial_phase_aperture_handoff"
SOURCE_IDS = (
    "caller_activity_corrected_reactive_transport_history",
    "caller_cellwise_competing_solid_kinetic_rate_campaign",
    "caller_solid_molar_volume_and_deposition_coverage",
    "sequential_finite_volume_phase_inventory_to_slit_aperture_handoff",
)
MAX_CELL_KNOT_PHASE_RECORDS = 2_000_000


class CreviceActivityTransportPhaseApertureRequest(Contract):
    schema_version: Literal["matintegrity.crevice_activity_transport_phase_aperture.v1"] = (
        "matintegrity.crevice_activity_transport_phase_aperture.v1"
    )
    assessment_id: str = Field(min_length=1)
    activity_transport_request: CreviceActivityReactiveTransportRequest
    activity_transport_result: dict
    activity_transport_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solid_kinetic_campaign: CompetingSolidKineticTransport
    initial_aperture_m_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    cell_length_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    transverse_width_m: Positive
    deposition_side_count: Literal[1, 2]
    coverage_fraction_by_cell: tuple[float, ...] = Field(min_length=2, max_length=2000)
    solid_molar_volume_m3_mol_by_phase: dict[str, Positive]
    molar_volume_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    molar_volume_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    absolute_inventory_balance_tolerance_mol_m3: Positive = 1e-10
    relative_inventory_balance_tolerance: float = Field(default=1e-9, gt=0.0, le=0.01)
    absolute_charge_balance_tolerance_mol_eq_m3: Positive = 1e-10
    relative_charge_balance_tolerance: float = Field(default=1e-7, gt=0.0, le=0.01)
    geometry_match_relative_tolerance: float = Field(default=1e-10, gt=0.0, le=1e-5)
    fixed_uniform_initial_geometry_reviewed: bool
    activity_and_kinetic_species_mapping_reviewed: bool
    rate_campaign_is_interval_extent_rate_basis_reviewed: bool
    phase_volume_coverage_and_side_partition_reviewed: bool
    sequential_split_and_next_segment_only_reviewed: bool
    no_morphology_or_local_pit_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_lineage_and_geometry(self):
        if canonical_digest(self.activity_transport_result) != self.activity_transport_result_sha256:
            raise ValueError("activity transport result digest mismatch")
        if canonical_digest(self.solid_molar_volume_m3_mol_by_phase) != self.molar_volume_record_sha256:
            raise ValueError("molar-volume record digest mismatch")
        if not any(row.sha256 == self.molar_volume_record_sha256 for row in self.molar_volume_evidence):
            raise ValueError("molar-volume Evidence must pin the complete phase mapping")
        if not all((self.fixed_uniform_initial_geometry_reviewed,
                    self.activity_and_kinetic_species_mapping_reviewed,
                    self.rate_campaign_is_interval_extent_rate_basis_reviewed,
                    self.phase_volume_coverage_and_side_partition_reviewed,
                    self.sequential_split_and_next_segment_only_reviewed,
                    self.no_morphology_or_local_pit_claim_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all source mapping, split-order, geometry and use reviews are required")

        transport = self.activity_transport_request
        campaign = self.solid_kinetic_campaign
        kinetic_transport = campaign.transport
        count = transport.cell_count
        if count != len(self.initial_aperture_m_by_cell) or count != len(self.cell_length_m) or count != len(self.coverage_fraction_by_cell):
            raise ValueError("geometry arrays must exactly match transport cell count")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.coverage_fraction_by_cell):
            raise ValueError("cell coverage fractions must lie in [0, 1]")
        if len(self.solid_kinetic_campaign.kinetic_intervals) != len(transport.output_time_s) - 1:
            raise ValueError("this handoff requires one explicit kinetic rate interval per transport segment")
        if campaign.phase_rate_laws:
            raise ValueError("this handoff consumes explicit interval rates only; callbacks are not executed")
        if campaign.transport.cell_count != count or campaign.transport.length_m != transport.length_m:
            raise ValueError("kinetic campaign and activity transport geometry dimensions differ")
        if campaign.transport.output_times_s != transport.output_time_s:
            raise ValueError("kinetic and activity transport clocks must match exactly")
        if campaign.transport.species_ids != tuple(row.species_id for row in transport.species):
            raise ValueError("kinetic and activity transport species order must match exactly")
        if campaign.kinetic_intervals[0].start_time_s != transport.output_time_s[0]:
            raise ValueError("first kinetic interval does not start at activity transport clock origin")
        if kinetic_transport.cell_widths_m is not None and kinetic_transport.cell_widths_m != self.cell_length_m:
            raise ValueError("kinetic campaign cell widths must match the declared geometry exactly")
        if any(not math.isclose(value, self.cell_length_m[0], rel_tol=0.0, abs_tol=0.0)
               for value in self.cell_length_m[1:]) or not math.isclose(
            math.fsum(self.cell_length_m), transport.length_m,
            rel_tol=self.geometry_match_relative_tolerance,
            abs_tol=self.geometry_match_relative_tolerance * max(transport.length_m, 1e-30),
        ):
            raise ValueError("activity transport's uniform cells require equal cell lengths spanning the declared slit")
        if any(not math.isclose(value, self.initial_aperture_m_by_cell[0],
                               rel_tol=self.geometry_match_relative_tolerance,
                               abs_tol=self.geometry_match_relative_tolerance * max(self.initial_aperture_m_by_cell[0], 1e-30))
               for value in self.initial_aperture_m_by_cell[1:]):
            raise ValueError("the activity transport API has one cross-section; initial aperture must be uniform")
        expected_area = self.initial_aperture_m_by_cell[0] * self.transverse_width_m
        if not math.isclose(transport.cross_section_area_m2, expected_area,
                            rel_tol=self.geometry_match_relative_tolerance,
                            abs_tol=self.geometry_match_relative_tolerance * max(expected_area, 1e-30)):
            raise ValueError("initial slit aperture × transverse width must match activity transport cross section")
        if kinetic_transport.reference_cross_section_m2 is None:
            raise ValueError("kinetic campaign requires an explicit reference cross-section for geometry matching")
        if not math.isclose(
            kinetic_transport.reference_cross_section_m2, transport.cross_section_area_m2,
            rel_tol=self.geometry_match_relative_tolerance,
            abs_tol=self.geometry_match_relative_tolerance * max(transport.cross_section_area_m2, 1e-30),
        ):
            raise ValueError("kinetic campaign reference cross-section differs from activity transport")
        if kinetic_transport.cell_cross_section_m2 is not None and any(
            not math.isclose(area, transport.cross_section_area_m2,
                             rel_tol=self.geometry_match_relative_tolerance,
                             abs_tol=self.geometry_match_relative_tolerance * max(transport.cross_section_area_m2, 1e-30))
            for area in kinetic_transport.cell_cross_section_m2
        ):
            raise ValueError("kinetic campaign cell cross-sections must equal the fixed activity transport area")
        species = {row.species_id: row for row in transport.species}
        kinetic_species = {row.species_id: row for row in campaign.aqueous_species}
        if set(species) != set(kinetic_species):
            raise ValueError("kinetic and activity transport aqueous species sets must match")
        for species_id, row in species.items():
            kinetic_row = kinetic_species[species_id]
            if row.charge_number != kinetic_row.charge_number or row.elemental_composition != kinetic_row.elemental_composition:
                raise ValueError("kinetic species charge/elements differ from activity transport species")
            if tuple(row.initial_cell_concentration_mol_m3) != tuple(
                kinetic_transport.initial_concentration_mol_m3[kinetic_transport.species_ids.index(species_id)]
            ):
                raise ValueError("kinetic and activity transport initial cell concentrations must match exactly")
        phase_ids = {row.solid_species_id for row in campaign.candidate_solid_phases}
        if set(self.solid_molar_volume_m3_mol_by_phase) != phase_ids:
            raise ValueError("molar-volume mapping must cover every and only declared solid phase")
        if count * len(transport.output_time_s) * len(phase_ids) > MAX_CELL_KNOT_PHASE_RECORDS:
            raise ValueError("cell × time × phase output budget exceeded")
        result = self.activity_transport_result
        values = result.get("values") if isinstance(result.get("values"), dict) else result
        if result.get("status") != "computed" or not isinstance(values, dict):
            raise ValueError("a computed activity-corrected reactive transport result is required")
        if values.get("model_id") != REACTIVE_MODEL_ID:
            raise ValueError("upstream result is not the activity-corrected reactive transport model")
        if values.get("input_sha256") != canonical_digest(transport.model_dump(mode="json")):
            raise ValueError("activity transport result is not bound to the typed request")
        if (values.get("asset_id") != transport.asset_id
                or values.get("physical_scope_id") != transport.physical_scope_id
                or values.get("clock_id") != transport.clock_id):
            raise ValueError("activity transport result scope/clock lineage differs")
        if len(values.get("state_history", ())) != len(transport.output_time_s):
            raise ValueError("activity transport result knot count differs from request")
        history = values["state_history"]
        for index, (state, expected_time) in enumerate(zip(history, transport.output_time_s, strict=True)):
            if not isinstance(state, dict) or state.get("time_s") != expected_time:
                raise ValueError("activity transport state history must match every requested exact time")
            state_concentrations = state.get("species_concentration_mol_m3_by_id")
            if not isinstance(state_concentrations, dict) or set(state_concentrations) != set(species):
                raise ValueError("activity transport result species mapping differs from its typed request")
            for species_id, row in state_concentrations.items():
                if (not isinstance(row, list) or len(row) != count
                        or any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0
                               for value in row)):
                    raise ValueError(f"upstream concentration field {species_id!r} is invalid at knot {index}")
            charge_vector = state.get("local_charge_residual_mol_eq_m3_by_cell")
            if not isinstance(charge_vector, list) or len(charge_vector) != count:
                raise ValueError("activity transport local charge diagnostics must align with cells")
            for cell, charge in enumerate(charge_vector):
                charge_scale = math.fsum(abs(species_row.charge_number) * state_concentrations[species_id][cell]
                                          for species_id, species_row in species.items())
                allowed_charge = (self.absolute_charge_balance_tolerance_mol_eq_m3
                                  + self.relative_charge_balance_tolerance * max(charge_scale, 1e-30))
                if not math.isfinite(charge) or abs(charge) > allowed_charge:
                    raise ValueError("upstream activity transport local charge residual exceeds mapped tolerance")
        balance = values.get("finite_volume_inventory_balance_residual_mol_by_species")
        if not isinstance(balance, dict) or set(balance) != set(species):
            raise ValueError("activity transport finite-volume inventory residuals are required")
        full_volume = transport.cross_section_area_m2 * transport.length_m
        for species_id, residuals in balance.items():
            if not isinstance(residuals, list) or len(residuals) != len(transport.output_time_s):
                raise ValueError("upstream inventory residuals must align with every time knot")
            concentrations = [row["species_concentration_mol_m3_by_id"][species_id] for row in history]
            cell_volume = transport.cross_section_area_m2 * self.cell_length_m[0]
            scale = max(cell_volume * math.fsum(concentration) for concentration in concentrations)
            allowed = transport.absolute_tolerance_mol_m3 * full_volume + transport.relative_tolerance * max(scale, 1e-30)
            if any(not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > allowed
                   for value in residuals):
                raise ValueError("upstream finite-volume species inventory residual exceeds its declared tolerance")
        if len(campaign.kinetic_intervals) != len(transport.output_time_s) - 1:
            raise ValueError("explicit kinetic rates must span every adjacent activity transport knot")
        return self


def _unwrap_result(result: dict) -> dict:
    values = result.get("values")
    return values if isinstance(values, dict) else result


def evaluate_crevice_activity_transport_phase_aperture(
    request: CreviceActivityTransportPhaseApertureRequest,
) -> Calculation:
    """Apply cellwise solid extents to an activity-transport segment and return next-segment gaps."""
    digest = canonical_digest(request.model_dump(mode="json"))
    transport = request.activity_transport_request
    campaign = request.solid_kinetic_campaign
    result = _unwrap_result(request.activity_transport_result)
    cell_count = transport.cell_count
    phase_ids = tuple(row.solid_species_id for row in campaign.candidate_solid_phases)
    phase_by_id = {row.solid_species_id: row for row in campaign.candidate_solid_phases}
    species_by_id = {row.species_id: row for row in transport.species}
    times = transport.output_time_s
    dx = transport.length_m / cell_count
    liquid_cell_volume = transport.cross_section_area_m2 * dx
    plan_area = request.transverse_width_m * dx
    concentrations_by_phase = {
        phase_id: list(campaign.initial_solid_inventory_mol_m3_by_phase[phase_id])
        for phase_id in phase_ids
    }
    phase_history = []
    aperture_history = []
    coupled_aqueous_history = []
    cumulative_extent = {phase_id: [0.0] * cell_count for phase_id in phase_ids}
    allowed_balance = request.absolute_inventory_balance_tolerance_mol_m3
    for knot_index, time_s in enumerate(times):
        if knot_index > 0:
            interval = campaign.kinetic_intervals[knot_index - 1]
            dt = interval.end_time_s - interval.start_time_s
            for phase_id in phase_ids:
                rates = interval.phase_extent_rate_mol_m3_s_by_cell[phase_id]
                for cell, rate in enumerate(rates):
                    extent = rate * dt
                    final_solid = concentrations_by_phase[phase_id][cell] + extent
                    tolerance = allowed_balance + request.relative_inventory_balance_tolerance * max(
                        concentrations_by_phase[phase_id][cell], abs(extent), 1e-30
                    )
                    if final_solid < -tolerance or not math.isfinite(final_solid):
                        return Calculation(status="out_of_scope", values={
                            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                            "input_sha256": digest, "committed_knot_count": len(aperture_history),
                            "failed_interval_index": knot_index - 1, "failed_cell_index": cell,
                            "failed_phase_id": phase_id, "reason": "phase kinetic increment depletes finite solid inventory",
                            "aperture_history": aperture_history,
                        })
                    if final_solid < 0.0:
                        return Calculation(status="out_of_scope", values={
                            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                            "input_sha256": digest, "committed_knot_count": len(aperture_history),
                            "failed_interval_index": knot_index - 1, "failed_cell_index": cell,
                            "failed_phase_id": phase_id, "reason": "small negative phase inventory is not clipped",
                            "aperture_history": aperture_history,
                        })
                    concentrations_by_phase[phase_id][cell] = final_solid
                    cumulative_extent[phase_id][cell] += extent

        state = result["state_history"][knot_index]
        if state.get("time_s") != time_s:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_knot_count": len(aperture_history),
                "failed_knot_index": knot_index, "reason": "upstream state time does not match exact request knot",
                "aperture_history": aperture_history,
            })
        source_concentrations = state.get("species_concentration_mol_m3_by_id", {})
        if set(source_concentrations) != set(species_by_id):
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_knot_count": len(aperture_history),
                "failed_knot_index": knot_index, "reason": "upstream species mapping differs",
                "aperture_history": aperture_history,
            })
        coupled_concentrations = {species_id: [] for species_id in species_by_id}
        for cell in range(cell_count):
            for species_id, species in species_by_id.items():
                source_row = source_concentrations[species_id]
                if not isinstance(source_row, list) or len(source_row) != cell_count:
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "input_sha256": digest, "committed_knot_count": len(aperture_history),
                        "failed_knot_index": knot_index, "failed_species_id": species_id,
                        "reason": "upstream species concentration field has invalid cell dimension",
                        "aperture_history": aperture_history,
                    })
                phase_uptake = math.fsum(
                    phase_by_id[phase_id].precipitation_stoichiometry.get(species_id, 0.0)
                    * cumulative_extent[phase_id][cell] for phase_id in phase_ids
                )
                concentration = source_row[cell] - phase_uptake
                if not math.isfinite(concentration) or concentration < 0.0:
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "input_sha256": digest, "committed_knot_count": len(aperture_history),
                        "failed_knot_index": knot_index, "failed_cell_index": cell,
                        "failed_species_id": species_id,
                        "reason": "phase extent exceeds the transported aqueous species inventory; no clipping is applied",
                        "aperture_history": aperture_history,
                    })
                coupled_concentrations[species_id].append(concentration)
            charge = math.fsum(species_by_id[species_id].charge_number * coupled_concentrations[species_id][cell]
                               for species_id in species_by_id)
            charge_scale = math.fsum(abs(species_by_id[species_id].charge_number)
                                     * coupled_concentrations[species_id][cell] for species_id in species_by_id)
            allowed_charge = (request.absolute_charge_balance_tolerance_mol_eq_m3
                              + request.relative_charge_balance_tolerance * max(charge_scale, 1e-30))
            if abs(charge) > allowed_charge:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                    "input_sha256": digest, "committed_knot_count": len(aperture_history),
                    "failed_knot_index": knot_index, "failed_cell_index": cell,
                    "charge_balance_residual_mol_eq_m3": charge,
                    "reason": "phase-corrected local liquid charge balance exceeds tolerance",
                    "aperture_history": aperture_history,
                })

        phase_volume_by_cell = []
        remaining_average_aperture = []
        remaining_covered_aperture = []
        for cell in range(cell_count):
            solid_volume = math.fsum(
                concentrations_by_phase[phase_id][cell] * liquid_cell_volume
                * request.solid_molar_volume_m3_mol_by_phase[phase_id] for phase_id in phase_ids
            )
            mean_loss = solid_volume / plan_area
            coverage = request.coverage_fraction_by_cell[cell]
            if coverage == 0.0:
                if solid_volume > 0.0:
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "input_sha256": digest, "committed_knot_count": len(aperture_history),
                        "failed_knot_index": knot_index, "failed_cell_index": cell,
                        "reason": "positive phase volume cannot map to zero declared coverage",
                        "aperture_history": aperture_history,
                    })
                covered_remaining = None
            else:
                local_loss = solid_volume / (request.deposition_side_count * coverage * plan_area)
                covered_remaining = request.initial_aperture_m_by_cell[cell] - local_loss
                if covered_remaining < 0.0 or not math.isfinite(covered_remaining):
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "input_sha256": digest, "committed_knot_count": len(aperture_history),
                        "failed_knot_index": knot_index, "failed_cell_index": cell,
                        "reason": "covered-patch aperture would be negative or nonfinite",
                        "aperture_history": aperture_history,
                    })
            mean_remaining = request.initial_aperture_m_by_cell[cell] - mean_loss
            if mean_remaining < 0.0 or not math.isfinite(mean_remaining):
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                    "input_sha256": digest, "committed_knot_count": len(aperture_history),
                    "failed_knot_index": knot_index, "failed_cell_index": cell,
                    "reason": "equivalent mean aperture would be negative or nonfinite",
                    "aperture_history": aperture_history,
                })
            phase_volume_by_cell.append(solid_volume)
            remaining_average_aperture.append(mean_remaining)
            remaining_covered_aperture.append(covered_remaining)
        phase_history.append({
            "time_s": time_s,
            "solid_inventory_mol_per_initial_cell_volume_m3_by_phase_and_cell": {
                phase_id: list(concentrations_by_phase[phase_id]) for phase_id in phase_ids
            },
            "solid_volume_m3_by_cell": phase_volume_by_cell,
        })
        aperture_history.append({
            "time_s": time_s,
            "phase_kinetic_interval_id": campaign.kinetic_intervals[knot_index - 1].interval_id if knot_index else None,
            "net_phase_extent_mol_m3_by_phase_and_cell": {
                phase_id: list(cumulative_extent[phase_id]) for phase_id in phase_ids
            },
            "phase_corrected_aqueous_concentration_mol_m3_by_species_and_cell": coupled_concentrations,
            "equivalent_mean_remaining_aperture_m_by_cell": remaining_average_aperture,
            "covered_patch_remaining_aperture_m_by_cell": remaining_covered_aperture,
            "deposit_volume_m3_by_cell": phase_volume_by_cell,
        })
        coupled_aqueous_history.append({"time_s": time_s, "concentration_mol_m3_by_species_and_cell": coupled_concentrations})

    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": transport.asset_id,
        "physical_scope_id": transport.physical_scope_id,
        "clock_id": transport.clock_id,
        "input_sha256": digest,
        "activity_transport_input_sha256": canonical_digest(transport.model_dump(mode="json")),
        "activity_transport_result_sha256": request.activity_transport_result_sha256,
        "kinetic_campaign_input_sha256": canonical_digest(campaign.model_dump(mode="json")),
        "kinetic_configuration_sha256": campaign.kinetic_configuration_sha256,
        "kinetic_parameter_source_sha256": campaign.kinetic_parameter_source_sha256,
        "molar_volume_record_sha256": request.molar_volume_record_sha256,
        "geometry": {
            "cell_count": cell_count,
            "cell_length_m": list(request.cell_length_m),
            "transverse_width_m": request.transverse_width_m,
            "deposition_side_count": request.deposition_side_count,
            "coverage_fraction_by_cell": list(request.coverage_fraction_by_cell),
            "fixed_geometry_activity_transport_cross_section_m2": transport.cross_section_area_m2,
        },
        "phase_inventory_history": phase_history,
        "aperture_history": aperture_history,
        "prefix_policy": "each exact knot commits only after phase inventory, liquid species availability, charge and nonnegative aperture checks",
        "coupling_order": "activity-corrected transport result, then caller interval solid kinetics, then phase-volume-to-aperture map; aperture applies only to a separately reviewed next segment",
        "interpretation": "bounded spatial phase-inventory and equivalent-aperture handoff",
        "limitations": [
            "Solid phase rates are caller-supplied interval extent rates from the typed direct-rate kinetic campaign; this API does not evaluate a saturation callback or derive kinetics.",
            "Precipitation extent is applied after each activity transport segment and is not fed back into that already computed segment; the updated aperture is a next-segment handoff only.",
            "The activity transport source uses one fixed uniform cross-section. This request therefore requires a uniform initial aperture and produces a mapped per-cell aperture history for subsequent variable-geometry transport handling.",
            "Equal face partition and uniform covered-cell deposition are caller-reviewed geometric approximations; no local morphology, porosity, adhesion, pit geometry or deposit redistribution is inferred.",
            "No automatic speciation, phase discovery, equilibrium selection, wall-rate law, global multiphysics solve, corrosion rate or qualification is provided.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceActivityTransportPhaseApertureRequest,
        evaluator=evaluate_crevice_activity_transport_phase_aperture,
        units={
            "initial_aperture_m_by_cell[]": "m",
            "cell_length_m[]": "m",
            "solid_molar_volume_m3_mol_by_phase.*": "m^3/mol",
            "phase_inventory_history[].solid_inventory_mol_per_initial_cell_volume_m3_by_phase_and_cell.*[]": "mol/m^3(initial liquid volume)",
            "phase_inventory_history[].solid_volume_m3_by_cell[]": "m^3",
            "aperture_history[].equivalent_mean_remaining_aperture_m_by_cell[]": "m",
            "aperture_history[].covered_patch_remaining_aperture_m_by_cell[]": "m",
            "aperture_history[].phase_corrected_aqueous_concentration_mol_m3_by_species_and_cell.*[]": "mol/m^3",
        },
        assumptions=(
            "The activity-corrected reactive transport calculation is completed on a fixed, uniform initial slit geometry and exact caller clock.",
            "The solid kinetic campaign supplies explicit cellwise extent rates for each exact interval; rates are held constant over that interval.",
            "Aqueous species are adjusted by balanced solid reaction extents after each transport segment and checked against finite cell inventories.",
            "Phase volume is converted to per-cell equivalent gap using caller molar volumes, face count and coverage; no morphology is solved.",
            "The aperture output is for a subsequent segment and does not feed back into the source transport result.",
        ),
        source_ids=SOURCE_IDS,
        qualification="user_model",
    )]
