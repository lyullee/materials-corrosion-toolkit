"""Evaluate a layered scale-diffusion bound at shared computed history knots."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, canonical_digest
from .models.scale_film_transport import LayeredScaleDiffusionLimit, layered_scale_diffusion_limit
from .registry import ModelSpec
from .scale_layer_stack_transport import ScaleLayerHistoryBinding


class LayeredScaleHistorySeriesTransport(Contract):
    """Bind distinct phase histories to layers and evaluate exact common knots."""

    schema_version: Literal["matintegrity.layered_scale_history_series_transport.v1"] = (
        "matintegrity.layered_scale_history_series_transport.v1"
    )
    transport_request: LayeredScaleDiffusionLimit
    layer_bindings: tuple[ScaleLayerHistoryBinding, ...] = Field(min_length=1, max_length=20)
    layer_history_order_and_phase_mapping_reviewed: bool
    common_scope_time_and_knot_alignment_reviewed: bool
    independent_quasi_steady_knot_interpretation_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_sources_and_knots(self):
        request = self.transport_request
        layers = request.layers
        layer_ids = [layer.layer_id for layer in layers]
        if len(set(layer_ids)) != len(layer_ids):
            raise ValueError("transport layer IDs must be unique")
        if len(self.layer_bindings) != len(layers):
            raise ValueError("provide exactly one scale history assessment per transport layer")
        binding_ids = [binding.layer_id for binding in self.layer_bindings]
        if len(set(binding_ids)) != len(binding_ids) or set(binding_ids) != set(layer_ids):
            raise ValueError("every transport layer must map to exactly one distinct scale history")
        if any(value is not None for value in (
            request.scale_history_result_digest,
            request.scale_history_time_s,
            request.scale_history_model_id,
            request.scale_history_phase_id,
            request.scale_history_layer_id,
            request.scale_history_covered_area_fraction,
            request.scale_history_mapping_reviewed,
        )):
            raise ValueError("base transport request must not carry a conflicting single-history lineage")

        identities = set()
        histories: list[dict[str, Any]] = []
        digests = set()
        for binding in self.layer_bindings:
            result = binding.scale_history_result
            if result.model_id != "chemistry.caller_surface_scale_kinetics" or result.status != "computed":
                raise ValueError("every layer requires a computed caller single-phase scale-thickness history")
            assessment_id = result.values.get("assessment_id")
            if not isinstance(assessment_id, str) or not assessment_id:
                raise ValueError("scale history result must retain its assessment ID in values")
            if assessment_id in {row["assessment_id"] for row in histories}:
                raise ValueError("scale history assessment IDs must be unique")
            result_digest = canonical_digest(result.model_dump(mode="json"))
            if result_digest in digests:
                raise ValueError("each transport layer requires a distinct scale history record")
            digests.add(result_digest)
            values = result.values
            if values.get("input_digest") != canonical_digest(result.inputs):
                raise ValueError("scale history result input digest does not match its request")
            for field, expected in (
                ("physical_scope_id", request.physical_scope_id),
                ("substrate_condition_id", request.substrate_condition_id),
                ("solution_condition_id", request.solution_condition_id),
            ):
                if values.get(field) != expected or result.inputs.get(field) != expected:
                    raise ValueError(f"scale history does not match stack {field}")
            phase_id = values.get("scale_phase_id")
            if not isinstance(phase_id, str) or not phase_id or phase_id != result.inputs.get("scale_phase_id"):
                raise ValueError("scale history phase identity must match its input")
            identity = (result.context.asset_id, result.context.location_id, result.context.time_basis)
            identities.add(identity)
            rows = values.get("scale_history")
            if not isinstance(rows, list) or not rows:
                raise ValueError("scale history must contain at least one knot")
            if len(rows) > 100000:
                raise ValueError("scale history exceeds the 100000-knot limit")
            times = [row.get("time_s") if isinstance(row, dict) else None for row in rows]
            if any(
                isinstance(time_s, bool)
                or not isinstance(time_s, (int, float))
                or not math.isfinite(time_s)
                or time_s < 0
                for time_s in times
            ) or any(right <= left for left, right in zip(times, times[1:])):
                raise ValueError("scale history knots must have finite nonnegative strictly increasing times")
            for row in rows:
                thickness = row.get("scale_thickness_m")
                if (
                    isinstance(thickness, bool)
                    or not isinstance(thickness, (int, float))
                    or not math.isfinite(thickness)
                    or thickness < 0
                ):
                    raise ValueError("every scale history knot must contain finite nonnegative thickness")
            histories.append({"assessment_id": assessment_id, "layer_id": binding.layer_id, "rows": rows})
        if len(identities) != 1:
            raise ValueError("phase histories must share asset, location and time-basis identity")
        baseline = [row.get("time_s") for row in histories[0]["rows"]]
        if any([row.get("time_s") for row in history["rows"]] != baseline for history in histories[1:]):
            raise ValueError("every scale history must supply the same exact ordered time knots")
        return self


def evaluate_layered_scale_history_series_transport(
    request: LayeredScaleHistorySeriesTransport,
) -> Calculation:
    """Evaluate the existing layered steady diffusion limit at each shared knot."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    reviews = {
        "layer_history_order_and_phase_mapping_reviewed": request.layer_history_order_and_phase_mapping_reviewed,
        "common_scope_time_and_knot_alignment_reviewed": request.common_scope_time_and_knot_alignment_reviewed,
        "independent_quasi_steady_knot_interpretation_reviewed": request.independent_quasi_steady_knot_interpretation_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    history_sources = [
        {
            "layer_id": binding.layer_id,
            "scale_phase_id": binding.scale_history_result.values["scale_phase_id"],
            "assessment_id": binding.scale_history_result.values["assessment_id"],
            "model_id": binding.scale_history_result.model_id,
            "result_sha256": canonical_digest(binding.scale_history_result.model_dump(mode="json")),
            "input_sha256": binding.scale_history_result.values["input_digest"],
            "source_ids": list(binding.scale_history_result.source_ids),
        }
        for binding in request.layer_bindings
    ]
    missing = [field for field, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values={
            "input_sha256": request_digest,
            "scale_history_sources": history_sources,
            "completed_knot_count": 0,
            "knots": [],
            "missing_reviews": missing,
            "time_interpolation": "not_performed_exact_shared_knots_only",
        })

    time_values = request.layer_bindings[0].scale_history_result.values["scale_history"]
    sources_by_layer = {binding.layer_id: binding.scale_history_result for binding in request.layer_bindings}
    knot_results = []
    status = "computed"
    for row_index, first_row in enumerate(time_values):
        time_s = float(first_row["time_s"])
        updated_layers = []
        knot_sources = []
        for layer in request.transport_request.layers:
            source = sources_by_layer[layer.layer_id]
            source_row = source.values["scale_history"][row_index]
            thickness = float(source_row["scale_thickness_m"])
            updated_layers.append(layer.model_copy(update={"thickness_m": thickness}))
            knot_sources.append({
                "layer_id": layer.layer_id,
                "scale_phase_id": source.values["scale_phase_id"],
                "scale_history_result_sha256": canonical_digest(source.model_dump(mode="json")),
                "scale_history_input_sha256": source.values["input_digest"],
                "scale_history_time_s": time_s,
                "scale_thickness_m": thickness,
            })
        data = request.transport_request.model_dump(mode="python")
        data["layers"] = [layer.model_dump(mode="python") for layer in updated_layers]
        data["scale_history_result_digest"] = None
        data["scale_history_time_s"] = None
        data["scale_history_model_id"] = None
        data["scale_history_phase_id"] = None
        data["scale_history_layer_id"] = None
        data["scale_history_covered_area_fraction"] = None
        data["scale_history_mapping_reviewed"] = None
        transport = LayeredScaleDiffusionLimit.model_validate(data)
        result = layered_scale_diffusion_limit(transport)
        record = {
            "time_s": time_s,
            "scale_layer_sources": knot_sources,
            "transport_request_sha256": canonical_digest(transport.model_dump(mode="json")),
            "transport_result": result.model_dump(mode="json"),
        }
        knot_results.append(record)
        if result.status != "computed":
            status = result.status
            break

    return Calculation(
        status=status,
        values={
            "input_sha256": request_digest,
            "scale_history_sources": history_sources,
            "completed_knot_count": sum(row["transport_result"]["status"] == "computed" for row in knot_results),
            "knots": knot_results,
            "time_interpolation": "not_performed_exact_shared_knots_only",
            "between_knot_transport": "not_evaluated",
            "temporal_coupling": "independent_quasi_steady_calculation_at_each_shared_scale_history_knot",
            "not_inferred": ["scale_phase_interactions", "moving_boundary_coupling", "corrosion_rate", "wall_loss", "acceptance", "failure_probability"],
        },
        notes=(
            "Each time knot is an independent application of the existing caller-configured layered diffusion bound using the exact source thicknesses.",
            "The time series does not model transient transport, phase creation or dissolution, inter-knot evolution, corrosion kinetics, wall loss or acceptance.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="chemistry.layered_scale_history_series_transport",
        input_type=LayeredScaleHistorySeriesTransport,
        evaluator=evaluate_layered_scale_history_series_transport,
        units={
            "scale_history_sources[].scale_thickness_m": "m",
            "knots[].time_s": "s",
            "knots[].transport_result.values.area_average_flux_limit_mol_m2_s": "mol/m^2/s",
        },
        assumptions=(
            "One digest-pinned, caller-calibrated thickness history is supplied for each ordered diffusion layer, with identical exact time knots and shared physical context.",
            "At each shared knot the existing layered steady diffusion-bound calculation is evaluated independently; no history interpolation or transient transport is performed.",
            "Phase-to-layer mapping, quasi-steady interpretation, common time/scope and computational-use rights are caller reviewed.",
            "No scale reaction, corrosion-rate, wall-loss, acceptance or qualification result is inferred.",
        ),
        source_ids=("caller_layered_scale_history_series_transport",),
        qualification="user_model",
    )]
