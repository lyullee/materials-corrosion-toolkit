# Crevice electrochemistry handoff request for downstream modules

## Purpose

MatIntegrity now exposes a caller-configurable sequential chain from local crevice chemistry through redox/electrode quantities. This request describes how downstream repositories can consume it without silently changing the meaning of the quantities. It does not imply that any external repository has been modified.

## Current producer APIs

The current local contracts are:

1. `degradation.crevice_nernst_potential_history`: caller activities and standard-potential history → one half-cell potential at each declared knot.
2. `electrochemistry.nernst_driven_butler_volmer_history`: one half-cell potential and one caller-calibrated kinetic branch → signed partial current/species flux.
3. `electrochemistry.crevice_mixed_potential_history`: multiple digest-pinned half-cell profiles and kinetic branches → common zero-net-current potential and branch fluxes at aligned knots.
4. `integration.crevice_electrochemical_inventory_transfer`: reviewed piecewise-linear branch flux reconstruction → signed, inward and outward species mole-transfer ledger on a fixed reference-area basis.
5. `integration.crevice_electrochemical_composition_history`: caller initial inventories and exact liquid-volume knots → well-mixed mole/concentration bookkeeping history.
6. `integration.crevice_composition_to_aqueous_mass_action_history`: exact-knot compositions and complete caller network/parameter systems → single-phase mass-action calculations.
7. `integration.aqueous_mass_action_to_crevice_nernst_history`: solved dimensionless activities and caller E0/redox mapping → Nernst profile at the same knots.
8. `integration.crevice_current_carrying_np_faradaic`: caller variable-area activity-corrected Nernst–Planck transport, spatial ohmic/BV mixed-potential inputs, Faradaic species mappings and exact-knot chemistry → current/charge/element-closed interval ledger. The default `endpoint_trapezoid` is backward-compatible; reviewed opt-ins provide `bdf_stage_linear_current` or `bdf_stage_spatial_mixed_potential`. The spatial mode can also take one digest-bound `AqueousBdotIteration` per constant-temperature interval and recompute B-dot coefficients at each BDF stage for transport, homogeneous activities and Nernst/BV. That interval mode is coefficient-only; stage mass-action/solid equilibrium and equilibrium-consistent endpoint activity remain unresolved.

9. `integration.crevice_aqueous_component_ledger` is a standalone precursor for a future component-state integrator. It requires caller role labels for every mass-action constraint, exact charge-row matching, reaction-conserved component maps, and projects typed species amount/face/source ledgers to component balances. It does not alter the existing BDF state, solve chemistry, or implement stage speciation. A future intrastage equilibrium extension must carry conserved components as solver state (or define an explicitly reviewed approximation) so that equilibrium species concentrations cannot silently replace an inconsistent species-level transport state.
10. `chemistry.crevice_closed_batch_aqueous_equilibrium` is a closed single-liquid batch consumer of that component-role basis: it derives analytical totals from initial species moles and fixed volume, solves the caller's Davies mass-action system, and checks final inventory closure. It remains independent of spatial transport and the current BDF. Future coupling should evolve conserved-component moles in the transport state and invoke equilibrium on stage totals; solids, gas transfer, kinetic reactions and aperture feedback need separately balanced source/phase-transfer contracts.
11. `integration.crevice_component_state_bdf` implements that conserved-component state boundary for an isolated fixed-volume, closed, diffusion-only mesh. It rebuilds each cell's equilibrium constraints from BDF trial inventories, applies caller-diffusivity Nernst–Planck species flux with algebraic zero-current closure, and projects flux to components. It does not yet accept Faradaic sources, mixed-potential fields, solids, advection or changing aperture. The next extension must balance those sources in the same component basis, couple current and ionic migration consistently, and include solid/geometry inventory transfers before claiming the parent Crevice calculation.
12. The component-state BDF child accepts caller-evidenced exact-knot reaction-extent schedules with external reservoir element/component/charge ledgers. Nonzero aqueous charge extent is now allowed only with a second opt-in caller ionic face-current schedule on the same exact knots. The request requires `ncell+1` face currents, zero external boundary currents, and knotwise `I_right-I_left = FΣ(zνr)` closure. Stage Nernst–Planck migration is solved to reproduce the prescribed internal current and its residual is checked in amperes. This does not derive current from Butler–Volmer or mixed-potential kinetics and does not yet couple solids, advection, or changing aperture; preserve source identity, signs, cell mapping, and whole-system elemental/electronic closure.
13. `integration.crevice_component_state_faradaic_schedule_binding` composes a fully committed exact-knot current-carrying result into the component-state BDF source/current schedules. It requires matching species, cell order, time knots and initial conserved component inventories; derives signed extent rates from exact-knot branch current densities using the declared reactive area and electron number; and preserves upstream result and schedule digests. This is endpoint-schedule handoff only. It rejects the producer's stage-re-solved mixed-potential mode and does not close an instantaneous chemistry–BV–aperture feedback loop. A future monolithic mode must transfer the BDF-stage speciation into current/kinetic evaluation and balance solid, fluid and moving geometry state in the same RHS.

