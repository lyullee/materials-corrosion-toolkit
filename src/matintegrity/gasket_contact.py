"""Equilibrium of an elastic bolt and an explicitly supplied reversible gasket curve."""

import math
from bisect import bisect_right

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class GasketCompressionPoint(Contract):
    compression_m: Nonnegative
    force_N: Nonnegative


class BoltForceChangePoint(Contract):
    """Caller-supplied incremental bolt force versus signed extension."""

    extension_change_m: float
    force_change_N: float


class NonlinearBoltGasketJoint(Contract):
    """Quasi-static joint equilibrium with supplied nonlinear bolt and gasket curves."""

    joint_id: str = Field(min_length=1)
    gasket_curve_id: str = Field(min_length=1)
    gasket_curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    gasket_compression_curve: tuple[GasketCompressionPoint, ...] = Field(min_length=2)
    bolt_curve_id: str = Field(min_length=1)
    bolt_curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bolt_force_change_curve: tuple[BoltForceChangePoint, ...] = Field(min_length=3)
    initial_compression_m: Nonnegative
    external_separating_force_N: Nonnegative
    bolt_free_length_change_m: float = 0.0
    supplied_curves_and_uniform_contact_reviewed: bool
    both_curves_computational_use_authorized: bool

    @model_validator(mode="after")
    def curve_support(self):
        gasket = self.gasket_compression_curve
        if gasket[0].compression_m != 0 or gasket[0].force_N != 0:
            raise ValueError("gasket curve must start at zero compression and force")
        for left, right in zip(gasket[:-1], gasket[1:], strict=True):
            if right.compression_m <= left.compression_m or right.force_N <= left.force_N:
                raise ValueError("gasket curve compression and force must increase strictly")
        if self.initial_compression_m > gasket[-1].compression_m:
            raise ValueError("initial compression is outside supplied gasket support")
        bolt = self.bolt_force_change_curve
        if not any(row.extension_change_m == 0 and row.force_change_N == 0 for row in bolt):
            raise ValueError("bolt force-change curve must include the origin")
        for left, right in zip(bolt[:-1], bolt[1:], strict=True):
            if right.extension_change_m <= left.extension_change_m or right.force_change_N <= left.force_change_N:
                raise ValueError("bolt extension and force-change curve must increase strictly")
        return self


def evaluate_nonlinear_bolt_gasket_joint(request: NonlinearBoltGasketJoint) -> dict:
    """Solve the monotone quasi-static force balance without curve extrapolation."""
    base = dict(
        joint_id=request.joint_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        gasket_curve_id=request.gasket_curve_id,
        gasket_curve_source_sha256=request.gasket_curve_source_sha256,
        bolt_curve_id=request.bolt_curve_id,
        bolt_curve_source_sha256=request.bolt_curve_source_sha256,
    )
    if not (
        request.supplied_curves_and_uniform_contact_reviewed
        and request.both_curves_computational_use_authorized
    ):
        return base
    from bisect import bisect_right

    gasket = request.gasket_compression_curve
    bolt = request.bolt_force_change_curve

    def interpolate(points, x_key, y_key, value):
        xs = [getattr(row, x_key) for row in points]
        if value < xs[0] or value > xs[-1]:
            raise ValueError("required state is outside supplied curve support")
        index = min(max(bisect_right(xs, value) - 1, 0), len(points) - 2)
        left, right = points[index], points[index + 1]
        fraction = (value - getattr(left, x_key)) / (getattr(right, x_key) - getattr(left, x_key))
        return getattr(left, y_key) + fraction * (getattr(right, y_key) - getattr(left, y_key))

    try:
        initial_force = interpolate(gasket, "compression_m", "force_N", request.initial_compression_m)
        max_compression = gasket[-1].compression_m
        required_separated_delta = request.external_separating_force_N - initial_force
        if bolt[0].force_change_N <= required_separated_delta <= bolt[-1].force_change_N:
            separated_extension = interpolate(
                bolt, "force_change_N", "extension_change_m", required_separated_delta
            )
            separated_opening = separated_extension + request.bolt_free_length_change_m
            if separated_opening >= request.initial_compression_m:
                return base | dict(
                    status="computed",
                    contact_state="separated",
                    compression_m=0.0,
                    opening_displacement_m=separated_opening,
                    contact_gap_m=separated_opening - request.initial_compression_m,
                    bolt_extension_change_m=separated_extension,
                    initial_bolt_force_N=initial_force,
                    bolt_force_N=request.external_separating_force_N,
                    gasket_force_N=0.0,
                    force_balance_residual_N=0.0,
                    basis="Quasi-static equilibrium from caller-authorized nonlinear bolt and gasket curves; no hysteresis, flange field, leakage or acceptance model.",
                )

        def state(compression):
            extension = request.initial_compression_m - compression - request.bolt_free_length_change_m
            delta = interpolate(bolt, "extension_change_m", "force_change_N", extension)
            gasket_force = interpolate(gasket, "compression_m", "force_N", compression)
            bolt_force = initial_force + delta
            return bolt_force - gasket_force - request.external_separating_force_N, extension, bolt_force, gasket_force

        feasible_low = max(
            0.0,
            request.initial_compression_m
            - request.bolt_free_length_change_m
            - bolt[-1].extension_change_m,
        )
        feasible_high = min(
            max_compression,
            request.initial_compression_m
            - request.bolt_free_length_change_m
            - bolt[0].extension_change_m,
        )
        if feasible_high < feasible_low:
            return base | dict(status="out_of_scope", reason="Bolt and gasket curve supports do not overlap")
        low_state, high_state = state(feasible_low), state(feasible_high)
        if low_state[0] < 0 or high_state[0] > 0:
            return base | dict(status="out_of_scope", reason="No closed equilibrium is bracketed by supplied curve supports")
        low, high = feasible_low, feasible_high
        for _ in range(100):
            middle = (low + high) / 2
            residual = state(middle)[0]
            if residual > 0:
                low = middle
            else:
                high = middle
            if high - low <= max(1e-15, 1e-12 * max_compression):
                break
        compression = (low + high) / 2
        residual, extension, bolt_force, gasket_force = state(compression)
        opening = request.initial_compression_m - compression
        if bolt_force < 0 or not all(math.isfinite(value) for value in (compression, extension, bolt_force, gasket_force, residual)):
            return base | dict(status="out_of_scope", reason="Nonfinite or nonphysical equilibrium state")
        return base | dict(
            status="computed",
            contact_state="closed" if compression > 0 else "incipient_separation",
            compression_m=compression,
            opening_displacement_m=opening,
            contact_gap_m=0.0,
            bolt_extension_change_m=extension,
            initial_bolt_force_N=initial_force,
            bolt_force_N=bolt_force,
            gasket_force_N=gasket_force,
            force_balance_residual_N=residual,
            basis="Quasi-static single-degree-of-freedom force balance with caller-supplied monotone nonlinear component curves. No path dependence, flange bending field, leakage or acceptance model.",
        )
    except (ArithmeticError, OverflowError, ValueError) as error:
        return base | dict(status="out_of_scope", reason=str(error))


