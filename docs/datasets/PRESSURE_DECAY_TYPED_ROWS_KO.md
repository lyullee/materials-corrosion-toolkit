# Typed pressure-decay sample rows

`iter_pressure_decay_leak_samples()` exposes the existing digest-pinned pressure/temperature workbook parser as typed records. The CC BY 4.0 dataset record is [Zenodo DOI 10.5281/zenodo.20582921](https://doi.org/10.5281/zenodo.20582921); cite the dataset and provide attribution when redistributing permitted derivatives.

The iterator first validates the local workbook's SHA-256, workbook shape, sheet, provider labels, and exact 31-point time grid. It then yields ten series of 31 records. Each record carries dataset/license identifiers, caller attribution, workbook SHA-256, sheet and series identities, gas label, capillary length, sample index, time, temperature, and pressure.

Caller authorization includes attribution and explicit computational/local-use declarations. Each emitted sample carries the authorization SHA-256 and `local_only=true`, so downstream modules can retain those terms with the row. No workbook is copied into the distribution. Temperature is converted from the provider-declared Celsius column to kelvin by the existing reader. The workbook describes pressure as relative/gauge, and the temperature's ambient/internal role remains unresolved.

These records are raw pressure/temperature observations. They are not leak-rate measurements. The dataset lacks a reference/blank state, vessel volume, absolute-pressure basis, and measurement uncertainty; this adapter does not infer leak rate, defect size, acceptance, or failure probability. Existing dataset limitations remain authoritative in `docs/CERTIFICATE_VACUUM_DISSIMILAR_WELD_KO.md`.

Example code is in `examples/pressure_decay_typed_rows_local.py` and is intentionally not executed as part of implementation.

`data.zenodo_pressure_decay_leak_sample_rows` is the registered metadata-only path. It requires a local path and `PressureDecayLeakReadAuthorization`, returns the pinned workbook audit without echoing the path, and does not calculate a leak rate. Use `iter_pressure_decay_leak_samples()` only when the downstream caller needs the typed sample records.