The original producer chain above remains sequential. In the new current-carrying API, BDF-stage Faradaic source integration is available; the spatial-mixed-potential mode also re-solves the quasi-steady ohmic/BV equations at each BDF RHS. Aqueous equilibrium and phase chemistry remain exact-knot calculations, and no double-layer storage, transient momentum or qualified wall law is included.

## Requested downstream record

Add a versioned optional `CreviceElectrochemicalHistoryRecord` (or equivalent) that stores, without dropping detail:

- asset, location, physical scope, clock/time basis and exact knot times/temperatures;
- original producer model IDs/versions, statuses, input digests, full-result digests and history digests;
- reaction IDs, reference-electrode identities, standard-potential provider/record digests, kinetic calibration digests, exposed areas and reference-area basis;
- current-carrying request schema version, Faradaic integration mode and method source ID, stage-review gates, spatial mixed-potential lineage, transport/mixed-potential evaluation budgets and per-interval closure diagnostics;
- per-knot mixed potential, net-current residual and each branch's signed current, anodic/cathodic partial currents and species flux;
- interval reconstruction method/review, signed/inward/outward integrated species transfer and the fixed area basis;
- caller initial species inventories, volume samples and resulting concentrations, clearly labeled as well-mixed bookkeeping;
- aqueous network and per-knot parameter-set digests, constraint IDs explicitly rebuilt from composition, fixed target constraints and solver outcomes;
- assumptions, caller review gates, Evidence and the explicit sequential/no-feedback boundary.

Provide JSON Schema and strict round-trip tests. Reject stale digests, changed species or reaction identities, mismatched time/temperature/reference/clock, and incomplete provider evidence. Preserve `needs_data` and `out_of_scope`; do not turn them into zero values or normal operation.

## Integrity and risk integration boundary

A receiving pipeline module may use an explicitly calibrated material-loss law to convert a metal-species transfer to wall recession only after it declares metal stoichiometry, exposed geometry, unit conversion and calibration support. A risk/FTA module must separately bind that qualified damage state to a failure mode, time horizon, exposure, failure criterion and probability model. The zero-current potential is not an event probability; signed partial current is not by itself a corrosion rate; species mole transfer is not by itself wall loss; concentration is not equilibrium speciation unless the downstream solver reports that result.

## Acceptance criteria for the receiving repository

- Pin and publish the accepted schema version; retain producer digests and repository/package identity.
- Validate all exact knot and reference identities before computing downstream results.
- Keep conversion laws, calibration data and probability semantics in the receiving model's own qualified contract.
- Add round-trip, mutation-rejection, missing-review and noncomputed-status tests in that repository.
- Document any lossy projection before reducing the full history to a scalar.

No external changes, data transfers or risk calculations are made by this request document.
