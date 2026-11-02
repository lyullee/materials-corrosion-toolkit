"""Read paired experimental-life and processed critical-plane files without double counting."""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

METHODS = ("FS", "SWT")
FILENAME = re.compile(
    r"^(?P<method>FS|SWT)_(?P<load>ASS|TOR|MULTI)_(?P<specimen>BLUNT|SHARP)"
    r"(?:_PSI(?P<phase>0|45|90)_LAMB(?P<lambda>1|2))?_R(?P<ratio>-1|01|05)\.txt$"
)
STRESS_RATIO = {"-1": -1.0, "01": 0.1, "05": 0.5}


def _filename_metadata(path: Path) -> dict:
    match = FILENAME.fullmatch(path.name)
    if match is None:
        raise ValueError(f"unrecognized multiaxial-fatigue filename: {path.name}")
    values = match.groupdict()
    if values["load"] == "MULTI" and (values["phase"] is None or values["lambda"] is None):
        raise ValueError("combined-loading files require phase and biaxiality tokens")
    if values["load"] != "MULTI" and (values["phase"] is not None or values["lambda"] is not None):
        raise ValueError("single-channel files cannot carry combined-loading tokens")
    configuration_id = path.name.split("_", 1)[1].removesuffix(".txt")
    return {
        "method": values["method"],
        "configuration_id": configuration_id,
        "provider_load_code": values["load"],
        "specimen_geometry_code": values["specimen"],
        "phase_angle_deg": None if values["phase"] is None else int(values["phase"]),
        "biaxiality_ratio": None if values["lambda"] is None else float(values["lambda"]),
        "stress_ratio": STRESS_RATIO[values["ratio"]],
    }


def _read_rows(path: Path) -> list[tuple[float, float, float]]:
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row_number, row in enumerate(csv.reader(stream, delimiter="\t"), 1):
            if len(row) != 3:
                raise ValueError(f"expected three tab-separated values in {path.name} row {row_number}")
            try:
                values = tuple(float(value) for value in row)
            except ValueError as exc:
                raise ValueError(f"nonnumeric value in {path.name} row {row_number}") from exc
            if not all(math.isfinite(value) and value > 0 for value in values):
                raise ValueError(f"positive finite values required in {path.name} row {row_number}")
            rows.append(values)
    if not rows:
        raise ValueError(f"empty multiaxial-fatigue file: {path.name}")
    return rows


def read_ecp_multiaxial_fatigue(directory: str | Path) -> dict:
    """Read paired FS/SWT tables while retaining one experimental observation per row pair."""
    import pandas as pd

    directory = Path(directory)
    files = sorted(directory.glob("*.txt"))
    if not files:
        raise ValueError("no multiaxial-fatigue text files found")

    parsed: dict[tuple[str, str], tuple[Path, dict, list[tuple[float, float, float]]]] = {}
    for path in files:
        metadata = _filename_metadata(path)
        key = (metadata["configuration_id"], metadata["method"])
        if key in parsed:
            raise ValueError(f"duplicate method/configuration file: {key}")
        parsed[key] = (path, metadata, _read_rows(path))

    configurations = sorted({key[0] for key in parsed})
    expected = {(configuration, method) for configuration in configurations for method in METHODS}
    missing = sorted(expected - set(parsed))
    unexpected = sorted(set(parsed) - expected)
    if missing or unexpected:
        raise ValueError(f"paired FS/SWT files required; missing={missing}, unexpected={unexpected}")

    observations = []
    processed = []
    configuration_rows = []
    for configuration in configurations:
        fs_path, fs_meta, fs_rows = parsed[(configuration, "FS")]
        swt_path, swt_meta, swt_rows = parsed[(configuration, "SWT")]
        common_keys = (
            "provider_load_code",
            "specimen_geometry_code",
            "phase_angle_deg",
            "biaxiality_ratio",
            "stress_ratio",
        )
        if any(fs_meta[key] != swt_meta[key] for key in common_keys):
            raise ValueError(f"paired filename metadata differs for {configuration}")
        if len(fs_rows) != len(swt_rows):
            raise ValueError(f"paired row count differs for {configuration}")
        fs_lives = [row[0] for row in fs_rows]
        swt_lives = [row[0] for row in swt_rows]
        if fs_lives != swt_lives:
            raise ValueError(f"paired experimental lives differ for {configuration}")

        configuration_rows.append(
            {
                "configuration_id": configuration,
                **{key: fs_meta[key] for key in common_keys},
                "observation_rows": len(fs_rows),
                "physical_specimen_identity_status": "not_supplied_in_dataset_files",
                "endpoint_definition_status": "requires_linked_article_review",
            }
        )
        for index, experimental_life in enumerate(fs_lives, 1):
            observation_id = f"{configuration}:row-{index}"
            observations.append(
                {
                    "article_local_observation_id": observation_id,
                    "configuration_id": configuration,
                    **{key: fs_meta[key] for key in common_keys},
                    "reported_cycles_to_failure": experimental_life,
                    "source_filenames": (fs_path.name, swt_path.name),
                    "source_row": index,
                    "physical_specimen_id": None,
                    "physical_specimen_independence_reviewed": False,
                    "censoring_status": "not_reported_in_dataset_files",
                    "endpoint_definition_status": "requires_linked_article_review",
                }
            )
            for path, metadata, rows in (
                (fs_path, fs_meta, fs_rows),
                (swt_path, swt_meta, swt_rows),
            ):
                _, factor, predicted_life = rows[index - 1]
                processed.append(
                    {
                        "article_local_observation_id": observation_id,
                        "configuration_id": configuration,
                        "method": metadata["method"],
                        "reported_ecp_factor": factor,
                        "provider_predicted_cycles": predicted_life,
                        "source_filename": path.name,
                        "source_row": index,
                        "prediction_role": "provider_processed_same_study",
                        "independent_prediction_validation": False,
                    }
                )

    return {
        "source_id": "ecp-multiaxial-fatigue",
        "configurations": pd.DataFrame(configuration_rows),
        "experimental_observations": pd.DataFrame(observations),
        "processed_method_rows": pd.DataFrame(processed),
        "qualification": (
            "Experimental life is represented once per paired FS/SWT row. Method-specific ECP factors "
            "and predicted lives remain processed outputs from the same study. Dataset files do not "
            "supply physical specimen identifiers, censoring flags, endpoint definitions, local tensor "
            "histories or finite-element meshes; none are inferred."
        ),
    }
