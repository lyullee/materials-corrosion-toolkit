# Crevice moving-volume liquid continuity

## Purpose

`integration.crevice_moving_volume_liquid_continuity` reconstructs conservative interval-mean liquid flow through a fixed ordered slit mesh when caller-provided aperture histories change cell volumes. The operator is intended as a reusable handoff primitive for later hydraulic and reactive-transport coupling.

## Balance and sign convention

Positive face flow points from the left reservoir to the right reservoir. For cell `i`,

`dV_i/dt = Q_i - Q_(i+1)`.

The cell volume is `length_i * width * aperture_i`. Aperture is linearly interpolated between consecutive input knots, so its volume rate is constant within each interval. Starting from the interval-mean left boundary flow, the API recursively determines each downstream face flow. The implied right boundary flow must match the independently supplied right-boundary schedule within the declared absolute and relative tolerances.

## Input contract

The caller supplies ordered unique cell IDs, lengths, common transverse width, exact increasing time knots, positive aperture for every cell and knot, and signed left/right boundary flows at every knot. Geometry and boundary histories have separate SHA-256 digests; Evidence records must pin each digest and include a license or permission identifier. The caller also confirms fixed mesh, incompressible-liquid, geometry, boundary, and sign assumptions and computational-use authorization.

## Output

The result returns cell liquid volumes at knots, interval volume rates, all `ncell + 1` interval-mean face flows, cell residuals, right-boundary mismatch, input digests, commit status, and an explicit non-qualification flag. An inconsistent right boundary returns `needs_data` and `committed=false`.

## Scope boundary

This is a kinematic continuity operator. It does not calculate pressure, transient momentum, hydraulic constitutive parameters, species advection/diffusion/migration, phase precipitation, aperture mechanics, changing cell topology, liquid compressibility, corrosion rate, integrity acceptance, or qualification. The result may support a later caller-owned coupled solver but must not be treated as that solver.

## Extension path

The next coupled implementation should place volume and species inventories in one BDF state, add boundary-displaced liquid/component ledgers, evaluate pressure-driven face flow at the same trial state, and feed phase occupancy back into cell volume. Independent conservation and limiting-case checks are still required before scientific use.
