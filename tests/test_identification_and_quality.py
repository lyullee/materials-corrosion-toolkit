import copy
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad

from matintegrity import evaluate
from matintegrity.composition import ParameterProfile, SatisfactionGate, WorkflowStep, run_workflow
from matintegrity.contracts import Evidence, RunContext
from matintegrity.identification import DesignationAlias, DesignationResolver, MaterialDesignation
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="synthetic observed state")


def chemistry(inputs):
    return default_registry().run_json("materials.chemistry_reconciliation", json.dumps(inputs), CONTEXT)


def test_exact_alias_does_not_infer_transitivity_substitution_or_an_edition():
    original = MaterialDesignation(
        namespace="user",
        specification="A",
        edition="1",
        grade="g",
        product_form="plate",
        condition="as declared",
    )
    canonical = original.model_copy(update={"specification": "B"})
    entry = DesignationAlias(
        alias=original,
        canonical=canonical,
        evidence=Evidence(
            source_id="synthetic", origin="synthetic", citation="Authored naming relation", license_id="MIT"
        ),
        permitted_use_note="Software test only",
    )
    resolver = DesignationResolver([entry])
    result = resolver.resolve(original)
    assert result["canonical"]["specification"] == "B" and len(result["mapping_digest"]) == 64
    assert resolver.resolve(canonical)["status"] == "needs_data"
    assert resolver.resolve(original.model_copy(update={"edition": "2"}))["status"] == "needs_data"
    with pytest.raises(ValueError, match="ambiguous"):
        DesignationResolver([entry, entry])


def test_unmeasured_carbon_is_unknown_instead_of_zero():
    inputs = copy.deepcopy(EXAMPLES["materials.chemistry_reconciliation"])
    del inputs["verification"]["element_intervals"]["C"]
    result = chemistry(inputs)
    assert result.status == "computed" and result.values["outcome"] == "unknown"
    assert (
        next(r for r in result.values["checks"] if r["check_id"] == "C.verification")["outcome"] == "unknown"
    )


@pytest.mark.parametrize(
    "bounds,expected",
    [({"lower": 0.168, "upper": 0.182}, "unknown"), ({"lower": 0.2, "upper": 0.21}, "not_satisfied")],
)
def test_chemistry_boundary_crossing_and_disjoint_intervals_are_distinct(bounds, expected):
    inputs = copy.deepcopy(EXAMPLES["materials.chemistry_reconciliation"])
    inputs["verification"]["element_intervals"]["Cr"] = bounds
    assert chemistry(inputs).values["outcome"] == expected


def test_traceability_and_overlap_policy_are_explicit_and_hashed():
    inputs = copy.deepcopy(EXAMPLES["materials.chemistry_reconciliation"])
    inputs["verification"]["heat_id"] = None
    assert chemistry(inputs).values["outcome"] == "unknown"
    inputs["verification"]["heat_id"] = "another heat"
    assert chemistry(inputs).values["outcome"] == "not_satisfied"
    inputs = copy.deepcopy(EXAMPLES["materials.chemistry_reconciliation"])
    inputs["verification"]["element_intervals"]["Cr"] = {"lower": 0.185, "upper": 0.185}
    overlap = chemistry(inputs)
    inputs["require_certificate_verification_interval_overlap"] = False
    independent = chemistry(inputs)
    assert overlap.values["outcome"] == "not_satisfied" and independent.values["outcome"] == "satisfied"
    assert overlap.input_digest != independent.input_digest


