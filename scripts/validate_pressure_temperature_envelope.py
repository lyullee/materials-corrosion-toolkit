"""Verify the caller-supplied pressure-temperature envelope contract with authored values."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.models import mechanics
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def _close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-6):
        raise AssertionError(f"{label}: expected {expected}, received {actual}")


def main() -> None:
    result = default_registry().run(
        "structural.pressure_temperature_envelope",
        {
            "envelope_id": "authored-affine-validation",
            "applicability_basis": "independent arithmetic check, not a design limit",
            "source_sha256": "a" * 64,
            "knots": [
                {"temperature_K": 200.0, "allowable_pressure_Pa": 14.0e6},
                {"temperature_K": 300.0, "allowable_pressure_Pa": 10.0e6},
                {"temperature_K": 500.0, "allowable_pressure_Pa": 6.0e6},
            ],
            "operating_points": [
                {"point_id": "first-affine-segment", "temperature_K": 250.0, "pressure_Pa": 11.0e6},
                {"point_id": "second-affine-segment", "temperature_K": 400.0, "pressure_Pa": 9.0e6},
            ],
            "applicability_reviewed": True,
            "operating_points_reviewed": True,
        },
        RunContext(
            asset_id="authored-envelope-validation",
            location_id="synthetic-pressure-boundary",
            time_basis="two authored operating points",
        ),
    )
    if result.status != "computed":
        raise AssertionError(f"unexpected status: {result.status}")
    expected_allowable = [12.0e6, 8.0e6]
    expected_margin = [1.0e6, -1.0e6]
    for index, (actual, expected) in enumerate(
        zip(result.values["allowable_pressures_Pa"], expected_allowable, strict=True)
    ):
        _close(actual, expected, f"allowable pressure {index}")
    for index, (actual, expected) in enumerate(
        zip(result.values["pressure_margins_Pa"], expected_margin, strict=True)
    ):
        _close(actual, expected, f"pressure margin {index}")

    record = {
        "schema_version": "matintegrity.pressure_temperature_envelope_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_source_sha256": hashlib.sha256(Path(mechanics.__file__).read_bytes()).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_digest": result.input_digest,
        "expected_allowable_pressures_Pa": expected_allowable,
        "actual_allowable_pressures_Pa": result.values["allowable_pressures_Pa"],
        "expected_pressure_margins_Pa": expected_margin,
        "actual_pressure_margins_Pa": result.values["pressure_margins_Pa"],
        "qualification": (
            "Independently authored affine interpolation and margin arithmetic only. This is not a design-code "
            "table, material qualification, transient validation, uncertainty bound or acceptance decision."
        ),
    }
    target = ROOT / "validation/pressure_temperature_envelope_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
