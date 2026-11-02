import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.surface_examination import (
    LiquidPenetrantExamination,
    MagneticParticleExamination,
    liquid_penetrant_summary,
    magnetic_particle_summary,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "user-surface-examination",
    "origin": "user_declared",
    "citation": "caller-controlled examination record",
}
AREAS = [
    {
        "area_id": "area-a",
        "physical_location_id": "weld-a",
        "target_area_m2": 1.0,
        "examined_area_m2": 0.75,
        "unexamined_basis": "support footprint",
    }
]
INDICATIONS = [
    {
        "indication_id": "indication-1",
        "area_id": "area-a",
        "physical_location_id": "weld-a-clock-3",
        "reported_indication_type": "linear indication",
        "location_description": "caller datum plus 0.2 m",
        "measured_length_m": 0.008,
        "evidence": [EVIDENCE],
    }
]


def _penetrant(**updates):
    values = {
        "examination_id": "pt-001",
        "procedure_id": "user-pt-procedure",
        "procedure_revision": "2",
        "penetrant_type": "visible",
        "removal_method": "solvent_removable",
        "cleaner_batch_id": "cleaner-1",
        "penetrant_batch_id": "penetrant-1",
        "remover_or_emulsifier_batch_id": "remover-1",
        "developer_batch_id": "developer-1",
        "surface_material_id": "material-1",
        "surface_condition": "clean dry surface",
        "precleaning_basis": "caller-controlled preclean record",
        "drying_basis": "caller-controlled drying record",
        "examination_temperature_K": 295.15,
        "penetrant_dwell_s": 600.0,
        "excess_removal_basis": "caller-controlled removal record",
        "developer_application_basis": "caller-controlled developer record",
        "development_time_s": 600.0,
        "observation_lighting_basis": "caller-controlled lighting record",
        "final_cleaning_basis": "caller-controlled final cleaning record",
        "areas": AREAS,
        "indications": INDICATIONS,
        "areas_mutually_exclusive_reviewed": True,
        "material_and_consumables_compatibility_reviewed": True,
        "process_sequence_reviewed": True,
        "temperature_and_times_reviewed": True,
        "surface_condition_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": False,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return values


def _magnetic(**updates):
    values = {
        "examination_id": "mt-001",
        "procedure_id": "user-mt-procedure",
        "procedure_revision": "4",
        "surface_material_id": "ferromagnetic-material-1",
        "surface_condition": "clean dry surface",
        "particle_medium": "wet_fluorescent",
        "particle_batch_id": "particles-1",
        "carrier_batch_id": "carrier-1",
        "observation_lighting_basis": "caller-controlled lighting record",
        "minimum_direction_separation_rad": math.pi / 3,
        "directional_coverage_requirement_basis": "caller-approved directional requirement",
        "areas": AREAS,
        "magnetization_passes": [
            {
                "pass_id": "pass-0",
                "area_id": "area-a",
                "technique": "yoke",
                "current_mode": "ac",
                "field_direction_rad": 0.0,
                "field_adequacy_basis": "caller-controlled field indicator record",
                "equipment_id": "yoke-1",
            },
            {
                "pass_id": "pass-90",
                "area_id": "area-a",
                "technique": "yoke",
                "current_mode": "ac",
                "field_direction_rad": math.pi / 2,
                "field_adequacy_basis": "caller-controlled field indicator record",
                "equipment_id": "yoke-1",
            },
        ],
        "indications": INDICATIONS,
        "areas_mutually_exclusive_reviewed": True,
        "ferromagnetic_applicability_reviewed": True,
        "equipment_and_media_reviewed": True,
        "field_adequacy_reviewed": True,
        "directional_requirement_reviewed": True,
        "surface_condition_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": False,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return values


def test_penetrant_summary_preserves_process_and_coverage_without_acceptance():
    result = liquid_penetrant_summary(LiquidPenetrantExamination.model_validate(_penetrant()))
    assert result.status == "computed"
    assert result.values["coverage_fraction"] == pytest.approx(0.75)
    assert result.values["penetrant_dwell_s"] == 600.0
    assert result.values["indication_count"] == 1
    assert not any("accept" in key for key in result.values)


def test_penetrant_negative_record_and_review_gates_are_explicit():
    negative = liquid_penetrant_summary(LiquidPenetrantExamination.model_validate(_penetrant(indications=[])))
    assert negative.status == "needs_data"
    reviewed = liquid_penetrant_summary(
        LiquidPenetrantExamination.model_validate(_penetrant(indications=[], negative_result_reviewed=True))
    )
    assert reviewed.status == "computed"
    pending = liquid_penetrant_summary(
        LiquidPenetrantExamination.model_validate(_penetrant(process_sequence_reviewed=False))
    )
    assert pending.status == "needs_data"
    assert pending.values["missing_reviews"] == ["process_sequence_reviewed"]


def test_magnetic_particle_direction_coverage_uses_unoriented_angle():
    result = magnetic_particle_summary(MagneticParticleExamination.model_validate(_magnetic()))
    assert result.status == "computed"
    assert result.values["maximum_unoriented_direction_separation_rad_by_area"]["area-a"] == pytest.approx(
        math.pi / 2
    )
    reversed_field = _magnetic()
    reversed_field["magnetization_passes"][1]["field_direction_rad"] = math.pi - 0.1
    result = magnetic_particle_summary(MagneticParticleExamination.model_validate(reversed_field))
    assert result.status == "needs_data"
    assert result.values["maximum_unoriented_direction_separation_rad_by_area"]["area-a"] == pytest.approx(
        0.1
    )
    assert result.values["insufficient_direction_area_ids"] == ["area-a"]


def test_magnetic_particle_missing_area_pass_is_needs_data():
    values = _magnetic(
        areas=[
            *AREAS,
            {
                "area_id": "area-b",
                "physical_location_id": "weld-b",
                "target_area_m2": 0.5,
                "examined_area_m2": 0.5,
            },
        ]
    )
    result = magnetic_particle_summary(MagneticParticleExamination.model_validate(values))
    assert result.status == "needs_data"
    assert result.values["magnetization_pass_count_by_area"]["area-b"] == 0
    assert result.values["insufficient_direction_area_ids"] == ["area-b"]


@pytest.mark.parametrize(
    ("factory", "updates"),
    [
        (_penetrant, {"areas": [{**AREAS[0], "examined_area_m2": 1.1}]}),
        (_penetrant, {"indications": [{**INDICATIONS[0], "area_id": "unknown"}]}),
        (
            _magnetic,
            {
                "magnetization_passes": [
                    {
                        **_magnetic()["magnetization_passes"][0],
                        "area_id": "unknown",
                    }
                ]
            },
        ),
        (
            _magnetic,
            {
                "magnetization_passes": [
                    _magnetic()["magnetization_passes"][0],
                    _magnetic()["magnetization_passes"][0],
                ]
            },
        ),
    ],
)
def test_surface_contracts_reject_geometry_and_identity_errors(factory, updates):
    contract = LiquidPenetrantExamination if factory is _penetrant else MagneticParticleExamination
    with pytest.raises(ValidationError):
        contract.model_validate(factory(**updates))


@pytest.mark.parametrize(
    ("model_id", "factory", "source_id"),
    [
        (
            "inspection.liquid_penetrant_summary",
            _penetrant,
            "liquid_penetrant_examination_definition",
        ),
        (
            "inspection.magnetic_particle_summary",
            _magnetic,
            "magnetic_particle_examination_definition",
        ),
    ],
)
def test_registry_routes_have_no_probability_semantics(model_id, factory, source_id):
    result = default_registry().run(
        model_id,
        factory(),
        RunContext(asset_id="asset-1", location_id="weld-a", time_basis="campaign-1"),
    )
    assert result.status == "computed"
    assert result.source_ids == (source_id,)
    assert result.probability_semantics == {}
