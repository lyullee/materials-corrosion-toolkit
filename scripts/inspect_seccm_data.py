"""Audit the pinned 316L SECCM archive without executing provider code."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import zipfile
from collections import Counter
from pathlib import Path

from matintegrity.seccm_data import (
    SECCM_ARCHIVE_SHA256,
    SECCM_CODE_COMMIT,
    SECCM_CODE_SHA256,
    SECCM_PROVIDER_MD5,
    audit_seccm_archive,
)

ROOT = Path(__file__).resolve().parents[1]


def _read_dict_rows(archive: zipfile.ZipFile, member: str, encoding: str = "utf-8-sig"):
    text = archive.read(member).decode(encoding)
    return list(csv.DictReader(io.StringIO(text)))


def _integer_ids(rows: list[dict[str, str]], field: str) -> list[int]:
    try:
        values = [int(row[field]) for row in rows]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"SECCM {field} values must be integer text") from exc
    return values


def _numeric_range(rows: list[dict[str, str]], field: str) -> list[float]:
    try:
        values = [float(row[field]) for row in rows]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"SECCM {field} values must be numeric") from exc
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"SECCM {field} values must be finite and nonempty")
    return [min(values), max(values)]


def _audit_related_tables(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        parameters = _read_dict_rows(archive, "SS_NaCl_Parameters_M_1031_C.csv")
        descriptors = _read_dict_rows(archive, "CA_SECCM_descriptors_area.csv")
        normalised = _read_dict_rows(
            archive,
            "CA_SECCM_descriptors_area_normalised.csv",
            encoding="cp1252",
        )
        labels = _read_dict_rows(archive, "labels.csv")
        pixels = _read_dict_rows(archive, "selected_oval_pixels.csv")
        sem = _read_dict_rows(archive, "SEM_EBSD.csv")
        ebsd = _read_dict_rows(archive, "ebsd_filtered.csv")

    expected_ids = set(range(1, 206))
    parameter_ids = _integer_ids(parameters, "x/y")
    descriptor_ids = _integer_ids(descriptors, "map_id")
    normalised_ids = _integer_ids(normalised, "map_id")
    label_ids = _integer_ids(labels, "map_id")
    pixel_ids = _integer_ids(pixels, "oval_id")
    if len(parameters) != 205 or set(parameter_ids) != expected_ids:
        raise ValueError("SECCM parameter identifiers must be a permutation of 1 through 205")
    if descriptor_ids != list(range(1, 206)) or normalised_ids != list(range(1, 206)):
        raise ValueError("SECCM descriptor identifiers must be ordered 1 through 205")
    if len(label_ids) != len(set(label_ids)) or not set(label_ids) <= expected_ids:
        raise ValueError("SECCM label identifiers must be a unique subset of 1 through 205")
    if set(pixel_ids) != expected_ids:
        raise ValueError("SECCM footprint identifiers must cover 1 through 205")

    pixel_counts = Counter(pixel_ids)
    label_counts = Counter(row["labels"] for row in labels)
    sem_coordinates = {(row["X"], row["Y"]) for row in sem}
    ebsd_coordinates = {(row["X"], row["Y"]) for row in ebsd}
    if len(sem_coordinates) != len(sem) or len(ebsd_coordinates) != len(ebsd):
        raise ValueError("SECCM imaging tables contain repeated coordinate text pairs")
    return {
        "acquisition_parameters": {
            "rows": len(parameters),
            "identifier_field": "x/y",
            "identifier_set": "permutation_1_through_205",
            "row_order_matches_map_id": parameter_ids == list(range(1, 206)),
            "blank_charge_retract_cells": sum(not row["Charge_Retract_C"].strip() for row in parameters),
            "position_x_range_unit_unreviewed": _numeric_range(parameters, "PosX"),
            "position_y_range_unit_unreviewed": _numeric_range(parameters, "PosY"),
            "map_id_crosswalk_status": "provider_description_only_not_promoted_to_join_contract",
        },
        "provider_descriptors": {
            "rows": len(descriptors),
            "map_ids": "ordered_1_through_205",
            "blank_cells": sum(not value.strip() for row in descriptors for value in row.values()),
            "role": "provider_curated_not_recomputed",
        },
        "provider_normalised_descriptors": {
            "rows": len(normalised),
            "map_ids": "ordered_1_through_205",
            "encoding": "cp1252",
            "blank_cells": sum(not value.strip() for row in normalised for value in row.values()),
            "role": "provider_derived_not_recomputed",
        },
        "provider_labels": {
            "rows": len(labels),
            "unique_map_ids": len(label_ids),
            "map_id_min": min(label_ids),
            "map_id_max": max(label_ids),
            "label_string_counts": dict(sorted(label_counts.items())),
            "role": "post_hoc_provider_annotations_not_independent_truth",
        },
        "footprint_pixels": {
            "rows": len(pixels),
            "oval_ids": "complete_1_through_205",
            "points_per_oval_min": min(pixel_counts.values()),
            "points_per_oval_max": max(pixel_counts.values()),
            "x_range_unit_unreviewed": _numeric_range(pixels, "x"),
            "y_range_unit_unreviewed": _numeric_range(pixels, "y"),
            "area_calculation_status": "not_recomputed",
        },
        "imaging_tables": {
            "sem_rows": len(sem),
            "ebsd_rows": len(ebsd),
            "sem_unique_coordinate_text_pairs": len(sem_coordinates),
            "ebsd_unique_coordinate_text_pairs": len(ebsd_coordinates),
            "sem_x_range_unit_unreviewed": _numeric_range(sem, "X"),
            "sem_y_range_unit_unreviewed": _numeric_range(sem, "Y"),
            "ebsd_x_range_unit_unreviewed": _numeric_range(ebsd, "X"),
            "ebsd_y_range_unit_unreviewed": _numeric_range(ebsd, "Y"),
            "registration_status": "not_qualified",
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "data/raw/seccm-ebsd-316l-pitting-v1/seccm-ebsd-316l-pitting_dataset.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/seccm_316l_pitting_dataset.json",
    )
    args = parser.parse_args()
    audit = audit_seccm_archive(args.archive)
    if audit.archive_md5 != SECCM_PROVIDER_MD5:
        raise ValueError("SECCM archive MD5 differs from the provider checksum")
    record = audit.model_dump(mode="json")
    record.update(
        provider_archive_md5=SECCM_PROVIDER_MD5,
        project_pinned_archive_sha256=SECCM_ARCHIVE_SHA256,
        provider_code_commit=SECCM_CODE_COMMIT,
        provider_code_evidence_sha256=SECCM_CODE_SHA256,
        provider_code_execution="not_executed",
        raw_ca_matrix={
            "sites": len(audit.map_ids),
            "samples_per_site": audit.sample_count_per_trace,
            "numeric_current_values": len(audit.map_ids) * audit.sample_count_per_trace,
            "time_unit": "s",
            "current_unit": "A",
            "nonfinite_values": 0,
        },
        related_table_structure=_audit_related_tables(args.archive),
        qualification=(
            "Checksum, archive membership, raw time/current units and numeric structure only. Map points "
            "are not independent specimens. Related-table identifiers and aggregate shapes are audited, "
            "but parameter, descriptor, label, SEM and EBSD cross-table alignment remains unqualified; "
            "no smoothing, descriptor reproduction, class truth, pit size, "
            "POD, life, acceptance or failure probability is produced."
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
