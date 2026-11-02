# Coupled lateral-wall metal-loss exchange

`Co2CorrosionCampaign.wall_metal_loss_selection` invokes this conversion from the campaign and returns the result separately from the selected tip-reaction dissolution mapping.

`corrosion.coupled_wall_metal_loss` maps signed, solver-integrated wall species ledgers from a completed electrochemical transport result to total metal transfer and area-average recession. When `cellwise_recession_interpretation_reviewed` is enabled and the transport result includes matching per-cell ledgers and wall geometry, it also returns each cell's signed cell-average recession. It supports direct electrochemical results, campaign responses containing `electrochemical_result`, and registry `AssessmentResult` objects whose `values` hold either form.

## Required lineage and reviews

- Pass the complete coupled result and its canonical SHA-256 digest.
- Select a species explicitly present in the result's ordered species list and review the one-metal-atom-per-mole stoichiometric meaning.
- Provide the physical reference cross-section and require exact agreement with the solver result.
- The solver must have returned a positive `wall_area_over_reference_area`, derived from its cell volumes and caller-supplied wall-area density.
- Review that the signed wall flux means metal dissolution/redeposition and that the resulting area-average interpretation applies to the selected reactive wall.
- Supply caller-owned metal molar mass and density. No alloy property table is included.
- For cell-resolved output, provide reviewed wall flux and wall-area basis plus `cellwise_recession_interpretation_reviewed=true`. Cell areas are reconstructed from the fixed cell widths, wall-area density and (when present) cross sections; their sum must match the transport's total reactive wall area.

## Calculation

For each solver output time, total signed metal amount is the selected species' cumulative wall amount per reference area multiplied by the physical reference area. Mass is amount times caller molar mass; volume change is mass divided by caller density. Reactive wall area is the solver's wall/reference area ratio times the physical reference area. Signed area-average recession is volume change divided by reactive wall area. Positive wall uptake means loss; negative uptake means redeposition. This uses the solver-integrated signed species ledger directly (`wall_transfer_basis=solver_integrated_signed_species_ledger`) and applies no current-efficiency multiplier. Keep it separate from the tip current-based `DissolutionSelection`, which has its own declared efficiency and reaction-current interpretation.

## Limits

Cell output is a signed cell-average volume balance; it is not a within-cell spatial field or a prediction that the caller's cell segmentation resolves a pit or localized attack. The conversion does not infer species stoichiometry, predict transport or surface kinetics, qualify metal properties, or account for moving geometry, selective alloy dissolution, porosity, scale, capacity, acceptance, remaining life, or failure probability. It does not consume FTA or risk thresholds itself; downstream modules must preserve this interpretation and result digest.
