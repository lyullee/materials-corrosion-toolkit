"""Caller-calibrated gasket contact-pressure to leakage-flux mapping."""

from __future__ import annotations

import math
from bisect import bisect_left
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class GasketLeakageCalibrationRow(Contract):
    contact_pressure_Pa: Nonnegative
    molar_leak_flux_by_delta_pressure_mol_s_m2: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)


class GasketLeakageCalibrationMap(Contract):
    differential_pressure_Pa: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)
    rows: tuple[GasketLeakageCalibrationRow, ...] = Field(min_length=2, max_length=10000)

    @model_validator(mode="after")
    def rectangular_monotone_map(self):
        pressure = [row.contact_pressure_Pa for row in self.rows]
        delta = list(self.differential_pressure_Pa)
        if pressure[0] != 0 or any(b <= a for a, b in zip(pressure, pressure[1:])):
            raise ValueError("calibration contact-pressure knots must begin at zero and increase strictly")
        if delta[0] != 0 or any(b <= a for a, b in zip(delta, delta[1:])):
            raise ValueError("calibration differential-pressure knots must begin at zero and increase strictly")
        if any(len(row.molar_leak_flux_by_delta_pressure_mol_s_m2) != len(delta) for row in self.rows):
            raise ValueError("each calibration row must contain one leakage flux per pressure-difference knot")
        if len(pressure) * len(delta) > 2_000_000:
            raise ValueError("calibration table exceeds the two-million-cell contract budget")
        return self


class GasketLeakageHistory(Contract):
    schema_version: Literal["matintegrity.gasket_leakage_history.v1"] = "matintegrity.gasket_leakage_history.v1"
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    node_ids: tuple[str, ...] = Field(min_length=1)
    contact_area_m2: tuple[Positive, ...] = Field(min_length=1)
    mean_contact_pressure_history_Pa: tuple[tuple[Nonnegative, ...], ...] | None = None
    differential_pressure_history_Pa: tuple[Nonnegative, ...] = Field(min_length=2)
    calibration: GasketLeakageCalibrationMap
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    upstream_contact_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    contact_pressure_transfer_review_id: str = Field(min_length=1)
    differential_pressure_basis_review_id: str = Field(min_length=1)
    calibration_scope_review_id: str = Field(min_length=1)
    complete_contact_area_partition_reviewed: bool
    calibration_and_joint_match_reviewed: bool
    contact_field_and_leakage_basis_reviewed: bool
    pressure_direction_and_unit_reviewed: bool
    temporal_alignment_reviewed: bool
    refined_contact_time_interpolation_reviewed: bool = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    maximum_time_integration_subintervals: int = Field(default=100000, ge=1, le=10000000)

    @model_validator(mode="after")
    def aligned_history(self):
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:])):
            raise ValueError("leakage history times must increase strictly")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("contact node identifiers must be unique")
        n_time, n_node = len(self.time_s), len(self.node_ids)
        if len(self.contact_area_m2) != n_node:
            raise ValueError("contact areas must align with node identifiers")
        try:
            total_area = math.fsum(self.contact_area_m2)
        except OverflowError as error:
            raise ValueError("sum of contact areas must remain finite") from error
        if not math.isfinite(total_area):
            raise ValueError("sum of contact areas must remain finite")
        if self.mean_contact_pressure_history_Pa is not None and (
            len(self.mean_contact_pressure_history_Pa) != n_time or any(
                len(row) != n_node for row in self.mean_contact_pressure_history_Pa
            )
        ):
            raise ValueError("contact-pressure history must be time by contact node")
        if len(self.differential_pressure_history_Pa) != n_time:
            raise ValueError("differential-pressure history must align with the time knots")
        return self


class GasketLeakageNodePressureEnvelope(Contract):
    node_id: str = Field(min_length=1)
    contact_area_m2: Positive
    minimum_contact_pressure_Pa: Nonnegative
    maximum_contact_pressure_Pa: Nonnegative
    minimum_differential_pressure_Pa: Nonnegative
    maximum_differential_pressure_Pa: Nonnegative

    @model_validator(mode="after")
    def ordered_pressure_ranges(self):
        if self.maximum_contact_pressure_Pa < self.minimum_contact_pressure_Pa:
            raise ValueError("contact-pressure uncertainty bounds must be ordered")
        if self.maximum_differential_pressure_Pa < self.minimum_differential_pressure_Pa:
            raise ValueError("differential-pressure uncertainty bounds must be ordered")
        return self


