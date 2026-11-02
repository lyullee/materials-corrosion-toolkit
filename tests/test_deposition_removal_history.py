import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.fabrication_surface import (
    DepositedLayerGeometry,
    DepositionRemovalHistory,
    LayerGeometryEvent,
    deposition_removal_history,
)
from matintegrity.registry import default_registry


def layer(identifier="initial", thickness=0.004):
    return DepositedLayerGeometry(
        layer_id=identifier,
        material_condition_id="steel",
        thickness_m=thickness,
        thickness_origin="measured",
        record_digest="a" * 64,
    )


def event(identifier, kind, thickness, layer_id=None):
    return LayerGeometryEvent(
        event_id=identifier,
        kind=kind,
        thickness_m=thickness,
        thickness_origin="procedure_target",
        layer_id=layer_id,
        material_condition_id="filler" if layer_id else None,
        record_digest="b" * 64,
    )


def request(initial=None, events=None, **updates):
    initial = (layer(),) if initial is None else initial
    events = (
        (event("deposit", "deposit", 0.002, "new"), event("grind", "surface_removal", 0.003))
        if events is None
        else events
    )
    digest = canonical_digest(
        {
            "initial_layers": [r.model_dump(mode="json") for r in initial],
            "events": [r.model_dump(mode="json") for r in events],
        }
    )
    values = dict(
        asset_id="asset",
        location_id="joint",
        physical_region_id="local-profile",
        coordinate_frame_id="frame",
        outward_normal_direction_id="normal",
        initial_layers=initial,
        events=events,
        history_digest=digest,
        common_normal_and_uniform_local_thickness_reviewed=True,
        event_order_and_thickness_origins_reviewed=True,
        evidence=(dict(source_id="authored", origin="synthetic", citation="authored layer balance"),),
    )
    values.update(updates)
    return DepositionRemovalHistory(**values)


def test_cross_layer_removal_and_balance_preserve_identities():
    r = deposition_removal_history(request())
    assert r.status == "computed"
    assert r.values["final_total_thickness_m"] == pytest.approx(0.003)
    assert r.values["thickness_balance_residual_m"] == pytest.approx(0.0, abs=1e-18)
    assert r.values["final_layers"][0]["retained_thickness_m"] == pytest.approx(0.003)
    assert r.values["final_layers"][1]["retained_thickness_m"] == 0.0
    assert r.values["exposed_top_layer_id"] == "initial"
    removed = r.values["event_history"][-1]["removed_by_layer"]
    assert [row["layer_id"] for row in removed] == ["new", "initial"]
    assert [row["removed_thickness_m"] for row in removed] == pytest.approx([0.002, 0.001])
    assert r.values["event_history"][0]["retained_layers"][1]["retained_thickness_m"] == 0.002
    assert r.values["final_layers"][0]["thickness_origin"] == "measured"
    assert r.values["final_layers"][1]["thickness_origin"] == "procedure_target"


def test_empty_initial_stack_can_receive_deposition():
    r = deposition_removal_history(request(initial=(), events=(event("d", "deposit", 0.002, "first"),)))
    assert r.values["initial_total_thickness_m"] == 0.0
    assert r.values["exposed_top_layer_id"] == "first"


def test_complete_removal_preserves_zero_layer_record():
    r = deposition_removal_history(request(events=(event("g", "surface_removal", 0.004),)))
    assert r.status == "computed"
    assert r.values["final_total_thickness_m"] == 0.0
    assert r.values["exposed_top_layer_id"] is None
    assert len(r.values["final_layers"]) == 1


def test_removal_into_unspecified_substrate_is_outside_scope():
    r = deposition_removal_history(request(events=(event("g", "surface_removal", 0.005),)))
    assert r.status == "out_of_scope"
    assert r.values["unsupported_event_id"] == "g"
    assert "final_layers" not in r.values


def test_execution_order_changes_geometry():
    a = deposition_removal_history(request())
    x = request(events=(event("g", "surface_removal", 0.003), event("d", "deposit", 0.002, "new")))
    b = deposition_removal_history(x)
    assert a.values["final_total_thickness_m"] == pytest.approx(b.values["final_total_thickness_m"])
    assert a.values["exposed_top_layer_id"] != b.values["exposed_top_layer_id"]


def test_layer_id_cannot_be_reused_after_complete_removal():
    with pytest.raises(ValueError, match="reused"):
        request(events=(event("g", "surface_removal", 0.004), event("d", "deposit", 0.001, "initial")))


def test_duplicate_event_identity_is_rejected():
    with pytest.raises(ValueError, match="event identities"):
        request(events=(event("g", "surface_removal", 0.001), event("g", "surface_removal", 0.001)))


def test_history_digest_detects_event_reordering():
    x = request()
    with pytest.raises(ValueError, match="history digest"):
        request(events=tuple(reversed(x.events)), history_digest=x.history_digest)


def test_missing_review_withholds_geometry():
    r = deposition_removal_history(request(event_order_and_thickness_origins_reviewed=False))
    assert r.status == "needs_data"
    assert "final_layers" not in r.values


def test_unrepresentable_total_is_not_reported():
    r = deposition_removal_history(request(initial=(layer("a", 1e308), layer("b", 1e308))))
    assert r.status == "out_of_scope"


def test_public_python_json_exchange_and_context_binding():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="asset", location_id="joint", time_basis="ordered-events")
    a = registry.run("fabrication.deposition_removal_history", x, context)
    b = registry.run_json("fabrication.deposition_removal_history", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
    with pytest.raises(ValueError, match="asset|location"):
        registry.run(
            "fabrication.deposition_removal_history", x, context.model_copy(update={"asset_id": "other"})
        )
