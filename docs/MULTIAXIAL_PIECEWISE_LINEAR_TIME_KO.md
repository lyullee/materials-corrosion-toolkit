# Piecewise-linear time history for finite-plane fatigue factors

`fatigue.critical_plane_piecewise_linear_time_history` evaluates the existing finite-plane Fatemi–Socie and SWT factor definitions for one timed, reviewed, closed local tensor cycle. The caller explicitly declares that stress and infinitesimal-strain tensor components are reconstructed linearly between recorded times. Tensor shear strain follows the `CriticalPlaneHistory` contract and is interpreted as tensor shear.

## Why the returned range is exact for this interpolation

Under the declared reconstruction, any scalar normal stress or strain varies linearly over a time segment, so its minimum and maximum occur at segment endpoints. A resolved two-component shear path also varies linearly within each segment. The segment lies inside the convex hull of its endpoints; therefore it cannot extend beyond the maximum pairwise distance between recorded vertices, and a disk containing all vertices also contains every segment. Thus both the maximum pairwise chord and the minimum enclosing circle of the continuous reconstructed shear path are represented exactly by the recorded vertices.

The output marks `continuous_time_extrema_exact_for_declared_interpolation` only when the underlying representative-cycle closure review succeeds. It also reports segment Frobenius rates for stress and strain and a bounded plane/sample work estimate.

## Use and limits

The result is exact for the declared piecewise-linear interpolation, selected factor definitions and supplied finite plane set. This does not show that the interpolation reproduces behavior between measurements. It does not search continuous plane orientations, pair multiaxial rainflow cycles, accumulate variable-amplitude damage, predict life, or quantify solver, measurement, calibration or model-form uncertainty. A different temporal reconstruction requires a separate reviewed method.

The synthetic example is in `examples/model_inputs.json`. Numerical tests and package work remain deferred under the project instruction.
