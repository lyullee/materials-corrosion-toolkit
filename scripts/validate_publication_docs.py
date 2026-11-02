"""Check visible API documentation against every executable model contract."""

import ast
import json
import re
from pathlib import Path

from matintegrity import __version__
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "https://github.com/lyullee/materials-corrosion-toolkit/blob/main/"


def main():
    registry = default_registry()
    directory = json.loads((ROOT / "docs/API_DIRECTORY.json").read_text(encoding="utf8"))
    records = {r["id"]: r for r in directory["models"]}
    assert set(records) == set(registry.list_models())
    assert directory["version"] == __version__
    readme = (ROOT / "README.md").read_text(encoding="utf8")
    assert len(readme.encode()) < 500_000
    paths = [
        ROOT / "README.md",
        ROOT / "docs/GETTING_STARTED_KO.md",
        ROOT / "docs/RESEARCH_CONTINUATION_KO.md",
        ROOT / "docs/RELEASE_STATUS_KO.md",
        ROOT / "docs/MODULE_DIRECTORY_KO.md",
    ]
    for identifier in registry.list_models():
        r = records[identifier]
        assert f"[`{identifier}`]" in readme
        path = ROOT / r["documentation"]
        text = path.read_text(encoding="utf8")
        assert r["purpose"] in text
        schema = registry.describe(identifier)["input_schema"]
        for field in schema.get("properties", {}):
            assert f"| `{field}` |" in text, (identifier, field)
        for field in registry.describe(identifier)["output_units"]:
            assert f"`{field.replace('|', chr(92) + '|')}`" in text, (identifier, field)
        assert (ROOT / r["schema"]).is_file()
        paths.append(path)
    links = 0
    for path in paths:
        text = path.read_text(encoding="utf8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(PREFIX):
                candidate = ROOT / target[len(PREFIX) :].split("#")[0]
            elif "://" in target or target.startswith(("#", "mailto:")):
                continue
            else:
                candidate = path.parent / target.split("#")[0]
            assert candidate.is_file(), (path.name, target)
            links += 1
        if path.name == "README.md":
            for code in re.findall(r"```python\n(.*?)```", text, re.DOTALL):
                ast.parse(code)
    result = registry.run_json(
        "corrosion.coupon_loss",
        json.dumps(dict(mass_loss_kg=0.001, exposed_area_m2=0.01, density_kg_m3=1000.0, duration_s=100.0)),
        RunContext(asset_id="authored", location_id="authored", time_basis="elapsed seconds"),
    )
    assert result.status == "computed"
    assert abs(result.values["mean_penetration_m"] - 0.0001) < 1e-15
    report = dict(
        status="passed",
        registered_apis=len(records),
        detailed_pages=len(records),
        checked_document_links=links,
        readme_example="passed",
        version=__version__,
        meaning="Documentation-contract consistency, not scientific or legal certification.",
    )
    (ROOT / "validation/publication_docs_audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
