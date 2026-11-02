# Gasket contact pressure window event audit

`fabrication.gasket_contact_pressure_window_events` takes a computed viscoelastic flange contact history and evaluates one selected node's mean contact pressure against caller-declared minimum and optional maximum bounds. It retains the complete upstream result digest, registry input digest, RunContext, criterion Evidence, rights Evidence, selected node and source time knots.

The time history must contain at least two strictly increasing exact output knots. The requested node must occur once at every knot. This API linearly interpolates between adjacent computed samples only after the caller approves that interpolation and the criterion's applicability. It reports intervals below the minimum and, when a maximum is supplied, intervals above the maximum. An excursion is a descriptive window comparison; it is not a gasket leak, seal failure, code acceptance, causal conclusion or probability.

Supported upstream model IDs are `fabrication.flange_viscoelastic_contact_history` and `fabrication.flange_nonlinear_viscoelastic_contact_history`. A static field is rejected because it does not define a time history. The output scope is one node's mean contact pressure in Pa; it does not aggregate spatial area or interpolate between spatial nodes.

See `examples/gasket_contact_pressure_window_events.py` for a synthetic input template. The example has not been run. Tests, calculations, fits, packaging and HPC execution are deferred.
