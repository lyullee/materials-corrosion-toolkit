"""Synchronize public metadata into the installed Python package."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "src/matintegrity/catalog_data"
    target.mkdir(exist_ok=True)
    for name in ("capabilities", "datasets", "sources"):
        shutil.copyfile(ROOT / "data/catalogs" / f"{name}.json", target / f"{name}.json")
    shutil.copyfile(
        ROOT / "validation/ct110_weld_corrosion_rates.json",
        target / "ct110_weld_corrosion_rates.json",
    )


if __name__ == "__main__":
    main()
