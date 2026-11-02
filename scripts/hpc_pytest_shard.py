"""Run a deterministic subset of the pytest collection without an xdist dependency."""

import argparse
import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DeterministicShard:
    def __init__(self, index: int, count: int):
        self.index = index
        self.count = count

    def pytest_collection_modifyitems(self, config, items):
        selected = []
        deselected = []
        for item in items:
            digest = hashlib.sha256(item.nodeid.encode("utf-8")).digest()
            target = int.from_bytes(digest[:8], "big") % self.count
            (selected if target == self.index else deselected).append(item)
        if deselected:
            config.hook.pytest_deselected(items=deselected)
        items[:] = selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--shard-count", type=int, required=True)
    parser.add_argument("--junitxml", type=Path, required=True)
    args = parser.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        parser.error("shard index must be inside [0, shard count)")
    args.junitxml.parent.mkdir(parents=True, exist_ok=True)
    raise SystemExit(
        pytest.main(
            ["-q", f"--junitxml={args.junitxml}", "tests"],
            plugins=[DeterministicShard(args.shard_index, args.shard_count)],
        )
    )


if __name__ == "__main__":
    main()
