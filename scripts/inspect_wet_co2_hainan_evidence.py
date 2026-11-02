"""Audit only the five eastern-Hainan rows reproduced by an official secondary article."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from matintegrity.wet_co2_data import (
    WetCo2LiteratureEvidenceRow,
    WetCo2LiteratureFieldMap,
    audit_wet_co2_literature_row,
    read_unresolved_wet_co2_compilation,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPILATION = ROOT / "data/raw/heterogeneous-wet-co2-corrosion/CO2.csv"
DEFAULT_EVIDENCE = ROOT / "data/evidence/wet-co2/pipechina_2025_fulltext_api.json"
DEFAULT_OUTPUT = ROOT / "validation/wet_co2_hainan_secondary_crosswalk.json"
EXPECTED_EVIDENCE_SHA256 = "654c7ac3f5a11c5010782acb35059ed63c19a3a80c679fcad7c340ca1a34a236"
PRIMARY_DOI = "10.1016/j.jngse.2020.103716"
SECONDARY_DOI = "10.6047/j.issn.1000-8241.2025.10.006"


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        del attrs
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self._cell is not None:
            assert self._row is not None
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _extract_reproduced_rows(path: Path):
    digest = _digest(path)
    if digest != EXPECTED_EVIDENCE_SHA256:
        raise ValueError("official secondary-article evidence hash changed")
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = [
        paragraph
        for section in payload.get("data", {}).get("secList", [])
        for paragraph in section.get("paraContents", [])
        if paragraph.get("paraType") == "table" and paragraph.get("labelText") == "2"
    ]
    if len(candidates) != 1:
        raise ValueError("expected exactly one reproduced Hainan table 2")
    parser = _TableParser()
    parser.feed(candidates[0].get("paraContent", ""))
    numeric_rows = []
    for cells in parser.rows:
        if len(cells) == 10 and cells[0].isdigit():
            numeric_rows.append((int(cells[0]), tuple(float(value) for value in cells[1:])))
    if [row_number for row_number, _ in numeric_rows] != [1, 2, 3, 4, 60]:
        raise ValueError("reviewed secondary article no longer reproduces rows 1-4 and 60")
    return digest, numeric_rows


def _field_maps():
    basis = f"doi:{SECONDARY_DOI}#reproduced-table-2"
    return (
        WetCo2LiteratureFieldMap(
            compilation_field="raw_temperature",
            source_fields=("temperature_c",),
            operation="single_value_affine",
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:temperature-celsius",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_internal_pressure",
            source_fields=("total_pressure_kpa",),
            operation="single_value_affine",
            scale=0.01,
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:total-kpa-to-compilation-bar",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_co2_pressure",
            source_fields=("co2_pressure_kpa",),
            operation="single_value_affine",
            scale=0.01,
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:co2-kpa-to-compilation-bar",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_flow_velocity",
            source_fields=("flow_velocity_m_s",),
            operation="single_value_affine",
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:flow-velocity",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_ph",
            source_fields=("ph",),
            operation="single_value_affine",
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:ph",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_shear_stress",
            source_fields=("liquid_shear_pa", "gas_shear_pa"),
            operation="arithmetic_mean_affine",
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:two-phase-arithmetic-mean",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_corrosion_rate",
            source_fields=("corrosion_rate_mm_y",),
            operation="single_value_affine",
            absolute_tolerance=1e-12,
            reviewed_transform_basis_id=f"{basis}:corrosion-rate",
        ),
    )


def _source_values(values):
    temperature, liquid_holdup, pressure, co2_pressure, velocity, ph, liquid_shear, gas_shear, rate = values
    return {
        "temperature_c": temperature,
        "liquid_holdup": liquid_holdup,
        "total_pressure_kpa": pressure,
        "co2_pressure_kpa": co2_pressure,
        "flow_velocity_m_s": velocity,
        "ph": ph,
        "liquid_shear_pa": liquid_shear,
        "gas_shear_pa": gas_shear,
        "corrosion_rate_mm_y": rate,
    }


def _candidate_rows(compilation_rows, source_values):
    expected = {
        "raw_temperature": source_values["temperature_c"],
        "raw_internal_pressure": source_values["total_pressure_kpa"] * 0.01,
        "raw_co2_pressure": source_values["co2_pressure_kpa"] * 0.01,
        "raw_flow_velocity": source_values["flow_velocity_m_s"],
        "raw_ph": source_values["ph"],
        "raw_shear_stress": (source_values["liquid_shear_pa"] + source_values["gas_shear_pa"]) / 2.0,
    }
    return [
        row
        for row in compilation_rows
        if all(
            getattr(row, field) is not None
            and math.isclose(getattr(row, field), value, rel_tol=0.0, abs_tol=1e-12)
            for field, value in expected.items()
        )
    ]


def inspect(compilation_path=DEFAULT_COMPILATION, evidence_path=DEFAULT_EVIDENCE):
    compilation_rows = read_unresolved_wet_co2_compilation(Path(compilation_path))
    evidence_hash, reproduced_rows = _extract_reproduced_rows(Path(evidence_path))
    maps = _field_maps()
    audits = []
    candidate_counts = []
    for source_row_number, values in reproduced_rows:
        source_values = _source_values(values)
        candidates = _candidate_rows(compilation_rows, source_values)
        candidate_counts.append(len(candidates))
        if len(candidates) != 1:
            raise ValueError("reproduced Hainan row does not have one unique six-field candidate")
        evidence = WetCo2LiteratureEvidenceRow(
            evidence_id=f"doi:{SECONDARY_DOI}:table-2-row-{source_row_number}",
            source_group_id=f"doi:{PRIMARY_DOI}",
            source_record_id=f"reported-location-{source_row_number}",
            source_locator=f"secondary-article-table-2-row-{source_row_number}",
            bibliographic_id=f"doi:{PRIMARY_DOI}",
            bibliographic_link_status="secondary_reproduction_row",
            compilation_row_link_status="bibliographically_supported_numeric_sequence",
            compilation_row_link_basis_id=(
                "associated-compilation-citation-plus-unique-six-field-transformed-match"
            ),
            evidence_asset_sha256=evidence_hash,
            source_values=source_values,
            source_data_role="field_observation",
            publication_license_id=None,
            observation_redistribution_status="not_verified",
            data_dictionary_status="partial",
            physical_specimen_identity_status="unresolved",
        )
        audits.append(audit_wet_co2_literature_row(candidates[0], evidence, maps))

    counts = {
        field: Counter(
            comparison.status
            for audit in audits
            for comparison in audit.comparisons
            if comparison.compilation_field == field
        )
        for field in (mapping.compilation_field for mapping in maps)
    }
    mismatches = [
        {
            "source_record_id": audit.source_record_id,
            "compilation_provider_source_row": audit.compilation_provider_source_row,
            "field": comparison.compilation_field,
            "source_value": comparison.transformed_source_value,
            "compilation_value": comparison.compilation_value,
            "absolute_difference": comparison.absolute_difference,
        }
        for audit in audits
        for comparison in audit.comparisons
        if comparison.status == "mismatch"
    ]
    return {
        "schema": "matintegrity.wet_co2_hainan_secondary_crosswalk_aggregate.v1",
        "compilation_dataset_id": "heterogeneous-wet-co2-corrosion",
        "compilation_sha256": compilation_rows[0].source_archive_sha256,
        "primary_source_doi": PRIMARY_DOI,
        "secondary_source_doi": SECONDARY_DOI,
        "secondary_evidence_sha256": evidence_hash,
        "primary_reported_rows": 60,
        "secondary_rows_reproduced": [number for number, _ in reproduced_rows],
        "secondary_rows_checked": len(audits),
        "unique_candidate_count_by_reproduced_row": candidate_counts,
        "candidate_compilation_provider_source_rows": [
            audit.compilation_provider_source_row for audit in audits
        ],
        "comparison_status_by_field": {
            field: dict(sorted(field_counts.items())) for field, field_counts in counts.items()
        },
        "mismatches": mismatches,
        "source_group_assignment_status": "candidate_not_qualified",
        "reason_not_qualified": (
            "The official secondary article reproduces only five of the primary paper's sixty rows; "
            "the primary table is unavailable, one reproduced corrosion rate disagrees, physical "
            "location/specimen identity is unresolved, and observation redistribution is unverified."
        ),
        "automatic_correction_performed": False,
        "empirical_calibration_ready": False,
        "mechanistic_calibration_ready": False,
        "public_release_boundary": (
            "Only this aggregate audit is public. The API response and pointwise table remain outside "
            "distribution."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--compilation", type=Path, default=DEFAULT_COMPILATION)
    parser.add_argument("--evidence-json", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = inspect(args.compilation, args.evidence_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