def test_json_cli_workflow_and_profiles_accept_nested_evidence_arrays(tmp_path):
    inputs = EXAMPLES["materials.chemistry_reconciliation"]
    request = tmp_path / "request.json"
    output = tmp_path / "answer.json"
    request.write_text(
        json.dumps(
            dict(
                model_id="materials.chemistry_reconciliation",
                inputs=inputs,
                context=CONTEXT.model_dump(mode="json"),
            )
        ),
        encoding="utf-8",
    )
    run = subprocess.run(
        [sys.executable, "-m", "matintegrity.cli", "run", str(request), "--out", str(output)],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    answer = json.loads(output.read_text(encoding="utf-8"))
    workflow = run_workflow(
        default_registry(),
        [WorkflowStep(id="chemistry", model_id="materials.chemistry_reconciliation", inputs=inputs)],
        CONTEXT,
    )
    assert workflow["steps"]["chemistry"]["input_digest"] == answer["input_digest"]
    profile = ParameterProfile(
        profile_id="demo",
        model_id="materials.chemistry_reconciliation",
        parameters={k: v for k, v in inputs.items() if k != "verification"},
        source_id="synthetic",
        domain="synthetic evidence only",
    )
    assert (
        profile.run(default_registry(), {"verification": inputs["verification"]}, CONTEXT).values["outcome"]
        == "satisfied"
    )


def test_thickness_measurement_does_not_repeat_manufacturing_or_forming_loss():
    result = evaluate("fabrication.thickness_budget", EXAMPLES["fabrication.thickness_budget"], CONTEXT)
    assert result.values["nominal_budget_structural_thickness_m"] == pytest.approx(
        (0.01 - 0.0005) * 0.9 - 0.001
    )
    assert result.values["measured_structural_thickness_m"] == pytest.approx(0.0088 - 0.001)


@pytest.mark.parametrize("method", ["theil_sen", "soft_l1"])
def test_joint_profile_excludes_weld_height_and_robustly_recovers_planes(method):
    positions = np.r_[np.linspace(-0.08, -0.02, 7), 0.0, np.linspace(0.02, 0.08, 7)]
    heights = np.where(positions < 0, 0.1 * positions, 0.002 + 0.2 * positions)
    heights[0] += 0.1
    heights[7] = 100.0
    heights[-1] += 0.1
    result = evaluate(
        "welding.joint_profile",
        dict(
            transverse_position_m=positions.tolist(),
            measured_surface_height_m=heights.tolist(),
            excluded_joint_half_width_m=0.01,
            fit_method=method,
            robust_residual_scale_m=1e-7,
        ),
        CONTEXT,
    )
    assert result.values["signed_surface_offset_at_joint_m"] == pytest.approx(0.002, abs=1e-6)
    assert result.values["signed_angular_mismatch_rad"] == pytest.approx(
        math.atan(0.2) - math.atan(0.1), abs=1e-4
    )


def test_hardness_straddling_and_unmeasured_regions_stay_unknown():
    inputs = copy.deepcopy(EXAMPLES["welding.hardness_traverse"])
    inputs["points"][1].update(hardness_Pa=2.25e9, expanded_uncertainty_Pa=0.1e9)
    assert evaluate("welding.hardness_traverse", inputs, CONTEXT).values["outcome"] == "unknown"
    inputs["points"][1].update(hardness_Pa=2.5e9, expanded_uncertainty_Pa=0.05e9)
    assert evaluate("welding.hardness_traverse", inputs, CONTEXT).values["outcome"] == "not_satisfied"
    inputs = copy.deepcopy(EXAMPLES["welding.hardness_traverse"])
    inputs["declared_region_upper_limits_Pa"]["unmeasured HAZ"] = 2.5e9
    assert evaluate("welding.hardness_traverse", inputs, CONTEXT).values["outcome"] == "unknown"


def test_dilution_conserves_known_elements_without_inventing_missing_silicon():
    result = evaluate("welding.dilution", EXAMPLES["welding.dilution"], CONTEXT).values
    assert result["role_mass_fractions"]["base"] == 0.25
    chemistry = result["mixed_composition_mass_fraction"]
    assert chemistry["Cr"] == pytest.approx(0.3) and chemistry["Fe"] == pytest.approx(0.2525)
    assert sum(chemistry[e] for e in ("Cr", "Fe", "Ni")) == pytest.approx(1.0)
    assert chemistry["Si"] is None


def test_cathodic_budget_integrates_joint_variation_and_interior_peak():
    inputs = EXAMPLES["protection.cathodic_budget"]
    result = evaluate("protection.cathodic_budget", inputs, CONTEXT).values
    integral = quad(lambda time: 10 * (time / 10) * (1 - time / 10), 0, 10)[0]
    assert result["required_charge_C"] == pytest.approx(integral)
    assert result["peak_current_A"] == pytest.approx(2.5) and result["peak_time_s"] == pytest.approx(5.0)
    assert result["minimum_anodes_by_charge"] == 2 and result["minimum_anodes_by_peak_current"] == 3
    assert result["installed_charge_margin_C"] > 0 and result["installed_peak_current_margin_A"] < 0


def test_cathodic_budget_is_invariant_under_equivalent_linear_subdivision():
    original = EXAMPLES["protection.cathodic_budget"]
    segmented = copy.deepcopy(original)
    segmented.update(
        time_s=[0.0, 5.0, 10.0],
        bare_surface_fraction=[0.0, 0.5, 1.0],
        bare_surface_current_density_A_m2=[1.0, 0.5, 0.0],
        additional_current_drain_A=[0.0, 0.0, 0.0],
    )
    a = evaluate("protection.cathodic_budget", original, CONTEXT).values
    b = evaluate("protection.cathodic_budget", segmented, CONTEXT).values
    assert b["required_charge_C"] == pytest.approx(a["required_charge_C"])
    assert b["peak_current_A"] == pytest.approx(a["peak_current_A"])


@pytest.mark.parametrize(
    "case,expected", [("satisfied", "computed"), ("missing", "needs_data"), ("mismatch", "out_of_scope")]
)
def test_explicit_workflow_gate_does_not_treat_computed_as_acceptance(case, expected):
    inputs = copy.deepcopy(EXAMPLES["materials.chemistry_reconciliation"])
    if case == "missing":
        inputs["verification"]["element_intervals"]["C"] = None
    if case == "mismatch":
        inputs["verification"]["heat_id"] = "other heat"
    steps = [
        WorkflowStep(
            id="verify",
            model_id="materials.chemistry_reconciliation",
            inputs=inputs,
            satisfaction_gate=SatisfactionGate(),
        ),
        WorkflowStep(
            id="dimensions",
            model_id="fabrication.thickness_budget",
            inputs=EXAMPLES["fabrication.thickness_budget"],
        ),
    ]
    result = run_workflow(default_registry(), steps, CONTEXT)
    assert result["status"] == expected
    assert ("dimensions" in result["steps"]) == (case == "satisfied")
    if case != "satisfied":
        assert result["steps"]["verify"]["status"] == "computed"
