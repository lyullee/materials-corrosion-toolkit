"""Run one isolated HPC validation-array task and record reproducible evidence."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_tree_digest(root: Path) -> tuple[str, int]:
    """Hash exactly the public allowlisted snapshot, including docs and data catalogs."""
    try:
        from scripts.build_release import public_files
    except ModuleNotFoundError:  # direct script execution puts scripts/ on sys.path
        from build_release import public_files

    paths = public_files()
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest(), len(paths)


def _runtime_versions() -> dict[str, str]:
    versions = {}
    for package in ("matintegrity", "pydantic", "numpy", "scipy", "pandas", "pytest", "ruff", "CoolProp"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            continue
    return versions


def validate_manifest(manifest: dict) -> None:
    if manifest.get("schema_version") != "matintegrity.hpc_tasks.v1":
        raise ValueError("unexpected HPC task manifest schema")
    shard_count = manifest.get("pytest_shards")
    tasks = manifest.get("tasks")
    if not isinstance(shard_count, int) or shard_count <= 0 or not isinstance(tasks, list) or not tasks:
        raise ValueError("HPC manifest requires positive pytest_shards and non-empty tasks")
    names = []
    shard_indices = []
    for index, task in enumerate(tasks):
        kind = task.get("kind")
        if kind == "pytest_shard":
            shard_indices.append(task.get("shard_index"))
            names.append(f"pytest-shard-{task.get('shard_index')}")
        elif kind == "pytest":
            if not task.get("name") or not task.get("paths"):
                raise ValueError(f"pytest task {index} requires name and paths")
            for task_path in task["paths"]:
                if not isinstance(task_path, str) or not task_path:
                    raise ValueError(f"pytest task {index} contains an invalid path")
                resolved = (ROOT / task_path).resolve()
                try:
                    resolved.relative_to(ROOT.resolve())
                except ValueError as exc:
                    raise ValueError(f"pytest task {index} path escapes the project") from exc
                if not resolved.is_file():
                    raise ValueError(f"pytest task {index} references missing file: {task_path}")
            names.append(task["name"])
        elif kind == "command":
            if not task.get("name") or not task.get("arguments"):
                raise ValueError(f"command task {index} requires name and arguments")
            names.append(task["name"])
        else:
            raise ValueError(f"unsupported task kind at {index}: {kind!r}")
    if shard_indices != list(range(shard_count)):
        raise ValueError("pytest shard tasks must cover ordered indices exactly once")
    if len(names) != len(set(names)):
        raise ValueError("HPC task names must be unique")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-index", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "hpc/task_manifest.json")
    args = parser.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    validate_manifest(manifest)
    tasks = manifest["tasks"]
    if not 0 <= args.task_index < len(tasks):
        parser.error(f"task index must be inside [0, {len(tasks)})")
    task = tasks[args.task_index]
    source_digest, source_file_count = source_tree_digest(ROOT)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if task["kind"] == "pytest_shard":
        name = f"pytest-shard-{task['shard_index']}"
        command = [
            sys.executable,
            "scripts/hpc_pytest_shard.py",
            "--shard-index",
            str(task["shard_index"]),
            "--shard-count",
            str(manifest["pytest_shards"]),
            "--junitxml",
            str(output / "junit.xml"),
        ]
        commands = [command]
    elif task["kind"] == "pytest":
        name = task["name"]
        commands = [
            [
                sys.executable,
                "-m",
                "pytest",
                *task["paths"],
                "--junitxml",
                str(output / "junit.xml"),
            ]
        ]
    else:
        name = task["name"]
        groups = [[]]
        for argument in task["arguments"]:
            if argument == "&&":
                groups.append([])
            else:
                groups[-1].append(argument)
        commands = [[sys.executable, *group] for group in groups]
    started = datetime.now(timezone.utc)
    records = []
    returncode = 0
    for command in commands:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, errors="replace")
        combined = completed.stdout + completed.stderr
        records.append(
            {
                "command": command,
                "returncode": completed.returncode,
                "output_sha256": hashlib.sha256(combined.encode()).hexdigest(),
                "output": combined,
            }
        )
        if completed.returncode:
            returncode = completed.returncode
            break
    result = {
        "schema_version": "matintegrity.hpc_task_result.v1",
        "task_index": args.task_index,
        "task_name": name,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_tree_sha256": source_digest,
        "source_file_count": source_file_count,
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "python_executable": str(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "runtime_versions": _runtime_versions(),
        "returncode": returncode,
        "commands": records,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"task_index": args.task_index, "task_name": name, "returncode": returncode}))
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
