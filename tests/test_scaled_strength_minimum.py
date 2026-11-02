import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ScaledStrengthCandidate,
    ScaledStrengthMinimum,
    scaled_strength_minimum,
)
from matintegrity.registry import default_registry


def candidate(identifier, strength, multiplier):
    return ScaledStrengthCandidate(
        candidate_id=identifier,
        property_definition_id=identifier,
        strength_Pa=strength,
        multiplier=multiplier,
        property_record_digest="a" * 64,
    )


def request(candidates=None):
    candidates = candidates or (candidate("tensile", 600e6, 0.25), candidate("yield", 300e6, 0.6))
    raw = dict(
        material_condition_id="authored-material-state", temperature_K=293.15, strength_candidates=candidates
    )
    digest = canonical_digest(
        ScaledStrengthMinimum.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return ScaledStrengthMinimum(
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
                    citation="authored strength arithmetic",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_governing_minimum_and_candidate_values():
    r = scaled_strength_minimum(request())
    assert r.status == "computed"
    assert r.values["minimum_scaled_strength_Pa"] == 150e6
    assert r.values["governing_candidate_ids"] == ["tensile"]
    assert r.values["scaled_strength_candidates_Pa"] == {"tensile": 150e6, "yield": 180e6}


def test_tied_governing_identities_are_retained():
    r = scaled_strength_minimum(request((candidate("a", 200.0, 0.5), candidate("b", 400.0, 0.25))))
    assert r.values["governing_candidate_ids"] == ["a", "b"]


@pytest.mark.parametrize("strength,factor", [(1e308, 2.0), (1e-300, 1e-300)])
def test_unsupported_scaled_range_withholds_minimum(strength, factor):
    r = scaled_strength_minimum(request((candidate("a", strength, factor),)))
    assert r.status == "out_of_scope"
    assert "minimum_scaled_strength_Pa" not in r.values


def test_duplicate_candidate_is_rejected():
    c = candidate("a", 100.0, 0.5)
    with pytest.raises(ValueError, match="unique"):
        request((c, c))


def test_factor_tampering_invalidates_digest():
    raw = request().model_dump()
    raw["strength_candidates"][0]["multiplier"] = 0.5
    with pytest.raises(ValueError, match="pin the complete"):
        ScaledStrengthMinimum.model_validate(raw)


def test_public_python_json_exchange():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="synthetic", location_id="material", time_basis="authored")
    a = registry.run("materials.scaled_strength_minimum", x, context)
    b = registry.run_json("materials.scaled_strength_minimum", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
