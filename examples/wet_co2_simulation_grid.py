"""Inspect a licensed NORSOK-derived simulation grid without bundling its workbook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.wet_co2_data import (
    WetCo2SimulationGridSummary,
    read_wet_co2_simulation_grid,
    summarize_wet_co2_simulation_grid,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path, help="path to the separately acquired CC BY workbook")
    args = parser.parse_args()
    rows = read_wet_co2_simulation_grid(args.workbook)
    result = summarize_wet_co2_simulation_grid(WetCo2SimulationGridSummary(rows=tuple(rows)))
    print(json.dumps(result.values, indent=2))


if __name__ == "__main__":
    main()
