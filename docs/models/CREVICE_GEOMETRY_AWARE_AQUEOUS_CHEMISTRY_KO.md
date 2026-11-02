# Geometry-aware aqueous chemistry provider for crevice recession feedback

## Purpose and scope

`solve_crevice_transport_recession_feedback()` already repeats a transport solve for each guessed aperture path. This provider option lets a caller's **aqueous reaction-rate law** use that exact trial's linearly interpolated cell apertures, so each fixed-point iterate reevaluates chemistry against the same geometry guess used by transport.

This adds a callback contract and an optional solver argument; it does not provide a chemistry law, parameter set, activity model, or empirical calibration. It does not calculate precipitation, dissolution into a solid phase, deposit morphology, or phase selection. The reaction set is restricted to a caller-declared balanced aqueous species basis.

## API

- Provider module: `matintegrity.crevice_geometry_aware_chemistry`
- Typed provider contract: `CreviceGeometryAwareAqueousChemistryContract`
- Species record: `GeometryAwareAqueousSpecies`
- Reaction record: `GeometryAwareReactionDefinition`
- Runtime provider: `CreviceGeometryAwareAqueousChemistryProvider`
- Callback factory: `bind_linear_aperture_path(start_time_s, end_time_s, start_aperture_m, guessed_end_aperture_m)`
- Solver: `matintegrity.crevice_campaign.solve_crevice_transport_recession_feedback(..., geometry_aware_chemistry_provider=provider)`
- provider source ID: `caller_crevice_geometry_aware_aqueous_chemistry_provider`

When this option is used, omit the legacy `reaction` callable. The provider requires within-segment geometry fixed-point mode enabled, provider species order identical to the transport species order, and campaign time/geometry/concentration states inside its declared support. Other surface flux, activity and hydraulic callbacks keep their existing roles.

## Provider contract construction

Declare species in exact transport order with integer charge and elemental counts. Declare each reaction's net stoichiometric coefficient vector in that same order (reactants negative, products positive). All aqueous reaction vectors are checked for element and charge balance. Each caller law returns signed net reaction extent rates with shape `[reaction][cell]` and units `mol/(m3 s)`. The provider maps those extents to transported species source rates using the declared stoichiometry.

The serializable contract pins provider ID/revision, provider source SHA-256, species/reaction definitions, valid time, aperture and concentration ranges, and unit basis. Build a configuration mapping with `geometry_aware_chemistry_configuration_payload(...)`, then set `configuration_sha256 = canonical_digest(mapping)` before constructing the contract. Include `Evidence` with the same provider ID and source digest. The evaluator function itself is caller code; the digest and review gates are declarations that bind its identity and applicability, not an automatic hash or qualification of executable code.

Require caller reviews for geometry-path dependence, reaction order/units, element/charge balance, finite support, deterministic reevaluation, inventory closure and computational use. Determinism matters because the solver may call the law repeatedly at the same state and across rejected or uncommitted fixed-point trials.

## Iteration and closure behavior

For every inner fixed-point iteration, the provider captures the current segment's start aperture and guessed endpoint aperture. At each reaction callback time `t`, it linearly interpolates the per-cell aperture on that interval and calls the user evaluator with `(global_time_s, concentrations_mol_m3[species,cell], aperture_m[cell])`. Transport then uses the corresponding guessed cell/face area and wall-area-density path. The transport-integrated signed metal wall ledger predicts a new endpoint aperture; the existing relaxation, convergence tolerance, iteration budget and accepted-prefix behavior remain in force.

Each balanced stoichiometric reaction has zero net elemental and charge source by construction. The existing transport solver checks aqueous species inventory against its declared boundary, homogeneous-reaction and wall ledgers. A provider exception, invalid extent shape, nonfinite rate, or support violation marks that trial and segment uncommitted; the result retains the previously accepted segment prefix and the failed callback time/provider identity.

## Limits

- The time-varying geometry used by the callback is linear between segment endpoint aperture guesses. Chemistry is reevaluated at solver callback times, but the solver remains an operator-split transport/recession fixed point, not a monolithic simultaneous chemistry, momentum and moving-boundary method.
- Reaction stoichiometry is restricted to closed aqueous species. Solid phases and their inventories are not included in this provider; therefore precipitation/deposition-driven aperture change is unsupported here.
- The callback supplies rate law values; it must not mutate hidden state, read nondeterministic external state, or exceed declared bounds. The code can check returned rates and support but cannot prove callback determinism or scientific validity.
- Existing aperture feedback derives geometry from the selected signed metal wall ledger. This new provider does not alter that mapping.
- Transient momentum, automatically generated thermodynamics, activity coefficients, speciation, phase selection, solid deposition mechanics, calibrated wall laws, validation and qualification remain outside the API.
- Global species balance and declared reaction stoichiometry provide bookkeeping checks, not independent physical qualification or safety acceptance.

