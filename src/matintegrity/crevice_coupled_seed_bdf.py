"""Internal BDF driver with accepted-boundary seed and depletion transitions.

The driver integrates only nonnegative solid inventories, locates zero and seed
threshold events, and restarts BDF after each accepted state change. Invalid
trial states, event-budget exhaustion, or solver failures withhold the trajectory.
"""

from __future__ import annotations

import math


def integrate_coupled_seed_bdf(
    rhs,
    initial_state,
    time_s,
    *,
    relative_tolerance,
    absolute_tolerance_mol,
    maximum_step_s,
    maximum_seed_events,
    integrate_component_sources=False,
    seed_threshold_inventory=None,
    absolute_tolerance_vector=None,
):
    """Integrate layout state plus optional RHS-integrated auxiliaries.

    The leading ``layout.total_size`` values are the physical component/solid
    state used for seed and depletion events. Any remaining values in
    ``initial_state`` are caller RHS states (for example integrated face and
    reservoir ledgers) and are carried through each event-driven restart.

    ``seed_threshold_inventory`` may provide a moving threshold amount as
    ``callback(phase_index, cell_index, time_s, integration_state)``. Its
    returned value is a positive finite solid inventory in mol. When omitted,
    the original fixed-volume threshold calculation is preserved.
    """
    from scipy.integrate import solve_ivp

    times = tuple(float(t) for t in time_s)
    if (
        len(times) < 2
        or any(not math.isfinite(t) for t in times)
        or any(b <= a for a, b in zip(times, times[1:], strict=False))
    ):
        raise ValueError("output times must be finite and strictly increasing")
    if any(
        not math.isfinite(v) or v <= 0 for v in (relative_tolerance, absolute_tolerance_mol, maximum_step_s)
    ):
        raise ValueError("positive finite BDF tolerances and step bound are required")
    if type(maximum_seed_events) is not int or maximum_seed_events < 1:
        raise ValueError("a positive seed event budget is required")
    layout = rhs.layout
    if type(integrate_component_sources) is not bool:
        raise ValueError("component source integration must be an explicit boolean")
    if seed_threshold_inventory is not None and not callable(seed_threshold_inventory):
        raise ValueError("seed threshold inventory must be a callable or absent")
    layout_size = layout.total_size
    integration_state_size = len(initial_state)
    if integration_state_size < layout_size:
        raise ValueError("integration state must include the complete leading phase-layout state")
    if any(isinstance(value, bool) or not math.isfinite(float(value)) for value in initial_state):
        raise ValueError("initial integration state must contain only finite values")
    if absolute_tolerance_vector is None:
        absolute_tolerances = (float(absolute_tolerance_mol),) * integration_state_size
    else:
        absolute_tolerances = tuple(float(value) for value in absolute_tolerance_vector)
        if len(absolute_tolerances) != integration_state_size or any(
            not math.isfinite(value) or value <= 0.0 for value in absolute_tolerances
        ):
            raise ValueError("absolute tolerance vector must provide one positive finite value per integrated state")
    initial_physical_state = tuple(initial_state[:layout_size])
    unpack_trial = getattr(layout, "unpack_trial", None)
    if not callable(unpack_trial):
        unpack_trial = getattr(rhs, "unpack_trial", None)
    if not callable(unpack_trial):
        raise ValueError("seed-aware BDF layout requires an unpack_trial method")
    _, solids = unpack_trial(initial_physical_state)
    nc = len(layout.cell_ids)
    phase_count = len(layout.phase_ids)
    split = len(layout.component_ids) * nc

    nucleation = getattr(rhs, "nucleation", None)
    if nucleation is None:
        raise ValueError("seed-aware BDF requires one nucleation law per phase and cell")
    phase_major = getattr(rhs, "nucleation_phase_major", False)
    expected_outer = phase_count if phase_major else nc
    expected_inner = nc if phase_major else phase_count
    if (len(nucleation) != expected_outer
            or any(len(row) != expected_inner for row in nucleation)):
        raise ValueError("nucleation-law grid must match its declared phase/cell ordering")

    def nucleation_law(phase_index, cell_index):
        return (nucleation[phase_index][cell_index] if phase_major
                else nucleation[cell_index][phase_index])

    def threshold_inventory(phase_index, cell_index, time_s, integration_state):
        if seed_threshold_inventory is None:
            amount = (
                float(nucleation_law(phase_index, cell_index).nucleated_inventory_threshold_mol_m3)
                * float(rhs.volumes[cell_index])
            )
        else:
            try:
                amount = seed_threshold_inventory(
                    phase_index, cell_index, float(time_s), tuple(integration_state)
                )
            except (TypeError, ValueError, ArithmeticError, OverflowError, RuntimeError) as error:
                raise RuntimeError(f"seed_threshold_inventory_callback_failed:{phase_index}:{cell_index}") from error
        if isinstance(amount, bool):
            raise ValueError("seed threshold inventory cannot be boolean")
        try:
            result = float(amount)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("seed threshold inventory must be a finite molar amount") from error
        if not math.isfinite(result) or result <= 0.0:
            raise ArithmeticError("seed threshold inventory must be finite and positive")
        return result

    initial_thresholds = tuple(
        tuple(threshold_inventory(j, c, times[0], initial_state) for c in range(nc))
        for j in range(len(layout.phase_ids))
    )
    modes = [
        [bool(solids[j][c] >= initial_thresholds[j][c]) for c in range(nc)]
        for j in range(len(layout.phase_ids))
    ]
    state = tuple(initial_state) + ((0.0,) * split if integrate_component_sources else ())
    integrated_source_start = integration_state_size

    def coupled_derivative(time, values):
        rates = tuple(rhs(time, values[:integration_state_size]))
        if len(rates) != integration_state_size or any(
            isinstance(value, bool) or not math.isfinite(float(value)) for value in rates
        ):
            raise ArithmeticError("seed-aware RHS must return one finite rate per integration-state value")
        return rates + (rates[:split] if integrate_component_sources else ())

    now = times[0]
    segments, transitions, depletions = [], [], []
    event_boundary_states = {}
    seed_mode_by_time = {times[0]: tuple(tuple(row) for row in modes)}
    try:
        while now < times[-1]:
            rhs.set_seed_modes_at_boundary(modes)
            events, identities = [], []
            for j in range(len(layout.phase_ids)):
                for c in range(nc):
                    index = split + j * nc + c
                    if state[index] > 0:

                        def depleted(t, y, index=index):
                            return y[index]

                        depleted.terminal = True
                        depleted.direction = -1
                        events.append(depleted)
                        identities.append(("depletion", j, c))
                    elif state[index] < 0:
                        raise ArithmeticError("negative_solid_inventory_at_event_restart")
                    if modes[j][c]:
                        continue

                    def crossing(t, y, index=index, j=j, c=c):
                        threshold = threshold_inventory(j, c, t, y[:integration_state_size])
                        return y[index] - threshold

                    crossing.terminal = True
                    crossing.direction = 1
                    events.append(crossing)
                    identities.append(("seed", j, c))
            auxiliary_tolerances = ((absolute_tolerances[:split]) * len(layout.component_ids)
                                    if integrate_component_sources else ())
            result = solve_ivp(
                coupled_derivative,
                (now, times[-1]),
                state,
                method="BDF",
                rtol=relative_tolerance,
                atol=absolute_tolerances + auxiliary_tolerances,
                max_step=maximum_step_s,
                events=events or None,
                dense_output=True,
            )
            if not result.success:
                raise RuntimeError("coupled seed BDF integration failed")
            end = float(result.t[-1])
            if end <= now:
                raise RuntimeError("coupled seed event made no time progress")
            segments.append((now, end, result.sol, tuple(tuple(row) for row in modes)))
            state = tuple(float(x) for x in result.y[:, -1])
            if result.status != 1:
                if any(state[split + j * nc + c] < -absolute_tolerance_mol
                       for j in range(len(layout.phase_ids)) for c in range(nc)):
                    raise ArithmeticError("negative_solid_inventory_at_output_knot")
                state = tuple(0.0 if split <= index < split + len(layout.phase_ids) * nc
                              and value < 0.0 else value for index, value in enumerate(state))
                unpack_trial(state[:layout_size])
                now = end
                break
            hits = [identities[i] for i, values in enumerate(result.t_events) if len(values)]
            if not hits:
                raise RuntimeError("terminal seed event has no phase/cell identity")
            # Root localization can leave a tiny negative solid representation.
            # Project only explicitly located zero events before evaluating the
            # endpoint chemistry; ordinary trial states remain unclipped.
            for kind, j, c in hits:
                if kind == "depletion":
                    index = split + j * nc + c
                    state = tuple(0.0 if position == index else value for position, value in enumerate(state))
            if any(state[split + j * nc + c] < -absolute_tolerance_mol
                   for j in range(len(layout.phase_ids)) for c in range(nc)):
                raise ArithmeticError("negative_solid_inventory_at_event_boundary")
            state = tuple(0.0 if split <= index < split + len(layout.phase_ids) * nc
                          and value < 0.0 else value for index, value in enumerate(state))
            unpack_trial(state[:layout_size])
            # A terminal root can suppress reporting other roots at the same
            # endpoint. Group seed/depletion surfaces only within binary rounding
            # resolution, rather than using the ODE's much larger absolute tol.
            endpoint_rates = coupled_derivative(end, state)
            for j in range(len(layout.phase_ids)):
                for c in range(nc):
                    index = split + j * nc + c
                    threshold = threshold_inventory(j, c, end, state[:integration_state_size])
                    if modes[j][c] and ("depletion", j, c) not in hits:
                        rounding_tolerance = 64 * math.ulp(absolute_tolerance_mol)
                        if state[index] >= 0 and state[index] <= rounding_tolerance and endpoint_rates[index] < 0:
                            hits.append(("depletion", j, c))
                    elif not modes[j][c] and ("seed", j, c) not in hits:
                        rounding_tolerance = 64 * max(math.ulp(state[index]), math.ulp(threshold))
                        if abs(state[index] - threshold) <= rounding_tolerance and endpoint_rates[index] > 0:
                            hits.append(("seed", j, c))
            hits.sort(key=lambda row: (row[1], row[2], row[0]))
            if len(transitions) + len(depletions) + len(hits) > maximum_seed_events:
                raise RuntimeError("coupled phase-state event budget exceeded")
            for kind, j, c in hits:
                index = split + j * nc + c
                if kind == "depletion":
                    # This is an event-boundary projection after locating the
                    # zero surface, not clipping an unconstrained trial step.
                    state = tuple(0.0 if position == index else value for position, value in enumerate(state))
                    modes[j][c] = False
                    depletions.append(dict(time_s=end, phase_id=layout.phase_ids[j], cell_id=layout.cell_ids[c]))
                else:
                    modes[j][c] = True
                    transitions.append(dict(time_s=end, phase_id=layout.phase_ids[j], cell_id=layout.cell_ids[c]))
            event_boundary_states[end] = state
            seed_mode_by_time[end] = tuple(tuple(row) for row in modes)
            now = end
        output, source_history, balance_history, seed_modes_at_time = [], [], [], []
        for t in times:
            segment = next((row for row in segments if row[0] <= t <= row[1]), None)
            if segment is None:
                raise RuntimeError("requested knot has no integrated support")
            values = event_boundary_states.get(t)
            if values is None:
                values = tuple(float(x) for x in segment[2](t))
            physical = values[:integration_state_size]
            unpack_trial(physical[:layout_size])
            output.append(physical)
            mode_snapshot = seed_mode_by_time.get(t)
            if mode_snapshot is None:
                mode_snapshot = segment[3]
            seed_modes_at_time.append(mode_snapshot)
            if integrate_component_sources:
                sources = tuple(
                    tuple(values[integrated_source_start + i * nc : integrated_source_start + (i + 1) * nc])
                    for i in range(len(layout.component_ids))
                )
                balance = layout.component_balance(
                    initial_physical_state,
                    physical[:layout_size],
                    sources,
                    absolute_tolerance_mol=absolute_tolerance_mol,
                    relative_tolerance=relative_tolerance,
                )
                if not balance["balanced"]:
                    raise ArithmeticError("integrated component balance exceeds declared tolerances")
                source_history.append(sources)
                balance_history.append(balance)
        report = dict(
            committed=True,
            time_s=times,
            state_by_time=tuple(output),
            seed_transitions=tuple(transitions),
            phase_depletions=tuple(depletions),
            seed_modes_by_time=tuple(seed_modes_at_time),
            rhs_evaluations=rhs.evaluations,
            layout_state_size=layout_size,
            integration_state_size=integration_state_size,
            seed_threshold_policy=(
                "caller_time_state_dependent_inventory_callback"
                if seed_threshold_inventory is not None else "fixed_volume_law_threshold_times_cell_volume"
            ),
            simultaneous_event_policy=(
                "upward_seed_surfaces_within_64_binary64_ulps; downward_zero_surfaces_within_64_ulps_of_absolute_tolerance"
            ),
            solid_state_policy="accepted_zero_event_releases_seed_latch_and_allows_later_reappearance",
        )
        if integrate_component_sources:
            report.update(
                integrated_net_sources_by_time=tuple(source_history),
                component_balance_by_time=tuple(balance_history),
                source_integration_policy="same_BDF_trial_derivative_augmented_state",
            )
        return report
    except (TypeError, ValueError, ArithmeticError, OverflowError, RuntimeError) as error:
        return dict(
            committed=False,
            reason=str(error),
            seed_transitions=tuple(transitions),
            phase_depletions=tuple(depletions),
            rhs_evaluations=rhs.evaluations,
        )
