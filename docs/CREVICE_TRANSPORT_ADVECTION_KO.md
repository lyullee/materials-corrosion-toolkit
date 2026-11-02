# Restricted-transport advection extension

`RestrictedTransportRequest` can include `axial_advection_velocity_m_s`, one nonnegative fixed velocity per cell face, or declare a time-varying Python callback through `solve_restricted_transport(..., axial_advection_velocity=callback)`. The callback returns a finite signed velocity at every face for the requested solver time. In both modes, the caller identifies the provider/configuration digest and reviews velocity mapping, volumetric-flow continuity with face areas, and the one-dimensional reduction basis. The callback's `configuration_sha256` attribute, when supplied, must match the declared digest.

## Numerical treatment

At each face, the solver adds a first-order donor-cell flux `v * c_upwind` to the existing diffusive or Scharfetter–Gummel flux. The mouth boundary concentration is the upwind state at the inlet. At internal and distal faces, the upstream cell concentration is used. Cross-sectional face areas continue through the existing reference-area flux ledger, so the advective term participates in the same conservative inventory balance as diffusion, reaction, and boundary exchange.

The fixed velocity profile must be nonnegative. A time-varying callback may return signed values only with separate flow-reversal review and an explicit distal inflow concentration; the distal state then follows the upwind direction. Signed mouth and tip exchange enters the existing conservative boundary ledgers, and every output-clock velocity profile is returned. The caller must ensure physically consistent volume flow and face-area choices; the model does not solve continuity or momentum equations. Compressibility, pressure-drop calculation, momentum balance, dispersion, and geometry evolution remain outside scope. The callback is not inferred from pressure or geometry.

```python
def signed_face_velocity(time_s):
    # Caller-owned provider: one signed velocity at each face, in m/s.
    return velocity_provider.evaluate(time_s)

signed_face_velocity.configuration_sha256 = reviewed_velocity_configuration_sha256
result = solve_restricted_transport(
    request, reaction,
    axial_advection_velocity=signed_face_velocity,
)
```

Set `time_varying_axial_advection_reviewed=True`, provide provider ID/digest, and set `axial_advection_and_flow_continuity_reviewed=True`. If the callback can return a negative distal-face velocity, also set `axial_flow_reversal_and_tip_boundary_reviewed=True` and supply `tip_advection_inflow_mol_m3` in the request's species order. The ODE solver samples the callback at its internal time steps, so callers should provide a deterministic profile suitable for the intended time scale.

This is a numerical transport component; it does not supply crevice chemistry, wall reaction kinetics, material susceptibility, corrosion rate, crack growth, life, acceptance, or failure probability. The caller remains responsible for the physical validity of velocity, geometry, species properties, and boundary conditions.
