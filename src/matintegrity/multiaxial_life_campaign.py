"""Reviewed local tensor cycle to sampled-plane factors and calibrated life."""

import math

from typing import Annotated, Literal, Sequence

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest
from .critical_plane_life import (
    CriticalPlaneFsLife,
    CriticalPlaneSwtLife,
    evaluate_critical_plane_fs_life,
    evaluate_critical_plane_swt_life,
)
from .models.fatigue import (
    CriticalPlaneHistory,
    critical_plane_factors,
    critical_plane_minimum_enclosing_circle_factors,
    critical_plane_vector_path_factors,
)


class FsLifeCalibration(Contract):
    criterion: Literal["fatemi_socie"] = "fatemi_socie"
    calibrated_fatemi_socie_coefficient: Nonnegative
    calibrated_normalization_stress_Pa: Positive
    shear_modulus_Pa: Positive
    shear_fatigue_strength_coefficient_Pa: Positive
    shear_fatigue_strength_exponent: float = Field(lt=0)
    shear_fatigue_ductility_coefficient: Positive
    shear_fatigue_ductility_exponent: float = Field(lt=0)


class SwtLifeCalibration(Contract):
    criterion: Literal["swt"] = "swt"
    elastic_modulus_Pa: Positive
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)


class ShearNormalLifeCurvePoint(Contract):
    cycles_to_failure: Positive
    parameter_value: Positive
    evidence_source_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)


class ShearNormalStrainLifeCalibration(Contract):
    """Caller-fitted curve for a declared additive shear/normal strain parameter."""

    criterion: Literal["shear_normal_strain_curve"] = "shear_normal_strain_curve"
    normal_strain_weight: Nonnegative
    curve_points: tuple[ShearNormalLifeCurvePoint, ...] = Field(min_length=2)
    curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_material_condition_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    curve_interpolation_and_parameter_basis_reviewed: bool
    calibration_rights_and_condition_match_reviewed: bool

    @model_validator(mode="after")
    def curve_consistent(self):
        cycles = [point.cycles_to_failure for point in self.curve_points]
        values = [point.parameter_value for point in self.curve_points]
        if any(b <= a for a, b in zip(cycles, cycles[1:])):
            raise ValueError("curve cycles must be strictly increasing")
        if any(b >= a for a, b in zip(values, values[1:])):
            raise ValueError("parameter values must strictly decrease with cycles")
        if canonical_digest([point.model_dump(mode="json") for point in self.curve_points]) != self.curve_sha256:
            raise ValueError("curve_sha256 must match the ordered calibration points")
        source_ids = {item.source_id for item in self.evidence}
        if any(point.evidence_source_id not in source_ids for point in self.curve_points):
            raise ValueError("each curve point must link to a declared Evidence source_id")
        record_ids = [point.source_record_id for point in self.curve_points]
        if len(set(record_ids)) != len(record_ids):
            raise ValueError("curve point source_record_id values must be unique")
        return self


class KandilBrownMillerLifeCalibration(Contract):
    """Caller-calibrated KBM parameter curve for finite sampled planes."""

    criterion: Literal["kandil_brown_miller_curve"] = "kandil_brown_miller_curve"
    normal_strain_range_coefficient: Nonnegative
    curve_points: tuple[ShearNormalLifeCurvePoint, ...] = Field(min_length=2)
    curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_material_condition_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    curve_interpolation_and_parameter_basis_reviewed: bool
    calibration_rights_and_condition_match_reviewed: bool

    @model_validator(mode="after")
    def curve_consistent(self):
        # Share the generic caller-curve structural checks while preserving a
        # distinct named parameter contract and coefficient interpretation.
        ShearNormalStrainLifeCalibration(
            normal_strain_weight=self.normal_strain_range_coefficient,
            curve_points=self.curve_points,
            curve_sha256=self.curve_sha256,
            calibration_material_condition_id=self.calibration_material_condition_id,
            evidence=self.evidence,
            curve_interpolation_and_parameter_basis_reviewed=self.curve_interpolation_and_parameter_basis_reviewed,
            calibration_rights_and_condition_match_reviewed=self.calibration_rights_and_condition_match_reviewed,
        )
        return self


