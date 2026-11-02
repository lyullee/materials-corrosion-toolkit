"""Apply a digest-pinned wall-sink Arrhenius calibration to an exact temperature history."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_wall_sink_arrhenius_calibration import (
    CreviceWallSinkArrheniusCalibrationRequest,
    fit_crevice_wall_sink_arrhenius,
)
from .crevice_wall_sink_rate_history import (
    CreviceWallSinkRateHistoryRequest,
    evaluate_crevice_wall_sink_rate_history,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_calibrated_wall_sink_rate_history"
SOURCE_ID = "caller_crevice_wall_sink_calibration_application"
MAX_KNOTS = 5000


class CreviceCalibratedWallSinkHistoryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_calibrated_wall_sink_history.v1"] = (
        "matintegrity.crevice_calibrated_wall_sink_history.v1"
    )
    history_id: str = Field(min_length=1)
    calibration_request: CreviceWallSinkArrheniusCalibrationRequest
    calibration_result: dict
    calibration_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    elapsed_time_s: tuple[float, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    temperature_K: tuple[Positive, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    application_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    calibration_application_and_state_match_reviewed: bool
    output_condition_mapping_reviewed: bool
    first_order_irreversible_wall_law_application_reviewed: bool

    @model_validator(mode="after")
    def validate_lineage_and_clock(self):
        if canonical_digest(self.calibration_result) != self.calibration_result_sha256:
            raise ValueError("calibration result digest mismatch")
        if len(self.elapsed_time_s) != len(self.temperature_K):
            raise ValueError("temperature and elapsed-time knot counts must match")
        if any(right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:])):
            raise ValueError("application time knots must be strictly increasing")
        source_ids = [row.source_id for row in self.calibration_request.evidence + self.application_evidence]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("calibration and application Evidence source IDs must be unique")
        return self


def evaluate_crevice_calibrated_wall_sink_history(
    request: CreviceCalibratedWallSinkHistoryRequest,
) -> Calculation:
    """Validate a fitted law's provenance and evaluate its exact-knot rate history."""
    calibration = request.calibration_request
    calibration_result = request.calibration_result
    calibration_sha = request.calibration_result_sha256
    expected_calibration_input_sha = canonical_digest(calibration.model_dump(mode="json"))
    values = calibration_result.get("values") if isinstance(calibration_result, dict) else None
    if values is None and isinstance(calibration_result, dict):
        values = calibration_result
    base = {
        "history_id": request.history_id,
        "calibration_id": calibration.calibration_id,
        "calibration_request_sha256": expected_calibration_input_sha,
        "calibration_result_sha256": calibration_sha,
        "physical_scope_id": calibration.physical_scope_id,
        "material_condition_id": calibration.material_condition_id,
        "wall_surface_state_id": calibration.wall_surface_state_id,
        "fluid_chemistry_state_id": calibration.fluid_chemistry_state_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "geometry_id": request.geometry_id,
        "species_id": request.species_id,
        "condition_id": request.condition_id,
        "elapsed_time_s": list(request.elapsed_time_s),
        "temperature_K": list(request.temperature_K),
    }
    if calibration_result.get("status") != "computed" or not isinstance(values, dict):
        return Calculation(status="needs_data", values=base | {
            "reason": "a computed calibration result is required",
            "wall_rate_knots": [],
        })
    if any(not getattr(calibration, name) for name in (
        "observation_to_effective_wall_velocity_mapping_reviewed",
        "shared_surface_and_fluid_state_across_temperatures_reviewed",
        "calibration_holdout_partition_predeclared",
        "temperature_and_measurement_support_reviewed",
        "arrhenius_law_applicability_reviewed",
        "computational_use_and_data_rights_reviewed",
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "source calibration is missing one or more required review gates",
            "wall_rate_knots": [],
        })
    recomputed_calibration = fit_crevice_wall_sink_arrhenius(calibration)
    if recomputed_calibration.status != "computed":
        return Calculation(status="needs_data", values=base | {
            "reason": "source calibration request no longer yields a computed fit",
            "recomputed_calibration_status": recomputed_calibration.status,
            "wall_rate_knots": [],
        })
    if canonical_digest(recomputed_calibration.model_dump(mode="json")) != calibration_sha:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "supplied fit result differs from deterministic recalculation of its pinned observations",
            "wall_rate_knots": [],
        })
    if (
        values.get("calibration_id") != calibration.calibration_id
        or values.get("physical_scope_id") != calibration.physical_scope_id
        or values.get("input_sha256") != expected_calibration_input_sha
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "calibration result does not match its typed request and condition identity",
            "wall_rate_knots": [],
        })
    if not all((
        request.calibration_application_and_state_match_reviewed,
        request.output_condition_mapping_reviewed,
        request.first_order_irreversible_wall_law_application_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": [name for name in (
                "calibration_application_and_state_match_reviewed",
                "output_condition_mapping_reviewed",
                "first_order_irreversible_wall_law_application_reviewed",
            ) if not getattr(request, name)],
            "wall_rate_knots": [],
        })
    minimum_temperature = values.get("calibration_temperature_min_K")
    maximum_temperature = values.get("calibration_temperature_max_K")
    reference_rate = values.get("reference_wall_transfer_velocity_m_s")
    reference_temperature = values.get("reference_temperature_K")
    activation_energy = values.get("activation_energy_J_mol")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in (minimum_temperature, maximum_temperature, reference_rate, reference_temperature, activation_energy)
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "calibration result is missing finite Arrhenius parameters or support",
            "wall_rate_knots": [],
        })
    support_min = float(minimum_temperature)
    support_max = float(maximum_temperature)
    if any(not support_min <= temperature <= support_max for temperature in request.temperature_K):
        return Calculation(status="out_of_scope", values=base | {
            "temperature_support_K": [support_min, support_max],
            "unsupported_temperature_knots": [
                index for index, temperature in enumerate(request.temperature_K)
                if not support_min <= temperature <= support_max
            ],
            "wall_rate_knots": [],
            "complete_history_returned": False,
        })

    history_request = CreviceWallSinkRateHistoryRequest(
        history_id=request.history_id,
        asset_id=request.asset_id,
        location_id=request.location_id,
        geometry_id=request.geometry_id,
        species_id=request.species_id,
        condition_id=request.condition_id,
        elapsed_time_s=request.elapsed_time_s,
        temperature_K=request.temperature_K,
        reference_wall_transfer_velocity_m_s=float(reference_rate),
        activation_energy_J_mol=float(activation_energy),
        reference_temperature_K=float(reference_temperature),
        minimum_supported_temperature_K=support_min,
        maximum_supported_temperature_K=support_max,
        activation_parameter_and_use_reviewed=True,
        temperature_history_to_condition_mapping_reviewed=True,
        first_order_irreversible_wall_law_reviewed=True,
        evidence=calibration.evidence + request.application_evidence,
    )
    history = evaluate_crevice_wall_sink_rate_history(history_request)
    if history.status != "computed":
        return Calculation(status=history.status, values=base | {
            "temperature_support_K": [support_min, support_max],
            "wall_rate_history_status": history.status,
            "wall_rate_history_result": history.model_dump(mode="json"),
            "wall_rate_knots": [],
        })
    return Calculation(values=base | {
        "status": "computed",
        "calibration_fit_result_sha256": calibration_sha,
        "rate_history_request_sha256": canonical_digest(history_request.model_dump(mode="json")),
        "rate_history_result_sha256": canonical_digest(history.model_dump(mode="json")),
        "rate_history": history.model_dump(mode="json"),
        "wall_rate_knots": history.values.get("wall_rate_knots", []),
        "temperature_support_K": [support_min, support_max],
        "calibration_holdout_rmse_log_velocity": values.get("holdout_rmse_log_velocity"),
        "holdout_used_in_calibration_fit": False,
        "inter_knot_temperature_interpolation_performed": False,
        "interpretation_boundary": "This application reuses the calibrated effective wall-transfer velocity only at the supplied exact temperature knots. It does not solve wall concentration, transport, material loss or corrosion rate.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCalibratedWallSinkHistoryRequest,
        evaluator=evaluate_crevice_calibrated_wall_sink_history,
        units={
            "temperature_K[]": "K",
            "elapsed_time_s[]": "s",
            "wall_rate_knots[].wall_transfer_velocity_m_s": "m/s",
            "wall_rate_knots[].temperature_K": "K",
            "wall_rate_knots[].elapsed_time_s": "s",
            "calibration_holdout_rmse_log_velocity": "1",
        },
        assumptions=(
            "The calibration request/result pair is digest-bound and the computed fit's IDs, parameters and temperature support must match the supplied source request.",
            "Caller reviews that material, wall surface, fluid chemistry and geometry condition represented by the calibration are applicable to the requested history.",
            "Only exact supplied temperature knots are evaluated; every temperature must remain within calibration observation support.",
            "The existing first-order irreversible Arrhenius wall-sink evaluator is used; no calibration parameter is refit or modified by this bridge.",
            "The result is an effective transfer-velocity history, not a corrosion rate, penetration history, probability, acceptance or qualification claim.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
