# Caller-defined aqueous mass-action temperature history

`integration.aqueous_mass_action_vant_hoff_history` updates caller-supplied equilibrium constants from a reference temperature and solves the existing single-liquid-phase mass-action model independently at each declared time/temperature knot. It is a temperature-sensitivity composition, not a kinetic trajectory.

## Calculation

For each reaction, the input `AqueousMassActionSystem` supplies the dimensionless `log10(K)` at `reference_temperature_K`. The reaction thermochemistry record supplies the reference standard reaction enthalpy and may supply a reference reaction heat-capacity change, using that same standard state. The constant-enthalpy form is

```text
log10(K(T)) = log10(K(Tref))
             + ΔHref / (R ln(10)) × (1/Tref − 1/T)
```

When `delta_cp_reference_J_mol_K` is supplied, it is treated as constant over the caller's validity interval and the integrated correction is

```text
ln(K(T)/K(Tref)) = ΔHref/R × (1/Tref − 1/T)
                  + ΔCp_ref/R × (ln(T/Tref) + Tref/T − 1)
```

For a linearly varying heat-capacity difference, also supply `delta_cp_slope_J_mol_K2` and retain the reference coefficient explicitly:

```text
ΔCp(T) = ΔCp_ref + slope × (T − Tref)
ΔlnK_slope = slope/(2R) × [(T − Tref) − 2 Tref ln(T/Tref) + Tref²(1/Tref − 1/T)]
```

This option requires `temperature_dependent_reaction_heat_capacity_reviewed`; a slope without an explicit reference ΔCp is rejected. It remains a caller-selected heat-capacity model over the stated source support.

The API then calls the existing mass-action solver with that reaction-constant set and knot temperature. The constant-enthalpy relation follows the [IDAES reaction equilibrium documentation](https://idaes-pse.readthedocs.io/en/2.13.0/explanations/components/property_package/general_reactions/equil_constant.html); the heat-capacity temperature correction follows the thermodynamic treatment in the [OECD NEA thermochemical database documentation](https://www.oecd-nea.org/upload/docs/application/pdf/2020-09/tdb4new_2020-09-02_11-54-56_843.pdf). The standard equilibrium-constant basis is described in the [IUPAC Gold Book](https://goldbook.iupac.org/terms/view/S05915). `R` uses the [NIST 2022 CODATA molar gas constant](https://physics.nist.gov/cgi-bin/cuu/Value?r%7Csearch_for=R).

## Inputs and review gates

- `mass_action_system_at_reference` is the complete existing chemistry network, including species, reactions, balances, evidence and reference-temperature `log10(K)` values.
- `reaction_enthalpies` must cover the exact reaction ID set. Every record carries a source-record ID, Evidence, and caller-declared validity interval. `delta_cp_reference_J_mol_K` is optional; constant-ΔCp rows require `constant_reaction_heat_capacity_change_reviewed`. An optional `delta_cp_slope_J_mol_K2` requires the reference ΔCp and its own `temperature_dependent_reaction_heat_capacity_reviewed` gate. Measured/open rows require a file SHA-256; open-dataset rows also require a license identifier.
- `reference_temperature_K` must equal the base system's temperature. Every target knot must be inside every relevant thermochemical record's support; this API does not extrapolate.
- `reaction_enthalpy_standard_state` must identify the same declared standard state used for the mass-action constants.
- `reaction_thermochemistry_temperature_model_reviewed`, `temperature_support_and_time_mapping_reviewed`, and `computational_use_authorized` must all be true before any knot is solved.
- For temperature-varying activity coefficients, supply `activity_coefficients_by_knot` with one Evidence-linked row per time/temperature knot. Each row follows the exact species order in the reference system and carries provider ID/revision/configuration SHA-256 and a source-record ID. All knots must retain the same provider configuration. `activity_coefficient_temperature_history_reviewed` is required. Measured/open rows require a file SHA-256; open-dataset rows also require a license identifier.
- If `activity_coefficients_by_knot` is omitted, the reference system's coefficients remain fixed across all temperatures and `fixed_activity_coefficients_temperature_applicability_reviewed` must be true.
- `maximum_absolute_log10_equilibrium_constant` is a caller-adjustable numeric budget. Values beyond it return `out_of_scope`; they are not clipped.

## Interpretation limits

Reaction enthalpy is treated as constant when heat-capacity inputs are omitted. Otherwise ΔCp is constant or linear in temperature according to the caller's explicit inputs over declared support. Higher-order heat-capacity functions, activity-coefficient inference, speciation model transfer, phase selection/precipitation, gas-liquid equilibrium, reaction kinetics, scale growth and corrosion rate are not calculated. Per-knot activity coefficients are direct caller inputs, not values estimated by this module. If those inputs are omitted, reference coefficients are reused only after the caller approves their temperature applicability. Time labels organize independently solved equilibrium states; they do not imply that the solution follows an equilibrium path or resolves transient chemistry.

The catalogued TUDOdata aqueous-electrolyte collection reports mean ionic coefficients and has unresolved underlying-record provenance; it is not an input source for the species-specific coefficient vector without separately reviewed source rights and a valid thermodynamic conversion. See [data acquisition and reuse notes](DATA_KO.md#수용액-활동도-계수의-사용-경계).

The bundled two-knot input is synthetic and exists only to demonstrate API wiring. It does not contain measured thermochemical values or a validated corrosion chemistry model. No source prose, data tables or implementation code is copied into the package.
