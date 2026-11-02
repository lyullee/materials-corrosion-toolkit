import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.component_material_class import (
    ComponentMaterialClassAssessment,
    ComponentMaterialRequirement,
    MaterialClassComponentRecord,
    component_material_class_assessment,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        class_id="profile",
        class_revision="1",
        governing_requirement_id="authored",
        asset_id="asset",
        location_id="location",
        physical_scope_id="assembly",
        service_id="service",
        allowed_service_ids=("service",),
        requirements=(
            ComponentMaterialRequirement(
                component_role="body",
                allowed_material_condition_ids=("cast-state",),
                required_attributes={"form": "casting"},
                maximum_count=1,
            ),
        ),
        components=(
            MaterialClassComponentRecord(
                component_id="body-1",
                component_role="body",
                physical_scope_id="assembly",
                material_condition_id="cast-state",
                attributes={"form": "casting"},
                source_id="authored",
                record_sha256="a" * 64,
            ),
        ),
        profile_authority_and_component_mapping_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        ComponentMaterialClassAssessment.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return ComponentMaterialClassAssessment(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored exact-label profile.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_no_dummy_pressure_or_corrosion_quantities():
    result = component_material_class_assessment(request())
    assert result.status == "computed"
    assert result.values["declared_component_class_outcome"] == "satisfied"


@pytest.mark.parametrize(
    "changes,status,outcome",
    [
        ({"material_condition_id": "wrought-state"}, "computed", "not_satisfied"),
        ({"material_condition_id": None}, "needs_data", "unknown"),
        ({"attributes": {}}, "needs_data", "unknown"),
        ({"attributes": {"form": "forging"}}, "computed", "not_satisfied"),
        ({"component_role": "unmapped"}, "needs_data", "unknown"),
    ],
)
def test_exact_identity_and_missingness(changes, status, outcome):
    component = request().components[0].model_copy(update=changes)
    result = component_material_class_assessment(request(components=(component,)))
    assert result.status == status
    assert result.values["declared_component_class_outcome"] == outcome


def test_missing_and_optional_roles():
    assert component_material_class_assessment(request(components=())).status == "needs_data"
    rule = request().requirements[0].model_copy(update={"minimum_count": 0})
    assert (
        component_material_class_assessment(request(components=(), requirements=(rule,))).values[
            "declared_component_class_outcome"
        ]
        == "satisfied"
    )


def test_excess_count_and_duplicate_identity():
    first = request().components[0]
    second = first.model_copy(update={"component_id": "body-2"})
    result = component_material_class_assessment(request(components=(first, second)))
    assert result.status == "computed"
    assert result.values["declared_component_class_outcome"] == "not_satisfied"
    with pytest.raises(ValueError, match="unique"):
        request(components=(first, first))


def test_service_and_authority():
    assert component_material_class_assessment(request(service_id="other")).status == "out_of_scope"
    assert (
        component_material_class_assessment(
            request(profile_authority_and_component_mapping_reviewed=False)
        ).status
        == "needs_data"
    )


def test_scope_and_duplicate_role_rejected():
    with pytest.raises(ValueError, match="physical scope"):
        request(components=(request().components[0].model_copy(update={"physical_scope_id": "other"}),))
    rule = request().requirements[0]
    with pytest.raises(ValueError, match="unique"):
        request(requirements=(rule, rule))


def test_python_json_and_context():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    model = "materials.component_material_class_assessment"
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
    with pytest.raises(ValueError, match="context"):
        registry.run(model, x.model_dump(), context.model_copy(update={"asset_id": "other"}))
