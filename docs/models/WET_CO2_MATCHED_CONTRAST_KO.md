# Wet-CO₂ simulation matched-contrast API

`degradation.wet_co2_simulation_matched_contrast` compares two explicitly selected rows from the open NORSOK M-506 simulation-grid adapter. Every input other than one declared factor must match exactly. The API reports the provider model's finite-difference corrosion-rate response, and where defined a ratio and log-log secant elasticity.

## Python use

Load and retain the source rows through the existing `matintegrity.wet_co2_data.read_wet_co2_simulation_grid` provenance-aware reader. Select a pair whose nonvaried inputs match exactly, then construct `WetCo2MatchedContrastRequest` with the lower and upper values, the varied field name, and caller reviews for pairing and simulation-output scope. Pass it to `wet_co2_matched_contrast`, or use the registered model ID through the registry.

The result is a finite contrast between two provider-generated model outputs. It is not an experimentally observed sensitivity, causal estimate, independent sample, physical corrosion law, predictive uncertainty, failure probability, acceptance determination, or equipment qualification. No interpolation, parameter fitting, extrapolation, redistribution of workbook rows, or conversion to wall loss/lifetime is performed. If model inputs do not exactly match apart from the selected factor, request validation rejects the pair.

The source dataset is attributed in the existing wet-CO₂ data guide. This module contains no copied source table; callers supply source rows with their preserved row identity, license and archive digest.
