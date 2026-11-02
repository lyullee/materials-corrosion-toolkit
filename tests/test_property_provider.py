import pytest

from matintegrity.contracts import Evidence
from matintegrity.data import TabulatedProperty
from matintegrity.providers import (
    DesignPropertyTable,
    PropertyIdentity,
    PropertyQuery,
    TabulatedPropertyProvider,
)


def test_design_property_does_not_mix_editions_or_extrapolate_and_snapshots_data():
    identity = PropertyIdentity(
        material_id="synthetic",
        product_form="plate",
        material_condition="declared",
        orientation="longitudinal",
        property_id="allowable_stress",
        basis_id="user-design-basis",
        basis_edition="A",
    )
    curve = TabulatedProperty(
        property_id="allowable_stress",
        x=[100.0, 300.0],
        y=[200.0, 100.0],
        x_unit="K",
        y_unit="MPa",
        source_id="synthetic",
    )
    table = DesignPropertyTable(
        identity=identity,
        temperature_table=curve,
        evidence=Evidence(
            source_id="synthetic", origin="synthetic", citation="Project synthetic example", license_id="MIT"
        ),
        permitted_use_note="Synthetic values for a software check only.",
    )
    provider = TabulatedPropertyProvider([table])
    curve.y[0] = 999.0
    query = PropertyQuery(identity=identity, temperature_K=200.0, requested_unit="Pa")
    answer = provider.resolve(query)
    assert answer["value"] == pytest.approx(150e6)
    assert len(answer["table_digest"]) == 64
    assert provider.resolve(query.model_copy(update={"temperature_K": 400.0}))["status"] == "out_of_scope"
    assert (
        provider.resolve(
            query.model_copy(update={"identity": identity.model_copy(update={"basis_edition": "B"})})
        )["status"]
        == "needs_data"
    )
    with pytest.raises(ValueError, match="duplicate"):
        TabulatedPropertyProvider([table, table])
