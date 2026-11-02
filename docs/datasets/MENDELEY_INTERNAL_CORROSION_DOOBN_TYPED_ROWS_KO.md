# Mendeley internal-corrosion DOOBN workbook reader

## Dataset and reuse boundary

- Dataset: [Mendeley Data version 3](https://data.mendeley.com/datasets/g5h5gktwnd/3), DOI `10.17632/g5h5gktwnd.3`.
- Official machine-readable record: [Mendeley public dataset API](https://data.mendeley.com/public-api/datasets/g5h5gktwnd).
- Dataset-level license: CC BY 4.0. Attribution must identify the versioned dataset, include the license, and mark changes. The provider's license metadata also cautions that some embedded third-party material can require separate permission.
- The dataset record describes probabilistic relationships for an internal-corrosion Dynamic Object-Oriented Bayesian Network and says the data were prepared using expert elicitation. These are model inputs, not independent field measurements or universal probabilities.
- The workbook file is `Internal Corrosion - Export Gas Data - 2015 to 2020.xlsx`, 271,763 bytes, official SHA-256 `44f03e17d5669d20ed3ea6a35132e89a68b9e6755be5a5f87dca421830bff0b6`.
- The record also lists `Internal corrosion nodes in DOOBN model.pdf`, 249,087 bytes, official SHA-256 `d3cc2d1d12a8b41eab622c84886eb40c0b0eb6ef9e172d837300421adccc1c53`. This reader neither downloads nor interprets that PDF.

The pinned XLSX is kept under ignored `data/raw/mendeley-internal-corrosion-doobn/`. Do not place raw cells in release files, fixtures, or examples. The parser preserves spreadsheet structure only; a separately reviewed consumer is responsible for deciding which fields are usable and whether independent source permissions are needed.

## API

- `InternalCorrosionReadAuthorization` requires attribution, dataset DOI, CC BY identifier, and explicit local computational-use authorization.
- `InternalCorrosionWorkbookCell` preserves column number, cell address, Excel storage type, and raw value. Formula cells remain formula strings.
- `InternalCorrosionWorkbookRow` binds every row to dataset/file identity, authorization digest, Evidence, and a canonical row digest.
- `iter_internal_corrosion_doobn_rows(path, authorization=...)` yields nonempty original rows after checking the exact filename, byte count, provider SHA-256, sheet name, and dimensions.
- `audit_internal_corrosion_doobn_workbook(request)` reports workbook structure and file digests without returning cell values.
- Model/interface ID: `data.mendeley_internal_corrosion_doobn_typed_rows`; source ID: `mendeley_internal_corrosion_doobn_xlsx_rows`.
- JSON schema, default registry and capability/source catalog integration are maintained centrally.

Example for a downstream local caller:

```python
from matintegrity.mendeley_internal_corrosion_doobn_rows import (
    InternalCorrosionReadAuthorization,
    iter_internal_corrosion_doobn_rows,
)

authorization = InternalCorrosionReadAuthorization(
    attribution=(
        "Dao et al. (2023), Mendeley Data v3, DOI 10.17632/g5h5gktwnd.3; "
        "CC BY 4.0; workbook values used locally with source review"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)
for row in iter_internal_corrosion_doobn_rows(
    "data/raw/mendeley-internal-corrosion-doobn/"
    "Internal Corrosion - Export Gas Data - 2015 to 2020.xlsx",
    authorization=authorization,
):
    # A project-specific parser must establish field meaning before use.
    print(row.worksheet_name, row.provider_row_number, row.source_row_sha256)
```

This API does not map fields into conditional probability tables, check normalization or network structure, estimate corrosion rates, train models, or execute DOOBN/FTA calculations. Expert judgments must remain distinguishable from observations, and any later risk adapter needs an independently documented mapping and validation plan.
