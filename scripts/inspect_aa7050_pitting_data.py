"""Audit checksum-pinned AA7050 local-pitting MAT files without interpreting fields."""

import argparse
import json
from pathlib import Path

from matintegrity.pitting_data import read_local_pitting_numeric_mat

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "aa7050-local-pitting-evolution"
SPECIMEN_ID = "provider-aa7050-specimen-01"
SOURCE_GROUP_ID = "mendeley-hhf5sfk5bj-v1-one-specimen"
FILES = (
    (
        "TSS01_CorrosionCropped_02Days.mat",
        "11ce736d163af08a691ab1b8b9d7c6f1b9452d4a34082d42bbd6406cedacd945",
        46392832,
        "surface_morphology",
        2.0,
    ),
    (
        "TSS01_CorrosionCropped_06Days.mat",
        "eca2ed2658f62d6a6cd0d8e9672ae505e87b0c24de3252f8453c95676cebc66f",
        43087980,
        "surface_morphology",
        6.0,
    ),
    (
        "TSS01_strainCropped.mat",
        "b12487fb5a51a5a9e78453e2bdee91030f8345d2ceda54b9d8ce465c708f126c",
        35873099,
        "strain_field",
        None,
    ),
    (
        "TSS01_stressCropped.mat",
        "4c7f8c0280fe66ee588ba16196072ce61bb1fea8a25d91eaccc918abf246b31f",
        2412094,
        "stress_field",
        None,
    ),
)


def inspect(raw_root: Path) -> dict:
    files = []
    missing = []
    incomplete = []
    for filename, sha256, expected_bytes, role, exposure_days in FILES:
        path = raw_root / filename
        if not path.is_file():
            missing.append(filename)
            continue
        if path.stat().st_size != expected_bytes:
            incomplete.append(
                {
                    "filename": filename,
                    "observed_bytes": path.stat().st_size,
                    "expected_bytes": expected_bytes,
                }
            )
            continue
        result = read_local_pitting_numeric_mat(
            path,
            expected_sha256=sha256,
            dataset_id=DATASET_ID,
            physical_specimen_id=SPECIMEN_ID,
            source_group_id=SOURCE_GROUP_ID,
            source_role=role,
            exposure_duration_days=exposure_days,
        )
        metadata = result["metadata"]
        files.append(
            {
                "filename": metadata.source_filename,
                "sha256": metadata.source_sha256,
                "bytes": metadata.source_bytes,
                "source_role": metadata.source_role,
                "exposure_duration_days": metadata.exposure_duration_days,
                "variables": [
                    {
                        "name": item.variable_name,
                        "matlab_class": item.matlab_class,
                        "numpy_dtype": item.numpy_dtype,
                        "shape": list(item.shape),
                        "element_count": item.element_count,
                        "finite_count": item.finite_count,
                        "nonfinite_count": item.nonfinite_count,
                        "finite_minimum": item.finite_minimum,
                        "finite_maximum": item.finite_maximum,
                        "declared_unit": item.declared_unit,
                    }
                    for item in metadata.variables
                ],
                "coordinate_status": metadata.coordinate_status,
                "interpretation_status": metadata.interpretation_status,
            }
        )

    shape_sets_by_role = {}
    for role in ("surface_morphology", "strain_field", "stress_field"):
        shapes = {
            tuple(variable["shape"])
            for file_record in files
            if file_record["source_role"] == role
            for variable in file_record["variables"]
        }
        shape_sets_by_role[role] = [list(shape) for shape in sorted(shapes)]
    morphology_shapes = shape_sets_by_role["surface_morphology"]

    return {
        "schema_version": "matintegrity.validation.aa7050_local_pitting_dataset_audit.v1",
        "dataset_id": DATASET_ID,
        "physical_specimen_id": SPECIMEN_ID,
        "source_group_id": SOURCE_GROUP_ID,
        "audit_status": (
            "complete_file_structure" if not missing and not incomplete else "partial_file_structure"
        ),
        "expected_file_count": len(FILES),
        "audited_file_count": len(files),
        "missing_files": missing,
        "incomplete_files": incomplete,
        "files": files,
        "shape_sets_by_role": shape_sets_by_role,
        "morphology_arrays_have_equal_shape": len(morphology_shapes) == 1,
        "direct_index_alignment_status": (
            "blocked_coordinates_unreviewed"
            if len(morphology_shapes) == 1
            else "blocked_shape_mismatch_and_coordinates_unreviewed"
        ),
        "qualification": (
            "Checksum and top-level numeric-array structure only. Array names and equal shapes do not establish "
            "coordinate registration, units, height sign, pit geometry, temporal transition truth, independent "
            "specimens, action effects, field corrosion rates, POD, remaining life, or acceptance."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=ROOT / "data/raw/aa7050-local-pitting-evolution",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/aa7050_local_pitting_dataset.json",
    )
    args = parser.parse_args()
    result = inspect(args.raw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "audit_status": result["audit_status"],
                "audited_file_count": result["audited_file_count"],
                "missing_file_count": len(result["missing_files"]),
                "incomplete_file_count": len(result["incomplete_files"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
