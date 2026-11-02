"""Unexecuted example for locally streaming one pinned aqueous-corrosion file."""

from pathlib import Path

from matintegrity.ti12mo5zr_corrosion_data import (
    Ti12Mo5ZrWorkbookRequest,
    iter_local_rows,
)


def read_local_ocp_rows(archive_path: Path):
    request = Ti12Mo5ZrWorkbookRequest(
        local_archive_path=str(archive_path),
        member_path="zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.1.xls",
        computational_use_authorized=True,
        local_only_authorized=True,
    )
    yield from iter_local_rows(request)


if __name__ == "__main__":
    local_zip = Path("data/raw/zenodo-ti12mo5zr-aqueous-corrosion/zenodo_APSUC_2024.zip")
    for _raw_row in read_local_ocp_rows(local_zip):
        # A consuming pipeline receives provenance and unmodified source cells.
        # Keep conversions, segmentation, and assessment in separately reviewed modules.
        pass
