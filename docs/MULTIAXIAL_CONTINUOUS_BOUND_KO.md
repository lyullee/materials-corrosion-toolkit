# Continuous-plane bound for sampled multiaxial fatigue factors

`fatigue.critical_plane_continuous_bound` evaluates a reviewed closed local tensor cycle on successively refined icosphere vertex sets. It uses the same basis-invariant maximum pairwise engineering-shear chord and FS/SWT factor definitions as `fatigue.critical_plane_vector_path_factors`.

## Orientation coverage

Each icosphere level triangulates the complete unit sphere. A plane normal and its negative represent the same plane and are canonicalized to one candidate. Every point on the sphere belongs to one spherical triangular face. The maximum great-circle edge angle of the mesh is used as a conservative face covering radius: the distance from any point in a face to at least one of its vertices is no greater than that face's largest edge. The reported angular radius therefore covers continuous plane orientation, subject to the stated spherical-triangulation construction.

## Factor Lipschitz bounds

Let `Mσ` and `Mε` be the largest sample-wise Frobenius norms of the symmetric stress and tensor-strain histories, `k` the supplied Fatemi-Socie coefficient, and `S0` its positive normalization stress. For a unit-normal change with angular distance `θ`, the implementation uses these conservative constants:

- `Lγ = 6 Mε` for half the maximum pairwise chord of the two-component engineering-shear path;
- `Lσ = 2 Mσ` for maximum tensile normal stress;
- `Lε = 2 Mε` for normal-strain half-range;
- `LFS = Lγ (1 + k Mσ/S0) + 4 k Mε Mσ/S0`;
- `LSWT = 4 Mσ Mε`.

For each fully evaluated level with sampled maxima `F*` and `W*` and maximum edge angle `θmax`, the returned continuous-plane bounds are `F* ≤ Fcontinuous ≤ F* + LFS θmax` and `W* ≤ Wcontinuous ≤ W* + LSWT θmax`. These bounds apply to the exact discrete sample-cycle factor definitions in this package, not to unsampled time histories or other fatigue criteria.

## Limits and budgets

The caller supplies a closed representative local cycle, tensor source lineage, material condition, Fatemi-Socie parameters, maximum subdivision level, candidate-evaluation budget and sample-pair work budget. A complete level is evaluated before its coverage radius is used. If a later level exceeds either budget, the last fully evaluated level still supplies a valid bound. `all_bounds_within_tolerance` reports only whether both requested absolute gaps are met.

The calculation does not bound time-interpolation extrema, cycle counting, tensor-field or mesh discretization, coefficient calibration uncertainty, material transfer, physical model error, fatigue life or acceptance. The example in `examples/model_inputs.json` is synthetic. Tests and physical qualification remain deferred.
