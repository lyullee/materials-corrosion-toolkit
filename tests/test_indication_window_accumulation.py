import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    IndicationWindowAccumulation,
    ProjectedIndicationInterval,
    indication_window_accumulation,
)
from matintegrity.registry import default_registry


def request(intervals=((1.0, 3.0), (5.0, 6.0)), **updates):
    rows = tuple(
        ProjectedIndicationInterval(
            indication_id=str(i), start_m=a, end_m=b, observation_record_digest="a" * 64
        )
        for i, (a, b) in enumerate(intervals)
    )
    raw = dict(
        physical_scope_id="seam",
        coordinate_frame_id="frame",
        coordinate_origin_id="origin",
        examined_length_m=10.0,
        window_length_m=5.0,
        indications=rows,
        overlap_semantics="sum_indication_overlap",
        examined_extent_and_no_gaps_reviewed=True,
        indication_identity_and_projection_reviewed=True,
        overlap_semantics_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        IndicationWindowAccumulation.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return IndicationWindowAccumulation(
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
                    citation="authored interval geometry",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_disjoint_intervals_and_interior_maximizer():
    r = indication_window_accumulation(request())
    assert r.status == "computed"
    assert r.values["maximum_accumulated_length_m"] == 3.0
    assert r.values["representative_window_start_m"] == 1.0
    assert [a["overlap_length_m"] for a in r.values["representative_indication_overlaps"]] == [2.0, 1.0]


@pytest.mark.parametrize("mode,expected", [("sum_indication_overlap", 6.0), ("union_covered_length", 4.0)])
def test_overlap_semantics_are_explicit(mode, expected):
    r = indication_window_accumulation(
        request(((1.0, 4.0), (2.0, 5.0)), window_length_m=4.0, overlap_semantics=mode)
    )
    assert r.values["maximum_accumulated_length_m"] == expected


def test_maximizing_plateau_is_retained():
    r = indication_window_accumulation(request(((1.0, 9.0),), window_length_m=3.0))
    assert r.values["maximum_accumulated_length_m"] == 3.0
    assert r.values["maximizing_start_ranges_m"] == [{"minimum_start_m": 1.0, "maximum_start_m": 6.0}]


def test_empty_observation_list_has_zero_measure_for_all_windows():
    r = indication_window_accumulation(request(()))
    assert r.values["maximum_accumulated_length_m"] == 0.0
    assert r.values["maximizing_start_ranges_m"] == [{"minimum_start_m": 0.0, "maximum_start_m": 5.0}]


def test_full_extent_window_and_touching_union():
    r = indication_window_accumulation(
        request(((0.0, 2.0), (2.0, 4.0)), window_length_m=10.0, overlap_semantics="union_covered_length")
    )
    assert r.values["maximum_accumulated_length_m"] == 4.0
    assert r.values["representative_window_start_m"] == 0.0


def test_missing_projection_review_withholds_accumulation():
    r = indication_window_accumulation(request(indication_identity_and_projection_reviewed=False))
    assert r.status == "needs_data"
    assert "maximum_accumulated_length_m" not in r.values


def test_invalid_extent_and_duplicate_identity_are_rejected():
    with pytest.raises(ValueError, match="extent"):
        request(examined_length_m=4.0)
    x = request()
    with pytest.raises(ValueError, match="unique"):
        request(indications=(x.indications[0], x.indications[0]))


def test_unresolved_window_scale_is_withheld():
    assert (
        indication_window_accumulation(request((), examined_length_m=1e308, window_length_m=1e-300)).status
        == "out_of_scope"
    )


def test_accumulation_overflow_is_withheld():
    assert (
        indication_window_accumulation(
            request(((0.0, 1e308), (0.0, 1e308)), examined_length_m=1e308, window_length_m=1e308)
        ).status
        == "out_of_scope"
    )


def test_digest_pins_overlap_policy():
    raw = request().model_dump()
    raw["overlap_semantics"] = "union_covered_length"
    with pytest.raises(ValueError, match="pin the complete"):
        IndicationWindowAccumulation.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="seam", time_basis="authored")
    a = registry.run("inspection.indication_window_accumulation", x, context)
    b = registry.run_json("inspection.indication_window_accumulation", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
