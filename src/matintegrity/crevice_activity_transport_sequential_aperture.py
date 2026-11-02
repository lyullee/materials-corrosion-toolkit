"""Sequential moving-aperture campaign for activity-corrected crevice transport."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_activity_corrected_transport import (
    CreviceActivityReactiveTransportRequest,
    REACTION_SOURCE_ID,
    solve_crevice_activity_corrected_reactive_transport,
)
from .crevice_activity_transport_phase_aperture import (
    CreviceActivityTransportPhaseApertureRequest,
    evaluate_crevice_activity_transport_phase_aperture,
)
from .multiphase_kinetic_transport import CompetingSolidKineticTransport
from .registry import ModelSpec

MODEL_ID = "integration.crevice_activity_transport_sequential_aperture_campaign"
SOURCE_IDS = (
    "caller_activity_corrected_reactive_transport_history",
    "caller_cellwise_competing_solid_kinetic_rate_campaign",
    "caller_solid_molar_volume_and_deposition_coverage",
    "sequential_fixed_aperture_reactive_transport_segments",
)


class CreviceActivityTransportSequentialApertureCampaign(Contract):
    """Run exact two-knot transport segments and carry a uniform aperture forward."""

    schema_version: Literal["matintegrity.crevice_activity_transport_sequential_aperture.v1"] = (
        "matintegrity.crevice_activity_transport_sequential_aperture.v1"
    )
    assessment_id: str = Field(min_length=1)
    activity_transport_request: CreviceActivityReactiveTransportRequest
    solid_kinetic_campaign: CompetingSolidKineticTransport
    initial_aperture_m_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    cell_length_m: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    transverse_width_m: Positive
    deposition_side_count: Literal[1, 2]
    coverage_fraction_by_cell: tuple[float, ...] = Field(min_length=2, max_length=300)
    solid_molar_volume_m3_mol_by_phase: dict[str, Positive]
    molar_volume_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    molar_volume_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    aperture_uniformity_relative_tolerance: float = Field(default=1e-9, gt=0.0, le=1e-3)
    maximum_relative_aperture_change_per_segment: float = Field(default=0.1, gt=0.0, le=1.0)
    absolute_inventory_balance_tolerance_mol_m3: Positive = 1e-10
    relative_inventory_balance_tolerance: float = Field(default=1e-9, gt=0.0, le=0.01)
    absolute_charge_balance_tolerance_mol_eq_m3: Positive = 1e-10
    relative_charge_balance_tolerance: float = Field(default=1e-7, gt=0.0, le=0.01)
    geometry_match_relative_tolerance: float = Field(default=1e-10, gt=0.0, le=1e-5)
    fixed_uniform_initial_geometry_reviewed: bool
    activity_and_kinetic_species_mapping_reviewed: bool
    rate_campaign_is_interval_extent_rate_basis_reviewed: bool
    phase_volume_coverage_and_side_partition_reviewed: bool
    between_segment_geometry_update_reviewed: bool
    uniform_aperture_remap_reviewed: bool
    no_within_segment_convergence_or_morphology_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_campaign(self):
        transport = self.activity_transport_request
        campaign = self.solid_kinetic_campaign
        kinetic_transport = campaign.transport
        count = transport.cell_count
        if count != len(self.initial_aperture_m_by_cell) or count != len(self.cell_length_m):
            raise ValueError("initial apertures and cell lengths must align with transport cell count")
        if count != len(self.coverage_fraction_by_cell):
            raise ValueError("coverage fractions must align with transport cell count")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.coverage_fraction_by_cell):
            raise ValueError("coverage fractions must lie in [0, 1]")
        if any(not math.isclose(value, self.initial_aperture_m_by_cell[0],
                               rel_tol=self.geometry_match_relative_tolerance,
                               abs_tol=self.geometry_match_relative_tolerance * self.initial_aperture_m_by_cell[0])
               for value in self.initial_aperture_m_by_cell[1:]):
            raise ValueError("activity transport exposes one cross-section, so the initial aperture must be uniform")
        if any(not math.isclose(value, self.cell_length_m[0], rel_tol=0.0, abs_tol=0.0)
               for value in self.cell_length_m[1:]):
            raise ValueError("the activity transport solver requires uniform axial cell lengths")
        if not math.isclose(math.fsum(self.cell_length_m), transport.length_m,
                            rel_tol=self.geometry_match_relative_tolerance,
                            abs_tol=self.geometry_match_relative_tolerance * transport.length_m):
            raise ValueError("cell lengths must span the transport domain")
        expected_area = self.initial_aperture_m_by_cell[0] * self.transverse_width_m
        if not math.isclose(transport.cross_section_area_m2, expected_area,
                            rel_tol=self.geometry_match_relative_tolerance,
                            abs_tol=self.geometry_match_relative_tolerance * expected_area):
            raise ValueError("initial aperture × width must match the transport cross-section")
        if campaign.phase_rate_laws or not campaign.kinetic_intervals:
            raise ValueError("only explicit interval extent rates are supported by this sequential adapter")
        if len(campaign.kinetic_intervals) != len(transport.output_time_s) - 1:
            raise ValueError("one caller rate interval must match every adjacent transport knot pair")
        if campaign.transport.output_times_s != transport.output_time_s:
            raise ValueError("activity and kinetic campaign clocks must match exactly")
        if campaign.transport.cell_count != count or campaign.transport.length_m != transport.length_m:
            raise ValueError("activity and kinetic campaign grids must match")
        if campaign.transport.species_ids != tuple(row.species_id for row in transport.species):
            raise ValueError("activity and kinetic campaign species order must match")
        if kinetic_transport.reference_cross_section_m2 is None or not math.isclose(
            kinetic_transport.reference_cross_section_m2, expected_area,
            rel_tol=self.geometry_match_relative_tolerance,
            abs_tol=self.geometry_match_relative_tolerance * expected_area,
        ):
            raise ValueError("kinetic campaign reference cross-section must match the initial aperture")
        if kinetic_transport.cell_cross_section_history_m2 is not None or kinetic_transport.face_cross_section_history_m2 is not None:
            raise ValueError("predeclared moving-area histories cannot be combined with this between-segment updater")
        if any(not math.isclose(row, expected_area, rel_tol=self.geometry_match_relative_tolerance,
                                abs_tol=self.geometry_match_relative_tolerance * expected_area)
               for row in (kinetic_transport.cell_cross_section_m2 or ())):
            raise ValueError("kinetic campaign cell cross-sections must match the initial slit")
        if set(self.solid_molar_volume_m3_mol_by_phase) != {
            row.solid_species_id for row in campaign.candidate_solid_phases
        }:
            raise ValueError("molar volume mapping must cover exactly the kinetic phase set")
        if canonical_digest(self.solid_molar_volume_m3_mol_by_phase) != self.molar_volume_record_sha256:
            raise ValueError("molar-volume digest does not bind the phase mapping")
        if not any(row.sha256 == self.molar_volume_record_sha256 for row in self.molar_volume_evidence):
            raise ValueError("molar-volume Evidence must pin the phase mapping")
        if not all((self.fixed_uniform_initial_geometry_reviewed,
                    self.activity_and_kinetic_species_mapping_reviewed,
                    self.rate_campaign_is_interval_extent_rate_basis_reviewed,
                    self.phase_volume_coverage_and_side_partition_reviewed,
                    self.between_segment_geometry_update_reviewed,
                    self.uniform_aperture_remap_reviewed,
                    self.no_within_segment_convergence_or_morphology_claim_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all chemistry mapping, geometry, rate and authorization reviews are required")
        return self


def _segment_transport_request(
    base: CreviceActivityReactiveTransportRequest,
    segment: int,
    concentrations_by_species: dict[str, list[float]],
    aperture_m: float,
    transverse_width_m: float,
) -> CreviceActivityReactiveTransportRequest:
    payload = base.model_dump(mode="python")
    payload["cross_section_area_m2"] = aperture_m * transverse_width_m
    duration = base.output_time_s[segment + 1] - base.output_time_s[segment]
    # The transport integrator and its matching kinetic campaign require a zero-based local clock.
    # All coefficient and boundary samples are sliced at the original exact interval endpoints.
    payload["output_time_s"] = [0.0, duration]
    payload["mouth_boundary_concentration_mol_m3_by_species"] = {
        species_id: list(values[segment:segment + 2])
        for species_id, values in base.mouth_boundary_concentration_mol_m3_by_species.items()
    }
    payload["cell_face_axial_velocity_m_s_by_knot"] = [
        list(values[segment:segment + 2]) for values in base.cell_face_axial_velocity_m_s_by_knot
    ]
    species_payload = []
    for row in base.species:
        item = row.model_dump(mode="python")
        item["initial_cell_concentration_mol_m3"] = list(concentrations_by_species[row.species_id])
        item["activity_coefficient_by_time_and_cell"] = [
            list(values) for values in row.activity_coefficient_by_time_and_cell[segment:segment + 2]
        ]
        item["mouth_activity_coefficient_by_time"] = list(row.mouth_activity_coefficient_by_time[segment:segment + 2])
        species_payload.append(item)
    payload["species"] = species_payload
    if hasattr(base, "temperature_K_by_knot"):
        payload["temperature_K_by_knot"] = list(base.temperature_K_by_knot[segment:segment + 2])
        reactions = []
        for reaction in base.reactions:
            item = reaction.model_dump(mode="python")
            for name in ("forward_rate_constant_mol_m3_s_by_knot", "reverse_rate_constant_mol_m3_s_by_knot",
                         "equilibrium_constant_dimensionless_by_knot"):
                item[name] = list(getattr(reaction, name)[segment:segment + 2])
            parameter_digest = canonical_digest({
                "reaction_id": item["reaction_id"],
                "forward_rate_constant_mol_m3_s_by_knot": item["forward_rate_constant_mol_m3_s_by_knot"],
                "reverse_rate_constant_mol_m3_s_by_knot": item["reverse_rate_constant_mol_m3_s_by_knot"],
                "equilibrium_constant_dimensionless_by_knot": item["equilibrium_constant_dimensionless_by_knot"],
            })
            item["parameter_record_sha256"] = parameter_digest
            source_evidence = next(
                row for row in reaction.evidence
                if row.source_id == reaction.parameter_record_id
                and row.license_id is not None
            )
            item["evidence"] = [source_evidence.model_copy(update={
                "origin": "user_declared",
                "citation": source_evidence.citation + "; interval subset generated from the caller-pinned full schedule",
                "sha256": parameter_digest,
            }).model_dump(mode="python")]
            reactions.append(item)
        payload["reactions"] = reactions
        payload["reaction_network_sha256"] = canonical_digest([row for row in reactions])
        network_evidence = next(
            row for row in base.reaction_network_evidence
            if row.source_id == REACTION_SOURCE_ID and row.license_id is not None
        )
        payload["reaction_network_evidence"] = [network_evidence.model_copy(update={
            "origin": "user_declared",
            "citation": network_evidence.citation + "; interval subset generated from the caller-pinned full schedule",
            "sha256": payload["reaction_network_sha256"],
        }).model_dump(mode="python")]
    return CreviceActivityReactiveTransportRequest.model_validate(payload)


def _segment_kinetic_campaign(
    base: CompetingSolidKineticTransport,
    segment: int,
    concentrations_by_species: dict[str, list[float]],
    solid_inventory_by_phase: dict[str, list[float]],
    area_m2: float,
) -> CompetingSolidKineticTransport:
    payload = base.model_dump(mode="python")
    transport = payload["transport"]
    duration = base.transport.output_times_s[segment + 1] - base.transport.output_times_s[segment]
    transport["output_times_s"] = [0.0, duration]
    transport["initial_concentration_mol_m3"] = [
        list(concentrations_by_species[species_id]) for species_id in base.transport.species_ids
    ]
    transport["reference_cross_section_m2"] = area_m2
    if transport.get("cell_cross_section_m2") is not None:
        transport["cell_cross_section_m2"] = [area_m2] * base.transport.cell_count
    if transport.get("face_cross_section_m2") is not None:
        transport["face_cross_section_m2"] = [area_m2] * (base.transport.cell_count + 1)
    if transport.get("mouth_concentration_history_mol_m3") is not None:
        transport["mouth_concentration_history_mol_m3"] = [
            list(row) for row in base.transport.mouth_concentration_history_mol_m3[segment:segment + 2]
        ]
        transport["mouth_concentration_mol_m3"] = list(transport["mouth_concentration_history_mol_m3"][0])
    payload["initial_solid_inventory_mol_m3_by_phase"] = solid_inventory_by_phase
    interval = base.kinetic_intervals[segment].model_dump(mode="python")
    interval["start_time_s"] = 0.0
    interval["end_time_s"] = duration
    payload["kinetic_intervals"] = [interval]
    return CompetingSolidKineticTransport.model_validate(payload)


def evaluate_crevice_activity_transport_sequential_aperture(
    request: CreviceActivityTransportSequentialApertureCampaign,
) -> Calculation:
    """Re-solve transport on each segment's entering uniform aperture, then hand aperture forward."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = request.activity_transport_request
    campaign = request.solid_kinetic_campaign
    aperture = float(request.initial_aperture_m_by_cell[0])
    concentrations = {
        row.species_id: list(row.initial_cell_concentration_mol_m3) for row in base.species
    }
    solid_inventory = {
        phase_id: list(values) for phase_id, values in campaign.initial_solid_inventory_mol_m3_by_phase.items()
    }
    segments: list[dict] = []
    for index in range(len(base.output_time_s) - 1):
        area = aperture * request.transverse_width_m
        try:
            transport_request = _segment_transport_request(
                base, index, concentrations, aperture, request.transverse_width_m
            )
            kinetic_campaign = _segment_kinetic_campaign(
                campaign, index, concentrations, solid_inventory, area
            )
            transport_result = solve_crevice_activity_corrected_reactive_transport(transport_request)
            if transport_result.status != "computed":
                return Calculation(status=transport_result.status, values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                    "input_sha256": digest, "committed_segment_count": len(segments),
                    "failed_segment_index": index, "failed_stage": "reactive_transport",
                    "reason": transport_result.values.get("reason", "transport segment did not compute"),
                    "segments": segments,
                })
            phase_request = CreviceActivityTransportPhaseApertureRequest(
                assessment_id=f"{request.assessment_id}:segment:{index}",
                activity_transport_request=transport_request,
                activity_transport_result=transport_result.model_dump(mode="json"),
                activity_transport_result_sha256=canonical_digest(transport_result.model_dump(mode="json")),
                solid_kinetic_campaign=kinetic_campaign,
                initial_aperture_m_by_cell=tuple(aperture for _ in range(base.cell_count)),
                cell_length_m=request.cell_length_m,
                transverse_width_m=request.transverse_width_m,
                deposition_side_count=request.deposition_side_count,
                coverage_fraction_by_cell=request.coverage_fraction_by_cell,
                solid_molar_volume_m3_mol_by_phase=request.solid_molar_volume_m3_mol_by_phase,
                molar_volume_record_sha256=request.molar_volume_record_sha256,
                molar_volume_evidence=request.molar_volume_evidence,
                absolute_inventory_balance_tolerance_mol_m3=request.absolute_inventory_balance_tolerance_mol_m3,
                relative_inventory_balance_tolerance=request.relative_inventory_balance_tolerance,
                absolute_charge_balance_tolerance_mol_eq_m3=request.absolute_charge_balance_tolerance_mol_eq_m3,
                relative_charge_balance_tolerance=request.relative_charge_balance_tolerance,
                geometry_match_relative_tolerance=request.geometry_match_relative_tolerance,
                fixed_uniform_initial_geometry_reviewed=True,
                activity_and_kinetic_species_mapping_reviewed=True,
                rate_campaign_is_interval_extent_rate_basis_reviewed=True,
                phase_volume_coverage_and_side_partition_reviewed=True,
                sequential_split_and_next_segment_only_reviewed=True,
                no_morphology_or_local_pit_claim_reviewed=True,
                computational_use_authorized=True,
            )
            phase_result = evaluate_crevice_activity_transport_phase_aperture(phase_request)
        except (ValueError, TypeError, KeyError, OverflowError) as error:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_segment_count": len(segments),
                "failed_segment_index": index, "failed_stage": "segment_contract",
                "reason": str(error), "segments": segments,
            })
        if phase_result.status != "computed":
            return Calculation(status=phase_result.status, values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_segment_count": len(segments),
                "failed_segment_index": index, "failed_stage": "phase_aperture_handoff",
                "reason": phase_result.values.get("reason", "phase/aperture segment did not compute"),
                "segments": segments,
            })
        values = phase_result.values
        endpoint = values["aperture_history"][-1]
        local_apertures = endpoint["equivalent_mean_remaining_aperture_m_by_cell"]
        mean_aperture = math.fsum(local_apertures) / len(local_apertures)
        relative_spread = max(abs(value - mean_aperture) for value in local_apertures) / max(mean_aperture, 1e-30)
        relative_change = abs(mean_aperture - aperture) / max(aperture, 1e-30)
        if relative_spread > request.aperture_uniformity_relative_tolerance:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_segment_count": len(segments),
                "failed_segment_index": index,
                "reason": "cellwise phase deposition creates nonuniform aperture unsupported by the scalar-area transport solver",
                "relative_cell_aperture_spread": relative_spread,
                "segments": segments,
            })
        if relative_change > request.maximum_relative_aperture_change_per_segment:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "committed_segment_count": len(segments),
                "failed_segment_index": index,
                "reason": "aperture change exceeds caller step limit; refine the caller clock before rerunning",
                "relative_aperture_change": relative_change,
                "segments": segments,
            })
        phase_history = values["phase_inventory_history"][-1][
            "solid_inventory_mol_per_initial_cell_volume_m3_by_phase_and_cell"
        ]
        next_area = mean_aperture * request.transverse_width_m
        volume_basis_ratio = area / next_area
        solid_inventory = {
            key: [value * volume_basis_ratio for value in row]
            for key, row in phase_history.items()
        }
        end_aqueous = {
            key: list(value) for key, value in endpoint[
                "phase_corrected_aqueous_concentration_mol_m3_by_species_and_cell"
            ].items()
        }
        concentrations = {
            key: [value * volume_basis_ratio for value in row]
            for key, row in end_aqueous.items()
        }
        segment_record = {
            "segment_index": index,
            "start_time_s": base.output_time_s[index],
            "end_time_s": base.output_time_s[index + 1],
            "solver_local_time_origin_s": base.output_time_s[index],
            "solver_local_output_times_s": [0.0, base.output_time_s[index + 1] - base.output_time_s[index]],
            "entering_uniform_aperture_m": aperture,
            "leaving_uniform_aperture_m": mean_aperture,
            "relative_aperture_change": relative_change,
            "liquid_volume_concentration_basis_conversion_factor": volume_basis_ratio,
            "transport_input_sha256": canonical_digest(transport_request.model_dump(mode="json")),
            "transport_result_sha256": canonical_digest(transport_result.model_dump(mode="json")),
            "phase_handoff_input_sha256": canonical_digest(phase_request.model_dump(mode="json")),
            "phase_handoff_result_sha256": canonical_digest(phase_result.model_dump(mode="json")),
            "transport_result": transport_result.model_dump(mode="json"),
            "phase_handoff_result": phase_result.model_dump(mode="json"),
            "end_concentration_before_next_volume_basis_conversion_mol_m3": end_aqueous,
            "next_segment_initial_concentration_mol_m3_by_species_and_cell": concentrations,
            "next_segment_initial_solid_inventory_mol_m3_by_phase_and_cell": solid_inventory,
        }
        segments.append(segment_record)
        aperture = mean_aperture

    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "segment_count": len(segments),
        "segments": segments,
        "final_uniform_aperture_m": aperture,
        "final_solid_inventory_mol_m3_by_phase_and_cell": solid_inventory,
        "final_aqueous_concentration_mol_m3_by_species_and_cell": concentrations,
        "geometry_update_mode": "sequential_between_segments_uniform_area_only",
        "fixed_point_convergence_claimed": False,
        "interpretation": "sequential activity-reactive transport and caller-explicit solid kinetics with carried phase inventory and uniform aperture",
        "limitations": [
            "Transport is re-solved once per caller interval using the uniform aperture inherited from the previous interval; no within-interval fixed-point iteration is performed.",
            "Cellwise aperture changes are accepted only when their spread is within a tight caller tolerance; the scalar-area solver cannot resolve nonuniform geometry.",
            "Solid kinetic extent rates are explicit caller inputs and are not recalibrated or recomputed from saturation during this campaign.",
            "The calculation has no deposit morphology, porosity, adhesion, phase discovery, automatic speciation, qualified wall law or risk probability.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceActivityTransportSequentialApertureCampaign,
        evaluator=evaluate_crevice_activity_transport_sequential_aperture,
        units={
            "segments[].start_time_s": "s",
            "segments[].end_time_s": "s",
            "segments[].entering_uniform_aperture_m": "m",
            "segments[].leaving_uniform_aperture_m": "m",
            "final_uniform_aperture_m": "m",
            "final_solid_inventory_mol_m3_by_phase_and_cell.*[]": "mol/m^3",
            "final_aqueous_concentration_mol_m3_by_species_and_cell.*[]": "mol/m^3",
        },
        assumptions=(
            "Each exact caller time segment is solved once on its entering uniform aperture, then explicit phase rates update inventory and the next segment geometry.",
            "Cellwise phase-volume-to-aperture mapping must remain uniform within the declared spread tolerance because the activity transport solver has a scalar cross-section.",
            "No within-segment fixed-point or nonlinear convergence claim is made.",
        ),
        source_ids=SOURCE_IDS,
        qualification="user_model",
    ),)
