# Crevice slit wall-shear exposure

`corrosion.crevice_wall_shear_exposure` composes one computed `corrosion.planar_slit_transient_hydraulic_history` AssessmentResult. It calculates a local fully-developed planar-slit wall shear descriptor for every cell and interval without rebuilding or modifying the upstream hydraulic result.

For cell aperture `h`, transverse width `w`, dynamic viscosity `μ` and signed flow `Q(t)`, the relation is

\[
\tau_w(t)=\frac{6\mu Q(t)}{w h^2}.
\]

The upstream model uses constant pressure and aperture over an interval and returns the exact exponential flow path from its lumped inertance/resistance balance. The adapter therefore integrates signed wall-shear impulse directly from integrated signed volume. Absolute exposure uses the absolute flow integral, splitting at a reported internal flow reversal. For cells in series, `w` is shared and each `h` is the source interval's cell aperture.

## Provenance and input conditions

The request pins both the complete hydraulic AssessmentResult digest and the digest of its declared inputs. The source must be `computed`; ordered cell IDs, apertures, clock and interval records must align. Geometry, pressure and fluid-property provider IDs and record hashes must match the evidence on the source request. This linkage is provenance, not a digital signature or proof that a provider record is physically correct.

Caller reviews cover the wide-slit laminar wall relation, using a quasi-steady wall profile with a lumped transient flow trajectory, and descriptor-only interpretation. Signed shear distinguishes the flow direction. Absolute shear impulse is nonnegative and is accumulated per cell over the supplied intervals; it is not a damage law or a material threshold.

## Limits

This calculation does not solve Navier–Stokes, near-wall transient profile relaxation, entrance flow, roughness, non-Newtonian fluid behavior, local turbulence, wall-force distribution, erosion, corrosion or protective effects. It supplies no critical-shear threshold, material constants, acceptance criterion, life or risk probability. Use caller-owned downstream models for any such relation. `examples/crevice_wall_shear_exposure.py` is synthetic wiring only; no experimental or recommended values are provided.