def build_shear_normal_strain_life_calibration(
    *,
    normal_strain_weight: float,
    curve_points: Sequence[ShearNormalLifeCurvePoint | dict],
    calibration_material_condition_id: str,
    evidence: Sequence[Evidence | dict],
    curve_interpolation_and_parameter_basis_reviewed: bool,
    calibration_rights_and_condition_match_reviewed: bool,
) -> tuple[ShearNormalStrainLifeCalibration, str]:
    """Validate caller points and return the calibration with its canonical digest."""
    points = tuple(
        point if isinstance(point, ShearNormalLifeCurvePoint)
        else ShearNormalLifeCurvePoint.model_validate(point)
        for point in curve_points
    )
    evidence_rows = tuple(
        row if isinstance(row, Evidence) else Evidence.model_validate(row)
        for row in evidence
    )
    curve_digest = canonical_digest([point.model_dump(mode="json") for point in points])
    calibration = ShearNormalStrainLifeCalibration(
        normal_strain_weight=normal_strain_weight,
        curve_points=points,
        curve_sha256=curve_digest,
        calibration_material_condition_id=calibration_material_condition_id,
        evidence=evidence_rows,
        curve_interpolation_and_parameter_basis_reviewed=curve_interpolation_and_parameter_basis_reviewed,
        calibration_rights_and_condition_match_reviewed=calibration_rights_and_condition_match_reviewed,
    )
    return calibration, canonical_digest(calibration.model_dump(mode="json"))


def build_kandil_brown_miller_life_calibration(
    *,
    normal_strain_range_coefficient: float,
    curve_points: Sequence[ShearNormalLifeCurvePoint | dict],
    calibration_material_condition_id: str,
    evidence: Sequence[Evidence | dict],
    curve_interpolation_and_parameter_basis_reviewed: bool,
    calibration_rights_and_condition_match_reviewed: bool,
) -> tuple[KandilBrownMillerLifeCalibration, str]:
    """Validate a caller KBM curve and bind both its point and full digests."""
    points = tuple(
        point if isinstance(point, ShearNormalLifeCurvePoint)
        else ShearNormalLifeCurvePoint.model_validate(point)
        for point in curve_points
    )
    evidence_rows = tuple(
        row if isinstance(row, Evidence) else Evidence.model_validate(row)
        for row in evidence
    )
    calibration = KandilBrownMillerLifeCalibration(
        normal_strain_range_coefficient=normal_strain_range_coefficient,
        curve_points=points,
        curve_sha256=canonical_digest([point.model_dump(mode="json") for point in points]),
        calibration_material_condition_id=calibration_material_condition_id,
        evidence=evidence_rows,
        curve_interpolation_and_parameter_basis_reviewed=curve_interpolation_and_parameter_basis_reviewed,
        calibration_rights_and_condition_match_reviewed=calibration_rights_and_condition_match_reviewed,
    )
    return calibration, canonical_digest(calibration.model_dump(mode="json"))


class MultiaxialLifeCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    history: CriticalPlaneHistory
    calibration: Annotated[
        FsLifeCalibration | SwtLifeCalibration | ShearNormalStrainLifeCalibration | KandilBrownMillerLifeCalibration,
        Field(discriminator="criterion"),
    ]
    calibration_material_condition_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive
    shear_range_method: Literal["directional_component", "maximum_pairwise_chord", "minimum_enclosing_circle"]
    local_measure_calibration_and_nonproportional_scope_reviewed: bool

    @model_validator(mode="after")
    def consistent(self):
        if self.history.material_condition_id != self.calibration_material_condition_id:
            raise ValueError("history and life calibration material conditions must match")
        if isinstance(self.calibration, (ShearNormalStrainLifeCalibration, KandilBrownMillerLifeCalibration)) and (
            self.history.material_condition_id != self.calibration.calibration_material_condition_id
        ):
            raise ValueError("history and shear/normal curve material conditions must match")
        if isinstance(self.calibration, (ShearNormalStrainLifeCalibration, KandilBrownMillerLifeCalibration)) and (
            canonical_digest(self.calibration.model_dump(mode="json")) != self.calibration_sha256
        ):
            raise ValueError("calibration_sha256 must match the complete caller curve calibration")
        if isinstance(self.calibration, FsLifeCalibration) and (
            self.history.fatemi_socie_coefficient != self.calibration.calibrated_fatemi_socie_coefficient
            or self.history.normalization_stress_Pa != self.calibration.calibrated_normalization_stress_Pa
        ):
            raise ValueError(
                "FS factor coefficient and normalization stress must match the calibrated definition"
            )
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("cycle support must be a nonempty interval")
        if isinstance(self.calibration, (ShearNormalStrainLifeCalibration, KandilBrownMillerLifeCalibration)) and (
            self.minimum_valid_cycles < self.calibration.curve_points[0].cycles_to_failure
            or self.maximum_valid_cycles > self.calibration.curve_points[-1].cycles_to_failure
        ):
            raise ValueError("campaign cycle support must remain inside the supplied curve")
        return self


