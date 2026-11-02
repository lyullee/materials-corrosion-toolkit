"""Local-only nominal uniaxial Sines fit; never a multiaxial qualification."""

import copy
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from matintegrity.contracts import canonical_digest
from matintegrity.multiaxial_sines_life_fit import MultiaxialSinesLifeFit
from matintegrity.multiaxial_stress_invariant_history import SampledStressInvariantHistory

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "data/raw/hannover-weld/fatigue_test_data.txt"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = "a7f7f11b96ad83e62d7e24d81222c97652243754e1f662f689e1866051722187"
    if digest != expected:
        raise ValueError("Source bytes differ from the reviewed Hannover dataset")
    rows = list(csv.DictReader(path.read_text(encoding="utf8").splitlines(), delimiter="\t"))
    counts = Counter(row["SpecimenName"] for row in rows)
    baseline = json.loads(
        (ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8")
    )["model_inputs"]["fatigue.multiaxial_sines_mean_limit_screen"]
    calibration = dict(
        basis="Analytic nominal uniaxial reduction: sqrt(3)*half-diameter sqrt(J2)=stress amplitude; hydrostatic coefficient zero; limit is an execution placeholder, not an allowable.",
        condition="S355MLO-AW-V1-R0.1",
    )
    cal_digest = canonical_digest(calibration)
    tests = []
    amplitudes = set()
    for line, row in enumerate(rows, 2):
        name = row["SpecimenName"]
        if not (
            name.endswith("-V1-S355-AW")
            and counts[name] == 1
            and row["RunOut"] == "0"
            and row["Outlier"] == "0"
            and float(row["StressRatio"]) == 0.1
        ):
            continue
        stress_range = float(row["NominalStressRange_MPa"]) * 1e6
        if stress_range in amplitudes:
            continue
        amplitudes.add(stress_range)
        screen = copy.deepcopy(baseline)
        history = screen["stress_history"]
        maximum = stress_range / 0.9
        minimum = maximum * 0.1
        history.update(
            analysis_id=name + "-nominal-reconstruction",
            material_condition_id=calibration["condition"],
            location_id=name,
            source_id="hannover-nominal-load-reconstruction",
            source_sha256=canonical_digest(
                {
                    "source_sha256": digest,
                    "line": line,
                    "assumption": "nominal uniaxial min/max/min; normalized cycle time, not measured time or local stress",
                }
            ),
            stress_tensor_components_Pa=[[v, 0.0, 0.0, 0.0, 0.0, 0.0] for v in (minimum, maximum, minimum)],
        )
        typed_history = SampledStressInvariantHistory.model_validate_json(json.dumps(history))
        screen.update(
            analysis_id=name,
            stress_history_sha256=canonical_digest(typed_history.model_dump(mode="json")),
            sample_time_s=[0.0, 0.5, 1.0],
            calibration_id="analytic-nominal-uniaxial",
            calibration_source_id="authored-analytic-reduction",
            calibration_sha256=cal_digest,
            calibration_material_condition_id=calibration["condition"],
            deviatoric_coefficient=math.sqrt(3),
            mean_hydrostatic_coefficient=0.0,
            calibration_evidence=dict(
                source_id="authored-analytic-reduction",
                origin="synthetic",
                sha256=cal_digest,
                citation=calibration["basis"],
            ),
        )
        tests.append(
            dict(
                test_id=name,
                physical_specimen_id=name,
                source_group_id="hannover-doi-10.25835/0dojws6u",
                source_record_id=f"fatigue_test_data.txt:line:{line}",
                cycles_to_failure=float(row["LoadCyclesToFailure"]),
                screen=screen,
                observation_evidence=dict(
                    source_id="hannover-fatigue-failures",
                    origin="open_dataset",
                    sha256=digest,
                    citation="Christian Daenekas, DOI 10.25835/0dojws6u, CC BY 4.0; provider failure cycles. Applied nominal stress reconstructed separately; no measured local tensor history.",
                ),
            )
        )
        if len(tests) == 4:
            break
    request = MultiaxialSinesLifeFit.model_validate_json(
        json.dumps(
            dict(
                campaign_id="hannover-nominal-execution-only",
                material_condition_id=calibration["condition"],
                tests=tests,
                independent_specimen_identity_reviewed=True,
                failure_endpoint_and_observation_rights_reviewed=True,
                loglog_power_law_form_and_fit_domain_reviewed=True,
            )
        )
    )
    output = ROOT / "artifacts/validation/full_core_calculations/execution_inputs.local.json"
    content = json.loads(output.read_text(encoding="utf8"))
    content["model_inputs"]["fatigue.multiaxial_sines_life_fit"] = request.model_dump(mode="json")
    output.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(f"Prepared {len(tests)} independent failure observations; nominal uniaxial fit only")


if __name__ == "__main__":
    main()
