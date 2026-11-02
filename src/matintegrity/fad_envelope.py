"""Compare caller-supplied FAD coordinates with a reviewed piecewise-linear limit curve."""

from bisect import bisect_right

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, canonical_digest


class FadEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    lr: tuple[Nonnegative, ...] = Field(min_length=2)
    kr_limit: tuple[Nonnegative, ...] = Field(min_length=2)
    material_geometry_load_basis: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool

    @model_validator(mode="after")
    def curve(self):
        if len(self.lr) != len(self.kr_limit) or any(
            b <= a for a, b in zip(self.lr[:-1], self.lr[1:], strict=True)
        ):
            raise ValueError("FAD curve requires aligned strictly increasing Lr")
        if any(b > a for a, b in zip(self.kr_limit[:-1], self.kr_limit[1:], strict=True)):
            raise ValueError("FAD Kr limit must be nonincreasing")
        return self


class FadPoint(Contract):
    point_id: str = Field(min_length=1)
    lr: Nonnegative
    kr: Nonnegative
    material_geometry_load_basis: str = Field(min_length=1)
    provider_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool


def evaluate_fad_envelope(point: FadPoint, envelope: FadEnvelope) -> dict:
    result = dict(
        point_id=point.point_id,
        envelope_id=envelope.envelope_id,
        input_sha256=canonical_digest(
            {"point": point.model_dump(mode="json"), "envelope": envelope.model_dump(mode="json")}
        ),
        status="needs_data",
        kr_limit=None,
        kr_margin=None,
        within_caller_envelope=None,
    )
    if not point.reviewed or not envelope.reviewed:
        return result
    if (
        point.material_geometry_load_basis != envelope.material_geometry_load_basis
        or not envelope.lr[0] <= point.lr <= envelope.lr[-1]
    ):
        result["status"] = "out_of_scope"
        return result
    index = min(bisect_right(envelope.lr, point.lr) - 1, len(envelope.lr) - 2)
    fraction = (point.lr - envelope.lr[index]) / (envelope.lr[index + 1] - envelope.lr[index])
    limit = (1 - fraction) * envelope.kr_limit[index] + fraction * envelope.kr_limit[index + 1]
    result.update(
        status="computed",
        kr_limit=limit,
        kr_margin=limit - point.kr,
        within_caller_envelope=point.kr <= limit,
    )
    return result
