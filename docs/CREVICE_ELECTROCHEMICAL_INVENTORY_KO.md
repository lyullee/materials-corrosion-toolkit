# Crevice electrochemical inventory transfer

`integration.crevice_electrochemical_inventory_transfer` converts the branch species-flux history from `electrochemistry.crevice_mixed_potential_history` into a signed mole-transfer ledger on the same reference-area basis. It accepts only a computed upstream assessment whose input digest, complete result digest and history digest agree. The caller must explicitly approve a piecewise-linear flux reconstruction between the supplied time knots, constant reference area and the inherited inward-species sign convention.

For each reaction and species, the signed flux is integrated exactly over each linear segment. Positive inward and negative outward contributions are integrated separately, including an exact zero-crossing split when endpoint signs differ. Results are reported per reaction and species, by interval and cumulatively, in moles over the upstream reference area. There is no time extrapolation, concentration conversion, bulk-volume assumption, electrochemical recalculation, chemistry solve, phase selection, metal-loss conversion or acceptance decision.

A receiving transport or corrosion module must supply its own volume/geometry, aqueous balance, species consumption, solids, material-loss stoichiometry and calibration. The current ledger is a connector quantity, not a standalone corrosion prediction. The linear between-knot hypothesis is a numerical reconstruction requiring caller review, not evidence that the actual kinetics follow a linear path.

Python callers use `CreviceElectrochemicalInventoryIntegration` and registry model ID `integration.crevice_electrochemical_inventory_transfer`. The public schema preserves the upstream result digest and exact interval transfer history. Numerical tests and physical validation remain part of the later validation batch.

## Synthetic end-to-end wiring

`examples/crevice_electrochemical_composition.py` shows the digest-preserving sequence from two caller Nernst profiles through mixed potential, interval species transfer and caller-volume composition. Its constants are synthetic wiring values and the example has intentionally not been executed; it is not calibration or validation evidence.
