"""Verify the bounded applicability review for the carbide-trap hydrogen exports."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "data/data_inventory.json"
TARGET = ROOT / "validation/hydrogen_carbide_applicability.json"


def main() -> None:
    inventory_bytes = INVENTORY_PATH.read_bytes()
    inventory = json.loads(inventory_bytes)
    carbide = inventory["datasets"]["carbide-traps"]
    exports = carbide["numeric_exports"]
    protocol = carbide["protocol_review"]

    tds_exports = [
        row for row in exports["files"] if row["reader"] in {"read_tds_export", "read_tds_exposure_summary"}
    ]
    if len(tds_exports) != 3:
        raise AssertionError(f"expected three TDS exports, found {len(tds_exports)}")
    if any(row.get("ppm_basis") != "hydrogen_mass_per_sample_mass" for row in tds_exports):
        raise AssertionError("TDS exports do not preserve the reviewed mass-ppm basis")
    if protocol["tds_reported_content_basis"] != "hydrogen_mass_per_sample_mass":
        raise AssertionError("protocol review does not preserve the reviewed mass-ppm basis")
    if protocol["tds_nominal_heating_rate_measured_clock_equivalent"] is not False:
        raise AssertionError("nominal TDS heating rate must not be treated as a measured clock")
    if protocol["measured_sample_clock_available"] is not False:
        raise AssertionError("a measured TDS sample clock was not established")

    mappings = protocol["tds_raw_workbook_material_mapping"]
    expected_mappings = {"IP0time": "TiC steel", "IP2time": "(Ti,Mo)C steel"}
    for workbook, material in expected_mappings.items():
        mapping = mappings[workbook]
        if mapping["candidate_material"] != material:
            raise AssertionError(f"unexpected candidate mapping for {workbook}")
        if "not_specimen_identity" not in mapping["status"]:
            raise AssertionError(f"{workbook} mapping overstates specimen identity")

    readiness = {
        "tds_mass_normalized_signal_conversion_ready": protocol[
            "tds_mass_normalized_signal_conversion_ready"
        ],
        "tds_transport_inverse_ready": protocol["tds_transport_inverse_ready"],
        "permeation_transport_inverse_ready": protocol["permeation_transport_inverse_ready"],
    }
    if any(readiness.values()):
        raise AssertionError(f"experimental readiness is overstated: {readiness}")

    required_tds_inverse_blockers = {
        "measured_sample_clock_absent",
        "initial_spatial_hydrogen_distribution_not_established",
        "curved_and_end_surface_release_conditions_not_established",
        "detector_dynamics_not_established",
    }
    required_permeation_blockers = {
        "membrane_thickness_not_reported",
        "exposed_area_not_reported",
        "potential_reference_not_reported",
        "raw_curve_to_material_and_replicate_mapping_not_established",
    }
    if not required_tds_inverse_blockers.issubset(protocol["tds_transport_inverse_blockers"]):
        raise AssertionError("TDS inverse blockers are incomplete")
    if not required_permeation_blockers.issubset(protocol["permeation_transport_inverse_blockers"]):
        raise AssertionError("permeation inverse blockers are incomplete")

    record = {
        "schema_version": "matintegrity.validation.hydrogen_carbide_applicability.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "review_sources": {
            "article_url": protocol["source_url"],
            "supplementary_information_url": protocol["supplementary_information_url"],
            "supplementary_information_sha256": protocol["supplementary_information_sha256"],
            "license": protocol["source_license"],
        },
        "confirmed_metadata": {
            "tds_content_basis": protocol["tds_reported_content_basis"],
            "tds_nominal_heating_rate_K_h": protocol["tds_nominal_heating_rate_from_workbook_K_h"],
            "nominal_heating_rate_is_measured_clock": protocol[
                "tds_nominal_heating_rate_measured_clock_equivalent"
            ],
            "permeation_error_statistic": protocol["permeation_summary_error_statistic"],
        },
        "candidate_material_mappings": mappings,
        "readiness": readiness,
        "blockers": {
            "tds_mass_normalized_signal": protocol["tds_mass_normalized_signal_blockers"],
            "tds_transport_inverse": protocol["tds_transport_inverse_blockers"],
            "permeation_transport_inverse": protocol["permeation_transport_inverse_blockers"],
        },
        "qualification": (
            "Public metadata and export contracts support the TDS mass-ppm basis and bounded "
            "candidate material mappings. They do not establish curve-level specimen identity, "
            "detector calibration, a measured TDS clock, permeation geometry or transport-inverse "
            "readiness. No pointwise observations are copied into this artifact."
        ),
    }
    TARGET.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
