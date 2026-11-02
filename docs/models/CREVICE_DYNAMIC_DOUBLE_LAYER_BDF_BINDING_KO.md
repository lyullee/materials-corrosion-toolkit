# Dynamic double-layer/Faradaic history to component BDF

## Purpose

`integration.crevice_dynamic_double_layer_to_component_bdf_binding` converts a completed, digest-verified `integration.crevice_dynamic_double_layer_faradaic_history` result into exact-knot component-state BDF source/current schedules. It recomputes the dynamic history request before binding. The component BDF calculation itself is left to the caller.

## Sign and charge mapping

The dynamic history defines current positive into the electrode. The BDF capacitive source is positive into aqueous solution, so the adapter uses `I_cap,aq = -I_cap,electrode`. Each polarization branch must map to one caller-evidenced aqueous reaction and electron number. For the selected positive extent direction, the signed source stoichiometry must satisfy `sign_per_extent * Σ(z_i ν_i) = -n_e`; otherwise the adapter rejects the mapping. Extent is calculated from the branch Faradaic current as `r = sign_per_extent * I_F/(n_e F)`.

At every knot, the adapter accumulates

`I_face,right - I_face,left = F * Σ(z_i ν_i r) + I_cap,aq`.

The current component-state BDF contract requires both external ionic-current faces to be zero. A non-closing derived face schedule is rejected before a BDF request is returned. Reaction component, element and charge-reservoir checks are repeated by `CreviceComponentStateBDFRequest` validation.

## Inputs and outputs

Inputs include an aqueous-only fixed-volume base BDF request, the typed dynamic-history request and computed result, a branch/reaction/electron map, an explicit caller rights basis for derived schedules, and review flags for reaction stoichiometry, current sign, boundaries, operator splitting and computational use. The adapter returns a digest-bound BDF request containing Faradaic extent, capacitive current and ionic face-current schedules. It never starts the BDF integration.

## Limits

This is an endpoint handoff with linearly reconstructed schedules, not a simultaneous potential/speciation solve. The BDF chemistry does not feed back into the potential history; there is no within-stage Butler–Volmer/Cdl state, spatial ohmic solve, moving geometry, hydraulic coupling or qualification. The derived schedule rights basis is caller supplied and must be valid for the source records and computational purpose.

## Python interface

Use `DynamicBranchReactionMap`, `CreviceDynamicDoubleLayerBDFBindingRequest`, and `bind_crevice_dynamic_double_layer_to_component_bdf` from `matintegrity.crevice_dynamic_double_layer_bdf_binding`.
