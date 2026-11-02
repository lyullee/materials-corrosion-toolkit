# Crevice pressure-driven moving-volume hydraulic history

## Purpose

`corrosion.crevice_moving_volume_hydraulic_history` combines prescribed cell aperture motion, incompressible volume continuity, and a reduced pressure-driven series-slit momentum balance. It extends the preceding kinematic volume-continuity API by solving the pressure-driven inlet-flow degree of freedom.

## Governing balance

Within each exact interval, cell aperture changes linearly and pressure drop is held constant. Thus cell volume rate is constant. With positive flow left-to-right, the face rates satisfy

`dV_i/dt = Q_i - Q_(i+1)`.

The left inlet flow is the single integrated state. Continuity gives each downstream face flow as inlet flow minus cumulative upstream cell-volume rates. Each cell carries the reduced slit resistance `R_i = 12 μ L_i/(w_i h_i^3)` and lumped inertance `I_i = ρ L_i/(w_i h_i)`. The summed series momentum equation integrates the inlet-flow state. At the interval midpoint, cell pressure drops are reconstructed from cell inertance, midpoint cell flow, and resistance, and their sum must close to the caller pressure drop.

## Inputs and evidence

Supply a strictly increasing time grid, unique ordered cell IDs, per-cell lengths and widths, positive aperture at each knot, one signed pressure drop per interval, initial inlet flow, density and viscosity. Geometry and pressure records have separate digests pinned by licensed Evidence. Explicit reviews cover the geometry history, pressure sign/reference, incompressible Newtonian fluid, reduced slit law, and computational-use authorization. Work, solver effort, aspect ratio, Reynolds number, and pressure-closure limits are caller configurable.

## Results

The calculation returns knot inlet flow, interval mean flow on every face, interval mean cell flow, cell volume rates, cell pressure drops, integrated inlet volume, solver effort, support diagnostics and commit status. It also returns each cell's continuity residual `Q_left - Q_right - dV/dt` and the integrated boundary-volume residual `(Q_in - Q_out) Δt - ΔV_total`, both per interval, with maximum absolute values. Residuals are checked against the caller's absolute and relative flow tolerances before the interval is committed. The face-flow differences encode the prescribed liquid-volume changes; a pressure-closure, continuity, integrated-volume, or declared-support failure prevents commit.

These residuals are internal conservation checks for the reduced hydraulic calculation. They do not provide independent physical validation of the slit law, moving geometry, or fluid-property assumptions.

## Scope limitations

This is a one-dimensional reduced series model, not transient Navier–Stokes. Aperture history is prescribed and is not inferred from precipitation or mechanics. The API does not solve aqueous species advection/diffusion/migration, component or element transport, solid kinetics, moving cell topology, fluid compressibility, corrosion rate, integrity acceptance, or material qualification. Stage-coupled chemistry and deposit-volume feedback require a downstream solver.
