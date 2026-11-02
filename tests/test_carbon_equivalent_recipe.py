import pytest
from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.models.engineering_correlations import CarbonEquivalentRecipe, carbon_equivalent_recipe
from matintegrity.models.fabrication import SteelChemistry, carbon_equivalents


def recipe(chemistry, terms, response=None):
    payload = {
        "method_id": "synthetic-declared-index",
        "chemistry_mass_percent": chemistry,
        "base_carbon_multiplier": 1.0,
        "terms": tuple(terms),
        "carbon_response": response,
    }
    # Normalize term defaults to the same canonical representation as the public contract.
    from matintegrity.models.engineering_correlations import CarbonIndexTerm

    payload["terms"] = tuple(CarbonIndexTerm(**term).model_dump(mode="json") for term in terms)
    sha = canonical_digest(payload)
    return CarbonEquivalentRecipe(
        **payload,
        basis={
            "source_id": "synthetic",
            "revision": "1",
            "license_id": "synthetic-example",
            "record_sha256": sha,
            "applicability_and_units_reviewed": True,
            "computational_use_authorized": True,
            "evidence": (
                {
                    "source_id": "synthetic",
                    "origin": "synthetic",
                    "citation": "Toy composition index.",
                    "license_id": "synthetic-example",
                    "sha256": sha,
                },
            ),
        },
    )


def test_declared_iiw_terms_match_existing_independent_fixed_index():
    chemistry = dict(C=0.1, Mn=1.2, Cr=0.2, Mo=0.1, V=0.01, Ni=0.3, Cu=0.2, Si=0.1, B=0.001)
    terms = [
        {"term_id": key, "numerator_element": key, "coefficient": value}
        for key, value in {
            "Mn": 1 / 6,
            "Cr": 1 / 5,
            "Mo": 1 / 5,
            "V": 1 / 5,
            "Ni": 1 / 15,
            "Cu": 1 / 15,
        }.items()
    ]
    result = carbon_equivalent_recipe(recipe(chemistry, terms))
    assert result.values["carbon_index_mass_percent"] == pytest.approx(
        carbon_equivalents(SteelChemistry(**chemistry)).values["CE_IIW"]
    )


def test_fixed_indices_use_mass_percent_not_mass_fraction():
    result = carbon_equivalents(
        SteelChemistry(
            C=0.1,
            Mn=1.2,
            Cr=0.0,
            Mo=0.0,
            V=0.0,
            Ni=0.0,
            Cu=0.0,
            Si=0.0,
            B=0.0,
        )
    )
    assert result.values["CE_IIW"] == pytest.approx(0.3)
    assert result.values["Pcm"] == pytest.approx(0.16)


def test_ratio_and_reciprocal_terms_are_actual_arithmetic():
    result = carbon_equivalent_recipe(
        recipe(
            {"C": 0.1, "Nb": 0.02, "S": 0.01},
            [
                {
                    "term_id": "Nb_over_C",
                    "coefficient": 0.5,
                    "numerator_element": "Nb",
                    "denominator_element": "C",
                },
                {"term_id": "reciprocal_S", "coefficient": 0.002, "denominator_element": "S"},
            ],
        )
    )
    assert result.values["carbon_index_mass_percent"] == pytest.approx(0.4)


def test_response_at_center_has_exact_declared_offset():
    result = carbon_equivalent_recipe(
        recipe(
            {"C": 0.1, "Mn": 1.0},
            [
                {"term_id": "Mn", "numerator_element": "Mn", "coefficient": 0.5},
            ],
            {
                "offset": 0.75,
                "amplitude": 0.25,
                "slope_per_carbon_mass_percent": 20.0,
                "center_carbon_mass_percent": 0.1,
                "minimum_valid_carbon_mass_percent": 0.05,
                "maximum_valid_carbon_mass_percent": 0.2,
            },
        )
    )
    assert result.values["carbon_response_factor"] == 0.75
    assert result.values["carbon_index_mass_percent"] == pytest.approx(0.475)


@pytest.mark.parametrize(
    "chemistry,term",
    [
        ({"C": 0.1}, {"term_id": "Mn", "numerator_element": "Mn", "coefficient": 1.0}),
        ({"C": 0.1, "S": 0.0}, {"term_id": "S", "denominator_element": "S", "coefficient": 1.0}),
    ],
)
def test_missing_assay_and_zero_denominator_are_rejected(chemistry, term):
    with pytest.raises(ValidationError):
        recipe(chemistry, [term])


def test_ratio_avoids_intermediate_product_overflow():
    result = carbon_equivalent_recipe(
        recipe(
            {"C": 0.1, "Mn": 10.0},
            [
                {
                    "term_id": "ratio",
                    "coefficient": 1e308,
                    "numerator_element": "Mn",
                    "denominator_element": "Mn",
                },
            ],
        )
    )
    assert result.status == "computed"
    assert result.values["carbon_index_mass_percent"] == 1e308


@pytest.mark.parametrize(
    "chemistry,terms",
    [
        (
            {"C": 0.1, "S": 1e-300},
            [
                {"term_id": "overflow", "coefficient": 1e308, "denominator_element": "S"},
            ],
        ),
        (
            {"C": 0.1, "S": 1e-100},
            [
                {"term_id": "underflow", "coefficient": 1e-300, "numerator_element": "S"},
            ],
        ),
        (
            {"C": 0.1},
            [
                {"term_id": "a", "coefficient": 1e308},
                {"term_id": "b", "coefficient": 1e308},
            ],
        ),
    ],
)
def test_unrepresentable_index_returns_status_instead_of_nonfinite_output(chemistry, terms):
    result = carbon_equivalent_recipe(recipe(chemistry, terms))
    assert result.status == "out_of_scope"
    assert "carbon_index_mass_percent" not in result.values


def test_excessive_assay_sum_is_validation_error():
    with pytest.raises(ValidationError):
        recipe({"C": 1e308, "Mn": 1e308}, [{"term_id": "constant", "coefficient": 1.0}])
