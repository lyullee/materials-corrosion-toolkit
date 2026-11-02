# Crevice slit aperture history

`corrosion.planar_slit_aperture_history` converts a caller-pinned cumulative, signed, cell-average wall recession history into successive planar-slit geometry states. Each state reports cell aperture, axial cross section, solution volume, reactive broad-wall area and wall-area-to-volume ratio for a separate transport calculation.

## Inputs and geometry rule

The caller supplies the original geometry identity and digest, wall-loss source digest, cell widths, and each cell's initial aperture. The recession history can be supplied directly, or the complete digest-pinned result of `corrosion.coupled_wall_metal_loss` can be passed in `wall_loss_result`. The latter path carries the cellwise output clock and cell ordering forward and requires its cellwise recession option to have produced a history. Positive recession denotes metal loss; negative recession denotes net deposition under the same signed convention. The first clock entry must be zero and the initial recession row must be zero.

For a slit with `n` reactive broad faces, the sequential remap is:

`aperture(cell, t) = initial_aperture(cell) + n * cumulative_average_recession(cell, t)`

For two reactive faces, this relation assumes equal recession of the opposing faces. The caller must review that allocation. A one-face model treats the opposite boundary as fixed. The API also requires the caller-declared provider aperture range. If an updated aperture leaves that range, the result is `out_of_scope` and retains geometry states through the last accepted knot, the first failed interval, and failing cell indices. This prefix is useful for diagnosing where support ended; it is not a complete history and must not be promoted to a computed campaign.

Cross section and volume are calculated cellwise as `aperture * transverse_width` and `cross_section * cell_width`. Broad-wall area uses the selected face count and fixed transverse width. The returned geometry states can be passed into a new fixed-geometry transport calculation by the caller.

Each time row also includes a `restricted_transport_geometry` object using the field names expected by `RestrictedTransportRequest`: `cell_count`, `length_m`, `cell_widths_m`, `cell_cross_section_m2`, `face_cross_section_m2`, `reference_cross_section_m2`, and `wall_area_per_volume_m2_m3`. The caller can merge these geometry fields into the original transport request for a sequential solve and must review/set `variable_area_one_dimensional_reduction_reviewed` for that use. Face area is linearly interpolated between nonuniform cell centers, with constant extrapolation from the nearest cell to the two outer faces; the caller must review this mapping. When an upstream wall-loss result is supplied, its reference area and total/per-cell reactive wall-area ratios must reconcile with the declared slit face count, transverse width, and cell widths.

## Scope boundary

This is a sequential geometry remap, not a fully coupled corrosion/flow solver. It does not solve fluid continuity or momentum, redistribute flow, update chemistry within a time interval, model roughness or deposits, or establish how asymmetric wall loss changes the aperture. The supplied wall recession must already represent the intended cell-averaged signed material-volume balance and must be tied to the reviewed geometry and wall-loss records by their digests. When passing a `coupled_wall_metal_loss` result, set `wall_loss_source_sha256` to the canonical digest of the entire serialized result object; the API rejects a mismatch and checks the returned cell indices and times before constructing geometry states.

The synthetic API example is in `examples/model_inputs.json`. No physical validation is implied. Numerical tests and package work remain deferred under the project instruction.
