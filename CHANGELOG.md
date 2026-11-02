# Changelog

## 0.1.0a1 — 2026-11-03

First public research-alpha snapshot of the Materials Corrosion Toolkit. The installable distribution is `materials-corrosion-toolkit`; the existing `matintegrity` import path and model IDs are retained.

- Publish a registry of 757 APIs spanning material behavior, corrosion, electrochemistry, transport, mechanics, fatigue/fracture/creep, fabrication/welding, inspection, data contracts and integration.
- Expose purposes, inputs, declared outputs, assumptions, complete input schemas and implementation links through a visible README directory and one page per API.
- Preserve authored mathematical tests, fixed 63-group/232-API audit inventories, physical consistency checks and machine-readable evidence with explicit limitations.
- Include the accumulated development record and procedures for resuming research, data acquisition, validation and cross-project integration.
- Fix previously unexecuted provider arguments, dynamic hydraulic closure variables, temperature-slice and phase-index references, and per-interval condensate density handling.
- Restore core installation without SciPy by importing the optional hydraulic fitting solver only when used.
- Exclude machine-local receipts and restricted assets, inspect decoded JSON paths, and include required synthetic test JSON in source distributions.

Known full static-quality findings, incomplete main JSON example membership and two external-evidence-dependent normal execution cases remain documented. This release does not claim full experimental qualification, field accuracy, standard compliance or legal clearance.
