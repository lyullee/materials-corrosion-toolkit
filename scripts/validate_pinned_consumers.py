"""Run MatIntegrity payloads through two pinned external consumer implementations."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API581_COMMIT = "7c8badb829f84b19c7b84d07fbc476601d9194eb"
CONSEQUENCE_COMMIT = "4106da0020196fcf61c8b6264ae0598e63a881a1"
SHA = "a" * 64


def _head(path: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _handoff():
    from matintegrity.consequence_exchange import consequence_scenario_handoff

    requested = tuple(
        {
            "stage": stage,
            "provider_id": "process-risk-provider",
            "model_id": f"{stage}-model",
            "model_revision": "1",
            "configuration_digest": SHA,
        }
        for stage in ("source", "release", "dispersion", "effect")
    )
    return consequence_scenario_handoff(
        handoff_id="consumer-validation-handoff",
        scenario_id="scenario-1",
        event={
            "event_id": "event-1",
            "asset_id": "asset-1",
            "location_id": "location-1",
            "failure_mode": "caller-defined loss of containment",
            "physical_scope_id": "scope-1",
            "clock_id": "clock-1",
            "horizon_start_s": 0.0,
            "horizon_end_s": 100.0,
            "event_probability": 0.01,
            "probability_semantics": "conditional_first_failure_in_period",
            "probability_conditioning": "survival to horizon start",
            "integrity_model_id": "integrity-model",
            "integrity_model_version": "1",
            "integrity_input_digest": SHA,
            "integrity_result_digest": SHA,
        },
        process_state={
            "pressure_pa": 2_000_000.0,
            "pressure_basis": "absolute",
            "temperature_k": 350.0,
            "temperature_basis": "upstream bulk state",
            "composition": (
                {
                    "component_id": "methane",
                    "fraction": 1.0,
                    "fraction_basis": "mole_fraction",
                    "source_id": "composition-1",
                },
            ),
            "composition_basis_description": "reviewed dry mole fraction",
            "state_source_digest": SHA,
        },
        release={
            "release_scenario_id": "release-1",
            "inventory_id": "inventory-1",
            "release_location_id": "location-1",
            "release_phase_basis": "gas",
            "release_geometry_basis": "caller_defined",
            "release_geometry_description": "caller circular opening",
            "opening_area_m2": 1e-4,
            "release_direction_basis": "surface normal",
            "release_duration_s": 10.0,
            "isolation_basis": "caller isolation clock",
            "source_boundary_basis": "declared process state",
            "source_digest": SHA,
        },
        requested_models=requested,
        handoff_status="ready",
        limitations=("Consumer validation uses synthetic values and no physical qualification.",),
    )


def _damage_record():
    from matintegrity.api581_exchange import api581_damage_exchange_record

    evidence = {"source_id": "synthetic", "origin": "synthetic", "citation": "consumer validation"}
    return api581_damage_exchange_record(
        exchange_id="numeric-provider-validation",
        asset_id="asset-1",
        component_id="component-1",
        location_id="location-1",
        physical_scope_id="scope-1",
        horizon_start_s=0.0,
        horizon_end_s=31_536_000.0,
        survival_conditioning="survived to horizon start",
        damage_mechanism_id="synthetic-mechanism",
        damage_mechanism_definition="caller supplied aggregate factor validation",
        wall_flaw_material_state={
            "state_id": "state-1",
            "wall_thickness_value": 0.01,
            "wall_thickness_unit_token": "m",
            "wall_thickness_basis": "synthetic measured minimum",
            "flaw_definition_id": "flaw-1",
            "flaw_state_digest": SHA,
            "material_id": "material-1",
            "material_condition_id": "condition-1",
            "material_state_digest": SHA,
            "state_record_digest": SHA,
            "evidence": (evidence,),
        },
        inspection_lineage=(),
        status="computed",
        status_basis="synthetic numeric provider execution",
        damage_factor=2.0,
        damage_factor_definition="caller supplied aggregate damage factor",
        damage_factor_unit_token="1",
        provider_id="synthetic-provider",
        provider_revision="1",
        model_id="synthetic-damage-factor",
        model_revision="1",
        provider_configuration_digest=SHA,
        provider_input_digest=SHA,
        provider_result_digest=SHA,
        evidence=(evidence,),
        limitations=("Synthetic integration input; no engineering applicability claim.",),
    )


def _consequence_request(*, expected_engine_code_digest: str = SHA, model_id: str = "synthetic-provider"):
    from matintegrity.consequence_pinned_adapter import (
        PinnedProviderRequestOptions,
        export_pinned_provider_request,
    )

    options = PinnedProviderRequestOptions.model_validate(
        {
            "operating_case_id": "case-1",
            "context_mode": "engineering_review_required",
            "evidence": (
                {
                    "id": "source-evidence-1",
                    "kind": "user_supplied",
                    "citation": "synthetic consumer validation source",
                    "locator": "synthetic-1",
                    "sha256": SHA,
                },
            ),
            "source": {
                "asset_id": "asset-1",
                "scenario_id": "scenario-1",
                "operating_case_id": "case-1",
                "origin": "user_supplied",
                "source_digest": SHA,
                "source_code_digest": SHA,
                "evidence_ids": ("source-evidence-1",),
                "phase": "vapour",
                "mass_rate_kg_s": 2.0,
                "duration_s": 10.0,
                "released_mass_kg": 20.0,
            },
            "engine": "user_supplied",
            "model_id": model_id,
            "expected_engine_code_digest": expected_engine_code_digest,
            "receptor_id": "receptor-1",
            "distance_m": 25.0,
            "quantity": "concentration_kg_m3",
            "provider_settings": {"weather_case_id": "synthetic-weather"},
        }
    )
    return export_pinned_provider_request(_handoff(), options)


def validate_consumers(api581_repo: Path, consequence_repo: Path) -> dict:
    if _head(api581_repo) != API581_COMMIT or _head(consequence_repo) != CONSEQUENCE_COMMIT:
        raise ValueError("external consumer checkout is not at the reviewed commit")
    sys.path[:0] = [str(api581_repo / "src"), str(consequence_repo / "src")]

    from api581.api.frequency import PofMethodSelectionInput, pof_method_selection
    from ccps_consequence.contracts import code_digest
    from ccps_consequence.integrations import ProviderRequest, ProviderResult, evaluate_provider

    from matintegrity.api581_numeric_provider import (
        Api581NumericFrequencySettings,
        run_pinned_api581_numeric_frequency,
    )
    from matintegrity.api581_pinned_adapter import PinnedPofMethodSelectionRequest
    from matintegrity.ccps_native_provider import CcpsNativePlumeSettings, run_pinned_ccps_native_plume

    api_payload = PinnedPofMethodSelectionRequest(
        method="structural_reliability",
        qualification_basis="Caller-reviewed synthetic consumer validation basis.",
        uncertainty_quantified=True,
    )
    external_api_input = PofMethodSelectionInput.model_validate_json(api_payload.model_dump_json())
    api_receipt = pof_method_selection(external_api_input)
    numeric_report = run_pinned_api581_numeric_frequency(
        _damage_record(),
        Api581NumericFrequencySettings(
            generic_frequency_per_year=1e-4,
            generic_frequency_basis="synthetic caller value",
            generic_frequency_source_digest=SHA,
            management_factor=0.5,
            management_factor_basis="synthetic caller value",
            management_factor_source_digest=SHA,
            seconds_per_year=31_536_000.0,
            caller_reviewed_damage_factor_mapping=True,
            caller_reviewed_constant_rate_poisson_assumption=True,
        ),
    )

    envelope = _consequence_request()
    external_request = ProviderRequest.model_validate_json(json.dumps(envelope.request, allow_nan=False))

    class BoundSyntheticProvider:
        def evaluate(self, request):
            return ProviderResult(
                request_digest=request.digest(),
                engine=request.engine,
                model_id=request.model_id,
                engine_version="synthetic-consumer-binding-1",
                engine_code_digest=request.expected_engine_code_digest,
                receptor_id=request.receptor_id,
                quantity=request.quantity,
                value=0.0,
                evidence_ids=request.source.evidence_ids,
                limitations=("Binding exercise only; no consequence engine executed.",),
            )

    bound_result = evaluate_provider(external_request, BoundSyntheticProvider())
    native_envelope = _consequence_request(
        expected_engine_code_digest=code_digest(),
        model_id="ccps-native-dispersion-plume-v1",
    )
    native_report = run_pinned_ccps_native_plume(
        native_envelope,
        CcpsNativePlumeSettings(
            wind_speed_m_s=5.0,
            crosswind_distance_m=0.0,
            receptor_height_m=0.0,
            release_height_m=0.0,
            sigma_y_m=10.0,
            sigma_z_m=5.0,
            sigma_basis="caller synthetic validation values",
            applicability="passive_steady_open_terrain",
            caller_reviewed=True,
        ),
    )
    payload = {
        "schema_version": "matintegrity.pinned_consumer_execution.v1",
        "api581": {
            "commit": API581_COMMIT,
            "consumer_input_model": "api581.api.frequency.PofMethodSelectionInput",
            "calculation_id": api_receipt.calculation_id,
            "input_accepted": True,
            "consumer_calculation_executed": True,
            "output_validated": api_receipt.outputs.numeric_pof_route == "external_method_result",
            "numeric_pof_provider_executed": True,
            "adjusted_calculation_id": numeric_report.adjusted_calculation_id,
            "probability_calculation_id": numeric_report.probability_calculation_id,
            "annual_failure_frequency_per_year": numeric_report.annual_failure_frequency_per_year,
            "period_failure_probability": numeric_report.period_failure_probability,
        },
        "consequence": {
            "commit": CONSEQUENCE_COMMIT,
            "consumer_input_model": "ccps_consequence.integrations.ProviderRequest",
            "request_digest": external_request.digest(),
            "matintegrity_request_digest": envelope.request_digest,
            "input_accepted": True,
            "provider_binding_executed": True,
            "provider_result_validated": bound_result.request_digest == external_request.digest(),
            "external_consequence_engine_executed": True,
            "external_calculation_id": native_report.calculation_id,
            "external_native_result_digest": native_report.provider_result_digest,
            "external_native_concentration_kg_m3": native_report.concentration_kg_m3,
        },
        "consumer_execution_performed": True,
        "end_to_end_engine_qualification_claimed": False,
        "physical_validation_claimed": False,
    }
    payload["report_digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api581-repo", default="artifacts/external-repositories/api581-risk-analysis")
    parser.add_argument(
        "--consequence-repo",
        default="artifacts/external-repositories/process-risk-consequence-toolkit",
    )
    parser.add_argument("--output", default="validation/pinned_consumer_execution.json")
    args = parser.parse_args()
    report = validate_consumers((ROOT / args.api581_repo).resolve(), (ROOT / args.consequence_repo).resolve())
    target = (ROOT / args.output).resolve()
    if ROOT not in target.parents:
        raise ValueError("output must remain inside the project")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
