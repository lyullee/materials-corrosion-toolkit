# Mendeley AM-MPEA corrosion database: metadata-only review

- Review date: 2026-11-01
- Current record version observed: version 3, DOI `10.17632/cfz68tkwfk.3`
- Public record: [Mendeley Data version 3](https://data.mendeley.com/datasets/cfz68tkwfk/3)
- Provider-stated license: CC BY 4.0
- Decision: retain as a metadata-only candidate; do not add a numeric importer or model-validation dataset yet.

## Why this is a strong candidate

The record directly concerns corrosion of additively manufactured multi-principal-element alloys. The provider describes composition and phase information, additive-manufacturing process descriptors, electrolyte identity and concentration, and corrosion-related endpoints including corrosion potential, pitting potential and corrosion current density. This makes it more relevant to the materials-and-corrosion scope than a generic materials record.

The current version was published 25 April 2025. The repository's older candidate note and catalog entry refer to version 1 (`10.17632/cfz68tkwfk.1`), so they do not identify the current record. The official version 3 page displays CC BY 4.0. It also describes the collection as derived from open literature and gives a source-study link for each entry. The page's rendered file section did not expose an asset manifest in this review. Mendeley API documentation marks the public file-list operation as OAuth-protected; no authenticated API access was used.

## Metadata-only candidate priority

| Rank | Dataset/version | Why it is useful | Current blocker |
|---|---|---|---|
| 1 | [Carbon-steel atmospheric corrosion with ERA5, v1](https://data.mendeley.com/datasets/ysr7wy3y7z/1), DOI `10.17632/ysr7wy3y7z.1` | Direct infrastructure-material corrosion-rate records and a provider-described independent-study subset; strongest candidate for later, grouped external comparison. | Official landing page provides no file-level name/UUID/size/checksum in the reviewed view; exposure rows are attributed to published sources and need row-level provenance/rights and partition review. |
| 2 | [AM-MPEA corrosion compilation, v3](https://data.mendeley.com/datasets/cfz68tkwfk/3), DOI `10.17632/cfz68tkwfk.3` | Electrochemical corrosion endpoints for additively manufactured alloy families, with composition and process context. | File manifest and provider checksum are unavailable in the reviewed view; per-source literature permissions and harmonization are unresolved. |

Both records currently remain metadata-only. The rank is a research-priority judgment based on fit to integrity evaluation; it does not rank dataset quality or establish scientific validation.

### Carbon-steel atmospheric corrosion database, version 1

The provider record was published 20 October 2026 and declares CC BY 4.0. Its metadata describes 617 programme records at 170 sites and 106 records from 16 independent studies, plus separate sensitivity and pooled-analysis material. It reports first-year corrosion rate and environmental/location covariates; the provider page describes an associated paper as submitted to *Corrosion Science*. These are provider metadata, not an independently reproduced audit of row counts, study independence, uncertainty or data quality.

The provider page says the exposure values originate from publications cited in the files and that those sources should be cited with the dataset. The rendered page reviewed here lists no asset filenames or checksums. No file was downloaded. Thus there is no immutable file pin, and the source-study rights, record-group overlap, calibration/holdout separation and definitions of the reported corrosion-rate fields remain unverified. It must not yet be treated as independent validation data or fed to a calibration importer.

## Pin and rights status

For the MPEA record, the verified public metadata is version number, DOI, publication date, dataset-level license declaration and subject scope. The page review did not yield a filename, provider file UUID, byte size, or provider checksum for the current version. For the atmospheric record, the verified metadata includes its version/date/DOI, CC BY 4.0 declaration and provider-stated record counts/scope, but likewise no file manifest or checksum. No file was downloaded, and no local raw file was opened or copied.

The provider's CC BY 4.0 declaration is recorded as a dataset-level license. Because the provider identifies individual source publications for entries, the license alone does not establish that each underlying literature observation can be republished as a row in another public dataset. This is a rights-review boundary inferred from the provider's source-link description; individual source permissions have not been audited here.

## Scientific-use boundary

The collection is a literature-derived compilation, not one harmonized experiment or a raw time-history dataset. Alloy categories, processing routes, electrolytes, reference electrodes, test protocols, endpoint definitions and measurement uncertainty may differ among source studies. Composition-derived features such as atomic fractions, mixing entropy or valence-electron concentration must be kept distinct from provider-measured quantities. Any reuse must preserve source-study lineage and missingness rather than treating all rows as independent, protocol-matched replicates.

Do not use this record as independent validation, calibration, a corrosion-rate time history, a universal alloy ranking, a failure probability, or a service-life/acceptance basis without a separate row-level condition, source-rights and study-independence review.

## Importer gate and next steps

An independently authored importer should remain deferred until the version 3 file inventory and provider checksums are available and a row-level rights policy is established. If those gates clear, the reader should preserve provider row identifiers, source-study references, original fields, missing-value states and provider units; calculated descriptors must be recorded as such and kept separate from measured endpoints. The raw workbook or CSV and observed row values should remain outside public examples and fixtures.

## Sources

- [Official Mendeley Data record, version 3](https://data.mendeley.com/datasets/cfz68tkwfk/3)
- [Official Mendeley Data atmospheric-corrosion record, version 1](https://data.mendeley.com/datasets/ysr7wy3y7z/1)
- [Official Mendeley Data API documentation](https://data.mendeley.com/api/docs/)
- [Official version comparison page](https://data.mendeley.com/datasets/compare/cfz68tkwfk)
