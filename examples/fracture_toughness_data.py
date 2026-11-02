"""Summarize a reviewed fracture-toughness workbook without printing pointwise observations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.fracture_toughness_data import read_fracture_toughness_temperature


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--temperature-unit", choices=("degC", "K"))
    parser.add_argument("--dimension-unit", choices=("mm", "m"))
    parser.add_argument("--no-article-dimension-review", action="store_true")
    parser.add_argument("--condition-group-relative-tolerance", type=float, default=0.03)
    parser.add_argument("--condition-group-absolute-tolerance-m", type=float, default=1e-4)
    args = parser.parse_args()
    frame = read_fracture_toughness_temperature(
        args.archive,
        temperature_unit_override=args.temperature_unit,
        dimension_unit_override=args.dimension_unit,
        apply_article_dimension_review=not args.no_article_dimension_review,
        condition_group_relative_tolerance=args.condition_group_relative_tolerance,
        condition_group_absolute_tolerance_m=args.condition_group_absolute_tolerance_m,
    )
    print(
        json.dumps(
            {
                "rows": len(frame),
                "partition_rows": frame.source_partition.value_counts().sort_index().to_dict(),
                "materials": int(frame.material_label.nunique()),
                "temperature_unit_override": args.temperature_unit,
                "normalized_temperature_rows": int(frame.temperature_K.notna().sum()),
                "dimension_unit_override": args.dimension_unit,
                "apply_article_dimension_review": not args.no_article_dimension_review,
                "normalized_dimension_rows": int(frame[["W_m", "B_m", "a_m"]].notna().all(axis=1).sum()),
                "condition_groups": int(frame.condition_group_id.nunique()),
                "condition_groups_present_in_both_partitions": int(
                    frame.groupby("condition_group_id").source_partition.nunique().eq(2).sum()
                ),
                "condition_group_relative_tolerance": frame.attrs["condition_group_relative_tolerance"],
                "condition_group_absolute_tolerance_m": frame.attrs["condition_group_absolute_tolerance_m"],
                "article_source_group_status_rows": (
                    frame.article_source_group_status.value_counts().sort_index().to_dict()
                ),
                "article_reference_identity_status_rows": (
                    frame.article_reference_identity_status.value_counts().sort_index().to_dict()
                ),
                "observation_rights_status_rows": (
                    frame.article_reference_observation_rights_status.value_counts().sort_index().to_dict()
                ),
                "qualification": (
                    "Reported compiled rows and article-local source-group screening only; no row-level "
                    "literature identity, specimen-independence, test-validity, lower-bound, FAD or "
                    "failure-probability claim. Geometry groups are leakage-control strata only."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
