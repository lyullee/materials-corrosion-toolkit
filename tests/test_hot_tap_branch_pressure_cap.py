import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    HotTapBranchTestPressureCap,
    hot_tap_branch_test_pressure_cap,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        host_component_id="run",
        branch_component_id="branch",
        host_external_capacity_record_id="external-qualified",
        branch_test_limit_record_id="branch-qualified",
        host_operating_pressure_Pa_abs=1e5,
        allowable_host_external_pressure_difference_Pa=2e5,
        branch_test_pressure_limit_Pa_abs=5e5,
        proposed_test_pressure_Pa_abs=3e5,
    )
    raw.update(updates)
    digest = canonical_digest(
        HotTapBranchTestPressureCap.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return HotTapBranchTestPressureCap(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            computational_use_authorized=True,
            applicability_and_units_reviewed=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="authored pressure bounds",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_host_external_differential_governs_at_inclusive_limit():
    r = hot_tap_branch_test_pressure_cap(request())
    assert r.status == "computed"
    assert r.values["maximum_test_pressure_Pa_abs"] == 3e5
    assert r.values["governing_limits"] == ["host_external_differential"]
    assert r.values["proposed_external_pressure_difference_Pa"] == 2e5
    assert r.values["proposed_pressure_within_declared_upper_limits"] is True


def test_branch_limit_and_ties_are_preserved():
    r = hot_tap_branch_test_pressure_cap(request(allowable_host_external_pressure_difference_Pa=5e5))
    assert r.values["maximum_test_pressure_Pa_abs"] == 5e5
    assert r.values["governing_limits"] == ["branch_limit"]
    r = hot_tap_branch_test_pressure_cap(request(allowable_host_external_pressure_difference_Pa=4e5))
    assert r.values["governing_limits"] == ["branch_limit", "host_external_differential"]


def test_upper_limit_exceedance_is_not_a_failed_calculation():
    r = hot_tap_branch_test_pressure_cap(request(proposed_test_pressure_Pa_abs=4e5))
    assert r.status == "computed"
    assert r.values["pressure_cap_margin_Pa"] == -1e5
    assert r.values["proposed_pressure_within_declared_upper_limits"] is False


def test_negative_external_differential_is_not_made_absolute():
    r = hot_tap_branch_test_pressure_cap(
        request(branch_test_pressure_limit_Pa_abs=0.8e5, proposed_test_pressure_Pa_abs=0.8e5)
    )
    assert r.values["proposed_external_pressure_difference_Pa"] == -0.2e5
    assert r.values["maximum_test_pressure_Pa_abs"] == 0.8e5


def test_unused_overflowing_candidate_does_not_corrupt_finite_cap():
    r = hot_tap_branch_test_pressure_cap(
        request(
            host_operating_pressure_Pa_abs=1e308,
            allowable_host_external_pressure_difference_Pa=1e308,
            branch_test_pressure_limit_Pa_abs=1.5e308,
            proposed_test_pressure_Pa_abs=1.5e308,
        )
    )
    assert r.values["maximum_test_pressure_Pa_abs"] == 1.5e308
    assert r.values["proposed_pressure_within_declared_upper_limits"] is True


def test_capacity_tampering_invalidates_digest():
    raw = request().model_dump()
    raw["allowable_host_external_pressure_difference_Pa"] = 4e5
    with pytest.raises(ValueError, match="pin the complete"):
        HotTapBranchTestPressureCap.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="branch", time_basis="authored")
    a = registry.run("inspection.hot_tap_branch_test_pressure_cap", x, context)
    b = registry.run_json("inspection.hot_tap_branch_test_pressure_cap", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
