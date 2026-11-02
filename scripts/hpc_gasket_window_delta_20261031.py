"""Focused synthetic pressure-window events; no contact solve or prior jobs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from matintegrity.contracts import AssessmentResult, RunContext, canonical_digest
from matintegrity.models.gasket_contact_window_events import (
    GasketContactPressureWindowEvents,
    audit_gasket_contact_pressure_window_events,
    specifications,
)
from matintegrity.registry import ModelRegistry

ROOT = Path(__file__).resolve().parents[1]


def fixture(pressures=(0.0, 30.0, 0.0), times=(0.0, 3.0, 6.0), maximum=20.0):
    context = RunContext(asset_id="synthetic-joint", location_id="synthetic-surface", time_basis="elapsed_seconds")
    inputs = {"physical_scope_id": "synthetic-scope", "times_s": list(times), "node_ids": ["node-A", "node-B"]}
    model_id = "fabrication.flange_viscoelastic_contact_history"
    source = AssessmentResult(
        model_id=model_id, model_version="1.0.0", status="computed", inputs=inputs,
        values={"time_history": [{"time_s": time, "response_field": [
            {"node_id": "node-A", "mean_contact_pressure_Pa": pressure},
            {"node_id": "node-B", "mean_contact_pressure_Pa": 1000.0},
        ]} for time, pressure in zip(times, pressures, strict=True)]},
        units={"time_history[].response_field[].mean_contact_pressure_Pa": "Pa"},
        assumptions=("Fabricated contract fixture; not a computed physical joint.",), notes=(), context=context,
        input_digest=canonical_digest({"model_id": model_id, "model_version": "1.0.0", "inputs": inputs, "context": context.model_dump(mode="json")}),
        source_ids=("synthetic-contact-history",), qualification="user_model", runtime={},
    )
    basis = {"criterion_provider_id": "synthetic-criterion", "criterion_provider_revision": "1", "criterion_record_id": "window",
        "physical_scope_id": "synthetic-scope", "node_id": "node-A", "minimum_contact_pressure_Pa": 10.0, "maximum_contact_pressure_Pa": maximum}
    values = {"assessment_id": "synthetic-window", "contact_history": source.model_dump(mode="json"),
        "contact_history_sha256": canonical_digest(source.model_dump(mode="json")), **basis,
        "criterion_sha256": canonical_digest(basis),
        "criterion_evidence": [{"source_id": "synthetic-criterion", "origin": "synthetic", "citation": "Fabricated pressure bounds only.", "sha256": canonical_digest(basis)}],
        "usage_rights_evidence": [{"source_id": "synthetic-rights", "origin": "synthetic", "citation": "Project-authored software fixture only.", "license_id": "synthetic-MIT"}], "usage_license_id": "synthetic-MIT"}
    for key in ("physical_scope_and_time_basis_reviewed", "criterion_applicability_reviewed", "interpolation_basis_reviewed", "pressure_basis_and_units_reviewed", "usage_rights_reviewed", "computational_use_authorized"):
        values[key] = True
    return GasketContactPressureWindowEvents.model_validate_json(json.dumps(values))


def repinned(request, mutate):
    payload = request.model_dump(mode="json")
    mutate(payload["contact_history"])
    payload["contact_history_sha256"] = canonical_digest(payload["contact_history"])
    return GasketContactPressureWindowEvents.model_validate_json(json.dumps(payload))


def boundaries_and_censoring():
    equal = audit_gasket_contact_pressure_window_events(fixture((10.0, 10.0, 20.0, 20.0, 10.0), (0.0, 1.0, 2.0, 3.0, 4.0)))
    assert equal.status == "computed" and equal.values["below_minimum_duration_s"] == 0.0 and equal.values["above_maximum_duration_s"] == 0.0
    crossing = audit_gasket_contact_pressure_window_events(fixture())
    assert crossing.status == "computed"
    below, above = crossing.values["below_minimum_intervals"], crossing.values["above_maximum_intervals"]
    assert [(row["start_time_s"], row["end_time_s"]) for row in below] == [(0.0, 1.0), (5.0, 6.0)]
    assert [(row["start_time_s"], row["end_time_s"]) for row in above] == [(2.0, 4.0)]
    assert below[0]["left_censored"] is True and below[-1]["right_censored"] is True
    assert crossing.values["below_minimum_duration_s"] == crossing.values["above_maximum_duration_s"] == 2.0
    plateau = audit_gasket_contact_pressure_window_events(fixture((0.0, 10.0, 10.0, 0.0), (0.0, 1.0, 2.0, 3.0)))
    assert plateau.values["below_minimum_duration_s"] == 2.0
    entire = audit_gasket_contact_pressure_window_events(fixture((5.0, 5.0), (0.0, 4.0), maximum=None))
    row = entire.values["below_minimum_intervals"][0]
    assert row["left_censored"] is True and row["right_censored"] is True and row["duration_s"] == 4.0
    assert entire.values["above_maximum_intervals"] == []
    return {"strict_equal_boundaries_are_inside": True, "exact_linear_crossings": [1.0, 2.0, 4.0, 5.0],
            "boundary_plateau_not_outside": True, "both_end_censoring": True, "open_upper_window": True,
            "meaning": "synthetic interpolation checks, no seal acceptance"}


def node_and_clock_mapping():
    request = fixture((12.0, 18.0, 12.0), (0.0, 2.0, 5.0))
    result = audit_gasket_contact_pressure_window_events(request)
    assert result.status == "computed" and result.values["time_points_s"] == [0.0, 2.0, 5.0]
    assert result.values["pressure_points_Pa"] == [12.0, 18.0, 12.0]
    assert result.values["above_maximum_duration_s"] == 0.0
    missing = repinned(request, lambda source: source["values"]["time_history"][1]["response_field"].pop(0))
    duplicate = repinned(request, lambda source: source["values"]["time_history"][1]["response_field"].append(dict(source["values"]["time_history"][1]["response_field"][0])))
    for candidate, count in ((missing, 0), (duplicate, 2)):
        failed = audit_gasket_contact_pressure_window_events(candidate)
        assert failed.status == "out_of_scope" and failed.values["node_match_count"] == count and failed.values["failed_knot_index"] == 1
    wrong_unit = repinned(request, lambda source: source["units"].update({"time_history[].response_field[].mean_contact_pressure_Pa": "MPa"}))
    assert audit_gasket_contact_pressure_window_events(wrong_unit).values["out_of_scope_reason"] == "upstream_pressure_unit_not_explicitly_pascal"
    wrong_clock = repinned(request, lambda source: source["values"]["time_history"][1].update(time_s=0.0))
    assert audit_gasket_contact_pressure_window_events(wrong_clock).values["out_of_scope_reason"] == "contact_history_times_not_strictly_increasing"
    prefix = repinned(request, lambda source: source["values"]["time_history"][1].update(status="needs_data"))
    assert audit_gasket_contact_pressure_window_events(prefix).status == "needs_data"
    return {"exact_source_knots_preserved": True, "other_node_ignored": True, "single_node_membership_required": True,
            "wrong_unit_and_clock_rejected": True, "incomplete_prefix_not_promoted": True}


def criteria_rights_and_metadata():
    request = fixture()
    for name in ("physical_scope_and_time_basis_reviewed", "criterion_applicability_reviewed", "interpolation_basis_reviewed", "pressure_basis_and_units_reviewed", "usage_rights_reviewed", "computational_use_authorized"):
        payload = request.model_dump(mode="json")
        payload[name] = False
        result = audit_gasket_contact_pressure_window_events(GasketContactPressureWindowEvents.model_validate_json(json.dumps(payload)))
        assert result.status == "needs_data" and name in result.values["missing_reviews"]
    invalids = []
    changed = request.model_dump(mode="json"); changed["criterion_sha256"] = "f"*64; invalids.append(changed)
    changed = request.model_dump(mode="json"); changed["usage_license_id"] = "not-declared"; invalids.append(changed)
    changed = request.model_dump(mode="json"); changed["criterion_evidence"][0]["source_id"] = "wrong-provider"; invalids.append(changed)
    changed = request.model_dump(mode="json"); changed["contact_history_sha256"] = "f"*64; invalids.append(changed)
    for payload in invalids:
        try: GasketContactPressureWindowEvents.model_validate_json(json.dumps(payload))
        except ValidationError: pass
        else: raise AssertionError("bad criterion/rights/provenance accepted")
    registry = ModelRegistry(); registry.register(specifications()[0])
    assert registry.run(specifications()[0].model_id, request, request.contact_history.context).status == "computed"
    try: registry.run(specifications()[0].model_id, request, RunContext(asset_id="wrong-asset", location_id="synthetic-surface", time_basis="elapsed_seconds"))
    except ValueError: pass
    else: raise AssertionError("mismatched downstream context accepted")
    schema_path = ROOT/"docs/schemas/GasketContactPressureWindowEvents.json"
    assert json.loads(schema_path.read_text(encoding="utf-8")) == GasketContactPressureWindowEvents.model_json_schema()
    assert not (ROOT/"data/raw").exists()
    return {"all_review_gates_checked": True, "criterion_rights_source_digest_checks": True, "ModelSpec_and_context": True,
            "schema_sha256": hashlib.sha256(schema_path.read_bytes()).hexdigest(), "raw_data_staged": False,
            "upstream_history_is_synthetic_fixture": True}


def main():
    tasks = {"boundaries": boundaries_and_censoring, "mapping": node_and_clock_mapping, "gates": criteria_rights_and_metadata}
    parser = argparse.ArgumentParser(); parser.add_argument("--task", choices=tasks, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); args.output.parent.mkdir(parents=True, exist_ok=True)
    try: details = tasks[args.task]()
    except Exception as error:
        args.output.write_text(json.dumps({"task": args.task, "status": "failed", "exception_type": type(error).__name__, "message": str(error)}, indent=2), encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task": args.task, "status": "passed", "details": details, "meaning": "targeted synthetic software/interpolation checks; no joint physics or qualification"}, indent=2), encoding="utf-8")


if __name__ == "__main__": main()
