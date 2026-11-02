# UCI MetroPT-3 process-history adapter

The reader streams the allowlisted `MetroPT3(AirCompressor).csv` member from the local UCI archive. The publisher record identifies compressor instrumentation data and licenses the dataset under CC BY 4.0. Cite the [UCI dataset record](https://archive.ics.uci.edu/dataset/791/metropt%2B3%2Bdataset) and attribute the original provider whenever redistributing permitted derived material.

## Input and lineage

- Expected archive name: `metropt+3+dataset.zip`; expected size: 218,381,995 bytes.
- Archive SHA-256: `aab991a970e58210de853bb8078ce0e63abb4d9412fdc5c79792dae3d8e1721a`.
- Member SHA-256: `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`.
- Both values are project-held-copy integrity pins. UCI did not supply these checksums, and they have not been matched against a provider-published checksum; they do not independently confirm byte identity with an online provider copy.
- The reader verifies the exact provider header order and emits rows lazily, retaining provider row number, provider index, timestamp text, raw signal strings and finite numeric values.
- The caller's nonempty CC BY attribution and an SHA-256 digest of the authorization declaration are carried in each row; the metadata-only archive audit also returns it, while never echoing the local archive path.
- The raw archive stays in `data/raw`, which is excluded from the source distribution. The adapter does not extract or copy the archive.

## Interpretation boundary

This is compressor process and predictive-maintenance context data. It is not corrosion growth evidence, a material degradation curve, an annual failure frequency or an acceptance criterion. Signal values retain provider-native units and reference semantics. Confirm time zone, pressure basis, channel calibration and data split before using a channel in a thermodynamic, mechanical or reliability model. Numeric parsing preserves values but does not assign engineering units or infer a fault label.

The adapter rejects a changed archive/member digest, unexpected header, malformed row, nonincreasing provider index, nonnumeric/nonfinite signal and an incomplete row sequence. It does not normalize timestamps, resample irregular intervals, impute missing values, classify failures or estimate remaining life.

`data.uci_metropt3_process_history` is registered as a metadata-only archive audit. Supply a local path and `MetroPT3ArchiveAuthorization`; the model checks the pinned archive/member without returning the local path or measurements. Use `iter_metropt3_rows()` when a downstream caller explicitly needs lazy access to source rows.
