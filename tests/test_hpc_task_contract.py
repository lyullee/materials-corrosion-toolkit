import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.hpc_run_task import source_tree_digest, validate_manifest
from scripts.validate_hpc_manifest import validate_hpc_submission

ROOT = Path(__file__).resolve().parents[1]


def manifest_with_focused_pytest() -> dict:
    return {
        "schema_version": "matintegrity.hpc_tasks.v1",
        "pytest_shards": 1,
        "tasks": [
            {"kind": "pytest_shard", "shard_index": 0},
            {
                "kind": "pytest",
                "name": "focused-contract",
                "paths": ["tests/test_github_integration_catalog.py"],
            },
        ],
    }


def test_manifest_validation_rejects_duplicate_task_identity():
    payload = manifest_with_focused_pytest()
    payload["tasks"].append(
        {"kind": "pytest", "name": "focused-contract", "paths": ["tests/test_hpc_task_contract.py"]}
    )
    with pytest.raises(ValueError, match="unique"):
        validate_manifest(payload)


def test_manifest_validation_rejects_missing_or_escaping_pytest_paths(tmp_path):
    missing = manifest_with_focused_pytest()
    missing["tasks"][1]["paths"] = ["tests/not-a-real-test.py"]
    with pytest.raises(ValueError, match="missing file"):
        validate_manifest(missing)

    escaping = manifest_with_focused_pytest()
    outside = tmp_path / "test_outside.py"
    outside.write_text("def test_placeholder(): pass\n", encoding="utf-8")
    escaping["tasks"][1]["paths"] = [str(outside)]
    with pytest.raises(ValueError, match="escapes the project"):
        validate_manifest(escaping)


def test_focused_pytest_task_executes_and_records_junit(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_with_focused_pytest()), encoding="utf-8")
    output = tmp_path / "result"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hpc_run_task.py",
            "--task-index",
            "1",
            "--output-dir",
            str(output),
            "--manifest",
            str(manifest),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert json.loads(completed.stdout)["task_name"] == "focused-contract"
    assert result["returncode"] == 0
    assert result["runtime_versions"]["pytest"]
    assert len(result["source_tree_sha256"]) == 64
    assert result["source_file_count"] > 0
    assert Path(result["python_executable"]).is_absolute()
    assert (output / "junit.xml").is_file()


def test_repository_pbs_and_slurm_ranges_match_manifest():
    report = validate_hpc_submission(ROOT / "hpc/task_manifest.json", ROOT / "hpc/slurm_array.sh")
    assert report["task_count"] == report["valid_array_last"] + 1
    assert report["valid_array_first"] == 0
    assert report["slurm_index_guard"] == "runtime_index_within_manifest"
    assert report["pbs_index_guard"] == "runtime_index_within_manifest"


def test_pbs_range_mismatch_is_rejected(tmp_path):
    pbs_script = tmp_path / "pbs_array.sh"
    pbs_script.write_text("#PBS -J 0-80%16\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PBS script must require and bound"):
        validate_hpc_submission(
            ROOT / "hpc/task_manifest.json",
            ROOT / "hpc/slurm_array.sh",
            pbs_script,
        )


def test_parallel_pbs_bundle_derives_task_range_and_bounds_worker_count():
    script = (ROOT / "hpc/pbs_bundle.sh").read_text(encoding="utf-8")
    assert 'task_count="$(' in script
    assert 'seq 0 "$((task_count - 1))"' in script
    assert "MATINTEGRITY_PBS_WORKERS:-16" in script
    assert "workers > 64" in script
    assert "seq 0 75" not in script


def test_pbs_and_slurm_array_stage_private_data_by_reference():
    for name in ("pbs_array.sh", "slurm_array.sh"):
        script = (ROOT / "hpc" / name).read_text(encoding="utf-8")
        for private_data in ("raw", "derived", "evidence"):
            assert f'--exclude "data/{private_data}"' in script or (
                f"--exclude 'data/{private_data}'" in script
            )
        assert 'ln -s "${MATINTEGRITY_PROJECT}/data/${private_data}"' in script


def test_hpc_source_fingerprint_covers_public_release_allowlist():
    digest, file_count = source_tree_digest(ROOT)
    assert len(digest) == 64
    assert file_count >= 1500
