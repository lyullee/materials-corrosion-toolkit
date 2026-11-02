from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from matintegrity.crevice_component_state_bdf import (
    CellAqueousEquilibriumTemplate,
    ComponentInventoryByCell,
    CreviceComponentStateBDFRequest,
    SpeciesFaceDiffusivity,
    solve_crevice_component_state_bdf,
)
from matintegrity.crevice_bdf_kinetic_phase_set import (
    CreviceBDFInitialSolidInventory,
    CreviceBDFKineticPhaseSet,
)
from matintegrity.crevice_nucleation_kinetic_history import (
    CreviceMolarNucleationLaw,
    EvidenceBoundSaturationGrowthLaw,
)
from matintegrity.multiphase_kinetic_ledger import SolidSaturationRateLaw
from test_crevice_coupled_phase_chemistry import template as aqueous_template


def synthetic_evidence(source_id, digest, citation):
    return Evidence(
        source_id=source_id,
        origin="synthetic",
        citation=citation,
        license_id="synthetic-example-only",
        sha256=digest,
    )


def aqueous_cell(cell_id):
    raw = aqueous_template().model_dump(mode="python")
    system = raw["aqueous_activity_request"]["system"]
    formulas = {"H": {"H": 1}, "OH": {"H": 1, "O": 1}, "Na": {"Na": 1}}
    for species in system["species"]:
        species["elemental_composition"] = formulas[species["species_id"]]
    system["species"] = tuple(system["species"]) + (
        {
            "species_id": "water",
            "charge_number": 0,
            "activity_coefficient": 1.0,
            "initial_activity": 1.0,
            "elemental_composition": {"H": 2, "O": 1},
        },
        {"species_id": "Cl", "charge_number": -1, "activity_coefficient": 1.0,
         "initial_activity": 1e-3, "elemental_composition": {"Cl": 1}},
    )
    reaction = system["reactions"][0]
    reaction["terms"] = tuple(reaction["terms"]) + ({"species_id": "water", "coefficient": -1.0},)
    system["constraints"] = tuple(system["constraints"]) + (
        {"constraint_id": "chloride", "target_mol_L": 0.001, "residual_scale_mol_L": 0.001,
         "terms": ({"species_id": "Cl", "coefficient": 1.0},)},
        {"constraint_id": "solvent", "target_mol_L": 1.0, "residual_scale_mol_L": 1.0,
         "terms": ({"species_id": "water", "coefficient": 1.0},)},
    )
    charge = next(row for row in system["constraints"] if row["constraint_id"] == "charge")
    charge["terms"] = tuple(charge["terms"]) + ({"species_id": "Cl", "coefficient": -1.0},)
    system["elemental_formula_and_reaction_balance_reviewed"] = True
    raw["cell_id"] = cell_id
    raw["constraint_roles"] = tuple(raw["constraint_roles"]) + (
        {"constraint_id": "chloride", "role": "conserved_component", "component_id": "Cl"},
        {"constraint_id": "solvent", "role": "fixed_target"},
    )
    raw["conserved_components"] = tuple(raw["conserved_components"]) + (
        {"component_id": "Cl", "species_coefficients": ({"species_id": "Cl", "coefficient": 1.0},)},
    )
    return CellAqueousEquilibriumTemplate.model_validate(raw)


