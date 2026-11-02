"""Read the pinned CC0 Zenodo DEIS matrix from the ignored local data cache.

This example reports only metadata and a bounded first-row shape. It does not print or persist
provider measurements and makes no frequency, time, circuit, or corrosion claim.
"""

from pathlib import Path

from matintegrity.zenodo_deis_import import (
    create_zenodo_deis_adjacent_pair_view,
    inspect_zenodo_deis_archive,
    iter_zenodo_deis_adjacent_spectrum_pairs,
    summarize_zenodo_deis_depositor_conditions,
)


project_root = Path(__file__).resolve().parents[1]
archive = project_root / "data/raw/az-we43-az31-molybdate-eis/Dataset_CorSci.zip"
manifest = inspect_zenodo_deis_archive(archive)
metadata_path = project_root / "data/raw/az-we43-az31-molybdate-eis/Metadata_Description.txt"
conditions = summarize_zenodo_deis_depositor_conditions(metadata_path)

for item in manifest.matrices:
    view = create_zenodo_deis_adjacent_pair_view(
        manifest,
        conditions,
        item.member_path,
        zero_based_adjacent_pairing_reviewed=True,
    )
    row_index, pairs = next(iter_zenodo_deis_adjacent_spectrum_pairs(archive, manifest, view))
    print(item.member_path, "row_index", row_index, "pair_count", len(pairs), item.member_sha256)

print("metadata_sha256", conditions.metadata_sha256)
print("provider_condition_summary", conditions.model_dump(mode="json"))
