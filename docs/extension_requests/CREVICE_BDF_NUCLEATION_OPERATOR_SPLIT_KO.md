# Downstream extension request: component BDF and seed-ledger split

The new `integration.crevice_bdf_nucleation_operator_split` orchestrator executes fixed-volume aqueous component BDF transport, then applies exact seed-threshold cell ledgers, then projects dissolved species back onto conserved component moles for the next interval. Preserve its operator order, cellwise absolute-saturation provenance, local/absolute affine clock maps, separate solid inventories, and atomic interval commits.

Before using the result for an integrity assessment, collect independent evidence for the saturation histories, kinetic parameters, liquid volumes, component mappings and property support. Compare transport and precipitation histories with rights-cleared measurements. Dynamic geometry, pressure-driven momentum, prescribed-source/Faradaic modes and within-interval feedback require separate extensions; do not silently add those effects to this API.
