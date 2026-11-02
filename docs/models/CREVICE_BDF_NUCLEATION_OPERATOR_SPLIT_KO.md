# Component-state BDF ↔ cellwise nucleation operator split

## Scope and order

`integration.crevice_bdf_nucleation_operator_split` connects the fixed-volume aqueous-only component BDF to per-cell, conservative nucleation/growth ledgers. For each adjacent exact absolute interval, it performs:

1. Aqueous component BDF transport across the fixed cell mesh.
2. One closed-batch nucleation/growth ledger per cell, using that cell's caller saturation record for the same absolute interval.
3. Projection of post-kinetic aqueous species through the BDF cell's explicit component coefficients back to molar component inventories.
4. Carry of those aqueous component moles and the separate solid phase inventories into the next interval.

The order is an operator split. The kinetic rate does not enter the BDF RHS or modify transport during its completed interval. It only changes the state used by the next interval.

## Contract and exact clock lineage

The outer, BDF, and cell kinetic assessment identities must be linked; the BDF assessment ID equals the orchestration ID, and each cell kinetic ID is a unique child ID beginning with `<assessment_id>:`. The BDF and kinetic records must have the exact same ordered cell IDs, species order/formulas/charges, fixed solution volumes, clock knots, phase set, provider revisions, and caller laws. Cell length/area-derived volumes, BDF center distances and interior face areas must describe the same fixed mesh. For each shared face, its input area must match the harmonic interpolation of the neighboring cell cross-sections; center spacing must equal the adjacent half-cell lengths. The component basis must reconstruct every declared element. Kinetic saturation values may vary by cell; each remains attached to its original absolute-time digest and Evidence. Initial cell aqueous species must reconstruct the BDF initial component inventory within its declared tolerance and be charge neutral.

The BDF subrequest uses local time `[0, Δt]`, and the existing batch kinetic contract requires the full source history to start at zero. For each source interval `[t0,t1]`, the adapter retains the original `record_sha256`, creates a translated local record `[0,t1−t0]` with a new digest and derived Evidence, and records the affine map `t_absolute = t_local + t0`. This translation is exact because the interval laws are time independent and saturation is constant within each declared interval. The original source digest and translated digest are both returned. Absolute event times are reconstructed from the map. At every BDF start knot, the local equilibrium reconstruction can change individual species concentrations while preserving the conserved component totals; the pre-BDF species, reconstructed species, and resulting amount jump are reported separately.

## Ledgers and atomic commit

Each BDF segment retains its per-cell conserved-component and element ledgers. After the local kinetic ledgers succeed, aqueous component moles are computed from post-kinetic species concentration, the cell fixed liquid volume and the declared component species coefficients. Solid component contributions are independently computed from each phase's precipitation stoichiometry and carried solid amount. The aqueous-plus-solid component balance must close before the interval can commit. Species/solid amounts, global element amounts and aqueous charge are also returned before BDF, after BDF, and after kinetics; global BDF elemental closure and post-kinetic element/charge closure are gates. Element and charge residuals from the per-cell conservative ledger are retained alongside those global checks. If either the BDF solve, any cell ledger, a work budget or a closure check fails, the current interval is excluded from committed state history; earlier intervals remain identifiable as a committed prefix.

## Rejected modes

The request rejects instantaneous solid-equilibrium BDF, dynamic geometry, hydraulic advection, Faradaic stage coupling, prescribed ionic or capacitive current, external electrochemical sources and other source schedules. These modes do not have a validated transfer rule through this split. Face geometry, diffusivity, liquid volume and wall-area assumptions stay fixed. Cells do not exchange aqueous material during the kinetic stage.

## Limits

- This is sequential transport followed by local kinetics, not simultaneous reactive transport.
- No moving aperture, recession, porosity, wall area or kinetic morphology update occurs.
- Phase/saturation/rate-law records are caller supplied; no automatic reaction or phase discovery is performed.
- BDF, equilibrium, ledger, output-record and nested-work budgets are aggregated over intervals.
- The result is a research calculation, not physical validation, qualified corrosion rate, life, probability or engineering acceptance.

## Python API

- Request: `CreviceBDFNucleationOperatorSplitRequest`
- Evaluator: `solve_crevice_bdf_nucleation_operator_split`
- Model ID: `integration.crevice_bdf_nucleation_operator_split`
- Cell-order digest helper: `compute_cell_order_sha256(assessment_id, physical_scope_id, clock_id, cells)` from `crevice_cellwise_nucleation_kinetic_history`.

Each nested kinetic history supplies the complete absolute BDF interval schedule and a per-cell assessment ID derived from the outer assessment, for example `<assessment_id>:cell:<cell_id>`. The helper returns the digest to attach to `kinetic_cell_order_evidence` before constructing the orchestration request.
