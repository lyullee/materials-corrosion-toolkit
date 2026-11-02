"""Bind synchronized caller scale-thickness histories into an ordered layer stack."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Nonnegative, canonical_digest
from .models.scale_film_transport import LayeredScaleDiffusionLimit, layered_scale_diffusion_limit
from .registry import ModelSpec


class ScaleLayerHistoryBinding(Contract):
    """Map one computed single-phase thickness history to one named transport layer."""

    layer_id: str = Field(min_length=1)
    scale_history_result: AssessmentResult


class LayeredScaleHistoryStackTransport(Contract):
    """Evaluate a layered diffusion bound using one exact, shared scale-history time."""

    schema_version: Literal["matintegrity.layered_scale_history_stack_transport.v1"] = (
        "matintegrity.layered_scale_history_stack_transport.v1"
    )
    transport_request: LayeredScaleDiffusionLimit
    selected_time_s: Nonnegative
    layer_bindings: tuple[ScaleLayerHistoryBinding, ...] = Field(min_length=1, max_length=20)
    layer_order_and_phase_mapping_reviewed: bool
    common_scope_and_time_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_layer_stack(self):
        request = self.transport_request
        layer_ids = [layer.layer_id for layer in request.layers]
        binding_ids = [binding.layer_id for binding in self.layer_bindings]
        if len(set(layer_ids)) != len(layer_ids):
            raise ValueError("transport layer IDs must be unique")
        if len(set(binding_ids)) != len(binding_ids):
            raise ValueError("each scale-history layer mapping must be unique")
        if set(binding_ids) != set(layer_ids):
            raise ValueError("every declared transport layer must map to exactly one phase history")
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
        result_digests = set()
        for binding in self.layer_bindings:
            result = binding.scale_history_result
            if result.model_id != "chemistry.caller_surface_scale_kinetics" or result.status != "computed":
                raise ValueError("each layer requires a computed single-phase scale-thickness result")
            values = result.values
            result_digest = canonical_digest(result.model_dump(mode="json"))
            if result_digest in result_digests:
                raise ValueError("each layer must bind a distinct scale-history result record")
            result_digests.add(result_digest)
            if values.get("input_digest") != canonical_digest(result.inputs):
                raise ValueError("scale-history result input digest does not match its request")
            for field, expected in (
                ("physical_scope_id", request.physical_scope_id),
                ("substrate_condition_id", request.substrate_condition_id),
                ("solution_condition_id", request.solution_condition_id),
            ):
                if values.get(field) != expected or result.inputs.get(field) != expected:
                    raise ValueError(f"scale-history result does not match the stack {field}")
            if values.get("scale_phase_id") != result.inputs.get("scale_phase_id"):
                raise ValueError("scale phase identity must match between result and input")
            phase_id = values.get("scale_phase_id")
            if not isinstance(phase_id, str) or not phase_id:
                raise ValueError("each scale history must declare its phase identity")
            identity = (result.context.asset_id, result.context.location_id, result.context.time_basis)
            identities.add(identity)
            history = values.get("scale_history")
            if not isinstance(history, list) or not history:
                raise ValueError("scale history must contain recorded knots")
            selected = [row for row in history if isinstance(row, dict) and row.get("time_s") == self.selected_time_s]
            if len(selected) != 1:
                raise ValueError("the selected stack time must match exactly one knot in every phase history")
            thickness = selected[0].get("scale_thickness_m")
            if isinstance(thickness, bool) or not isinstance(thickness, (int, float)) or not math.isfinite(thickness) or thickness < 0:
                raise ValueError("selected scale thickness must be finite and nonnegative")
        if len(identities) != 1:
            raise ValueError("phase histories must share one asset, location and time basis")
        return self


def evaluate_layered_scale_history_stack_transport(
    request: LayeredScaleHistoryStackTransport,
) -> Calculation:
    """Substitute exact phase thickness knots and evaluate the existing layered bound."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    bindings = {row.layer_id: row.scale_history_result for row in request.layer_bindings}
    source_rows = []
    updated_layers = []
    for layer in request.transport_request.layers:
        result = bindings[layer.layer_id]
        result_digest = canonical_digest(result.model_dump(mode="json"))
        history = result.values["scale_history"]
        selected = next(row for row in history if row["time_s"] == request.selected_time_s)
        updated_layers.append(layer.model_copy(update={"thickness_m": float(selected["scale_thickness_m"])}))
        source_rows.append({
            "layer_id": layer.layer_id,
            "scale_phase_id": result.values["scale_phase_id"],
            "scale_history_model_id": result.model_id,
            "scale_history_result_sha256": result_digest,
            "scale_history_input_sha256": result.values["input_digest"],
            "scale_history_time_s": request.selected_time_s,
            "scale_thickness_m": float(selected["scale_thickness_m"]),
        })

    if not all((
        request.layer_order_and_phase_mapping_reviewed,
        request.common_scope_and_time_reviewed,
        request.computational_use_authorized,
    )):
        return Calculation(status="needs_data", values={
            "input_sha256": request_digest,
            "selected_time_s": request.selected_time_s,
            "scale_layer_sources": source_rows,
            "missing_reviews": [
                key for key in (
                    "layer_order_and_phase_mapping_reviewed",
                    "common_scope_and_time_reviewed",
                    "computational_use_authorized",
                ) if not getattr(request, key)
            ],
        })

    data = request.transport_request.model_dump(mode="python")
    data["layers"] = [layer.model_dump(mode="python") for layer in updated_layers]
    transport = LayeredScaleDiffusionLimit.model_validate(data)
    result = layered_scale_diffusion_limit(transport)
    return Calculation(
        status=result.status,
        values={
            "input_sha256": request_digest,
            "transport_request_sha256": canonical_digest(transport.model_dump(mode="json")),
            "selected_time_s": request.selected_time_s,
            "scale_layer_sources": source_rows,
            "layered_diffusion_result": result.model_dump(mode="json"),
            "history_binding_semantics": "exact_shared_output_knot_per_phase; no temporal interpolation",
        },
        notes=(
            "The adapter requires one exact matching scale-thickness history knot for every ordered transport layer.",
            "Each phase history and phase-to-layer mapping remains separately digest-pinned; no phase discovery, co-precipitation, or between-knot scale evolution is inferred.",
        ) + result.notes,
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.layered_scale_history_stack_transport",
        LayeredScaleHistoryStackTransport,
        evaluate_layered_scale_history_stack_transport,
        {
            "selected_time_s": "s",
            "layered_diffusion_result.values.area_average_flux_limit_mol_m2_s": "mol/m^2/s",
            "scale_layer_sources[].scale_thickness_m": "m",
        },
        (
            "Bind one exact common time knot from a distinct caller-calibrated single-phase thickness history into every named layer of an ordered transport stack.",
            "The resulting layered diffusion bound retains the digest of each phase history and requires reviewed phase-to-layer ordering; it does not discover phases or infer kinetic interactions.",
        ),
        ("layered_scale_history_stack_assembly",),
        qualification="user_model",
    )]
