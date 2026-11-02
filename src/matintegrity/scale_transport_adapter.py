"""Typed binding from a recorded uniform scale history knot to a layer input."""

from __future__ import annotations

import math

from pydantic import Field, PositiveFloat, model_validator

from .adapters import layered_scale_transport_request_from_history
from .contracts import AssessmentResult, Contract, Nonnegative, RunContext, canonical_digest
from .electrochemical_transport import ElectrochemicalTransport, solve_electrochemical_transport
from .models.scale_film_transport import LayeredScaleDiffusionLimit


class ScaleHistoryTransportLink(Contract):
    scale_history_result: AssessmentResult
    transport_request: LayeredScaleDiffusionLimit
    selected_time_s: Nonnegative
    scale_layer_id: str = Field(min_length=1)
    scale_state_to_layer_mapping_reviewed: bool
    coverage_characteristic_thickness_m: PositiveFloat | None = None
    coverage_shape_exponent: PositiveFloat | None = None
    thickness_to_coverage_relation_reviewed: bool = False

    @model_validator(mode="after")
    def paired_coverage_parameters(self):
        supplied = (
            self.coverage_characteristic_thickness_m is not None,
            self.coverage_shape_exponent is not None,
        )
        if any(supplied) != all(supplied):
            raise ValueError("coverage mapping requires both characteristic thickness and exponent")
        if any(supplied) != self.thickness_to_coverage_relation_reviewed:
            raise ValueError("coverage mapping parameters and explicit review must be supplied together")
        return self


class ScaleHistoryTransportSeriesLink(Contract):
    """Bind every recorded scale-history knot to a caller transport state."""

    scale_history_result: AssessmentResult
    transport_request: LayeredScaleDiffusionLimit
    scale_layer_id: str = Field(min_length=1)
    scale_state_to_layer_mapping_reviewed: bool
    coverage_characteristic_thickness_m: PositiveFloat | None = None
    coverage_shape_exponent: PositiveFloat | None = None
    thickness_to_coverage_relation_reviewed: bool = False

    @model_validator(mode="after")
    def paired_coverage_parameters(self):
        supplied = (
            self.coverage_characteristic_thickness_m is not None,
            self.coverage_shape_exponent is not None,
        )
        if any(supplied) != all(supplied):
            raise ValueError("coverage mapping requires both characteristic thickness and exponent")
        if any(supplied) != self.thickness_to_coverage_relation_reviewed:
            raise ValueError("coverage mapping parameters and explicit review must be supplied together")
        return self


