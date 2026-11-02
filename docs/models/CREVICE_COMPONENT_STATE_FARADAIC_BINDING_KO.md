# CREVICE current-carrying result to component-state BDF binding

`integration.crevice_component_state_faradaic_schedule_binding` is a typed sequential adapter between the existing spatial current-carrying/Faradaic calculation and the conserved-component BDF child. It produces a validated `CreviceComponentStateBDFRequest`; it does not run either solver.

## Inputs and identity checks

The binding request contains the clean component-state request, the exact current-carrying producer request/result pair, one caller-reviewed producer index for each component cell, and explicit gates for cell order/physical scope, endpoint reconstruction, source/reservoir mapping, derived current schedule and computational use. The adapter accepts only a fully computed producer result whose input digest matches the supplied producer request and whose requested intervals all committed.

The species IDs, order and charges, cell count/order, exact output times, and each initial conserved component inventory must match. Initial component moles are recomputed from the producer initial species concentrations, the component coefficient map and the component-state cell volume. A mismatch fails closed. The base request must be clean (no pre-existing source/current schedules) and set the finite maximum source-rate ceiling. The binding request carries the source/reservoir and derived-current review gates; only after those gates pass does the adapter set the matching flags on the generated BDF request.

## Schedule construction

The current-carrying producer returns exact-knot ionic face currents and signed branch current densities. For each branch and cell, the adapter converts current density to a molar extent rate using the producer's declared reactive area and electron number:

```text
r_extent = j_branch × A_reactive / (n_e F)
```

Branch stoichiometry, element reservoir changes and source Evidence are copied from the reviewed producer branch map. External component changes are derived from the component basis so each source closes the transported components; the corresponding aqueous charge is balanced against the external electronic reservoir. The ionic face history carries producer/result digests and an adapter derivation digest. The output request is revalidated by the component-state BDF contract, including per-knot charge continuity, zero external current, migration-current residual units and source-rate limits.

The adapter accepts producer modes whose schedule is representable by exact-knot endpoint currents and linear reconstruction. It rejects `bdf_stage_spatial_mixed_potential`, because an endpoint schedule cannot reproduce currents that were re-solved at internal BDF stages. Even in accepted modes, the resulting component-state run uses prescribed currents and extents; it does not recalculate mixed potential from its own evolving stage chemistry.

## API

- Model ID: `integration.crevice_component_state_faradaic_schedule_binding`
- Request: `CreviceCurrentCarryingComponentStateBinding`
- Cell mapping: `CreviceCurrentCarryingCellBinding`
- Evaluator: `evaluate_crevice_current_carrying_component_state_binding`
- Pure request builder: `bind_crevice_current_carrying_result_to_component_state_bdf`
- Result: the complete serialized component-state request and its digest; pass that request to `integration.crevice_component_state_bdf` separately.

The binding is a sequential handoff. It does not couple pressure-driven aperture, solid transfer, advection, changing volume or stage-re-solved kinetics. It is not an independent electrochemical law or physical validation.
