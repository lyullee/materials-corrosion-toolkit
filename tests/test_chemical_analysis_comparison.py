import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ChemicalAnalysisLimit,
    ChemicalAnalysisLinearRule,
    ChemicalAnalysisObservation,
    ChemicalAnalysisSumRule,
    DeclaredChemicalAnalysisComparison,
    declared_chemical_analysis_comparison,
)
from matintegrity.registry import default_registry


def linear_request(x=0.5, missing=False, **updates):
    observations = tuple(
        ChemicalAnalysisObservation(
            measurement_id=key,
            element_id=element,
            sample_id="same",
            method_id="authored",
            record_sha256="a" * 64,
            measured_mass_fraction=None if missing and key == "y" else value,
            expanded_uncertainty_mass_fraction=None if missing and key == "y" else 0.015625,
        )
        for key, element, value in [("x", "X", x), ("y", "Y", 0.125)]
    )
    limits = tuple(
        ChemicalAnalysisLimit(
            element_id=key,
            minimum_mass_fraction=0.0,
            maximum_mass_fraction=1.0,
            tolerance_basis_id="authored",
        )
        for key in ("X", "Y")
    )
    rule = ChemicalAnalysisLinearRule(
        rule_id="linear",
        measurement_coefficients={"x": 1.0, "y": -2.0},
        minimum_value=0.0,
        requirement_basis_id="authored",
    )
    raw = dict(observations=observations, limits=limits, linear_rules=(rule,)) | updates
    return request(**raw)


@pytest.mark.parametrize(
    "value,state",
    [(0.5, "within_declared_interval"), (0.25, "uncertainty_overlap"), (0.125, "outside_declared_interval")],
)
def test_signed_same_sample_linear_rule_with_conservative_interval(value, state):
    result = declared_chemical_analysis_comparison(linear_request(x=value))
    row = result.values["linear_comparisons"][0]
    assert row["comparison_state"] == state
    assert row["linear_expression_value"] == value - 0.25
    assert row["expanded_interval_bound"] == 0.046875


def test_linear_missing_measurement_is_not_zero():
    result = declared_chemical_analysis_comparison(linear_request(missing=True))
    assert result.status == "needs_data"
    assert result.values["linear_comparisons"][0]["linear_expression_value"] is None


def test_linear_rule_cannot_join_different_samples_or_repeat_element():
    original = linear_request()
    for update in ({"sample_id": "other"}, {"element_id": "X"}):
        observations = (original.observations[0], original.observations[1].model_copy(update=update))
        with pytest.raises(ValueError, match="one sample"):
            linear_request(observations=observations)


def test_linear_rule_registry_python_json_exchange_and_pin():
    x = linear_request()
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    model = "materials.declared_chemical_analysis_comparison"
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
    raw = x.model_dump()
    raw["linear_rules"][0]["measurement_coefficients"]["x"] = 2.0
    with pytest.raises(ValueError, match="pin the complete"):
        DeclaredChemicalAnalysisComparison(**raw)


def test_linear_rule_nonrepresentable_interval_is_withheld():
    original = linear_request()
    observations = tuple(
        row.model_copy(update={"expanded_uncertainty_mass_fraction": 1.0}) for row in original.observations
    )
    rule = ChemicalAnalysisLinearRule(
        rule_id="huge",
        measurement_coefficients={"x": 1e308, "y": 1e308},
        minimum_value=0.0,
        requirement_basis_id="authored",
    )
    result = declared_chemical_analysis_comparison(
        linear_request(observations=observations, linear_rules=(rule,))
    )
    assert result.status == "out_of_scope"
    assert "comparisons" not in result.values


def test_linear_bound_and_missing_identity_validation():
    with pytest.raises(ValueError, match="ordered"):
        ChemicalAnalysisLinearRule(
            rule_id="bad",
            measurement_coefficients={"x": 1.0},
            minimum_value=1.0,
            maximum_value=0.0,
            requirement_basis_id="authored",
        )
    rule = ChemicalAnalysisLinearRule(
        rule_id="missing",
        measurement_coefficients={"absent": 1.0},
        minimum_value=0.0,
        requirement_basis_id="authored",
    )
    with pytest.raises(ValueError, match="explicit observation"):
        linear_request(linear_rules=(rule,))


