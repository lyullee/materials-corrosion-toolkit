"""Authored mathematical checks for provider-driven failure-assessment points."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import Evidence
from matintegrity.models.fad import (
    FailureAssessment,
    FailureAssessmentCurve,
    FailureAssessmentPoint,
    assess_failure_diagram,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/matintegrity/models/fad.py"
OUTPUT = ROOT / "validation/failure_assessment_math.json"


def main():
    evidence = Evidence(
        source_id="authored-fad-verification",
        origin="synthetic",
        citation="Project-authored piecewise-linear benchmark",
        license_id="MIT",
    )
    lr_knots = (0.0, 0.3, 0.8, 1.2)
    kr_knots = (1.0, 0.94, 0.55, 0.0)
    curve = FailureAssessmentCurve(
        curve_id="authored-piecewise-boundary",
        assessment_basis_id="software-math-check",
        load_ratio=lr_knots,
        allowable_toughness_ratio=kr_knots,
        validity_description="Synthetic benchmark only",
        evidence=(evidence,),
    )
    queries = np.linspace(0, 1.2, 49)
    points = tuple(
        FailureAssessmentPoint(
            point_id=f"q-{index}",
            load_case_id="proportional-synthetic",
            location_id=f"location-{index}",
            material_condition_id="synthetic-condition",
            geometry_solution_id="authored-k",
            reference_stress_solution_id="authored-reference-stress",
            toughness_source_id="authored-resistance",
            effective_stress_intensity_Pa_sqrt_m=40e6,
            fracture_resistance_Pa_sqrt_m=80e6,
            reference_stress_Pa=float(lr * 400e6),
            normalizing_strength_Pa=400e6,
        )
        for index, lr in enumerate(queries)
    )
    request = FailureAssessment(
        material_condition_id="synthetic-condition",
        curve=curve,
        points=points,
        linear_elastic_k_solution_reviewed=True,
        reference_stress_solution_reviewed=True,
        toughness_applicability_reviewed=True,
        load_combination_reviewed=True,
        curve_applicability_reviewed=True,
    )
    result = assess_failure_diagram(request)
    calculated = np.asarray([row["allowable_toughness_ratio"] for row in result.values["points"]])
    independent = np.empty_like(queries)
    for index, value in enumerate(queries):
        segment = min(np.searchsorted(lr_knots, value, side="right") - 1, len(lr_knots) - 2)
        segment = max(segment, 0)
        fraction = (value - lr_knots[segment]) / (lr_knots[segment + 1] - lr_knots[segment])
        independent[index] = kr_knots[segment] + fraction * (kr_knots[segment + 1] - kr_knots[segment])
    maximum_error = float(np.max(np.abs(calculated - independent)))
    beyond = request.model_copy(
        update={
            "points": (
                points[0].model_copy(update={"point_id": "beyond", "reference_stress_Pa": 1.21 * 400e6}),
            )
        }
    )
    beyond_result = assess_failure_diagram(beyond)
    report = {
        "schema_version": "matintegrity.failure_assessment_verification.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": "structural.failure_assessment_points",
        "model_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "status": "passed"
        if result.status == "computed"
        and maximum_error <= 1e-15
        and beyond_result.status == "out_of_scope"
        and beyond_result.values["points"][0]["allowable_toughness_ratio"] is None
        else "failed",
        "piecewise_linear_queries": len(queries),
        "maximum_independent_interpolation_error": maximum_error,
        "boundary_knots_reproduced": bool(np.allclose(calculated[[0, 12, 32, 48]], kr_knots)),
        "outside_support_status": beyond_result.status,
        "outside_support_allowable_value": beyond_result.values["points"][0]["allowable_toughness_ratio"],
        "qualification": (
            "Authored normalization and interpolation verification only. It does not qualify a standard curve, K/reference-stress solution, fracture resistance, material or cracked component."
        ),
    }
    if report["status"] != "passed":
        raise AssertionError(report)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
