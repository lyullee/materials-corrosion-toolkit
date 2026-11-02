import json
import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.davies_activity import (
    DaviesActivityCoefficientInput,
    davies_activity_coefficients,
    specifications,
)
from matintegrity.registry import default_registry

EVIDENCE = {"source_id": "synthetic-davies-fixture", "origin": "synthetic", "citation": "Authored fixture"}
DIGEST = "c" * 64
CONTEXT = RunContext(asset_id="asset", location_id="solution", time_basis="sample instant")


def payload(**updates):
    data = {
        "assessment_id": "davies-1",
        "solution_id": "brine-1",
        "temperature_K": 298.15,
        "ionic_strength_limit_mol_kg": 0.5,
        "davies_A_at_temperature": 0.5,
        "A_provider_id": "caller-property-provider",
        "A_provider_revision": "1",
        "A_configuration_digest": DIGEST,
        "A_record_digest": DIGEST,
        "charge_balance_absolute_tolerance_mol_kg": 1e-12,
        "species": (
            {"species_id": "sodium", "species_label": "Na+", "charge_number": 1, "molality_mol_kg": 0.1},
            {"species_id": "chloride", "species_label": "Cl-", "charge_number": -1, "molality_mol_kg": 0.1},
            {
                "species_id": "carbon-dioxide",
                "species_label": "CO2*",
                "charge_number": 0,
                "molality_mol_kg": 0.02,
            },
        ),
        "complete_ionic_inventory_reviewed": True,
        "charge_balance_reviewed": True,
        "ionic_strength_convention_reviewed": True,
        "davies_scope_reviewed": True,
        "temperature_solvent_A_lineage_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    data.update(updates)
    data["species"] = tuple(data["species"])
    return data


def test_davies_coefficients_match_equation_and_report_dimensionless_activity():
    result = default_registry().run("chemistry.davies_activity_coefficients", payload(), CONTEXT)
    ionic_strength = 0.1
    term = math.sqrt(ionic_strength) / (1 + math.sqrt(ionic_strength)) - 0.3 * ionic_strength
    expected = 10 ** (-0.5 * term)
    assert result.status == "computed"
    assert result.values["ionic_strength_mol_kg"] == pytest.approx(ionic_strength)
    assert result.values["charge_balance_residual_mol_kg"] == pytest.approx(0.0)
    assert result.values["species"][0]["activity_coefficient"] == pytest.approx(expected)
    assert result.values["species"][0]["dimensionless_activity"] == pytest.approx(0.1 * expected)
    assert result.values["species"][2]["activity_coefficient"] == pytest.approx(1.0)
    assert result.values["species"][2]["neutral_gamma_convention"] == "unity"


def test_charge_imbalance_and_declared_ionic_strength_scope_are_not_silently_used():
    imbalanced = payload(species=[payload()["species"][0]])
    result = davies_activity_coefficients(DaviesActivityCoefficientInput.model_validate(imbalanced))
    assert result.status == "needs_data"
    assert result.values["out_of_scope_reason"] == "charge_balance_tolerance_exceeded"

    too_concentrated = payload(ionic_strength_limit_mol_kg=0.05)
    result = davies_activity_coefficients(DaviesActivityCoefficientInput.model_validate(too_concentrated))
    assert result.status == "out_of_scope"
    assert result.values["out_of_scope_reason"] == "ionic_strength_exceeds_declared_davies_limit"


def test_davies_limit_cannot_be_extended_past_classic_declared_domain():
    with pytest.raises(ValidationError, match="less than or equal to 0.5"):
        DaviesActivityCoefficientInput.model_validate(payload(ionic_strength_limit_mol_kg=0.5001))


def test_missing_review_and_duplicate_species_identity_are_explicit():
    data = payload(davies_scope_reviewed=False)
    result = davies_activity_coefficients(DaviesActivityCoefficientInput.model_validate(data))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["davies_scope_reviewed"]

    data = payload(species=[payload()["species"][0], payload()["species"][0]])
    with pytest.raises(ValidationError, match="identifiers must be unique"):
        DaviesActivityCoefficientInput.model_validate(data)


def test_davies_contract_registers_public_source_and_units():
    spec = specifications()[0]
    assert spec.model_id == "chemistry.davies_activity_coefficients"
    assert spec.source_ids == (
        "usgs_phreeqc_davies_activity_coefficients",
        "usgs_davies_ionic_strength_approximation",
    )
    assert spec.units["species.activity_coefficient"] == "1"
