# Caller gasket preload-retention curve

`fabrication.gasket_relaxation_curve` evaluates a time-dependent preload-retention history supplied by the caller. It does not estimate relaxation from gasket composition, temperature, stress, or a standard table.

## Input contract

- Identify the gasket material condition, physical specimen, source group, provider revision, and test-condition digest.
- Pin the original observation/source digest and confirm computational-use authorization.
- Supply elapsed time in seconds and normalized retained preload fractions. The first knot must be `(0 s, 1)`; times must increase and fractions must not increase.
- Supply a caller-established initial preload in newtons and the requested evaluation times.
- Mark the test/normalization, transfer to the assessed joint, and use authorization as reviewed only after the responsible engineer has established those bases.

## Calculation

For each requested time, the implementation linearly interpolates the retained fraction between adjacent supplied knots and computes residual preload as `initial_preload * retained_fraction`. Duplicate evaluation times are permitted and retain their order. Any query outside the curve's time support returns `out_of_scope`; no extrapolation or clipping occurs.

## Interpretation limits

The curve represents one caller-identified test condition. It is not a fitted constitutive law, a general material property, or a transfer model across different geometry, temperature, media, seating, or load histories. It does not model recovery, unloading/reloading hysteresis, flange bending, contact-pressure distribution, leakage, sealing, structural capacity, acceptance, remaining life, or failure probability. The output is a preload history only.

The synthetic example in `examples/model_inputs.json` demonstrates the schema and has no engineering significance. Numerical and physical validation is deferred to the project validation campaign.

## Caller-calibrated viscoelastic strain history

`fabrication.gasket_prony_history` evaluates a generalized Maxwell response from an explicit caller-owned equilibrium modulus, positive Prony branch moduli and relaxation times, and initial branch stresses. The request binds these parameters to the gasket condition, physical specimen, temperature, source/configuration hashes, provider revision and computational-use authorization. Calibration applicability and the initial branch-state basis have separate review flags. A separately reviewed compression area and a nonnegative, time-ordered strain history are required.

Each interval is treated as a piecewise-linear compressive-strain ramp. For each branch, the state update is the closed-form solution of `dq/dt + q/tau = E*dε/dt` over that ramp. The equilibrium spring contributes `E_inf*ε`; compressive force is total compressive stress times the declared area. This permits caller-supplied hold, unload, reload and recovery histories without fitting or transferring a material law. Initial internal stresses are explicit and are not inferred from the first strain.

The calculator returns `out_of_scope` if the linear response becomes tensile because contact separation mechanics are not included. The model is small-strain, linear and isothermal for one declared condition. It does not predict flange bending, leakage, sealing, contact-pressure distributions, nonlinear gasket response, damage, coefficients, acceptance or life. The example in `examples/model_inputs.json` is synthetic and has no material calibration meaning; validation is deferred.
