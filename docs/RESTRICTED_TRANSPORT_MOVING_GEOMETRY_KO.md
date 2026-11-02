# Caller-supplied moving-area transport

## Scope

`RestrictedTransportRequest` can carry cell and face cross-section histories aligned with `output_times_s`. This extends the existing finite-volume transport calculation to a supplied geometry that changes during one ODE solve. The solver interpolates areas linearly between requested knots; it does not infer geometry from chemistry, wall flux, pressure or corrosion rate.

## Conservation form

For cell `i`, let `V_i(t) = A_i(t) Δx_i` denote cell volume divided by the fixed reference cross section. The concentration state follows the inventory equation

```text
d(C_i V_i)/dt = F_(i-1/2) A_(i-1/2)/A_ref - F_(i+1/2) A_(i+1/2)/A_ref
                + (r_i + s_i) V_i
```

where `F` is the signed face flux density, `r` is the caller reaction rate per solution volume, and `s` is the optional caller wall source per solution volume. In concentration form this adds the geometric term `-C_i (dV_i/dt)/V_i`. The signed mouth, distal, reaction and cellwise wall ledgers are integrated on the same solve clock. Output inventory uses the time-aligned cell volume at every reported time.

## Input contract

- Supply both `cell_cross_section_history_m2` and `face_cross_section_history_m2`, one row per `output_times_s` sample. Cell and face counts must match the transport grid.
- Keep `cell_cross_section_m2` and `face_cross_section_m2` equal to the first history row. `reference_cross_section_m2` remains a fixed normalization basis.
- Set `moving_geometry_interpolation_reviewed` and `moving_geometry_inventory_dilution_reviewed` only after reviewing the supplied history and conservation interpretation.
- Pin `moving_geometry_provider_id`, `moving_geometry_configuration_sha256`, and `moving_geometry_time_basis_id`; optionally bind a provider result digest.
- If wall flux is active, provide `wall_area_per_volume_history_m2_m3`, aligned to the same clock and cell order, and keep its static field equal to its first row.
- When advection is present, retain the existing flow-continuity review and use time-dependent velocity only when its provider basis and geometry alignment are reviewed. The solver does not repair an inconsistent velocity/area pair.

## Limits

The histories are prescribed exogenous inputs. Geometry does not feed back from chemistry, metal dissolution, scale deposition or transport. Piecewise-linear area changes create piecewise-constant `dV/dt` between knots; the implicit BDF solve is restarted at each supplied knot so a step cannot cross a derivative discontinuity. Knot locations are supplied by the caller and are not adaptively refined by this interface. The feature does not implement moving mesh, momentum/pressure solution, phase mechanics, automatic wall-area law, chemistry-derived kinetics, or corrosion qualification. Tests and physical validation remain pending.
