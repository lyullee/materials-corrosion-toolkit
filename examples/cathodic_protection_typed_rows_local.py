"""Illustrative typed row access; intentionally not executed."""

from pathlib import Path

from matintegrity.cathodic_protection_data import (
    CathodicProtectionReadAuthorization,
    iter_cathodic_protection_samples,
)


authorization = CathodicProtectionReadAuthorization(
    attribution="Okeil et al., CREATE Year 1 dataset, Zenodo DOI 10.5281/zenodo.18735817",
    computational_use_authorized=True,
    local_only_authorized=True,
)

data_dir = Path("data/raw/zenodo-18735817-cathodic-protection")
for index, row in enumerate(iter_cathodic_protection_samples(data_dir, authorization=authorization)):
    print(row.source_filename, row.provider_curve_label, row.curve_sample_index, row.potential_V_vs_calomel)
    if index == 9:
        break
