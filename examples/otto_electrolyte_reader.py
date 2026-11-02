"""Read a caller-downloaded, CC BY Otto dataset archive without exporting rows."""

from __future__ import annotations

import argparse

from matintegrity.otto_electrolyte_data import read_otto_electrolyte_archive


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", help="path to the provider otto_data.zip archive")
    args = parser.parse_args()
    rows = read_otto_electrolyte_archive(args.archive)
    print({
        "records": len(rows),
        "unique_runs": len({row.source_run_id for row in rows}),
        "protocols": sorted({row.test_protocol_as_reported for row in rows}),
        "source_archive_sha256": rows[0].source_archive_sha256,
        "pointwise_records_printed": False,
        "corrosion_polarization_conversion": False,
    })


if __name__ == "__main__":
    main()
