"""Show the provenance-only API; run locally after placing the Zenodo ZIP."""

from pathlib import Path

from matintegrity.ti12mo5hf_corrosion_data import (
    DEFAULT_LOCAL_DIRECTORY,
    ARCHIVE_NAME,
    audit_local_archive,
    declared_conditions,
)


def main() -> None:
    # Synthetic caller-owned example: this is not a provider measurement.
    local_zip = DEFAULT_LOCAL_DIRECTORY / ARCHIVE_NAME
    if not local_zip.is_file():
        print(f"Local dataset not installed: {local_zip}")
        print("Download it from the Zenodo record linked in the dataset guide.")
        return

    audit = audit_local_archive(local_zip)
    print("Dataset:", audit.dataset_id)
    print("Archive SHA-256:", audit.archive_sha256)
    print("Archive members:", audit.member_count)
    print("Expanded byte count:", audit.uncompressed_total_bytes)
    print("Conditions are provider metadata only:")
    for condition in declared_conditions():
        print(" ", condition.alloy_label, condition.environment_label)


if __name__ == "__main__":
    main()
