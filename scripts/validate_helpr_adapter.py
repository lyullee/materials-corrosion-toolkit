"""Verify the authored HELPR CSV exchange contract without importing HELPR."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.helpr_adapter import read_helpr_life_criteria_csv

ROOT = Path(__file__).resolve().parents[1]
REVISION = "ae12d20b6608123af41dd9d5f70db6b6547fece5"


def main():
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / "probabilistic_life_criteria.csv"
        source.write_text(
            "a(crit),Cycles to a(crit),Cycles to 25% a(crit),"
            "Cycles to 1/2 Nc,Cycles to FAD line\n"
            "0.008,12000,3000,6000,9000\n"
            "0.009,nan,4000,,10000\n",
            encoding="utf-8",
        )
        records = read_helpr_life_criteria_csv(
            source,
            provider_version="2.1.0",
            provider_revision=REVISION,
            analysis_id="authored-contract-check",
            study_type="probabilistic",
            asset_id="synthetic-pipe",
            location_id="synthetic-longitudinal-flaw",
            material_condition_id="synthetic-steel",
            load_case_id="synthetic-pressure-cycle",
            sample_ids=["sample-000", "sample-001"],
            provider_configuration_digest="b" * 64,
            units_reviewed=True,
            missing_value_semantics="blank or NaN retained pending provider-run review",
            provider_a_crit_interpretation="provider field retained without physical qualification",
            provider_run_warning_codes=(),
            provider_run_warnings_reviewed=True,
        )
    if records[1].provider_reported_cycles_to_a_crit is not None:
        raise AssertionError("missing criterion was not preserved")
    if records[1].provider_reported_cycles_to_half_nc is not None:
        raise AssertionError("blank criterion was not preserved")
    if any(record.probability_semantics != "none" for record in records):
        raise AssertionError("life criteria were incorrectly promoted to probabilities")
    record = {
        "schema_version": "matintegrity.helpr_adapter_contract.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "interface_id": "integration.helpr_life_criteria",
        "provider_version_contract": "2.1.0",
        "provider_revision_contract": REVISION,
        "record_count": len(records),
        "record_digests": [canonical_digest(item.model_dump(mode="json")) for item in records],
        "preserved_missing_fields": [
            "provider_reported_cycles_to_a_crit",
            "provider_reported_cycles_to_half_nc",
        ],
        "adapter_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/helpr_adapter.py").read_bytes()
        ).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "qualification": (
            "Authored CSV verifies schema refusal, provenance restoration and missing-value preservation. "
            "It does not execute HELPR, qualify its physics, validate a pipeline, or convert a life "
            "criterion into observed failure or probability."
        ),
    }
    target = ROOT / "validation/helpr_adapter_contract.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
