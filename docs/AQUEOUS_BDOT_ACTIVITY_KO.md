# Caller-parameterized aqueous B-dot activity/speciation

## Purpose

`chemistry.aqueous_bdot_self_consistent_speciation` couples the existing general aqueous mass-action solver to a caller-supplied extended Debye–Hückel B-dot activity model. It is intended as a reusable calculation component: callers provide their species, reactions, balances, coefficient records, unit basis, applicability limits, and evidence.

The implemented expression is

\[
\log_{10}\gamma_i^{(m)}=-\frac{A z_i^2\sqrt I}{1+B a_i\sqrt I}+b_i I,
\]

where \(I\) is in mol/kg water, \(a_i\) is in angstrom, \(B\) is supplied in the matching square-root ionic-strength/length basis, and \(b_i\) is supplied in kg/mol. The form follows the extended Debye–Hückel B-dot model documented by USGS PHREEQC. This project contains its own implementation and does not copy provider code or coefficient tables. [USGS PHREEQC model documentation](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-26.htm)

## Input and result

- `AqueousBdotIteration.system` is an `AqueousMassActionSystem` using the dimensionless 1 mol/L concentration standard state.
- The caller supplies temperature-specific `debye_huckel_A_at_temperature` and `debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom` and binds each to temperature, provider revision, configuration digest, record digest, and `Evidence`.
- `species_parameters` must follow the exact mass-action species order. Every row supplies ion size, B-dot coefficient, source ID, source-record ID, and the source-record SHA-256. Charged species require positive ion size. Neutral species may use zero ion size; their supplied B-dot term is applied as written and does not imply a general neutral-solute salting law.
- `water_mass_per_solution_volume_kg_L` maps molality-basis coefficients to the solver's molarity standard state as \(\gamma_c=\gamma_m/w\). Review this conversion for the actual solution basis.
- The outer iteration solves mass action, derives molal ionic strength and charge residual, updates activity coefficients with caller damping, and returns a result only when the declared fixed-point and charge tolerances are met. It preserves the input and parameter digests and per-iteration residual history.

The maximum supported ionic strength is an explicit caller parameter. A state above that ceiling returns `out_of_scope`; missing review or an invalid charge balance does not become a numerical equilibrium. Nonconvergence never promotes the last iterate as a computed result.

For a transport calculation, `build_bdot_transport_activity_callback()` consumes the same B-dot contract and returns molality-basis coefficients in the exact mass-action species order for each mouth/cell concentration column. It checks temperature, ionic-strength support and all applicability reviews, and exposes provider, configuration, record, species-parameter, and evidence digests as callback metadata. This callback changes the Nernst–Planck chemical-potential term through local `ln(gamma)` differences; it does not solve local mass action, enforce local charge balance, or infer a local parameter set. See `examples/aqueous_bdot_transport_activity.py` for synthetic wiring.

`build_bdot_transport_saturation_callback()` adds a digest-bound caller Ksp screen to the same activity provider for `solve_competitive_solid_kinetic_transport`. The screen must use the same ordered species, temperature, and molality standard state. Solid identities, solubility products, inventories, and kinetic rate laws remain separate caller inputs; this adapter does not select a stable phase or calculate a corrosion law.

For ordered operation points, `integration.aqueous_bdot_speciation_history` accepts one complete, evidence-bound B-dot/mass-action request at each time knot. Species order, reaction stoichiometry, constraint topology, and parameter-provider identity/revision remain fixed; temperature, equilibrium constants, balance targets, solvent basis, coefficients, and parameter record hashes can differ only through explicit knot requests. It computes every supplied knot independently, performs no interpolation or extrapolation, and retains the successful prefix plus the first failed result without reporting an incomplete history as computed. This is a sequence of equilibrium calculations, not a transient reaction-kinetics model.

## Scope limits

This API does not discover species or reactions, supply A/B/ion-size/B-dot values, infer the water-mass conversion, establish a parameter validity range, choose a liquid or solid phase, model gas partitioning, predict precipitation or scale, or calculate corrosion rate, life, risk, or code acceptance. Parameter support, temperature/solvent basis, complete species inventory, rights, and engineering applicability remain caller-reviewed. This model is not a general mixed-electrolyte Pitzer model.

## Source and reuse

The equation is independently implemented from the public method description cited above. No text, code, or numerical parameter table is copied from the reference. The synthetic example in `examples/model_inputs.json` uses fabricated placeholder constants solely to demonstrate the input contract; they are not recommended parameters or validation data.

## Validation status

The API is cataloged and schema-exportable. Tests, numerical verification, parameter-source validation, and release packaging have not been performed as part of the implementation-first workflow.
