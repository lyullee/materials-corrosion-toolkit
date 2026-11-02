"""Illustrate the knot-split integration contract using synthetic fixture data."""

import json
from pathlib import Path

from matintegrity.models.gasket_leakage_calibration import (
    GasketLeakageHistory,
    evaluate_gasket_leakage_history,
)


def main() -> None:
    fixture = Path(__file__).with_name("model_inputs.json")
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    request = GasketLeakageHistory.model_validate(
        payload["models"]["fabrication.gasket_calibrated_leakage_history"]
    )
    result = evaluate_gasket_leakage_history(request)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
