import hashlib
import json

from scripts.hpc_collect import collect_results


def _fixture_run(tmp_path):
    manifest = {
        "schema_version": "matintegrity.hpc_tasks.v1",
        "pytest_shards": 1,
        "tasks": [
            {"kind": "pytest_shard", "shard_index": 0},
            {"kind": "pytest", "name": "focused-contract", "paths": ["tests/test_hpc_collect.py"]},
        ],
    }
    manifest_bytes = json.dumps(manifest, separators=(",", ":")).encode()
    digest = hashlib.sha256(manifest_bytes).hexdigest()
    for index, name in enumerate(("pytest-shard-0", "focused-contract")):
        folder = tmp_path / f"task-{index}"
        folder.mkdir()
        result = {
            "schema_version": "matintegrity.hpc_task_result.v1",
            "task_index": index,
            "task_name": name,
            "manifest_sha256": digest,
            "source_tree_sha256": "b" * 64,
            "source_file_count": 17,
            "returncode": 0,
            "commands": [{"command": ["python", "-m", "pytest"], "returncode": 0}],
        }
        (folder / "result.json").write_text(json.dumps(result), encoding="utf-8")
        (folder / "junit.xml").write_text(
            '<testsuites><testsuite tests="2" failures="0" errors="0" skipped="0" /></testsuites>',
            encoding="utf-8",
        )
    return manifest, manifest_bytes


def test_collector_accepts_complete_manifest_matched_results(tmp_path):
    manifest, manifest_bytes = _fixture_run(tmp_path)
    summary = collect_results(tmp_path, manifest, manifest_bytes)
    assert summary["task_count"] == 2
    assert summary["completed_task_count"] == 2
    assert summary["tests"] == 4
    assert summary["failed_task_indices"] == []
    assert summary["problems"] == []


def test_collector_rejects_task_name_and_command_count_mismatches(tmp_path):
    manifest, manifest_bytes = _fixture_run(tmp_path)
    result_path = tmp_path / "task-1/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["task_name"] = "wrong-task"
    result["commands"] = []
    result_path.write_text(json.dumps(result), encoding="utf-8")
    summary = collect_results(tmp_path, manifest, manifest_bytes)
    assert summary["failed_task_indices"] == [1]
    assert any("task identity mismatch" in item for item in summary["problems"])
    assert any("command record count mismatch" in item for item in summary["problems"])


def test_collector_rejects_command_failure_hidden_by_task_status(tmp_path):
    manifest, manifest_bytes = _fixture_run(tmp_path)
    result_path = tmp_path / "task-0/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["commands"][0]["returncode"] = 1
    result_path.write_text(json.dumps(result), encoding="utf-8")
    summary = collect_results(tmp_path, manifest, manifest_bytes)
    assert summary["failed_task_indices"] == [0]
    assert any("task and command status mismatch" in item for item in summary["problems"])


def test_collector_rejects_results_from_mixed_source_trees(tmp_path):
    manifest, manifest_bytes = _fixture_run(tmp_path)
    result_path = tmp_path / "task-1/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["source_tree_sha256"] = "c" * 64
    result_path.write_text(json.dumps(result), encoding="utf-8")
    summary = collect_results(tmp_path, manifest, manifest_bytes)
    assert summary["failed_task_indices"] == [1]
    assert any("source tree mismatch" in item for item in summary["problems"])


def test_collector_rejects_source_count_mismatch(tmp_path):
    manifest, manifest_bytes = _fixture_run(tmp_path)
    result_path = tmp_path / "task-1/result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["source_file_count"] += 1
    result_path.write_text(json.dumps(result), encoding="utf-8")
    summary = collect_results(tmp_path, manifest, manifest_bytes)
    assert summary["failed_task_indices"] == [1]
    assert any("source file count mismatch" in item for item in summary["problems"])
