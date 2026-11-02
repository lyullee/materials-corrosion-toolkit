"""Linear combinations of measured phase fractions with caller-supplied covariance."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Positive
from ..registry import ModelSpec


class PhaseFractionContrastObservation(Contract):
    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    phase_id: str = Field(min_length=1)
    measured_fraction: Fraction
    expanded_uncertainty_fraction: Fraction
    method_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class PhaseFractionLinearTerm(Contract):
    phase_id: str = Field(min_length=1)
    coefficient: float


class PhaseFractionContrastRequirement(Contract):
    contrast_id: str = Field(min_length=1)
    terms: tuple[PhaseFractionLinearTerm, ...] = Field(min_length=1)
    minimum_value_fraction: float
    maximum_value_fraction: float
    requirement_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_terms_and_ordered_bounds(self):
        phase_ids = [term.phase_id for term in self.terms]
        if len(phase_ids) != len(set(phase_ids)):
            raise ValueError("each phase may appear only once in a linear contrast")
        if all(term.coefficient == 0.0 for term in self.terms):
            raise ValueError("at least one linear contrast coefficient must be nonzero")
        if self.maximum_value_fraction < self.minimum_value_fraction:
            raise ValueError("contrast requirement bounds must be ordered")
        return self


class PhaseFractionCovariance(Contract):
    observation_ids: tuple[str, ...] = Field(min_length=1)
    expanded_covariance_matrix_fraction2: tuple[tuple[float, ...], ...] = Field(min_length=1)
    expansion_factor: Positive
    covariance_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def symmetric_positive_semidefinite(self):
        n = len(self.observation_ids)
        matrix = np.asarray(self.expanded_covariance_matrix_fraction2, dtype=float)
        if len(self.observation_ids) != len(set(self.observation_ids)):
            raise ValueError("covariance observation identifiers must be unique")
        if matrix.shape != (n, n):
            raise ValueError("expanded covariance matrix dimensions must match observation_ids")
        if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-15):
            raise ValueError("expanded covariance matrix must be symmetric")
        eigenvalues = np.linalg.eigvalsh(matrix)
        tolerance = max(float(np.max(np.abs(eigenvalues))), np.finfo(float).tiny) * 1e-12
        if float(np.min(eigenvalues)) < -tolerance:
            raise ValueError("expanded covariance matrix must be positive semidefinite")
        return self


class PhaseFractionContrastAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    processing_history_id: str = Field(min_length=1)
    observations: tuple[PhaseFractionContrastObservation, ...] = Field(min_length=1)
    requirements: tuple[PhaseFractionContrastRequirement, ...] = Field(min_length=1)
    covariance: PhaseFractionCovariance | None = None
    sample_region_mapping_reviewed: bool
    material_processing_identity_reviewed: bool
    method_applicability_reviewed: bool
    covariance_basis_reviewed: bool
    phase_identity_reviewed: bool
    requirement_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_identity_and_covariance_diagonal(self):
        observation_ids = [row.observation_id for row in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("phase-fraction contrast observation identifiers must be unique")
        requirement_ids = [row.contrast_id for row in self.requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("phase-fraction contrast identifiers must be unique")
        phases = [row.phase_id for row in self.observations]
        if len(phases) != len(set(phases)):
            raise ValueError("this assessment accepts one observation per phase")
        scopes = {(row.sample_id, row.region_id, row.method_id) for row in self.observations}
        if len(scopes) != 1:
            raise ValueError("all contrast observations must share one sample, region, and method")
        phase_ids = set(phases)
        if any(
            not {term.phase_id for term in requirement.terms} <= phase_ids
            for requirement in self.requirements
        ):
            raise ValueError("every contrast term must reference an observed phase")
        if self.covariance is not None:
            if set(self.covariance.observation_ids) != set(observation_ids):
                raise ValueError("covariance must cover exactly the supplied observation identifiers")
            matrix = np.asarray(self.covariance.expanded_covariance_matrix_fraction2, dtype=float)
            covariance_order = {key: i for i, key in enumerate(self.covariance.observation_ids)}
            for row in self.observations:
                diagonal = matrix[covariance_order[row.observation_id], covariance_order[row.observation_id]]
                expected = row.expanded_uncertainty_fraction**2
                if not math.isclose(diagonal, expected, rel_tol=1e-8, abs_tol=1e-15):
                    raise ValueError(
                        "covariance diagonal must equal squared observation expanded uncertainty"
                    )
        return self


def phase_fraction_linear_contrast(x: PhaseFractionContrastAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "sample_region_mapping_reviewed",
            "material_processing_identity_reviewed",
            "method_applicability_reviewed",
            "covariance_basis_reviewed",
            "phase_identity_reviewed",
            "requirement_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    if x.covariance is None:
        missing_reviews.append("expanded_covariance_matrix")
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "contrast_rows": [],
                "missing_reviews": missing_reviews,
                "all_contrasts_within_declared_ranges": None,
            },
            notes=(
                "This model propagates the supplied expanded covariance matrix through caller-defined linear contrasts.",
                "The supplied expansion factor and covariance basis are retained; the result is not a probability or material acceptance decision.",
            ),
        )

    assert x.covariance is not None  # narrowed after the explicit missing-data return above
    observation_index = {row.observation_id: i for i, row in enumerate(x.observations)}
    phase_observations = {row.phase_id: row for row in x.observations}
    covariance_order = {key: i for i, key in enumerate(x.covariance.observation_ids)}
    rows = []
    for requirement in x.requirements:
        coefficients = np.zeros(len(x.observations), dtype=float)
        for term in requirement.terms:
            observation = phase_observations[term.phase_id]
            coefficients[observation_index[observation.observation_id]] = term.coefficient
        permutation = [covariance_order[row.observation_id] for row in x.observations]
        covariance = np.asarray(x.covariance.expanded_covariance_matrix_fraction2, dtype=float)[
            np.ix_(permutation, permutation)
        ]
        values = np.asarray([row.measured_fraction for row in x.observations], dtype=float)
        nominal = float(coefficients @ values)
        variance = float(coefficients @ covariance @ coefficients)
        expanded_uncertainty = math.sqrt(max(variance, 0.0))
        lower = nominal - expanded_uncertainty
        upper = nominal + expanded_uncertainty
        within = lower >= requirement.minimum_value_fraction and upper <= requirement.maximum_value_fraction
        rows.append(
            {
                "contrast_id": requirement.contrast_id,
                "sample_id": x.observations[0].sample_id,
                "region_id": x.observations[0].region_id,
                "method_id": x.observations[0].method_id,
                "terms": [term.model_dump(mode="json") for term in requirement.terms],
                "nominal_value_fraction": nominal,
                "expanded_uncertainty_fraction": expanded_uncertainty,
                "expansion_factor": x.covariance.expansion_factor,
                "uncertainty_interval_fraction": [lower, upper],
                "within_declared_range": within,
            }
        )
    return Calculation(
        status="computed",
        values={
            "assessment_id": x.assessment_id,
            "covariance_observation_ids": list(x.covariance.observation_ids),
            "covariance_basis": x.covariance.covariance_basis,
            "contrast_rows": rows,
            "missing_reviews": [],
            "all_contrasts_within_declared_ranges": all(row["within_declared_range"] for row in rows),
        },
        notes=(
            "Each linear contrast is propagated with its caller-supplied expanded covariance matrix, including cross-phase covariance.",
            "Caller-defined phase groups and bounds are not embedded material or welding acceptance rules.",
            "The interval is a deterministic expanded-uncertainty interval; it is not a confidence or probability interval.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("phase-fraction contrast asset and location must match the run context")

    return [
        ModelSpec(
            "materials.phase_fraction_linear_contrast",
            PhaseFractionContrastAssessment,
            phase_fraction_linear_contrast,
            {
                "contrast_rows": "mixed",
                "missing_reviews": "1",
                "all_contrasts_within_declared_ranges": "1",
            },
            (
                "One sample, region and measurement method are assessed at a time.",
                "A caller-supplied expanded covariance matrix propagates through caller-defined phase-fraction linear contrasts.",
                "Ranges, phase grouping, uncertainty coverage and method applicability are caller-reviewed and are not code acceptance rules.",
            ),
            ("declared_phase_fraction_linear_contrast", "nist_tn1297_uncertainty_propagation"),
            context_validator=same_identity,
        )
    ]
