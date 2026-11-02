"""Record a manually reviewed Origin Viewer export set; never execute project scripts."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from matintegrity.hydrogen_exports import TabularExportProvenance

ROOT = Path(__file__).resolve().parents[1]
MEMBER_FOLDER = "Thermal desorption spectroscopy and hydroge permeability raw data/"
PROJECTS = {
    "H Permeation test.opju": "603e26cab507e289aad956d5c4ec7285e66129eb2797c23e6afb4a31e990f3c2",
    "TDS.opju": "c02925f4b284656dc241c75ba9f6fb0c4373dcb4656fda8bf84fbfd7a7485c0d",
}
EXPORTS = [
    ("BQ0.csv", ["permeation_A20201129ZBNB.csv"], "A20201129ZBNB", "BQ0", "viewer_reviewed"),
    ("BQ2.csv", ["permeation_A20201201ZBNB.csv"], "A20201201ZBNB", "BQ2", "viewer_reviewed"),
    ("BQ0_2nd.csv", [], "A20201202ZBNB", "unverified", "mapping_requires_review"),
    ("BQ2-2nd.csv", [], "A20201213ZBNB", "unverified", "mapping_requires_review"),
    ("20201213-ZBN-Fe_Mo_hot_rolled-ya.csv", [], "A20201213ZBNF", "unverified", "mapping_requires_review"),
    ("b_diffusion_coefficient.csv", [], "Book1", "Sheet2", "viewer_reviewed"),
    ("tds_IP0time.csv", [], "IP0time", "Sheet1", "viewer_reviewed"),
    ("tds_IP2time.csv", [], "IP2time", "Sheet1", "viewer_reviewed"),
    ("tds_A4ElapsedTime_Sheet1.csv", [], "A4ElapsedTime", "Sheet1", "viewer_reviewed"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tool-version", required=True, help="Actual reviewed Viewer version, e.g. 10.4.0.25"
    )
    args = parser.parse_args()
    folder = ROOT / "data/derived/carbide-traps/viewer-export"
    ledger = json.loads((ROOT / "data/acquisition_log.json").read_text(encoding="utf-8"))
    acquisition = [
        r for r in ledger["attempts"] if r["dataset_id"] == "carbide-traps" and r["status"] == "downloaded"
    ][-1]
    archive_sha256 = acquisition["sha256"]
    archive_path = ROOT / "data/raw/carbide-traps/NCOMMS-23-27903B data.zip"
    if archive_path.stat().st_size != acquisition["bytes"]:
        raise ValueError("archive size differs from acquisition record")
    with zipfile.ZipFile(archive_path) as archive:
        for name, expected in PROJECTS.items():
            if hashlib.sha256(archive.read(MEMBER_FOLDER + name)).hexdigest() != expected:
                raise ValueError("project member digest mismatch")
    exports = []
    for name, aliases, workbook, worksheet, review in EXPORTS:
        candidates = [folder / filename for filename in [name, *aliases] if (folder / filename).is_file()]
        if not candidates:
            raise FileNotFoundError(f"missing reviewed export: {name}")
        hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in candidates}
        if len(hashes) != 1:
            raise ValueError("purported duplicate exports differ; review versions instead of merging")
        project = "TDS.opju" if name.startswith("tds_") else "H Permeation test.opju"
        reference = TabularExportProvenance(
            dataset_id="carbide-traps",
            archive_sha256=archive_sha256,
            member_path=MEMBER_FOLDER + project,
            member_sha256=PROJECTS[project],
            tool_name="Origin Viewer",
            tool_version=args.tool_version,
            workbook_id=workbook,
            worksheet_id=worksheet,
            csv_sha256=next(iter(hashes)),
            identity_review=review,
        )
        if name == "b_diffusion_coefficient.csv":
            reader, kwargs = (
                "read_permeation_summary",
                dict(label_policy="join_split_ti_mo", diffusivity_unit="m2/s", concentration_unit="ppm"),
            )
        elif name == "tds_A4ElapsedTime_Sheet1.csv":
            reader, kwargs = (
                "read_tds_exposure_summary",
                dict(
                    exposure_unit="h",
                    content_unit="ppm",
                    ppm_basis="hydrogen_mass_per_sample_mass",
                ),
            )
        elif name.startswith("tds_"):
            reader, kwargs = (
                "read_tds_export",
                dict(
                    temperature_unit="degC",
                    rate_unit="ppm/s",
                    ppm_basis="hydrogen_mass_per_sample_mass",
                ),
            )
        else:
            reader, kwargs = (
                "read_permeation_export",
                dict(potential_unit="V", current_unit="A", clock_unit="s"),
            )
        exports.append(
            dict(
                filename=candidates[0].name,
                duplicate_filenames=[p.name for p in candidates[1:]],
                provenance=reference.model_dump(mode="json"),
                reader=reader,
                reader_kwargs=kwargs,
            )
        )
    manifest = dict(
        schema_version="matintegrity.hydrogen_export_set.v1",
        exports=exports,
        archive_hash_basis="previous_checksum_verified_acquisition_record; project members rehashed here",
        review_basis="Viewer project/workbook display and graph axes plus the CC-BY-4.0 article supplement; unknown worksheet identities remain marked. Permeation current scale correspondence is reviewed but membrane thickness, electrode area, potential reference and charging origin remain unresolved. The supplement identifies the TDS rate and content as hydrogen mass ppm per sample mass and the nominal program as 100 K/h; the source-derived integral column units, measured sample clock, detector response and exact physical specimen identities remain unresolved. Auxiliary fits were not exported as measurements.",
    )
    (folder / "export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "unique_exports": len(exports),
                "duplicate_exports": sum(len(r["duplicate_filenames"]) for r in exports),
            }
        )
    )


if __name__ == "__main__":
    main()
