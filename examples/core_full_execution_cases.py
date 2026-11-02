"""Authored mathematical execution cases, with no experimental qualification claims.

Review flags describe the explicitly declared toy problem and its software use.
All material, equilibrium and kinetic coefficients below are synthetic inputs.
"""

import copy
import json
import math
from pathlib import Path

from matintegrity.contracts import canonical_digest

ROOT = Path(__file__).resolve().parents[1]


def evidence(source, digest):
    return dict(
        source_id=source,
        origin="synthetic",
        citation="Project-authored mathematical execution fixture; not observations or material calibration.",
        license_id="CC0-1.0",
        sha256=digest,
    )


def sample_requests():
    from matintegrity.registry import default_registry

    registry = default_registry()
    result = {}
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    baselines = json.loads(
        (ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8")
    )["model_inputs"]
    # Exactly closed periodic sinusoid: the Fourier reference work is pi*A*B.
    stress = [[1e8 * math.cos(2 * math.pi * i / 8), 0.0, 0.0, 0.0, 0.0, 0.0] for i in range(8)]
    strain = [[1e-3 * math.sin(2 * math.pi * i / 8), 0.0, 0.0, 0.0, 0.0, 0.0] for i in range(8)]
    stress.append(stress[0].copy())
    strain.append(strain[0].copy())
    digest = canonical_digest({"stress": stress, "strain": strain})
    ev = evidence("authored-periodic-cycle", digest)
    fourier = dict(
        analysis_id="toy-fourier",
        material_condition_id="toy-material",
        source_id=ev["source_id"],
        source_sha256=digest,
        evidence=ev,
        sample_ids=[f"s{i}" for i in range(9)],
        stress_tensor_components_Pa=stress,
        strain_tensor_components=strain,
        strain_shear_convention="tensor",
        tensor_basis_and_order_reviewed=True,
        uniform_periodic_sampling_reviewed=True,
        closed_cycle_and_path_order_reviewed=True,
        stress_strain_conjugacy_and_work_sign_reviewed=True,
        fourier_reconstruction_suitability_reviewed=True,
    )
    result["fatigue.periodic_fourier_tensor_work"] = fourier
    calibration = canonical_digest({"work": [1e3, 1e7], "life": [1e7, 1e3]})
    result["fatigue.periodic_fourier_tensor_work_life"] = dict(
        analysis_id="toy-fourier-life",
        material_condition_id="toy-material",
        cycles=[dict(cycle_id="c1", work_request=fourier, cycle_count_equivalents=10.0)],
        calibration_id="toy-curve",
        calibration_material_condition_id="toy-material",
        calibration_source_id="authored-curve",
        calibration_sha256=calibration,
        calibration_evidence=evidence("authored-curve", calibration),
        absolute_work_density_points_J_m3=[1e3, 1e7],
        cycles_to_failure=[1e7, 1e3],
        material_match_and_curve_basis_reviewed=True,
        rights_and_engineering_use_reviewed=True,
        cycle_decomposition_and_repetitions_reviewed=True,
        absolute_work_parameter_and_curve_fit_reviewed=True,
        linear_miner_rule_reviewed=True,
    )
    result["fatigue.sampled_tensor_stress_strain_work_cycle"] = dict(
        analysis_id="toy-polygon-work",
        material_condition_id="toy-material",
        location_id="toy-volume",
        stress_history_source_id=ev["source_id"],
        stress_history_sha256=digest,
        strain_history_source_id=ev["source_id"],
        strain_history_sha256=digest,
        sample_ids=fourier["sample_ids"],
        stress_tensor_components_Pa=stress,
        strain_tensor_components=strain,
        strain_shear_convention="tensor",
        cycle_closure_and_sample_order_reviewed=True,
        stress_basis_and_sign_reviewed=True,
        strain_basis_and_sign_reviewed=True,
        stress_strain_conjugacy_reviewed=True,
    )
    system = copy.deepcopy(examples["chemistry.aqueous_mass_action_speciation"])
    params = dict(A=0.5, B=3.3, temperature_K=system["temperature_K"], ion_size_nm=0.5)
    digest = canonical_digest(params)
    ev = evidence("authored-dh-parameters", digest)
    result["chemistry.aqueous_extended_debye_huckel_self_consistent_speciation"] = dict(
        system=system,
        water_mass_per_solution_volume_kg_L=0.997,
        debye_huckel_A_at_temperature=params["A"],
        debye_huckel_B_at_temperature_sqrt_kg_mol_per_nm=params["B"],
        parameter_temperature_K=system["temperature_K"],
        parameter_provider_id=ev["source_id"],
        parameter_provider_revision="toy-1",
        parameter_configuration_sha256=digest,
        parameter_record_sha256=digest,
        maximum_supported_ionic_strength_mol_kg=0.5,
        charge_balance_tolerance_mol_kg=1e-8,
        species_parameters=[
            dict(
                species_id=s["species_id"],
                ion_size_parameter_nm=0.5 if s["charge_number"] else None,
                evidence_source_id=ev["source_id"],
                evidence_record_sha256=digest,
            )
            for s in system["species"]
        ],
        water_mass_conversion_reviewed=True,
        molarity_to_molality_standard_state_mapping_reviewed=True,
        temperature_solvent_parameter_basis_reviewed=True,
        complete_inventory_and_charge_scope_reviewed=True,
        species_parameter_completeness_and_applicability_reviewed=True,
        fixed_point_solver_settings_reviewed=True,
        single_liquid_no_precipitation_scope_reviewed=True,
        evidence=[ev],
    )
    # Two explicitly supplied neutral phases compete for a finite toy inventory.
    source = copy.deepcopy(examples["chemistry.competitive_solid_saturation_kinetics"])
    laws = []
    growth = []
    all_evidence = []
    for phase, law in zip(source["candidate_solid_phases"], source["phase_rate_laws"], strict=True):
        raw = dict(
            solid_species_id=phase["solid_species_id"],
            critical_saturation_ratio=1.0,
            source_rate_constant_mol_m3_s=0.001,
            supersaturation_order=1.0,
            nucleated_inventory_threshold_mol_m3=0.0001,
            maximum_rate_mol_m3_s=0.1,
        )
        digest = canonical_digest(raw)
        raw.update(
            source_sha256=digest,
            evidence=[evidence("authored-nucleation-" + phase["solid_species_id"], digest)],
        )
        laws.append(raw)
        growth.append(
            dict(
                law=law,
                evidence=[evidence("authored-growth-" + phase["solid_species_id"], law["source_sha256"])],
            )
        )
        all_evidence.extend(raw["evidence"])
        all_evidence.extend(growth[-1]["evidence"])
    interval = dict(
        interval_id="hold",
        start_time_s=0.0,
        end_time_s=1.0,
        temperature_K=298.15,
        saturation_ratio_by_phase={p["solid_species_id"]: 1.5 for p in source["candidate_solid_phases"]},
    )
    digest = canonical_digest(interval)
    interval.update(record_sha256=digest, evidence=[evidence("authored-saturation", digest)])
    all_evidence += interval["evidence"]
    for index, digest in enumerate(
        [source["kinetic_configuration_sha256"], source["kinetic_parameter_source_sha256"]]
        + [s["source_sha256"] for s in source["aqueous_species"]]
        + [p["source_sha256"] for p in source["candidate_solid_phases"]]
    ):
        all_evidence.append(evidence(f"authored-record-{index}", digest))
    request = {
        key: source[key]
        for key in (
            "assessment_id",
            "physical_scope_id",
            "provider_id",
            "provider_revision",
            "kinetic_configuration_sha256",
            "kinetic_parameter_source_sha256",
            "temperature_K",
            "aqueous_species",
            "candidate_solid_phases",
        )
    }
    request.update(
        clock_id="toy-seconds",
        nucleation_laws=laws,
        growth_laws=growth,
        intervals=[interval],
        evidence=all_evidence,
        maximum_total_nucleation_rate_mol_m3_s=0.2,
        phase_stoichiometry_and_volume_reviewed=True,
        saturation_source_and_standard_state_reviewed=True,
        nucleation_law_units_threshold_and_support_reviewed=True,
        growth_law_temperature_support_reviewed=True,
        dissolution_then_formation_split_reviewed=True,
        closed_batch_scope_reviewed=True,
        computational_use_authorized=True,
    )
    result["chemistry.crevice_nucleation_kinetic_history"] = request
    from matintegrity.crevice_cellwise_nucleation_kinetic_history import (
        FixedKineticCell,
        compute_cell_order_sha256,
    )

    cells = []
    for name in ("left", "right"):
        geometry = dict(cell_id=name, cell_length_m=0.01, cross_section_area_m2=1e-4, solution_volume_m3=1e-6)
        digest = canonical_digest(geometry)
        history = copy.deepcopy(request)
        history["assessment_id"] = "toy-" + name
        cell = geometry | dict(
            geometry_sha256=digest,
            geometry_evidence=[evidence("authored-cell-" + name, digest)],
            kinetic_history=history,
        )
        cells.append(FixedKineticCell.model_validate_json(json.dumps(cell)))
    digest = compute_cell_order_sha256(
        "toy-cellwise", request["physical_scope_id"], request["clock_id"], tuple(cells)
    )
    result["integration.crevice_cellwise_nucleation_kinetic_history"] = dict(
        assessment_id="toy-cellwise",
        physical_scope_id=request["physical_scope_id"],
        clock_id=request["clock_id"],
        cells=[cell.model_dump(mode="json") for cell in cells],
        cell_order_sha256=digest,
        cell_order_evidence=[evidence("authored-cell-order", digest)],
        independent_cell_batch_scope_reviewed=True,
        no_intercell_transfer_during_kinetic_substep_reviewed=True,
        fixed_cell_solution_volume_reviewed=True,
        computational_use_authorized=True,
    )
    material = dict(
        physical_scope_id="toy-volume",
        material_condition_id="toy-material",
        provider_id="authored-strength",
        provider_revision="1",
        crack_case="A",
        reversed_torsion_fatigue_strength_Pa=2e8,
        ultimate_tensile_strength_Pa=6e8,
    )
    history = dict(
        physical_scope_id="toy-volume",
        provider_id="authored-stress",
        provider_revision="1",
        stress_history=[
            dict(
                time_s=float(i),
                sigma_xx_Pa=0.0,
                sigma_yy_Pa=0.0,
                sigma_zz_Pa=0.0,
                tau_xy_Pa=value,
                tau_yz_Pa=0.0,
                tau_zx_Pa=0.0,
            )
            for i, value in enumerate((0.0, 1e8, 0.0))
        ],
        candidate_planes=[dict(plane_id="x", normal_x=1.0, normal_y=0.0, normal_z=0.0)],
    )
    md = canonical_digest(material)
    hd = canonical_digest(history)
    result["fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen"] = dict(
        assessment_id="toy-mcdiarmid",
        physical_scope_id="toy-volume",
        material_condition_id="toy-material",
        crack_case="A",
        stress_history=history["stress_history"],
        candidate_planes=history["candidate_planes"],
        reversed_torsion_fatigue_strength_Pa=2e8,
        ultimate_tensile_strength_Pa=6e8,
        material_provider_id=material["provider_id"],
        material_provider_revision="1",
        material_record_sha256=md,
        usage_license_id="CC0-1.0",
        material_evidence=[evidence(material["provider_id"], md)],
        history_provider_id=history["provider_id"],
        history_provider_revision="1",
        history_record_sha256=hd,
        history_usage_license_id="CC0-1.0",
        history_evidence=[evidence(history["provider_id"], hd)],
        repeated_cycle_and_tensor_convention_reviewed=True,
        material_condition_and_crack_case_reviewed=True,
        plane_set_and_surface_orientation_reviewed=True,
        calibration_records_and_computational_use_reviewed=True,
    )
    cell = copy.deepcopy(baselines["chemistry.crevice_component_solid_partition"]["cell"])
    result["chemistry.crevice_closed_batch_aqueous_equilibrium"] = dict(
        assessment_id="toy-closed-aqueous",
        cell_id=cell["cell_id"],
        solution_volume_L=1.0,
        aqueous_activity_request=cell["aqueous_activity_request"],
        initial_species_amounts=[
            dict(
                species_id=s["species_id"],
                amount_mol={"Na": 0.001, "Cl": 0.001, "water": 1.0}.get(s["species_id"], 0.0),
            )
            for s in cell["aqueous_activity_request"]["system"]["species"]
        ],
        constraint_roles=cell["constraint_roles"],
        conserved_components=cell["conserved_components"],
        role_map_and_charge_scope_reviewed=True,
        closed_inventory_scope_reviewed=True,
        single_liquid_no_precipitation_scope_reviewed=True,
        equilibrium_and_activity_provider_scope_reviewed=True,
        computational_use_authorized=True,
    )
    from matintegrity.models.fad import FailureAssessmentCurve

    curve = FailureAssessmentCurve.model_validate_json(
        json.dumps(examples["structural.failure_assessment_points"]["curve"])
    ).model_dump(mode="json")
    scope = dict(
        asset_id="toy-asset",
        location_id="toy-location",
        physical_scope_id="toy-volume",
        clock_id="toy-seconds",
        material_condition_id=curve.get("material_condition_id", "toy-material"),
        geometry_basis_id="toy-geometry",
        load_history_id="toy-load",
    )
    knots = []
    for time, stress_intensity in ((0.0, 40e6), (1.0, 50e6)):
        values = dict(
            effective_mode_i_stress_intensity=stress_intensity,
            fracture_resistance=80e6,
            reference_stress=200e6,
            normalizing_strength=400e6,
        )
        receipts = []
        for quantity, value in values.items():
            digest = canonical_digest(dict(quantity=quantity, time_s=time, value=value))
            receipts.append(
                scope
                | dict(
                    quantity=quantity,
                    time_s=time,
                    provider_id="authored-fad-provider",
                    result_id=f"{quantity}-{time}",
                    result_sha256=digest,
                    evidence=[evidence("authored-fad-provider", digest)],
                )
            )
        knots.append(
            dict(
                time_s=time,
                effective_stress_intensity_Pa_sqrt_m=stress_intensity,
                fracture_resistance_Pa_sqrt_m=80e6,
                reference_stress_Pa=200e6,
                normalizing_strength_Pa=400e6,
                provider_receipts=receipts,
            )
        )
    result["structural.failure_assessment_history"] = scope | dict(
        assessment_id="toy-fad-history",
        curve=curve,
        curve_sha256=canonical_digest(curve),
        knots=knots,
        linear_elastic_k_solution_reviewed=True,
        reference_stress_solution_reviewed=True,
        toughness_and_strength_applicability_reviewed=True,
        load_history_and_combination_reviewed=True,
        geometry_and_material_scope_reviewed=True,
        curve_applicability_reviewed=True,
    )
    branches = []
    records = []
    for index, equilibrium in enumerate((-0.1, 0.1)):
        branch = dict(
            reaction_id=f"toy-bv-{index}",
            electron_number=1,
            signed_current_multiplier=1,
            exchange_current_density_A_m2_by_cell=[0.001, 0.001],
            equilibrium_potential_V_by_cell_and_time=[[equilibrium], [equilibrium]],
            anodic_transfer_coefficient=0.5,
            cathodic_transfer_coefficient=0.5,
            minimum_overpotential_V=-0.2,
            maximum_overpotential_V=0.2,
            kinetics_provider_id=f"authored-bv-{index}",
            kinetics_revision="1",
        )
        digest = canonical_digest(branch)
        branch["kinetics_sha256"] = digest
        branches.append(branch)
        records.append(evidence(branch["kinetics_provider_id"], digest))
    geometry = dict(
        cell_ids=["left", "right"],
        cell_lengths_m=[0.01, 0.01],
        cell_apertures_m=[0.001, 0.001],
        slit_width_m=0.02,
        reactive_face_count=2,
    )
    gd = canonical_digest(geometry)
    cd = canonical_digest([[1.0], [1.0]])
    records += [evidence("authored-geometry", gd), evidence("authored-conductivity", cd)]
    result["integration.crevice_spatial_ohmic_mixed_potential"] = geometry | dict(
        assessment_id="toy-ohmic",
        asset_id="toy-asset",
        location_id="toy-location",
        physical_scope_id="toy-volume",
        clock_id="toy-seconds",
        geometry_provider_id="authored-geometry",
        geometry_revision="1",
        geometry_sha256=gd,
        conductivity_provider_id="authored-conductivity",
        conductivity_revision="1",
        conductivity_sha256=cd,
        time_s=[0.0],
        temperature_K_by_time=[298.15],
        electrolyte_conductivity_S_m_by_cell_and_time=[[1.0], [1.0]],
        branches=branches,
        evidence=records,
        usage_rights_evidence=[records[0]],
        geometry_mapping_and_cell_order_reviewed=True,
        electrolyte_conductivity_support_reviewed=True,
        local_butler_volmer_parameters_and_sign_convention_reviewed=True,
        electronically_continuous_metal_and_no_metal_ohmic_drop_reviewed=True,
        electrolyte_ohmic_closure_and_insulated_ends_reviewed=True,
        quasi_steady_interval_independence_reviewed=True,
        usage_rights_reviewed=True,
        computational_use_authorized=True,
    )
    spatial = copy.deepcopy(
        baselines["integration.wet_co2_cylindrical_stage_speciation_scale_feedback"]["spatial_request"]
    )
    knots = []
    for knot in spatial["knots"]:
        records = [
            evidence("authored-electrode-calibration-" + str(i), reaction["calibration_sha256"])
            for i, reaction in enumerate(knot["reactions"])
        ]
        knots.append(
            dict(
                time_s=knot["time_s"],
                solution_film_thickness_m=knot["solution_film_thickness_m"],
                species=knot["species_boundaries"],
                reactions=knot["reactions"],
                kinetics_evidence=records,
            )
        )
    result["integration.wet_co2_cylindrical_transport_mixed_potential"] = dict(
        assessment_id="toy-steady-radial",
        geometry=spatial["geometry"],
        geometry_sha256=spatial["geometry_sha256"],
        knots=knots,
        boundary_chemistry_and_reference_reviewed=True,
        radial_domain_mesh_and_film_reviewed=True,
        current_reaction_and_surface_area_basis_reviewed=True,
    )

    def computed(model, payload):
        spec = registry._models[model]
        value = spec.evaluator(spec.input_type.model_validate_json(json.dumps(payload)))
        if value.status != "computed":
            raise ValueError((model, value.values))
        return value

    geometry = spatial["geometry"]
    geometry_result = computed("degradation.wet_co2_cylindrical_scale_geometry_history", geometry)
    hydraulic_knots = []
    for knot in geometry["history"]:
        record = dict(
            time_s=knot["time_s"],
            signed_flow_rate_m3_s=0.01,
            fluid_density_kg_m3=1000.0,
            dynamic_viscosity_Pa_s=0.001,
            absolute_roughness_m=1e-5,
        )
        digest = canonical_digest(record)
        record.update(record_sha256=digest, evidence=[evidence("authored-hydraulic-knot", digest)])
        hydraulic_knots.append(record)
    assessment = "toy-finite-electrode"
    hydraulics = computed(
        "integration.wet_co2_cylindrical_steady_hydraulics",
        dict(
            assessment_id=assessment,
            geometry=geometry,
            geometry_result=geometry_result.model_dump(mode="json"),
            knots=hydraulic_knots,
            laminar_regime_and_single_phase_reviewed=True,
            straight_pipe_and_fully_developed_flow_reviewed=True,
        ),
    )
    hydraulic_digest = canonical_digest(hydraulics.model_dump(mode="json"))
    transfer = {}
    for species_id in ("Fe2+", "OH-"):
        diffusivity = []
        for knot in geometry["history"]:
            record = dict(time_s=knot["time_s"], species_id=species_id, diffusivity_m2_s=1e-9)
            digest = canonical_digest(record)
            record.update(
                record_id="authored-diffusivity",
                record_sha256=digest,
                evidence=[evidence("authored-diffusivity", digest)],
            )
            diffusivity.append(record)
        value = computed(
            "integration.wet_co2_cylindrical_liquid_transfer_capacity_history",
            dict(
                assessment_id=assessment,
                physical_scope_id="toy-volume",
                condition_id="toy-condition",
                species_id=species_id,
                geometry=geometry,
                geometry_result=geometry_result.model_dump(mode="json"),
                hydraulics_result=hydraulics.model_dump(mode="json"),
                hydraulics_evidence=evidence(
                    "integration.wet_co2_cylindrical_steady_hydraulics", hydraulic_digest
                ),
                diffusivity_history=diffusivity,
                single_phase_pipe_region_reviewed=True,
                provider_state_and_time_alignment_reviewed=True,
                turbulent_flow_and_local_shear_reviewed=True,
                property_species_temperature_solvent_match_reviewed=True,
                area_basis_and_left_held_integration_reviewed=True,
                correlation_scope_and_exponent_reviewed=True,
            ),
        )
        transfer[species_id] = value.model_dump(mode="json")
    inventories = []
    exchanges = []
    for species_id, concentration in (("Fe2+", 0.1), ("OH-", 0.2)):
        record = dict(
            species_id=species_id,
            bulk_inventory_mol=concentration * 0.001,
            wall_inventory_mol=concentration * 1e-5,
        )
        digest = canonical_digest(record)
        record.update(record_sha256=digest, evidence=[evidence("authored-finite-stock", digest)])
        inventories.append(record)
        record = dict(
            species_id=species_id,
            start_time_s=0.0,
            end_time_s=1.0,
            bulk_inventory_change_mol=0.0,
            wall_inventory_change_mol=0.0,
        )
        digest = canonical_digest(record)
        record.update(record_sha256=digest, evidence=[evidence("authored-closed-boundary", digest)])
        exchanges.append(record)
    result["integration.wet_co2_finite_inventory_electrode_mixed_potential"] = dict(
        assessment_id=assessment,
        geometry_result=geometry_result.model_dump(mode="json"),
        transfer_capacity_results=transfer,
        species=[
            dict(species_id="Fe2+", charge_number=2, elemental_composition={"Fe": 1.0}),
            dict(species_id="OH-", charge_number=-1, elemental_composition={"O": 1.0, "H": 1.0}),
        ],
        initial_inventories=inventories,
        volume_history=[dict(time_s=time, bulk_volume_m3=0.001, wall_volume_m3=1e-5) for time in (0.0, 1.0)],
        intervals=[
            dict(
                start_time_s=0.0,
                end_time_s=1.0,
                reactions=[
                    dict(
                        kinetics=reaction,
                        metal_element_release_mol_per_extent={"Fe": 1.0},
                        evidence=[evidence("authored-kinetics", reaction["calibration_sha256"])],
                    )
                    for reaction in spatial["knots"][0]["reactions"]
                ],
            )
        ],
        external_exchanges=exchanges,
        finite_reservoir_and_current_area_reviewed=True,
        reaction_formula_charge_and_direction_reviewed=True,
        well_mixed_bulk_and_wall_compartments_reviewed=True,
    )
    digest = canonical_digest({"description": "toy scale and electrode coefficients"})
    branch = dict(
        equilibrium_potential_V=0.0,
        exchange_current_density_A_m2=0.001,
        electron_count=2,
        anodic_transfer_coefficient=0.5,
        cathodic_transfer_coefficient=0.5,
    )
    knot = dict(
        knot_id="steady",
        time_s=0.0,
        temperature_K=298.15,
        scale_thickness_m=1e-5,
        cell_count=2,
        effective_diffusivity_m2_s=1e-9,
        first_order_scale_sink_rate_s=0.0,
        bulk_reactant_concentration_mol_m3=1.0,
        reference_reactant_concentration_mol_m3=1.0,
        reactant_species_id="toy-reactant",
        potential_reference_id="toy-reference",
        potential_lower_V=-0.1,
        potential_upper_V=0.1,
        anodic_branches=[
            branch
            | dict(
                reaction_id="oxidation",
                metal_atoms_per_reaction_extent=1.0,
                metal_molar_mass_kg_mol=0.055845,
                metal_density_kg_m3=7850.0,
            )
        ],
        cathodic_branches=[
            branch
            | dict(
                reaction_id="reduction",
                reactant_species_id="toy-reactant",
                reactant_moles_per_reaction_extent=1.0,
            )
        ],
        transport_provider_id="authored-scale",
        transport_provider_revision="1",
        transport_configuration_sha256=digest,
        electrode_provider_id="authored-electrode",
        electrode_provider_revision="1",
        electrode_configuration_sha256=digest,
        transport_evidence=[evidence("authored-scale", digest)],
        electrode_evidence=[evidence("authored-electrode", digest)],
        potential_support_and_branch_signs_reviewed=True,
    )
    result["integration.wet_co2_scale_diffusion_electrode_mixed_potential"] = dict(
        assessment_id="toy-scale-electrode",
        asset_id="toy-asset",
        location_id="toy-location",
        physical_scope_id="toy-volume",
        condition_id="toy-condition",
        knots=[knot],
        fixed_geometry_patch_reviewed=True,
        finite_volume_and_first_order_sink_reviewed=True,
        common_metal_potential_and_no_ohmic_drop_reviewed=True,
        steady_state_at_each_knot_reviewed=True,
        computational_use_authorized=True,
    )
    for model, payload in result.items():
        registry._models[model].input_type.model_validate_json(json.dumps(payload))
    return result
