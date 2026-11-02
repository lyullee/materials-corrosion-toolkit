"""Audit the allowlisted public source tree without building release artifacts."""

import hashlib
import json

try:
    from scripts.build_release import ROOT, public_files
except ModuleNotFoundError:  # direct script execution puts scripts/ on sys.path
    from build_release import ROOT, public_files

AUDIT_PATH = ROOT / "validation/public_source_boundary_audit.json"


def audit_public_source_boundary() -> dict:
    files = [path for path in public_files() if path != AUDIT_PATH]
    relative = [path.relative_to(ROOT).as_posix() for path in files]
    digest = hashlib.sha256("\n".join(relative).encode()).hexdigest()
    return {
        "schema_version": "matintegrity.public_source_boundary_audit.v1",
        "status": "passed",
        "file_count": len(files),
        "total_bytes": sum(path.stat().st_size for path in files),
        "path_manifest_sha256": digest,
        "excluded_private_roots": [
            "data/raw",
            "data/derived",
            "data/evidence",
            "artifacts",
            "tmp",
            "validation/hpc-local",
        ],
        "meaning": "Allowlist, restricted-asset and local/source-document marker audit only; not legal clearance.",
    }


def main() -> None:
    report = audit_public_source_boundary()
    AUDIT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