class GasketLeakageRateEnvelope(Contract):
    schema_version: Literal["matintegrity.gasket_leakage_rate_envelope.v1"] = (
        "matintegrity.gasket_leakage_rate_envelope.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: Nonnegative
    calibration: GasketLeakageCalibrationMap
    nodes: tuple[GasketLeakageNodePressureEnvelope, ...] = Field(min_length=1, max_length=100000)
    maximum_corner_evaluations: int = Field(default=2_000_000, ge=1, le=10_000_000)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scope_transfer_and_uncertainty_bounds_reviewed: bool
    calibration_and_joint_match_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_nodes(self):
        node_ids = [row.node_id for row in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("gasket leakage envelope node IDs must be unique")
        return self


def _bracket(knots: tuple[float, ...], value: float) -> tuple[int, float]:
    if not math.isfinite(value) or value < knots[0] or value > knots[-1]:
        raise ValueError("requested contact state is outside the caller calibration support")
    index = min(max(bisect_left(knots, value) - 1, 0), len(knots) - 2)
    return index, (value - knots[index]) / (knots[index + 1] - knots[index])


def _calibrated_flux(
    calibration: GasketLeakageCalibrationMap,
    contact_pressure_knots_Pa: tuple[float, ...],
    contact_pressure_Pa: float,
    differential_pressure_Pa: float,
) -> tuple[float, int, int]:
    rows = calibration.rows
    pressure_index, pressure_fraction = _bracket(contact_pressure_knots_Pa, contact_pressure_Pa)
    delta_index, delta_fraction = _bracket(calibration.differential_pressure_Pa, differential_pressure_Pa)
    low_row, high_row = rows[pressure_index], rows[pressure_index + 1]
    q00 = low_row.molar_leak_flux_by_delta_pressure_mol_s_m2[delta_index]
    q01 = low_row.molar_leak_flux_by_delta_pressure_mol_s_m2[delta_index + 1]
    q10 = high_row.molar_leak_flux_by_delta_pressure_mol_s_m2[delta_index]
    q11 = high_row.molar_leak_flux_by_delta_pressure_mol_s_m2[delta_index + 1]
    low = q00 + delta_fraction * (q01 - q00)
    high = q10 + delta_fraction * (q11 - q10)
    flux = low + pressure_fraction * (high - low)
    if not math.isfinite(flux) or flux < 0.0:
        raise ValueError("interpolated leakage flux must be finite and nonnegative")
    return flux, pressure_index, delta_index


def evaluate_gasket_leakage_rate_envelope(x: GasketLeakageRateEnvelope) -> Calculation:
    """Bound a single-time aggregate rate over caller-declared pressure intervals.

    For each independent node rectangle, bilinear calibration extrema occur at
    rectangle corners within a calibration cell. Adding every crossed table
    knot partitions the domain into such cells and yields exact bounds for the
    declared interpolation. Node pressure ranges are treated independently.
    """
    calibration_digest = canonical_digest(x.calibration.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id,
        "time_s": x.time_s,
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "provider_configuration_sha256": x.provider_configuration_sha256,
        "calibration_record_sha256": x.calibration_record_sha256,
        "maximum_corner_evaluations": x.maximum_corner_evaluations,
        "calibration_map_sha256": calibration_digest,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "calibration_contact_pressure_support_Pa": [
            x.calibration.rows[0].contact_pressure_Pa,
            x.calibration.rows[-1].contact_pressure_Pa,
        ],
        "calibration_differential_pressure_support_Pa": [
            x.calibration.differential_pressure_Pa[0],
            x.calibration.differential_pressure_Pa[-1],
        ],
    }
    missing = [key for key, passed in {
        "scope_transfer_and_uncertainty_bounds_reviewed": x.scope_transfer_and_uncertainty_bounds_reviewed,
        "calibration_and_joint_match_reviewed": x.calibration_and_joint_match_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    contact_knots = tuple(row.contact_pressure_Pa for row in x.calibration.rows)
    delta_knots = x.calibration.differential_pressure_Pa
    node_rows = []
    lower_terms = []
    upper_terms = []
    corner_evaluation_count = 0
    try:
        for node in x.nodes:
            if (
                node.minimum_contact_pressure_Pa < contact_knots[0]
                or node.maximum_contact_pressure_Pa > contact_knots[-1]
                or node.minimum_differential_pressure_Pa < delta_knots[0]
                or node.maximum_differential_pressure_Pa > delta_knots[-1]
            ):
                raise ValueError(f"pressure uncertainty for node {node.node_id!r} exceeds calibration support")
            pressure_candidates = tuple(sorted({
                node.minimum_contact_pressure_Pa,
                node.maximum_contact_pressure_Pa,
                *(k for k in contact_knots if node.minimum_contact_pressure_Pa < k < node.maximum_contact_pressure_Pa),
            }))
            delta_candidates = tuple(sorted({
                node.minimum_differential_pressure_Pa,
                node.maximum_differential_pressure_Pa,
                *(k for k in delta_knots if node.minimum_differential_pressure_Pa < k < node.maximum_differential_pressure_Pa),
            }))
            required_evaluations = len(pressure_candidates) * len(delta_candidates)
            if corner_evaluation_count + required_evaluations > x.maximum_corner_evaluations:
                raise ValueError("exact leakage-envelope corners exceed the declared total evaluation budget")
            samples = []
            for pressure in pressure_candidates:
                for differential in delta_candidates:
                    flux, pressure_index, delta_index = _calibrated_flux(
                        x.calibration, contact_knots, pressure, differential
                    )
                    samples.append((flux, pressure, differential, pressure_index, delta_index))
            corner_evaluation_count += required_evaluations
            low = min(samples, key=lambda row: row[0])
            high = max(samples, key=lambda row: row[0])
            lower_rate = low[0] * node.contact_area_m2
            upper_rate = high[0] * node.contact_area_m2
            if not math.isfinite(lower_rate) or not math.isfinite(upper_rate):
                raise ValueError("area-weighted leakage envelope must be finite")
            lower_terms.append(lower_rate)
            upper_terms.append(upper_rate)
            node_rows.append({
                "node_id": node.node_id,
                "contact_area_m2": node.contact_area_m2,
                "minimum_calibrated_flux_mol_s_m2": low[0],
                "minimum_flux_witness_contact_pressure_Pa": low[1],
                "minimum_flux_witness_differential_pressure_Pa": low[2],
                "minimum_flux_interpolation_cell": {"contact_pressure_lower_index": low[3], "differential_pressure_lower_index": low[4]},
                "maximum_calibrated_flux_mol_s_m2": high[0],
                "maximum_flux_witness_contact_pressure_Pa": high[1],
                "maximum_flux_witness_differential_pressure_Pa": high[2],
                "maximum_flux_interpolation_cell": {"contact_pressure_lower_index": high[3], "differential_pressure_lower_index": high[4]},
                "minimum_molar_leak_rate_contribution_mol_s": lower_rate,
                "maximum_molar_leak_rate_contribution_mol_s": upper_rate,
                "candidate_pressure_pair_count": len(samples),
            })
        minimum_rate = math.fsum(lower_terms)
        maximum_rate = math.fsum(upper_terms)
        if not math.isfinite(minimum_rate) or not math.isfinite(maximum_rate):
            raise ValueError("aggregate leakage envelope exceeds finite floating-point range")
    except (ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error), "completed_nodes": node_rows})
    return Calculation(values=base | {
        "minimum_molar_leak_rate_mol_s": minimum_rate,
        "maximum_molar_leak_rate_mol_s": maximum_rate,
        "node_envelopes": node_rows,
        "corner_evaluation_count": corner_evaluation_count,
        "uncertainty_semantics": "independent_declared_contact_and_differential_pressure_intervals_per_node; calibration fixed",
        "extremum_method": "all_rectangular_subcell_corners_at_crossed_calibration_axis_knots",
        "calibration_interpolation": "piecewise_bilinear_without_extrapolation",
    }, notes=(
        "This is an exact range for the caller-declared independent pressure intervals and fixed bilinear table, not a probability distribution or statistical confidence interval.",
        "It does not include calibration measurement uncertainty, area uncertainty, correlations, temporal integration, leak-tightness acceptance or transfer to another joint.",
    ))


def _exact_piecewise_bilinear_interval_amount(
    calibration: GasketLeakageCalibrationMap,
    node_areas_m2: tuple[float, ...],
    pressure_start_Pa: tuple[float, ...],
    pressure_end_Pa: tuple[float, ...],
    delta_start_Pa: float,
    delta_end_Pa: float,
    duration_s: float,
    maximum_subintervals: int,
) -> tuple[float, tuple[float, ...]]:
    """Integrate area-weighted bilinear flux exactly along linear pressure paths.

    Splitting at every crossed calibration axis knot makes each flux segment
    quadratic or lower in time; Simpson's three-point rule is then exact.
    """
    if len(node_areas_m2) != len(pressure_start_Pa) or len(node_areas_m2) != len(pressure_end_Pa):
        raise ValueError("contact node areas and endpoint pressures must align")
    fractions = {0.0, 1.0}

    def add_crossings(start: float, end: float, knots: tuple[float, ...]) -> None:
        difference = end - start
        if difference == 0.0:
            return
        low, high = sorted((start, end))
        for knot in knots:
            if low < knot < high:
                fraction = (knot - start) / difference
                if 0.0 < fraction < 1.0:
                    fractions.add(fraction)

    contact_knots = tuple(row.contact_pressure_Pa for row in calibration.rows)
    for start, end in zip(pressure_start_Pa, pressure_end_Pa, strict=True):
        add_crossings(start, end, contact_knots)
    add_crossings(delta_start_Pa, delta_end_Pa, calibration.differential_pressure_Pa)
    ordered = tuple(sorted(fractions))
    if len(ordered) - 1 > maximum_subintervals:
        raise ValueError("calibration-axis crossings exceed the declared time-integration subinterval budget")

    def total_rate(fraction: float) -> float:
        delta = delta_start_Pa + fraction * (delta_end_Pa - delta_start_Pa)
        terms = []
        for area, start, end in zip(node_areas_m2, pressure_start_Pa, pressure_end_Pa, strict=True):
            pressure = start + fraction * (end - start)
            flux, _, _ = _calibrated_flux(calibration, contact_knots, pressure, delta)
            terms.append(area * flux)
        return math.fsum(terms)

    amounts = []
    for left, right in zip(ordered[:-1], ordered[1:], strict=True):
        middle = left + 0.5 * (right - left)
        amounts.append(duration_s * (right - left) / 6.0 * (
            total_rate(left) + 4.0 * total_rate(middle) + total_rate(right)
        ))
    return math.fsum(amounts), ordered


def evaluate_gasket_leakage_history(x: GasketLeakageHistory) -> Calculation:
    """Integrate a caller's calibrated local molar-leak flux over contact areas.

    Bilinear interpolation is performed in contact pressure and differential
    pressure. No extrapolation, seal acceptance or constitutive transfer is made.
    """
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id,
        "time_basis": x.time_basis,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "provider_configuration_sha256": x.provider_configuration_sha256,
        "calibration_record_sha256": x.calibration_record_sha256,
        "calibration_map_sha256": canonical_digest(x.calibration.model_dump(mode="json")),
        "upstream_contact_result_sha256": x.upstream_contact_result_sha256,
        "maximum_time_integration_subintervals": x.maximum_time_integration_subintervals,
        "refined_contact_time_interpolation_reviewed": x.refined_contact_time_interpolation_reviewed,
        "node_ids_sha256": canonical_digest(x.node_ids),
        "contact_area_sum_m2": math.fsum(x.contact_area_m2),
        "calibration_contact_pressure_support_Pa": [
            x.calibration.rows[0].contact_pressure_Pa,
            x.calibration.rows[-1].contact_pressure_Pa,
        ],
        "calibration_differential_pressure_support_Pa": [
            x.calibration.differential_pressure_Pa[0],
            x.calibration.differential_pressure_Pa[-1],
        ],
    }
    reviews = {
        "complete_contact_area_partition_reviewed": x.complete_contact_area_partition_reviewed,
        "calibration_and_joint_match_reviewed": x.calibration_and_joint_match_reviewed,
        "contact_field_and_leakage_basis_reviewed": x.contact_field_and_leakage_basis_reviewed,
        "pressure_direction_and_unit_reviewed": x.pressure_direction_and_unit_reviewed,
        "temporal_alignment_reviewed": x.temporal_alignment_reviewed,
    }
    missing = [name for name, passed in reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    if x.mean_contact_pressure_history_Pa is None:
        return Calculation(status="needs_data", values=base | {
            "missing_input": "mean_contact_pressure_history_Pa_or_flange_contact_history_adapter",
        })

    delta_knots = x.calibration.differential_pressure_Pa
    contact_knots = tuple(row.contact_pressure_Pa for row in x.calibration.rows)
    history = []
    try:
        for time_index, (time_s, differential) in enumerate(
            zip(x.time_s, x.differential_pressure_history_Pa, strict=True)
        ):
            _bracket(delta_knots, differential)
            node_results = []
            total = []
            for node_index, pressure in enumerate(x.mean_contact_pressure_history_Pa[time_index]):
                flux, pressure_index, delta_index = _calibrated_flux(
                    x.calibration, contact_knots, pressure, differential
                )
                contribution = flux * x.contact_area_m2[node_index]
                if not math.isfinite(contribution):
                    raise ValueError("node leakage-rate contribution must be finite")
                node_results.append({
                    "node_id": x.node_ids[node_index],
                    "contact_pressure_Pa": pressure,
                    "contact_area_m2": x.contact_area_m2[node_index],
                    "calibrated_molar_leak_flux_mol_s_m2": flux,
                    "molar_leak_rate_contribution_mol_s": contribution,
                    "interpolation_cell": {
                        "contact_pressure_lower_index": pressure_index,
                        "differential_pressure_lower_index": delta_index,
                    },
                })
                total.append(contribution)
            total_rate = math.fsum(total)
            if not math.isfinite(total_rate):
                raise ValueError("total leakage rate must be finite")
            history.append({
                "time_s": time_s,
                "differential_pressure_Pa": differential,
                "molar_leak_rate_mol_s": total_rate,
                "node_responses": node_results,
            })
    except (ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": str(error),
            "completed_time_knot_count": len(history),
            "completed_history": history,
        }, notes=("No interpolation or extrapolation outside the caller's calibration support is performed.",))

    interval_leak_amounts = []
    interval_integration = []
    integration_subinterval_count = 0
    try:
        for left, right in zip(history, history[1:]):
            amount, fractions = _exact_piecewise_bilinear_interval_amount(
                x.calibration,
                x.contact_area_m2,
                tuple(row["contact_pressure_Pa"] for row in left["node_responses"]),
                tuple(row["contact_pressure_Pa"] for row in right["node_responses"]),
                left["differential_pressure_Pa"],
                right["differential_pressure_Pa"],
                right["time_s"] - left["time_s"],
                x.maximum_time_integration_subintervals - integration_subinterval_count,
            )
            if not math.isfinite(amount) or amount < 0.0:
                raise ValueError("integrated leakage amount must be finite and nonnegative")
            interval_leak_amounts.append(amount)
            integration_subinterval_count += len(fractions) - 1
            interval_integration.append({
                "start_time_s": left["time_s"],
                "end_time_s": right["time_s"],
                "calibration_cell_crossing_fractions": list(fractions),
                "quadratic_or_lower_subinterval_count": len(fractions) - 1,
            })
    except (ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "time_history": history,
            "completed_interval_amount_count": len(interval_leak_amounts),
            "interval_molar_leak_amount_mol": interval_leak_amounts,
            "interval_integration": interval_integration,
            "integration_subinterval_count": integration_subinterval_count,
            "out_of_scope_reason": str(error),
        }, notes=("No interpolation or extrapolation outside the caller's calibration support is performed.",))
    try:
        cumulative_amount = math.fsum(interval_leak_amounts)
    except OverflowError:
        return Calculation(status="out_of_scope", values=base | {
            "time_history": history,
            "interval_molar_leak_amount_mol": interval_leak_amounts,
            "interval_integration": interval_integration,
            "integration_subinterval_count": integration_subinterval_count,
            "out_of_scope_reason": "cumulative leakage amount exceeds finite floating-point support",
        })
    if not math.isfinite(cumulative_amount):
        return Calculation(status="out_of_scope", values=base | {
            "time_history": history,
            "interval_molar_leak_amount_mol": interval_leak_amounts,
            "interval_integration": interval_integration,
            "integration_subinterval_count": integration_subinterval_count,
            "out_of_scope_reason": "cumulative leakage amount exceeds finite floating-point support",
        })
    return Calculation(values=base | {
        "time_history": history,
        "interval_molar_leak_amount_mol": interval_leak_amounts,
        "interval_integration": interval_integration,
        "integration_subinterval_count": integration_subinterval_count,
        "cumulative_molar_leak_amount_mol": cumulative_amount,
        "differential_pressure_history_interpolation": (
            "reviewed_piecewise_linear_from_original_request_knots"
            if x.refined_contact_time_interpolation_reviewed
            else "caller_supplied_at_contact_knots"
        ),
        "interpolation": "bilinear_in_contact_pressure_and_differential_pressure_without_extrapolation",
        "time_integration": "exact_simpson_on_axis_knot_split_intervals_for_bilinear_flux_and_linear_pressure_paths",
        "contact_area_integration": "piecewise_constant_node_area_with_sum_of_calibrated_local_molar_flux",
    }, notes=(
        "This API maps caller-provided contact-pressure histories through a joint-matched empirical leakage-flux table and integrates the local flux over declared node areas.",
        "It does not generate contact mechanics, infer calibration transfer, resolve flow through the gasket, establish leak-tightness acceptance, or qualify a sealing design.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_calibrated_leakage_history",
        GasketLeakageHistory,
        evaluate_gasket_leakage_history,
        {
            "time_s": "s", "contact_area_sum_m2": "m2",
            "calibration_contact_pressure_support_Pa": "Pa",
            "calibration_differential_pressure_support_Pa": "Pa",
            "time_history.differential_pressure_Pa": "Pa",
            "time_history.molar_leak_rate_mol_s": "mol/s",
            "time_history.node_responses.contact_pressure_Pa": "Pa",
            "time_history.node_responses.contact_area_m2": "m2",
            "time_history.node_responses.calibrated_molar_leak_flux_mol_s_m2": "mol/s/m2",
            "time_history.node_responses.molar_leak_rate_contribution_mol_s": "mol/s",
            "interval_molar_leak_amount_mol": "mol",
            "interval_integration[].start_time_s": "s",
            "interval_integration[].end_time_s": "s",
            "interval_integration[].calibration_cell_crossing_fractions[]": "1",
            "interval_integration[].quadratic_or_lower_subinterval_count": "count",
            "integration_subinterval_count": "count",
            "cumulative_molar_leak_amount_mol": "mol",
        },
        (
            "Caller-calibrated pressure-dependent leakage flux is evaluated at each contact node and integrated over its declared area for an aligned joint history. Piecewise-linear pressure paths are split at calibration-axis knots and integrated exactly by Simpson quadrature on each resulting quadratic-or-lower segment.",
            "Calibration transfer, between-knot contact evolution, leak-tightness criteria and sealing acceptance remain caller-owned.",
        ),
        ("caller_qualified_gasket_leakage_flux_calibration",),
    ), ModelSpec(
        "fabrication.gasket_calibrated_leakage_rate_envelope",
        GasketLeakageRateEnvelope,
        evaluate_gasket_leakage_rate_envelope,
        {
            "time_s": "s",
            "minimum_molar_leak_rate_mol_s": "mol/s",
            "maximum_molar_leak_rate_mol_s": "mol/s",
            "corner_evaluation_count": "count",
            "node_envelopes[].contact_area_m2": "m2",
            "node_envelopes[].minimum_calibrated_flux_mol_s_m2": "mol/s/m2",
            "node_envelopes[].maximum_calibrated_flux_mol_s_m2": "mol/s/m2",
            "node_envelopes[].minimum_molar_leak_rate_contribution_mol_s": "mol/s",
            "node_envelopes[].maximum_molar_leak_rate_contribution_mol_s": "mol/s",
            "node_envelopes[].minimum_flux_witness_contact_pressure_Pa": "Pa",
            "node_envelopes[].minimum_flux_witness_differential_pressure_Pa": "Pa",
            "node_envelopes[].maximum_flux_witness_contact_pressure_Pa": "Pa",
            "node_envelopes[].maximum_flux_witness_differential_pressure_Pa": "Pa",
        },
        (
            "Bound a caller-calibrated bilinear leakage flux at each node over independent declared contact-pressure and differential-pressure intervals. Partition each rectangle at every calibration-axis knot and inspect all subcell corners, which give the exact minimum and maximum for a bilinear surface on each cell; sum area-weighted node bounds.",
            "This is a deterministic envelope for the supplied fixed calibration and bounded pressures, not a probability distribution, correlated joint uncertainty model, temporal integral, sealing criterion or qualification.",
        ),
        ("caller_qualified_gasket_leakage_flux_calibration",),
    )]


