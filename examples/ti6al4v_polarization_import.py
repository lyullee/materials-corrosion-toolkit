"""Import a locally acquired, pinned CC0 Zenodo Ti-6Al-4V polarization CSV."""

import argparse
from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.galvanic_data import (
    TI6AL4V_FIG1_SHA256,
    Ti6Al4VCathodicPolarizationImportRequest,
    import_ti6al4v_cathodic_polarization_csv,
)

parser = argparse.ArgumentParser()
parser.add_argument("csv", type=Path, help="locally acquired Fig1.csv from Zenodo record 12727325")
parser.add_argument("--medium", choices=("pbs", "pbs_h2o2"), default="pbs")
args = parser.parse_args()

request = Ti6Al4VCathodicPolarizationImportRequest(
    curve_id=f"zenodo-ti6al4v-{args.medium}",
    medium=args.medium,
    expected_csv_sha256=TI6AL4V_FIG1_SHA256,
    surface_condition_id="ti6al4v-source-condition-see-zenodo-readme",
    protocol_id="zenodo-12727325-pdp-scan",
    electrolyte_id="pbs-plus-33mm-h2o2" if args.medium == "pbs_h2o2" else "pbs",
    reference_electrode_id="SCE",
    temperature_K=296.15,
    source_conditions_reviewed=True,
    source_reference_and_scan_identity_reviewed=True,
    unit_conversion_reviewed=True,
    evidence=(Evidence(
        source_id="zenodo-ti6al4v-cathodic-corrosion",
        origin="open_dataset",
        citation="Zenodo record 12727325; https://doi.org/10.5281/zenodo.12727325",
        license_id="CC0-1.0",
        sha256=TI6AL4V_FIG1_SHA256,
    ),),
)
result = import_ti6al4v_cathodic_polarization_csv(args.csv.read_bytes(), request)
print(result.model_dump(mode="json"))
