import hashlib
import json
import subprocess
import sys

import pytest
from pydantic import Field

from matintegrity.contracts import Contract, Evidence, canonical_digest
from matintegrity.tabular_contract_import import (
    TabularFieldMapping,
    TabularImportProfile,
    read_csv_contracts,
    read_jsonl_contracts,
)


class DemoObservation(Contract):
    observation_id: str
    value: float
    unit: str
    metadata: dict[str, str] = Field(default_factory=dict)


class EvidenceBundle(Contract):
    records: tuple[Evidence, ...]


def profile(**updates):
    payload = {
        "profile_id": "demo-v1",
        "target_contract": "DemoObservation",
        "mappings": (
            TabularFieldMapping(target_path=("observation_id",), source_path=("id",)),
            TabularFieldMapping(target_path=("value",), source_path=("reading",), value_type="number"),
            TabularFieldMapping(target_path=("unit",), constant_value="mm"),
            TabularFieldMapping(
                target_path=("metadata",), source_path=("metadata",), value_type="json", required=False
            ),
        ),
    }
    payload.update(updates)
    return TabularImportProfile(**payload)


def test_csv_mapping_imports_valid_rows_and_rejects_without_leaking_values(tmp_path):
    source = tmp_path / "observations.csv"
    source.write_text('id,reading,metadata\na,1.25,"{""lot"":""L1""}"\nb,bad,\n', encoding="utf-8")
    records, report = read_csv_contracts(source, DemoObservation, profile())
    assert records[0].model_dump() == {
        "observation_id": "a",
        "value": 1.25,
        "unit": "mm",
        "metadata": {"lot": "L1"},
    }
    assert report.imported_rows == 1
    assert report.rejected_rows == 1
    assert report.findings[1].issue_paths == ("value",)
    assert "bad" not in report.model_dump_json()
    assert not report.unit_conversion_performed
    assert not report.code_evaluation_performed


def test_jsonl_nested_mapping_and_deterministic_digest(tmp_path):
    source = tmp_path / "observations.jsonl"
    source.write_text(json.dumps({"id": "x", "measurement": {"value": 2.5}}) + "\n", encoding="utf-8")
    nested = profile(
        mappings=(
            TabularFieldMapping(target_path=("observation_id",), source_path=("id",)),
            TabularFieldMapping(
                target_path=("value",), source_path=("measurement", "value"), value_type="number"
            ),
            TabularFieldMapping(target_path=("unit",), constant_value="MPa"),
        )
    )
    records, first = read_jsonl_contracts(source, DemoObservation, nested)
    _, second = read_jsonl_contracts(source, DemoObservation, nested)
    assert records[0].value == 2.5
    assert first.imported_records_digest == second.imported_records_digest
    assert first.source_sha256 == second.source_sha256


def test_unmapped_source_fields_are_rejected_by_default(tmp_path):
    source = tmp_path / "observations.jsonl"
    source.write_text(json.dumps({"id": "x", "reading": 1.0, "extra": "unreviewed"}), encoding="utf-8")
    records, report = read_jsonl_contracts(source, DemoObservation, profile())
    assert records == ()
    assert report.findings[0].issue_paths == ("source.extra",)


def test_csv_preserves_newline_inside_quoted_cell(tmp_path):
    source = tmp_path / "multiline.csv"
    source.write_bytes(b'id,reading,metadata\n"line 1\nline 2",1.0,{}\n')
    records, report = read_csv_contracts(source, DemoObservation, profile())
    assert records[0].observation_id == "line 1\nline 2"
    assert report.imported_rows == 1


def test_profile_rejects_scalar_and_nested_target_collision():
    with pytest.raises(ValueError, match="prefixes"):
        TabularImportProfile(
            profile_id="collision",
            target_contract="DemoObservation",
            mappings=(
                TabularFieldMapping(target_path=("metadata",), source_path=("metadata",), value_type="json"),
                TabularFieldMapping(target_path=("metadata", "lot"), source_path=("lot",)),
            ),
        )


def test_cli_imports_rows_only_into_registered_model_input_without_dynamic_import(tmp_path):
    source = tmp_path / "uniform.csv"
    source.write_text(
        "current,required,rate,horizon\n0.010,0.006,3.168808781402895e-12,31557600\n",
        encoding="utf-8",
    )
    mapping = TabularImportProfile(
        profile_id="uniform-forecast-v1",
        target_contract="UniformForecast",
        mappings=(
            TabularFieldMapping(
                target_path=("current_thickness_m",), source_path=("current",), value_type="number"
            ),
            TabularFieldMapping(
                target_path=("required_thickness_m",), source_path=("required",), value_type="number"
            ),
            TabularFieldMapping(target_path=("rate_m_s",), source_path=("rate",), value_type="number"),
            TabularFieldMapping(target_path=("horizon_s",), source_path=("horizon",), value_type="number"),
        ),
    )
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(mapping.model_dump_json(), encoding="utf-8")
    output = tmp_path / "result.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "matintegrity.cli",
            "import-tabular",
            "corrosion.uniform_forecast",
            str(source),
            str(profile_path),
            "--format",
            "csv",
            "--out",
            str(output),
        ],
        check=True,
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["report"]["imported_rows"] == 1
    assert payload["records"][0]["current_thickness_m"] == 0.01


def test_profile_can_pin_source_and_target_schema(tmp_path):
    source = tmp_path / "observations.jsonl"
    source.write_bytes((json.dumps({"id": "x", "reading": 1.0}) + "\n").encode())
    pinned = profile(
        expected_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        expected_target_schema_digest=canonical_digest(DemoObservation.model_json_schema()),
    )
    _, report = read_jsonl_contracts(source, DemoObservation, pinned)
    assert report.target_schema_digest == pinned.expected_target_schema_digest


def test_profile_rejects_changed_source_or_contract_schema(tmp_path):
    source = tmp_path / "observations.jsonl"
    source.write_text(json.dumps({"id": "x", "reading": 1.0}), encoding="utf-8")
    with pytest.raises(ValueError, match="source SHA-256"):
        read_jsonl_contracts(source, DemoObservation, profile(expected_source_sha256="0" * 64))
    with pytest.raises(ValueError, match="schema digest"):
        read_jsonl_contracts(source, DemoObservation, profile(expected_target_schema_digest="0" * 64))


def test_json_tuple_mapping_imports_arrays_for_immutable_contract_fields(tmp_path):
    source = tmp_path / "evidence.jsonl"
    source.write_text(
        json.dumps(
            {"evidence": [{"source_id": "paper-1", "origin": "measured", "citation": "caller citation"}]}
        )
        + "\n",
        encoding="utf-8",
    )
    profile = TabularImportProfile(
        profile_id="evidence-tuple-v1",
        target_contract="EvidenceBundle",
        mappings=(
            TabularFieldMapping(target_path=("records",), source_path=("evidence",), value_type="json_tuple"),
        ),
    )
    records, report = read_jsonl_contracts(source, EvidenceBundle, profile)
    assert report.imported_rows == 1
    assert isinstance(records[0].records, tuple)
    assert records[0].records[0].source_id == "paper-1"
