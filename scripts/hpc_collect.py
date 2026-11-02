"""Aggregate HPC results and reject missing or identity-inconsistent task records."""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.hpc_run_task import validate_manifest
except ModuleNotFoundError:  # direct script execution puts scripts/ on sys.path
    from hpc_run_task import validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def _expected_command_count(task: dict) -> int:
    if task["kind"] in {"pytest", "pytest_shard"}:
        return 1
    return 1 + task["arguments"].count("&&")


def collect_results(results_dir: Path, manifest: dict, manifest_bytes: bytes) -> dict:
    """Summarize a full run only when result identities and executed commands match its manifest."""
    validate_manifest(manifest)
    expected_digest = hashlib.sha256(manifest_bytes).hexdigest()
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    completed = 0
    observed_source_digest = None
    observed_source_file_count = None
    failed_tasks = []
    problems = []

    for index, task in enumerate(manifest["tasks"]):
        problems_before = len(problems)
        folder = results_dir / f"task-{index}"
        result_path = folder / "result.json"
        if not result_path.is_file():
            problems.append(f"missing task {index}")
            failed_tasks.append(index)
            continue
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            problems.append(f"unreadable result for task {index}: {error}")
            failed_tasks.append(index)
            continue

        if not isinstance(result, dict):
            problems.append(f"result is not an object for task {index}")
            failed_tasks.append(index)
            continue
        completed += 1
        expected_name = (
            f"pytest-shard-{task['shard_index']}" if task["kind"] == "pytest_shard" else task.get("name")
        )
        if result.get("schema_version") != "matintegrity.hpc_task_result.v1":
            problems.append(f"unexpected result schema for task {index}")
        if result.get("task_index") != index or result.get("task_name") != expected_name:
            problems.append(f"task identity mismatch for task {index}")
        if result.get("manifest_sha256") != expected_digest:
            problems.append(f"manifest mismatch for task {index}")
        source_digest = result.get("source_tree_sha256")
        valid_digest = (
            isinstance(source_digest, str)
            and len(source_digest) == 64
            and all(character in "0123456789abcdef" for character in source_digest)
        )
        if not valid_digest:
            problems.append(f"missing or invalid source tree digest for task {index}")
        elif observed_source_digest is None:
            observed_source_digest = source_digest
        elif source_digest != observed_source_digest:
            problems.append(f"source tree mismatch for task {index}")
        source_file_count = result.get("source_file_count")
        if type(source_file_count) is not int or source_file_count <= 0:
            problems.append(f"missing or invalid source file count for task {index}")
        elif observed_source_file_count is None:
            observed_source_file_count = source_file_count
        elif source_file_count != observed_source_file_count:
            problems.append(f"source file count mismatch for task {index}")

        commands = result.get("commands")
        if (
            not isinstance(commands, list)
            or len(commands) != _expected_command_count(task)
            or any(not isinstance(record, dict) for record in commands)
        ):
            problems.append(f"command record count mismatch for task {index}")
            command_status = None
        else:
            command_codes = [record.get("returncode") for record in commands]
            if any(type(code) is not int for code in command_codes):
                problems.append(f"invalid command status for task {index}")
                command_status = None
            else:
                command_status = next((code for code in command_codes if code != 0), 0)
        if result.get("returncode") != command_status:
            problems.append(f"task and command status mismatch for task {index}")
        if command_status != 0:
            problems.append(f"task {index} failed")

        if task["kind"] in {"pytest_shard", "pytest"}:
            junit = folder / "junit.xml"
            if not junit.is_file():
                problems.append(f"missing JUnit for task {index}")
            else:
                try:
                    root = ET.parse(junit).getroot()
                    suites = list(root.iter("testsuite"))
                    if not suites:
                        problems.append(f"JUnit has no test suites for task {index}")
                    for key in totals:
                        totals[key] += sum(int(suite.get(key, "0")) for suite in suites)
                except (ET.ParseError, OSError, ValueError) as error:
                    problems.append(f"unreadable JUnit for task {index}: {error}")

        if len(problems) > problems_before:
            failed_tasks.append(index)

    return {
        "schema_version": "matintegrity.hpc_summary.v1",
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": expected_digest,
        "source_tree_sha256": observed_source_digest,
        "source_file_count": observed_source_file_count,
        "task_count": len(manifest["tasks"]),
        "completed_task_count": completed,
        "failed_task_indices": sorted(set(failed_tasks)),
        **totals,
        "problems": problems,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "hpc/task_manifest.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    summary = collect_results(args.results_dir, manifest, manifest_bytes)
    target = args.output or args.results_dir / "summary.json"
    target.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    raise SystemExit(1 if summary["problems"] else 0)


if __name__ == "__main__":
    main()