class ScaleLimitedElectrochemicalHistorySegment(Contract):
    """One caller-defined transport interval with a fixed, digest-pinned scale state."""

    start_time_s: Nonnegative
    end_time_s: Nonnegative
    request: ElectrochemicalTransport

    @model_validator(mode="after")
    def interval_and_state(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("electrochemical segment end must follow its start")
        times = self.request.transport.output_times_s
        duration = self.end_time_s - self.start_time_s
        if times[0] != 0 or not math.isclose(times[-1], duration, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("segment transport clock must start at zero and end at the segment duration")
        bindings = tuple(
            row for row in (self.request.scale_limited_surface_flux, *self.request.additional_scale_limited_surface_fluxes)
            if row is not None
        )
        if not bindings:
            raise ValueError("every electrochemical history segment requires a pinned scale limiter")
        for binding in bindings:
            metadata = binding.scale_transport_result.context.metadata
            if metadata.get("scale_history_time_s") != self.start_time_s:
                raise ValueError("segment scale state must be evaluated at the exact segment start knot")
            scale_values = binding.scale_transport_result.values
            for field, expected in (
                ("scale_history_time_s", self.start_time_s),
                ("scale_state_id", binding.scale_state_id),
            ):
                if scale_values.get(field) != expected or metadata.get(field) != expected:
                    raise ValueError(f"scale transport context and result disagree on {field}")
            if scale_values.get("scale_history_result_digest") != metadata.get("scale_history_result_sha256"):
                raise ValueError("scale transport result and context disagree on the source scale-history digest")
        return self


class ScaleLimitedElectrochemicalHistory(Contract):
    """Sequentially solve explicit transport intervals against caller-pinned scale states."""

    campaign_id: str = Field(min_length=1)
    scale_history_result: AssessmentResult
    segments: tuple[ScaleLimitedElectrochemicalHistorySegment, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def contiguous_history_segments(self):
        source = self.scale_history_result
        if source.model_id not in {
            "chemistry.caller_surface_scale_kinetics",
            "chemistry.caller_scale_coverage_kinetics",
        } or source.status != "computed":
            raise ValueError("a computed caller scale-thickness or coverage history is required")
        source_input_digest = canonical_digest(source.inputs)
        source_assessment_digest = canonical_digest({
            "model_id": source.model_id,
            "model_version": source.model_version,
            "inputs": source.inputs,
            "context": source.context.model_dump(mode="json"),
        })
        if (
            source.values.get("input_digest") != source_input_digest
            or source.input_digest != source_assessment_digest
        ):
            raise ValueError("source scale-history assessment digests do not match its inputs and context")
        history = source.values.get("scale_history")
        if not isinstance(history, list) or not history:
            raise ValueError("scale history must contain recorded knots")
        knot_times = tuple(row.get("time_s") for row in history if isinstance(row, dict))
        if len(knot_times) != len(history) or any(
            isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) for t in knot_times
        ) or any(b <= a for a, b in zip(knot_times, knot_times[1:])):
            raise ValueError("scale history times must be finite and strictly increasing")
        if len(self.segments) != len(knot_times) - 1:
            raise ValueError("one electrochemical segment is required for each adjacent scale-history knot pair")
        for index, segment in enumerate(self.segments):
            if segment.start_time_s != knot_times[index] or segment.end_time_s != knot_times[index + 1]:
                raise ValueError("electrochemical intervals must exactly cover adjacent recorded scale knots")
            expected_digest = canonical_digest(source.model_dump(mode="json"))
            bindings = tuple(
                row for row in (segment.request.scale_limited_surface_flux, *segment.request.additional_scale_limited_surface_fluxes)
                if row is not None
            )
            for binding in bindings:
                metadata = binding.scale_transport_result.context.metadata
                if metadata.get("scale_history_result_sha256") != expected_digest:
                    raise ValueError("segment scale limiter is not linked to this exact scale-history result")
                scale_values = binding.scale_transport_result.values
                expected_lineage = {
                    "scale_history_result_digest": expected_digest,
                    "scale_history_model_id": source.model_id,
                    "scale_history_time_s": segment.start_time_s,
                }
                if any(scale_values.get(field) != value for field, value in expected_lineage.items()):
                    raise ValueError("segment scale-transport assessment does not match its source history knot")
                if scale_values.get("scale_state_id") != binding.scale_state_id:
                    raise ValueError("segment scale-transport assessment uses a different scale state ID")
        return self


def bind_scale_history_to_transport(link: ScaleHistoryTransportLink) -> LayeredScaleDiffusionLimit:
    """Bind one exact thickness or covered-area scale knot to a transport request."""
    return layered_scale_transport_request_from_history(
        link.scale_history_result,
        link.transport_request,
        selected_time_s=link.selected_time_s,
        scale_layer_id=link.scale_layer_id,
        scale_state_to_layer_mapping_reviewed=link.scale_state_to_layer_mapping_reviewed,
        coverage_characteristic_thickness_m=link.coverage_characteristic_thickness_m,
        coverage_shape_exponent=link.coverage_shape_exponent,
        thickness_to_coverage_relation_reviewed=link.thickness_to_coverage_relation_reviewed,
    )


def bind_scale_history_series_to_transport(
    link: ScaleHistoryTransportSeriesLink,
) -> tuple[LayeredScaleDiffusionLimit, ...]:
    """Bind all recorded scale knots; do not interpolate, reorder or skip knots."""
    result = link.scale_history_result
    if result.model_id not in {
        "chemistry.caller_surface_scale_kinetics",
        "chemistry.caller_scale_coverage_kinetics",
    } or result.status != "computed":
        raise ValueError("a computed caller scale-thickness or coverage result is required")
    history = result.values.get("scale_history")
    if not isinstance(history, list) or not history:
        raise ValueError("scale-kinetics result must contain a nonempty history")
    times = [row.get("time_s") if isinstance(row, dict) else None for row in history]
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
        for value in times
    ) or any(right <= left for left, right in zip(times, times[1:], strict=True)):
        raise ValueError("scale history knots must have finite strictly increasing times")
    return tuple(
        bind_scale_history_to_transport(
            ScaleHistoryTransportLink(
                scale_history_result=result,
                transport_request=link.transport_request,
                selected_time_s=time_s,
                scale_layer_id=link.scale_layer_id,
                scale_state_to_layer_mapping_reviewed=link.scale_state_to_layer_mapping_reviewed,
                coverage_characteristic_thickness_m=link.coverage_characteristic_thickness_m,
                coverage_shape_exponent=link.coverage_shape_exponent,
                thickness_to_coverage_relation_reviewed=link.thickness_to_coverage_relation_reviewed,
            )
        )
        for time_s in times
    )


def evaluate_scale_history_transport_series(
    link: ScaleHistoryTransportSeriesLink,
) -> dict:
    """Evaluate a steady diffusion-limit bound independently at every exact history knot."""
    requests = bind_scale_history_series_to_transport(link)
    source_result = link.scale_history_result
    result_digest = canonical_digest(source_result.model_dump(mode="json"))
    input_digest = canonical_digest(link.model_dump(mode="json"))
    provenance = {
        key: source_result.values.get(key)
        for key in (
            "provider_id",
            "provider_revision",
            "source_sha256",
            "condition_sha256",
            "kinetic_configuration_sha256",
        )
    }
    base = {
        "input_sha256": input_digest,
        "scale_history_result_sha256": result_digest,
        "scale_history_source_ids": list(source_result.source_ids),
        "scale_history_provenance": provenance,
        "physical_scope_id": link.transport_request.physical_scope_id,
        "substrate_condition_id": link.transport_request.substrate_condition_id,
        "solution_condition_id": link.transport_request.solution_condition_id,
        "scale_phase_id": link.transport_request.scale_phase_id,
        "scale_layer_id": link.scale_layer_id,
        "transport_configuration_sha256": link.transport_request.transport_configuration_sha256,
    }
    rows = []
    from .registry import default_registry

    registry = default_registry()
    for history_row, transport_request in zip(
        link.scale_history_result.values["scale_history"], requests, strict=True
    ):
        source_context = source_result.context
        context = RunContext(
            asset_id=source_context.asset_id,
            location_id=source_context.location_id,
            time_basis=source_context.time_basis,
            evidence=source_context.evidence,
            metadata=source_context.metadata
            | {
                "scale_history_result_sha256": result_digest,
                "scale_history_time_s": history_row["time_s"],
                "scale_state_id": transport_request.scale_state_id,
            },
        )
        assessment = registry.run("chemistry.layered_scale_diffusion_limit", transport_request, context)
        assessment_digest = canonical_digest(assessment.model_dump(mode="json"))
        row = {
            "time_s": history_row["time_s"],
            "scale_thickness_m": history_row.get("scale_thickness_m"),
            "scale_history_covered_area_fraction": history_row.get("covered_area_fraction"),
            "transport_covered_area_fraction": transport_request.covered_area_fraction,
            "scale_state_id": transport_request.scale_state_id,
            "transport_request_sha256": canonical_digest(transport_request.model_dump(mode="json")),
            "assessment_result_sha256": assessment_digest,
            "assessment_result": assessment.model_dump(mode="json"),
            "status": assessment.status,
        }
        if assessment.status != "computed":
            return {
                **base,
                "status": assessment.status,
                "completed_prefix": rows,
                "unresolved_time_s": history_row["time_s"],
                "reason": "one or more knotwise diffusion-bound calculations are incomplete",
            }
        rows.append(row)
    return {
        **base,
        "status": "computed",
        "scale_history_model_id": link.scale_history_result.model_id,
        "series_basis": "independent_steady_layered_diffusion_limit_at_exact_caller_scale_or_coverage_history_knots",
        "series": rows,
        "notes": [
            "This is a sequence of independent steady diffusion-limit bounds, not transient transport or a corrosion-rate prediction.",
            "No between-knot interpolation, scale evolution, charge-balance solution or protection factor is inferred.",
        ],
    }


def evaluate_scale_limited_electrochemical_history(
    campaign: ScaleLimitedElectrochemicalHistory,
    *,
    segment_callbacks: tuple[dict, ...] | None = None,
) -> dict:
    """Solve adjacent caller scale-history intervals in order, stopping at the first incomplete solve.

    Each interval uses its own reviewed electrochemical request and scale assessment. Python callbacks,
    when needed, are supplied as one kwargs mapping per interval and are never serialized or inferred.
    No result from an electrochemical interval modifies a later scale state.
    """
    if segment_callbacks is not None and len(segment_callbacks) != len(campaign.segments):
        raise ValueError("callback mappings must contain exactly one entry per segment")
    source_digest = canonical_digest(campaign.scale_history_result.model_dump(mode="json"))
    rows = []
    for index, segment in enumerate(campaign.segments):
        callbacks = {} if segment_callbacks is None else dict(segment_callbacks[index])
        allowed = {"wall_surface_flux", "activity_coefficients", "phase_transport", "axial_advection_velocity"}
        if set(callbacks) - allowed:
            raise ValueError("segment callback mapping contains unsupported solver arguments")
        result = solve_electrochemical_transport(segment.request, **callbacks)
        row = {
            "segment_index": index,
            "absolute_start_time_s": segment.start_time_s,
            "absolute_end_time_s": segment.end_time_s,
            "relative_output_times_s": list(segment.request.transport.output_times_s),
            "electrochemical_request_sha256": canonical_digest(segment.request.model_dump(mode="json")),
            "scale_state_ids": [
                binding.scale_state_id
                for binding in (segment.request.scale_limited_surface_flux, *segment.request.additional_scale_limited_surface_fluxes)
                if binding is not None
            ],
            "scale_transport_result_sha256": [
                binding.scale_transport_result_sha256
                for binding in (segment.request.scale_limited_surface_flux, *segment.request.additional_scale_limited_surface_fluxes)
                if binding is not None
            ],
            "scale_state_lineage": [
                {
                    "scale_state_id": binding.scale_state_id,
                    "scale_transport_result_sha256": binding.scale_transport_result_sha256,
                    "scale_history_model_id": binding.scale_transport_result.values.get("scale_history_model_id"),
                    "scale_history_time_s": binding.scale_transport_result.values.get("scale_history_time_s"),
                    "scale_layer_id": binding.scale_transport_result.values.get("scale_history_layer_id"),
                    "scale_history_covered_area_fraction": binding.scale_transport_result.values.get(
                        "scale_history_covered_area_fraction"
                    ),
                }
                for binding in (
                    segment.request.scale_limited_surface_flux,
                    *segment.request.additional_scale_limited_surface_fluxes,
                )
                if binding is not None
            ],
            "status": result.get("status", "needs_data"),
            "result": result,
        }
        if row["status"] != "computed":
            return {
                "campaign_id": campaign.campaign_id,
                "status": row["status"],
                "scale_history_result_sha256": source_digest,
                "completed_prefix": rows,
                "unresolved_segment_index": index,
                "unresolved_time_interval_s": [segment.start_time_s, segment.end_time_s],
                "reason": "an electrochemical segment did not produce a computed result; later segments were not run",
            }
        rows.append(row)
    return {
        "campaign_id": campaign.campaign_id,
        "status": "computed",
        "scale_history_result_sha256": source_digest,
        "segment_count": len(rows),
        "segments": rows,
        "coupling_basis": "caller_scale_state_fixed_per_adjacent_history_interval_one_way_to_electrochemical_transport",
        "notes": [
            "Each interval uses a fixed scale state pinned at its starting history knot.",
            "Scale evolution is supplied by the caller history; electrochemical results do not update or predict it.",
            "This campaign does not infer corrosion rate, remaining life, protection factor or failure probability.",
        ],
    }
