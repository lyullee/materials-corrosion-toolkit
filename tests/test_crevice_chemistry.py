import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.crevice_chemistry import (
    CreviceSpeciesInventoryHistory,
    crevice_species_inventory_history,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def payload(**updates):
    value = {
        "history_id": "crevice-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "physical_scope_id": "crevice-cell-1",
        "clock_id": "clock-1",
        "material_condition_id": "material-1",
        "bulk_solution_id": "solution-1",
        "elapsed_time_s": (0.0, 10.0, 30.0),
        "crevice_solution_volume_m3": (1e-6, 1e-6, 2e-6),
        "species": (
            {
                "species_id": "cation",
                "charge_number": 1,
                "initial_amount_mol": 1e-3,
                "species_definition": "authored monovalent cation",
                "evidence": (EVIDENCE,),
            },
            {
                "species_id": "anion",
                "charge_number": -1,
                "initial_amount_mol": 1e-3,
                "species_definition": "authored monovalent anion",
                "evidence": (EVIDENCE,),
            },
        ),
        "rate_intervals": (
            {
                "interval_id": "i-1",
                "support_id": "support-1",
                "temperature_K": 300.0,
                "gap_m": 1e-4,
                "net_species_source_mol_s": {"cation": 1e-6, "anion": 1e-6},
                "provider_record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "interval_id": "i-2",
                "support_id": "support-1",
                "temperature_K": 310.0,
                "gap_m": 1e-4,
                "boundary_condition_jump_reviewed": True,
                "net_species_source_mol_s": {"cation": 2e-6, "anion": 2e-6},
                "provider_record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "rate_supports": (
            {
                "support_id": "support-1",
                "material_condition_id": "material-1",
                "bulk_solution_id": "solution-1",
                "minimum_temperature_K": 290.0,
                "maximum_temperature_K": 320.0,
                "minimum_gap_m": 5e-5,
                "maximum_gap_m": 2e-4,
                "rate_provider_id": "provider-1",
                "rate_provider_version": "1",
                "rate_provider_state_digest": DIGEST_A,
                "supported_species_ids": ("cation", "anion"),
                "maximum_absolute_charge_imbalance_mol_charge": 1e-12,
                "calibration_basis": "authored provider support",
                "evidence": (EVIDENCE,),
            },
        ),
        "geometry_and_volume_history_reviewed": True,
        "material_and_bulk_solution_identity_reviewed": True,
        "species_definitions_and_initial_inventory_reviewed": True,
        "temperature_and_gap_history_reviewed": True,
        "rate_provider_and_calibration_reviewed": True,
        "clock_and_interval_alignment_reviewed": True,
        "charge_balance_tolerance_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CreviceSpeciesInventoryHistory(**value)


def test_balanced_species_inventory_and_prescribed_volume():
    result = crevice_species_inventory_history(payload())
    assert result.status == "computed"
    amounts = result.values["species_amount_history_mol"]
    assert amounts["cation"][-1] == pytest.approx(1.05e-3)
    assert result.values["species_concentration_history_mol_m3"]["cation"][-1] == pytest.approx(525.0)
    assert result.values["charge_balance_within_caller_tolerance"] is True


def test_outside_support_and_negative_inventory_are_not_extrapolated_or_clipped():
    assessment = payload()
    outside = assessment.rate_intervals[0].model_copy(update={"temperature_K": 330.0})
    assert (
        crevice_species_inventory_history(
            assessment.model_copy(update={"rate_intervals": (outside, assessment.rate_intervals[1])})
        ).status
        == "out_of_scope"
    )
    negative = assessment.rate_intervals[0].model_copy(
        update={"net_species_source_mol_s": {"cation": -1.0, "anion": -1.0}}
    )
    result = crevice_species_inventory_history(
        assessment.model_copy(update={"rate_intervals": (negative, assessment.rate_intervals[1])})
    )
    assert result.status == "out_of_scope"
    assert result.values["negative_inventory_records"]


def test_charge_imbalance_or_missing_review_needs_data():
    assessment = payload()
    unbalanced = assessment.rate_intervals[0].model_copy(
        update={"net_species_source_mol_s": {"cation": 1e-6, "anion": 0.0}}
    )
    result = crevice_species_inventory_history(
        assessment.model_copy(update={"rate_intervals": (unbalanced, assessment.rate_intervals[1])})
    )
    assert result.status == "needs_data"
    assert result.values["charge_balance_within_caller_tolerance"] is False
    assert (
        crevice_species_inventory_history(payload(rate_provider_and_calibration_reviewed=False)).status
        == "needs_data"
    )


def test_species_completeness_and_context_identity_are_enforced():
    assessment = payload()
    with pytest.raises(ValueError, match="exactly every"):
        assessment.model_copy(
            update={
                "rate_intervals": (
                    assessment.rate_intervals[0].model_copy(
                        update={"net_species_source_mol_s": {"cation": 1e-6}}
                    ),
                    assessment.rate_intervals[1],
                )
            }
        ).model_validate(
            assessment.model_copy(
                update={
                    "rate_intervals": (
                        assessment.rate_intervals[0].model_copy(
                            update={"net_species_source_mol_s": {"cation": 1e-6}}
                        ),
                        assessment.rate_intervals[1],
                    )
                }
            ).model_dump()
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.crevice_species_inventory_history",
            assessment,
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
