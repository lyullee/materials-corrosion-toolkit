# Projected scalar cycle counting for tensor histories

`fatigue.critical_plane_projected_rainflow` applies the installed scalar `rainflow` package to explicit projections of an ordered stress/strain tensor record. The record may be open or irregular and need not be a single closed representative cycle. The caller must review sample order and record boundaries.

## Projection choices

For every supplied plane frame, the caller selects one or more distinct channels:

- signed normal stress or normal strain;
- signed shear stress or engineering shear strain along the supplied in-plane direction;
- nonnegative in-plane shear stress or engineering shear strain vector magnitude.

Input strain shear components are declared as tensor shear or engineering shear. Engineering inputs are converted to tensor shear before projection, and the output engineering-shear signal applies the factor of two. The orthogonal in-plane direction is the cross product of the supplied normal and direction. Normal and directional shear channels retain sign. Vector-magnitude channels discard direction and sign changes; this can alter counted reversals and is explicitly identified in the result.

## Returned cycles

Each plane and projection returns its own range, mean, count, start/end sample indexes and caller sample IDs. If times are supplied, endpoint times are also included. Residual excursions returned by the scalar library remain half cycles. Candidate-plane, projection-channel and sample order are preserved, and the input record receives a canonical digest.

## Interpretation limits

This adapter does not pair shear cycles with normal-stress cycles, pair channels by phase, create a multiaxial equivalent cycle, infer a damage parameter, calculate fatigue life, correct for closure, or decide acceptance. The user must choose any subsequent pairing and damage rule and document its calibration basis separately. A finite plane set does not provide continuous orientation search, and discrete samples do not bound time extrema. The model example is synthetic and has no fatigue qualification meaning.
