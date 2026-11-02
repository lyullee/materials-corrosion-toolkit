# Caller-defined gasket contact-pressure screen

`fabrication.gasket_contact_pressure_screen` evaluates margins between a computed spatial gasket contact-pressure field and caller-supplied minimum and optional maximum pressure bounds. The bounds are a screening window. The module does not claim that they are a standard, sealing criterion, acceptance limit or qualification result.

## Inputs and provenance

The upstream result must be a computed `AssessmentResult` from a registered static or history contact-field model. Its full canonical digest must be supplied, and asset, location and physical-scope identities must match. The upstream output must explicitly declare pressure units as Pa. A history result is sampled only at an exact output time; interpolation is not performed. The caller may screen all nodes or an exact named subset, and selected node IDs must exist uniquely.

The caller provides a physical scope, pressure window, criterion provider/revision/record identifiers, criterion SHA-256 and matching Evidence. The criterion digest covers those identifiers, the declared physical scope and both pressure bounds. Separate rights Evidence must identify the declared license. Review flags cover load/scope applicability, criterion applicability, pressure basis and units, rights and computational authorization.

## Calculation

For a contact pressure `p`, the lower margin is `p − p_min`. If an upper bound exists, its margin is `p_max − p`. The node controlling margin is the smaller applicable margin, and the reported overall controlling node is the node with the smallest such value. A negative margin means the result is outside the caller-declared screening window. A nonnegative margin means only that the supplied pressure value lies inside that window.

## Boundaries

The screen consumes the pressure values recorded by the upstream contact model and does not recompute force balance, local gasket stress, contact evolution or leakage. It does not infer pressure limits, sealing performance, code acceptance, failure probability, remaining life or material qualification. Applicability and allowable bounds must come from caller evidence and remain provider-dependent.
