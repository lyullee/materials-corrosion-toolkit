# Downstream extension request: crevice hydraulics and double-layer charge

## Available contracts

- `corrosion.crevice_hydraulic_stage_rhs` evaluates the instantaneous lumped slit momentum derivative from an exact caller stage record.
- `integration.crevice_double_layer_to_component_bdf_binding` verifies that caller-supplied capacitive-current knots conserve the opposite change in caller-computed electrode stored charge before producing a component-state BDF request.

These APIs are composable calculation steps. They do not solve the joint time-dependent pressure, moving-volume, species-transport, electrode-potential and Faradaic problem.

## Requested research and implementation

Refactor the component-state BDF chemistry/geometry evaluation into a reusable stage callback, then implement a bounded coupled state that integrates signed flow and conserved component inventories while updating resistance/inertance from stage apertures. Include a physically justified liquid-volume/displaced-flow balance, cell/face pressure or its reviewed lumped reduction, and an explicit boundary exchange ledger. Couple electrode potential and capacitive charge to Faradaic branch kinetics only through an independently specified constitutive model and charge-conserving state equation.

Before use, validate the solver against analytic slit transients and synthetic conservative cases, then compare against independent rights-cleared pressure/flow, aperture and electrochemical measurements. Preserve provider revisions, clock/grid, parameter fit digests, uncertainty, and group-separated holdout records. Keep automatic material qualification and universal transfer claims outside this extension.
