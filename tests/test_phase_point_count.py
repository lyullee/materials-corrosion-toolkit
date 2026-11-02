import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.phase_point_count import (
    PhasePointCountField,
    PhasePointCountSummary,
    phase_point_count_summary,
)
from matintegrity.registry import default_registry


def field(name="one", a=30, b=70, unknown=0):
    return PhasePointCountField(
        field_id=name,
        image_id=name,
        image_sha256=("a" if name == "one" else "b") * 64,
        coordinate_frame_id="frame",
        grid_record_sha256="c" * 64,
        physical_specimen_id="specimen",
        total_test_points=a + b + unknown,
        phase_counts={"alpha": a, "beta": b},
        unresolved_points=unknown,
    )


def request(**updates):
    raw = dict(
        survey_id="survey",
        physical_specimen_id="specimen",
        material_condition_id="condition",
        phase_definition_id="authored-labels",
        counting_procedure_revision_id="authored-1",
        phase_ids=("alpha", "beta"),
        fields=(field(),),
        point_identity_and_nonoverlap_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        PhasePointCountSummary.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return PhasePointCountSummary(
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
                    citation="Authored count fixture",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_point_weighted_pooling_not_equal_field_mean():
    result = phase_point_count_summary(request(fields=(field(), field("two", a=9, b=1))))
    assert result.status == "computed"
    pooled = result.values["pooled_point_summary"]
    assert pooled["phase_counts"] == {"alpha": 39, "beta": 71}
    assert pooled["observed_phase_point_fractions"]["alpha"] == pytest.approx(39 / 110)


def test_unresolved_points_remain_in_denominator_and_bounds():
    result = phase_point_count_summary(request(fields=(field(a=20, b=60, unknown=20),)))
    assert result.status == "needs_data"
    pooled = result.values["pooled_point_summary"]
    assert pooled["observed_phase_point_fractions"] == {"alpha": 0.2, "beta": 0.6}
    assert pooled["phase_fraction_identification_bounds"] == {"alpha": [0.2, 0.4], "beta": [0.6, 0.8]}


def test_unreviewed_nonoverlap_withholds_pool_but_preserves_fields():
    result = phase_point_count_summary(request(point_identity_and_nonoverlap_reviewed=False))
    assert result.status == "needs_data"
    assert "pooled_point_summary" not in result.values
    assert len(result.values["field_summaries"]) == 1


def test_missing_phase_and_specimen_mismatch_rejected():
    with pytest.raises(ValueError, match="every declared phase"):
        request(fields=(field().model_copy(update={"phase_counts": {"alpha": 100}}),))
    with pytest.raises(ValueError, match="physical specimen"):
        request(fields=(field().model_copy(update={"physical_specimen_id": "other"}),))


def test_renamed_duplicate_grid_cannot_double_count():
    second = field().model_copy(update={"field_id": "renamed", "coordinate_frame_id": "renamed-frame"})
    with pytest.raises(ValueError, match="duplicate image/grid"):
        request(fields=(field(), second))


def test_count_balance_and_integer_types():
    raw = field().model_dump()
    raw["total_test_points"] = 101
    with pytest.raises(ValueError, match="all test points"):
        PhasePointCountField(**raw)
    raw = field().model_dump()
    raw["phase_counts"]["alpha"] = 30.5
    with pytest.raises(ValueError):
        PhasePointCountField(**raw)


def test_registry_python_json_exchange_and_digest():
    x = request()
    registry = default_registry()
    model = "testing.phase_point_count_summary"
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
    raw = x.model_dump()
    raw["phase_definition_id"] = "other"
    with pytest.raises(ValueError, match="pin the complete"):
        PhasePointCountSummary(**raw)
