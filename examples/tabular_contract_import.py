"""Import synthetic JSONL rows into a public contract with a caller-owned mapping profile."""

from pathlib import Path

from matintegrity.identification import MaterialDesignation
from matintegrity.tabular_contract_import import (
    TabularFieldMapping,
    TabularImportProfile,
    read_jsonl_contracts,
)

SOURCE = Path(__file__).with_name("material_designations.json")
PROFILE = TabularImportProfile(
    profile_id="synthetic-material-designation-v1",
    target_contract="MaterialDesignation",
    mappings=tuple(
        TabularFieldMapping(target_path=(name,), source_path=(name,))
        for name in ("namespace", "specification", "edition", "grade", "product_form", "condition")
    ),
)


def main() -> None:
    records, report = read_jsonl_contracts(SOURCE, MaterialDesignation, PROFILE)
    print(report.model_dump_json(indent=2))
    for record in records:
        print(record.model_dump_json())


if __name__ == "__main__":
    main()