class NonlinearGasketJoint(Contract):
    joint_id: str = Field(min_length=1)
    gasket_curve_id: str = Field(min_length=1)
    curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    compression_curve: tuple[GasketCompressionPoint, ...] = Field(min_length=2)
    initial_compression_m: Nonnegative
    bolt_stiffness_N_m: Positive
    external_separating_force_N: Nonnegative
    bolt_free_length_change_m: float = 0.0
    reversible_curve_and_uniform_contact_reviewed: bool
    curve_computational_use_authorized: bool

    @model_validator(mode="after")
    def support(self):
        if self.compression_curve[0].compression_m != 0 or self.compression_curve[0].force_N != 0:
            raise ValueError("gasket curve must start at zero compression and force")
        for first, second in zip(self.compression_curve[:-1], self.compression_curve[1:], strict=True):
            if second.compression_m <= first.compression_m or second.force_N < first.force_N:
                raise ValueError("compression must increase strictly and force must not decrease")
        if self.initial_compression_m > self.compression_curve[-1].compression_m:
            raise ValueError("initial compression is outside supplied curve support")
        return self


def evaluate_nonlinear_gasket_joint(request: NonlinearGasketJoint) -> dict:
    base = dict(
        joint_id=request.joint_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        curve_source_sha256=request.curve_source_sha256,
    )
    if not (
        request.reversible_curve_and_uniform_contact_reviewed and request.curve_computational_use_authorized
    ):
        return base
    points = request.compression_curve
    coordinates = [point.compression_m for point in points]

    def force(compression):
        index = min(max(bisect_right(coordinates, compression) - 1, 0), len(points) - 2)
        left, right = points[index : index + 2]
        fraction = (compression - left.compression_m) / (right.compression_m - left.compression_m)
        return left.force_N + fraction * (right.force_N - left.force_N)

    initial_force = force(request.initial_compression_m)
    stiffness = request.bolt_stiffness_N_m
    external = request.external_separating_force_N
    free_change = request.bolt_free_length_change_m

    def equilibrium(compression):
        opening = request.initial_compression_m - compression
        return initial_force + stiffness * (opening - free_change) - force(compression) - external

    if not all(math.isfinite(equilibrium(x)) for x in (0.0, coordinates[-1])):
        return base | dict(status="out_of_scope", reason="Nonfinite load equilibrium")
    if equilibrium(0.0) < 0:
        opening = free_change + (external - initial_force) / stiffness
        return base | dict(
            status="computed",
            contact_state="separated",
            gasket_force_N=0.0,
            bolt_force_N=external,
            initial_bolt_force_N=initial_force,
            compression_m=0.0,
            opening_displacement_m=opening,
            contact_gap_m=opening - request.initial_compression_m,
            basis="Separated static equilibrium only; sealing and stability are not assessed.",
        )
    if equilibrium(coordinates[-1]) > 0:
        return base | dict(
            status="out_of_scope", reason="Required compression exceeds supplied curve support"
        )
    # Piecewise-linear balance is affine on each curve interval; solve the unique bracket exactly.
    for left, right in zip(points[:-1], points[1:], strict=True):
        low, high = equilibrium(left.compression_m), equilibrium(right.compression_m)
        if low >= 0 >= high:
            fraction = low / (low - high)
            compression = left.compression_m + fraction * (right.compression_m - left.compression_m)
            opening = request.initial_compression_m - compression
            clamp = force(compression)
            bolt = initial_force + stiffness * (opening - free_change)
            if bolt < 0 or not all(math.isfinite(value) for value in (compression, opening, clamp, bolt)):
                return base | dict(
                    status="out_of_scope", reason="Nonfinite state or bolt compression outside scope"
                )
            return base | dict(
                status="computed",
                contact_state="closed" if compression > 0 else "incipient_separation",
                initial_bolt_force_N=initial_force,
                bolt_force_N=bolt,
                gasket_force_N=clamp,
                compression_m=compression,
                opening_displacement_m=opening,
                contact_gap_m=0.0,
                force_balance_residual_N=bolt - clamp - external,
                basis="Elastic bolt plus caller reversible compression-force curve; no extrapolation, hysteresis, relaxation, flange bending, leakage or acceptance model.",
            )
    raise RuntimeError("monotone gasket balance has no interval despite an enclosing bracket")
