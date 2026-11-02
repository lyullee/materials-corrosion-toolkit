"""Validate one actual pinned HELPR run through the public MatIntegrity adapter."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.helpr_adapter import read_helpr_life_criteria_csv

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data/evidence/helpr/representative_run_final"
REVISION = "ae12d20b6608123af41dd9d5f70db6b6547fece5"
EXPECTED_WARNING_CODES = [
    "provider_internal_bool_bitwise_inversion_deprecated",
    "fracture_resistance_not_reached_a_crit_over_t_set_to_0_8",
]


def main():
    manifest_path = RUN / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provider = manifest["provider"]
    if provider != {
        "id": "sandia.helpr",
        "version": "2.1.0",
        "revision": REVISION,
        "tag": "v2.1.0",
    }:
        raise ValueError("representative run provider identity changed")
    source = RUN / "nominal_life_criteria.csv"
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    if manifest["outputs"][source.name]["sha256"] != source_sha256:
        raise ValueError("HELPR output differs from the local run manifest")
    configuration_digest = canonical_digest(manifest["configuration"])
    (record,) = read_helpr_life_criteria_csv(
        source,
        provider_version=provider["version"],
        provider_revision=provider["revision"],
        analysis_id="helpr-v2.1.0-official-test-input",
        study_type="nominal",
        asset_id="synthetic-helpr-pipe",
        location_id="synthetic-internal-longitudinal-flaw",
        material_condition_id="synthetic-helpr-steel",
        load_case_id="synthetic-helpr-pressure-cycle",
        sample_ids=["deterministic-nominal"],
        provider_configuration_digest=configuration_digest,
        units_reviewed=True,
        missing_value_semantics=(
            "HELPR blank or NaN criterion is unavailable or not reached; provider-run interpretation required"
        ),
        provider_a_crit_interpretation=(
            "provider set a_crit/t to 0.8 because fracture resistance was not reached in this run"
        ),
        provider_run_warning_codes=tuple(manifest["provider_warning_codes"]),
        provider_run_warnings_reviewed=True,
    )
    criteria = {
        "provider_reported_a_crit_m": record.provider_reported_a_crit_m,
        "provider_reported_cycles_to_a_crit": record.provider_reported_cycles_to_a_crit,
        "provider_reported_cycles_to_25_percent_a_crit": (
            record.provider_reported_cycles_to_25_percent_a_crit
        ),
        "provider_reported_cycles_to_half_nc": record.provider_reported_cycles_to_half_nc,
        "provider_reported_cycles_to_fad_line": record.provider_reported_cycles_to_fad_line,
    }
    if criteria["provider_reported_a_crit_m"] is None:
        raise AssertionError("representative HELPR run did not report its a(crit) field")
    if not any(value is not None for key, value in criteria.items() if "cycles_" in key):
        raise AssertionError("representative HELPR run did not report any life criterion")
    warning_codes = manifest["provider_warning_codes"]
    if warning_codes != EXPECTED_WARNING_CODES:
        raise AssertionError("representative HELPR provider warning was not captured as reviewed")
    if manifest["provider_warning_count"] != len(warning_codes):
        raise AssertionError("representative HELPR warning count does not match its codes")
    if any(code.startswith("unclassified_warning_") for code in warning_codes):
        raise AssertionError("representative HELPR run retains an unclassified warning")
    validation = {
        "schema_version": "matintegrity.helpr_end_to_end.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "provider": provider,
        "environment_versions": manifest["environment"],
        "run_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "configuration_digest": configuration_digest,
        "source_output_sha256": source_sha256,
        "source_output_bytes": source.stat().st_size,
        "record_digest": canonical_digest(record.model_dump(mode="json")),
        "criterion_availability": {key: value is not None for key, value in criteria.items()},
        "provider_warning_codes": warning_codes,
        "provider_warning_count": len(warning_codes),
        "provider_a_crit_interpretation": record.provider_a_crit_interpretation,
        "endpoint_semantics": record.endpoint_semantics,
        "probability_semantics": record.probability_semantics,
        "adapter_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/helpr_adapter.py").read_bytes()
        ).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_output_redistributed": False,
        "qualification": (
            "An actual pinned HELPR deterministic run was saved and ingested with explicit provider, "
            "configuration, asset, location, material, load-case and sample identities. This is software "
            "integration evidence, not independent physics validation, code acceptance, remaining-life "
            "certification, or failure probability."
        ),
    }
    target = ROOT / "validation/helpr_end_to_end.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