def phase_set(cell_id, time_s):
    ksp_record_digest = canonical_digest({"synthetic_ksp": 1e-8, "phase": "NaCl(s)"})
    phase_payload = {
        "solid_species_id": "NaCl(s)",
        "solid_elemental_composition": {"Na": 1, "Cl": 1},
        "aqueous_reactant_stoichiometry": {"Na": 1.0, "Cl": 1.0},
        "initial_solid_moles_per_solution_volume_mol_m3": 0.0,
        "dimensionless_solubility_product": 1e-8,
        "equilibrium_constant_record_id": "synthetic-ksp-record",
        "equilibrium_constant_record_sha256": ksp_record_digest,
    }
    phase_digest = canonical_digest(phase_payload)
    phase = CreviceCompetingSolidPhase(
        **phase_payload,
        record_sha256=phase_digest,
        evidence=(
            synthetic_evidence("synthetic-phase", phase_digest, "Authored NaCl phase record"),
            synthetic_evidence("synthetic-ksp-record", ksp_record_digest, "Authored Ksp fixture"),
        ),
    )

    nucleation_payload = {
        "solid_species_id": "NaCl(s)",
        "critical_saturation_ratio": 2.0,
        "source_rate_constant_mol_m3_s": 0.01,
        "supersaturation_order": 1.0,
        "nucleated_inventory_threshold_mol_m3": 0.001,
        "maximum_rate_mol_m3_s": 1.0,
    }
    nucleation_digest = canonical_digest(nucleation_payload)
    nucleation = CreviceMolarNucleationLaw(
        **nucleation_payload,
        source_sha256=nucleation_digest,
        evidence=(synthetic_evidence("synthetic-nucleation", nucleation_digest, "Authored nucleation fixture"),),
    )
    growth_digest = "a" * 64
    growth = EvidenceBoundSaturationGrowthLaw(
        law=SolidSaturationRateLaw(
            solid_species_id="NaCl(s)",
            precipitation_rate_constant_mol_m3_s=0.01,
            precipitation_order=1.0,
            dissolution_rate_constant_mol_m3_s=0.01,
            dissolution_order=1.0,
            source_sha256=growth_digest,
        ),
        evidence=(synthetic_evidence("synthetic-growth", growth_digest, "Authored growth fixture"),),
    )
    base = CreviceBDFKineticPhaseSet.model_construct(
        assessment_id="synthetic-bdf-kinetics",
        asset_id="synthetic-asset",
        location_id=f"location-{cell_id}",
        physical_scope_id="synthetic-scope",
        cell_id=cell_id,
        phase_set_id=f"phase-set-{cell_id}",
        clock_id="synthetic-clock",
        valid_time_s=time_s,
        temperature_K=298.15,
        phase_candidates=(phase,),
        initial_solid_inventory_by_phase=(CreviceBDFInitialSolidInventory(
            solid_species_id="NaCl(s)", initial_solid_moles_mol=0.0),),
        nucleation_laws=(nucleation,),
        growth_laws=(growth,),
        phase_set_sha256="0" * 64,
        evidence=(),
    )
    digest = canonical_digest(base.model_dump(mode="json", exclude={"phase_set_sha256", "evidence"}))
    return CreviceBDFKineticPhaseSet.model_validate({
        **base.model_dump(mode="python", exclude={"phase_set_sha256", "evidence"}),
        "phase_set_sha256": digest,
        "evidence": (synthetic_evidence("synthetic-phase-set", digest, "Authored exact-clock phase set"),),
    })


def build_synthetic_request():
    time_s = (0.0, 0.003, 0.005)
    cells = (aqueous_cell("left"), aqueous_cell("right"))
    request = CreviceComponentStateBDFRequest(
        schema_version="matintegrity.crevice_component_state_bdf.v6",
        assessment_id="synthetic-bdf-kinetics",
        time_s=time_s,
        cells=cells,
        initial_component_inventory=(
            ComponentInventoryByCell(component_id="Na", inventory_mol_by_cell=(0.001, 0.001)),
            ComponentInventoryByCell(component_id="Cl", inventory_mol_by_cell=(0.001, 0.001)),
        ),
        kinetic_phase_sets_by_cell=(phase_set("left", time_s), phase_set("right", time_s)),
        kinetic_phase_mode_reviewed=True,
        total_component_inventory_includes_solid_reviewed=True,
        interior_face_area_m2=(1e-6,),
        center_distance_m_by_interior_face=(0.01,),
        species_face_diffusivity=tuple(
            SpeciesFaceDiffusivity(species_id=sid, diffusivity_m2_s_by_interior_face=(1e-9,))
            for sid in ("H", "OH", "Na", "water", "Cl")
        ),
        relative_tolerance=1e-4,
        absolute_solid_inventory_tolerance_mol=1e-12,
        maximum_step_s=0.005,
        component_state_and_flux_basis_reviewed=True,
        cell_equilibrium_templates_and_evidence_reviewed=True,
        fixed_volume_and_boundary_scope_reviewed=True,
        computational_use_authorized=True,
    )

    return request


def test_schema_v6_bdf_commits_same_stage_kinetic_seed_event_and_ledgers():
    request = build_synthetic_request()
    result = solve_crevice_component_state_bdf(request)

    assert result.status == "computed", result.values
    assert result.values["kinetic_phase_mode_enabled"] is True
    transitions = result.values["kinetic_event_policy"]["seed_transitions"]
    assert [row["cell_id"] for row in transitions] == ["left", "right"]
    assert transitions[0]["time_s"] == transitions[1]["time_s"]
    solid_history = result.values["solid_phase_inventory_mol_by_cell_phase_time"]
    assert solid_history["left"]["NaCl(s)"][-1] > 0.0
    assert solid_history["right"]["NaCl(s)"][-1] > 0.0
    assert result.values["maximum_normalized_component_closure_residual"] <= 1.0
