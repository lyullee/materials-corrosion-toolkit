"""Review acquired signed curves and preserve unresolved galvanic-transfer assumptions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from matintegrity.contracts import Evidence
from matintegrity.data import read_galvanized_polarization
from matintegrity.models.electrochemistry import PolarizationCurve

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/galvanized-polarization"
ELECTROLYTES = {
    "Hydrochloric acid": "0.1 mol/L HCl; nitrogen-purged",
    "Sulfuric acid": "0.1 mol/L H2SO4; nitrogen-purged",
    "Sodium_chloride": "5 percent NaCl; concentration basis not identified in reviewed method; nitrogen-purged",
}


def inspect():
    workbooks = []
    catalog = json.loads((ROOT / "data/catalogs/datasets.json").read_text(encoding="utf-8"))
    dataset = next(row for row in catalog["datasets"] if row["id"] == "galvanized-polarization")
    assets = {asset["filename"]: asset for asset in dataset["assets"]}

    def checked_digest(path):
        content = path.read_bytes()
        algorithm, expected = assets[path.name]["checksum"].split(":", 1)
        if hashlib.new(algorithm, content).hexdigest() != expected:
            raise ValueError("polarization protocol/data file differs from the pinned provider checksum")
        return hashlib.sha256(content).hexdigest()

    expected_workbooks = {name for name in assets if "polarization" in name and name.endswith(".xlsx")}
    if {path.name for path in RAW.glob("*polarization*.xlsx")} != expected_workbooks:
        raise ValueError("acquire exactly the three pinned polarization workbooks before inspection")
    for path in sorted(RAW.glob("*polarization*.xlsx")):
        digest = checked_digest(path)
        frame = read_galvanized_polarization(path)
        summaries = []
        for (electrolyte, specimen), group in frame.groupby(["electrolyte_id", "specimen_id"], sort=False):
            potential = group.potential_V.to_numpy()
            current = group.signed_current_density_A_m2.to_numpy()
            curve = PolarizationCurve(
                curve_id=f"{path.name}:{electrolyte}:{specimen}",
                surface_condition_id=specimen,
                protocol_id="metals-14-00993-p6-potentiodynamic-0.002V-per-s",
                electrolyte_id=ELECTROLYTES[electrolyte],
                reference_electrode_id="study-local-AgAgCl-filling-and-conversion-unresolved",
                temperature_K=298.15,
                point_ids=[f"source-row-{row}" for row in group.source_row],
                potential_V=potential.tolist(),
                signed_net_current_density_A_m2=current.tolist(),
                current_convention="unreviewed_signed_net",
                evidence=(
                    Evidence(
                        source_id="galvanized-polarization",
                        origin="open_dataset",
                        citation="Vontorova, Novak and Vanova; doi:10.5281/zenodo.13886478; source rows retained locally",
                        license_id="CC-BY-4.0",
                        sha256=digest,
                    ),
                ),
            )
            assert PolarizationCurve.model_validate_json(curve.model_dump_json()) == curve
            differences = np.diff(potential)
            summaries.append(
                dict(
                    specimen_id=specimen,
                    electrolyte_id=electrolyte,
                    points=len(group),
                    potential_range_V=[float(potential.min()), float(potential.max())],
                    increasing_intervals=int(np.sum(differences > 0)),
                    duplicate_potential_intervals=int(np.sum(differences == 0)),
                    reverse_potential_intervals=int(np.sum(differences < 0)),
                    negative_net_current_points=int(np.sum(current < 0)),
                    sign_crossing_intervals=int(
                        np.sum(
                            ((current[:-1] < 0) & (current[1:] > 0))
                            | ((current[:-1] > 0) & (current[1:] < 0))
                        )
                    ),
                    curve_contract_json_round_trip="passed",
                )
            )
        workbooks.append(dict(file=path.name, sha256=digest, rows=len(frame), curves=summaries))
    article = RAW / "metals-14-00993.pdf"
    review = dict(
        source_url="https://doi.org/10.3390/met14090993",
        method_page=6,
        article_sha256=checked_digest(article) if article.exists() else None,
        reference_family="Ag/AgCl; source-local reference; filling solution and inter-reference offset unresolved",
        temperature_K=298.15,
        reported_scan_rate_V_s=0.002,
        reported_potential_range_V=[-1.5, 1.0],
        recorded_maximum_potential_V=sorted(
            {curve["potential_range_V"][1] for workbook in workbooks for curve in workbook["curves"]}
        ),
        reported_immersion_depth_m=0.01,
        immersion_depth_is_exposed_area=False,
        reported_nitrogen_purge_duration_s=1800.0,
        ohmic_compensation="not identified in reviewed method",
        quasi_steady_galvanic_transfer="not established by recorded scan rate or single-electrode fits",
        coupled_experiment_validation="not supplied by these individual-electrode workbooks",
    )
    return dict(
        workbooks=workbooks,
        curves=sum(len(row["curves"]) for row in workbooks),
        numeric_points=sum(row["rows"] for row in workbooks),
        protocol_review=review,
        mixed_potential_readiness="needs_data",
        missing_reviews=[
            "coupled exposed areas",
            "ohmic-drop applicability",
            "quasi-steady transfer",
            "reference consistency and source-local potential convention",
        ],
        qualification="Signed current ingestion and reviewed protocol metadata only. Published Rp is labelled ohm without area normalization and is not silently passed to Stern-Geary. No sorting, Tafel-window selection, equilibrium prediction, metal-loss calibration or independent galvanic validation. Raw observations and article remain outside public releases.",
    )


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2))
