"""Direct longitudinal-wave FMC delay-and-sum on an explicitly declared point grid."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive, canonical_digest
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID, CorrelationRequest


class FmcElement(Contract):
    element_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]


class TfmImagePoint(Contract):
    point_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]


class FmcTimeTrace(Contract):
    trace_id: str = Field(min_length=1)
    transmit_element_id: str = Field(min_length=1)
    receive_element_id: str = Field(min_length=1)
    signed_samples: tuple[float, ...] = Field(min_length=2, max_length=32768)
    samples_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def pinned_samples(self):
        if canonical_digest(self.signed_samples) != self.samples_sha256:
            raise ValueError("trace sample digest does not match signed samples")
        return self


def _validate_fmc_membership(x):
    ids = [row.element_id for row in x.elements]
    if len(set(ids)) != len(ids):
        raise ValueError("FMC element IDs must be unique")
    for values in ([row.trace_id for row in x.traces], [row.point_id for row in x.image_points]):
        if len(set(values)) != len(values):
            raise ValueError("FMC trace and image-point IDs must be unique")
    expected = {(tx, rx) for tx in ids for rx in ids}
    pairs = [(row.transmit_element_id, row.receive_element_id) for row in x.traces]
    if len(pairs) != len(expected) or set(pairs) != expected:
        raise ValueError(
            "FMC requires exactly one explicitly identified trace for every ordered element pair"
        )
    if any(b <= a for a, b in zip(x.time_s, x.time_s[1:], strict=False)) or not math.isfinite(
        x.time_s[-1] - x.time_s[0]
    ):
        raise ValueError("sample times must strictly increase over a finite span")
    return x


class HomogeneousFmcTfm(CorrelationRequest):
    acquisition_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    probe_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    sample_clock_id: str = Field(min_length=1)
    time_zero_basis_id: str = Field(min_length=1)
    velocity_basis_id: str = Field(min_length=1)
    raw_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    amplitude_unit: str = Field(min_length=1)
    propagation_model: Literal["homogeneous_isotropic_direct_longitudinal"]
    aggregation: Literal["coherent_sum", "coherent_mean"]
    excitation_time_origin_s: float
    longitudinal_velocity_m_s: Positive
    time_s: tuple[float, ...] = Field(min_length=2, max_length=32768)
    elements: tuple[FmcElement, ...] = Field(min_length=1, max_length=64)
    traces: tuple[FmcTimeTrace, ...] = Field(min_length=1, max_length=4096)
    image_points: tuple[TfmImagePoint, ...] = Field(min_length=1, max_length=4096)
    maximum_point_trace_evaluations: int = Field(default=1000000, ge=1, le=10000000)

    @model_validator(mode="after")
    def exact_frame_membership(self):
        _validate_fmc_membership(self)
        if any(len(row.signed_samples) != len(self.time_s) for row in self.traces):
            raise ValueError("all FMC traces must align with the explicit common sample clock")
        if len(self.traces) * len(self.time_s) > 5000000:
            raise ValueError("FMC frame exceeds the bounded sample budget")
        return self


def _fmc_lineage(x):
    return dict(
        acquisition_id=x.acquisition_id,
        physical_specimen_id=x.physical_specimen_id,
        physical_scope_id=x.physical_scope_id,
        source_group_id=x.source_group_id,
        material_condition_id=x.material_condition_id,
        probe_id=x.probe_id,
        coordinate_frame_id=x.coordinate_frame_id,
        sample_clock_id=x.sample_clock_id,
        time_zero_basis_id=x.time_zero_basis_id,
        velocity_basis_id=x.velocity_basis_id,
        raw_record_sha256=x.raw_record_sha256,
        record_sha256=x.basis.record_sha256,
        amplitude_unit=x.amplitude_unit,
        aggregation=x.aggregation,
        trace_ids=[row.trace_id for row in x.traces],
        trace_records=[row.model_dump(mode="json", exclude={"signed_samples"}) for row in x.traces],
    )


def _fmc_from_times(
    x,
    transmit_times,
    receive_times,
    *,
    path_notes,
    additional_values=None,
    sample_reader=None,
    image_points=None,
) -> Calculation:
    import numpy as np

    base = _fmc_lineage(x)
    base.update(additional_values or {})
    points = x.image_points if image_points is None else image_points
    count = len(points) * len(x.traces)
    if count > x.maximum_point_trace_evaluations:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The caller point/trace evaluation budget is exceeded.",),
        )
    lookup = {row.element_id: i for i, row in enumerate(x.elements)}
    times = np.asarray(x.time_s)
    contributions = np.empty((len(points), len(x.traces)), dtype=float)
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        expected = (len(points), len(x.elements))
        if (
            transmit_times.shape != expected
            or receive_times.shape != expected
            or not np.all(np.isfinite(transmit_times))
            or not np.all(np.isfinite(receive_times))
            or np.any(transmit_times < 0)
            or np.any(receive_times < 0)
        ):
            return Calculation(
                status="out_of_scope",
                values=base,
                notes=("Propagation lookup geometry or travel time exceeds numeric support.",),
            )
        for index, trace in enumerate(x.traces):
            query = (
                x.excitation_time_origin_s
                + transmit_times[:, lookup[trace.transmit_element_id]]
                + receive_times[:, lookup[trace.receive_element_id]]
            )
            unsupported = ~np.isfinite(query) | (query < times[0]) | (query > times[-1])
            if np.any(unsupported):
                return Calculation(
                    status="out_of_scope",
                    values=base
                    | {
                        "unsupported_trace_id": trace.trace_id,
                        "unsupported_point_ids": [
                            point.point_id for point, bad in zip(points, unsupported, strict=True) if bad
                        ],
                    },
                    notes=(
                        "Every transmit/receive contribution must lie inside the observed clock support; no endpoint clamping, zero padding or partial image is supplied.",
                    ),
                )
            samples = np.asarray(trace.signed_samples) if sample_reader is None else sample_reader(index)
            if samples.shape != times.shape or not np.all(np.isfinite(samples)):
                return Calculation(
                    status="out_of_scope",
                    values=base,
                    notes=("Trace samples must be finite and aligned with the declared clock.",),
                )
            values = np.interp(query, times, samples)
            if not np.all(np.isfinite(values)):
                return Calculation(
                    status="out_of_scope",
                    values=base,
                    notes=("Linear RF interpolation exceeds numeric support.",),
                )
            if x.aggregation == "coherent_mean":
                scaled = values / len(x.traces)
                if np.any((values != 0.0) & (scaled == 0.0)):
                    return Calculation(
                        status="out_of_scope",
                        values=base,
                        notes=("A nonzero coherent-mean contribution underflows numeric support.",),
                    )
                values = scaled
            contributions[:, index] = values
    try:
        amplitudes = [math.fsum(row) for row in contributions]
    except (OverflowError, ValueError):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Coherent amplitude accumulation exceeds numeric support.",),
        )
    if not all(math.isfinite(value) for value in amplitudes):
        return Calculation(
            status="out_of_scope", values=base, notes=("Nonfinite coherent amplitudes are withheld.",)
        )
    return Calculation(
        values=base
        | {
            "point_trace_evaluations": count,
            "image": [
                dict(point_id=point.point_id, position_m=point.position_m, coherent_amplitude=amplitude)
                for point, amplitude in zip(points, amplitudes, strict=True)
            ],
        },
        notes=path_notes,
    )


def homogeneous_fmc_tfm(x: HomogeneousFmcTfm) -> Calculation:
    import numpy as np

    if x.propagation_model != "homogeneous_isotropic_direct_longitudinal":
        return Calculation(
            status="out_of_scope",
            values={"acquisition_id": x.acquisition_id},
            notes=("The direct homogeneous evaluator does not accept another propagation model.",),
        )
    points = np.asarray([row.position_m for row in x.image_points])
    elements = np.asarray([row.position_m for row in x.elements])
    with np.errstate(over="ignore", invalid="ignore", under="ignore", divide="ignore"):
        one_way = (
            np.hypot.reduce(points[:, None, :] - elements[None, :, :], axis=2) / x.longitudinal_velocity_m_s
        )
    return _fmc_from_times(
        x,
        one_way,
        one_way,
        path_notes=(
            "Unweighted direct longitudinal paths in one homogeneous isotropic medium, linear signed RF interpolation, and coherent sum or mean over the explicitly complete FMC frame.",
            "No wedge/refraction, reflection or mode conversion, anisotropy, apodization, spreading/attenuation correction, envelope, log compression, detection, flaw sizing, POD or acceptance is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.homogeneous_fmc_tfm",
            HomogeneousFmcTfm,
            homogeneous_fmc_tfm,
            {
                "image[].position_m": "m",
                "image[].coherent_amplitude": "caller_declared",
                "point_trace_evaluations": "1",
            },
            (
                "All element and image coordinates share the explicit reviewed frame and material condition.",
                "Raw/sample hashes, clock, excitation origin, velocity basis and ordered transmit/receive membership are caller supplied and digest-bound.",
                "Every direct-path delay must be inside the common observed time support; reconstruction does not qualify an examination or infer a flaw.",
            ),
            (SOURCE_ID,),
            qualification="user_model",
        )
    ]
