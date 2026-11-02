# NIST CORR-DATA archive boundary and audit

## Scope

The NIST-hosted CORR-DATA compilation offers a broad index of reported corrosion observations across materials and environments. This repository currently provides a **local archive and structure audit only**. It does not convert the compilation into a corrosion predictor, choose a material, infer an alloy ranking, or treat a reported value as a design limit.

The Data.gov record describes more than 24,000 observations derived from over 250 source documents. Its accompanying caution is consistent with treating each row as a report of one specific test rather than a general material-performance guarantee. NIST's open-data page also distinguishes government-created works from Standard Reference Data and material supplied under outside agreements. Therefore, the portal's open-data reference does not by itself settle rights for every underlying source record.

## Local acquisition and aggregate evidence

The pinned archive is **354,591 bytes**, SHA-256 `013d9c5d7d4b9433d8a679c8b793d17f487463e0472b466d289450290d0da95c`. It contains one CSV and two provider metadata files. The CSV has 24,721 rows and 15 columns; all rows have the same width. The archive and row-level values are stored only under ignored `data/raw/` and are omitted from source distributions.

An aggregate audit found 239 non-empty reference keys and 25 rows without one. The two reported-rate fields are heterogeneous: one field contains 5,896 simple numeric tokens, 16 numeric ranges, and 18,442 other or qualitative tokens; the second contains 5,823 simple numeric tokens, 15 ranges, and 18,449 other or qualitative tokens. These counts demonstrate that the fields cannot be treated as one clean numeric series. Temperature, concentration, duration, localized-attack and condition fields also include missing or textual values.

The audit records archive/member hashes, schema digest, row count, field missingness and broad token classes. It deliberately does not write sample values, provider comments, citations, or transformed point records. The term “numeric scalar” denotes only a token shape; it is not a checked unit, valid measurement, independent specimen, or eligible calibration datum.

## Rights and use controls

The dataset catalog records the public NIST endpoint and its listed terms, alongside the unresolved possibility of rights attached to the underlying source documents. The archive is useful for local discovery and workflow development. Before a downstream project uses individual records for fitting or includes any values in a publication or package, it must establish for those rows the originating source, exact test and material conditions, units, specimen/source-group relationship, attribution duties and reuse permission. Any commercial advisory or analysis behavior from legacy NACE/NIST software is outside this implementation.

No provider prose, reference text, record values, precomputed decision rules, standard limits, or fitted correlations are copied into the package. The module implements only a separately authored archive/schema audit.

## Reproduce the local audit

```powershell
.venv\Scripts\python.exe scripts\fetch_data.py --ids nist-corr-data-corrosion-observations
.venv\Scripts\python.exe scripts\inspect_nist_corr_data.py
.venv\Scripts\python.exe -m pytest tests\test_nist_corr_data.py -q
```

The generated `validation/nist_corr_data_audit.json` is an aggregate structure report, not a legal clearance, source-row review, scientific qualification, or risk result. The small synthetic unit tests exercise parser boundaries without carrying the downloaded database.

## References

- [Data.gov NIST CORR-DATA record](https://catalog.data.gov/dataset/corr-data)
- [NIST copyright, fair-use and licensing statements](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications)
- [NACE-NIST corrosion data program overview](https://www.metallurgy.nist.gov/techactv1995/corrosdata.html)

## Current provider-page review

On 2026-10-29, the official Data.gov record still attributes CORR-DATA to NIST, lists NIST open-data terms, and reports the compilation as last updated in 1997. It describes over 24,000 records assembled from more than 250 source documents and says the observations characterize specific reported tests rather than guaranteeing general performance. NIST's licensing page distinguishes Standard Reference Data from other NIST-created works and notes that extramural or third-party rights can apply. These statements support the current conservative boundary: public portal access does not resolve reuse rights for every source-derived row. See the live [CORR-DATA catalog record](https://catalog.data.gov/dataset/corr-data) and [NIST rights guidance](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications).