def _shear_normal_curve_life(parameter: float, calibration: ShearNormalStrainLifeCalibration) -> float:
    """Interpolate log(parameter) against log(cycles), without extrapolation."""
    points = calibration.curve_points
    if parameter <= 0 or parameter > points[0].parameter_value or parameter < points[-1].parameter_value:
        raise ValueError("parameter is outside the supplied calibration curve")
    for left, right in zip(points, points[1:]):
        if left.parameter_value >= parameter >= right.parameter_value:
            fraction = (math.log(parameter) - math.log(left.parameter_value)) / (
                math.log(right.parameter_value) - math.log(left.parameter_value)
            )
            return math.exp(math.log(left.cycles_to_failure) + fraction * (
                math.log(right.cycles_to_failure) - math.log(left.cycles_to_failure)
            ))
    return points[-1].cycles_to_failure


def evaluate_multiaxial_life_campaign(request: MultiaxialLifeCampaign) -> dict:
    base = dict(
        campaign_id=request.campaign_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        calibration_sha256=request.calibration_sha256,
        factor_result=None,
        life_result=None,
        tied_sampled_plane_ids=[],
    )
    if not request.local_measure_calibration_and_nonproportional_scope_reviewed:
        return base
    if isinstance(request.calibration, (ShearNormalStrainLifeCalibration, KandilBrownMillerLifeCalibration)) and not (
        request.calibration.curve_interpolation_and_parameter_basis_reviewed
        and request.calibration.calibration_rights_and_condition_match_reviewed
    ):
        return base
    functions = {
        "directional_component": critical_plane_factors,
        "maximum_pairwise_chord": critical_plane_vector_path_factors,
        "minimum_enclosing_circle": critical_plane_minimum_enclosing_circle_factors,
    }
    factors = functions[request.shear_range_method](request.history)
    factor_payload = factors.model_dump(mode="json")
    if factors.status != "computed":
        return base | dict(status=factors.status, factor_result=factor_payload)
    kbm = isinstance(request.calibration, KandilBrownMillerLifeCalibration)
    rows = factor_payload["values"]["candidate_factors"]
    if kbm:
        if request.shear_range_method != "maximum_pairwise_chord":
            return base | dict(
                status="out_of_scope",
                reason="Kandil-Brown-Miller uses the sampled maximum shear-strain range; select maximum_pairwise_chord",
                factor_result=factor_payload,
            )
        maximum_shear = max(row["shear_strain_amplitude"] for row in rows)
        shear_critical_rows = [row for row in rows if row["shear_strain_amplitude"] == maximum_shear]
        for row in shear_critical_rows:
            row["kandil_brown_miller_parameter"] = (
                row["shear_strain_amplitude"]
                + request.calibration.normal_strain_range_coefficient * 2.0 * row["normal_strain_amplitude"]
            )
    if isinstance(request.calibration, ShearNormalStrainLifeCalibration) and not kbm:
        for row in rows:
            row["shear_normal_parameter"] = (
                row["shear_strain_amplitude"]
                + request.calibration.normal_strain_weight * row["normal_strain_amplitude"]
            )
    base["factor_result"] = factor_payload
    factor_digest = canonical_digest(factor_payload)
    fs = isinstance(request.calibration, FsLifeCalibration)
    sn = isinstance(request.calibration, ShearNormalStrainLifeCalibration) or kbm
    if kbm:
        critical_rows = shear_critical_rows
        key = "kandil_brown_miller_parameter"
    else:
        key = "fatemi_socie_factor" if fs else ("shear_normal_parameter" if sn else "swt_factor_Pa")
        critical_rows = rows
    maximum = max(row[key] for row in critical_rows)
    tied = [row for row in critical_rows if row[key] == maximum]
    base["tied_sampled_plane_ids"] = [row["plane_id"] for row in tied]
    if maximum <= 0:
        return base | dict(
            status="out_of_scope", reason="Zero sampled factor has no finite calibrated life root"
        )
    selected = tied[0]
    if sn:
        calibration = request.calibration
        try:
            life_cycles = _shear_normal_curve_life(maximum, calibration)
        except ValueError as exc:
            return base | dict(status="out_of_scope", reason=str(exc), factor_result_sha256=factor_digest)
        if not request.minimum_valid_cycles <= life_cycles <= request.maximum_valid_cycles:
            return base | dict(
                status="out_of_scope",
                reason="interpolated life is outside the declared campaign cycle support",
                factor_result_sha256=factor_digest,
            )
        result = dict(
            analysis_id=request.campaign_id,
            plane_id=selected["plane_id"],
            plane_factor_result_sha256=factor_digest,
            calibration_curve_sha256=calibration.curve_sha256,
            cycles_to_failure=life_cycles,
            calibration_evidence=[item.model_dump(mode="json") for item in calibration.evidence],
            curve_point_record_ids=[point.source_record_id for point in calibration.curve_points],
            curve_point_evidence_source_ids=[point.evidence_source_id for point in calibration.curve_points],
            status="computed",
            basis=(
                "Kandil-Brown-Miller sampled parameter: shear-strain amplitude plus caller-calibrated coefficient times the full normal-strain range, evaluated only on supplied finite planes tied for maximum sampled shear range. Life uses bounded log-log interpolation on a same-condition caller curve. No continuous-plane optimum, cycle counting, material qualification or acceptance is inferred."
                if kbm else
                "Caller-declared shear-amplitude plus weighted normal-strain-amplitude parameter, mapped by bounded log-log interpolation on a same-condition caller curve. This generic calibrated parameter is not asserted to reproduce any named published criterion. No extrapolation or continuous-plane search is inferred."
            ),
        )
        if kbm:
            result["kandil_brown_miller_parameter"] = maximum
            result["maximum_shear_range_plane_ids"] = [row["plane_id"] for row in shear_critical_rows]
            result["normal_strain_range_coefficient"] = calibration.normal_strain_range_coefficient
            result["normal_strain_range"] = 2.0 * selected["normal_strain_amplitude"]
        return base | dict(
            status="computed",
            life_result=result,
            factor_result_sha256=factor_digest,
            tied_sampled_plane_ids=[row["plane_id"] for row in tied],
        )
    common = dict(
        analysis_id=request.campaign_id,
        plane_id=selected["plane_id"],
        plane_factor_result_sha256=factor_digest,
        minimum_valid_cycles=request.minimum_valid_cycles,
        maximum_valid_cycles=request.maximum_valid_cycles,
    )
    coefficients = request.calibration.model_dump(
        exclude={"criterion", "calibrated_fatemi_socie_coefficient", "calibrated_normalization_stress_Pa"}
    )
    if fs:
        result = evaluate_critical_plane_fs_life(
            CriticalPlaneFsLife(
                **common,
                **coefficients,
                fatemi_socie_factor=maximum,
                engineering_shear_amplitude_and_calibration_reviewed=True,
            )
        )
    else:
        result = evaluate_critical_plane_swt_life(
            CriticalPlaneSwtLife(
                **common,
                **coefficients,
                maximum_normal_stress_Pa=selected["maximum_tensile_normal_stress_Pa"],
                normal_strain_amplitude=selected["normal_strain_amplitude"],
                plane_measure_range_and_material_calibration_reviewed=True,
            )
        )
    return base | dict(
        status=result["status"],
        life_result=result,
        factor_result_sha256=factor_digest,
        basis="One reviewed closed local cycle, supplied finite plane set and calibrated life relation. Exact sampled ties retained; no continuous-plane optimum, cycle counting, life qualification or acceptance is inferred.",
    )
