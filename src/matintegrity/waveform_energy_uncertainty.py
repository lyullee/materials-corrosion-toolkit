"""First-order covariance propagation for measured welding waveform energy."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .models.fabrication import WaveformEnergy, waveform_energy
from .registry import ModelSpec

MODEL_ID = "welding.waveform_energy_uncertainty"
SOURCE_ID = "caller_covariance_for_waveform_heat_input_uncertainty"
MAXIMUM_WAVEFORM_SAMPLES = 256
MAXIMUM_COVARIANCE_DIMENSION = 2 * MAXIMUM_WAVEFORM_SAMPLES + 2


def _coordinate_order(sample_count: int) -> tuple[str, ...]:
    return (
        *(f"voltage_V[{index}]" for index in range(sample_count)),
        *(f"current_A[{index}]" for index in range(sample_count)),
        "efficiency",
        "travel_distance_m",
    )


def _coordinate_units(sample_count: int) -> tuple[str, ...]:
    return (*("V" for _ in range(sample_count)), *("A" for _ in range(sample_count)), "1", "m")


def waveform_energy_covariance_digest(
    waveform: WaveformEnergy,
    coordinate_order: tuple[str, ...],
    coordinate_unit_tokens: tuple[str, ...],
    covariance_matrix: tuple[tuple[float, ...], ...],
    source_id: str,
    provider_revision: str,
    record_id: str,
) -> str:
    """Digest the pinned waveform, covariance coordinate basis and complete matrix."""
    return canonical_digest(
        {
            "source_id": source_id,
            "provider_revision": provider_revision,
            "record_id": record_id,
            "waveform_sha256": canonical_digest(waveform.model_dump(mode="json")),
            "coordinate_order": list(coordinate_order),
            "coordinate_unit_tokens": list(coordinate_unit_tokens),
            "covariance_matrix": [list(row) for row in covariance_matrix],
        }
    )


class WaveformEnergyUncertainty(Contract):
    """Waveform heat-input request and caller-pinned covariance for first-order propagation."""

    schema_version: Literal["matintegrity.welding_waveform_energy_uncertainty.v1"] = (
        "matintegrity.welding_waveform_energy_uncertainty.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    waveform: WaveformEnergy
    covariance_coordinate_order: tuple[str, ...] = Field(
        min_length=6, max_length=MAXIMUM_COVARIANCE_DIMENSION
    )
    covariance_coordinate_unit_tokens: tuple[str, ...] = Field(
        min_length=6, max_length=MAXIMUM_COVARIANCE_DIMENSION
    )
    input_covariance: tuple[
        tuple[float, ...], ...
    ] = Field(min_length=6, max_length=MAXIMUM_COVARIANCE_DIMENSION)
    covariance_source_id: str = Field(min_length=1, max_length=160)
    covariance_provider_revision: str = Field(min_length=1, max_length=160)
    covariance_record_id: str = Field(min_length=1, max_length=160)
    covariance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    covariance_usage_license_id: str = Field(min_length=1, max_length=160)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    covariance_order_and_units_reviewed: bool
    waveform_clock_treated_exact_reviewed: bool
    first_order_linearization_and_local_support_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_covariance_basis(self):
        sample_count = len(self.waveform.time_s)
        if sample_count > MAXIMUM_WAVEFORM_SAMPLES:
            raise ValueError(
                f"full covariance supports at most {MAXIMUM_WAVEFORM_SAMPLES} waveform samples"
            )
        if any(
            not math.isfinite(value)
            for values in (self.waveform.time_s, self.waveform.voltage_V, self.waveform.current_A)
            for value in values
        ):
            raise ValueError("waveform time, voltage and current values must be finite")
        expected_order = _coordinate_order(sample_count)
        expected_units = _coordinate_units(sample_count)
        if self.covariance_coordinate_order != expected_order:
            raise ValueError("covariance coordinates must follow voltage samples, current samples, efficiency, distance")
        if self.covariance_coordinate_unit_tokens != expected_units:
            raise ValueError("covariance coordinate unit tokens do not match the declared waveform basis")

        dimension = len(expected_order)
        if len(self.input_covariance) != dimension or any(
            len(row) != dimension for row in self.input_covariance
        ):
            raise ValueError("full covariance matrix must align with every ordered waveform input coordinate")
        if any(not math.isfinite(value) for row in self.input_covariance for value in row):
            raise ValueError("covariance entries must be finite")
        _validate_covariance(self.input_covariance)

        expected_digest = waveform_energy_covariance_digest(
            self.waveform,
            self.covariance_coordinate_order,
            self.covariance_coordinate_unit_tokens,
            self.input_covariance,
            self.covariance_source_id,
            self.covariance_provider_revision,
            self.covariance_record_id,
        )
        if expected_digest != self.covariance_sha256:
            raise ValueError("covariance digest must bind waveform, record identity, ordered units and full matrix")
        if not any(
            item.source_id == self.covariance_source_id
            and item.sha256 == self.covariance_sha256
            and item.license_id == self.covariance_usage_license_id
            for item in self.evidence
        ):
            raise ValueError("Evidence must bind the covariance provider, digest and computational-use license")
        return self


def _validate_covariance(matrix: tuple[tuple[float, ...], ...]) -> None:
    dimension = len(matrix)
    variances = [matrix[index][index] for index in range(dimension)]
    if any(value < 0.0 for value in variances):
        raise ValueError("covariance diagonal variances cannot be negative")
    scales = [math.sqrt(value) for value in variances]
    correlation = [[0.0] * dimension for _ in range(dimension)]
    for i in range(dimension):
        for j in range(dimension):
            left, right = matrix[i][j], matrix[j][i]
            covariance_scale = scales[i] * scales[j]
            symmetry_tolerance = 1e-10 * max(covariance_scale, abs(left), abs(right), 1e-300)
            if abs(left - right) > symmetry_tolerance:
                raise ValueError("covariance matrix must be symmetric within scale-aware tolerance")
            if scales[i] == 0.0 or scales[j] == 0.0:
                if abs(left) > 1e-300:
                    raise ValueError("zero-variance coordinates must have zero covariance with other coordinates")
            else:
                correlation[i][j] = 0.5 * (left + right) / covariance_scale

    # The correlation matrix is dimensionless, avoiding PSD tolerances across mixed units.
    try:
        import numpy as np
    except ImportError as exc:
        raise ValueError("NumPy is required for full covariance positive-semidefinite validation") from exc
    eigenvalues = np.linalg.eigvalsh(np.asarray(correlation, dtype=float))
    if not np.isfinite(eigenvalues).all() or float(eigenvalues[0]) < -1e-10:
        raise ValueError("covariance matrix must be positive semidefinite")


def evaluate_waveform_energy_uncertainty(request: WaveformEnergyUncertainty) -> Calculation:
    """Propagate voltage/current/efficiency/distance covariance through waveform energy."""
    waveform = request.waveform
    waveform_sha256 = canonical_digest(waveform.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "waveform_sha256": waveform_sha256,
        "covariance_sha256": request.covariance_sha256,
        "covariance_source_id": request.covariance_source_id,
        "covariance_provider_revision": request.covariance_provider_revision,
        "covariance_record_id": request.covariance_record_id,
        "covariance_usage_license_id": request.covariance_usage_license_id,
        "covariance_evidence_source_ids": [item.source_id for item in request.evidence],
        "covariance_coordinate_order": list(request.covariance_coordinate_order),
        "covariance_coordinate_unit_tokens": list(request.covariance_coordinate_unit_tokens),
    }
    reviews = {
        "covariance_order_and_units_reviewed": request.covariance_order_and_units_reviewed,
        "waveform_clock_treated_exact_reviewed": request.waveform_clock_treated_exact_reviewed,
        "first_order_linearization_and_local_support_reviewed": request.first_order_linearization_and_local_support_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    nominal = waveform_energy(waveform)
    if nominal.status != "computed":
        return Calculation(
            status=nominal.status,
            values=base | {"nominal_status": nominal.status, "nominal_values": nominal.values},
            notes=nominal.notes,
        )

    time = waveform.time_s
    voltage = waveform.voltage_V
    current = waveform.current_A
    sample_count = len(time)
    weights = [0.0] * sample_count
    weights[0] = 0.5 * (time[1] - time[0])
    weights[-1] = 0.5 * (time[-1] - time[-2])
    for index in range(1, sample_count - 1):
        weights[index] = 0.5 * (time[index + 1] - time[index - 1])

    energy = math.fsum(
        weights[index] * voltage[index] * current[index] for index in range(sample_count)
    )
    efficiency = waveform.efficiency
    distance = waveform.travel_distance_m
    net_heat_input = efficiency * energy / distance
    energy_gradient = [
        *(weights[index] * current[index] for index in range(sample_count)),
        *(weights[index] * voltage[index] for index in range(sample_count)),
        0.0,
        0.0,
    ]
    heat_gradient = [
        *(efficiency / distance * value for value in energy_gradient[: 2 * sample_count]),
        energy / distance,
        -efficiency * energy / (distance * distance),
    ]

    energy_variance = _quadratic_form(energy_gradient, request.input_covariance)
    heat_variance = _quadratic_form(heat_gradient, request.input_covariance)
    if energy_variance is None or heat_variance is None:
        return Calculation(status="out_of_scope", values=base | {"reason": "nonfinite_covariance_propagation"})
    energy_uncertainty = math.sqrt(energy_variance)
    heat_uncertainty = math.sqrt(heat_variance)
    return Calculation(
        values=base
        | {
            "arc_energy_J": energy,
            "net_heat_input_J_m": net_heat_input,
            "arc_energy_standard_uncertainty_J": energy_uncertainty,
            "net_heat_input_standard_uncertainty_J_m": heat_uncertainty,
            "arc_energy_variance_J2": energy_variance,
            "net_heat_input_variance_J2_m2": heat_variance,
            "sample_count": sample_count,
            "uncertainty_method": "first_order_covariance_delta_method_over_trapezoid_waveform_integral",
            "uncertainty_meaning": "caller covariance propagated locally; no probability distribution or confidence level is implied",
            "qualification_claimed": False,
        },
        notes=(
            "The sample clock is treated as exact; timing uncertainty is not propagated.",
            "Standard uncertainty is a local first-order approximation and is not a probability or acceptance statement.",
            "The caller remains responsible for waveform calibration, arc-efficiency applicability and travel-distance metrology.",
        ),
    )


def _quadratic_form(gradient: list[float], covariance: tuple[tuple[float, ...], ...]) -> float | None:
    terms = (
        gradient[i] * covariance[i][j] * gradient[j]
        for i in range(len(gradient))
        for j in range(len(gradient))
    )
    variance = math.fsum(terms)
    magnitude = math.fsum(
        abs(gradient[i] * covariance[i][j] * gradient[j])
        for i in range(len(gradient))
        for j in range(len(gradient))
    )
    if not math.isfinite(variance) or not math.isfinite(magnitude):
        return None
    tolerance = 1e-12 * max(magnitude, 1e-300)
    if variance < -tolerance:
        return None
    return max(variance, 0.0)


def specifications() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            model_id=MODEL_ID,
            input_type=WaveformEnergyUncertainty,
            evaluator=evaluate_waveform_energy_uncertainty,
            units={
                "arc_energy_J": "J",
                "net_heat_input_J_m": "J/m",
                "arc_energy_standard_uncertainty_J": "J",
                "net_heat_input_standard_uncertainty_J_m": "J/m",
                "arc_energy_variance_J2": "J^2",
                "net_heat_input_variance_J2_m2": "J^2/m^2",
                "sample_count": "1",
                "qualification_claimed": "1",
            },
            assumptions=(
                "The full covariance follows the fixed coordinate order of every voltage sample, every current sample, efficiency, and travel distance with corresponding declared units.",
                "The waveform time vector is treated as exact; the reported standard uncertainties use first-order local covariance propagation only.",
                "No probability distribution, confidence level, acceptance criterion, welding-code rule, or qualification is inferred.",
            ),
            source_ids=(SOURCE_ID, "twi_arc_measurement"),
            qualification="user_model",
        ),
    )
