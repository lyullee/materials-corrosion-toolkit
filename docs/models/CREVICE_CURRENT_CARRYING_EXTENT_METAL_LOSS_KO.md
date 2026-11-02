# Current-carrying CREVICE extent to cellwise metal loss

## Purpose and data path

`integration.crevice_current_carrying_extent_to_metal_loss` consumes a computed, digest-pinned result from `integration.crevice_current_carrying_np_faradaic` together with the exact request that produced it. It converts each already integrated reaction extent in mol per cell into caller-mapped metal moles, mass, solid volume, and uniform cell-area recession. It does not integrate current or apply Faraday's law a second time.

The output exposes both an interval ledger and a cumulative per-cell metal-volume ledger. Every declared Faradaic reaction must be classified as either a caller-mapped metal-dissolution branch or an explicitly excluded non-dissolution branch. The branch-disposition record and every metal mapping are digest bound to caller-declared Evidence.

## Required caller inputs

For each mapped branch, supply:

- metal species identity and metal moles per reaction extent;
- molar mass in kg/mol and density in kg/m³;
- one positive reactive area in m² for each upstream transport cell, in exact upstream cell order;
- an Evidence-backed mapping digest and explicit review that the branch represents net dissolution, the extent has no unresolved negative reversal, and uniform cell-area recession is an acceptable average.

Supply every remaining reaction ID in `excluded_non_dissolution_reaction_ids`. The disposition digest is the canonical digest of the object with keys `mapped_dissolution_reaction_ids` and `excluded_non_dissolution_reaction_ids`, each containing the IDs in request order. Disposition Evidence uses source ID `caller_crevice_current_branch_disposition` and must carry that digest.

The model rejects an uncomputed or partial upstream result, request/result digest mismatch, changed result inputs, missing branch disposition, noncontiguous or nonmatching exact interval clocks, cell-order mismatch, nonfinite extent, and negative net extent for a mapped dissolution branch. An interval total cannot reveal a sign reversal inside that interval; such cases must remain unmapped until supported by a more detailed source history.

## Calculation

For each cell and mapped reaction, let `ξ` be the committed reaction extent in mol, `ν_M` the caller's mol metal per mol reaction extent, `M_M` the molar mass, `ρ_M` the density, and `A_cell` the reactive area. The adapter calculates:

```text
n_M = ξ ν_M
m_M = n_M M_M
V_M = m_M / ρ_M
Δh_cell = V_M / A_cell
```

It checks that the per-cell cumulative volumes sum to cumulative mass divided by density before allowing the geometry adapter to consume them.

## Geometry handoff

The resulting registered `AssessmentResult` can be passed to `integration.electrochemical_metal_loss_to_crevice_geometry`. For this result type, the geometry adapter uses the exact upstream cell IDs and cumulative per-cell metal volumes; caller-provided cell volume fractions must be omitted. The geometry request must give `geometry_cell_ids` in the same order as `cell_widths_m`. Geometry still requires the existing material/geometry review gates, support bounds, context match, and signed volume closure. The geometry operation remains sequential and does not feed the new aperture back into the already completed current/chemistry solve.

## Scope and limitations

- Caller supplies reaction-to-metal stoichiometry, metal identity, material properties, branch disposition and reactive areas; no mechanism or material property is inferred.
- Only nonnegative net extents are accepted for mapped dissolution branches. Cathodic branches can be explicitly excluded; redeposition is not modeled.
- Recession is an area average over each declared cell. Pits, roughness, undercutting, moving-boundary transport, subinterval current reversals and material qualification are outside this adapter.
- The output is a conditional engineering calculation with complete lineage, not a validated corrosion rate, remaining life, failure probability or acceptance result.

## Registration

The request and mapping contracts are exported as standalone JSON Schemas. The model is registered in the default `ModelRegistry`, source/capability catalogues and the `degradation.crevice_chemistry` partial-scope trace. No numerical test, example execution, package build or HPC calculation is implied by catalog generation.
