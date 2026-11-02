"""Inspect the pinned train/test fracture-toughness compilation without fitting a model."""

from __future__ import annotations

import json
from pathlib import Path

from matintegrity.fracture_toughness_data import (
    ARTICLE_REFERENCE_CATALOG,
    read_fracture_toughness_temperature,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/fracture-toughness-temperature/2vkgrbsy8j-1.zip"


def inspect_fracture_toughness_data(path: Path = ARCHIVE) -> dict:
    frame = read_fracture_toughness_temperature(path)
    partition_counts = frame.source_partition.value_counts().sort_index().to_dict()
    type_counts = frame.specimen_type.value_counts().sort_index().to_dict()
    full_columns = [
        "carbon_wt_percent",
        "reported_temperature",
        "yield_strength_MPa",
        "specimen_type",
        "reported_W",
        "reported_B",
        "reported_a",
        "reported_KJc_MPa_sqrt_m",
        "material_label",
    ]
    training = frame.loc[frame.source_partition.eq("training"), full_columns]
    test = frame.loc[frame.source_partition.eq("test"), full_columns]
    overlap = len(
        set(map(tuple, training.itertuples(index=False, name=None)))
        & set(map(tuple, test.itertuples(index=False, name=None)))
    )
    result = {
        "source_id": frame.attrs["source_id"],
        "source_archive_sha256": frame.attrs["source_archive_sha256"],
        "source_member_sha256": frame.attrs["source_member_sha256"],
        "license_id": frame.attrs["license_id"],
        "rows": len(frame),
        "partition_rows": partition_counts,
        "materials": int(frame.material_label.nunique()),
        "specimen_type_rows": type_counts,
        "reported_temperature_range": [
            float(frame.reported_temperature.min()),
            float(frame.reported_temperature.max()),
        ],
        "source_temperature_unit_label": "K",
        "normalized_temperature_rows": int(frame.temperature_K.notna().sum()),
        "temperature_unit_resolution": (
            "negative values conflict with the workbook K label; associated article DOI "
            "10.1016/j.engfailanal.2020.104458 identifies the tested-temperature feature in degrees Celsius"
        ),
        "normalized_temperature_range_K": [
            float(frame.temperature_K.min()),
            float(frame.temperature_K.max()),
        ],
        "source_dimension_unit_label": None,
        "dimension_unit_resolution": (
            "the associated article defines W, B and a and identifies T-size thicknesses in millimetres; "
            "all 640 workbook rows match the reviewed millimetre thickness scale"
        ),
        "normalized_dimension_rows": int(frame[["W_m", "B_m", "a_m"]].notna().all(axis=1).sum()),
        "dimension_unit_basis_rows": frame.dimension_unit_basis.value_counts().sort_index().to_dict(),
        "reported_thickness_range": [float(frame.reported_B.min()), float(frame.reported_B.max())],
        "normalized_thickness_range_m": [float(frame.B_m.min()), float(frame.B_m.max())],
        "reported_crack_ratio_range": [
            float((frame.reported_a / frame.reported_W).min()),
            float((frame.reported_a / frame.reported_W).max()),
        ],
        "reported_yield_strength_range_MPa": [
            float(frame.yield_strength_MPa.min()),
            float(frame.yield_strength_MPa.max()),
        ],
        "reported_KJc_range_MPa_sqrt_m": [
            float(frame.reported_KJc_MPa_sqrt_m.min()),
            float(frame.reported_KJc_MPa_sqrt_m.max()),
        ],
        "identical_rows_across_partitions": overlap,
        "physical_specimen_ids_present": int(frame.physical_specimen_id.notna().sum()),
        "condition_groups": int(frame.condition_group_id.nunique()),
        "condition_group_relative_tolerance": frame.attrs["condition_group_relative_tolerance"],
        "condition_group_absolute_tolerance_m": frame.attrs["condition_group_absolute_tolerance_m"],
        "condition_group_status_rows": frame.condition_group_status.value_counts().sort_index().to_dict(),
        "condition_groups_present_in_both_partitions": int(
            frame.groupby("condition_group_id").source_partition.nunique().eq(2).sum()
        ),
        "condition_group_physical_independence_reviewed_rows": int(
            frame.condition_group_physical_independence_reviewed.sum()
        ),
        "underlying_literature_ids_present": int(frame.underlying_literature_id.notna().sum()),
        "article_source_group_status_rows": (
            frame.article_source_group_status.value_counts().sort_index().to_dict()
        ),
        "article_source_groups_present": int(frame.article_source_group_id.notna().sum()),
        "article_source_group_unresolved_materials": sorted(
            frame.loc[frame.article_source_group_status.eq("unresolved"), "material_label"].unique()
        ),
        "article_source_group_probable_variants": {
            row.material_label: row.article_source_material_label
            for row in frame.loc[
                frame.article_source_group_status.eq("probable_name_variant"),
                ["material_label", "article_source_material_label"],
            ]
            .drop_duplicates()
            .itertuples(index=False)
        },
        "article_reference_catalog_entries": len(ARTICLE_REFERENCE_CATALOG),
        "article_reference_catalog_resolved_dois": sum(
            record["identity_status"] == "resolved_doi" for record in ARTICLE_REFERENCE_CATALOG.values()
        ),
        "article_reference_identity_status_rows": (
            frame.article_reference_identity_status.value_counts().sort_index().to_dict()
        ),
        "article_reference_bibliographic_id_rows": int(
            frame.article_reference_bibliographic_id.notna().sum()
        ),
        "article_reference_observation_rights_status_rows": (
            frame.article_reference_observation_rights_status.value_counts().sort_index().to_dict()
        ),
        "workbook_formula_execution": frame.attrs["workbook_formula_execution"],
        "qualification": (
            "Compiled reported KJc rows with provider train/test labels. The associated article resolves the "
            "conflicting workbook temperature label to degrees Celsius and identifies the dimension scale as "
            "millimetres; physical-specimen independence, row-level original literature identity and test validity "
            "remain unresolved. Article-local "
            "source groups are recorded as exact, probable-name-variant or unresolved screening links. Seven of nine "
            "article references have resolved DOIs, but no underlying-observation redistribution right is claimed. "
            "All geometry condition groups cross the provider split, so it is not treated as an independent holdout. "
            "No toughness model, standard rule or FAD boundary is fitted."
        ),
    }
    expected = {
        "rows": 640,
        "partition_rows": {"test": 192, "training": 448},
        "materials": 14,
        "specimen_type_rows": {"CT": 394, "PCCv": 81, "SEB": 165},
        "normalized_temperature_rows": 640,
        "normalized_dimension_rows": 640,
        "dimension_unit_basis_rows": {"article_mm": 640},
        "article_source_group_status_rows": {
            "article_table_exact": 614,
            "probable_name_variant": 18,
            "unresolved": 8,
        },
        "article_reference_catalog_entries": 9,
        "article_reference_catalog_resolved_dois": 7,
        "article_reference_identity_status_rows": {
            "bibliography_only": 456,
            "resolved_doi": 176,
            "unresolved_source_group": 8,
        },
        "article_reference_bibliographic_id_rows": 176,
        "article_reference_observation_rights_status_rows": {"unresolved": 640},
        "condition_groups": 34,
        "condition_group_relative_tolerance": 0.03,
        "condition_group_absolute_tolerance_m": 1e-4,
        "condition_group_status_rows": {"geometry_condition_only": 640},
        "condition_groups_present_in_both_partitions": 34,
        "condition_group_physical_independence_reviewed_rows": 0,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise ValueError(f"pinned fracture-toughness workbook changed: {key}")
    return result


if __name__ == "__main__":
    print(json.dumps(inspect_fracture_toughness_data(), indent=2, ensure_ascii=False))
