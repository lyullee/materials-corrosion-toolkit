import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredEquipmentEffectiveness,
    DeclaredParetoCategory,
    DeclaredParetoSummary,
    declared_equipment_effectiveness,
    declared_pareto_summary,
)
from matintegrity.registry import default_registry


def bind(cls, raw):
    digest = canonical_digest(cls.model_construct(**raw).model_dump(mode="json", exclude={"basis"}))
    return cls(
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
                    citation="Authored descriptor arithmetic.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def oee(**updates):
    raw = dict(
        asset_id="a",
        observation_window_id="w",
        production_quantity_unit="piece",
        planned_operating_time_s=100.0,
        actual_running_time_s=80.0,
        reference_production_rate_per_s=10.0,
        actual_running_production_rate_per_s=5.0,
        total_output_quantity=400.0,
        conforming_output_quantity=300.0,
        window_rate_and_quality_definitions_reviewed=True,
    )
    raw.update(updates)
    return bind(DeclaredEquipmentEffectiveness, raw)


def pareto(**updates):
    raw = dict(
        observation_window_id="w",
        mode="occurrence_count",
        common_window_categories_and_cost_basis_reviewed=True,
        categories=(
            DeclaredParetoCategory(
                category_id="a", occurrence_count=4, cost_per_occurrence=1.0, record_id="a"
            ),
            DeclaredParetoCategory(
                category_id="b", occurrence_count=2, cost_per_occurrence=10.0, record_id="b"
            ),
        ),
    )
    raw.update(updates)
    return bind(DeclaredParetoSummary, raw)


def test_effectiveness_factors_and_product():
    result = declared_equipment_effectiveness(oee())
    assert result.values["availability_fraction"] == 0.8
    assert result.values["performance_ratio"] == 0.5
    assert result.values["quality_fraction"] == 0.75
    assert result.values["equipment_effectiveness"] == pytest.approx(0.3)


def test_effectiveness_asset_must_match_registry_context():
    with pytest.raises(ValueError, match="asset must match"):
        default_registry().run(
            "maintenance.declared_equipment_effectiveness",
            oee().model_dump(),
            RunContext(asset_id="another", location_id="l", time_basis="synthetic"),
        )


def test_performance_above_reference_is_not_clipped():
    result = declared_equipment_effectiveness(oee(actual_running_production_rate_per_s=20.0))
    assert result.values["performance_ratio"] == 2.0
    assert result.values["performance_above_declared_reference"] is True


def test_no_output_quality_is_undefined():
    assert (
        declared_equipment_effectiveness(
            oee(total_output_quantity=0.0, conforming_output_quantity=0.0)
        ).status
        == "needs_data"
    )


@pytest.mark.parametrize("updates", [{"actual_running_time_s": 101.0}, {"conforming_output_quantity": 401.0}])
def test_inconsistent_effectiveness_bounds_rejected(updates):
    with pytest.raises(ValueError):
        oee(**updates)


def test_count_and_cost_rankings_differ():
    count = declared_pareto_summary(pareto())
    cost = declared_pareto_summary(pareto(mode="occurrence_cost", cost_unit="authored-currency"))
    assert count.values["ranked_categories"][0]["category_id"] == "a"
    assert cost.values["ranked_categories"][0]["category_id"] == "b"
    assert cost.values["total_measure"] == 24.0
    assert cost.values["ranked_categories"][-1]["cumulative_fraction"] == 1.0


def test_ties_keep_input_order_and_zero_total_stays_undefined():
    rows = tuple(
        DeclaredParetoCategory(category_id=name, occurrence_count=0, record_id=name) for name in ("z", "a")
    )
    result = declared_pareto_summary(pareto(categories=rows))
    assert [r["category_id"] for r in result.values["ranked_categories"]] == ["z", "a"]
    assert all(r["fraction_of_total"] is None for r in result.values["ranked_categories"])


def test_unknown_cost_is_not_zero():
    rows = (DeclaredParetoCategory(category_id="a", occurrence_count=1, record_id="a"),)
    with pytest.raises(ValueError, match="cost for every category"):
        pareto(mode="occurrence_cost", cost_unit="authored", categories=rows)


def test_duplicate_categories_rejected():
    x = pareto()
    with pytest.raises(ValueError, match="identities must be unique"):
        pareto(categories=x.categories * 2)


def test_cost_product_overflow_returns_status():
    rows = (
        DeclaredParetoCategory(
            category_id="a", occurrence_count=10, cost_per_occurrence=1e308, record_id="a"
        ),
    )
    assert (
        declared_pareto_summary(pareto(mode="occurrence_cost", cost_unit="authored", categories=rows)).status
        == "out_of_scope"
    )


@pytest.mark.parametrize("kind", ["oee", "pareto"])
def test_unreviewed_definitions_need_data(kind):
    result = (
        declared_equipment_effectiveness(oee(window_rate_and_quality_definitions_reviewed=False))
        if kind == "oee"
        else declared_pareto_summary(pareto(common_window_categories_and_cost_basis_reviewed=False))
    )
    assert result.status == "needs_data"


@pytest.mark.parametrize(
    "model,x",
    [
        ("maintenance.declared_equipment_effectiveness", oee()),
        ("maintenance.declared_pareto_summary", pareto()),
    ],
)
def test_python_json_exchange(model, x):
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    a = registry.run(model, x.model_dump(), context)
    b = registry.run_json(model, x.model_dump_json(), context)
    assert a.values == b.values
