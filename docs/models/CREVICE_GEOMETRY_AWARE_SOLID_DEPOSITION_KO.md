# Geometry-aware solid reaction extents in crevice recession feedback

## Purpose

`CreviceGeometryAwareSolidDepositionProvider` adds a caller-provided endpoint reaction-extent operation to the existing `solve_crevice_transport_recession_feedback()` fixed-point loop. For every trial aperture endpoint, it evaluates the caller's specified balanced aqueous-to-solid reaction extent, checks aqueous and solid inventories, converts the net solid volume change into a mean aperture change, and includes that change with wall-metal recession in the endpoint residual.

The callback supplies all reaction extents. This API does not infer solubility products, rate constants, phase selection, or precipitation/dissolution kinetics.

## API

- Module: `matintegrity.crevice_geometry_aware_solid_deposition`
- Contract: `CreviceGeometryAwareSolidDepositionContract`
- Records: `SolidCoupledSpecies`, `SolidPhaseInventoryBasis`, `CallerSolidReactionExtent`
- Runtime provider: `CreviceGeometryAwareSolidDepositionProvider`
- Configuration mapper: `solid_deposition_configuration_payload()`
- Integrated function: `matintegrity.crevice_campaign.solve_crevice_transport_recession_feedback(..., geometry_aware_solid_deposition_provider=provider)`
- source ID: `caller_crevice_geometry_aware_solid_deposition_extent`

The option requires within-segment geometry fixed-point mode. If it is the only reaction provider, the transport solve uses an explicit zero homogeneous source and applies the solid extents at the segment endpoint. It can also run alongside a separate geometry-aware aqueous callback, provided reaction IDs do not overlap. A legacy reaction callback may be combined only when it exposes a nonoverlapping `reaction_ids` tuple; the zero homogeneous-source callback is selected automatically when the endpoint extent provider is the only chemistry source.

## Caller contract

Declare aqueous species in exact transport order, with integer charge and elemental composition. Declare solid phases with elemental composition, neutral charge, initial cell inventory (`mol/m2` of the transport reference area), caller molar volume (`m3/mol`), and SHA-256 source records for both the initial inventory and molar volume. Include matching `Evidence` entries for the provider, each phase molar-volume record, and each phase initial-inventory record (`{phase_id}:initial_inventory`).

Each reaction defines aqueous and solid stoichiometric vectors in the declared phase orders. Products use positive coefficients and reactants negative coefficients. The contract checks charge and every declared element across aqueous and solid species. Extents are signed net reaction amounts in `mol/m3 solution` for one endpoint operator-split event; they are not rates. The callback receives `(start_time_s, end_time_s, endpoint_concentration[species,cell], start_aperture[cell], guessed_end_aperture[cell], current_solid_inventory[phase][cell])` and returns a finite `[reaction,cell]` extent matrix.

Input support bounds include time, aperture, per-aqueous-species concentration, and absolute extent per reaction. Callback results are evaluated twice at identical inputs and must match exactly. `configuration_sha256` must be the canonical digest of `solid_deposition_configuration_payload(...)`; this binds the provider/revision/source, reaction basis, support, initial solid inventory, molar volumes, reference area, face count and coverage.

## Interval calculation and geometry

For an endpoint extent `xi[r,i]`, aqueous concentration change in cell `i` is `sum_r(nu_aq[s,r] * xi[r,i])`. The solid amount change per reference area is `sum_r(nu_solid[p,r] * xi[r,i]) * Vcell_end/Aref`, where `Vcell_end/Aref` comes from the guessed endpoint slit cross section and cell width. The result is added to the current phase inventory. Dissolution that would make any phase inventory negative fails closed.

The phase inventory change times its caller molar volume gives signed solid volume change per reference area. Equivalent mean aperture loss is that volume multiplied by `Aref` and divided by cell plan area. The covered-patch mapping also divides by the caller coverage fraction and checks that the local gap stays nonnegative. Existing signed wall-metal recession and this signed deposition change jointly predict the endpoint aperture. Only a converged endpoint is committed.

For each trial, output records provider, contract, source, configuration, transport and endpoint-extent digests. A failed callback, negative aqueous/solid inventory, element/charge closure failure, unsupported gap, or failed fixed-point iteration leaves the current segment uncommitted and preserves the previously accepted prefix. Extent callback evaluations are bounded to 10 million reaction-cell values across the declared segment and fixed-point budgets; adaptive bisection is checked against that same limit. The aqueous reaction source is added to the campaign species inventory ledger; the campaign also closes each phase inventory against accumulated reaction extents.

## Boundaries

- This is an endpoint operator split: transport first, caller solid reaction extent second, then geometry update. It does not evolve solid phases continuously inside a transport solve or imply fully simultaneous chemistry/geometry physics.
- Solid inventories are per reference area. Initial solid inventory is an inventory constraint; any baseline deposit already represented by the initial aperture is not subtracted again. Only the computed interval inventory change updates the gap.
- Solid phases are neutral. Reactions must balance every declared element and charge across aqueous and solid species.
- Solid deposit is represented by compact volume, caller coverage, and the selected face count. Porosity, morphology, adhesion, nucleation and cell-internal spatial distribution are not resolved.
- If adaptive aperture bisection splits an interval, the caller extent callback is called again for each smaller endpoint interval. It must use the supplied interval start/end and current inventory. The coarse interval's extent is not automatically partitioned or preserved.
- A callback must remain deterministic and within its declared support. Source digests and review gates do not independently establish its physical validity.
- The existing recession conversion still depends on the caller-selected metal species, material density/molar mass, wall mapping and wall-flux applicability.