def gasket_leakage_request_from_flange_contact_history(
    request: GasketLeakageHistory,
    contact_result: AssessmentResult | dict,
) -> GasketLeakageHistory:
    """Bind an assessed spatial gasket-contact history to its leakage request.

    Node order and time knots must match exactly. The leakage request remains the
    owner of contact areas, pressure history and calibration identities.
    """
    allowed_models = {
        "fabrication.flange_viscoelastic_contact_history",
        "fabrication.flange_nonlinear_viscoelastic_contact_history",
    }
    result = contact_result.model_dump(mode="json") if hasattr(contact_result, "model_dump") else contact_result
    if not isinstance(result, dict) or result.get("model_id") not in allowed_models:
        raise ValueError("upstream result must be an assessed supported flange contact-history model")
    if result.get("status") != "computed":
        raise ValueError("upstream flange contact history must have computed status")
    upstream_inputs = result.get("inputs")
    context = result.get("context")
    if not isinstance(upstream_inputs, dict) or not isinstance(context, dict):
        raise ValueError("upstream result must retain its original request and run context")
    expected_input_digest = canonical_digest({
        "model_id": result["model_id"],
        "model_version": result.get("model_version"),
        "inputs": upstream_inputs,
        "context": context,
    })
    if result.get("input_digest") != expected_input_digest:
        raise ValueError("upstream flange assessment input digest does not match its request and context")
    for field, expected in (
        ("joint_id", request.joint_id),
        ("physical_scope_id", request.physical_scope_id),
        ("node_ids", list(request.node_ids)),
        ("times_s", list(request.time_s)),
        ("gasket_contact_area_m2", list(request.contact_area_m2)),
    ):
        if upstream_inputs.get(field) != expected:
            raise ValueError(f"upstream flange contact {field} differs from the leakage request")
    result_values = result.get("values")
    if not isinstance(result_values, dict) or not isinstance(result_values.get("time_history"), list):
        raise ValueError("upstream contact result has no complete time_history")
    history = result_values["time_history"]
    if len(history) < 2:
        raise ValueError("upstream contact history must contain at least two complete knots")
    upstream_times = tuple(row.get("time_s") for row in history)
    if (
        any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in upstream_times
        )
        or any(right <= left for left, right in zip(upstream_times, upstream_times[1:]))
    ):
        raise ValueError("upstream contact history times must be finite and strictly increasing")
    if upstream_times[0] != request.time_s[0] or upstream_times[-1] != request.time_s[-1]:
        raise ValueError("upstream contact history must cover exactly the leakage request time endpoints")
    refined = upstream_times != request.time_s
    if refined and not request.refined_contact_time_interpolation_reviewed:
        raise ValueError("refined contact knots require reviewed linear interpolation of the differential-pressure history")
    pressure_times = request.time_s
    pressure_values = request.differential_pressure_history_Pa
    if refined:
        interpolated = []
        segment = 0
        for time_s in upstream_times:
            while segment < len(pressure_times) - 2 and time_s > pressure_times[segment + 1]:
                segment += 1
            left_time, right_time = pressure_times[segment], pressure_times[segment + 1]
            fraction = (time_s - left_time) / (right_time - left_time)
            interpolated.append(
                pressure_values[segment]
                + fraction * (pressure_values[segment + 1] - pressure_values[segment])
            )
        pressure_times = upstream_times
        pressure_values = tuple(interpolated)
    pressure_history = []
    for time_index, row in enumerate(history):
        field = row.get("response_field")
        if not isinstance(field, list) or tuple(item.get("node_id") for item in field) != request.node_ids:
            raise ValueError(f"upstream contact node order differs at knot {time_index}")
        if any("mean_contact_pressure_Pa" not in item for item in field):
            raise ValueError("upstream contact field lacks mean_contact_pressure_Pa")
        pressure_history.append(tuple(item["mean_contact_pressure_Pa"] for item in field))
    digest = canonical_digest(result)
    return GasketLeakageHistory.model_validate(request.model_dump(mode="python") | {
        "time_s": pressure_times,
        "differential_pressure_history_Pa": pressure_values,
        "mean_contact_pressure_history_Pa": tuple(pressure_history),
        "upstream_contact_result_sha256": digest,
    })
