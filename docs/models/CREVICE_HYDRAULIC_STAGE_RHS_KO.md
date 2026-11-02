# Crevice hydraulic instantaneous stage balance

## Purpose

`corrosion.crevice_hydraulic_stage_rhs` evaluates one pressure-driven reduced slit stage. Schema v1 preserves the fixed-volume single-flow equation. Schema v2 accepts a digest-pinned per-cell liquid volume rate so stage geometry motion can alter face flow through incompressible continuity.

## Balance

With positive flow left-to-right, each cell obeys `dV_i/dt = Q_left,i - Q_right,i`. Given the inlet flow, the downstream face flow is obtained by subtracting the cumulative upstream volume rates. The cell mean flow is the mean of its two face rates. The lumped series momentum relation is `Δp = Σ(I_i dQ_in/dt + R_i Q_mean,i)`, where `R_i = 12 μ L_i/(w h_i³)` and `I_i = ρ L_i/(w h_i)`, multiplied by the declared correction factors. The returned derivative is solved from that scalar balance.

## Inputs and safeguards

Use schema v2 when any cell volume rate is nonzero. The geometry evidence digest then includes the ordered volume-rate vector together with the stage geometry. v1 rejects nonzero rates and keeps its prior digest layout. All values must remain finite, positive aperture and wide-slit/Reynolds bounds must hold, and caller review and licensed evidence remain required.

## Outputs

The result reports face and cell-mean flow, cell continuity residuals, cell pressure drops and series pressure closure residual, alongside the inlet-flow derivative and resistance/inertance diagnostics. The result is rejected if the pressure residual exceeds a 64-ULP floating-point roundoff allowance scaled to the pressure terms; the allowance and pass flag are returned. Reynolds support is checked in every cell and the maximum is returned. This makes the stage conservation equations inspectable by a parent integrator.

## Scope

The stage balance treats supplied volume rates as constant during that instantaneous evaluation; it does not represent the derivative of those rates. The API does not derive volume rate from solid precipitation, integrate flow, solve cell pressure nodes, or couple itself to the reactive component BDF. It is a same-stage primitive for a future coupled solver; using it alone does not close moving-geometry reactive transport or validate the reduced slit law physically.
