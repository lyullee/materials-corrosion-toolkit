"""Readers for the pinned C1/C2 crack-arrest raw-test archive."""

from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from pathlib import Path

EXPECTED_COLUMNS = ("Time Sec", "Weg mm", "Kraft kN", "Sandner_1191 mm", "Cycle")
ROOT = "Raw test data of C1 and C2 crack arrest toughness test/Raw data "


def _archive(path: str | Path):
    source = Path(path)
    return source, zipfile.ZipFile(source)


def _metadata(member: str) -> dict:
    normalized = member.replace("\\", "/")
    if not normalized.startswith(ROOT) or not normalized.lower().endswith(".csv"):
        raise ValueError("unexpected crack-arrest archive member")
    relative = normalized[len(ROOT) :]
    family, filename = relative.split("/", 1)
    if family not in {"C1", "C2"} or "/" in filename:
        raise ValueError("expected one C1 or C2 folder level")
    stem = filename[:-4]
    pattern = r"^L7_(m?)(\d+)(?:[pP](\d+))?_" if family == "C1" else r"_(m?)(\d+)(?:[pP](\d+))?$"
    match = re.search(pattern, stem)
    if match is None:
        raise ValueError("temperature token cannot be resolved from source filename")
    magnitude = float(match.group(2) + ("." + match.group(3) if match.group(3) else ""))
    temperature_C = -magnitude if match.group(1) else magnitude
    return {
        "specimen_id": stem,
        "test_family": family,
        "reported_temperature_C": temperature_C,
        "reported_temperature_K": temperature_C + 273.15,
        "source_member": normalized,
    }


def list_crack_arrest_runs(path: str | Path):
    """List source identities and filename-derived temperatures without opening point data."""
    import pandas as pd

    source, archive = _archive(path)
    with archive:
        rows = [_metadata(name) for name in archive.namelist() if name.lower().endswith(".csv")]
    frame = pd.DataFrame(rows).sort_values(["test_family", "reported_temperature_K", "specimen_id"])
    if len(frame) != 18 or not frame.specimen_id.is_unique:
        raise ValueError("expected 18 unique C1/C2 source files")
    frame.attrs.update(
        source_id="crack-arrest-c1-c2",
        source_doi="10.17632/g69875w65c.1",
        source_archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        license_id="CC-BY-4.0",
        temperature_origin="parsed from source filenames and not independently checked against specimen logs",
        limitations=[
            "C1 and C2 are different crack-arrest test families; rows and channels are not additional specimens.",
            "Filename temperature is preserved as reported metadata and is not a verified specimen-temperature history.",
            "This archive does not by itself supply an initiation toughness, service lower bound or FAD assessment curve.",
        ],
    )
    return frame.reset_index(drop=True)


def _normalized_header(line: str) -> tuple[str, ...]:
    # One source file quotes the complete header instead of each field. Normalize only that exact
    # representational defect; point rows and channel signs remain untouched.
    parsed = next(csv.reader([line], delimiter=";"))
    if len(parsed) == 1:
        parsed = [item.strip('"') for item in parsed[0].split(";")]
    return tuple(item.strip().strip('"') for item in parsed)


def read_crack_arrest_series(path: str | Path, specimen_id: str):
    """Read one raw signed machine series and preserve the source sample clock."""
    import numpy as np
    import pandas as pd

    if not specimen_id or "/" in specimen_id or "\\" in specimen_id or specimen_id.lower().endswith(".csv"):
        raise ValueError("specimen_id must be a source filename stem")
    source, archive = _archive(path)
    with archive:
        matches = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv") and Path(name).stem == specimen_id
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one source member for specimen {specimen_id!r}, found {len(matches)}")
        member = matches[0]
        payload = archive.read(member)
    text = payload.decode("utf-8-sig")
    lines = text.splitlines()
    if len(lines) < 2 or _normalized_header(lines[0]) != EXPECTED_COLUMNS:
        raise ValueError("crack-arrest raw column names changed")
    rows = list(csv.reader(io.StringIO("\n".join(lines[1:])), delimiter=";"))
    if not rows or any(len(row) != 5 for row in rows):
        raise ValueError("complete five-column crack-arrest rows required")
    numeric = np.asarray([[float(value) for value in row] for row in rows], dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("finite crack-arrest values required")
    if numeric[0, 0] < 0 or np.any(np.diff(numeric[:, 0]) <= 0):
        raise ValueError("source time must be nonnegative and strictly increasing")
    if np.any(numeric[:, 4] < 0) or np.any(numeric[:, 4] != np.floor(numeric[:, 4])):
        raise ValueError("cycle channel must contain nonnegative integer values")
    metadata = _metadata(member)
    frame = pd.DataFrame(
        {
            "time_s": numeric[:, 0],
            "machine_displacement_m": numeric[:, 1] * 1e-3,
            "force_N": numeric[:, 2] * 1e3,
            "extensometer_displacement_m": numeric[:, 3] * 1e-3,
            "reported_cycle_index": numeric[:, 4].astype(int),
        }
    )
    frame.attrs.update(
        source_id="crack-arrest-c1-c2",
        source_doi="10.17632/g69875w65c.1",
        source_archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        source_member=metadata["source_member"],
        source_member_sha256=hashlib.sha256(payload).hexdigest(),
        license_id="CC-BY-4.0",
        specimen_id=metadata["specimen_id"],
        test_family=metadata["test_family"],
        reported_temperature_K=metadata["reported_temperature_K"],
        temperature_origin="parsed from source filename; not independently checked against specimen logs",
        channel_basis={
            "machine_displacement_m": "source Weg mm converted by 1e-3; sign and zero retained",
            "force_N": "source Kraft kN converted by 1e3; sign and zero retained",
            "extensometer_displacement_m": "source Sandner_1191 mm converted by 1e-3; sign and zero retained",
        },
        limitations=[
            "No zeroing, sign reversal, filtering, resampling, compliance correction or event picking is applied.",
            "Machine and extensometer displacement meanings inherit the source labels; geometry and validity metadata require separate evidence.",
            "A raw force-displacement series is not a qualified toughness value or FAD validation point.",
        ],
    )
    return frame
