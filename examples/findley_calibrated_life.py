"""Wire a synthetic Findley stress history to a synthetic caller life curve."""

import json
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.models.fatigue_findley_life import (
    CriticalPlaneFindleyCalibratedLife,
    FindleyParameterLifePoint,
    critical_plane_findley_calibrated_life,
)


def build_synthetic_request() -> CriticalPlaneFindleyCalibratedLife:
    """Reuse the project-authored synthetic Findley fixture and add a toy life curve."""
    root = Path(__file__).resolve().parents[1]
    examples = json.loads((root / "examples" / "model_inputs.json").read_text(encoding="utf-8"))
    stress_history = examples["models"]["fatigue.critical_plane_findley_parameter"]
    points = (
        FindleyParameterLifePoint(point_id="synthetic-low", parameter_Pa=1e6, life_cycles=1e6),
        FindleyParameterLifePoint(point_id="synthetic-high", parameter_Pa=1e8, life_cycles=1e3),
    )
    point_digest = canonical_digest([point.model_dump(mode="json") for point in points])
    license_id = "CC0-1.0"
    return CriticalPlaneFindleyCalibratedLife.model_validate_json(json.dumps({
        "stress_history": stress_history,
        "life_curve_provider_id": "synthetic-findley-life-curve-provider",
        "life_curve_provider_revision": "example-v1",
        "life_curve_record_id": "synthetic-findley-life-curve",
        "life_curve_sha256": point_digest,
        "life_curve_points": [point.model_dump(mode="json") for point in points],
        "life_curve_evidence": [{
            "source_id": "synthetic-findley-life-curve-provider",
            "origin": "synthetic",
            "citation": "Toy project-authored curve for API wiring only; not material data.",
            "license_id": license_id,
            "sha256": point_digest,
        }],
        "usage_rights_evidence": [{
            "source_id": "synthetic-findley-example-rights",
            "origin": "synthetic",
            "citation": "Project-authored synthetic fixture and toy curve; no external data included.",
            "license_id": license_id,
        }],
        "same_material_condition_and_load_basis_reviewed": True,
        "monotone_curve_and_interpolation_reviewed": True,
        "curve_support_and_no_extrapolation_reviewed": True,
        "usage_rights_reviewed": True,
        "computational_use_authorized": True,
    }))


def main() -> None:
    result = critical_plane_findley_calibrated_life(build_synthetic_request())
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
