"""Synthetic recipe; no empirical screening coefficients or limits bundled."""

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import CompositionIndexRecipe, CompositionIndexTerm
from matintegrity.registry import default_registry


def sample_requests():
    terms = tuple(
        CompositionIndexTerm(
            term_id=f"{a}-{b}", coefficient=1.0, factors=(dict(element_id=a), dict(element_id=b))
        )
        for a in ("A", "B")
        for b in ("I", "J")
    )
    values = dict(
        index_id="authored-interaction",
        chemistry={"A": 2.0, "B": 3.0, "I": 0.01, "J": 0.02},
        input_mass_basis="mass_percent",
        recipe_mass_basis="mass_percent",
        output_unit="authored_index",
        constant_offset=0.0,
        terms=terms,
    )
    serialized = CompositionIndexRecipe.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    digest = canonical_digest(serialized)
    inputs = CompositionIndexRecipe(
        **values,
        basis=dict(
            source_id="authored-example",
            revision="1",
            license_id="authored-example",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored-example",
                    origin="synthetic",
                    citation="synthetic polynomial recipe",
                    license_id="authored-example",
                    sha256=digest,
                ),
            ),
        ),
    )
    from matintegrity.models.engineering_correlations import SteelCompositionIndexRecipe

    named = []
    chemistry = {
        "Mn": 2.0,
        "Si": 3.0,
        "P": 0.01,
        "Sn": 0.02,
        "Sb": 0.03,
        "As": 0.04,
        "Cr": 1.0,
        "Mo": 2.0,
        "V": 3.0,
        "Pb": 0.05,
        "Bi": 0.06,
    }
    for method, coefficients in (
        ("J", {"product_scale": 2.0}),
        ("X", {"P": 2.0, "Sb": 3.0, "Sn": 4.0, "As": 5.0}),
        ("RCS", {"Cr": 1.0, "Mo": 2.0, "V": 3.0}),
        ("K", {"Pb": 2.0, "Bi": 3.0, "Sb": 4.0}),
    ):
        values = dict(
            method=method,
            chemistry=chemistry,
            input_mass_basis="mass_percent",
            recipe_mass_basis="mass_percent",
            coefficients=coefficients,
            normalization=1.0,
            constant_offset=0.0,
            output_unit="authored_index",
        )
        digest = canonical_digest(values)
        named.append(
            (
                "materials.steel_composition_index",
                SteelCompositionIndexRecipe(
                    **values,
                    basis=dict(
                        source_id="authored-example",
                        revision="1",
                        license_id="authored-example",
                        record_sha256=digest,
                        applicability_and_units_reviewed=True,
                        computational_use_authorized=True,
                        evidence=(
                            dict(
                                source_id="authored-example",
                                origin="synthetic",
                                citation="toy coefficients, not empirical factors",
                                license_id="authored-example",
                                sha256=digest,
                            ),
                        ),
                    ),
                ),
            )
        )
    return (("materials.composition_index_recipe", inputs), *named)


if __name__ == "__main__":
    registry = default_registry()
    for model_id, inputs in sample_requests():
        print(
            registry.run(
                model_id, inputs, RunContext(asset_id="synthetic", location_id="assay", time_basis="example")
            ).model_dump_json(indent=2)
        )
