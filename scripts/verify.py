"""Run reproducible local checks and preserve bounded machine-readable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(
        description="Run the repository's complete local verification suite and preserve evidence."
    )
    parser.parse_args()
    validation = ROOT / "validation"
    validation.mkdir(exist_ok=True)
    artifacts = ROOT / "artifacts/verification"
    artifacts.mkdir(parents=True, exist_ok=True)
    commands = [
        ["scripts/build_source_catalog.py"],
        ["scripts/build_capability_catalog.py"],
        ["scripts/sync_catalogs.py"],
        ["scripts/build_model_reference.py"],
        ["scripts/export_schemas.py"],
        ["scripts/validate_atmospheric_corrosion.py"],
        ["scripts/validate_pulse_echo_thickness.py"],
        ["scripts/validate_pulse_echo_calibration.py"],
        ["scripts/validate_visual_surface.py"],
        ["scripts/validate_surface_examination.py"],
        ["scripts/validate_radiography.py"],
        ["scripts/validate_phased_array.py"],
        ["scripts/validate_tofd.py"],
        ["scripts/validate_eddy_current.py"],
        ["scripts/validate_magnetic_flux_leakage.py"],
        ["scripts/validate_inspection_scheduling.py"],
        ["scripts/validate_inspection_action_expected_loss.py"],
        ["scripts/validate_inspection_disposition_tree.py"],
        ["scripts/validate_multi_period_inspection_policy.py"],
        ["scripts/validate_multi_period_policy_comparison.py"],
        ["scripts/validate_finite_policy_path_generation.py"],
        ["scripts/validate_finite_policy_probability_calibration.py"],
        ["scripts/validate_thickness_first_passage.py"],
        ["scripts/validate_gaussian_thickness_sampling.py"],
        ["scripts/validate_thickness_state_space.py"],
        ["-m", "ruff", "check", "src", "tests", "scripts", "examples"],
        ["-m", "ruff", "format", "--check", "src", "tests", "scripts", "examples"],
        ["-m", "pytest", "-q", "--junitxml=validation/unit_tests.xml"],
    ]
    records = []
    for index, arguments in enumerate(commands):
        completed = subprocess.run(
            [sys.executable, *arguments],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = completed.stdout + completed.stderr
        (artifacts / f"check-{index}.txt").write_text(output, encoding="utf-8")
        records.append(
            dict(
                command=["python", *arguments],
                returncode=completed.returncode,
                output_sha256=hashlib.sha256(output.encode()).hexdigest(),
            )
        )
        if completed.returncode:
            encoding = sys.stdout.encoding or "utf-8"
            print(output.encode(encoding, errors="replace").decode(encoding))
            raise SystemExit(completed.returncode)
    xml = ET.parse(validation / "unit_tests.xml").getroot()
    suites = list(xml.iter("testsuite"))
    for suite in suites:
        suite.attrib.pop("hostname", None)
    ET.ElementTree(xml).write(validation / "unit_tests.xml", encoding="utf-8", xml_declaration=True)
    summary = dict(
        schema_version="matintegrity.verification.v1",
        run_at_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        platform=platform.system(),
        checks=records,
        tests=sum(int(s.get("tests", "0")) for s in suites),
        failures=sum(int(s.get("failures", "0")) for s in suites),
        errors=sum(int(s.get("errors", "0")) for s in suites),
        skipped=sum(int(s.get("skipped", "0")) for s in suites),
        qualification="Local software and mathematical verification; see data inventory for calibration and experimental comparison scope.",
    )
    (validation / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in ("tests", "failures", "errors", "skipped")}, indent=2))


if __name__ == "__main__":
    main()
