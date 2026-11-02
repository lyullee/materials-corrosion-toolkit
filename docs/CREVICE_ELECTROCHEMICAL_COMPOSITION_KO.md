# Crevice electrochemical composition history

`integration.crevice_electrochemical_composition_history` turns an upstream digest-pinned species-transfer ledger into a caller-volume, well-mixed composition bookkeeping history. The request carries one initial mole amount for every species touched by the flux ledger and a liquid-volume value at each exact transfer endpoint. The transfer request's whole assessment and ledger digest are checked before use; volume knots must cover the initial transfer time and each subsequent endpoint exactly.

At the first knot, the caller amounts are the initial state. At each subsequent knot, the adapter sums signed net species transfer across upstream reaction branches, adds those moles to the prior inventory, and divides by the corresponding caller-provided liquid volume. A negative resulting amount, an incomplete species inventory, mismatched clocks or a bad lineage digest is rejected.

The API requires explicit reviews that the inventory includes all relevant species, other sources and sinks are accounted for outside or within the caller's balance, the compartment is represented as one well-mixed liquid volume, transfer mapping is valid and computational use is authorized. These are caller assumptions, not automatic evidence of completeness.

This adapter does not recalculate electrochemical flux, solve mass action or activities, transport species between crevice cells, handle solids/precipitation, infer gas exchange or liquid outflow, calculate metal loss, or determine risk/acceptance. It supplies exact-knot concentration points to downstream models while retaining the transfer-history digest and area basis.

Python contract: `CreviceElectrochemicalCompositionHistory`; volume knots: `CreviceElectrolyteVolumeKnot`; initial amounts: `CreviceInitialSpeciesInventory`; registry ID: `integration.crevice_electrochemical_composition_history`. Numerical tests and experimental validation remain in the later validation workstream.

## Synthetic end-to-end wiring

`examples/crevice_electrochemical_composition.py` shows a digest-preserving sequential chain: two caller Nernst profiles feed a first mixed-potential history; its signed interval fluxes feed a caller-volume composition; each exact composition knot is solved by its own caller-supplied aqueous mass-action system; two caller redox definitions then turn the computed dimensionless activities into new Nernst profiles; those profiles feed a second mixed-potential history. The second chain preserves the same asset, location, physical-scope and clock identifiers and checks the complete upstream assessment digests. The Nernst handoff retains a `derived_activity_provider_evidence` record that identifies the mass-action assessment and its digest.

The sequence is operator-split: the second electrochemical calculation does not feed current or reaction transfer back into the composition/speciation states. All kinetic, equilibrium, standard-potential and volume parameters are caller-owned. Constants in the example are synthetic wiring values; the example has intentionally not been executed and provides no calibration or validation evidence.
