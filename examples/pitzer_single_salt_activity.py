"""Synthetic contract example for a single-salt Pitzer activity calculation."""

from matintegrity.models.pitzer_single_salt import PitzerSingleSaltActivity, pitzer_single_salt_activity

record_sha256 = "a" * 64
request = PitzerSingleSaltActivity.model_validate({
    "assessment_id": "synthetic-pitzer-salt-example",
    "salt_id": "synthetic-monovalent-salt",
    "cation_id": "X+",
    "anion_id": "Y-",
    "cation_charge_number": 1,
    "anion_charge_number": -1,
    "cation_stoichiometric_number": 1,
    "anion_stoichiometric_number": 1,
    "salt_molality_mol_kg_water": 0.5,
    "temperature_K": 298.15,
    "parameter_temperature_K": 298.15,
    "temperature_match_tolerance_K": 0.01,
    "maximum_supported_ionic_strength_mol_kg": 1.0,
    "debye_huckel_A_phi": 0.3,
    "debye_huckel_b_sqrt_kg_mol": 1.2,
    "beta_phi_0_kg_mol": 0.1,
    "beta_phi_1_kg_mol": 0.2,
    "beta_phi_2_kg_mol": 0.0,
    "alpha_1_sqrt_kg_mol": 2.0,
    "alpha_2_sqrt_kg_mol": 12.0,
    "c_phi_kg2_mol2": 0.001,
    "parameter_set_id": "synthetic-unfitted-parameters",
    "parameter_record_id": "not-experimental",
    "parameter_record_sha256": record_sha256,
    "temperature_and_parameter_applicability_reviewed": True,
    "single_pure_electrolyte_scope_reviewed": True,
    "stoichiometry_and_charge_reviewed": True,
    "parameter_values_and_units_reviewed": True,
    "parameter_use_authorized": True,
    "evidence": [{
        "source_id": "synthetic-unfitted-parameters",
        "origin": "synthetic",
        "citation": "Invented coefficients for API wiring only; not a fit or electrolyte data",
        "sha256": record_sha256,
    }],
})
print(pitzer_single_salt_activity(request).model_dump(mode="json"))
