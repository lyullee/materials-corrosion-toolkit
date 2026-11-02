"""Render the English public README from the API directory and fixed physics groups."""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/lyullee/materials-corrosion-toolkit"
GROUP_NAMES = """Mass-loss corrosion rate
Faraday metal loss
Polarization-resistance corrosion current
Galvanic current and resistive coupling
Mixed potential and Butler-Volmer reactions
Nernst equilibrium potential
Empirical corrosion and thickness loss
Atmospheric corrosion loss
Combined erosion-corrosion loss
Stress-corrosion crack growth
Mass-action and carbonate aqueous equilibrium
Nonideal solution activities
Single and competing solid-phase equilibrium
Aqueous reaction-network kinetics
Nucleation, precipitation and dissolution
Surface coverage and scale kinetics
Scale diffusion, reaction and moving boundaries
Gas-liquid mass transfer and two-film transport
Coupled wet-CO2 reaction, transport and scale
Fickian diffusion
Diffusion with wall reactions
Ionic Nernst-Planck transport
Coupled crevice chemistry, electrodes and solids
Slit flow, pressure and volume continuity
Hydrogen diffusion, trapping, release and surface reactions
Thin- and thick-cylinder pressure stresses
Stress tensors, principal stresses and invariants
Constrained thermal expansion and through-wall thermal stress
Bolts, elastic joints and frictional torque
Nonlinear flange and gasket contact
Gasket viscoelasticity and stress relaxation
Gasket leakage history
Remaining-thickness and profile pressure capacity
Crack stress-intensity factors
Failure assessment diagrams (FAD)
Paris-law and tabulated crack growth
Norton steady-state creep
Larson-Miller and related rupture relations
Creep time fractions and creep-fatigue
Stress-life fatigue and mean-stress corrections
Strain-life fatigue, Morrow and SWT
Miner cumulative damage
Critical-plane multiaxial fatigue
Stress-invariant multiaxial fatigue
Nonproportional multiaxial strain-path fatigue
J2 cyclic plasticity and kinematic hardening
Neuber notch stress-strain
Hysteresis-energy and tensor-work fatigue
Multilayer steady conduction, convection and radiation
Transient conduction and lumped thermal capacitance
Rosenthal moving welding heat source
CoolProp equations of state and fugacity
Condensation-film heat and mass balances
Gas pressure decay, leakage and expansion energy
Archard wear
Parabolic and nonisothermal oxidation
Arrhenius kinetics and thermal aging
Ramberg-Osgood and Hollomon constitutive relations
Well-mixed gas purging
Cathodic-protection current, charge and lifetime balances
Cavitation margin and pressure-drop indicators
Acoustic arrival-time location and depth inversion
FMC/TFM ultrasonic image reconstruction""".splitlines()
DOMAIN_NAMES = {
    "adapter": "Result exchange with other systems",
    "calibration": "Material, transport and observation parameter fitting",
    "chemistry": "Aqueous activities, equilibrium and solid reactions",
    "corrosion": "Corrosion rates, currents, metal loss and crevices",
    "creep": "Creep rate, rupture and cumulative damage",
    "data": "External-data inspection and authorized readers",
    "degradation": "Erosion, oxidation, wear and environmental effects",
    "design": "Design inputs and caller-defined criteria",
    "electrochemistry": "Potential, polarization and electrode reactions",
    "fabrication": "Machining, bolts, gaskets and fabrication evidence",
    "fatigue": "Fatigue, multiaxial paths, plasticity and life",
    "flow": "Flow and pressure-loss calculations",
    "fracture": "Cracks, stress intensity and fracture mechanics",
    "geometry": "Geometry, loss profiles and spatial data",
    "inspection": "Inspection, imaging, observations and procedures",
    "integration": "Evidence-bound calculation coupling",
    "kinetics": "Reaction kinetics and temperature dependence",
    "maintenance": "Maintenance histories and caller-defined indicators",
    "materials": "Constitutive relations, composition and test interpretation",
    "mechanics": "Pressure, thermal stress, contact and elasticity",
    "piping": "Piping conditions and caller-defined requirements",
    "protection": "Cathodic protection and protection balances",
    "reliability": "Explicit reliability and risk calculations",
    "structural": "Thickness, pressure capacity and FAD assessment",
    "testing": "Material tests and statistical summaries",
    "thermal": "Heat conduction, histories and heat treatment",
    "thermo": "Thermodynamic states and fugacity",
    "transport": "Diffusion, ions and component transport",
    "validation": "Evidence alignment and comparison metrics",
    "welding": "Welding heat, hydrogen, metallurgy and procedures",
    "workflow": "Caller-defined criteria and assessment workflows",
}


