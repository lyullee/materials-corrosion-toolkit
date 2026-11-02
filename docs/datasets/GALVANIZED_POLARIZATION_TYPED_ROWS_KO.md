# Galvanized-steel polarization typed rows

This adapter wraps the existing `read_galvanized_polarization()` parser for the three catalogued Zenodo potentiodynamic workbooks: HCl, H2SO4, and NaCl. It pins each asset to the byte count and MD5 recorded in the dataset catalog, computes an additional SHA-256 for local row lineage, and emits typed rows from the parser's original sheet/specimen order. The current parser loads one small workbook into a DataFrame before the iterator yields records; this interface does not claim streaming file I/O.

The dataset is the galvanized DRECE steel polarization collection at [Zenodo DOI 10.5281/zenodo.13886478](https://doi.org/10.5281/zenodo.13886478), catalogued under CC BY 4.0. Zenodo's official record metadata is available at [the record API](https://zenodo.org/api/records/13886478). Callers supply attribution and explicitly authorize computational/local use. Every emitted row preserves the source filename, provider source row, per-call sample index, specimen and electrolyte labels, file MD5/SHA-256, authorization digest, local-only status, potential as reported, and signed current density. The provider current-density unit A/cm2 is retained alongside the existing parser's A/m2 conversion.

## Use

```python
from matintegrity.galvanized_polarization_rows import (
    GalvanizedPolarizationReadAuthorization,
    iter_galvanized_polarization_samples,
)

authorization = GalvanizedPolarizationReadAuthorization(
    attribution="Vontorova et al., Zenodo 10.5281/zenodo.13886478",
    computational_use_authorized=True,
    local_only_authorized=True,
)
for sample in iter_galvanized_polarization_samples(
    local_workbook_path,
    authorization=authorization,
):
    consume(sample)
```

`data.zenodo_galvanized_polarization_typed_rows` exposes a metadata-only audit through the model registry. It does not return local paths or sample values.

## Interpretation limits

Potential-reference details are not inferred from the generic potential header. The adapter does not choose anodic/cathodic Tafel windows, compensate solution resistance, fit corrosion current, infer corrosion rate, rank materials, or decide protection/acceptance. These experiments concern zinc-coated, DRECE-processed steel in laboratory electrolytes and should not be treated as pressure-equipment field corrosion rates. Raw workbook files and point values are not copied into the package.
