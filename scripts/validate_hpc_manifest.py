"""Check task-manifest structure and runtime array-index guards before submission."""

import argparse
import hashlib
import json
from pathlib import Path

try:
    from scripts.hpc_run_task import validate_manifest
except ModuleNotFoundError:  # direct script execution puts scripts/ on sys.path
    from hpc_run_task import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
SLURM_INDEX_GUARD = '"${SLURM_ARRAY_TASK_ID:?Slurm array index is required}"'
PBS_INDEX_GUARD = '"${PBS_ARRAY_INDEX:?PBS array index is required}"'


def validate_hpc_submission(manifest_path: Path, slurm_path: Path, pbs_path: Path | None = None) -> dict:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    validate_manifest(manifest)
    slurm_text = slurm_path.read_text(encoding="utf-8")
    if SLURM_INDEX_GUARD not in slurm_text or "SLURM_ARRAY_TASK_ID >= task_count" not in slurm_text:
        raise ValueError("Slurm script must require and bound the array index against manifest task count")
    pbs_script = pbs_path or ROOT / "hpc/pbs_array.sh"
    pbs_text = pbs_script.read_text(encoding="utf-8")
    if PBS_INDEX_GUARD not in pbs_text or "PBS_ARRAY_INDEX >= task_count" not in pbs_text:
        raise ValueError("PBS script must require and bound the array index against manifest task count")
    return {
        "schema_version": "matintegrity.hpc_submission_check.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "task_count": len(manifest["tasks"]),
        "valid_array_first": 0,
        "valid_array_last": len(manifest["tasks"]) - 1,
        "slurm_index_guard": "runtime_index_within_manifest",
        "pbs_index_guard": "runtime_index_within_manifest",
        "pytest_shards": manifest["pytest_shards"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "hpc/task_manifest.json")
    parser.add_argument("--slurm", type=Path, default=ROOT / "hpc/slurm_array.sh")
    parser.add_argument("--pbs", type=Path, default=ROOT / "hpc/pbs_array.sh")
    args = parser.parse_args()
    print(json.dumps(validate_hpc_submission(args.manifest, args.slurm, args.pbs), indent=2))


if __name__ == "__main__":
    main()
