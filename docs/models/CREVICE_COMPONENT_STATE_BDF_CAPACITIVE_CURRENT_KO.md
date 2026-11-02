# Crevice component-state BDF capacitor-current handoff

## Purpose

`CapacitiveCellCurrentSchedule` is an optional, caller-supplied forcing path for the component-state BDF. At exact request knots, it supplies one signed double-layer current per cell. Positive values are defined as current from the interface into the aqueous phase. The BDF charge-continuity convention is `I_ionic,right - I_ionic,left = F Σ(z_i ν_i r) + I_cap`.

The schedule binds ordered time and cell-current records to a SHA-256 digest and licensed `Evidence` with source identity `caller_evidenced_double_layer_capacitive_current_schedule`. The request must explicitly review the schedule, match its clock/cell order to the BDF request, and include an ionic face-current schedule. Both forcing histories are linearly interpolated between identical knots, so endpoint closure gives interval closure under that interpolation. The solver reports knot residuals and trapezoidal cumulative charge by cell.

## Constructing the forcing

A caller may use measured current or a reviewed external double-layer model to prepare this record. The standalone `integration.crevice_double_layer_charge_history` produces stored-charge knots and interval-mean capacitive currents from caller potential, area and differential-capacitance histories. An interval mean does not uniquely determine exact-knot currents; do not relabel interval means as knot samples. If a compatible exact-knot current history is unavailable, retain the standalone charge result and do not activate this BDF schedule.

## Scope boundary

This schedule injects current values only. It does not add a BDF potential or charge state, derive current from `C_dl dE/dt`, solve prescribed-potential Butler–Volmer kinetics, or feed changing potential back into mixed-potential kinetics. The existing stage spatial mixed-potential option is mutually exclusive with this schedule. No corrosion rate, material qualification, life or probability is inferred.

## Work record

The schedule digest covers the exact ordered time and per-cell current table. Evidence must carry the same digest, the source identity above, and a license identifier. Input and output remain caller-owned application data; this guide supplies no empirical parameter table.
