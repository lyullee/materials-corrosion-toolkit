"""Audit the pinned corrosion-alloy metric workbook without fitting a model."""

from __future__ import annotations

import json
from pathlib import Path

from matintegrity.corrosion_metrics_data import read_corrosion_alloy_metrics

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = (
    ROOT
    / "data/raw/corrosion-resistant-alloy-metrics"
    / "CRA_database_Scientific_Data_Publication_12102020.xlsx"
)
OUTPUT = ROOT / "validation/corrosion_alloy_metrics_package.json"


def inspect_corrosion_alloy_metrics(path: Path = WORKBOOK) -> dict:
    frame = read_corrosion_alloy_metrics(path, require_pinned_hash=True)
    special = frame.loc[
        frame.value_status.isin(["lower_bound", "upper_bound", "qualitative", "exact_text_numeric"])
    ]
    result = {
        "source_id": frame.attrs["source_id"],
        "source_doi": frame.attrs["source_doi"],
        "workbook_bytes": path.stat().st_size,
        "source_workbook_sha256": frame.attrs["source_workbook_sha256"],
        "publisher_checksum": "md5:719900ece651461def03a2cb54a33b33",
        "compilation_license_id": frame.attrs["compilation_license_id"],
        "source_rows": int(frame.source_observation_id.nunique()),
        "metric_cells": len(frame),
        "source_rows_by_sheet": (
            frame.groupby("source_sheet").source_observation_id.nunique().sort_index().to_dict()
        ),
        "metric_cells_by_status": frame.value_status.value_counts().sort_index().to_dict(),
        "normalized_numeric_metric_cells": int(frame.normalized_value.notna().sum()),
        "reference_catalog_entries": frame.attrs["reference_catalog_entries"],
        "used_reference_numbers": int(frame.reference_number.nunique()),
        "used_reference_numbers_with_doi": int(
            frame.loc[frame.underlying_reference_doi.notna(), "reference_number"].nunique()
        ),
        "metric_cells_with_reference_doi": int(frame.underlying_reference_doi.notna().sum()),
        "metric_cells_with_physical_specimen_id": int(frame.physical_specimen_id.notna().sum()),
        "physical_specimen_independence_reviewed_cells": int(
            frame.physical_specimen_independence_reviewed.sum()
        ),
        "test_validity_reviewed_cells": int(frame.test_validity_reviewed.sum()),
        "underlying_observation_rights_status_cells": (
            frame.underlying_observation_rights_status.value_counts().sort_index().to_dict()
        ),
        "special_value_counts": {
            f"{status}:{raw}": int(count)
            for (raw, status), count in special.value_counts(["raw_value", "value_status"]).items()
        },
        "workbook_formula_execution": frame.attrs["workbook_formula_execution"],
        "workbook_macro_execution": frame.attrs["workbook_macro_execution"],
        "qualification": (
            "The CC BY 4.0 workbook is a literature compilation, not a physical-specimen database. "
            "The public description says 81 publications while the workbook reference sheet contains "
            "85 numbered entries and 84 are used by metric rows; this discrepancy is preserved. Exact, "
            "bounded, qualitative and missing cells remain distinct. Potential references and endpoint "
            "families are not collapsed into a material score. Underlying-observation redistribution "
            "rights, specimen identity and test validity remain unresolved, and no model is fitted."
        ),
    }
    expected = {
        "source_rows": 1268,
        "metric_cells": 3579,
        "source_rows_by_sheet": {
            "Crevice Corrosion Potential": 31,
            "Crevice Corrosion Temp": 70,
            "HEAs_Ecorr, icorr, ipass, Rate": 51,
            "Pitting Potential": 810,
            "Pitting Temp": 117,
            "Repassivation Potential": 189,
        },
        "metric_cells_by_status": {
            "exact": 1605,
            "exact_text_numeric": 1,
            "lower_bound": 14,
            "missing": 1913,
            "qualitative": 44,
            "upper_bound": 2,
        },
        "normalized_numeric_metric_cells": 1622,
        "reference_catalog_entries": 85,
        "used_reference_numbers": 84,
        "used_reference_numbers_with_doi": 78,
        "metric_cells_with_reference_doi": 2950,
        "metric_cells_with_physical_specimen_id": 0,
        "physical_specimen_independence_reviewed_cells": 0,
        "test_validity_reviewed_cells": 0,
        "underlying_observation_rights_status_cells": {"unresolved": 3579},
        "workbook_formula_execution": False,
        "workbook_macro_execution": False,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise ValueError(f"pinned corrosion metric workbook changed: {key}")
    return result


if __name__ == "__main__":
    audit = inspect_corrosion_alloy_metrics()
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
