"""Illustrative local streaming use; this example is intentionally not executed."""

from pathlib import Path

from matintegrity.metropt3_data import (
    MetroPT3ArchiveAuthorization,
    iter_metropt3_rows,
)


authorization = MetroPT3ArchiveAuthorization(
    attribution="UCI Machine Learning Repository, MetroPT-3, DOI 10.24432/C5VW3R",
    computational_use_authorized=True,
    local_only_authorized=True,
)

archive = Path("data/raw/metropt3/metropt+3+dataset.zip")
for index, row in enumerate(iter_metropt3_rows(archive, authorization=authorization)):
    print(row.timestamp_text, row.signal_values_provider_native["TP2"])
    if index == 2:
        break
