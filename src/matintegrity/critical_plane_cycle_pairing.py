"""Caller-declared pairing and calibrated damage for scalar plane cycles."""

from __future__ import annotations

import heapq
import math

from pydantic import Field, model_validator

from .contracts import Contract, Fraction, Nonnegative, Positive, canonical_digest
from .critical_plane_life import CriticalPlaneFsLife, evaluate_critical_plane_fs_life


class CriticalPlaneCyclePair(Contract):
    """One explicit normal-stress/shear-strain cycle allocation."""

    pair_id: str = Field(min_length=1)
    normal_stress_cycle_index: int = Field(ge=0)
    shear_strain_cycle_index: int = Field(ge=0)
    allocated_cycle_count: Positive


class CriticalPlaneCyclePairDamage(Contract):
    """Apply a reviewed cycle map and caller-calibrated FS strain-life relation."""

    analysis_id: str = Field(min_length=1)
    projected_rainflow_result: dict
    projected_rainflow_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plane_id: str = Field(min_length=1)
    shear_projection: str = Field(
        pattern=r"^(engineering_shear_strain_directional_component|engineering_shear_strain_vector_magnitude)$"
    )
    pairings: tuple[CriticalPlaneCyclePair, ...] = Field(min_length=1, max_length=100000)
    cycle_pairing_method_id: str = Field(min_length=1)
    cycle_pairing_method_revision: str = Field(min_length=1)
    cycle_pairing_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pairing_proposal: dict | None = None
    pairing_proposal_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    cycle_pairing_and_allocation_reviewed: bool
    load_channel_interpretation_reviewed: bool
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    calibration_material_condition_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    shear_modulus_Pa: Positive
    shear_fatigue_strength_coefficient_Pa: Positive
    shear_fatigue_strength_exponent: float = Field(lt=0)
    shear_fatigue_ductility_coefficient: Positive
    shear_fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    material_calibration_and_factor_convention_reviewed: bool

    @model_validator(mode="after")
    def ordered_unique_pairings(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("calibrated cycle support must be strictly ordered")
        pair_ids = [row.pair_id for row in self.pairings]
        if len(set(pair_ids)) != len(pair_ids):
            raise ValueError("pair IDs must be unique")
        if (self.pairing_proposal is None) != (self.pairing_proposal_sha256 is None):
            raise ValueError("a pairing proposal and its digest must be supplied together")
        return self


class CriticalPlaneIntervalOverlapPairing(Contract):
    """Propose cycle allocations by deterministic overlap of rainflow sample intervals."""

    projected_rainflow_result: dict
    projected_rainflow_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plane_id: str = Field(min_length=1)
    shear_projection: str = Field(
        pattern=r"^(engineering_shear_strain_directional_component|engineering_shear_strain_vector_magnitude)$"
    )
    minimum_interval_iou: Fraction = 0.0
    method_revision: str = Field(min_length=1)
    configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    same_ordered_sample_clock_reviewed: bool = False
    maximum_cycle_pair_work: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_flow_augmentations: int = Field(default=100_000, ge=1, le=1_000_000)


def propose_critical_plane_interval_overlap_pairing(request: CriticalPlaneIntervalOverlapPairing) -> dict:
    """Create a deterministic, review-required map; it does not assert physical pairing."""
    result_digest = canonical_digest(request.projected_rainflow_result)
    base = {
        "status": "needs_data",
        "plane_id": request.plane_id,
        "shear_projection": request.shear_projection,
        "projected_rainflow_result_sha256": result_digest,
        "cycle_pairing_configuration_sha256": request.configuration_sha256,
        "cycle_pairing_method_id": "rainflow_sample_interval_iou_maxflow_v2",
        "cycle_pairing_method_revision": request.method_revision,
        "cycle_pairing_and_allocation_reviewed": False,
        "load_channel_interpretation_reviewed": False,
        "material_calibration_and_factor_convention_reviewed": False,
        "pairings": None,
        "normal_unallocated_cycle_count": None,
        "shear_unallocated_cycle_count": None,
    }
    if result_digest != request.projected_rainflow_result_sha256:
        raise ValueError("projected rainflow result digest differs from the caller-pinned value")
    if not request.same_ordered_sample_clock_reviewed:
        return base | {"reason": "same_ordered_sample_clock_review_required"}
    result = request.projected_rainflow_result
    if result.get("status") != "computed" or not isinstance(result.get("values"), dict):
        result_status = result.get("status")
        result_status = result_status if result_status in {"needs_data", "out_of_scope"} else "needs_data"
        return base | {"status": result_status, "reason": "computed_projection_result_required"}
    rows = result["values"].get("projection_cycle_results")
    if not isinstance(rows, list):
        return base | {"reason": "projection_cycle_records_missing"}
    plane = next((row for row in rows if isinstance(row, dict) and row.get("plane_id") == request.plane_id), None)
    if plane is None or not isinstance(plane.get("projections"), dict):
        return base | {"status": "out_of_scope", "reason": "requested_plane_missing"}
    projections = plane["projections"]
    normal_data = projections.get("normal_stress")
    shear_data = projections.get(request.shear_projection)
    if not isinstance(normal_data, dict) or not isinstance(shear_data, dict):
        return base | {"status": "out_of_scope", "reason": "requested_projection_missing"}
    if normal_data.get("projection_interpretation") != "signed_normal_stress":
        return base | {"status": "out_of_scope", "reason": "normal_projection_interpretation_mismatch"}
    expected_shear = (
        "signed_engineering_shear_component_along_supplied_in_plane_direction"
        if request.shear_projection == "engineering_shear_strain_directional_component"
        else "nonnegative_engineering_shear_vector_magnitude_direction_lost"
    )
    if shear_data.get("projection_interpretation") != expected_shear:
        return base | {"status": "out_of_scope", "reason": "shear_projection_interpretation_mismatch"}
    normal = normal_data.get("cycles")
    shear = shear_data.get("cycles")
    if not isinstance(normal, list) or not isinstance(shear, list):
        return base | {"reason": "cycle_lists_missing"}
    sample_count = result["values"].get("sample_count")
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 1:
        return base | {"status": "out_of_scope", "reason": "source_sample_count_missing"}
    pair_work = len(normal) * len(shear)
    if pair_work > request.maximum_cycle_pair_work:
        return base | {"status": "out_of_scope", "pair_work": pair_work, "reason": "candidate_pair_work_limit_exceeded"}

    def cycle_rows(cycles):
        parsed = []
        for index, cycle in enumerate(cycles):
            if not isinstance(cycle, dict):
                return None
            start, end, count = cycle.get("start_index"), cycle.get("end_index"), cycle.get("count")
            if (
                isinstance(start, bool) or not isinstance(start, int)
                or isinstance(end, bool) or not isinstance(end, int)
                or end < start
                or start < 0 or end >= sample_count
                or isinstance(count, bool) or not isinstance(count, (int, float))
                or not math.isfinite(float(count)) or count <= 0
            ):
                return None
            parsed.append((index, start, end, float(count)))
        return parsed

    normal_rows, shear_rows = cycle_rows(normal), cycle_rows(shear)
    if normal_rows is None or shear_rows is None:
        return base | {"status": "out_of_scope", "reason": "cycle_interval_or_count_invalid"}
    candidates = []
    for ni, ns, ne, _ in normal_rows:
        for si, ss, se, _ in shear_rows:
            overlap = max(0, min(ne, se) - max(ns, ss) + 1)
            if overlap == 0:
                continue
            union = max(ne, se) - min(ns, ss) + 1
            iou = overlap / union
            if iou >= request.minimum_interval_iou:
                candidates.append((iou, overlap, ni, si))
    normal_remaining = {index: count for index, _, _, count in normal_rows}
    shear_remaining = {index: count for index, _, _, count in shear_rows}

    # Continuous-capacity bipartite min-cost max-flow: first maximize the total
    # paired cycle equivalent, then minimize (1 - interval IoU) per allocated
    # equivalent. Stable node/edge order makes equal-cost solutions repeatable.
    source = 0
    normal_offset = 1
    shear_offset = normal_offset + len(normal_rows)
    sink = shear_offset + len(shear_rows)
    graph: list[list[list[float | int]]] = [[] for _ in range(sink + 1)]

    def add_edge(start: int, end: int, capacity: float, cost: float):
        forward = [end, len(graph[end]), capacity, cost]
        reverse = [start, len(graph[start]), 0.0, -cost]
        graph[start].append(forward)
        graph[end].append(reverse)
        return forward

    normal_node = {index: normal_offset + position for position, (index, _, _, _) in enumerate(normal_rows)}
    shear_node = {index: shear_offset + position for position, (index, _, _, _) in enumerate(shear_rows)}
    for index, count in normal_remaining.items():
        add_edge(source, normal_node[index], count, 0.0)
    for index, count in shear_remaining.items():
        add_edge(shear_node[index], sink, count, 0.0)
    candidate_edges = {}
    for iou, overlap, ni, si in sorted(candidates, key=lambda row: (row[2], row[3])):
        edge = add_edge(normal_node[ni], shear_node[si], math.inf, 1.0 - iou)
        candidate_edges[(ni, si)] = (edge, iou, overlap)

    potentials = [0.0] * len(graph)
    flow_augmentation_count = 0
    while True:
        distances = [math.inf] * len(graph)
        previous: list[tuple[int, int] | None] = [None] * len(graph)
        distances[source] = 0.0
        queue = [(0.0, source)]
        while queue:
            distance, node = heapq.heappop(queue)
            if distance > distances[node]:
                continue
            for edge_index, edge in enumerate(graph[node]):
                target, _, capacity, cost = edge
                if capacity <= 0:
                    continue
                reduced_cost = float(cost) + potentials[node] - potentials[int(target)]
                if reduced_cost < 0 and reduced_cost > -1e-12:
                    reduced_cost = 0.0
                candidate_distance = distance + reduced_cost
                if candidate_distance < distances[int(target)]:
                    distances[int(target)] = candidate_distance
                    previous[int(target)] = (node, edge_index)
                    heapq.heappush(queue, (candidate_distance, int(target)))
        if previous[sink] is None:
            break
        if flow_augmentation_count >= request.maximum_flow_augmentations:
            return base | {
                "status": "out_of_scope",
                "reason": "maximum_flow_augmentation_budget_exceeded",
                "flow_augmentation_count": flow_augmentation_count,
                "maximum_flow_augmentations": request.maximum_flow_augmentations,
                "candidate_pair_count": len(candidates),
                "pair_work": pair_work,
            }
        for node, distance in enumerate(distances):
            if math.isfinite(distance):
                potentials[node] += distance
        amount = math.inf
        node = sink
        while node != source:
            prior = previous[node]
            if prior is None:
                amount = 0.0
                break
            parent, edge_index = prior
            amount = min(amount, float(graph[parent][edge_index][2]))
            node = parent
        if not math.isfinite(amount) or amount <= 0:
            break
        node = sink
        while node != source:
            parent, edge_index = previous[node]  # type: ignore[misc]
            edge = graph[parent][edge_index]
            reverse = graph[node][int(edge[1])]
            edge[2] = float(edge[2]) - amount
            reverse[2] = float(reverse[2]) + amount
            node = parent
        flow_augmentation_count += 1

    pairings = []
    diagnostics = []
    normal_remaining = {index: count for index, count in normal_remaining.items()}
    shear_remaining = {index: count for index, count in shear_remaining.items()}
    for (ni, si), (edge, iou, overlap) in sorted(candidate_edges.items()):
        # Candidate forward capacity began unbounded; its reverse residual is
        # the net allocation after any later augmenting-path reroutes.
        reverse_flow = float(graph[int(edge[0])][int(edge[1])][2])
        allocated = reverse_flow
        if allocated <= 0:
            continue
        pair_id = f"interval-overlap-{len(pairings):06d}"
        pairings.append({
            "pair_id": pair_id,
            "normal_stress_cycle_index": ni,
            "shear_strain_cycle_index": si,
            "allocated_cycle_count": allocated,
        })
        diagnostics.append({
            "pair_id": pair_id,
            "interval_intersection_over_union": iou,
            "shared_sample_index_count": overlap,
        })
        normal_remaining[ni] -= allocated
        shear_remaining[si] -= allocated
    proposal = base | {
        "status": "computed",
        "pairings": pairings,
        "pairing_diagnostics": diagnostics,
        "normal_unallocated_cycle_count": math.fsum(normal_remaining.values()),
        "shear_unallocated_cycle_count": math.fsum(shear_remaining.values()),
        "normal_cycle_count": math.fsum(row[3] for row in normal_rows),
        "shear_cycle_count": math.fsum(row[3] for row in shear_rows),
        "candidate_pair_count": len(candidates),
        "pair_work": pair_work,
        "flow_augmentation_count": flow_augmentation_count,
        "minimum_interval_iou": request.minimum_interval_iou,
        "allocation_method": "continuous-capacity min-cost max-flow maximizes total paired cycle count, then maximizes allocated-count-weighted interval IoU; stable source-index edge order resolves equal-cost paths",
        "damage_request_reviewed": False,
        "limitations": [
            "This is a deterministic temporal-overlap proposal, not a validated physical cycle-pairing law.",
            "The optimization objective is a temporal-overlap proxy; it does not establish a physical stress-strain cycle-pairing law.",
            "Unallocated residual cycles are reported and must not be silently discarded when forming damage.",
        ],
    }
    proposal["proposal_sha256"] = canonical_digest(proposal)
    return proposal


def _finite_cycle_value(cycle: dict, key: str) -> float | None:
    value = cycle.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def critical_plane_cycle_pair_damage(request: CriticalPlaneCyclePairDamage) -> dict:
    """Use only the caller's cycle allocations; never infer channel pairing."""
    source_digest = canonical_digest(request.projected_rainflow_result)
    base = dict(
        analysis_id=request.analysis_id,
        status="needs_data",
        projected_rainflow_result_sha256=source_digest,
        cycle_pairing_configuration_sha256=request.cycle_pairing_configuration_sha256,
        calibration_sha256=request.calibration_sha256,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        pair_results=None,
        total_miner_damage=None,
    )
    if source_digest != request.projected_rainflow_result_sha256:
        raise ValueError("projected rainflow result digest differs from the caller-pinned value")
    proposal_values = None
    if request.pairing_proposal is not None:
        proposal_digest = canonical_digest(request.pairing_proposal)
        if proposal_digest != request.pairing_proposal_sha256:
            raise ValueError("pairing proposal differs from the caller-pinned digest")
        proposal_values = request.pairing_proposal.get("values", request.pairing_proposal)
        proposal_status = request.pairing_proposal.get("status")
        if proposal_status != "computed" or not isinstance(proposal_values, dict):
            return base | dict(status="out_of_scope", reason="A computed interval-overlap proposal is required")
        proposal_core = {key: value for key, value in proposal_values.items() if key != "proposal_sha256"}
        proposal_core["status"] = "computed"
        if (
            proposal_values.get("proposal_sha256") != canonical_digest(proposal_core)
            or proposal_values.get("projected_rainflow_result_sha256") != source_digest
            or proposal_values.get("plane_id") != request.plane_id
            or proposal_values.get("shear_projection") != request.shear_projection
            or proposal_values.get("cycle_pairing_method_id") != request.cycle_pairing_method_id
            or proposal_values.get("cycle_pairing_method_revision") != request.cycle_pairing_method_revision
            or proposal_values.get("cycle_pairing_configuration_sha256") != request.cycle_pairing_configuration_sha256
        ):
            return base | dict(status="out_of_scope", reason="Proposal lineage does not match the reviewed damage request")
        proposed_edges = {
            (item.get("normal_stress_cycle_index"), item.get("shear_strain_cycle_index"))
            for item in proposal_values.get("pairings", [])
            if isinstance(item, dict)
        }
        if any((item.normal_stress_cycle_index, item.shear_strain_cycle_index) not in proposed_edges for item in request.pairings):
            return base | dict(status="out_of_scope", reason="Reviewed allocation introduces an edge absent from the pinned proposal")
        base["pairing_proposal_sha256"] = proposal_digest
    if not (
        request.cycle_pairing_and_allocation_reviewed
        and request.load_channel_interpretation_reviewed
        and request.material_calibration_and_factor_convention_reviewed
    ):
        return base
    result = request.projected_rainflow_result
    if result.get("status") != "computed":
        return base | dict(
            status=result.get("status") if result.get("status") in {"needs_data", "out_of_scope"} else "needs_data",
            reason="A computed scalar projection/rainflow result is required",
        )
    values = result.get("values")
    if not isinstance(values, dict):
        return base | dict(reason="Rainflow result values must be an object")
    if values.get("material_condition_id") != request.calibration_material_condition_id:
        return base | dict(
            status="out_of_scope",
            reason="Life calibration material condition differs from the projected history",
        )
    plane_rows = values.get("projection_cycle_results")
    if not isinstance(plane_rows, list):
        return base | dict(reason="Projected cycle records are unavailable")
    selected_plane = next(
        (row for row in plane_rows if isinstance(row, dict) and row.get("plane_id") == request.plane_id),
        None,
    )
    if selected_plane is None or not isinstance(selected_plane.get("projections"), dict):
        return base | dict(status="out_of_scope", reason="Selected plane is absent from the projected result")
    projections = selected_plane["projections"]
    normal_data = projections.get("normal_stress")
    shear_data = projections.get(request.shear_projection)
    if not isinstance(normal_data, dict) or not isinstance(shear_data, dict):
        return base | dict(status="out_of_scope", reason="Selected normal or shear channel is absent")
    if normal_data.get("quantity_unit") != "Pa" or shear_data.get("quantity_unit") != "1":
        return base | dict(status="out_of_scope", reason="Cycle channels do not have the required stress/strain units")
    normal_cycles = normal_data.get("cycles")
    shear_cycles = shear_data.get("cycles")
    if not isinstance(normal_cycles, list) or not isinstance(shear_cycles, list):
        return base | dict(reason="Normal and shear cycle lists are required")
    if normal_data.get("projection_interpretation") != "signed_normal_stress":
        return base | dict(status="out_of_scope", reason="Normal channel is not signed normal stress")
    expected_shear_interpretation = (
        "signed_engineering_shear_component_along_supplied_in_plane_direction"
        if request.shear_projection == "engineering_shear_strain_directional_component"
        else "nonnegative_engineering_shear_vector_magnitude_direction_lost"
    )
    if shear_data.get("projection_interpretation") != expected_shear_interpretation:
        return base | dict(status="out_of_scope", reason="Shear projection interpretation does not match its identifier")

    allocated: dict[tuple[str, int], float] = {}
    pair_results = []
    unresolved_pairs = []
    for pair in request.pairings:
        if pair.normal_stress_cycle_index >= len(normal_cycles) or pair.shear_strain_cycle_index >= len(shear_cycles):
            return base | dict(
                status="out_of_scope",
                reason="A caller-declared cycle index is outside its source channel",
                invalid_pair_id=pair.pair_id,
            )
        normal_cycle = normal_cycles[pair.normal_stress_cycle_index]
        shear_cycle = shear_cycles[pair.shear_strain_cycle_index]
        if not isinstance(normal_cycle, dict) or not isinstance(shear_cycle, dict):
            return base | dict(status="out_of_scope", reason="Source cycle rows must be objects")
        normal_count = _finite_cycle_value(normal_cycle, "count")
        shear_count = _finite_cycle_value(shear_cycle, "count")
        normal_range = _finite_cycle_value(normal_cycle, "range")
        normal_mean = _finite_cycle_value(normal_cycle, "mean")
        shear_range = _finite_cycle_value(shear_cycle, "range")
        if None in (normal_count, shear_count, normal_range, normal_mean, shear_range):
            return base | dict(
                status="out_of_scope",
                reason="Source cycles contain nonfinite or incomplete scalar values",
                invalid_pair_id=pair.pair_id,
            )
        if normal_range < 0 or shear_range <= 0 or normal_count <= 0 or shear_count <= 0:
            return base | dict(
                status="out_of_scope",
                reason="Cycle ranges/counts must be positive; zero shear amplitude has no calibrated FS life",
                invalid_pair_id=pair.pair_id,
            )
        for channel, index, available in (
            ("normal", pair.normal_stress_cycle_index, normal_count),
            ("shear", pair.shear_strain_cycle_index, shear_count),
        ):
            key = (channel, index)
            used = allocated.get(key, 0.0) + pair.allocated_cycle_count
            if used > available + 1e-12 * max(1.0, available):
                return base | dict(
                    status="out_of_scope",
                    reason="Pair allocations consume more cycles than the source channel contains",
                    invalid_pair_id=pair.pair_id,
                    source_channel=channel,
                    source_cycle_index=index,
                    allocated_count=used,
                    available_count=available,
                )
            allocated[key] = used

        shear_strain_amplitude = shear_range / 2
        maximum_tensile_normal_stress = max(0.0, normal_mean + normal_range / 2)
        fs_factor = shear_strain_amplitude * (
            1
            + request.fatemi_socie_coefficient
            * maximum_tensile_normal_stress
            / request.normalization_stress_Pa
        )
        factor_basis = dict(
            pair_id=pair.pair_id,
            plane_id=request.plane_id,
            normal_stress_cycle_index=pair.normal_stress_cycle_index,
            shear_strain_cycle_index=pair.shear_strain_cycle_index,
            normal_stress_cycle=normal_cycle,
            shear_strain_cycle=shear_cycle,
            allocated_cycle_count=pair.allocated_cycle_count,
            maximum_tensile_normal_stress_Pa=maximum_tensile_normal_stress,
            engineering_shear_strain_amplitude=shear_strain_amplitude,
            fatemi_socie_factor=fs_factor,
            cycle_pairing_method_id=request.cycle_pairing_method_id,
            cycle_pairing_method_revision=request.cycle_pairing_method_revision,
            cycle_pairing_configuration_sha256=request.cycle_pairing_configuration_sha256,
            calibration_sha256=request.calibration_sha256,
            projected_rainflow_result_sha256=source_digest,
        )
        life = evaluate_critical_plane_fs_life(
            CriticalPlaneFsLife(
                analysis_id=request.analysis_id,
                plane_id=request.plane_id,
                plane_factor_result_sha256=canonical_digest(factor_basis),
                fatemi_socie_factor=fs_factor,
                shear_modulus_Pa=request.shear_modulus_Pa,
                shear_fatigue_strength_coefficient_Pa=request.shear_fatigue_strength_coefficient_Pa,
                shear_fatigue_strength_exponent=request.shear_fatigue_strength_exponent,
                shear_fatigue_ductility_coefficient=request.shear_fatigue_ductility_coefficient,
                shear_fatigue_ductility_exponent=request.shear_fatigue_ductility_exponent,
                minimum_valid_cycles=request.minimum_valid_cycles,
                maximum_valid_cycles=request.maximum_valid_cycles,
                engineering_shear_amplitude_and_calibration_reviewed=True,
            )
        )
        if life.get("status") != "computed":
            unresolved_pairs.append(dict(**factor_basis, life_result=life))
            continue
        cycles_to_failure = life["cycles_to_failure"]
        pair_results.append(
            dict(
                **factor_basis,
                life_result=life,
                cycles_to_failure=cycles_to_failure,
                miner_damage=pair.allocated_cycle_count / cycles_to_failure,
            )
        )
    if unresolved_pairs:
        return base | dict(
            status="out_of_scope",
            reason="At least one paired factor is outside the supplied calibrated life support; aggregate damage withheld",
            pair_results=pair_results + unresolved_pairs,
        )
    unpaired_cycles = []
    for channel, cycles in (("normal", normal_cycles), ("shear", shear_cycles)):
        for index, cycle in enumerate(cycles):
            if not isinstance(cycle, dict):
                return base | dict(
                    status="out_of_scope",
                    reason="Source cycle rows must be objects",
                    source_channel=channel,
                    source_cycle_index=index,
                )
            available = _finite_cycle_value(cycle, "count")
            if available is None or available <= 0:
                return base | dict(
                    status="out_of_scope",
                    reason="Every source cycle must have a finite positive count",
                    source_channel=channel,
                    source_cycle_index=index,
                )
            used = allocated.get((channel, index), 0.0)
            remaining = max(available - used, 0.0)
            if remaining > 1e-12 * max(1.0, available):
                unpaired_cycles.append(
                    dict(source_channel=channel, source_cycle_index=index, unallocated_cycle_count=remaining)
                )
    mapped_damage = math.fsum(row["miner_damage"] for row in pair_results)
    if unpaired_cycles:
        return base | dict(
            status="out_of_scope",
            reason="Not all selected normal-stress and shear-strain cycle counts have explicit pair allocations; aggregate damage withheld",
            pair_results=pair_results,
            mapped_pair_miner_damage=mapped_damage,
            unpaired_cycles=unpaired_cycles,
        )
    return base | dict(
        status="computed",
        pair_results=pair_results,
        total_miner_damage=mapped_damage,
        pairing_basis=dict(
            method_id=request.cycle_pairing_method_id,
            method_revision=request.cycle_pairing_method_revision,
            configuration_sha256=request.cycle_pairing_configuration_sha256,
            source_result_sha256=source_digest,
            plane_id=request.plane_id,
            normal_projection="normal_stress",
            shear_projection=request.shear_projection,
            calibration_material_condition_id=request.calibration_material_condition_id,
            calibration_sha256=request.calibration_sha256,
            pairing_proposal_sha256=request.pairing_proposal_sha256,
        ),
        notes=(
            "Cross-channel cycle mapping and count allocation are supplied explicitly by the caller; the calculation validates indices, prevents over-allocation, and withholds aggregate damage if either selected source channel has unpaired counts. It never infers temporal or physical pairing.",
            "Each mapped pair uses a caller-calibrated Fatemi-Socie engineering-shear strain-life relation within its declared cycle support. Linear Miner damage is an explicit accumulation assumption, not a failure probability, acceptance decision or validation result.",
        ),
    )
