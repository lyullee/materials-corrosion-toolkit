# Zenodo cathodic-protection typed sample rows

The existing DPlot parser already validates the five selected CSV exports against their pinned SHA-256 values and reconstructs eight provider curves. `iter_cathodic_protection_samples()` adds a typed row view over that parser without duplicating its format logic. It yields values in the catalogued file order, parser curve order and within-curve sample order.

The selected dataset is the CREATE Year 1 cathodic-protection collection, Zenodo DOI [10.5281/zenodo.18735817](https://doi.org/10.5281/zenodo.18735817). Zenodo's official record metadata reports `cc-by-4.0`; the evidence endpoint is [Zenodo record API](https://zenodo.org/api/records/18735817). Callers provide attribution and explicitly authorize local computational use. The raw exports remain in the ignored local cache and are not copied into the public package.

Every row carries the source filename and SHA-256, a digest of its curve record, curve index and label, within-curve sample index, provider-native x value and potential value, caller attribution and authorization digest. Open-circuit-potential exports retain the provider time axis in seconds. Potentiodynamic exports retain an unresolved current-axis unit because the provider's exponent is ambiguous. The potential is labelled as reported versus calomel, while the exact reference-electrode subtype remains unresolved. File hashes are local-copy integrity pins, not publisher-issued checksums.

These are provider curve samples only. The adapter does not infer protection thresholds, corrosion current or corrosion rate, exposure conditions, electrode subtype, acceptance, failure probability or material ranking. The separate CP workbook remains outside this row view. Existing dataset rights and interpretation limitations are summarized in `docs/DATA_KO.md`.

The example in `examples/cathodic_protection_typed_rows_local.py` is illustrative and was not executed.

`data.zenodo_cathodic_protection_sample_rows` is registered for a metadata-only audit through the model registry. It requires the local directory and an explicit authorization object, does not return sample rows or the path, and leaves row access to the lazy iterator.
