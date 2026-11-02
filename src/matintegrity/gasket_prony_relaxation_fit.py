"""Fit a caller-owned generalized-Maxwell spectrum to reviewed step-strain relaxation tests."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "fabrication.gasket_prony_relaxation_spectrum_fit"
DATA_SOURCE_ID = "caller_gasket_prony_step_strain_relaxation_tests"
FIT_SOURCE_ID = "nonlinear_weighted_generalized_maxwell_relaxation_fit"
MAX_OBSERVATIONS = 20_000
MAX_TESTS = 500


class GasketPronyRelaxationObservation(Contract):
    """One ordered stress observation during a declared constant-strain hold."""

    elapsed_time_s: float = Field(ge=0)
    compressive_stress_Pa: Positive
    standard_uncertainty_Pa: Positive


class GasketPronyRelaxationTest(Contract):
    """One identified specimen/test step under a common isothermal condition."""

    test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    compressive_step_strain: Positive
    temperature_K: Positive
    observations: tuple[GasketPronyRelaxationObservation, ...] = Field(min_length=3, max_length=MAX_OBSERVATIONS)

    @model_validator(mode="after")
    def validate_observation_order(self):
        times = [item.elapsed_time_s for item in self.observations]
        if not all(math.isfinite(value) for value in times) or times[0] != 0.0:
            raise ValueError("each relaxation test must start at t=0 with finite observations")
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("observation times must be strictly increasing")
        return self


class GasketPronyRelaxationSpectrumFit(Contract):
    """Evidence- and support-bounded fit of a finite Prony relaxation spectrum."""

    schema_version: Literal["matintegrity.gasket_prony_relaxation_spectrum_fit.v1"] = (
        "matintegrity.gasket_prony_relaxation_spectrum_fit.v1"
    )
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    temperature_K: Positive
    tests: tuple[GasketPronyRelaxationTest, ...] = Field(min_length=1, max_length=MAX_TESTS)
    prony_branch_count: StrictInt = Field(ge=1, le=8)
    maximum_modulus_Pa: Positive
    relaxation_time_min_s: Positive
    relaxation_time_max_s: Positive
    data_source_id: str = DATA_SOURCE_ID
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    protocol_and_sign_reviewed: bool
    common_material_condition_reviewed: bool
    isothermal_linear_viscoelastic_applicability_reviewed: bool
    rights_and_computational_use_reviewed: bool
    maximum_function_evaluations: StrictInt = Field(default=20_000, ge=100, le=200_000)

    @model_validator(mode="after")
    def validate_fit_basis(self):
        if self.data_source_id != DATA_SOURCE_ID:
            raise ValueError("data_source_id must identify caller-owned relaxation observations")
        if self.evidence.source_id != self.data_source_id or self.evidence.sha256 != self.data_sha256:
            raise ValueError("Evidence must match the source identifier and immutable data digest")
        if self.relaxation_time_max_s <= self.relaxation_time_min_s:
            raise ValueError("relaxation-time support bounds must be strictly increasing")
        if not all(math.isfinite(value) and value > 0.0 for value in (
            self.temperature_K,
            self.maximum_modulus_Pa,
            self.relaxation_time_min_s,
            self.relaxation_time_max_s,
        )):
            raise ValueError("temperature, modulus bound and relaxation-time bounds must be finite and positive")
        if len({test.test_id for test in self.tests}) != len(self.tests):
            raise ValueError("test IDs must be unique")
        if any(test.temperature_K != self.temperature_K for test in self.tests):
            raise ValueError("all tests must match the declared exact isothermal temperature")
        observation_count = sum(len(test.observations) for test in self.tests)
        if observation_count <= 2 * self.prony_branch_count + 1:
            raise ValueError("the finite record must contain more observations than fitted parameters")
        longest = max(test.observations[-1].elapsed_time_s for test in self.tests)
        if self.relaxation_time_min_s >= longest:
            raise ValueError("relaxation-time lower support must be below the observed hold duration")
        return self


def evaluate_gasket_prony_relaxation_spectrum_fit(
    request: GasketPronyRelaxationSpectrumFit,
    *,
    scipy: Any,
) -> Calculation:
    """Fit sigma(t)=epsilon0*(E_inf + sum(E_i exp(-t/tau_i))) by uncertainty-weighted least squares."""
    digest = canonical_digest(request.model_dump(mode="json"))
    common = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "physical_scope_id": request.physical_scope_id,
        "temperature_K": request.temperature_K,
        "data_sha256": request.data_sha256,
        "request_sha256": digest,
        "test_ids": [test.test_id for test in request.tests],
        "physical_specimen_ids": sorted({test.physical_specimen_id for test in request.tests}),
        "source_group_ids": sorted({test.source_group_id for test in request.tests}),
        "prony_branch_count": request.prony_branch_count,
        "maximum_modulus_Pa": request.maximum_modulus_Pa,
    }
    reviews = (
        request.protocol_and_sign_reviewed,
        request.common_material_condition_reviewed,
        request.isothermal_linear_viscoelastic_applicability_reviewed,
        request.rights_and_computational_use_reviewed,
    )
    if not all(reviews):
        return Calculation(status="needs_data", values=common | {
            "missing_review_count": sum(not value for value in reviews),
            "reason": "step-strain protocol, condition, model applicability or rights review is incomplete",
        })

    least_squares = getattr(getattr(scipy, "optimize", None), "least_squares", None)
    if not callable(least_squares):
        return Calculation(status="needs_data", values=common | {"reason": "scipy.optimize.least_squares is unavailable"})

    observations = [
        (test.compressive_step_strain, row.elapsed_time_s, row.compressive_stress_Pa, row.standard_uncertainty_Pa)
        for test in request.tests for row in test.observations
    ]
    if any(not all(math.isfinite(value) and value > 0.0 for value in (strain, stress, uncertainty))
           or not math.isfinite(time) or time < 0.0
           for strain, time, stress, uncertainty in observations):
        return Calculation(status="out_of_scope", values=common | {"reason": "nonfinite or nonpositive observation input"})

    branch_count = request.prony_branch_count
    modulus_ceiling = request.maximum_modulus_Pa
    tau_min = request.relaxation_time_min_s
    tau_max = request.relaxation_time_max_s
    if not math.isfinite(modulus_ceiling) or modulus_ceiling <= 0.0:
        return Calculation(status="out_of_scope", values=common | {"reason": "finite modulus bounds could not be formed"})

    initial_modulus = max(stress / strain for strain, _time, stress, _uncertainty in observations)
    branch_guess = max(initial_modulus * 0.8 / branch_count, modulus_ceiling * 1.0e-12)
    x0 = [max(initial_modulus * 0.2, modulus_ceiling * 1.0e-12)] + [branch_guess] * branch_count
    x0.extend(math.log(tau_min) + (i + 1) * (math.log(tau_max) - math.log(tau_min)) / (branch_count + 1)
              for i in range(branch_count))
    lower = [0.0] * (branch_count + 1) + [math.log(tau_min)] * branch_count
    upper = [modulus_ceiling] * (branch_count + 1) + [math.log(tau_max)] * branch_count

    def residual(parameters: list[float]) -> list[float]:
        equilibrium = parameters[0]
        moduli = parameters[1:1 + branch_count]
        taus = [math.exp(value) for value in parameters[1 + branch_count:]]
        return [
            (strain * (equilibrium + math.fsum(modulus * math.exp(-time / tau)
                                                for modulus, tau in zip(moduli, taus, strict=True))) - stress)
            / uncertainty
            for strain, time, stress, uncertainty in observations
        ]

    try:
        fit = least_squares(
            residual,
            x0,
            bounds=(lower, upper),
            method="trf",
            loss="linear",
            max_nfev=request.maximum_function_evaluations,
            x_scale="jac",
        )
    except (ArithmeticError, FloatingPointError, ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=common | {
            "reason": "bounded Prony optimizer failed on the declared input support",
            "optimizer_error_type": type(error).__name__,
        })

    fitted_residual = residual(fit.x)
    objective = math.fsum(value * value for value in fitted_residual)
    degrees_freedom = len(observations) - len(fit.x)
    rms_normalized = math.sqrt(objective / max(1, len(observations)))
    branches = sorted(
        ({"modulus_Pa": float(modulus), "relaxation_time_s": float(math.exp(log_tau))}
         for modulus, log_tau in zip(fit.x[1:1 + branch_count], fit.x[1 + branch_count:], strict=True)),
        key=lambda item: item["relaxation_time_s"],
    )
    from numpy.linalg import matrix_rank
    jacobian_rank = int(matrix_rank(fit.jac))
    full_rank = jacobian_rank == len(fit.x) if jacobian_rank is not None else None
    boundary_parameters = [
        index for index, (value, lo, hi) in enumerate(zip(fit.x, lower, upper, strict=True))
        if math.isclose(value, lo, rel_tol=1e-8, abs_tol=1e-10)
        or math.isclose(value, hi, rel_tol=1e-8, abs_tol=1e-10)
    ]
    status = "computed" if fit.success and all(math.isfinite(value) for value in (*fit.x, objective, rms_normalized)) else "out_of_scope"
    values = common | {
        "status": status,
        "equilibrium_modulus_Pa": float(fit.x[0]),
        "prony_branches": branches,
        "weighted_sum_squared_residual": objective,
        "normalized_residual_rms": rms_normalized,
        "observation_count": len(observations),
        "fitted_parameter_count": len(fit.x),
        "residual_degrees_of_freedom": degrees_freedom,
        "jacobian_rank": jacobian_rank,
        "local_parameter_identifiability_full_rank": full_rank,
        "parameters_at_bounds": boundary_parameters,
        "optimizer_success": bool(fit.success),
        "optimizer_message": str(fit.message),
        "relaxation_time_fit_support_s": [tau_min, tau_max],
        "method": FIT_SOURCE_ID,
        "interpretation": "same-condition calibrated descriptive generalized-Maxwell fit only",
        "limitations": [
            "A finite sum of exponentials is fitted to caller step-strain records; branch count, parameter bounds and measurement uncertainties are caller selections.",
            "The fit is not independent validation and does not establish a unique or transferable material spectrum.",
            "Uncensored linear-viscoelastic, isothermal step-strain behavior is assumed; physical specimen/test lineage is retained but not pooled as independent proof.",
            "No temperature shift, joint equilibrium, contact loss, leakage, seal acceptance, service-life probability or material qualification is inferred.",
        ],
    }
    if not fit.success:
        values["reason"] = "optimizer did not converge within the caller evaluation budget"
    return Calculation(status=status, values=values)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=GasketPronyRelaxationSpectrumFit,
        evaluator=evaluate_gasket_prony_relaxation_spectrum_fit,
        units={
            "temperature_K": "K",
            "equilibrium_modulus_Pa": "Pa",
            "prony_branches[].modulus_Pa": "Pa",
            "prony_branches[].relaxation_time_s": "s",
            "maximum_modulus_Pa": "Pa",
            "weighted_sum_squared_residual": "1",
            "normalized_residual_rms": "1",
            "relaxation_time_fit_support_s[]": "s",
        },
        assumptions=(
            "Fit a finite positive generalized-Maxwell relaxation spectrum from caller step-strain observations at one exact material condition and temperature.",
            "Residuals are normalized by caller standard measurement uncertainties; no automatic branch-count selection, robust loss, or cross-condition transfer is performed.",
            "The fitted curve is a calibration result only and is not independent validation, seal acceptance or a qualified gasket constitutive law.",
        ),
        source_ids=(DATA_SOURCE_ID, FIT_SOURCE_ID),
        runtime_dependency_names=("scipy",),
        qualification="user_model",
    )]
