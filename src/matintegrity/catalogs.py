"""Packaged capability, source and acquisition metadata."""

import json
from importlib.resources import files


def load_catalog(name: str) -> dict:
    if name not in {"capabilities", "datasets", "sources"}:
        raise ValueError("unknown catalog")
    return json.loads((files("matintegrity") / "catalog_data" / f"{name}.json").read_text(encoding="utf-8"))
