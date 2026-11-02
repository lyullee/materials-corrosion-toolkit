"""Check that the Nurion PBS array exactly covers the portable task manifest."""

import argparse
import json
import re
from pathlib import Path

try:
    from scripts.hpc_run_task import validate_manifest
except ModuleNotFoundError:
    from hpc_run_task import validate_manifest

ROOT = Path(__file__).resolve().parents[1]
ARRAY_PATTERN = re.compile(r"^#PBS\s+-J\s+(\d+)-(\d+)(?:%(\d+))?\s*$", re.MULTILINE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "hpc/task_manifest.json")
    parser.add_argument("--pbs", type=Path, default=ROOT / "hpc/pbs_array.sh")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    match = ARRAY_PATTERN.search(args.pbs.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("PBS script requires one explicit array range")
    first, last = (int(value) for value in match.groups()[:2])
    if (first, last) != (0, len(manifest["tasks"]) - 1):
        raise ValueError("PBS array bounds do not match the task manifest")
    print(
        json.dumps(
            {
                "schema_version": "matintegrity.pbs_submission_check.v1",
                "task_count": len(manifest["tasks"]),
                "array_first": first,
                "array_last": last,
                "concurrency_limit": int(match.group(3)) if match.group(3) else None,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
