"""Local JSON interface with nonzero exit status for invalid requests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import RunContext
from .registry import default_registry
from .tabular_contract_import import (
    TabularImportProfile,
    read_csv_contracts,
    read_jsonl_contracts,
)


def main():
    parser = argparse.ArgumentParser(prog="matintegrity")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("models")
    describe = sub.add_parser("describe")
    describe.add_argument("model")
    run = sub.add_parser("run")
    run.add_argument("input", type=Path)
    run.add_argument("--out", type=Path)
    tabular = sub.add_parser("import-tabular")
    tabular.add_argument("model")
    tabular.add_argument("input", type=Path)
    tabular.add_argument("profile", type=Path)
    tabular.add_argument("--format", choices=("csv", "jsonl"), required=True)
    tabular.add_argument("--out", type=Path)
    args = parser.parse_args()
    registry = default_registry()
    try:
        if args.command == "models":
            result = {"models": registry.list_models()}
        elif args.command == "describe":
            result = registry.describe(args.model)
        elif args.command == "run":
            payload = json.loads(args.input.read_text(encoding="utf-8"))
            if set(payload) != {"model_id", "inputs", "context"}:
                raise ValueError("request requires exactly model_id, inputs and context")
            context = RunContext.model_validate_json(json.dumps(payload["context"]))
            result = registry.run_json(
                payload["model_id"], json.dumps(payload["inputs"], allow_nan=False), context
            ).model_dump(mode="json")
        else:
            profile = TabularImportProfile.model_validate_json(args.profile.read_text(encoding="utf-8"))
            contract_type = registry.input_type(args.model)
            reader = read_csv_contracts if args.format == "csv" else read_jsonl_contracts
            records, report = reader(args.input, contract_type, profile)
            result = {
                "report": report.model_dump(mode="json"),
                "records": [record.model_dump(mode="json") for record in records],
            }
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.command in {"run", "import-tabular"} and args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(encoded, encoding="utf-8")
        else:
            print(encoded)
    except (ValueError, KeyError, TypeError, ImportError) as exc:
        parser.exit(2, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
