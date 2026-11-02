"""Caller-defined aqueous saturation indices for a set of candidate solids."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from numbers import Real
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec


class SaturationScreenSpecies(Contract):
    species_id: str = Field(min_length=1)
    dimensionless_activity: Positive
    log10_activity_absolute_bound: float = Field(
        default=0.0,
        ge=0.0,
        le=300.0,
        allow_inf_nan=False,
        description="Caller-reviewed absolute bound on log10(dimensionless activity); interpreted as a deterministic symmetric interval, not a probability distribution.",
    )


class SaturationScreenTerm(Contract):
    species_id: str = Field(min_length=1)
    stoichiometric_exponent: Positive


class CandidateSolid(Contract):
    solid_id: str = Field(min_length=1)
    log10_solubility_product: float
    log10_solubility_product_absolute_bound: float = Field(
        default=0.0,
        ge=0.0,
        le=300.0,
        allow_inf_nan=False,
        description="Caller-reviewed absolute bound on the log10 solubility product; interpreted as a deterministic symmetric interval, not a probability distribution.",
    )
    solubility_record_id: str = Field(min_length=1)
    solubility_evidence_source_id: str = Field(min_length=1)
    terms: tuple[SaturationScreenTerm, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_terms(self):
        ids = [term.species_id for term in self.terms]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate solid activity terms must be unique")
        return self


class AqueousSaturationScreen(Contract):
    schema_version: Literal["matintegrity.aqueous_saturation_screen.v1"] = "matintegrity.aqueous_saturation_screen.v1"
    assessment_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    temperature_K: Positive
    activity_standard_state: str = Field(min_length=1)
    species: tuple[SaturationScreenSpecies, ...] = Field(min_length=1, max_length=100)
    candidate_solids: tuple[CandidateSolid, ...] = Field(min_length=1, max_length=100)
    activity_state_provider_id: str = Field(min_length=1)
    activity_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    solubility_data_provider_id: str = Field(min_length=1)
    solubility_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    complete_species_inventory_reviewed: bool
    compatible_standard_states_reviewed: bool
    equilibrium_constants_temperature_reviewed: bool
    activity_interval_bounds_reviewed: bool = Field(
        default=False,
        description="Caller confirms that nonzero activity interval bounds have reviewed source, interpretation, units and applicability.",
    )
    solubility_product_interval_bounds_reviewed: bool = Field(
        default=False,
        description="Caller confirms that nonzero solubility-product interval bounds have reviewed source, interpretation and temperature applicability.",
    )
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_species_set(self):
        species_ids = [row.species_id for row in self.species]
        solid_ids = [row.solid_id for row in self.candidate_solids]
        if len(species_ids) != len(set(species_ids)):
            raise ValueError("aqueous species IDs must be unique")
        if len(solid_ids) != len(set(solid_ids)):
            raise ValueError("candidate solid IDs must be unique")
        known = set(species_ids)
        for solid in self.candidate_solids:
            unknown = {term.species_id for term in solid.terms} - known
            if unknown:
                raise ValueError(f"candidate solid references missing aqueous species: {sorted(unknown)}")
        evidence_by_id = {item.source_id: item for item in self.evidence}
        missing_evidence = sorted({
            solid.solubility_evidence_source_id
            for solid in self.candidate_solids
            if solid.solubility_evidence_source_id not in evidence_by_id
        })
        if missing_evidence:
            raise ValueError(f"candidate solid solubility evidence IDs are not declared: {missing_evidence}")
        evidence_ids = [item.source_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence source IDs must be unique")
        return self


def _log10_saturation_ratio(
    activities: Mapping[str, float], solid: CandidateSolid
) -> tuple[float, float]:
    log10_iap = math.fsum(
        term.stoichiometric_exponent * math.log10(activities[term.species_id])
        for term in solid.terms
    )
    return log10_iap, log10_iap - solid.log10_solubility_product


def _is_lowercase_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _assessment_input_digest_matches(result: AssessmentResult) -> bool:
    payload = {
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    }
    return _is_lowercase_sha256(result.input_digest) and canonical_digest(payload) == result.input_digest


def aqueous_saturation_screen(x: AqueousSaturationScreen) -> Calculation:
    uses_activity_bounds = any(row.log10_activity_absolute_bound > 0.0 for row in x.species)
    uses_solubility_bounds = any(
        row.log10_solubility_product_absolute_bound > 0.0 for row in x.candidate_solids
    )
    review_flags = {
        "complete_species_inventory_reviewed": x.complete_species_inventory_reviewed,
        "compatible_standard_states_reviewed": x.compatible_standard_states_reviewed,
        "equilibrium_constants_temperature_reviewed": x.equilibrium_constants_temperature_reviewed,
        "activity_interval_bounds_reviewed": x.activity_interval_bounds_reviewed,
        "solubility_product_interval_bounds_reviewed": x.solubility_product_interval_bounds_reviewed,
    }
    base = {
        "assessment_id": x.assessment_id,
        "solution_id": x.solution_id,
        "temperature_K": x.temperature_K,
        "activity_standard_state": x.activity_standard_state,
        "activity_state_provider_id": x.activity_state_provider_id,
        "activity_state_digest": x.activity_state_digest,
        "solubility_data_provider_id": x.solubility_data_provider_id,
        "solubility_data_digest": x.solubility_data_digest,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
        "evidence": [item.model_dump(mode="json") for item in x.evidence],
        "review_flags": review_flags,
        "review_requirements": {
            "complete_species_inventory_reviewed": True,
            "compatible_standard_states_reviewed": True,
            "equilibrium_constants_temperature_reviewed": True,
            "activity_interval_bounds_reviewed": uses_activity_bounds,
            "solubility_product_interval_bounds_reviewed": uses_solubility_bounds,
        },
    }
    reviews = {
        "complete_species_inventory_reviewed": x.complete_species_inventory_reviewed,
        "compatible_standard_states_reviewed": x.compatible_standard_states_reviewed,
        "equilibrium_constants_temperature_reviewed": x.equilibrium_constants_temperature_reviewed,
    }
    missing = [key for key, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing}, notes=("Review the complete aqueous inventory, activity conventions, and temperature applicability before interpreting saturation indices.",))

    missing_interval_reviews = []
    if uses_activity_bounds and not x.activity_interval_bounds_reviewed:
        missing_interval_reviews.append("activity_interval_bounds_reviewed")
    if uses_solubility_bounds and not x.solubility_product_interval_bounds_reviewed:
        missing_interval_reviews.append("solubility_product_interval_bounds_reviewed")
    if missing_interval_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_interval_reviews},
            notes=("Nonzero deterministic interval bounds require caller review of their source, interpretation and applicability before interval classifications are reported.",),
        )

    activities = {row.species_id: row.dimensionless_activity for row in x.species}
    activity_log_bounds = {row.species_id: row.log10_activity_absolute_bound for row in x.species}
    evidence_by_id = {item.source_id: item for item in x.evidence}
    candidates = []
    for solid in x.candidate_solids:
        try:
            log10_ion_activity_product, log10_saturation_ratio = _log10_saturation_ratio(activities, solid)
            log10_saturation_absolute_bound = math.fsum(
                term.stoichiometric_exponent * activity_log_bounds[term.species_id]
                for term in solid.terms
            ) + solid.log10_solubility_product_absolute_bound
            lower = log10_saturation_ratio - log10_saturation_absolute_bound
            upper = log10_saturation_ratio + log10_saturation_absolute_bound
        except (OverflowError, ValueError):
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "out_of_scope_reason": "saturation_index_arithmetic_overflow",
                    "unsupported_solid_id": solid.solid_id,
                    "completed_candidate_count": len(candidates),
                    "candidate_results": candidates,
                },
                notes=("The candidate saturation arithmetic exceeded the finite numeric range; no clipping or extrapolation was applied.",),
            )
        if not all(math.isfinite(value) for value in (
            log10_saturation_ratio, log10_saturation_absolute_bound, lower, upper,
        )):
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "nonfinite_saturation_index_or_bound", "candidate_results": candidates}, notes=("A finite saturation index or uncertainty bound could not be represented; no clipping or automatic phase selection was applied.",))
        candidates.append({
            "solid_id": solid.solid_id,
            "solubility_record_id": solid.solubility_record_id,
            "solubility_evidence": evidence_by_id[solid.solubility_evidence_source_id].model_dump(mode="json"),
            "log10_ion_activity_product": log10_ion_activity_product,
            "log10_saturation_ratio": log10_saturation_ratio,
            "log10_saturation_absolute_bound": log10_saturation_absolute_bound,
            "log10_saturation_ratio_lower_bound": lower,
            "log10_saturation_ratio_upper_bound": upper,
            "saturation_interval_classification": (
                "definitely_undersaturated" if upper < 0.0 else
                "definitely_supersaturated" if lower > 0.0 else
                "interval_overlaps_saturation"
            ),
            "saturation_ratio": 10.0 ** log10_saturation_ratio if -300.0 <= log10_saturation_ratio <= 300.0 else None,
            "saturation_ratio_outside_float_range": not (-300.0 <= log10_saturation_ratio <= 300.0),
            "candidate_is_supersaturated_by_declared_equilibrium": log10_saturation_ratio > 0.0,
            "activity_product_terms": [
                {"species_id": term.species_id, "activity": activities[term.species_id], "exponent": term.stoichiometric_exponent}
                for term in solid.terms
            ],
        })
    candidates.sort(key=lambda row: (-row["log10_saturation_ratio"], row["solid_id"]))
    return Calculation(
        status="computed",
        values=base | {
            "candidate_count": len(candidates),
            "candidate_results": candidates,
            "phase_selection_performed": False,
            "precipitated_amount_predicted": False,
        },
        notes=(
            "Each candidate saturation ratio uses caller-supplied dimensionless activities and a solubility product; absolute log10 bounds are propagated as deterministic worst-case intervals by the triangle inequality.",
            "Intervals are not probability distributions, confidence bounds, stable-phase selection, precipitation extent, nucleation, kinetics, competing-phase equilibrium, or corrosion rate.",
        ),
    )


def build_transport_saturation_callback_from_activity_provider(
    screen_template: AqueousSaturationScreen,
    *,
    transport_species_ids: Sequence[str],
    saturation_provider_id: str,
    saturation_provider_revision: str,
    activity_provider_id: str,
    activity_provider_revision: str,
    activity_provider_configuration_sha256: str,
    activity_provider: Callable[[float, int, float, tuple[float, ...]], Mapping[str, float]],
) -> Callable[[float, int, Sequence[float], dict[str, float]], dict[str, float]]:
    """Build a digest-bound transport callback from a caller activity provider and reviewed Ksp screen.

    The activity provider returns dimensionless activities for one local cell
    with signature ``(time_s, cell_index, temperature_K, concentrations)``.
    Solubility products, phase terms, standard state, source evidence and review
    gates are inherited from ``screen_template``. The resulting callback is
    compatible with ``solve_competing_solid_kinetic_transport``.
    """
    expected_species = tuple(row.species_id for row in screen_template.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("saturation template species order must match transport species order exactly")
    if not saturation_provider_id.strip() or not saturation_provider_revision.strip():
        raise ValueError("saturation provider identity and revision are required")
    if not activity_provider_id.strip() or not activity_provider_revision.strip():
        raise ValueError("activity provider identity and revision are required")
    if (len(activity_provider_configuration_sha256) != 64
        or any(character not in "0123456789abcdef" for character in activity_provider_configuration_sha256)):
        raise ValueError("activity provider configuration SHA-256 is invalid")
    if getattr(activity_provider, "configuration_sha256", None) != activity_provider_configuration_sha256:
        raise ValueError("activity callback configuration digest differs from the declared provider digest")
    if getattr(activity_provider, "provider_id", None) != activity_provider_id:
        raise ValueError("activity callback identity differs from the declared provider ID")
    if getattr(activity_provider, "provider_revision", None) != activity_provider_revision:
        raise ValueError("activity callback revision differs from the declared provider revision")
    provider_standard_state = getattr(activity_provider, "activity_standard_state", None)
    if provider_standard_state != screen_template.activity_standard_state:
        raise ValueError(
            "activity provider standard state must exactly match the reviewed saturation template"
        )
    required_reviews = (
        screen_template.complete_species_inventory_reviewed,
        screen_template.compatible_standard_states_reviewed,
        screen_template.equilibrium_constants_temperature_reviewed,
    )
    if not all(required_reviews):
        raise ValueError("saturation screen species, standard-state and temperature reviews are required")
    if any(row.log10_activity_absolute_bound > 0 for row in screen_template.species):
        raise ValueError("deterministic kinetics callback does not propagate activity uncertainty intervals")
    if any(row.log10_solubility_product_absolute_bound > 0 for row in screen_template.candidate_solids):
        raise ValueError("deterministic kinetics callback does not propagate solubility-product uncertainty intervals")

    screen_configuration = screen_template.model_dump(mode="json")
    screen_configuration["activity_state_provider_id"] = activity_provider_id
    screen_configuration["activity_state_digest"] = "0" * 64
    screen_configuration["species"] = [
        row | {"dimensionless_activity": 1.0} for row in screen_configuration["species"]
    ]
    configuration_digest = canonical_digest({
        "saturation_provider_id": saturation_provider_id,
        "saturation_provider_revision": saturation_provider_revision,
        "activity_provider_id": activity_provider_id,
        "activity_provider_revision": activity_provider_revision,
        "activity_provider_configuration_sha256": activity_provider_configuration_sha256,
        "activity_standard_state": provider_standard_state,
        "screen_configuration": screen_configuration,
        "transport_species_ids": list(expected_species),
    })
    phase_ids = {row.solid_id for row in screen_template.candidate_solids}
    temperature = screen_template.temperature_K

    def callback(
        global_time_s: float,
        cell_index: int,
        concentration_mol_m3: Sequence[float],
        _solid_inventory_mol_m3_by_phase: dict[str, float],
    ) -> dict[str, float]:
        if not math.isfinite(global_time_s) or cell_index < 0 or len(concentration_mol_m3) != len(expected_species):
            raise ValueError("activity callback state is not aligned to a valid transport cell and time")
        if any(isinstance(value, bool) or not isinstance(value, Real) for value in concentration_mol_m3):
            raise ValueError("cell concentrations must be numeric scalars")
        concentration = tuple(float(value) for value in concentration_mol_m3)
        if any(not math.isfinite(value) or value < 0 for value in concentration):
            raise ValueError("cell concentrations must be finite and nonnegative")
        raw_activities = activity_provider(
            float(global_time_s), int(cell_index), float(temperature), concentration
        )
        if not isinstance(raw_activities, Mapping) or set(raw_activities) != set(expected_species):
            raise ValueError("activity provider must return every transport species in the saturation template")
        activities: dict[str, float] = {}
        for species_id in expected_species:
            value = raw_activities[species_id]
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"dimensionless activity for {species_id} must be a numeric scalar")
            activity = float(value)
            if not math.isfinite(activity) or activity < 0:
                raise ValueError(f"dimensionless activity for {species_id} must be finite and nonnegative")
            activities[species_id] = activity
        result = {}
        for solid in screen_template.candidate_solids:
            if any(activities[term.species_id] == 0 for term in solid.terms):
                result[solid.solid_id] = 0.0
            else:
                _, log10_ratio = _log10_saturation_ratio(activities, solid)
                if not math.isfinite(log10_ratio) or not -300.0 <= log10_ratio <= 300.0:
                    raise ArithmeticError(f"saturation ratio for {solid.solid_id} is outside float support")
                result[solid.solid_id] = 10.0**log10_ratio
        if set(result) != phase_ids:
            raise ValueError("saturation solid identities changed unexpectedly")
        return result

    callback.configuration_sha256 = configuration_digest
    callback.provider_id = saturation_provider_id
    callback.provider_revision = saturation_provider_revision
    callback.activity_provider_id = activity_provider_id
    callback.activity_provider_revision = activity_provider_revision
    callback.activity_provider_configuration_sha256 = activity_provider_configuration_sha256
    callback.activity_standard_state = provider_standard_state
    callback.temperature_K = temperature
    lineage_fields = (
        "provider_id",
        "provider_revision",
        "configuration_sha256",
        "record_sha256",
        "source_request_sha256",
        "species_ids",
        "temperature_K",
        "sit_interaction_parameter_sha256",
        "sit_evidence_sha256",
        "sit_provider_configuration_sha256",
    )
    callback.activity_provider_lineage = {
        name: list(value) if isinstance((value := getattr(activity_provider, name, None)), tuple) else value
        for name in lineage_fields
        if getattr(activity_provider, name, None) is not None
    }
    callback.activity_provider_lineage_sha256 = canonical_digest(callback.activity_provider_lineage)
    return callback


def screen_mass_action_calculation(
    calculation: Calculation | AssessmentResult,
    *,
    assessment_id: str,
    solution_id: str,
    candidate_solids: tuple[CandidateSolid, ...],
    activity_log10_absolute_bounds: Mapping[str, float] | None = None,
    speciation_knot_index: int | None = None,
    solubility_data_provider_id: str,
    solubility_data_digest: str,
    complete_species_inventory_reviewed: bool,
    compatible_standard_states_reviewed: bool,
    equilibrium_constants_temperature_reviewed: bool,
    activity_interval_bounds_reviewed: bool = False,
    solubility_product_interval_bounds_reviewed: bool = False,
    evidence: tuple[Evidence, ...],
) -> Calculation:
    """Build a saturation-screen request from a computed aqueous activity result.

    The upstream result is retained by digest; only its explicit species activities,
    temperature, standard state, and declared provider/record lineage are forwarded.
    Exact-knot B-dot histories require a caller-selected knot and retain its individual
    request, result, clock and parameter-record identity.
    """
    upstream_digest = canonical_digest(calculation.model_dump(mode="json"))
    selected_knot_lineage: dict[str, object] | None = None
    upstream_values = calculation.values
    candidate_workflow_lineage: dict[str, object] | None = None
    is_candidate_network = (
        isinstance(calculation, AssessmentResult)
        and calculation.model_id == "integration.aqueous_candidate_network_speciation"
    )
    if is_candidate_network:
        wrapper_values = calculation.values
        raw_speciation = wrapper_values.get("speciation")
        raw_workflow = calculation.inputs.get("candidate_workflow_result")
        workflow_digest = calculation.inputs.get("candidate_workflow_result_sha256")
        workflow_values = raw_workflow.get("values") if isinstance(raw_workflow, Mapping) else None
        workflow_assembly = workflow_values.get("assembly") if isinstance(workflow_values, Mapping) else None
        assembly_values = workflow_assembly.get("values") if isinstance(workflow_assembly, Mapping) else None
        workflow_context = raw_workflow.get("context") if isinstance(raw_workflow, Mapping) else None
        try:
            expected_workflow_input_digest = canonical_digest({
                "model_id": raw_workflow["model_id"],
                "model_version": raw_workflow["model_version"],
                "inputs": raw_workflow["inputs"],
                "context": workflow_context,
            })
        except (KeyError, TypeError, ValueError):
            expected_workflow_input_digest = None
        try:
            speciation_result = Calculation.model_validate(raw_speciation)
        except (ValidationError, TypeError, ValueError):
            speciation_result = None
        if (
            not isinstance(raw_workflow, Mapping)
            or not _is_lowercase_sha256(workflow_digest)
            or canonical_digest(raw_workflow) != workflow_digest
            or raw_workflow.get("model_id") != "integration.aqueous_candidate_network_workflow"
            or raw_workflow.get("status") != "computed"
            or raw_workflow.get("input_digest") != expected_workflow_input_digest
            or not isinstance(assembly_values, Mapping)
            or not isinstance(workflow_assembly, Mapping)
            or workflow_assembly.get("status") != "computed"
            or not isinstance(speciation_result, Calculation)
            or speciation_result.status != "computed"
            or canonical_digest(speciation_result.model_dump(mode="json"))
            != wrapper_values.get("speciation_result_sha256")
            or not _is_lowercase_sha256(wrapper_values.get("mass_action_system_sha256"))
            or wrapper_values.get("mass_action_system_sha256")
            != assembly_values.get("mass_action_system_sha256")
        ):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "upstream_model_id": calculation.model_id,
                "upstream_record_issue": "candidate network workflow or nested speciation digest lineage is incomplete",
            }, notes=("The candidate-network handoff must retain a matching computed workflow, assembled-system digest and nested speciation result.",))
        upstream_values = dict(speciation_result.values) | {
            "temperature_K": wrapper_values.get("temperature_K"),
            "activity_standard_state": wrapper_values.get("activity_standard_state"),
            "activity_provider_id": speciation_result.values.get("activity_provider_id"),
            "activity_provider_revision": speciation_result.values.get("activity_provider_revision"),
            "activity_record_digest": speciation_result.values.get("activity_record_digest"),
        }
        candidate_workflow_lineage = {
            "upstream_candidate_workflow_result_sha256": workflow_digest,
            "upstream_candidate_workflow_input_digest": wrapper_values.get("candidate_workflow_input_digest"),
            "upstream_candidate_workflow_sha256": wrapper_values.get("candidate_workflow_sha256"),
            "upstream_candidate_mass_action_system_sha256": wrapper_values.get("mass_action_system_sha256"),
            "upstream_candidate_speciation_result_sha256": wrapper_values.get("speciation_result_sha256"),
        }
    is_bdot_history = (
        isinstance(calculation, AssessmentResult)
        and calculation.model_id == "integration.aqueous_bdot_speciation_history"
    )
    if is_bdot_history:
        if (
            isinstance(speciation_knot_index, bool)
            or not isinstance(speciation_knot_index, int)
            or speciation_knot_index < 0
        ):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "missing_or_invalid_speciation_knot_index": speciation_knot_index,
            }, notes=("A B-dot history must be screened at one explicitly selected exact knot.",))
        history_values = calculation.values
        knots = history_values.get("knot_results")
        parameter_digests = history_values.get("parameter_record_sha256_by_knot")
        requests = calculation.inputs.get("knot_requests")
        times = history_values.get("elapsed_time_s")
        temperatures = history_values.get("temperature_K")
        if (
            history_values.get("complete_history") is not True
            or not isinstance(knots, list)
            or history_values.get("knot_results_sha256") != canonical_digest(knots)
            or not isinstance(parameter_digests, list)
            or not isinstance(requests, list)
            or not isinstance(times, list)
            or not isinstance(temperatures, list)
            or not (len(knots) == len(parameter_digests) == len(requests) == len(times) == len(temperatures))
            or speciation_knot_index >= len(knots)
        ):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "upstream_record_issue": "B-dot exact-knot history or parameter lineage is incomplete",
                "speciation_knot_index": speciation_knot_index,
            }, notes=("The selected B-dot knot cannot be used unless the complete history and aligned source records verify.",))
        knot = knots[speciation_knot_index]
        knot_values = knot.get("values") if isinstance(knot, Mapping) else None
        request = requests[speciation_knot_index]
        expected_parameter_digest = parameter_digests[speciation_knot_index]
        if (
            not isinstance(knot, Mapping)
            or knot.get("knot_index") != speciation_knot_index
            or knot.get("status") != "computed"
            or knot.get("time_s") != times[speciation_knot_index]
            or knot.get("temperature_K") != temperatures[speciation_knot_index]
            or not isinstance(request, Mapping)
            or canonical_digest(request) != knot.get("request_sha256")
            or not _is_lowercase_sha256(expected_parameter_digest)
            or request.get("parameter_record_sha256") != expected_parameter_digest
            or request.get("parameter_provider_id") != history_values.get("parameter_provider_id")
            or request.get("parameter_provider_revision") != history_values.get("parameter_provider_revision")
            or not isinstance(knot_values, Mapping)
            or knot_values.get("parameter_record_sha256") != expected_parameter_digest
            or isinstance(knot.get("time_s"), bool)
            or not isinstance(knot.get("time_s"), Real)
            or not math.isfinite(float(knot.get("time_s")))
            or float(knot.get("time_s")) < 0.0
            or isinstance(knot.get("temperature_K"), bool)
            or not isinstance(knot.get("temperature_K"), Real)
            or not math.isfinite(float(knot.get("temperature_K")))
            or float(knot.get("temperature_K")) <= 0.0
        ):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "upstream_record_issue": "selected B-dot knot differs from its exact request or parameter record",
                "speciation_knot_index": speciation_knot_index,
            }, notes=("No phase saturation is screened when the selected knot's time, temperature, request or parameter digest disagrees.",))
        try:
            knot_calculation = Calculation.model_validate({
                "values": knot_values,
                "status": knot["status"],
                "notes": knot.get("notes", []),
            })
        except (ValidationError, TypeError, ValueError):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "upstream_record_issue": "selected B-dot knot result does not satisfy the Calculation contract",
                "speciation_knot_index": speciation_knot_index,
            })
        if canonical_digest(knot_calculation.model_dump(mode="json")) != knot.get("result_sha256"):
            return Calculation(status="needs_data", values={
                "upstream_assessment_sha256": upstream_digest,
                "upstream_record_issue": "selected B-dot knot result digest mismatch",
                "speciation_knot_index": speciation_knot_index,
            })
        upstream_values = dict(knot_values) | {
            "temperature_K": knot["temperature_K"],
            "activity_provider_id": history_values.get("parameter_provider_id"),
            "activity_provider_revision": history_values.get("parameter_provider_revision"),
            "activity_record_digest": expected_parameter_digest,
            "input_digest": knot["request_sha256"],
        }
        selected_knot_lineage = {
            "upstream_speciation_knot_index": speciation_knot_index,
            "upstream_speciation_knot_time_s": knot["time_s"],
            "upstream_speciation_knot_temperature_K": knot["temperature_K"],
            "upstream_speciation_knot_request_sha256": knot["request_sha256"],
            "upstream_speciation_knot_result_sha256": knot["result_sha256"],
            "upstream_speciation_parameter_record_sha256": expected_parameter_digest,
        }
    elif speciation_knot_index is not None:
        return Calculation(status="needs_data", values={
            "upstream_calculation_sha256": upstream_digest,
            "unexpected_speciation_knot_index": speciation_knot_index,
        }, notes=("A knot index is accepted only for a registered exact-knot B-dot speciation history.",))
    if isinstance(calculation, AssessmentResult) and calculation.model_id not in {
        "chemistry.aqueous_mass_action_speciation",
        "chemistry.aqueous_davies_self_consistent_speciation",
        "chemistry.aqueous_tabulated_activity_speciation",
        "chemistry.aqueous_bdot_self_consistent_speciation",
        "integration.aqueous_bdot_speciation_history",
        "integration.aqueous_candidate_network_speciation",
    }:
        return Calculation(
            status="out_of_scope",
            values={
                "upstream_model_id": calculation.model_id,
                "upstream_assessment_sha256": upstream_digest,
                "out_of_scope_reason": "unsupported_upstream_model_for_aqueous_activity_screen",
            },
            notes=("Only registered aqueous activity solvers or supported digest-pinned composition wrappers can supply this activity state.",),
        )
    if isinstance(calculation, AssessmentResult) and not _assessment_input_digest_matches(calculation):
        return Calculation(
            status="needs_data",
            values={
                "upstream_assessment_sha256": canonical_digest(calculation.model_dump(mode="json")),
                "upstream_record_issue": "registry_input_digest_does_not_match_inputs_and_context",
                "upstream_model_id": calculation.model_id,
            },
            notes=("The registry assessment input digest does not verify against its model ID, version, inputs and run context; no saturation screen was run.",),
        )
    if calculation.status != "computed":
        return Calculation(
            status=calculation.status,
            values={
                "upstream_calculation_sha256": upstream_digest,
                "upstream_status": calculation.status,
            },
            notes=("The upstream aqueous calculation did not produce a computed state; no saturation screen was run.",),
        )
    values = upstream_values
    required = {"temperature_K", "activity_standard_state", "species"}
    missing = sorted(required - set(values))
    if missing:
        return Calculation(
            status="needs_data",
            values={"missing_upstream_fields": missing},
            notes=("The upstream record lacks fields required to bind its aqueous activity state.",),
        )
    temperature = values["temperature_K"]
    standard_state = values["activity_standard_state"]
    invalid_state_fields = []
    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, Real)
        or not math.isfinite(float(temperature))
        or temperature <= 0
    ):
        invalid_state_fields.append("temperature_K")
    if not isinstance(standard_state, str) or not standard_state.strip():
        invalid_state_fields.append("activity_standard_state")
    if invalid_state_fields:
        return Calculation(
            status="needs_data",
            values={"upstream_calculation_sha256": upstream_digest, "invalid_upstream_fields": invalid_state_fields},
            notes=("The upstream temperature and activity standard state must be valid before saturation screening.",),
        )
    species_rows = values["species"]
    if not isinstance(species_rows, list) or any(
        not isinstance(row, dict)
        or not {"species_id", "dimensionless_activity"}.issubset(row)
        for row in species_rows
    ):
        return Calculation(
            status="needs_data",
            values={
                "upstream_calculation_sha256": upstream_digest,
                "upstream_record_issue": "species_activity_rows_are_not_aligned",
            },
            notes=("The upstream species activity rows are missing IDs or dimensionless activities.",),
        )
    invalid_activity_rows = []
    for row in species_rows:
        species_id = row["species_id"]
        activity = row["dimensionless_activity"]
        if not isinstance(species_id, str) or not species_id.strip():
            invalid_activity_rows.append("species_id_must_be_nonempty_text")
        if (
            isinstance(activity, bool)
            or not isinstance(activity, Real)
            or not math.isfinite(float(activity))
            or activity <= 0
        ):
            invalid_activity_rows.append(f"dimensionless_activity_must_be_finite_and_positive:{species_id}")
    if invalid_activity_rows:
        return Calculation(
            status="needs_data",
            values={"upstream_calculation_sha256": upstream_digest, "invalid_activity_rows": invalid_activity_rows},
            notes=("The upstream activity state contains a species ID or activity value that cannot be used in a saturation screen.",),
        )
    upstream_species_list = [row["species_id"] for row in species_rows]
    upstream_species_ids = set(upstream_species_list)
    if len(upstream_species_list) != len(upstream_species_ids):
        return Calculation(
            status="needs_data",
            values={
                "upstream_calculation_sha256": upstream_digest,
                "upstream_record_issue": "duplicate_species_activity_rows",
            },
            notes=("The upstream aqueous result repeats a species identity; no saturation request was composed.",),
        )
    if activity_log10_absolute_bounds is not None:
        supplied_bound_ids = set(activity_log10_absolute_bounds)
        if supplied_bound_ids != upstream_species_ids:
            return Calculation(
                status="needs_data",
                values={
                    "upstream_calculation_sha256": upstream_digest,
                    "missing_activity_bound_species_ids": sorted(upstream_species_ids - supplied_bound_ids),
                    "unknown_activity_bound_species_ids": sorted(supplied_bound_ids - upstream_species_ids),
                },
                notes=("Caller activity interval bounds must cover the exact upstream species identity set; no bound is silently omitted or applied to an unknown species.",),
            )
    activity_log10_absolute_bounds = activity_log10_absolute_bounds or {}
    provider_id = (
        values.get("activity_provider_id")
        or values.get("davies_A_provider_id")
        or values.get("activity_table_provider_id")
        or values.get("parameter_provider_id")
    )
    provider_revision = (
        values.get("activity_provider_revision")
        or values.get("davies_A_provider_revision")
        or values.get("activity_table_provider_revision")
        or values.get("parameter_provider_revision")
    )
    provider_record_digest = (
        values.get("activity_record_digest")
        or values.get("davies_A_record_digest")
        or values.get("activity_table_record_digest")
        or values.get("parameter_record_sha256")
    )
    provider_identity_valid = isinstance(provider_id, str) and bool(provider_id.strip())
    provider_revision_valid = isinstance(provider_revision, str) and bool(provider_revision.strip())
    provider_digest_valid = _is_lowercase_sha256(provider_record_digest)
    if not (provider_identity_valid and provider_revision_valid and provider_digest_valid):
        return Calculation(
            status="needs_data",
            values={
                "upstream_calculation_sha256": upstream_digest,
                "missing_activity_lineage": [
                    name for name, valid in (
                        ("provider_id", provider_identity_valid),
                        ("provider_revision", provider_revision_valid),
                        ("provider_record_digest_sha256", provider_digest_valid),
                    ) if not valid
                ],
            },
            notes=("The upstream aqueous activity provider lineage is incomplete; no saturation screen was run.",),
        )
    is_tabulated_activity = (
        isinstance(calculation, AssessmentResult)
        and calculation.model_id == "chemistry.aqueous_tabulated_activity_speciation"
    ) or any(key in values for key in (
        "activity_table_support_by_species",
        "activity_table_configuration_digest",
        "activity_table_record_digest",
    ))
    activity_table_lineage = None
    if is_tabulated_activity:
        lineage_fields = (
            "activity_table_temperature_K",
            "activity_table_temperature_support_K_by_species",
            "activity_table_support_by_species",
            "activity_table_interpolation",
            "activity_table_configuration_digest",
            "activity_table_record_digest",
            "activity_table_evidence",
            "activity_table_point_count",
            "maximum_activity_table_points",
            "ionic_strength_mol_kg",
        )
        missing_table_fields = [key for key in lineage_fields if key not in values]
        if missing_table_fields:
            return Calculation(
                status="needs_data",
                values={
                    "upstream_calculation_sha256": upstream_digest,
                    "missing_activity_table_lineage_fields": missing_table_fields,
                },
                notes=("A tabulated-activity result is missing required temperature, ionic-strength support or digest lineage; no saturation screen was run.",),
            )
        expected_interpolation = {
            "fixed_temperature": "piecewise_linear_in_ionic_strength_for_ln_gamma_without_extrapolation",
            "temperature_slices": "piecewise_linear_in_temperature_and_ionic_strength_for_ln_gamma_without_extrapolation",
        }
        table_temperature = values["activity_table_temperature_K"]
        query_ionic_strength = values["ionic_strength_mol_kg"]
        support_by_species = values["activity_table_support_by_species"]
        temperature_support_by_species = values["activity_table_temperature_support_K_by_species"]
        config_digest = values["activity_table_configuration_digest"]
        record_digest = values["activity_table_record_digest"]
        point_count_total = values["activity_table_point_count"]
        point_count_budget = values["maximum_activity_table_points"]
        table_evidence = values["activity_table_evidence"]
        issues = []
        system_temperature = values["temperature_K"]
        if (
            isinstance(table_temperature, bool)
            or not isinstance(table_temperature, Real)
            or not math.isfinite(float(table_temperature))
            or table_temperature <= 0
            or isinstance(system_temperature, bool)
            or not isinstance(system_temperature, Real)
            or not math.isfinite(float(system_temperature))
            or system_temperature <= 0
            or table_temperature != system_temperature
        ):
            issues.append("activity_table_temperature_does_not_match_system")
        if isinstance(query_ionic_strength, bool) or not isinstance(query_ionic_strength, Real) or not math.isfinite(float(query_ionic_strength)) or query_ionic_strength < 0:
            issues.append("upstream_ionic_strength_is_invalid")
        if not _is_lowercase_sha256(config_digest) or not _is_lowercase_sha256(record_digest):
            issues.append("activity_table_digest_is_invalid")
        if (
            not isinstance(point_count_total, int)
            or isinstance(point_count_total, bool)
            or point_count_total < 1
            or not isinstance(point_count_budget, int)
            or isinstance(point_count_budget, bool)
            or point_count_budget < point_count_total
        ):
            issues.append("activity_table_point_count_or_budget_is_invalid")
        allowed_evidence_origins = {"measured", "open_dataset", "model_prediction", "user_declared", "synthetic"}
        if not isinstance(table_evidence, list) or not table_evidence or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("source_id"), str)
            or not item["source_id"].strip()
            or not isinstance(item.get("citation"), str)
            or not item["citation"].strip()
            or item.get("origin") not in allowed_evidence_origins
            or (item.get("origin") == "open_dataset" and not (isinstance(item.get("license_id"), str) and item["license_id"].strip()))
            for item in table_evidence
        ):
            issues.append("activity_table_evidence_is_invalid")
        requires_row_ids = isinstance(table_evidence, list) and any(
            isinstance(item, Mapping) and item.get("origin") in {"measured", "open_dataset"}
            for item in table_evidence
        )
        if not isinstance(support_by_species, Mapping) or set(support_by_species) != upstream_species_ids:
            issues.append("activity_table_support_species_set_is_not_exact")
        if not isinstance(temperature_support_by_species, Mapping) or set(temperature_support_by_species) != upstream_species_ids:
            issues.append("activity_table_temperature_support_species_set_is_not_exact")
        supported_point_count = 0
        if not issues:
            for species_id in upstream_species_list:
                species_support = support_by_species[species_id]
                temperature_bounds = temperature_support_by_species[species_id]
                if not isinstance(species_support, Mapping) or species_support.get("mode") not in expected_interpolation:
                    issues.append(f"activity_table_mode_is_invalid:{species_id}")
                    continue
                mode = species_support["mode"]
                if values["activity_table_interpolation"] != expected_interpolation[mode]:
                    issues.append(f"activity_table_interpolation_mode_mismatch:{species_id}")
                    continue
                slices = species_support.get("temperature_slices")
                if not isinstance(slices, list) or not slices:
                    issues.append(f"activity_table_support_slices_are_missing:{species_id}")
                    continue
                if not isinstance(temperature_bounds, list) or len(temperature_bounds) != 2:
                    issues.append(f"activity_table_temperature_bounds_are_invalid:{species_id}")
                    continue
                temperatures = []
                for support in slices:
                    if not isinstance(support, Mapping):
                        issues.append(f"activity_table_slice_is_invalid:{species_id}")
                        continue
                    temperature = support.get("temperature_K")
                    ionic_min = support.get("ionic_strength_min_mol_kg")
                    ionic_max = support.get("ionic_strength_max_mol_kg")
                    point_count = support.get("ionic_strength_point_count")
                    source_record_id_count = support.get("source_record_id_count")
                    source_record_ids_sha256 = support.get("source_record_ids_sha256")
                    numeric = (temperature, ionic_min, ionic_max)
                    if any(isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)) for value in numeric):
                        issues.append(f"activity_table_slice_support_is_nonfinite:{species_id}")
                        continue
                    if ionic_min < 0 or ionic_max < ionic_min or not isinstance(point_count, int) or isinstance(point_count, bool) or point_count < 2:
                        issues.append(f"activity_table_slice_extent_is_invalid:{species_id}")
                        continue
                    supported_point_count += point_count
                    if (
                        not isinstance(source_record_id_count, int)
                        or isinstance(source_record_id_count, bool)
                        or not 0 <= source_record_id_count <= point_count
                        or not _is_lowercase_sha256(source_record_ids_sha256)
                        or (requires_row_ids and source_record_id_count != point_count)
                    ):
                        issues.append(f"activity_table_record_lineage_is_invalid:{species_id}")
                    if not ionic_min <= query_ionic_strength <= ionic_max:
                        issues.append(f"computed_ionic_strength_outside_activity_table_support:{species_id}")
                    temperatures.append(float(temperature))
                if temperatures:
                    if any(right <= left for left, right in zip(temperatures[:-1], temperatures[1:], strict=True)):
                        issues.append(f"activity_table_temperature_knots_are_not_ordered:{species_id}")
                    if not temperatures[0] <= table_temperature <= temperatures[-1]:
                        issues.append(f"system_temperature_outside_activity_table_support:{species_id}")
                    if temperature_bounds != [temperatures[0], temperatures[-1]]:
                        issues.append(f"activity_table_temperature_bounds_mismatch:{species_id}")
                if mode == "fixed_temperature" and len(slices) != 1:
                    issues.append(f"fixed_temperature_table_has_multiple_slices:{species_id}")
                if mode == "temperature_slices" and len(slices) < 2:
                    issues.append(f"temperature_sliced_table_has_fewer_than_two_slices:{species_id}")
        if not issues and supported_point_count != point_count_total:
            issues.append("activity_table_point_count_does_not_match_species_support")
        if issues:
            return Calculation(
                status="needs_data",
                values={
                    "upstream_calculation_sha256": upstream_digest,
                    "activity_table_lineage_issues": issues,
                },
                notes=("The activity-table temperature and ionic-strength query does not match the declared support; no saturation screen was run.",),
            )
        activity_table_lineage = {key: values[key] for key in lineage_fields if key != "ionic_strength_mol_kg"}
    digest = upstream_digest
    request = AqueousSaturationScreen(
        assessment_id=assessment_id,
        solution_id=solution_id,
        temperature_K=float(temperature),
        activity_standard_state=standard_state,
        species=tuple(
            SaturationScreenSpecies(
                species_id=row["species_id"],
                dimensionless_activity=float(row["dimensionless_activity"]),
                log10_activity_absolute_bound=activity_log10_absolute_bounds.get(row["species_id"], 0.0),
            )
            for row in species_rows
        ),
        candidate_solids=candidate_solids,
        activity_state_provider_id=provider_id,
        activity_state_digest=digest,
        solubility_data_provider_id=solubility_data_provider_id,
        solubility_data_digest=solubility_data_digest,
        complete_species_inventory_reviewed=complete_species_inventory_reviewed,
        compatible_standard_states_reviewed=compatible_standard_states_reviewed,
        equilibrium_constants_temperature_reviewed=equilibrium_constants_temperature_reviewed,
        activity_interval_bounds_reviewed=activity_interval_bounds_reviewed,
        solubility_product_interval_bounds_reviewed=solubility_product_interval_bounds_reviewed,
        evidence=evidence,
    )
    result = aqueous_saturation_screen(request)
    return Calculation(
        status=result.status,
        values=result.values | {
            "upstream_mass_action_result_sha256": digest,
            "upstream_result_representation": "registry_assessment" if isinstance(calculation, AssessmentResult) else "standalone_calculation",
            "upstream_model_id": calculation.model_id if isinstance(calculation, AssessmentResult) else None,
            "upstream_model_version": calculation.model_version if isinstance(calculation, AssessmentResult) else None,
            "upstream_model_source_ids": list(calculation.source_ids) if isinstance(calculation, AssessmentResult) else [],
            "upstream_model_qualification": calculation.qualification if isinstance(calculation, AssessmentResult) else None,
            "upstream_registry_input_sha256": calculation.input_digest if isinstance(calculation, AssessmentResult) else None,
            "upstream_model_input_sha256": values.get("input_digest"),
            "upstream_activity_provider_revision": provider_revision,
            "upstream_activity_record_digest": provider_record_digest,
            "upstream_activity_table_lineage": activity_table_lineage,
            **(selected_knot_lineage or {}),
            **(candidate_workflow_lineage or {}),
        },
        notes=("The saturation screen is bound to a computed caller-defined aqueous mass-action result.", *result.notes),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.aqueous_saturation_screen",
        AqueousSaturationScreen,
        aqueous_saturation_screen,
        {
            "temperature_K": "K",
            "candidate_results.log10_ion_activity_product": "1",
            "candidate_results.log10_saturation_ratio": "1",
            "candidate_results.log10_saturation_absolute_bound": "1",
            "candidate_results.log10_saturation_ratio_lower_bound": "1",
            "candidate_results.log10_saturation_ratio_upper_bound": "1",
            "candidate_results.saturation_ratio": "1",
            "candidate_count": "1",
            "phase_selection_performed": "1",
            "precipitated_amount_predicted": "1",
        },
        (
            "Caller-supplied dimensionless aqueous activities, activity standard state, candidate-solid activity products, and temperature-applicable solubility products.",
            "Reports separate saturation indices only; it does not select phases, solve precipitation extent, infer kinetics, or predict corrosion.",
        ),
        ("caller_aqueous_candidate_saturation_screen",),
    )]
