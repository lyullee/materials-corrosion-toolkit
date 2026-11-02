"""Synthetic request shape for local EIS magnitude/phase conversion."""

from matintegrity.contracts import Evidence
from matintegrity.ti12mo5zr_corrosion_data import (
    Ti12Mo5ZrRawRow,
    Ti12Mo5ZrWorkbookProvenance,
)
from matintegrity.ti12mo5zr_eis_complex import (
    EIS_MEMBER_SHA256,
    Ti12Mo5ZrComplexEISRequest,
    evaluate_ti12mo5zr_complex_eis,
)

member_path = "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.1.xls"
provenance = Ti12Mo5ZrWorkbookProvenance(
    member_path=member_path,
    member_bytes=33_280,
    member_sha256=EIS_MEMBER_SHA256[member_path],
    row_count_including_header=75,
    column_count=5,
    source_kind="eis_spectrum",
)
headers = ("Index", "Frequency (Hz)", "Time [s]", "|Z| [Ohm]", "WE.-Phase [deg]")
synthetic_rows = tuple(
    Ti12Mo5ZrRawRow(
        provenance=provenance,
        source_row_number=row_number,
        raw_headers=headers,
        raw_cells=(row_number - 1, 1000.0 / (row_number - 1), float(row_number - 2), 1200.0, -35.0),
    )
    for row_number in range(2, 76)
)

request = Ti12Mo5ZrComplexEISRequest(
    rows=synthetic_rows,
    phase_sign=1,
    phase_convention="reported_phase_positive_imaginary",
    phase_convention_evidence=Evidence(
        source_id="caller_ti12mo5zr_eis_phase_convention",
        origin="synthetic",
        citation="Synthetic demonstration of a caller phase-sign choice",
    ),
    phase_convention_reviewed=True,
    computational_use_authorized=True,
    local_only_authorized=True,
)
result = evaluate_ti12mo5zr_complex_eis(request)
