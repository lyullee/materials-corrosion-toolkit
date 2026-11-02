# Caller calibrated Findley parameter to life mapping

`CriticalPlaneFindleyCalibratedLife` composes the existing finite-sample critical-plane Findley stress evaluator with an independently supplied parameter-versus-life record. This provides a typed API for a caller's own material-condition calibration; it does not add or infer calibration data.

The curve contains at least two paired points. Its Findley parameter must increase strictly while cycles to failure decrease strictly. The canonical digest is computed over the ordered point records and must match Evidence carrying the same provider identifier and digest. Rights Evidence must identify a license. Review gates separately cover material/load-basis transfer, monotonicity and interpolation, support/no extrapolation, rights, and authorization.

For an in-range governing parameter, the calculator finds the neighboring points and interpolates linearly in `log(parameter)` versus `log(cycles)`. Values outside the provided interval return `out_of_scope`; no life extrapolation occurs. The nested stress-history request retains its own tensor, cycle, plane-set, Findley-coefficient and calibration lineage. The output carries both request digests and the selected endpoint point IDs.

This is a caller-calibrated interpolation adapter, not an independent reproduction or validation of a fatigue-life standard, a transferable material law, code acceptance, failure probability, or material qualification. Curve provenance, test method compatibility, statistical scatter, environmental conditions, sequence effects, and independent comparisons remain the caller's responsibility.
