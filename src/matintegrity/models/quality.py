"""Material evidence reconciliation and independently calculated fabrication features."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Fraction, Nonnegative, Positive, canonical_digest
from ..identification import ChemistryReconciliation, ElementSymbol, reconcile_chemistry
from ..registry import ModelSpec


class ThicknessBudget(Contract):
    nominal_thickness_m: Positive
    manufacturing_minus_tolerance_m: Nonnegative
    forming_loss_fraction: float = Field(ge=0, lt=1)
    corrosion_allowance_m: Nonnegative
    required_structural_thickness_m: Positive
    measured_postfabrication_thickness_m: Positive | None = None


def thickness_budget(x: ThicknessBudget) -> Calculation:
    minimum = x.nominal_thickness_m - x.manufacturing_minus_tolerance_m
    after_forming = minimum * (1 - x.forming_loss_fraction)
    net = after_forming - x.corrosion_allowance_m
    if minimum <= 0 or net <= 0:
        return Calculation(
            status="out_of_scope", values={}, notes=("Declared losses exhaust the positive structural wall.",)
        )
    measured_net = (
        None
        if x.measured_postfabrication_thickness_m is None
        else x.measured_postfabrication_thickness_m - x.corrosion_allowance_m
    )
    return Calculation(
        values=dict(
            minimum_supplied_thickness_m=minimum,
            minimum_formed_thickness_m=after_forming,
            nominal_budget_structural_thickness_m=net,
            nominal_budget_margin_m=net - x.required_structural_thickness_m,
            measured_structural_thickness_m=measured_net,
            measured_margin_m=None
            if measured_net is None
            else measured_net - x.required_structural_thickness_m,
        ),
        notes=(
            "Manufacturing subtraction precedes fractional forming loss. A postfabrication measurement already includes these dimensional effects, so only the declared future corrosion allowance is subtracted from that measurement.",
            "Required structural thickness and all losses are supplied by the caller; no code formula or acceptance tolerance is inferred.",
        ),
    )


class JointProfile(Contract):
    transverse_position_m: list[float] = Field(min_length=6)
    measured_surface_height_m: list[float] = Field(min_length=6)
    excluded_joint_half_width_m: Nonnegative
    fit_method: Literal["ols", "theil_sen", "soft_l1"]
    robust_residual_scale_m: Positive | None = None

    @model_validator(mode="after")
    def align(self):
        if len(self.transverse_position_m) != len(self.measured_surface_height_m) or np.any(
            np.diff(self.transverse_position_m) <= 0
        ):
            raise ValueError("aligned strictly increasing transverse profile positions are required")
        if self.fit_method == "soft_l1" and self.robust_residual_scale_m is None:
            raise ValueError("soft-L1 profile fitting requires an explicit residual scale")
        return self


def joint_profile(x: JointProfile) -> Calculation:
    position = np.asarray(x.transverse_position_m)
    height = np.asarray(x.measured_surface_height_m)
    left = position < -x.excluded_joint_half_width_m
    right = position > x.excluded_joint_half_width_m
    if min(int(left.sum()), int(right.sum())) < 3:
        return Calculation(
            status="needs_data",
            values={},
            notes=("At least three fitted base-surface observations on each side are required.",),
        )
    if x.fit_method == "theil_sen" and max(int(left.sum()), int(right.sum())) > 5000:
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "This exact pairwise Theil-Sen path is bounded at 5000 points per side; select soft_l1/ols or a documented spatial reduction.",
            ),
        )
    fits = []
    for mask in (left, right):
        if x.fit_method == "theil_sen":
            from scipy.stats import theilslopes

            result = theilslopes(height[mask], position[mask], method="joint")
            slope, intercept = float(result.slope), float(result.intercept)
        elif x.fit_method == "soft_l1":
            from scipy.optimize import least_squares

            xx = position[mask]
            yy = height[mask]
            origin = float(xx.mean())
            span = float(xx.std())
            level = float(np.median(yy))
            scaled = (xx - origin) / span
            initial = np.polyfit(scaled, yy - level, 1)
            fitted = least_squares(
                lambda p, xx0=scaled, y0=yy, level0=level: (
                    (p[0] * xx0 + p[1] + level0 - y0) / x.robust_residual_scale_m
                ),
                initial,
                loss="soft_l1",
                max_nfev=1000,
            )
            if not fitted.success:
                return Calculation(
                    status="needs_data",
                    values={},
                    notes=("Robust surface-profile optimization did not converge.",),
                )
            slope = float(fitted.x[0] / span)
            intercept = float(level + fitted.x[1] - slope * origin)
        else:
            slope, intercept = (float(v) for v in np.polyfit(position[mask], height[mask], 1))
        fits.append(
            (
                slope,
                intercept,
                float(np.sqrt(np.mean((height[mask] - (intercept + slope * position[mask])) ** 2))),
            )
        )
    (a, b, res_l), (c, d, res_r) = fits
    return Calculation(
        values=dict(
            signed_surface_offset_at_joint_m=d - b,
            signed_angular_mismatch_rad=math.atan(c) - math.atan(a),
            left_slope=a,
            right_slope=c,
            left_profile_rmse_m=res_l,
            right_profile_rmse_m=res_r,
            left_fit_observations=int(left.sum()),
            right_fit_observations=int(right.sum()),
        ),
        notes=(
            "Two locally planar base surfaces are fitted outside the excluded weld zone and projected to position zero. Surface offset is not automatically an inner-wall offset or a structural stress magnification factor.",
        ),
    )


class HardnessPoint(Contract):
    point_id: str = Field(min_length=1)
    position_m: float
    region_id: str = Field(min_length=1)
    hardness_Pa: Positive
    expanded_uncertainty_Pa: Nonnegative


class HardnessTraverse(Contract):
    method_id: str = Field(min_length=1)
    test_force_N: Positive
    dwell_s: Positive
    uncertainty_coverage_description: str = Field(min_length=1)
    points: list[HardnessPoint] = Field(min_length=1)
    declared_region_upper_limits_Pa: dict[str, Positive] = Field(min_length=1)

    @model_validator(mode="after")
    def identities(self):
        if len({p.point_id for p in self.points}) != len(self.points):
            raise ValueError("hardness point IDs must be unique")
        return self


def hardness_traverse(x: HardnessTraverse) -> Calculation:
    rows = []
    for region, limit in x.declared_region_upper_limits_Pa.items():
        points = [p for p in x.points if p.region_id == region]
        if not points:
            rows.append(dict(region_id=region, outcome="unknown", observations=0))
            continue
        if any(p.hardness_Pa - p.expanded_uncertainty_Pa > limit for p in points):
            outcome = "not_satisfied"
        elif all(p.hardness_Pa + p.expanded_uncertainty_Pa <= limit for p in points):
            outcome = "satisfied"
        else:
            outcome = "unknown"
        peak = max(points, key=lambda p: p.hardness_Pa)
        rows.append(
            dict(
                region_id=region,
                outcome=outcome,
                observations=len(points),
                peak_hardness_Pa=peak.hardness_Pa,
                peak_point_id=peak.point_id,
                peak_position_m=peak.position_m,
                declared_upper_limit_Pa=limit,
            )
        )
    overall = (
        "not_satisfied"
        if any(r["outcome"] == "not_satisfied" for r in rows)
        else "unknown"
        if any(r["outcome"] == "unknown" for r in rows)
        else "satisfied"
    )
    return Calculation(
        values=dict(
            outcome=overall,
            regions=rows,
            regions_without_declared_limits=sorted(
                {p.region_id for p in x.points} - set(x.declared_region_upper_limits_Pa)
            ),
        ),
        notes=(
            "One declared method, force, dwell and uncertainty convention per traverse. Bounds apply only at measured points; unsampled HAZ or weld peaks are not ruled out. No hardness conversion or standard limit is supplied.",
        ),
    )


class WeldConstituent(Contract):
    material_id: str = Field(min_length=1)
    role: str = Field(pattern=r"^(base|filler|previous_layer)$")
    melted_mass_kg: Positive
    composition_mass_fraction: dict[ElementSymbol, Fraction | None]

    @model_validator(mode="after")
    def composition(self):
        if sum(v for v in self.composition_mass_fraction.values() if v is not None) > 1 + 1e-12:
            raise ValueError("constituent mass fractions cannot sum above one")
        return self


class WeldDilution(Contract):
    constituents: list[WeldConstituent] = Field(min_length=2)
    requested_elements: list[ElementSymbol] = Field(min_length=1)

    @model_validator(mode="after")
    def elements(self):
        if len(set(self.requested_elements)) != len(self.requested_elements):
            raise ValueError("requested element identifiers must be unique")
        return self


def weld_dilution(x: WeldDilution) -> Calculation:
    exact_total = sum((Rational(part.melted_mass_kg) for part in x.constituents), Rational(0))
    try:
        total = float(exact_total)
    except OverflowError:
        total = None
    exact_fractions = {
        role: sum(
            (Rational(part.melted_mass_kg) for part in x.constituents if part.role == role), Rational(0)
        )
        / exact_total
        for role in ("base", "filler", "previous_layer")
    }
    fractions = {role: float(value) for role, value in exact_fractions.items()}
    if any(value and fractions[role] == 0 for role, value in exact_fractions.items()):
        return Calculation(
            status="out_of_scope", values={}, notes=("A nonzero role mass fraction underflows.",)
        )
    composition = {}
    missing = {}
    for element in x.requested_elements:
        absent = [
            part.material_id for part in x.constituents if part.composition_mass_fraction.get(element) is None
        ]
        missing[element] = absent
        if absent:
            composition[element] = None
        else:
            exact = (
                sum(
                    (
                        Rational(part.melted_mass_kg) * Rational(part.composition_mass_fraction[element])
                        for part in x.constituents
                    ),
                    Rational(0),
                )
                / exact_total
            )
            composition[element] = float(exact)
            if exact and composition[element] == 0:
                return Calculation(
                    status="out_of_scope", values={}, notes=("A nonzero mixed composition underflows.",)
                )
    return Calculation(
        values=dict(
            total_melted_mass_kg=total,
            role_mass_fractions=fractions,
            mixed_composition_mass_fraction=composition,
            constituents_missing_element_evidence=missing,
        ),
        notes=(
            "Mass-weighted complete mixing of declared melted material. Missing element evidence is not zero. Burnoff, transfer losses, segregation, interfacial gradients and corrosion acceptance need separate evidence.",
            "An unrepresentable total mass is returned as null while supported mass ratios remain available.",
        ),
    )


class ProvenanceWeldConstituent(Contract):
    material_id: str = Field(min_length=1)
    role: Literal["base", "filler", "previous_layer"]
    melted_mass_kg: Positive
    source_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    composition_mass_fraction: dict[ElementSymbol, Fraction | None]

    @model_validator(mode="after")
    def mass_fraction_sum(self):
        if sum(value for value in self.composition_mass_fraction.values() if value is not None) > 1 + 1e-12:
            raise ValueError("declared constituent mass fractions cannot exceed one")
        return self


class WeldDilutionUncertainty(Contract):
    constituents: tuple[ProvenanceWeldConstituent, ...] = Field(min_length=2, max_length=100)
    requested_elements: tuple[ElementSymbol, ...] = Field(min_length=1, max_length=50)
    joint_composition_covariance: list[list[float]] | None = None
    covariance_variable_order: tuple[str, ...] = ()
    covariance_basis: str | None = None
    uncertainty_coverage_factor: Positive | None = None
    melted_mass_and_roles_reviewed: bool
    composition_records_and_mass_basis_reviewed: bool
    covariance_basis_and_variable_order_reviewed: bool

    @model_validator(mode="after")
    def coherent_records_and_covariance(self):
        if len({row.material_id for row in self.constituents}) != len(self.constituents):
            raise ValueError("constituent material IDs must be unique")
        if len(set(self.requested_elements)) != len(self.requested_elements):
            raise ValueError("requested element order must not contain duplicates")
        missing = [
            (part.material_id, element)
            for part in self.constituents
            for element in self.requested_elements
            if part.composition_mass_fraction.get(element) is None
        ]
        if self.joint_composition_covariance is None:
            if (
                self.covariance_variable_order
                or self.covariance_basis
                or self.uncertainty_coverage_factor is not None
            ):
                raise ValueError("covariance metadata requires a joint covariance matrix")
        else:
            if missing:
                raise ValueError("joint composition covariance requires complete requested elemental data")
            dimension = len(self.constituents) * len(self.requested_elements)
            matrix = np.asarray(self.joint_composition_covariance, dtype=float)
            if matrix.shape != (dimension, dimension) or not np.isfinite(matrix).all():
                raise ValueError("joint composition covariance has the wrong shape or nonfinite values")
            matrix_scale = max(float(np.max(np.abs(matrix))), np.finfo(float).tiny)
            if not np.allclose(matrix, matrix.T, rtol=1e-12, atol=matrix_scale * 1e-12):
                raise ValueError("joint composition covariance must be symmetric")
            if np.any(np.diag(matrix) < 0):
                raise ValueError("joint composition covariance cannot have negative variances")
            eigenvalues = np.linalg.eigvalsh(matrix)
            scale = max(float(np.max(np.abs(eigenvalues))), np.finfo(float).tiny)
            if float(np.min(eigenvalues)) < -128 * np.finfo(float).eps * scale:
                raise ValueError("joint composition covariance must be positive semidefinite")
            expected_order = tuple(
                f"{part.material_id}:{element}"
                for part in self.constituents
                for element in self.requested_elements
            )
            if self.covariance_variable_order != expected_order:
                raise ValueError(
                    "covariance variable order must match constituent and requested-element order"
                )
            if not self.covariance_basis or self.uncertainty_coverage_factor is None:
                raise ValueError("covariance basis and uncertainty coverage factor are required")
        return self


def weld_dilution_with_uncertainty(x: WeldDilutionUncertainty) -> Calculation:
    """Mix caller-declared weld constituents and propagate their joint assay covariance."""
    input_digest = canonical_digest(x.model_dump(mode="json"))
    exact_total = sum((Rational(row.melted_mass_kg) for row in x.constituents), Rational(0))
    try:
        total_mass = float(exact_total)
    except OverflowError:
        total_mass = None
    weights = np.asarray(
        [float(Rational(row.melted_mass_kg) / exact_total) for row in x.constituents], dtype=float
    )
    if np.any(weights == 0):
        return Calculation(
            status="out_of_scope",
            values={"input_sha256": input_digest},
            notes=("A nonzero constituent weight underflows; covariance contributions are not dropped.",),
        )
    role_fractions = {
        role: math.fsum(
            float(weights[index])
            for index, constituent in enumerate(x.constituents)
            if constituent.role == role
        )
        for role in ("base", "filler", "previous_layer")
    }
    missing = {
        element: [
            row.material_id for row in x.constituents if row.composition_mass_fraction.get(element) is None
        ]
        for element in x.requested_elements
    }
    mixed = {
        element: (
            None
            if missing[element]
            else float(
                sum(
                    (
                        Rational(row.melted_mass_kg) * Rational(row.composition_mass_fraction[element])
                        for row in x.constituents
                    ),
                    Rational(0),
                )
                / exact_total
            )
        )
        for element in x.requested_elements
    }
    values = dict(
        input_sha256=input_digest,
        constituent_source_ids={row.material_id: row.source_id for row in x.constituents},
        constituent_record_sha256={row.material_id: row.record_sha256 for row in x.constituents},
        total_melted_mass_kg=total_mass,
        role_mass_fractions=role_fractions,
        mixed_composition_mass_fraction=mixed,
        constituents_missing_element_evidence=missing,
        covariance_variable_order=list(x.covariance_variable_order),
        covariance_basis=x.covariance_basis,
        propagated_covariance_mass_fraction_squared=None,
        expanded_uncertainty_mass_fraction=None,
    )
    if any(
        mixed[element] == 0
        and any((row.composition_mass_fraction.get(element) or 0) > 0 for row in x.constituents)
        for element in x.requested_elements
    ):
        return Calculation(
            status="out_of_scope",
            values={"input_sha256": input_digest},
            notes=("A nonzero mixed composition underflows.",),
        )
    if not (x.melted_mass_and_roles_reviewed and x.composition_records_and_mass_basis_reviewed):
        return Calculation(status="needs_data", values=values)
    if any(missing.values()):
        return Calculation(status="needs_data", values=values)
    if x.joint_composition_covariance is not None:
        if not x.covariance_basis_and_variable_order_reviewed:
            return Calculation(status="needs_data", values=values)
        element_count = len(x.requested_elements)
        jacobian = np.zeros((element_count, len(x.constituents) * element_count))
        for constituent_index, weight in enumerate(weights):
            for element_index in range(element_count):
                jacobian[element_index, constituent_index * element_count + element_index] = weight
        covariance = np.asarray(x.joint_composition_covariance, dtype=float)
        propagated = jacobian @ covariance @ jacobian.T
        propagated = (propagated + propagated.T) * 0.5
        if not np.isfinite(propagated).all():
            return Calculation(status="out_of_scope", values=values)
        expanded = x.uncertainty_coverage_factor * np.sqrt(np.maximum(np.diag(propagated), 0.0))
        values["propagated_covariance_mass_fraction_squared"] = propagated.tolist()
        values["expanded_uncertainty_mass_fraction"] = dict(
            zip(x.requested_elements, expanded.tolist(), strict=True)
        )
    return Calculation(
        status="computed",
        values=values,
        notes=(
            "Mixed composition is a mass-weighted balance of the declared melted constituents. The joint assay covariance is propagated linearly with the declared exact mass weights and variable order.",
            "Missing elemental evidence is not zero. Mass-fraction, melt-weight and covariance uncertainty is not inferred; uncertainty is returned only for the caller-supplied joint covariance. No burnoff, segregation, weldability, cracking, corrosion resistance or acceptance is calculated.",
            "An unrepresentable total mass is null; supported constituent weights and ratios are retained.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.chemistry_reconciliation",
            ChemistryReconciliation,
            reconcile_chemistry,
            {"elements[].limits.lower": "mass fraction", "elements[].limits.upper": "mass fraction"},
            (
                "Exact supplied identity and interval-valued certificate/verification chemistry with an explicit comparison policy.",
            ),
            ("declared_interval_comparison", "explicit_identity_mapping", "evident_pmi_limits"),
        ),
        ModelSpec(
            "fabrication.thickness_budget",
            ThicknessBudget,
            thickness_budget,
            {
                "minimum_supplied_thickness_m": "m",
                "minimum_formed_thickness_m": "m",
                "nominal_budget_structural_thickness_m": "m",
                "nominal_budget_margin_m": "m",
                "measured_structural_thickness_m": "m",
                "measured_margin_m": "m",
            },
            (
                "Caller-declared manufacturing, forming, future corrosion and structural requirements with a separate measured path.",
            ),
            ("dimensional_budget",),
        ),
        ModelSpec(
            "welding.joint_profile",
            JointProfile,
            joint_profile,
            {
                "signed_surface_offset_at_joint_m": "m",
                "signed_angular_mismatch_rad": "rad",
                "left_slope": "1",
                "right_slope": "1",
                "left_profile_rmse_m": "m",
                "right_profile_rmse_m": "m",
            },
            ("Transverse equal-reference surface observations outside an explicitly excluded joint zone.",),
            (
                "scipy_theilslopes",
                "scipy_least_squares",
                "line_geometry",
            ),
        ),
        ModelSpec(
            "welding.hardness_traverse",
            HardnessTraverse,
            hardness_traverse,
            {"regions[].peak_hardness_Pa": "Pa", "regions[].declared_upper_limit_Pa": "Pa"},
            (
                "Declared per-region upper hardness requirements and expanded measurement intervals, without spatial extrapolation.",
            ),
            ("declared_interval_comparison",),
        ),
        ModelSpec(
            "welding.dilution",
            WeldDilution,
            weld_dilution,
            {
                "total_melted_mass_kg": "kg",
                "role_mass_fractions": "1",
                "mixed_composition_mass_fraction": "1",
            },
            (
                "Known constituent melted masses and reported elemental fractions; no inferred elemental balance or dilution threshold.",
            ),
            (
                "mass_conservation",
                "twi_dilution",
            ),
        ),
        ModelSpec(
            "welding.dilution_with_uncertainty",
            WeldDilutionUncertainty,
            weld_dilution_with_uncertainty,
            {
                "total_melted_mass_kg": "kg",
                "role_mass_fractions": "1",
                "mixed_composition_mass_fraction": "1",
                "propagated_covariance_mass_fraction_squared": "1",
                "expanded_uncertainty_mass_fraction": "1",
            },
            (
                "Provenance-pinned declared melted constituent chemistry with a full caller-supplied joint covariance and explicit variable order.",
                "The calculation propagates assay covariance using exact declared melt-mass weights and does not infer weldability or qualification.",
            ),
            ("caller_declared_weld_dilution_uncertainty",),
        ),
    ]