def request(value=0.25, uncertainty=0.0, **updates):
    raw = dict(
        physical_product_id="p",
        heat_id="h",
        material_condition_id="m",
        governing_requirement_id="r",
        analysis_kind="product_analysis",
        sampling_and_analysis_kind_reviewed=True,
        product_tolerance_application_authorized=True,
        limits=(
            ChemicalAnalysisLimit(
                element_id="X",
                minimum_mass_fraction=0.125,
                maximum_mass_fraction=0.375,
                permitted_under_minimum=0.0625,
                permitted_over_maximum=0.0625,
                tolerance_basis_id="authored",
            ),
        ),
        observations=(
            ChemicalAnalysisObservation(
                measurement_id="obs",
                element_id="X",
                sample_id="s",
                method_id="lab",
                record_sha256="a" * 64,
                measured_mass_fraction=value,
                expanded_uncertainty_mass_fraction=uncertainty,
            ),
        ),
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredChemicalAnalysisComparison.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DeclaredChemicalAnalysisComparison(
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
                    citation="Authored binary-exact interval.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "value,u,state",
    [
        (0.0625, 0.0, "within_declared_interval"),
        (0.4375, 0.0, "within_declared_interval"),
        (0.5, 0.0, "outside_declared_interval"),
        (0.4375, 0.0625, "uncertainty_overlap"),
    ],
)
def test_interval_comparison(value, u, state):
    result = declared_chemical_analysis_comparison(request(value, u))
    assert result.status == "computed"
    assert result.values["comparisons"][0]["comparison_state"] == state


@pytest.mark.parametrize(
    "updates", [{"analysis_kind": "heat_analysis"}, {"product_tolerance_application_authorized": False}]
)
def test_product_tolerance_cannot_be_applied_without_role_and_authority(updates):
    with pytest.raises(ValueError, match="authorized product analysis"):
        request(**updates)


def test_heat_analysis_without_tolerance_uses_original_limits():
    limit = ChemicalAnalysisLimit(element_id="X", maximum_mass_fraction=0.375, tolerance_basis_id="original")
    result = declared_chemical_analysis_comparison(
        request(0.4375, analysis_kind="heat_analysis", limits=(limit,))
    )
    assert result.values["comparisons"][0]["comparison_state"] == "outside_declared_interval"


def test_missing_observation_and_unreviewed_sampling_remain_unknown():
    assert declared_chemical_analysis_comparison(request(None, None)).status == "needs_data"
    assert (
        declared_chemical_analysis_comparison(request(sampling_and_analysis_kind_reviewed=False)).status
        == "needs_data"
    )


def test_unobserved_required_element_is_not_imputed():
    x = request()
    additional = ChemicalAnalysisLimit(
        element_id="Y", maximum_mass_fraction=0.5, tolerance_basis_id="authored"
    )
    result = declared_chemical_analysis_comparison(request(limits=x.limits + (additional,)))
    assert result.status == "needs_data"
    assert result.values["missing_element_ids"] == ["Y"]


def test_duplicate_observation_id_rejected():
    x = request()
    with pytest.raises(ValueError, match="identities must be unique"):
        request(observations=x.observations * 2)


def test_repeated_element_samples_keep_individual_results():
    first = request().observations[0]
    second = first.model_copy(
        update={"measurement_id": "second", "sample_id": "another", "measured_mass_fraction": 0.5}
    )
    result = declared_chemical_analysis_comparison(request(observations=(first, second)))
    assert [r["comparison_state"] for r in result.values["comparisons"]] == [
        "within_declared_interval",
        "outside_declared_interval",
    ]


def test_complete_request_digest_prevents_silent_tolerance_change():
    x = request()
    raw = x.model_dump()
    raw["limits"][0]["permitted_over_maximum"] = 0.125
    with pytest.raises(ValueError, match="pin the complete"):
        DeclaredChemicalAnalysisComparison(**raw)


@pytest.mark.parametrize("with_sum", [False, True])
def test_python_json_registry_exchange(with_sum):
    x = summed_request() if with_sum else request()
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    a = registry.run("materials.declared_chemical_analysis_comparison", x.model_dump(), context)
    b = registry.run_json("materials.declared_chemical_analysis_comparison", x.model_dump_json(), context)
    assert a.values == b.values


def summed_request(second_value=0.25, second_uncertainty=0.0, **updates):
    first = request().observations[0]
    second = first.model_copy(
        update={
            "measurement_id": "y",
            "element_id": "Y",
            "measured_mass_fraction": second_value,
            "expanded_uncertainty_mass_fraction": second_uncertainty,
        }
    )
    limits = request().limits + (
        ChemicalAnalysisLimit(element_id="Y", maximum_mass_fraction=0.5, tolerance_basis_id="authored"),
    )
    rule = ChemicalAnalysisSumRule(
        rule_id="sum",
        measurement_ids=("obs", "y"),
        maximum_mass_fraction=0.375,
        requirement_basis_id="authored",
    )
    raw = dict(observations=(first, second), limits=limits, sum_rules=(rule,))
    raw.update(updates)
    return request(**raw)


def test_individual_elements_can_pass_while_explicit_sum_fails():
    result = declared_chemical_analysis_comparison(summed_request())
    assert all(r["comparison_state"] == "within_declared_interval" for r in result.values["comparisons"])
    assert result.values["sum_comparisons"][0]["comparison_state"] == "outside_declared_interval"
    assert result.values["sum_comparisons"][0]["summed_mass_fraction"] == 0.5


def test_sum_uncertainty_is_arithmetic_bound_not_independence_assumption():
    result = declared_chemical_analysis_comparison(summed_request(0.125, 0.0625))
    row = result.values["sum_comparisons"][0]
    assert row["comparison_state"] == "uncertainty_overlap"
    assert row["summed_expanded_uncertainty_bound"] == 0.0625


def test_missing_group_member_remains_unknown():
    result = declared_chemical_analysis_comparison(summed_request(None, None))
    assert result.status == "needs_data"
    assert result.values["sum_comparisons"][0]["summed_mass_fraction"] is None


@pytest.mark.parametrize("kind", ["other_sample", "same_element", "missing_id"])
def test_sum_cannot_mix_samples_duplicate_element_or_reference_missing_record(kind):
    x = summed_request()
    observations = list(x.observations)
    rules = x.sum_rules
    if kind == "other_sample":
        observations[1] = observations[1].model_copy(update={"sample_id": "another"})
    elif kind == "same_element":
        observations[1] = observations[1].model_copy(update={"element_id": "X"})
    else:
        rules = (rules[0].model_copy(update={"measurement_ids": ("obs", "missing")}),)
    with pytest.raises(ValueError):
        summed_request(observations=tuple(observations), sum_rules=rules)