def esc(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def names(values, limit):
    values = list(values)
    result = ", ".join(f"`{esc(v)}`" for v in values[:limit]) or "See detailed reference"
    if len(values) > limit:
        result += f" **(+{len(values) - limit} more)**"
    return result


def build_readme(records, groups, representative, version):
    by_id = {r["id"]: r for r in records}
    domains = defaultdict(list)
    for r in records:
        domains[r["domain"]].append(r)
    assert len(GROUP_NAMES) == len(groups) == 63
    intro = f"""# Materials Corrosion Toolkit

**Modular Python calculations for materials, corrosion and structural integrity.** Select individual APIs, supply your own parameters and evidence, and connect results to other engineering systems. The toolkit covers electrochemistry, transport, mechanics, fatigue, fabrication, welding and inspection.

**Distribution:** `materials-corrosion-toolkit` · **Python import / CLI:** `matintegrity` · **Release:** `{version}` · **Code license:** MIT · **Python:** 3.11+

> Research alpha. Calculation execution, mathematical verification, calibration, independent experimental validation and field applicability are separate states. Results do not constitute code compliance or safety certification.

## Find a module

- [63 core physics groups](#core-physics-groups): physical purpose, representative API and main input/output parameter names.
- [All 757 APIs by domain](#complete-api-directory): purpose and main parameters for every registered API. Click an API name for its complete reference.
- [Detailed module directory (Korean)]({REPO}/blob/main/docs/MODULE_DIRECTORY_KO.md): all top-level inputs, required fields, defaults, constraints, output units, schemas, implementation and available examples. API identifiers and parameter names are unchanged.
- [Getting started (Korean)]({REPO}/blob/main/docs/GETTING_STARTED_KO.md) · [Python API and common contracts (Korean)]({REPO}/blob/main/docs/API_KO.md).
- [Development history (Korean)]({REPO}/blob/main/docs/DEVELOPMENT_HISTORY_KO.md) · [Research continuation and verification (Korean)]({REPO}/blob/main/docs/RESEARCH_CONTINUATION_KO.md).
- [Release status and known limits (Korean)]({REPO}/blob/main/docs/RELEASE_STATUS_KO.md) · [Publication records and exact file hashes (Korean)]({REPO}/blob/main/docs/PUBLICATION_RECORD_KO.md).
- [PyPI](https://pypi.org/project/materials-corrosion-toolkit/{version}/) · [GitHub release]({REPO}/releases/tag/v{version}) · [Zenodo DOI](https://doi.org/10.5281/zenodo.23899598).

## Installation

```bash
python -m pip install materials-corrosion-toolkit=={version}
# Scientific solvers, supported file readers and CoolProp:
python -m pip install "materials-corrosion-toolkit[science,thermo]=={version}"
# Development from source:
git clone {REPO}.git
cd materials-corrosion-toolkit
python -m pip install -e ".[science,thermo,dev]"
```

The base installation requires NumPy, Pydantic and Pint. Optional solvers/readers use SciPy, pandas, rainflow and file-format libraries; thermodynamic APIs use CoolProp. The `ebsd` extra enables DefDAP integration. Supply applicable material properties, kinetic coefficients and assessment criteria explicitly.

## A working calculation

This independently authored example converts mass loss into average penetration and corrosion rate using the supplied exposed area, density and duration. Values are illustrative.

```python
from matintegrity import evaluate
from matintegrity.contracts import RunContext

result = evaluate(
    "corrosion.coupon_loss",
    {{"mass_loss_kg": 0.001, "exposed_area_m2": 0.01,
     "density_kg_m3": 1000.0, "duration_s": 100.0}},
    RunContext(asset_id="example-asset", location_id="example-coupon", time_basis="elapsed seconds"),
)
assert result.status == "computed"
print(result.values["mean_penetration_m"])  # 0.0001 m
print(result.values["rate_m_s"])            # 0.000001 m/s
print(result.units)
print(result.model_dump_json())             # Inputs, outputs, context and provenance
```

## Inspect complete inputs and outputs

```python
from matintegrity.registry import default_registry

registry = default_registry()
print(registry.list_models())
definition = registry.describe("corrosion.coupon_loss")
print(definition["input_schema"])  # Required fields, types, constraints and nested $defs
print(definition["output_units"])
print(definition["assumptions"])
```

`evaluate()` and `run()` accept Python inputs; `run_json()` accepts JSON. Strict Python contracts distinguish tuples from lists where declared. Use `run_json()` for JSON files or web payloads. Numeric strings are not silently converted, and units are not guessed.

| Common result field | Meaning |
|---|---|
| `status` | `computed`: calculation completed within declared scope; `needs_data`: missing evidence or inputs; `out_of_scope`: applicability or numerical support exceeded |
| `inputs`, `values`, `units` | Actual inputs, calculated outputs and declared units |
| `model_id`, `model_version` | API identifier and calculation-model version |
| `context` | Asset, location, time basis and caller context |
| `assumptions`, `notes`, `qualification` | Assumptions, diagnostics and interpretation limits |
| `input_digest`, `source_ids`, `runtime` | Input hash, source identifiers and runtime information |
| `probability_semantics` | Explicit probability meaning, where applicable |

A `computed` status does not establish structural acceptance. Preserve missing-data and out-of-scope states when chaining modules. Provide evidence for thickness, geometry, properties, environment, loading, calibration and data-use rights.

## Core physics groups

The **63 groups** organize physical functions. Their explicit execution audit covers **232 APIs**. The **757 registered APIs** also include data, evidence, exchange and workflow contracts; they are not 757 independently validated physics solvers. Main parameters are shown below; each API link opens the complete contract.

| No. | Physical purpose | Representative API / full reference | Main inputs | Declared outputs |
|---|---|---|---|---|"""
    lines = [intro]
    for group in groups:
        number = group["group"]
        r = by_id[representative[number]]
        lines.append(
            f"| {number} | {GROUP_NAMES[number - 1]} | [`{r['id']}`]({REPO}/blob/main/{r['documentation']}) | {names(r['input_parameters'], 4)} | {names(r['declared_output_units'], 3)} |"
        )
    lines += [
        "",
        "## Complete API directory",
        "",
        "**(+N more)** explicitly marks abbreviated parameter lists. Click an API name for every top-level input, required/default status, constraints, nested JSON Schema and declared output units. Some result structures depend on the selected calculation branch. Detailed references remain in Korean; schema keys, parameter names and most model assumptions are in English.",
        "",
    ]
    for domain, items in sorted(domains.items()):
        lines += [
            f"### {domain}: {DOMAIN_NAMES[domain]} ({len(items)} APIs)",
            "",
            "| API / full reference | Purpose | Main inputs | Declared outputs |",
            "|---|---|---|---|",
        ]
        for r in items:
            purpose = r["purpose"]
            lines.append(
                f"| [`{r['id']}`]({REPO}/blob/main/{r['documentation']}) | {esc(purpose)} | {names(r['input_parameters'], 2)} | {names(r['declared_output_units'], 2)} |"
            )
        lines.append("")
    lines.append(f"""## Customization and integration

1. Identify the material, surface, environment, loading, time basis and inspection location.
2. Select an API and inspect its schema and assumptions with `describe()`.
3. Supply coefficients, properties and criteria with evidence and applicability limits. Pin external providers by identity, revision, configuration and data hashes.
4. Pass complete upstream results, context and digests to downstream APIs. Check coordinates, units, pressure conventions and physical scope.
5. Keep caller-defined requirement decisions separate from calculation status.

CoolProp interfaces provide thermodynamic states and fugacity where supported. Risk-system adapters require explicit probability semantics. FTA is one possible downstream consumer; deterministic thickness loss does not automatically become failure probability. See [architecture (Korean)]({REPO}/blob/main/docs/ARCHITECTURE_KO.md), [Python API (Korean)]({REPO}/blob/main/docs/API_KO.md) and [extension requests (Korean)]({REPO}/blob/main/docs/extension_requests/README_KO.md).

## Verification status and known limits

| Evidence | Recorded result | Scope |
|---|---|---|
| Public input schemas | 757/757 API contracts match | Contract availability and consistency |
| Audited normal core executions | 230/232 calculated | Two require measured initial-thickness evidence or underlying-observation use authorization |
| Representative reference values and physical identities | 79 checks across 63/63 groups passed | Does not cover every branch or establish experimental validity |
| Additional invariants and conservation checks | 57 checks passed | Includes hydrogen and thermal balances; overlaps earlier sets |
| Additional prepublication tests | 25/25 passed | Runtime regressions, boundaries, optional dependencies and release boundaries |
| Main JSON example executions | 400/400 passed | Main example file contains 400/757 API IDs |
| Historical installed-wheel numerical tests | 59/59 passed | Executed outside the working source tree |
| Base/full installed-source comparison | 2/2 matched | Includes base operation without SciPy or CoolProp |
| Alpha publication workflow | 79/79 selected tests passed; build and base-install smoke passed | Separate bounded release suite, not the 79 representative formula checks above |

Known unresolved items include **885 Ruff findings**, **one main-example completeness failure** and **two externally dependent normal executions**. The strict full verification workflow retains its original gates and may report failure. Alpha release checks do not replace full verification. Overlapping test counts must not be added to infer model validation coverage.

Read [release status (Korean)]({REPO}/blob/main/docs/RELEASE_STATUS_KO.md), [prepublication checks (Korean)]({REPO}/blob/main/docs/PREPUBLISH_CHECKS_KO.md), [core executions (Korean)]({REPO}/blob/main/docs/CORE_EXECUTION_VERIFICATION_KO.md) and [physical review (Korean)]({REPO}/blob/main/docs/PHYSICAL_REVIEW_KO.md).

## Continue research and development

```bash
python -m pytest -q tests/test_physical_consistency_review.py
python scripts/verify_core_physics_formulas.py
python scripts/audit_schema_coverage.py
python scripts/audit_public_source_boundary.py
# Strict full verification; known unresolved gates may fail:
python scripts/verify.py
```

The [research continuation guide (Korean)]({REPO}/blob/main/docs/RESEARCH_CONTINUATION_KO.md) explains count definitions, evidence locations, reproduction commands, data acquisition and rights review, model additions, HPC checks and next verification priorities. The [development history (Korean)]({REPO}/blob/main/docs/DEVELOPMENT_HISTORY_KO.md) preserves dated implementation and verification records.

## Licensing, data and security

Code is MIT licensed. External datasets, dependencies, standards and commercial providers retain their own rights. Raw observations, third-party documents, experimental workbooks, device signals, local execution logs and credentials are excluded from public distributions. Public accessibility alone does not grant redistribution rights in underlying observations.

Model names, independently written explanations, implementations and authored synthetic checks remain identifiable. See [third-party notices]({REPO}/blob/main/THIRD_PARTY_NOTICES.md) and the source catalog. Rights, wording and archive-boundary checks reduce risk; they do not establish legal clearance.

[Contributing]({REPO}/blob/main/CONTRIBUTING.md) · [Security]({REPO}/blob/main/SECURITY.md) · [Changelog]({REPO}/blob/main/CHANGELOG.md) · [Citation]({REPO}/blob/main/CITATION.cff)
""")
    return "\n".join(lines) + "\n"


def main():
    directory = json.loads((ROOT / "docs/API_DIRECTORY.json").read_text(encoding="utf8"))
    groups = json.loads((ROOT / "tests/data/core_physics_full_run_targets.json").read_text(encoding="utf8"))[
        "groups"
    ]
    handoffs = json.loads(
        (ROOT / "tests/data/core_physics_rule_handoff_cases.json").read_text(encoding="utf8")
    )["cases"]
    representative = {r["group"]: r["model_id"] for r in handoffs}
    text = build_readme(directory["models"], groups, representative, directory["version"])
    (ROOT / "README.md").write_text(text, encoding="utf8")
    print(
        f"English README: {len(directory['models'])} APIs, {len(groups)} groups, {len(text.encode())} bytes"
    )


if __name__ == "__main__":
    main()
