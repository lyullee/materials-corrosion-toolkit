"""Unexecuted example: consume only the pinned local AESEC row stream."""

from pathlib import Path

from matintegrity.ti12mo5hf_aesec_rows import (
    Ti12Mo5HfAESECRequest,
    iter_local_aesec_rows,
)


def consume_local_aesec(archive_path: Path):
    request = Ti12Mo5HfAESECRequest(
        local_archive_path=str(archive_path),
        member_path="Data_Zenodo_EA2026/AESEC/Ti12Mo5Hf.xlsx",
        computational_use_authorized=True,
        local_only_authorized=True,
    )
    for row in iter_local_aesec_rows(request):
        # Send each provenance-bearing raw row to a caller-owned pipeline.
        # Keep unit conversion, segmentation, and interpretation in a separate model.
        yield row


if __name__ == "__main__":
    local = Path("data/raw/zenodo-ti12mo5hf-oxygen-corrosion/Data_Zenodo_EA2026.zip")
    for _row in consume_local_aesec(local):
        pass
