"""Explicit caller-parameterized engineering correlations with SI inputs."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

SOURCE_ID = "caller_parameterized_engineering_correlation_arithmetic"


class CorrelationBasis(Contract):
    source_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    license_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    applicability_and_units_reviewed: bool
    computational_use_authorized: bool


class CorrelationRequest(Contract):
    basis: CorrelationBasis

    @model_validator(mode="after")
    def bind_reviewed_record(self):
        digest = canonical_digest(self.model_dump(mode="json", exclude={"basis"}))
        basis = self.basis
        if digest != basis.record_sha256 or not any(
            e.source_id == basis.source_id and e.sha256 == digest and e.license_id == basis.license_id
            for e in basis.evidence
        ):
            raise ValueError("licensed Evidence must pin the complete declared inputs and coefficients")
        if not (basis.applicability_and_units_reviewed and basis.computational_use_authorized):
            raise ValueError("correlation units, applicability and computational use require review")
        return self


class BrinellSurfaceObservation(Contract):
    surface_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hardness_HBW: Positive
    expanded_uncertainty_HBW: Nonnegative
    scale_id: Literal["HBW"]
    method_revision_id: str = Field(min_length=1)
    test_force_N: Positive
    indenter_diameter_m: Positive
    dwell_time_s: Positive
    test_temperature_K: Positive


class MatingBrinellHardnessDifference(CorrelationRequest):
    mating_pair_id: str = Field(min_length=1)
    first: BrinellSurfaceObservation
    second: BrinellSurfaceObservation
    comparison_direction: Literal["first_harder", "second_harder", "either"]
    minimum_declared_difference_HBW: Nonnegative
    pairing_test_conditions_and_interval_interpretation_reviewed: bool

    @model_validator(mode="after")
    def distinct_surfaces_and_conditions(self):
        if self.first.surface_id == self.second.surface_id:
            raise ValueError("mating hardness comparison requires distinct surface identities")
        names = (
            "scale_id",
            "method_revision_id",
            "test_force_N",
            "indenter_diameter_m",
            "dwell_time_s",
            "test_temperature_K",
        )
        if any(getattr(self.first, name) != getattr(self.second, name) for name in names):
            raise ValueError(
                "Brinell test conditions must match exactly; no scale or condition conversion is inferred"
            )
        return self


def mating_brinell_hardness_difference(x: MatingBrinellHardnessDifference) -> Calculation:
    base = {
        "mating_pair_id": x.mating_pair_id,
        "comparison_direction": x.comparison_direction,
        "minimum_declared_difference_HBW": x.minimum_declared_difference_HBW,
        "observation_manifest": [x.first.model_dump(mode="json"), x.second.model_dump(mode="json")],
    }
    if not x.pairing_test_conditions_and_interval_interpretation_reviewed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Mating identities, common test conditions and interval interpretation require review.",),
        )
    difference = Rational(x.first.hardness_HBW) - Rational(x.second.hardness_HBW)
    spread = Rational(x.first.expanded_uncertainty_HBW) + Rational(x.second.expanded_uncertainty_HBW)
    low, high = difference - spread, difference + spread
    if x.comparison_direction == "second_harder":
        low, high = -high, -low
    elif x.comparison_direction == "either":
        low, high = (
            (Rational(0), max(abs(low), abs(high)))
            if low <= 0 <= high
            else (min(abs(low), abs(high)), max(abs(low), abs(high)))
        )
    threshold = Rational(x.minimum_declared_difference_HBW)
    state = (
        "within_declared_requirement"
        if low >= threshold
        else "outside_declared_requirement"
        if high < threshold
        else "uncertainty_overlap"
    )
    exact = {
        "signed_first_minus_second_HBW": difference,
        "comparison_interval_lower_HBW": low,
        "comparison_interval_upper_HBW": high,
    }
    try:
        values = {key: float(value) for key, value in exact.items()}
        if any(value and values[key] == 0 for key, value in exact.items()):
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("A hardness difference or interval bound exceeds numeric support.",),
        )
    return Calculation(
        values=base | values | {"comparison_state": state},
        notes=(
            "HBW observations under exactly matching declared conditions; uncertainty intervals are subtracted conservatively without assuming statistical independence or combined coverage.",
            "Either-direction comparison transforms the complete signed interval through absolute value, including zero-crossing support. No standard differential threshold, HB/HBS/HBW equivalence, galling resistance, wear, sealing, material suitability or valve acceptance is inferred.",
        ),
    )


class DeclaredFluxBasicityRatio(CorrelationRequest):
    flux_condition_id: str = Field(min_length=1)
    index_definition_id: str = Field(min_length=1)
    input_mass_basis: Literal["mass_fraction", "mass_percent", "mass_ppm"]
    compound_assay: dict[str, Nonnegative | None] = Field(min_length=1, max_length=100)
    numerator_weights: dict[str, Nonnegative] = Field(min_length=1, max_length=100)
    denominator_weights: dict[str, Nonnegative] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def declared_compound_basis(self):
        limit = {"mass_fraction": 1, "mass_percent": 100, "mass_ppm": 1000000}[self.input_mass_basis]
        if any(
            not key.strip()
            for mapping in (self.compound_assay, self.numerator_weights, self.denominator_weights)
            for key in mapping
        ):
            raise ValueError("flux compound identities cannot be blank")
        if sum((Rational(v) for v in self.compound_assay.values() if v is not None), Rational(0)) > limit:
            raise ValueError("known compound assay sum exceeds its mass basis")
        if not any(self.numerator_weights.values()) or not any(self.denominator_weights.values()):
            raise ValueError("each weighted side requires at least one positive weight")
        return self


def declared_flux_basicity_ratio(x: DeclaredFluxBasicityRatio) -> Calculation:
    base = {
        "flux_condition_id": x.flux_condition_id,
        "index_definition_id": x.index_definition_id,
        "input_mass_basis": x.input_mass_basis,
    }
    used = {
        key
        for weights in (x.numerator_weights, x.denominator_weights)
        for key, value in weights.items()
        if value > 0
    }
    missing = sorted(key for key in used if x.compound_assay.get(key) is None)
    if missing:
        return Calculation(
            status="needs_data",
            values=base | {"missing_compound_ids": missing},
            notes=("Every positively weighted compound requires an explicit assay; missing is not zero.",),
        )

    def weighted(weights):
        return sum(
            (
                Rational(weight) * Rational(x.compound_assay[key])
                for key, weight in weights.items()
                if weight > 0
            ),
            Rational(0),
        )

    numerator, denominator = weighted(x.numerator_weights), weighted(x.denominator_weights)
    if not denominator:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The declared weighted denominator is zero; no basicity ratio is defined.",),
        )
    exact = numerator / denominator
    try:
        ratio = float(exact)
        if exact and ratio == 0:
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The declared compound ratio exceeds numeric support.",),
        )
    sums = {}
    for name, value in (("weighted_numerator", numerator), ("weighted_denominator", denominator)):
        try:
            converted = float(value)
            sums[name] = None if value and converted == 0 else converted
        except OverflowError:
            sums[name] = None
    return Calculation(
        values=base | sums | {"basicity_ratio": ratio},
        notes=(
            "Caller-defined ratio of weighted compound mass assays; no named index coefficients, oxide conversion, unreported balance or compound alias is inferred. Weighted sums retain the input mass basis and may be null when only the ratio is representable.",
            "A composition descriptor is not gas-slag-metal equilibrium, oxygen potential/content, inclusion population, diffusible hydrogen, toughness, flux category or welding approval.",
        ),
    )


class DeclaredConsumableDepositionRate(CorrelationRequest):
    process_id: str = Field(min_length=1)
    consumable_condition_id: str = Field(min_length=1)
    material_cross_section_area_m2: Positive
    material_density_kg_m3: Positive
    arc_on_feed_speed_m_s: Nonnegative
    captured_feed_mass_fraction: Fraction
    arc_on_time_fraction: Fraction
    feed_volume_basis: Literal["continuous_uniform_material_cross_section"]
    cross_section_density_capture_and_time_basis_reviewed: bool


def declared_consumable_deposition_rate(x: DeclaredConsumableDepositionRate) -> Calculation:
    base = {
        "process_id": x.process_id,
        "consumable_condition_id": x.consumable_condition_id,
        "feed_volume_basis": x.feed_volume_basis,
    }
    if not x.cross_section_density_capture_and_time_basis_reviewed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Material section, density, capture and active/feed clock roles require review.",),
        )
    feed = (
        Rational(x.material_cross_section_area_m2)
        * Rational(x.material_density_kg_m3)
        * Rational(x.arc_on_feed_speed_m_s)
    )
    deposited = feed * Rational(x.captured_feed_mass_fraction)
    exact = {
        "arc_on_feed_mass_rate_kg_s": feed,
        "arc_on_deposited_feed_mass_rate_kg_s": deposited,
        "clock_average_deposited_feed_mass_rate_kg_s": deposited * Rational(x.arc_on_time_fraction),
    }
    try:
        values = {name: float(value) for name, value in exact.items()}
        if any(value and values[name] == 0 for name, value in exact.items()):
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("A declared feed/deposition mass rate exceeds numeric support.",),
        )
    return Calculation(
        values=base | values,
        notes=(
            "Continuous uniform material-section feed balance with caller density, captured-feed fraction and active-time fraction; no process-specific efficiency or typical rate is embedded.",
            "Deposited feed mass excludes melted base/previous-layer material. No weld-pool mass, penetration, dilution, transfer mode, bead shape, quality, productivity cost or acceptance is inferred.",
        ),
    )


class DeclaredEquipmentEffectiveness(CorrelationRequest):
    asset_id: str = Field(min_length=1)
    observation_window_id: str = Field(min_length=1)
    production_quantity_unit: str = Field(min_length=1)
    planned_operating_time_s: Positive
    actual_running_time_s: Nonnegative
    reference_production_rate_per_s: Positive
    actual_running_production_rate_per_s: Nonnegative
    total_output_quantity: Nonnegative
    conforming_output_quantity: Nonnegative
    window_rate_and_quality_definitions_reviewed: bool

    @model_validator(mode="after")
    def compatible_observations(self):
        if self.actual_running_time_s > self.planned_operating_time_s:
            raise ValueError("running time cannot exceed the declared planned operating window")
        if self.conforming_output_quantity > self.total_output_quantity:
            raise ValueError("conforming output cannot exceed total output")
        return self


def declared_equipment_effectiveness(x: DeclaredEquipmentEffectiveness) -> Calculation:
    base = {
        "asset_id": x.asset_id,
        "observation_window_id": x.observation_window_id,
        "production_quantity_unit": x.production_quantity_unit,
    }
    if not x.window_rate_and_quality_definitions_reviewed or x.total_output_quantity == 0:
        return Calculation(
            status="needs_data",
            values=base,
            notes=(
                "Common observation/rate/quality definitions and nonzero output are needed; undefined quality is not imputed.",
            ),
        )
    exact_a = Rational(x.actual_running_time_s) / Rational(x.planned_operating_time_s)
    exact_p = Rational(x.actual_running_production_rate_per_s) / Rational(x.reference_production_rate_per_s)
    exact_q = Rational(x.conforming_output_quantity) / Rational(x.total_output_quantity)
    exact_values = {
        "availability_fraction": exact_a,
        "performance_ratio": exact_p,
        "quality_fraction": exact_q,
        "equipment_effectiveness": exact_a * exact_p * exact_q,
    }
    try:
        values = {key: float(value) for key, value in exact_values.items()}
        if any(value and values[key] == 0 for key, value in exact_values.items()):
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("An effectiveness factor or product exceeds numeric support.",),
        )
    return Calculation(
        values=base | values | {"performance_above_declared_reference": exact_p > 1},
        notes=(
            "Observed availability, speed performance and conforming-output fractions share caller-reviewed definitions. Performance above reference is retained, not clipped.",
            "This production descriptor is not reliability, failure probability, remaining life, safety performance, regulatory compliance or a maintenance recommendation.",
        ),
    )


class DeclaredParetoCategory(Contract):
    category_id: str = Field(min_length=1)
    occurrence_count: int = Field(ge=0)
    cost_per_occurrence: Nonnegative | None = None
    record_id: str = Field(min_length=1)


class DeclaredParetoSummary(CorrelationRequest):
    observation_window_id: str = Field(min_length=1)
    mode: Literal["occurrence_count", "occurrence_cost"]
    cost_unit: str | None = Field(default=None, min_length=1)
    common_window_categories_and_cost_basis_reviewed: bool
    categories: tuple[DeclaredParetoCategory, ...] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def compatible_categories(self):
        if len({r.category_id for r in self.categories}) != len(self.categories):
            raise ValueError("Pareto category identities must be unique")
        if self.mode == "occurrence_cost" and (
            self.cost_unit is None or any(r.cost_per_occurrence is None for r in self.categories)
        ):
            raise ValueError("cost Pareto requires a common unit and cost for every category")
        return self


def declared_pareto_summary(x: DeclaredParetoSummary) -> Calculation:
    base = {
        "observation_window_id": x.observation_window_id,
        "mode": x.mode,
        "measure_unit": "count" if x.mode == "occurrence_count" else x.cost_unit,
    }
    if not x.common_window_categories_and_cost_basis_reviewed:
        return Calculation(
            status="needs_data", values=base, notes=("Category/window/cost definitions require review.",)
        )
    weighted = [
        (
            i,
            r,
            Rational(r.occurrence_count)
            * (Rational(1) if x.mode == "occurrence_count" else Rational(r.cost_per_occurrence)),
        )
        for i, r in enumerate(x.categories)
    ]
    weighted.sort(key=lambda row: (-row[2], row[0]))
    total = sum((row[2] for row in weighted), Rational(0))
    try:
        total_value = float(total)
        running = Rational(0)
        rows = []
        for _, row, value in weighted:
            running += value
            share = None if not total else float(value / total)
            if value and (float(value) == 0 or share == 0):
                raise OverflowError
            rows.append(
                {
                    "category_id": row.category_id,
                    "record_id": row.record_id,
                    "occurrence_count": row.occurrence_count,
                    "measure": float(value),
                    "fraction_of_total": share,
                    "cumulative_fraction": None if not total else float(running / total),
                }
            )
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("A Pareto measure, total or nonzero share exceeds numeric support.",),
        )
    return Calculation(
        values=base | {"total_measure": total_value, "ranked_categories": rows},
        notes=(
            "Descending caller category measures; ties retain input order and zero totals have undefined shares. No category merging, missing-cost inference or currency conversion is performed.",
            "Ranking is descriptive; no fixed cumulative cutoff, causal conclusion, failure probability, risk category or maintenance decision is inferred.",
        ),
    )


class WellMixedPurgeStage(Contract):
    stage_id: str = Field(min_length=1)
    duration_s: Positive
    inlet_actual_volume_flow_m3_s: Nonnegative
    inlet_component_mole_fraction: Fraction


class WellMixedGasPurge(CorrelationRequest):
    compartment_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    gas_state_basis_id: str = Field(min_length=1)
    compartment_volume_m3: Positive
    initial_component_mole_fraction: Fraction
    flow_volume_basis: Literal["compartment_actual_volume"]
    constant_volume_pressure_temperature_and_perfect_mixing_reviewed: bool
    equal_inlet_outlet_no_reaction_leak_or_adsorption_reviewed: bool
    stages: tuple[WellMixedPurgeStage, ...] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def unique_stages(self):
        if len({r.stage_id for r in self.stages}) != len(self.stages):
            raise ValueError("purge stage identities must be unique")
        return self


def well_mixed_gas_purge(x: WellMixedGasPurge) -> Calculation:
    base = {
        "compartment_id": x.compartment_id,
        "component_id": x.component_id,
        "clock_id": x.clock_id,
        "gas_state_basis_id": x.gas_state_basis_id,
        "flow_volume_basis": x.flow_volume_basis,
    }
    if not (
        x.constant_volume_pressure_temperature_and_perfect_mixing_reviewed
        and x.equal_inlet_outlet_no_reaction_leak_or_adsorption_reviewed
    ):
        return Calculation(
            status="needs_data",
            values=base,
            notes=("The constant-state well-mixed flow balance requires explicit review.",),
        )
    concentration = x.initial_component_mole_fraction
    elapsed = Rational(0)
    history = []
    try:
        for stage in x.stages:
            elapsed += Rational(stage.duration_s)
            exact_exchanges = (
                Rational(stage.inlet_actual_volume_flow_m3_s)
                * Rational(stage.duration_s)
                / Rational(x.compartment_volume_m3)
            )
            exchanges = float(exact_exchanges)
            if exact_exchanges and exchanges == 0:
                raise OverflowError
            retained = math.exp(-exchanges)
            replaced = -math.expm1(-exchanges)
            inlet = stage.inlet_component_mole_fraction
            # Select a nonnegative increment from the smaller endpoint to retain bounds.
            if inlet >= concentration:
                final = float(
                    Rational(concentration) + (Rational(inlet) - Rational(concentration)) * Rational(replaced)
                )
            else:
                final = float(
                    Rational(inlet) + (Rational(concentration) - Rational(inlet)) * Rational(retained)
                )
            if final == 0 and (concentration > 0 or inlet > 0 and exact_exchanges > 0):
                raise OverflowError
            history.append(
                {
                    "stage_id": stage.stage_id,
                    "end_time_s": float(elapsed),
                    "volume_exchanges": exchanges,
                    "initial_component_mole_fraction": concentration,
                    "inlet_component_mole_fraction": inlet,
                    "final_component_mole_fraction": final,
                }
            )
            concentration = final
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=(
                "Purge time, turnover or nonzero concentration exceeds numeric support; no partial history is returned.",
            ),
        )
    return Calculation(
        values=base | {"history": history, "final_component_mole_fraction": concentration},
        notes=(
            "Exact constant-flow stage solution of the ideal uniform component balance at constant volume, pressure and temperature; actual volumetric flow is specified at the compartment state.",
            "No dead-zone, plug-flow, leaks, reactions, adsorption, oxygen/color relation, fixed purge count, target attainment or welding approval is inferred.",
        ),
    )


class ChemicalToleranceBranch(Contract):
    branch_id: str = Field(min_length=1)
    original_limit_lower: Fraction
    original_limit_upper: Fraction
    lower_inclusive: bool
    upper_inclusive: bool
    multiplier: float
    offset_mass_fraction: float

    @model_validator(mode="after")
    def interval(self):
        if self.original_limit_lower > self.original_limit_upper:
            raise ValueError("tolerance branch bounds must be ordered")
        if self.original_limit_lower == self.original_limit_upper and not (
            self.lower_inclusive and self.upper_inclusive
        ):
            raise ValueError("a singleton tolerance branch must include its boundary")
        return self


class DeclaredAnalysisToleranceRecipe(CorrelationRequest):
    element_id: str = Field(min_length=1)
    product_specification_id: str = Field(min_length=1)
    analysis_kind: Literal["product_analysis"]
    boundary_role: Literal["minimum", "maximum"]
    original_specified_limit_mass_fraction: Fraction
    service_tolerance_application_authorized: bool
    branches: tuple[ChemicalToleranceBranch, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_branches(self):
        if len({r.branch_id for r in self.branches}) != len(self.branches):
            raise ValueError("tolerance branch identities must be unique")
        return self


def declared_analysis_tolerance_recipe(x: DeclaredAnalysisToleranceRecipe) -> Calculation:
    base = {
        "element_id": x.element_id,
        "product_specification_id": x.product_specification_id,
        "analysis_kind": x.analysis_kind,
        "boundary_role": x.boundary_role,
        "original_specified_limit_mass_fraction": x.original_specified_limit_mass_fraction,
    }
    if not x.service_tolerance_application_authorized:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Service-specific product tolerance authority is missing.",),
        )
    value = x.original_specified_limit_mass_fraction
    matches = [
        r
        for r in x.branches
        if (value > r.original_limit_lower or value == r.original_limit_lower and r.lower_inclusive)
        and (value < r.original_limit_upper or value == r.original_limit_upper and r.upper_inclusive)
    ]
    if len(matches) != 1:
        return Calculation(
            status="out_of_scope",
            values=base | {"matching_branch_ids": [r.branch_id for r in matches]},
            notes=(
                "The original specified boundary must match exactly one caller branch; no gap filling or priority is inferred.",
            ),
        )
    branch = matches[0]
    exact = Rational(branch.multiplier) * Rational(value) + Rational(branch.offset_mass_fraction)
    if not 0 <= exact <= 1:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Declared tolerance is outside the mass-fraction range.",),
        )
    tolerance = float(exact)
    if exact and tolerance == 0:
        return Calculation(
            status="out_of_scope", values=base, notes=("Nonzero declared tolerance underflows.",)
        )
    return Calculation(
        values=base
        | {"selected_branch_id": branch.branch_id, "permitted_variation_mass_fraction": tolerance},
        notes=(
            "Branch selection uses the original specified minimum or maximum, never a measured product value. Caller coefficients and endpoint inclusion are explicit.",
            "No standard table, service exemption, rounding or material acceptance is inferred; pass the result to the corresponding lower/upper comparison tolerance explicitly.",
        ),
    )


class ChemicalAnalysisLimit(Contract):
    element_id: str = Field(min_length=1)
    minimum_mass_fraction: Fraction | None = None
    maximum_mass_fraction: Fraction | None = None
    permitted_under_minimum: Fraction = 0
    permitted_over_maximum: Fraction = 0
    tolerance_basis_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_interval(self):
        low, high = self.minimum_mass_fraction, self.maximum_mass_fraction
        if low is None and high is None:
            raise ValueError("an element requires at least one declared composition limit")
        if low is None and self.permitted_under_minimum or high is None and self.permitted_over_maximum:
            raise ValueError("a tolerance requires its corresponding original limit")
        if low is not None and high is not None and low > high:
            raise ValueError("composition limits must be ordered")
        if low is not None and Rational(low) < Rational(self.permitted_under_minimum):
            raise ValueError("expanded lower composition limit cannot be negative")
        if high is not None and Rational(high) + Rational(self.permitted_over_maximum) > 1:
            raise ValueError("expanded upper composition limit cannot exceed unity")
        return self


class ChemicalAnalysisObservation(Contract):
    measurement_id: str = Field(min_length=1)
    element_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    measured_mass_fraction: Fraction | None = None
    expanded_uncertainty_mass_fraction: Fraction | None = None

    @model_validator(mode="after")
    def paired_measurement(self):
        if (self.measured_mass_fraction is None) != (self.expanded_uncertainty_mass_fraction is None):
            raise ValueError("reported composition and uncertainty must both be present or both missing")
        return self


class ChemicalAnalysisSumRule(Contract):
    rule_id: str = Field(min_length=1)
    measurement_ids: tuple[str, ...] = Field(min_length=2)
    minimum_mass_fraction: Fraction | None = None
    maximum_mass_fraction: Fraction | None = None
    requirement_basis_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_sum_bounds(self):
        if len(set(self.measurement_ids)) != len(self.measurement_ids):
            raise ValueError("sum rule measurement identities must be unique")
        if self.minimum_mass_fraction is None and self.maximum_mass_fraction is None:
            raise ValueError("sum rule requires a declared bound")
        if (
            self.minimum_mass_fraction is not None
            and self.maximum_mass_fraction is not None
            and self.minimum_mass_fraction > self.maximum_mass_fraction
        ):
            raise ValueError("sum rule bounds must be ordered")
        return self


class ChemicalAnalysisLinearRule(Contract):
    rule_id: str = Field(min_length=1)
    measurement_coefficients: dict[str, float] = Field(min_length=1, max_length=100)
    constant_offset: float = 0.0
    minimum_value: float | None = None
    maximum_value: float | None = None
    requirement_basis_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def explicit_expression(self):
        if any(not key.strip() or value == 0 for key, value in self.measurement_coefficients.items()):
            raise ValueError("linear rule requires explicit measurement identities and nonzero coefficients")
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("linear rule requires a declared bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.minimum_value > self.maximum_value
        ):
            raise ValueError("linear rule bounds must be ordered")
        return self


class DeclaredChemicalAnalysisComparison(CorrelationRequest):
    physical_product_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    governing_requirement_id: str = Field(min_length=1)
    analysis_kind: Literal["heat_analysis", "product_analysis"]
    sampling_and_analysis_kind_reviewed: bool
    product_tolerance_application_authorized: bool
    limits: tuple[ChemicalAnalysisLimit, ...] = Field(min_length=1)
    observations: tuple[ChemicalAnalysisObservation, ...] = Field(min_length=1)
    sum_rules: tuple[ChemicalAnalysisSumRule, ...] = ()
    linear_rules: tuple[ChemicalAnalysisLinearRule, ...] = ()

    @model_validator(mode="after")
    def exact_element_roles(self):
        if len({r.element_id for r in self.limits}) != len(self.limits):
            raise ValueError("element limits must be unique")
        if len({r.measurement_id for r in self.observations}) != len(self.observations):
            raise ValueError("measurement identities must be unique")
        if not {r.element_id for r in self.observations} <= {r.element_id for r in self.limits}:
            raise ValueError("every observed element requires an explicit limit")
        if any(r.permitted_under_minimum or r.permitted_over_maximum for r in self.limits):
            if self.analysis_kind != "product_analysis" or not self.product_tolerance_application_authorized:
                raise ValueError("composition tolerance requires authorized product analysis")
        if len({r.rule_id for r in self.sum_rules}) != len(self.sum_rules):
            raise ValueError("sum rule identities must be unique")
        observations = {r.measurement_id: r for r in self.observations}
        rule_ids = [r.rule_id for r in (*self.sum_rules, *self.linear_rules)]
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("sum and linear rule identities must be unique together")
        for rule in self.linear_rules:
            if not set(rule.measurement_coefficients) <= set(observations):
                raise ValueError("linear rule must reference explicit observation identities")
            members = [observations[name] for name in rule.measurement_coefficients]
            if len({r.sample_id for r in members}) != 1 or len({r.element_id for r in members}) != len(
                members
            ):
                raise ValueError("linear rule requires one sample and distinct measured elements")
        for rule in self.sum_rules:
            if not set(rule.measurement_ids) <= set(observations):
                raise ValueError("sum rule must reference explicit observation identities")
            members = [observations[name] for name in rule.measurement_ids]
            if len({r.sample_id for r in members}) != 1:
                raise ValueError("sum rule measurements must belong to the same sample")
            if len({r.element_id for r in members}) != len(members):
                raise ValueError("sum rule cannot count repeated measurements of one element")
        return self


def declared_chemical_analysis_comparison(x: DeclaredChemicalAnalysisComparison) -> Calculation:
    base = {
        "physical_product_id": x.physical_product_id,
        "heat_id": x.heat_id,
        "material_condition_id": x.material_condition_id,
        "analysis_kind": x.analysis_kind,
        "governing_requirement_id": x.governing_requirement_id,
    }
    if not x.sampling_and_analysis_kind_reviewed:
        return Calculation(
            status="needs_data",
            values=base,
            notes=("Sampling role and analysis kind require explicit review.",),
        )
    by_element = {r.element_id: r for r in x.limits}
    rows = []
    for observation in x.observations:
        limit = by_element[observation.element_id]
        low = (
            None
            if limit.minimum_mass_fraction is None
            else Rational(limit.minimum_mass_fraction) - Rational(limit.permitted_under_minimum)
        )
        high = (
            None
            if limit.maximum_mass_fraction is None
            else Rational(limit.maximum_mass_fraction) + Rational(limit.permitted_over_maximum)
        )
        state = "unknown"
        if observation.measured_mass_fraction is not None:
            value = Rational(observation.measured_mass_fraction)
            uncertainty = Rational(observation.expanded_uncertainty_mass_fraction)
            a, b = value - uncertainty, value + uncertainty
            if (low is None or a >= low) and (high is None or b <= high):
                state = "within_declared_interval"
            elif (low is not None and b < low) or (high is not None and a > high):
                state = "outside_declared_interval"
            else:
                state = "uncertainty_overlap"
        rows.append(
            observation.model_dump(mode="json")
            | {
                "effective_minimum_mass_fraction": None if low is None else float(low),
                "effective_maximum_mass_fraction": None if high is None else float(high),
                "tolerance_basis_id": limit.tolerance_basis_id,
                "comparison_state": state,
            }
        )
    missing = sorted(set(by_element) - {r.element_id for r in x.observations})
    sums = []
    observations = {r.measurement_id: r for r in x.observations}
    for rule in x.sum_rules:
        members = [observations[name] for name in rule.measurement_ids]
        state, total, uncertainty = "unknown", None, None
        if all(r.measured_mass_fraction is not None for r in members):
            total = sum((Rational(r.measured_mass_fraction) for r in members), Rational(0))
            uncertainty = sum((Rational(r.expanded_uncertainty_mass_fraction) for r in members), Rational(0))
            a, b = total - uncertainty, total + uncertainty
            low, high = rule.minimum_mass_fraction, rule.maximum_mass_fraction
            if (low is None or a >= Rational(low)) and (high is None or b <= Rational(high)):
                state = "within_declared_interval"
            elif (low is not None and b < Rational(low)) or (high is not None and a > Rational(high)):
                state = "outside_declared_interval"
            else:
                state = "uncertainty_overlap"
        sums.append(
            rule.model_dump(mode="json")
            | {
                "sample_id": members[0].sample_id,
                "summed_mass_fraction": None if total is None else float(total),
                "summed_expanded_uncertainty_bound": None if uncertainty is None else float(uncertainty),
                "comparison_state": state,
            }
        )
    linear = []
    for rule in x.linear_rules:
        members = {key: observations[key] for key in rule.measurement_coefficients}
        center, spread, state = None, None, "unknown"
        if all(row.measured_mass_fraction is not None for row in members.values()):
            exact = Rational(rule.constant_offset) + sum(
                (
                    Rational(weight) * Rational(members[key].measured_mass_fraction)
                    for key, weight in rule.measurement_coefficients.items()
                ),
                Rational(0),
            )
            uncertainty = sum(
                (
                    abs(Rational(weight)) * Rational(members[key].expanded_uncertainty_mass_fraction)
                    for key, weight in rule.measurement_coefficients.items()
                ),
                Rational(0),
            )
            low, high = exact - uncertainty, exact + uncertainty
            lower, upper = rule.minimum_value, rule.maximum_value
            if (lower is None or low >= Rational(lower)) and (upper is None or high <= Rational(upper)):
                state = "within_declared_interval"
            elif (lower is not None and high < Rational(lower)) or (
                upper is not None and low > Rational(upper)
            ):
                state = "outside_declared_interval"
            else:
                state = "uncertainty_overlap"
            try:
                center, spread = float(exact), float(uncertainty)
                if (
                    not math.isfinite(center)
                    or not math.isfinite(spread)
                    or (exact and center == 0)
                    or (uncertainty and spread == 0)
                ):
                    raise ArithmeticError
            except ArithmeticError:
                return Calculation(
                    status="out_of_scope",
                    values=base
                    | {
                        "reason": "linear analysis rule exceeds finite arithmetic support",
                        "rule_id": rule.rule_id,
                    },
                )
        linear.append(
            rule.model_dump(mode="json")
            | {
                "sample_id": next(iter(members.values())).sample_id,
                "linear_expression_value": center,
                "expanded_interval_bound": spread,
                "comparison_state": state,
            }
        )
    return Calculation(
        status="needs_data"
        if missing or any(r["comparison_state"] == "unknown" for r in (*rows, *linear))
        else "computed",
        values=base
        | {
            "comparisons": rows,
            "sum_comparisons": sums,
            "linear_comparisons": linear,
            "missing_element_ids": missing,
        },
        notes=(
            "Caller-declared mass-fraction bounds and authorized product tolerances only; no standard table, rounding, alloy identity or acceptance is inferred.",
            "Heat and product analysis remain distinct; same-sample sum rules use explicit measurement identities and arithmetic sums of uncertainty bounds, without independence, statistical coverage, PMI equivalence, imputation or composition closure claims.",
            "Signed linear rules use caller coefficients on mass-fraction measurements and conservative absolute-coefficient interval bounds; they are not physical phase fractions or joint statistical coverage.",
        ),
    )


class ResinHdtHeadroom(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    hdt_record_id: str = Field(min_length=1)
    test_method_id: str = Field(min_length=1)
    test_flexural_stress_Pa: Positive
    heat_deflection_temperature_K: Positive
    design_temperature_K: Positive
    required_headroom_K: Nonnegative


def resin_hdt_headroom(x: ResinHdtHeadroom) -> Calculation:
    headroom = Rational(x.heat_deflection_temperature_K) - Rational(x.design_temperature_K)
    surplus = headroom - Rational(x.required_headroom_K)
    try:
        surplus_value = float(surplus)
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values={"material_condition_id": x.material_condition_id},
            notes=("The signed headroom surplus exceeds numeric support.",),
        )
    return Calculation(
        values={
            "material_condition_id": x.material_condition_id,
            "hdt_record_id": x.hdt_record_id,
            "test_method_id": x.test_method_id,
            "test_flexural_stress_Pa": x.test_flexural_stress_Pa,
            "record_sha256": x.basis.record_sha256,
            "hdt_headroom_K": float(headroom),
            "headroom_surplus_K": surplus_value,
            "declared_headroom_satisfied": surplus >= 0,
        },
        notes=(
            "Subtract supplied design temperature from a load- and method-identified HDT record, then compare with caller required temperature difference.",
            "The computed headroom criterion is not continuous-use temperature, creep resistance, chemical compatibility, laminate/bond qualification or code acceptance. No default test load or required margin is supplied.",
        ),
    )


class DeclaredLogSlopeRuptureFactor(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    slope_definition_id: str = Field(min_length=1)
    negative_log_time_per_log_stress_slope: float = Field(lt=0)
    logarithm_base: float = Field(gt=1)
    upper_factor_cap: Positive


def declared_log_slope_rupture_factor(x: DeclaredLogSlopeRuptureFactor) -> Calculation:
    raw = math.pow(x.logarithm_base, 1.0 / x.negative_log_time_per_log_stress_slope)
    if not math.isfinite(raw) or raw <= 0.0:
        return Calculation(
            status="out_of_scope",
            values={"material_condition_id": x.material_condition_id},
            notes=(
                "The positive uncapped factor is outside numeric support; it is not replaced by zero or by the cap.",
            ),
        )
    factor = min(raw, x.upper_factor_cap)
    controlling = (
        ["log_slope"]
        if raw < x.upper_factor_cap
        else ["upper_cap"]
        if x.upper_factor_cap < raw
        else ["log_slope", "upper_cap"]
    )
    return Calculation(
        values={
            "material_condition_id": x.material_condition_id,
            "slope_definition_id": x.slope_definition_id,
            "record_sha256": x.basis.record_sha256,
            "uncapped_factor": raw,
            "capped_factor": factor,
            "controlling_terms": controlling,
        },
        notes=(
            "Compute base**(1/slope) for the declared negative log-time/log-stress slope, then apply the caller upper cap; controlling ties refer to returned numeric values.",
            "No material slope, standard cap, creep life, allowable stress or qualification is inferred.",
        ),
    )


class TemperatureTrendStrengthScaling(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    property_definition_id: str = Field(min_length=1)
    trend_basis_id: str = Field(min_length=1)
    reference_temperature_K: Positive
    evaluation_temperature_K: Positive
    reference_strength_Pa: Positive
    trend_strength_at_reference_Pa: Positive
    trend_strength_at_evaluation_Pa: Positive

    @model_validator(mode="after")
    def coincident_temperature_trend(self):
        if (
            self.reference_temperature_K == self.evaluation_temperature_K
            and self.trend_strength_at_reference_Pa != self.trend_strength_at_evaluation_Pa
        ):
            raise ValueError("one declared trend must have one value at a coincident temperature")
        return self


def temperature_trend_strength_scaling(x: TemperatureTrendStrengthScaling) -> Calculation:
    ratio = Rational(x.trend_strength_at_evaluation_Pa) / Rational(x.trend_strength_at_reference_Pa)
    exact = Rational(x.reference_strength_Pa) * ratio
    result = _positive_optional_float(exact)
    if result is None:
        return Calculation(
            status="out_of_scope",
            values={"material_condition_id": x.material_condition_id},
            notes=("The positive scaled strength exceeds numeric support.",),
        )
    ratio_value = _positive_optional_float(ratio)
    return Calculation(
        values={
            "material_condition_id": x.material_condition_id,
            "property_definition_id": x.property_definition_id,
            "trend_basis_id": x.trend_basis_id,
            "reference_temperature_K": x.reference_temperature_K,
            "evaluation_temperature_K": x.evaluation_temperature_K,
            "record_sha256": x.basis.record_sha256,
            "trend_ratio": ratio_value,
            "trend_ratio_representable": ratio_value is not None,
            "scaled_reference_strength_Pa": result,
        },
        notes=(
            "Scale the supplied reference strength by the supplied evaluation/reference trend ratio, forming the complete ratio before float conversion.",
            "No trend generation, interpolation/extrapolation, guaranteed minimum property, material selection or allowable-stress qualification is inferred.",
        ),
    )


class PlanarStressLinearization(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    stress_component_definition_id: str = Field(min_length=1)
    position_m: tuple[float, ...] = Field(min_length=2, max_length=4096)
    signed_stress_Pa: tuple[float, ...] = Field(min_length=2, max_length=4096)
    section_model: Literal["constant_width_planar_piecewise_linear_component"]

    @model_validator(mode="after")
    def aligned_profile(self):
        if len(self.position_m) != len(self.signed_stress_Pa):
            raise ValueError("stress samples and positions must align")
        if any(b <= a for a, b in zip(self.position_m, self.position_m[1:], strict=False)):
            raise ValueError("through-thickness positions must strictly increase")
        return self


def planar_stress_linearization(x: PlanarStressLinearization) -> Calculation:
    positions = [Rational(value) for value in x.position_m]
    stresses = [Rational(value) for value in x.signed_stress_Pa]
    thickness = positions[-1] - positions[0]
    s = [(value - positions[0]) / thickness for value in positions]
    mean, first_moment = Rational(0), Rational(0)
    for i in range(len(s) - 1):
        h = s[i + 1] - s[i]
        u0, u1 = s[i] - Rational(1, 2), s[i + 1] - Rational(1, 2)
        a, b = stresses[i], stresses[i + 1]
        mean += h * (a + b) / 2
        first_moment += h * ((2 * u0 + u1) * a + (u0 + 2 * u1) * b) / 6
    bending = [12 * first_moment * (value - Rational(1, 2)) for value in s]
    residual = [value - mean - b for value, b in zip(stresses, bending, strict=True)]
    exact_scalars = {
        "thickness_m": thickness,
        "membrane_stress_Pa": mean,
        "bending_stress_at_start_Pa": bending[0],
        "bending_stress_at_end_Pa": bending[-1],
        "membrane_force_per_unit_width_N_m": mean * thickness,
        "bending_moment_per_unit_width_N": first_moment * thickness**2,
        "maximum_absolute_residual_stress_Pa": max(abs(value) for value in residual),
    }
    try:
        scalars = {key: float(value) for key, value in exact_scalars.items()}
        profile = [
            dict(
                position_m=p,
                bending_stress_Pa=float(b),
                membrane_plus_bending_stress_Pa=float(mean + b),
                residual_stress_Pa=float(r),
            )
            for p, b, r in zip(x.position_m, bending, residual, strict=True)
        ]
        if any(value != 0 and scalars[key] == 0.0 for key, value in exact_scalars.items()):
            raise ArithmeticError("nonzero resultant underflow")
        if any(
            (b != 0 and row["bending_stress_Pa"] == 0.0)
            or (mean + b != 0 and row["membrane_plus_bending_stress_Pa"] == 0.0)
            or (r != 0 and row["residual_stress_Pa"] == 0.0)
            for b, r, row in zip(bending, residual, profile, strict=True)
        ):
            raise ArithmeticError("nonzero profile underflow")
    except (OverflowError, ArithmeticError):
        return Calculation(
            status="out_of_scope",
            values={"physical_scope_id": x.physical_scope_id},
            notes=("The component decomposition or section resultant exceeds numeric support.",),
        )
    return Calculation(
        values=scalars
        | {
            "physical_scope_id": x.physical_scope_id,
            "load_case_id": x.load_case_id,
            "coordinate_frame_id": x.coordinate_frame_id,
            "stress_component_definition_id": x.stress_component_definition_id,
            "record_sha256": x.basis.record_sha256,
            "profile": profile,
        },
        notes=(
            "Exact piecewise-linear component integrals over a constant-width planar thickness preserve membrane force and centroidal bending moment.",
            "Residual extrema apply to the declared piecewise-linear samples. No path selection, frame rotation, curvature correction, equivalent-stress linearization, primary/secondary classification, fatigue life or code acceptance is inferred.",
        ),
    )


class MeanShearStress(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    force_direction_id: str = Field(min_length=1)
    signed_shear_force_N: float
    effective_shear_area_m2: Positive


def mean_shear_stress(x: MeanShearStress) -> Calculation:
    exact = Rational(x.signed_shear_force_N) / Rational(x.effective_shear_area_m2)
    try:
        stress = float(exact)
    except OverflowError:
        stress = math.inf
    if not math.isfinite(stress) or (exact != 0 and stress == 0.0):
        return Calculation(
            status="out_of_scope", values={}, notes=("Mean shear stress exceeds numeric support.",)
        )
    return Calculation(
        values={
            "physical_scope_id": x.physical_scope_id,
            "force_direction_id": x.force_direction_id,
            "record_sha256": x.basis.record_sha256,
            "signed_mean_shear_stress_Pa": stress,
        },
        notes=(
            "Signed resultant force divided by caller effective shear area; no weld throat selection, local shear field or allowable stress is inferred.",
        ),
    )


class DeclaredShellCharacteristicLengths(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    radius_definition_id: str = Field(min_length=1)
    radius_m: Positive
    wall_thickness_m: Positive
    declared_length_multipliers: dict[str, Nonnegative] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def named_multipliers(self):
        if any(not key.strip() for key in self.declared_length_multipliers):
            raise ValueError("characteristic-length multiplier names must be nonempty")
        return self


def declared_shell_characteristic_lengths(x: DeclaredShellCharacteristicLengths) -> Calculation:
    characteristic = math.sqrt(x.radius_m) * math.sqrt(x.wall_thickness_m)
    lengths = {key: factor * characteristic for key, factor in x.declared_length_multipliers.items()}
    if (
        not math.isfinite(characteristic)
        or characteristic <= 0.0
        or any(
            not math.isfinite(value) or (x.declared_length_multipliers[key] > 0 and value == 0.0)
            for key, value in lengths.items()
        )
    ):
        return Calculation(
            status="out_of_scope", values={}, notes=("Shell length descriptor exceeds numeric support.",)
        )
    return Calculation(
        values={
            "physical_scope_id": x.physical_scope_id,
            "radius_definition_id": x.radius_definition_id,
            "record_sha256": x.basis.record_sha256,
            "sqrt_radius_thickness_m": characteristic,
            "declared_lengths_m": lengths,
        },
        notes=(
            "Caller length multipliers applied to sqrt(radius*thickness); no standard default, region extent/separation decision or shell discontinuity stress solution is inferred.",
        ),
    )


class NoSlipPhaseFlow(Contract):
    phase_id: str = Field(min_length=1)
    mass_flow_kg_s: Nonnegative
    density_kg_m3: Positive


class HomogeneousNoSlipMixtureDensity(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    phases: tuple[NoSlipPhaseFlow, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def unique_and_flowing(self):
        if len({row.phase_id for row in self.phases}) != len(self.phases):
            raise ValueError("phase flow IDs must be unique")
        if not any(row.mass_flow_kg_s > 0.0 for row in self.phases):
            raise ValueError("mixture density requires positive total mass flow")
        return self


def _positive_optional_float(value: Rational) -> float | None:
    try:
        result = float(value)
    except OverflowError:
        return None
    return None if value != 0 and result == 0.0 else result


def homogeneous_no_slip_mixture_density(x: HomogeneousNoSlipMixtureDensity) -> Calculation:
    mass = sum((Rational(row.mass_flow_kg_s) for row in x.phases), Rational(0))
    volumes = [Rational(row.mass_flow_kg_s) / Rational(row.density_kg_m3) for row in x.phases]
    volume = sum(volumes, Rational(0))
    density = _positive_optional_float(mass / volume)
    if density is None:
        return Calculation(
            status="out_of_scope", values={}, notes=("Mixture density exceeds numeric support.",)
        )
    return Calculation(
        values={
            "physical_scope_id": x.physical_scope_id,
            "condition_id": x.condition_id,
            "record_sha256": x.basis.record_sha256,
            "mixture_density_kg_m3": density,
            "total_mass_flow_kg_s": _positive_optional_float(mass),
            "total_volume_flow_m3_s": _positive_optional_float(volume),
            "phase_volume_flows": [
                {"phase_id": row.phase_id, "volume_flow_m3_s": _positive_optional_float(v)}
                for row, v in zip(x.phases, volumes, strict=True)
            ],
        },
        notes=(
            "Sum mass flows and additive phase volume flows at one caller-reviewed condition; no phase equilibrium, slip or measured holdup is inferred.",
            "A null flow descriptor denotes numeric range loss, not zero or a missing input; the density ratio is formed before float conversion.",
        ),
    )


class DeclaredInverseSqrtDensityVelocity(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    coefficient_basis_id: str = Field(min_length=1)
    coefficient_SI: Nonnegative
    coefficient_unit: Literal["m/s*sqrt(kg/m^3)"]
    mixture_density_kg_m3: Positive


def declared_inverse_sqrt_density_velocity(x: DeclaredInverseSqrtDensityVelocity) -> Calculation:
    velocity = x.coefficient_SI / math.sqrt(x.mixture_density_kg_m3)
    if not math.isfinite(velocity) or (x.coefficient_SI > 0 and velocity == 0.0):
        return Calculation(
            status="out_of_scope", values={}, notes=("Velocity descriptor exceeds numeric support.",)
        )
    return Calculation(
        values={
            "physical_scope_id": x.physical_scope_id,
            "coefficient_basis_id": x.coefficient_basis_id,
            "record_sha256": x.basis.record_sha256,
            "velocity_descriptor_m_s": velocity,
        },
        notes=(
            "Caller SI coefficient divided by the square root of supplied density; no customary-unit coefficient conversion or standard default is inferred.",
            "This descriptor is not an allowable velocity, erosion/FAC loss rate, particle model, oxygen-service safety or acceptance decision.",
        ),
    )


class DevicePressureDropCavitationIndex(CorrelationRequest):
    device_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    inlet_pressure_location_id: str = Field(min_length=1)
    outlet_pressure_location_id: str = Field(min_length=1)
    vapor_pressure_basis_id: str = Field(min_length=1)
    inlet_absolute_pressure_Pa: Positive
    outlet_absolute_pressure_Pa: Positive
    vapor_pressure_Pa: Positive


def device_pressure_drop_cavitation_index(x: DevicePressureDropCavitationIndex) -> Calculation:
    drop = Rational(x.inlet_absolute_pressure_Pa) - Rational(x.outlet_absolute_pressure_Pa)
    margin = Rational(x.inlet_absolute_pressure_Pa) - Rational(x.vapor_pressure_Pa)
    base = {
        "device_id": x.device_id,
        "condition_id": x.condition_id,
        "inlet_pressure_location_id": x.inlet_pressure_location_id,
        "outlet_pressure_location_id": x.outlet_pressure_location_id,
        "vapor_pressure_basis_id": x.vapor_pressure_basis_id,
        "record_sha256": x.basis.record_sha256,
        "inlet_to_outlet_pressure_drop_Pa": float(drop),
        "inlet_vapor_pressure_margin_Pa": float(margin),
    }
    if drop <= 0:
        return Calculation(
            status="out_of_scope", values=base, notes=("A positive device pressure drop is required.",)
        )
    ratio = margin / drop
    try:
        index = float(ratio)
    except OverflowError:
        index = math.inf
    if not math.isfinite(index) or (ratio != 0 and index == 0.0):
        return Calculation(
            status="out_of_scope", values=base, notes=("The device index exceeds numeric support.",)
        )
    return Calculation(
        values=base | {"device_pressure_drop_cavitation_index": index},
        notes=(
            "Signed inlet-minus-vapor pressure divided by positive inlet-minus-outlet device pressure drop; all static pressures use an explicit absolute basis.",
            "This is distinct from a dynamic-pressure cavitation number. No onset threshold, pressure recovery, nuclei, collapse damage or acceptance is inferred.",
        ),
    )


class ZenerHollomonParameter(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    strain_rate_definition_id: str = Field(min_length=1)
    activation_energy_basis_id: str = Field(min_length=1)
    strain_rate_s_1: Positive
    temperature_K: Positive
    activation_energy_J_mol: Nonnegative
    gas_constant_J_mol_K: Positive


def zener_hollomon_parameter(x: ZenerHollomonParameter) -> Calculation:
    exact_activation = (
        Rational(x.activation_energy_J_mol) / Rational(x.gas_constant_J_mol_K) / Rational(x.temperature_K)
    )
    try:
        activation = float(exact_activation)
    except OverflowError:
        activation = math.inf
    if not math.isfinite(activation) or (exact_activation != 0 and activation == 0.0):
        return Calculation(
            status="out_of_scope",
            values={"material_condition_id": x.material_condition_id},
            notes=("The temperature-compensation exponent exceeds numeric support.",),
        )
    log_z = math.log(x.strain_rate_s_1) + activation
    if not math.isfinite(log_z):
        return Calculation(
            status="out_of_scope",
            values={"material_condition_id": x.material_condition_id},
            notes=("The logarithmic parameter exceeds numeric support.",),
        )
    try:
        z = x.strain_rate_s_1 if activation == 0.0 else math.exp(log_z)
    except OverflowError:
        z = None
    if z is not None and (not math.isfinite(z) or z <= 0.0):
        z = None
    return Calculation(
        values={
            "material_condition_id": x.material_condition_id,
            "strain_rate_definition_id": x.strain_rate_definition_id,
            "activation_energy_basis_id": x.activation_energy_basis_id,
            "record_sha256": x.basis.record_sha256,
            "temperature_compensation_exponent": activation,
            "ln_z_relative_to_1_s_1": log_z,
            "z_s_1": z,
            "z_representable": z is not None,
        },
        notes=(
            "Natural logarithm uses a reference rate of one reciprocal second; the positive supplied strain rate is temperature-compensated with caller Q and R.",
            "A computed descriptor is not a strain-rate prediction, flow-stress law, creep damage, rupture life or material qualification. An unavailable direct value does not invalidate a representable logarithmic descriptor.",
        ),
    )


class ThicknessScaledRateLimit(CorrelationRequest):
    component_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    rate_direction: Literal["heating", "cooling"]
    governing_thickness_m: Positive
    minimum_supported_thickness_m: Positive
    maximum_supported_thickness_m: Positive
    reference_thickness_m: Positive
    reference_rate_K_s: Nonnegative
    ceiling_rate_K_s: Nonnegative
    metal_temperature_K: Positive
    activation_temperature_K: Positive
    activation_comparison: Literal["greater_than", "greater_or_equal"]

    @model_validator(mode="after")
    def ordered_support(self):
        if self.minimum_supported_thickness_m > self.maximum_supported_thickness_m:
            raise ValueError("thickness support must be ordered")
        return self


def thickness_scaled_rate_limit(x: ThicknessScaledRateLimit) -> Calculation:
    base = dict(
        component_id=x.component_id,
        procedure_id=x.procedure_id,
        rate_direction=x.rate_direction,
        record_sha256=x.basis.record_sha256,
    )
    if not x.minimum_supported_thickness_m <= x.governing_thickness_m <= x.maximum_supported_thickness_m:
        return Calculation(status="out_of_scope", values=base)
    active = (
        x.metal_temperature_K > x.activation_temperature_K
        if x.activation_comparison == "greater_than"
        else x.metal_temperature_K >= x.activation_temperature_K
    )
    if not active:
        return Calculation(
            values=base | dict(rule_active=False, maximum_rate_K_s=None, controlling_terms=[]),
            notes=("Inactive declared rule provides no rate permission or alternative limit.",),
        )
    exact = (
        Rational(x.reference_rate_K_s) * Rational(x.reference_thickness_m) / Rational(x.governing_thickness_m)
    )
    cap = Rational(x.ceiling_rate_K_s)
    bounded = min(exact, cap)
    limit = float(bounded)
    if bounded > 0 and limit == 0.0:
        return Calculation(
            status="out_of_scope", values=base, notes=("Positive rate limit underflows representation.",)
        )
    terms = (
        ["thickness_scaled"]
        if exact < cap
        else ["ceiling"]
        if exact > cap
        else ["thickness_scaled", "ceiling"]
    )
    try:
        uncapped = float(exact)
        if exact > 0 and uncapped == 0.0:
            uncapped = None
    except OverflowError:
        uncapped = None
    return Calculation(
        values=base
        | dict(
            rule_active=True,
            maximum_rate_K_s=limit,
            uncapped_rate_K_s=uncapped,
            uncapped_rate_representable=uncapped is not None,
            controlling_terms=terms,
        ),
        notes=(
            "Caller thickness scaling and ceiling only; no standard coefficients or heat-treatment qualification.",
        ),
    )


class DeclaredHydrogenSusceptibilityIndex(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    composition_index_definition_id: str = Field(min_length=1)
    composition_index_mass_percent: Nonnegative
    hydrogen_definition_id: str = Field(min_length=1)
    hydrogen_input_kind: Literal["measured_quantity", "declared_category_value"]
    hydrogen_unit_token: str = Field(min_length=1)
    hydrogen_value: Positive
    hydrogen_reference_value: Positive
    composition_coefficient: float
    logarithmic_coefficient: float
    constant_offset: float

    @model_validator(mode="after")
    def category_units(self):
        if self.hydrogen_input_kind == "declared_category_value" and self.hydrogen_unit_token != "1":
            raise ValueError("category values require dimensionless units")
        return self


def declared_hydrogen_susceptibility_index(x: DeclaredHydrogenSusceptibilityIndex) -> Calculation:
    base = dict(
        material_condition_id=x.material_condition_id,
        hydrogen_definition_id=x.hydrogen_definition_id,
        hydrogen_input_kind=x.hydrogen_input_kind,
        hydrogen_unit_token=x.hydrogen_unit_token,
        record_sha256=x.basis.record_sha256,
    )
    ratio = x.hydrogen_value / x.hydrogen_reference_value
    logarithm = (
        math.log1p((x.hydrogen_value - x.hydrogen_reference_value) / x.hydrogen_reference_value)
        / math.log(10.0)
        if 0.5 <= ratio <= 2.0
        else math.log10(x.hydrogen_value) - math.log10(x.hydrogen_reference_value)
    )
    composition = x.composition_coefficient * x.composition_index_mass_percent
    hydrogen = x.logarithmic_coefficient * logarithm
    try:
        index = math.fsum((x.constant_offset, composition, hydrogen))
        if not all(math.isfinite(v) for v in (index, composition, hydrogen)):
            raise ArithmeticError
    except (ArithmeticError, ValueError):
        return Calculation(status="out_of_scope", values=base)
    return Calculation(
        values=base
        | dict(
            index_value=index,
            composition_contribution=composition,
            hydrogen_contribution=hydrogen,
            log10_hydrogen_ratio=logarithm,
        ),
        notes=(
            "Hydrogen value and reference have the same explicitly declared meaning and units; category is not measured gas content.",
            "Caller-parameterized descriptor only; no susceptibility group, crack probability, preheat requirement or approval.",
        ),
    )


class HotTapBranchTestPressureCap(CorrelationRequest):
    host_component_id: str = Field(min_length=1)
    branch_component_id: str = Field(min_length=1)
    host_external_capacity_record_id: str = Field(min_length=1)
    branch_test_limit_record_id: str = Field(min_length=1)
    host_operating_pressure_Pa_abs: Positive
    allowable_host_external_pressure_difference_Pa: Nonnegative
    branch_test_pressure_limit_Pa_abs: Positive
    proposed_test_pressure_Pa_abs: Positive


def hot_tap_branch_test_pressure_cap(x: HotTapBranchTestPressureCap) -> Calculation:
    host = x.host_operating_pressure_Pa_abs
    branch_limit = x.branch_test_pressure_limit_Pa_abs
    differential = x.allowable_host_external_pressure_difference_Pa
    # Compare before adding to keep a finite governing branch cap even when
    # the unused host-plus-differential candidate would overflow.
    if host > branch_limit:
        cap, governing = branch_limit, ["branch_limit"]
    else:
        available = branch_limit - host
        if differential < available:
            cap, governing = host + differential, ["host_external_differential"]
        elif differential == available:
            cap, governing = branch_limit, ["branch_limit", "host_external_differential"]
        else:
            cap, governing = branch_limit, ["branch_limit"]
    return Calculation(
        values=dict(
            host_component_id=x.host_component_id,
            branch_component_id=x.branch_component_id,
            host_external_capacity_record_id=x.host_external_capacity_record_id,
            branch_test_limit_record_id=x.branch_test_limit_record_id,
            maximum_test_pressure_Pa_abs=cap,
            governing_limits=governing,
            proposed_external_pressure_difference_Pa=x.proposed_test_pressure_Pa_abs - host,
            pressure_cap_margin_Pa=cap - x.proposed_test_pressure_Pa_abs,
            proposed_pressure_within_declared_upper_limits=x.proposed_test_pressure_Pa_abs <= cap,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Host operating pressure and branch test pressure share an absolute basis; external differential is test minus host pressure.",
            "Upper-bound arithmetic only; no minimum test pressure, buckling capacity, hot-wall strength, procedure eligibility or approval is generated.",
        ),
    )


class ProjectedIndicationInterval(Contract):
    indication_id: str = Field(min_length=1)
    start_m: Nonnegative
    end_m: Positive
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def positive_length(self):
        if self.end_m <= self.start_m:
            raise ValueError("indication interval must have positive length")
        return self


class IndicationWindowAccumulation(CorrelationRequest):
    physical_scope_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_origin_id: str = Field(min_length=1)
    examined_length_m: Positive
    window_length_m: Positive
    indications: tuple[ProjectedIndicationInterval, ...] = Field(max_length=512)
    overlap_semantics: Literal["sum_indication_overlap", "union_covered_length"]
    examined_extent_and_no_gaps_reviewed: bool
    indication_identity_and_projection_reviewed: bool
    overlap_semantics_reviewed: bool

    @model_validator(mode="after")
    def scope(self):
        if self.window_length_m > self.examined_length_m:
            raise ValueError("window length cannot exceed examined extent")
        ids = [r.indication_id for r in self.indications]
        if len(ids) != len(set(ids)):
            raise ValueError("indication identities must be unique")
        if any(r.end_m > self.examined_length_m for r in self.indications):
            raise ValueError("indication exceeds examined extent")
        return self


def indication_window_accumulation(x: IndicationWindowAccumulation) -> Calculation:
    base = dict(
        physical_scope_id=x.physical_scope_id,
        coordinate_frame_id=x.coordinate_frame_id,
        coordinate_origin_id=x.coordinate_origin_id,
        overlap_semantics=x.overlap_semantics,
        record_sha256=x.basis.record_sha256,
    )
    if not (
        x.examined_extent_and_no_gaps_reviewed
        and x.indication_identity_and_projection_reviewed
        and x.overlap_semantics_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    length = x.window_length_m
    latest = x.examined_length_m - length
    if latest == x.examined_length_m:
        return Calculation(
            status="out_of_scope", values=base, notes=("Window is unresolved at coordinate scale.",)
        )
    intervals = sorted((r.start_m, r.end_m) for r in x.indications)
    if x.overlap_semantics == "union_covered_length":
        merged = []
        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((start, end))
        intervals = merged
    candidates = {0.0, latest}
    for a, b in intervals:
        candidates.update(max(0.0, min(latest, q)) for q in (a, b, a - length, b - length))
    starts = sorted(candidates)
    values = []
    try:
        for start in starts:
            end = min(x.examined_length_m, start + length)
            if end <= start:
                raise ArithmeticError
            value = math.fsum(max(0.0, min(end, b) - max(start, a)) for a, b in intervals)
            if not math.isfinite(value):
                raise ArithmeticError
            values.append(value)
    except (ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope", values=base, notes=("Accumulation exceeds finite arithmetic support.",)
        )
    maximum = max(values)
    indices = [i for i, v in enumerate(values) if v == maximum]
    ranges = []
    previous = None
    for i in indices:
        if previous is not None and i == previous + 1:
            ranges[-1]["maximum_start_m"] = starts[i]
        else:
            ranges.append(dict(minimum_start_m=starts[i], maximum_start_m=starts[i]))
        previous = i
    first = starts[indices[0]]
    end = min(x.examined_length_m, first + length)
    overlaps = [
        dict(indication_id=r.indication_id, overlap_length_m=min(end, r.end_m) - max(first, r.start_m))
        for r in x.indications
        if min(end, r.end_m) > max(first, r.start_m)
    ]
    return Calculation(
        values=base
        | dict(
            maximum_accumulated_length_m=maximum,
            maximizing_start_ranges_m=ranges,
            representative_window_start_m=first,
            representative_window_end_m=end,
            representative_indication_overlaps=overlaps,
            evaluated_breakpoint_count=len(starts),
        ),
        notes=(
            "Evaluate all clipped interval endpoints and endpoints minus window length; overlap measure is piecewise linear.",
            "Sum mode counts overlapping indications separately; union mode counts each covered coordinate once.",
            "No projection, identity matching, uncertainty expansion, standard threshold or acceptance is inferred.",
        ),
    )


class ThicknessSoakBand(Contract):
    band_id: str = Field(min_length=1)
    upper_thickness_m: Positive
    slope_s_per_m: Nonnegative


class PiecewiseThicknessSoakDuration(CorrelationRequest):
    component_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    governing_thickness_m: Positive
    minimum_supported_thickness_m: Nonnegative
    baseline_time_s: Nonnegative
    minimum_soak_time_s: Nonnegative
    thickness_bands: tuple[ThicknessSoakBand, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bands(self):
        ids = [row.band_id for row in self.thickness_bands]
        if len(ids) != len(set(ids)):
            raise ValueError("soak band identities must be unique")
        bounds = [row.upper_thickness_m for row in self.thickness_bands]
        if any(b <= a for a, b in zip(bounds, bounds[1:], strict=False)):
            raise ValueError("soak thickness band bounds must strictly increase")
        if self.minimum_supported_thickness_m > bounds[-1]:
            raise ValueError("minimum thickness support exceeds maximum band support")
        return self


def piecewise_thickness_soak_duration(x: PiecewiseThicknessSoakDuration) -> Calculation:
    base = dict(component_id=x.component_id, procedure_id=x.procedure_id, record_sha256=x.basis.record_sha256)
    if (
        not x.minimum_supported_thickness_m
        <= x.governing_thickness_m
        <= x.thickness_bands[-1].upper_thickness_m
    ):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Thickness lies outside the caller-declared support; no extrapolation.",),
        )
    lower = 0.0
    contributions = []
    try:
        for band in x.thickness_bands:
            width = max(0.0, min(x.governing_thickness_m, band.upper_thickness_m) - lower)
            duration = width * band.slope_s_per_m
            if not math.isfinite(duration) or (width > 0.0 and band.slope_s_per_m > 0.0 and duration == 0.0):
                raise ArithmeticError("unsupported band contribution")
            contributions.append(
                dict(
                    band_id=band.band_id,
                    lower_thickness_m=lower,
                    upper_thickness_m=band.upper_thickness_m,
                    applied_thickness_m=width,
                    contributed_time_s=duration,
                )
            )
            lower = band.upper_thickness_m
        recipe = math.fsum([x.baseline_time_s] + [row["contributed_time_s"] for row in contributions])
        if not math.isfinite(recipe):
            raise ArithmeticError("unsupported recipe total")
    except (ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope", values=base, notes=("Soak recipe exceeds finite arithmetic support.",)
        )
    return Calculation(
        values=base
        | dict(
            band_contributions=contributions,
            recipe_soak_time_s=recipe,
            required_soak_time_s=max(recipe, x.minimum_soak_time_s),
            controlling_terms=(
                ["recipe"]
                if recipe > x.minimum_soak_time_s
                else ["minimum"]
                if recipe < x.minimum_soak_time_s
                else ["recipe", "minimum"]
            ),
        ),
        notes=(
            "Integrate caller nonnegative slopes from zero thickness, add baseline, then apply the declared minimum time.",
            "Minimum supported thickness bounds applicability; it does not reset the recipe integration origin.",
            "No standard coefficients, phase transformation, temperature uniformity, grain-growth or procedure qualification are inferred.",
        ),
    )


class PressureTemperatureRampLimits(CorrelationRequest):
    history_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    metal_temperature_location_id: str = Field(min_length=1)
    pressure_location_id: str = Field(min_length=1)
    clock_basis: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    metal_temperature_K: tuple[Positive, ...] = Field(min_length=2)
    pressure_Pa_abs: tuple[Positive, ...] = Field(min_length=2)
    maximum_heating_rate_K_s: Nonnegative
    maximum_cooling_rate_K_s: Nonnegative
    maximum_pressurizing_rate_Pa_s: Nonnegative
    maximum_depressurizing_rate_Pa_s: Nonnegative
    piecewise_linear_history_and_location_reviewed: bool
    rate_limit_applicability_reviewed: bool

    @model_validator(mode="after")
    def aligned_clock(self):
        if len(self.time_s) != len(self.metal_temperature_K) or len(self.time_s) != len(self.pressure_Pa_abs):
            raise ValueError("time, metal temperature and absolute pressure histories must align")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("history clock must strictly increase")
        return self


def pressure_temperature_ramp_limits(x: PressureTemperatureRampLimits) -> Calculation:
    base = dict(
        history_id=x.history_id,
        component_id=x.component_id,
        metal_temperature_location_id=x.metal_temperature_location_id,
        pressure_location_id=x.pressure_location_id,
        clock_basis=x.clock_basis,
        record_sha256=x.basis.record_sha256,
    )
    if not (x.piecewise_linear_history_and_location_reviewed and x.rate_limit_applicability_reviewed):
        return Calculation(status="needs_data", values=base)
    rows = []
    exceeded = []
    for index, (start, end) in enumerate(zip(x.time_s, x.time_s[1:], strict=False)):
        duration = end - start
        temperature_rate = (x.metal_temperature_K[index + 1] - x.metal_temperature_K[index]) / duration
        pressure_rate = (x.pressure_Pa_abs[index + 1] - x.pressure_Pa_abs[index]) / duration
        if (x.metal_temperature_K[index + 1] != x.metal_temperature_K[index] and temperature_rate == 0.0) or (
            x.pressure_Pa_abs[index + 1] != x.pressure_Pa_abs[index] and pressure_rate == 0.0
        ):
            return Calculation(
                status="out_of_scope",
                values=base,
                notes=("A nonzero interval change underflows the rate representation.",),
            )
        if not all(math.isfinite(value) for value in (duration, temperature_rate, pressure_rate)):
            return Calculation(
                status="out_of_scope",
                values=base,
                notes=("Interval duration or rate exceeds finite arithmetic support.",),
            )
        flags = dict(
            heating=temperature_rate <= x.maximum_heating_rate_K_s,
            cooling=-temperature_rate <= x.maximum_cooling_rate_K_s,
            pressurizing=pressure_rate <= x.maximum_pressurizing_rate_Pa_s,
            depressurizing=-pressure_rate <= x.maximum_depressurizing_rate_Pa_s,
        )
        if not all(flags.values()):
            exceeded.append(index)
        rows.append(
            dict(
                interval_index=index,
                start_time_s=start,
                end_time_s=end,
                temperature_rate_K_s=temperature_rate,
                pressure_rate_Pa_s=pressure_rate,
                within_declared_rate_limits=flags,
            )
        )
    return Calculation(
        values=base
        | dict(
            interval_results=rows,
            exceeded_interval_indices=exceeded,
            all_intervals_within_declared_rate_limits=not exceeded,
        ),
        notes=(
            "Rates are constant only under the reviewed piecewise-linear history interpretation; unobserved excursions are not inferred.",
            "Pressure is absolute and temperature is the identified metal location, not an assumed bulk fluid temperature.",
            "Rate comparisons do not establish pressure-temperature boundary compliance, MPT, hydrogen outgassing, brittle-fracture safety or operating approval.",
        ),
    )


class ImpactWidthTemperatureReduction(Contract):
    specimen_width_m: Positive
    temperature_reduction_K: Nonnegative


class DeclaredImpactSubsizeRequirements(CorrelationRequest):
    method_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_geometry_definition_id: str = Field(min_length=1)
    specimen_width_m: Positive
    reference_specimen_width_m: Positive
    reference_required_mean_energy_J: Positive
    reference_required_individual_energy_J: Positive
    reference_test_temperature_K: Positive
    width_temperature_reduction_table: tuple[ImpactWidthTemperatureReduction, ...] = Field(min_length=2)
    linear_width_energy_requirement_scaling_reviewed: bool
    temperature_table_interpolation_and_applicability_reviewed: bool

    @model_validator(mode="after")
    def width_scope(self):
        if self.specimen_width_m > self.reference_specimen_width_m:
            raise ValueError("subsize width cannot exceed the declared reference width")
        widths = [r.specimen_width_m for r in self.width_temperature_reduction_table]
        if any(b <= a for a, b in zip(widths, widths[1:], strict=False)):
            raise ValueError("temperature-reduction table widths must strictly increase")
        return self


def declared_impact_subsize_requirements(x: DeclaredImpactSubsizeRequirements) -> Calculation:
    base = dict(
        method_id=x.method_id,
        material_condition_id=x.material_condition_id,
        specimen_geometry_definition_id=x.specimen_geometry_definition_id,
        record_sha256=x.basis.record_sha256,
    )
    if not (
        x.linear_width_energy_requirement_scaling_reviewed
        and x.temperature_table_interpolation_and_applicability_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    table = x.width_temperature_reduction_table
    width = x.specimen_width_m
    if not table[0].specimen_width_m <= width <= table[-1].specimen_width_m:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=(
                "Specimen width lies outside the supplied temperature-reduction table; no extrapolation.",
            ),
        )
    exact = next((r for r in table if r.specimen_width_m == width), None)
    if exact is not None:
        reduction = exact.temperature_reduction_K
        bracket = [width, width]
    else:
        left, right = next(
            (a, b)
            for a, b in zip(table, table[1:], strict=False)
            if a.specimen_width_m < width < b.specimen_width_m
        )
        fraction = (width - left.specimen_width_m) / (right.specimen_width_m - left.specimen_width_m)
        reduction = (1.0 - fraction) * left.temperature_reduction_K + fraction * right.temperature_reduction_K
        bracket = [left.specimen_width_m, right.specimen_width_m]
    ratio = width / x.reference_specimen_width_m
    mean = x.reference_required_mean_energy_J * ratio
    individual = x.reference_required_individual_energy_J * ratio
    temperature = x.reference_test_temperature_K - reduction
    if not all(math.isfinite(value) and value > 0.0 for value in (ratio, mean, individual, temperature)):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Scaled requirements or absolute temperature exceed positive finite arithmetic support.",),
        )
    return Calculation(
        values=base
        | dict(
            width_ratio=ratio,
            required_mean_energy_J=mean,
            required_individual_energy_J=individual,
            required_test_temperature_K=temperature,
            temperature_reduction_K=reduction,
            interpolation_width_bracket_m=bracket,
        ),
        notes=(
            "Declared test requirements only; measured impact energy is not normalized or converted to full-size toughness.",
            "No standard table, applicability exception, exemption or material acceptance is inferred.",
        ),
    )


class ScaledStrengthCandidate(Contract):
    candidate_id: str = Field(min_length=1)
    property_definition_id: str = Field(min_length=1)
    strength_Pa: Positive
    multiplier: Positive
    property_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class ScaledStrengthMinimum(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    temperature_K: Positive
    strength_candidates: tuple[ScaledStrengthCandidate, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_candidates(self):
        ids = [r.candidate_id for r in self.strength_candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("strength candidate identities must be unique")
        return self


def scaled_strength_minimum(x: ScaledStrengthMinimum) -> Calculation:
    scaled = {r.candidate_id: r.strength_Pa * r.multiplier for r in x.strength_candidates}
    if not all(math.isfinite(value) and value > 0.0 for value in scaled.values()):
        return Calculation(
            status="out_of_scope",
            values={"record_sha256": x.basis.record_sha256},
            notes=("Scaled strengths exceed positive finite arithmetic support.",),
        )
    minimum = min(scaled.values())
    return Calculation(
        values=dict(
            material_condition_id=x.material_condition_id,
            temperature_K=x.temperature_K,
            scaled_strength_candidates_Pa=scaled,
            minimum_scaled_strength_Pa=minimum,
            governing_candidate_ids=[identifier for identifier, value in scaled.items() if value == minimum],
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Candidate properties, factors, material state and temperature applicability are caller-reviewed and digest-pinned.",
            "Arithmetic minimum only; no standard factors, property generation, creep criterion, allowable-stress qualification or code approval.",
        ),
    )


class ReliefPressureEnvelope(CorrelationRequest):
    equipment_allowable_gauge_pressure_Pa: Positive
    device_set_gauge_pressure_Pa: Nonnegative
    peak_equipment_gauge_pressure_Pa: Nonnegative
    gauge_reference_id: str = Field(min_length=1)
    maximum_set_pressure_multiplier: Positive
    fractional_accumulation_allowance: Nonnegative
    absolute_accumulation_allowance_Pa: Nonnegative
    allowance_combination: Literal["larger_of", "smaller_of", "sum"]
    scenario_id: str = Field(min_length=1)


class ThicknessDimension(Contract):
    dimension_id: str = Field(min_length=1)
    value_m: Positive
    definition: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class SolutionConcentrationConversion(CorrelationRequest):
    component_id: str = Field(min_length=1)
    solution_state_id: str = Field(min_length=1)
    input_basis: Literal[
        "mass_fraction",
        "mass_concentration_kg_m3",
        "amount_concentration_mol_m3",
        "pure_component_volume_per_final_solution_volume",
    ]
    input_value: Nonnegative
    solution_density_kg_m3: Positive
    molar_mass_kg_mol: Positive | None = None
    pure_component_density_kg_m3: Positive | None = None
    pure_component_state_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def basis_requirements(self):
        if self.input_basis == "mass_fraction" and self.input_value > 1.0:
            raise ValueError("mass fraction cannot exceed one")
        if self.input_basis == "amount_concentration_mol_m3" and self.molar_mass_kg_mol is None:
            raise ValueError("amount concentration requires explicit molar mass")
        if (self.pure_component_density_kg_m3 is None) != (self.pure_component_state_id is None):
            raise ValueError("pure component density and state identity must be supplied together")
        if (
            self.input_basis == "pure_component_volume_per_final_solution_volume"
            and self.pure_component_density_kg_m3 is None
        ):
            raise ValueError("pure-component volume basis requires explicit pure component density")
        return self


def solution_concentration_conversion(x: SolutionConcentrationConversion) -> Calculation:
    if x.input_basis == "mass_fraction":
        mass_concentration = x.input_value * x.solution_density_kg_m3
    elif x.input_basis == "amount_concentration_mol_m3":
        mass_concentration = x.input_value * x.molar_mass_kg_mol
    elif x.input_basis == "pure_component_volume_per_final_solution_volume":
        mass_concentration = x.input_value * x.pure_component_density_kg_m3
    else:
        mass_concentration = x.input_value
    fraction = mass_concentration / x.solution_density_kg_m3
    amount = mass_concentration / x.molar_mass_kg_mol if x.molar_mass_kg_mol is not None else None
    pure_ratio = (
        mass_concentration / x.pure_component_density_kg_m3
        if x.pure_component_density_kg_m3 is not None
        else None
    )
    values = [value for value in (mass_concentration, fraction, amount, pure_ratio) if value is not None]
    if (
        not all(math.isfinite(value) for value in values)
        or fraction > 1.0
        or (x.input_value > 0.0 and any(value == 0.0 for value in values))
    ):
        return Calculation(
            status="out_of_scope",
            values={"component_id": x.component_id},
            notes=("Concentration is inconsistent with total solution density or exceeds numeric support.",),
        )
    return Calculation(
        values={
            "component_id": x.component_id,
            "solution_state_id": x.solution_state_id,
            "mass_fraction": fraction,
            "mass_concentration_kg_m3": mass_concentration,
            "amount_concentration_mol_m3": amount,
            "pure_component_volume_per_final_solution_volume": pure_ratio,
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "Density and molar mass are explicit caller properties at reviewed states; unspecified conversions remain null.",
            "Pure-component volume means mass divided by a separately supplied pure-component density, relative to final solution volume. No volume additivity, reagent-stock purity, acid strength, activity, pH or mixing heat is inferred.",
        ),
    )


class BlindIndicatorHoleLigament(CorrelationRequest):
    component_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    hole_id: str = Field(min_length=1)
    local_wall_thickness_m: Positive
    drilled_depth_m: Nonnegative
    reference_required_wall_m: Positive
    same_location_depth_direction_and_blind_hole_role_reviewed: bool


def blind_indicator_hole_ligament(x: BlindIndicatorHoleLigament) -> Calculation:
    base = {
        "component_id": x.component_id,
        "physical_location_id": x.physical_location_id,
        "hole_id": x.hole_id,
        "record_sha256": x.basis.record_sha256,
    }
    if not x.same_location_depth_direction_and_blind_hole_role_reviewed:
        return Calculation(status="needs_data", values=base)
    remaining = x.local_wall_thickness_m - x.drilled_depth_m
    depth_ratio = x.drilled_depth_m / x.reference_required_wall_m
    remaining_fraction = remaining / x.local_wall_thickness_m
    if not all(math.isfinite(v) for v in (remaining, depth_ratio, remaining_fraction)):
        return Calculation(
            status="out_of_scope", values=base, notes=("Hole geometry ratio exceeds finite numeric support.",)
        )
    return Calculation(
        status="computed" if remaining > 0.0 else "out_of_scope",
        values=base
        | {
            "remaining_ligament_m": remaining,
            "remaining_wall_fraction": remaining_fraction,
            "depth_to_reference_required_wall_ratio": depth_ratio,
            "positive_blind_ligament_present": remaining > 0.0,
        },
        notes=(
            "Depth and wall refer to the same reviewed local direction. Through-wall or over-depth geometry is outside this blind-hole model; signed remaining thickness is retained.",
            "This is geometric accounting, not a vent-hole model, permitted-service check, leak indication, pressure capacity, acceptance, corrosion rate or remaining-life prediction.",
        ),
    )


class FrictionResolvedBoltTorque(CorrelationRequest):
    bolt_id: str = Field(min_length=1)
    target_preload_N: Nonnegative
    mean_bearing_diameter_m: Positive
    thread_pitch_diameter_m: Positive
    lead_m_per_turn: Positive
    thread_half_angle_rad: float = Field(ge=0.0, lt=math.pi / 2.0)
    bearing_friction_coefficient: Nonnegative
    thread_friction_coefficient: Nonnegative


class BoltReferenceTorqueScaling(CorrelationRequest):
    bolt_id: str = Field(min_length=1)
    common_geometry_thread_bearing_and_lubrication_condition_id: str = Field(min_length=1)
    reference_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_torque_N_m: Nonnegative
    reference_tensile_stress_Pa: Positive
    target_tensile_stress_Pa: Nonnegative
    unchanged_geometry_and_friction_conditions_reviewed: bool


def bolt_reference_torque_scaling(x: BoltReferenceTorqueScaling) -> Calculation:
    base = {
        "bolt_id": x.bolt_id,
        "record_sha256": x.basis.record_sha256,
        "reference_record_digest": x.reference_record_digest,
    }
    if not x.unchanged_geometry_and_friction_conditions_reviewed:
        return Calculation(status="needs_data", values=base)
    ratio = x.target_tensile_stress_Pa / x.reference_tensile_stress_Pa
    torque = x.reference_torque_N_m * ratio
    if (
        not all(math.isfinite(value) for value in (ratio, torque))
        or (ratio == 0.0 and x.target_tensile_stress_Pa > 0.0)
        or (torque == 0.0 and ratio > 0.0 and x.reference_torque_N_m > 0.0)
    ):
        return Calculation(status="out_of_scope", values=base)
    return Calculation(
        values=base | {"stress_scale_ratio": ratio, "target_torque_N_m": torque},
        notes=(
            "Linear rescaling requires unchanged effective tensile area, thread/bearing geometry and friction conditions. No reference torque or target stress is supplied by the library.",
            "This does not qualify a changed coating, lubricant, retightening history, torque tool, bolt yielding or joint acceptance.",
        ),
    )


def friction_resolved_bolt_torque(x: FrictionResolvedBoltTorque) -> Calculation:
    tangent_lead = (x.lead_m_per_turn / x.thread_pitch_diameter_m) / math.pi
    cosine = math.cos(x.thread_half_angle_rad)
    denominator = cosine - x.thread_friction_coefficient * tangent_lead
    base = {"bolt_id": x.bolt_id, "record_sha256": x.basis.record_sha256}
    if not math.isfinite(tangent_lead) or denominator <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=(
                "Thread raising-torque denominator is nonpositive or lead geometry exceeds numeric support.",
            ),
        )
    thread_factor = (x.thread_friction_coefficient + cosine * tangent_lead) / denominator
    thread = (0.5 * x.target_preload_N) * x.thread_pitch_diameter_m * thread_factor
    bearing = (0.5 * x.target_preload_N) * x.mean_bearing_diameter_m * x.bearing_friction_coefficient
    torque = thread + bearing
    if not all(math.isfinite(v) for v in (thread_factor, thread, bearing, torque)):
        return Calculation(
            status="out_of_scope", values=base, notes=("Torque exceeds finite numeric support.",)
        )
    return Calculation(
        values=base
        | {
            "thread_raising_torque_N_m": thread,
            "bearing_friction_torque_N_m": bearing,
            "target_torque_N_m": torque,
            "lead_angle_rad": math.atan(tangent_lead),
        },
        notes=(
            "Quasistatic thread raising and effective-bearing friction only; lead is axial travel per revolution, not automatically the single-start pitch.",
            "Mean bearing diameter, friction coefficients, profile half-angle and application rights are caller reviewed. No standard friction defaults, torque table, preload scatter, torsional yielding or assembly acceptance is inferred.",
        ),
    )


class ThicknessRetentionFactor(Contract):
    factor_id: str = Field(min_length=1)
    retained_fraction: Fraction
    interpretation: str = Field(min_length=1)


class PipeBendWallAllowance(CorrelationRequest):
    component_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    nominal_wall_m: Positive
    retention_factors: tuple[ThicknessRetentionFactor, ...] = Field(min_length=1)
    corrosion_allowance_m: Nonnegative
    required_pressure_wall_m: Positive
    required_adjoining_wall_m: Nonnegative

    @model_validator(mode="after")
    def unique_factors(self):
        if len({row.factor_id for row in self.retention_factors}) != len(self.retention_factors):
            raise ValueError("thickness retention factor IDs must be unique")
        return self


def pipe_bend_wall_allowance(x: PipeBendWallAllowance) -> Calculation:
    wall = x.nominal_wall_m
    trace = []
    for factor in x.retention_factors:
        wall *= factor.retained_fraction
        trace.append({"factor_id": factor.factor_id, "wall_after_factor_m": wall})
    available = wall - x.corrosion_allowance_m
    required = max(x.required_pressure_wall_m, x.required_adjoining_wall_m)
    if not math.isfinite(available - required):
        return Calculation(
            status="out_of_scope",
            values={"component_id": x.component_id},
            notes=("Signed wall margin exceeds numeric support.",),
        )
    values = {
        "component_id": x.component_id,
        "scenario_id": x.scenario_id,
        "wall_after_retention_m": wall,
        "available_wall_after_allowance_m": available,
        "required_wall_m": required,
        "signed_wall_margin_m": available - required,
        "retention_trace": trace,
        "record_sha256": x.basis.record_sha256,
    }
    return Calculation(
        status="out_of_scope" if available <= 0.0 else "computed",
        values=values,
        notes=(
            "Sequential retained fractions are caller-defined allowances, not measured bend thinning or a forming simulation.",
            "A negative signed margin is preserved; calculation completion is not fabrication acceptance or pressure capacity.",
        ),
    )


class ThicknessSoakDuration(CorrelationRequest):
    component_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    governing_thickness_m: Positive
    proportional_soak_time_s_per_m: Nonnegative
    minimum_soak_time_s: Nonnegative


def thickness_soak_duration(x: ThicknessSoakDuration) -> Calculation:
    proportional = x.governing_thickness_m * x.proportional_soak_time_s_per_m
    if not math.isfinite(proportional) or (proportional == 0.0 and x.proportional_soak_time_s_per_m > 0.0):
        return Calculation(status="out_of_scope", values={"component_id": x.component_id})
    return Calculation(
        values={
            "component_id": x.component_id,
            "procedure_id": x.procedure_id,
            "proportional_soak_time_s": proportional,
            "required_soak_time_s": max(proportional, x.minimum_soak_time_s),
            "controlling_terms": (
                ["proportional"]
                if proportional > x.minimum_soak_time_s
                else ["minimum"]
                if proportional < x.minimum_soak_time_s
                else ["proportional", "minimum"]
            ),
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "Only the caller-declared thickness/time recipe is evaluated. Heating, temperature uniformity, sensor coverage and actual qualified soak time remain separate thermal-history inputs.",
        ),
    )


class TubeExpansionWallReduction(CorrelationRequest):
    tube_id: str = Field(min_length=1)
    tubesheet_hole_id: str = Field(min_length=1)
    initial_outer_diameter_m: Positive
    initial_inner_diameter_m: Positive
    hole_diameter_m: Positive
    expanded_inner_diameter_m: Positive
    final_outer_surface_contact_with_hole_reviewed: bool

    @model_validator(mode="after")
    def physical_diameters(self):
        if self.initial_inner_diameter_m >= self.initial_outer_diameter_m:
            raise ValueError("initial tube diameters must leave positive wall")
        if self.hole_diameter_m < self.initial_outer_diameter_m:
            raise ValueError("hole diameter cannot be smaller than initial outer diameter")
        if self.expanded_inner_diameter_m >= self.hole_diameter_m:
            raise ValueError("expanded diameters must leave positive wall")
        return self


def tube_expansion_wall_reduction(x: TubeExpansionWallReduction) -> Calculation:
    if not x.final_outer_surface_contact_with_hole_reviewed:
        return Calculation(
            status="needs_data", values={"tube_id": x.tube_id, "tubesheet_hole_id": x.tubesheet_hole_id}
        )
    original = (x.initial_outer_diameter_m - x.initial_inner_diameter_m) / 2.0
    expanded = (x.hole_diameter_m - x.expanded_inner_diameter_m) / 2.0
    if original == 0.0 or expanded == 0.0:
        return Calculation(
            status="out_of_scope", values={"reason": "wall thickness underflows numeric support"}
        )
    reduction = (original - expanded) / original
    if not math.isfinite(reduction * 100.0):
        return Calculation(status="out_of_scope", values={"reason": "wall reduction exceeds numeric support"})
    return Calculation(
        values={
            "tube_id": x.tube_id,
            "tubesheet_hole_id": x.tubesheet_hole_id,
            "original_wall_thickness_m": original,
            "expanded_wall_thickness_m": expanded,
            "initial_diametral_clearance_m": x.hole_diameter_m - x.initial_outer_diameter_m,
            "wall_reduction_fraction": reduction,
            "wall_reduction_percent": 100.0 * reduction,
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "Expanded outer diameter equals the reviewed hole diameter; wall change excludes initial clearance take-up. Negative reduction is retained.",
            "No material-specific rolling limit, joint strength, leak tightness or acceptance is inferred.",
        ),
    )


class TubeBendPreformThickness(CorrelationRequest):
    tube_id: str = Field(min_length=1)
    minimum_straight_wall_m: Positive
    tube_outer_diameter_m: Positive
    mean_bend_radius_m: Positive
    curvature_allowance_coefficient: Nonnegative

    @model_validator(mode="after")
    def tubular_geometry(self):
        if self.minimum_straight_wall_m >= self.tube_outer_diameter_m / 2.0:
            raise ValueError("straight tube wall must leave a positive bore")
        if self.mean_bend_radius_m <= self.tube_outer_diameter_m / 2.0:
            raise ValueError("mean bend radius must exceed the outer tube radius")
        return self


def tube_bend_preform_thickness(x: TubeBendPreformThickness) -> Calculation:
    multiplier = 1.0 + x.curvature_allowance_coefficient * (x.tube_outer_diameter_m / x.mean_bend_radius_m)
    thickness = x.minimum_straight_wall_m * multiplier
    if not math.isfinite(thickness) or thickness >= x.tube_outer_diameter_m / 2.0:
        return Calculation(
            status="out_of_scope",
            values={"tube_id": x.tube_id},
            notes=("Requested preform wall does not leave a finite positive bore.",),
        )
    return Calculation(
        values={
            "tube_id": x.tube_id,
            "preform_wall_thickness_m": thickness,
            "curvature_allowance_multiplier": multiplier,
            "added_wall_allowance_m": thickness - x.minimum_straight_wall_m,
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "Curvature coefficient is supplied with reviewed applicability and use rights; no code coefficient or minimum gauge is bundled.",
            "This scalar preform allowance does not predict thinning distribution, residual stress, post-bend heat treatment or tube acceptance.",
        ),
    )


class ThicknessExpression(Contract):
    expression_id: str = Field(min_length=1)
    operation: Literal["minimum", "maximum", "sum"]
    references: tuple[str, ...] = Field(min_length=1)


class GoverningThicknessRecipe(CorrelationRequest):
    component_id: str = Field(min_length=1)
    joint_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    purpose_id: str = Field(min_length=1)
    selected_geometry_case_id: str = Field(min_length=1)
    dimensions: tuple[ThicknessDimension, ...] = Field(min_length=1)
    expressions: tuple[ThicknessExpression, ...] = ()
    output_reference_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def directed_expression_graph(self):
        available = {row.dimension_id for row in self.dimensions}
        if len(available) != len(self.dimensions):
            raise ValueError("thickness dimension IDs must be unique")
        for expression in self.expressions:
            if expression.expression_id in available:
                raise ValueError("thickness expression IDs cannot shadow existing dimensions or expressions")
            if any(reference not in available for reference in expression.references):
                raise ValueError(
                    "thickness expressions may reference only existing dimensions or earlier expressions"
                )
            available.add(expression.expression_id)
        if self.output_reference_id not in available:
            raise ValueError("output thickness reference must exist")
        return self


def governing_thickness_recipe(x: GoverningThicknessRecipe) -> Calculation:
    values = {row.dimension_id: row.value_m for row in x.dimensions}
    trace = []
    for expression in x.expressions:
        arguments = [values[reference] for reference in expression.references]
        try:
            result = (
                min(arguments)
                if expression.operation == "minimum"
                else max(arguments)
                if expression.operation == "maximum"
                else math.fsum(arguments)
            )
        except OverflowError:
            return Calculation(
                status="out_of_scope", values={"numeric_range_expression_id": expression.expression_id}
            )
        if not math.isfinite(result):
            return Calculation(
                status="out_of_scope", values={"numeric_range_expression_id": expression.expression_id}
            )
        values[expression.expression_id] = result
        selected = (
            list(expression.references)
            if expression.operation == "sum"
            else [key for key in expression.references if values[key] == result]
        )
        trace.append(
            {
                "expression_id": expression.expression_id,
                "operation": expression.operation,
                "references": list(expression.references),
                "selected_reference_ids": selected,
                "value_m": result,
            }
        )
    return Calculation(
        values={
            "component_id": x.component_id,
            "joint_geometry_id": x.joint_geometry_id,
            "material_condition_id": x.material_condition_id,
            "purpose_id": x.purpose_id,
            "selected_geometry_case_id": x.selected_geometry_case_id,
            "governing_thickness_m": values[x.output_reference_id],
            "output_reference_id": x.output_reference_id,
            "expression_trace": trace,
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "This evaluates the exact caller-selected geometry recipe; no standard case selection, heat-treatment requirement, impact-test exemption or acceptance is inferred.",
            "All dimensions are positive SI lengths. Sum references retain multiplicity and minimum/maximum ties retain every controlling reference.",
        ),
    )


def relief_pressure_envelope(x: ReliefPressureEnvelope) -> Calculation:
    fractional = x.equipment_allowable_gauge_pressure_Pa * x.fractional_accumulation_allowance
    absolute = x.absolute_accumulation_allowance_Pa
    extra = {
        "larger_of": max(fractional, absolute),
        "smaller_of": min(fractional, absolute),
        "sum": fractional + absolute,
    }[x.allowance_combination]
    set_limit = x.equipment_allowable_gauge_pressure_Pa * x.maximum_set_pressure_multiplier
    peak_limit = x.equipment_allowable_gauge_pressure_Pa + extra
    set_margin = set_limit - x.device_set_gauge_pressure_Pa
    peak_margin = peak_limit - x.peak_equipment_gauge_pressure_Pa
    return Calculation(
        values=dict(
            maximum_set_gauge_pressure_Pa=set_limit,
            maximum_peak_gauge_pressure_Pa=peak_limit,
            set_pressure_margin_Pa=set_margin,
            peak_pressure_margin_Pa=peak_margin,
            declared_rule_outcome="within_declared_limits"
            if min(set_margin, peak_margin) >= 0
            else "exceeds_declared_limits",
            gauge_reference_id=x.gauge_reference_id,
            scenario_id=x.scenario_id,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Only caller-supplied pressure limits are evaluated. No device selection, relieving capacity, backpressure, installation qualification or regulatory acceptance is established.",
        ),
    )


class ConductivityPreheatCorrelation(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    solidus_temperature_K: Positive
    thermal_conductivity_W_mK: Positive
    conductivity_reference_temperature_K: Positive
    reciprocal_conductivity_coefficient_W_m: Positive
    minimum_supported_conductivity_W_mK: Positive
    maximum_supported_conductivity_W_mK: Positive
    minimum_supported_solidus_temperature_K: Positive
    maximum_supported_solidus_temperature_K: Positive

    @model_validator(mode="after")
    def ordered_property_support(self):
        if (
            self.minimum_supported_conductivity_W_mK > self.maximum_supported_conductivity_W_mK
            or self.minimum_supported_solidus_temperature_K > self.maximum_supported_solidus_temperature_K
        ):
            raise ValueError("conductivity and solidus supports must be ordered")
        return self


def conductivity_preheat_correlation(x: ConductivityPreheatCorrelation) -> Calculation:
    base = dict(
        material_condition_id=x.material_condition_id,
        correlation_id=x.correlation_id,
        conductivity_reference_temperature_K=x.conductivity_reference_temperature_K,
        record_sha256=x.basis.record_sha256,
    )
    if not (
        x.minimum_supported_conductivity_W_mK
        <= x.thermal_conductivity_W_mK
        <= x.maximum_supported_conductivity_W_mK
        and x.minimum_supported_solidus_temperature_K
        <= x.solidus_temperature_K
        <= x.maximum_supported_solidus_temperature_K
    ):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Solidus or conductivity is outside caller correlation support; no extrapolation.",),
        )
    offset = Rational(x.reciprocal_conductivity_coefficient_W_m) / Rational(x.thermal_conductivity_W_mK)
    target = Rational(x.solidus_temperature_K) - offset
    if target <= 0:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("The declared correlation gives no positive absolute preheat temperature.",),
        )
    try:
        values = {"temperature_offset_K": float(offset), "correlation_preheat_temperature_K": float(target)}
        if any(not math.isfinite(value) or value <= 0 for value in values.values()):
            raise ArithmeticError("required preheat result is not representable")
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope", values=base, notes=("Required preheat outputs exceed numeric support.",)
        )
    return Calculation(
        values=base | values,
        notes=(
            "Caller solidus minus explicit coefficient divided by conductivity; coefficient unit is W/m and conductivity is W/(m K).",
            "An empirical correlation descriptor, not welding heat input or a qualified preheat instruction. No ambient-temperature clamp, alloy lookup, crack probability, filler selection or acceptance is inferred.",
        ),
    )


class DeclaredTemperatureRateFactor(CorrelationRequest):
    material_condition_id: str = Field(min_length=1)
    mechanism_id: str = Field(min_length=1)
    temperature_K: Positive
    reference_temperature_K: Positive
    temperature_increment_K: Positive
    rate_factor_per_increment: Positive
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive

    @model_validator(mode="after")
    def declared_temperature_support(self):
        if (
            not self.minimum_supported_temperature_K
            <= self.reference_temperature_K
            <= self.maximum_supported_temperature_K
        ):
            raise ValueError("reference temperature must lie inside ordered temperature support")
        return self


def declared_temperature_rate_factor(x: DeclaredTemperatureRateFactor) -> Calculation:
    base = dict(
        material_condition_id=x.material_condition_id,
        mechanism_id=x.mechanism_id,
        reference_temperature_K=x.reference_temperature_K,
        record_sha256=x.basis.record_sha256,
    )
    if not x.minimum_supported_temperature_K <= x.temperature_K <= x.maximum_supported_temperature_K:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Temperature is outside the caller-calibrated support; no extrapolation.",),
        )
    try:
        factor = x.rate_factor_per_increment
        log_base = math.log1p(factor - 1) if 0.5 <= factor <= 2 else math.log(factor)
        exact_log = (
            Rational(log_base)
            * (Rational(x.temperature_K) - Rational(x.reference_temperature_K))
            / Rational(x.temperature_increment_K)
        )
        logarithm = float(exact_log)
        if not math.isfinite(logarithm) or (exact_log and logarithm == 0):
            raise ArithmeticError("rate-factor logarithm is not representable")
        multiplier = math.exp(logarithm)
        if not math.isfinite(multiplier) or multiplier == 0:
            raise ArithmeticError("positive rate factor is not representable")
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Required positive temperature rate factor exceeds numeric support.",),
        )
    return Calculation(
        values=base
        | dict(
            temperature_K=x.temperature_K,
            equivalent_time_rate_multiplier=multiplier,
            natural_log_rate_multiplier=logarithm,
        ),
        notes=(
            "Caller rate factor raised to the temperature difference divided by the declared increment; reference multiplier is one.",
            "A bounded empirical rate multiplier only. No alloy constants, kinetic mechanism, damage, penetration, remaining life or acceptance is inferred.",
        ),
    )


class CompositionIndexFactor(Contract):
    element_id: str = Field(min_length=1)
    power: int = Field(default=1, ge=-4, le=4)

    @model_validator(mode="after")
    def nonzero_power(self):
        if self.power == 0:
            raise ValueError("omit constant factors instead of declaring a zero power")
        return self


class CompositionIndexTerm(Contract):
    term_id: str = Field(min_length=1)
    coefficient: float
    factors: tuple[CompositionIndexFactor, ...] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def unique_elements(self):
        ids = [factor.element_id for factor in self.factors]
        if len(set(ids)) != len(ids):
            raise ValueError("an element occurs once per term; declare its power explicitly")
        return self


class CompositionIndexRecipe(CorrelationRequest):
    index_id: str = Field(min_length=1)
    chemistry: dict[str, Nonnegative] = Field(min_length=1, max_length=60)
    input_mass_basis: Literal["mass_fraction", "mass_percent", "mass_ppm"]
    recipe_mass_basis: Literal["mass_fraction", "mass_percent", "mass_ppm"]
    output_unit: str = Field(min_length=1)
    constant_offset: float = 0.0
    terms: tuple[CompositionIndexTerm, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def explicit_assay_and_terms(self):
        limit = {"mass_fraction": 1.0, "mass_percent": 100.0, "mass_ppm": 1e6}[self.input_mass_basis]
        if (
            any(value > limit for value in self.chemistry.values())
            or math.fsum(self.chemistry.values()) > limit
        ):
            raise ValueError("sum of supplied composition exceeds its declared mass basis")
        if any(not element.strip() for element in self.chemistry):
            raise ValueError("composition element IDs cannot be blank")
        ids = [term.term_id for term in self.terms]
        if len(set(ids)) != len(ids):
            raise ValueError("composition-index term IDs must be unique")
        if any(factor.element_id not in self.chemistry for term in self.terms for factor in term.factors):
            raise ValueError("every recipe element needs an explicit assay; missing is not zero")
        return self


def _composition_recipe_exact_arithmetic(x, floors, *, return_exact=False):
    scales = {"mass_fraction": 1, "mass_percent": 100, "mass_ppm": 1_000_000}
    multiplier = Rational(scales[x.recipe_mass_basis], scales[x.input_mass_basis])
    exact_assay = {element: Rational(value) * multiplier for element, value in x.chemistry.items()}

    def represent(exact):
        value = float(exact)
        if not math.isfinite(value) or (exact != 0 and value == 0):
            raise ArithmeticError("nonzero recipe value cannot be represented")
        return value

    contributions = {}
    assay = {key: represent(value) for key, value in exact_assay.items()}
    effective = {key: max(value, Rational(floors.get(key, 0.0))) for key, value in exact_assay.items()}
    exact_contributions = []
    for term in x.terms:
        exact = Rational(term.coefficient)
        for factor in term.factors:
            if factor.power < 0 and effective[factor.element_id] == 0:
                raise ArithmeticError("a reciprocal composition factor requires a positive effective assay")
            exact *= effective[factor.element_id] ** factor.power
        exact_contributions.append(exact)
        contributions[term.term_id] = represent(exact)
    exact_value = sum(exact_contributions, Rational(x.constant_offset))
    value = represent(exact_value)
    result = (assay, {key: represent(value) for key, value in effective.items()}, contributions, value)
    return (*result, exact_value) if return_exact else result


def composition_index_recipe(x: CompositionIndexRecipe) -> Calculation:
    try:
        assay, _, contributions, value = _composition_recipe_exact_arithmetic(x, {})
    except (ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope", values={"reason": "declared recipe exceeds finite arithmetic support"}
        )
    return Calculation(
        values=dict(
            index_id=x.index_id,
            index_value=value,
            output_unit=x.output_unit,
            recipe_mass_basis=x.recipe_mass_basis,
            converted_assay=assay,
            term_contributions=contributions,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "The supplied assay may be partial; no unreported element or balance alloy is inferred.",
            "Caller-defined composition descriptor with explicit integer powers and reciprocal factors only; no embrittlement, cracking, transition-temperature, probability or acceptance prediction.",
        ),
    )


class FlooredCompositionIndexRecipe(CompositionIndexRecipe):
    constituent_floors: dict[str, Nonnegative] = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def explicit_floors(self):
        limit = {"mass_fraction": 1.0, "mass_percent": 100.0, "mass_ppm": 1e6}[self.recipe_mass_basis]
        used = {factor.element_id for term in self.terms for factor in term.factors}
        if not self.constituent_floors.keys() <= used:
            raise ValueError("floors must reference measured constituents used by the recipe")
        if any(value > limit for value in self.constituent_floors.values()):
            raise ValueError("floor exceeds the declared recipe mass basis")
        return self


def floored_composition_index_recipe(x: FlooredCompositionIndexRecipe) -> Calculation:
    try:
        assay, effective, contributions, value = _composition_recipe_exact_arithmetic(x, x.constituent_floors)
    except (ArithmeticError, ValueError):
        return Calculation(
            status="out_of_scope", values={"reason": "floored recipe exceeds finite arithmetic support"}
        )
    return Calculation(
        values=dict(
            index_id=x.index_id,
            index_value=value,
            output_unit=x.output_unit,
            recipe_mass_basis=x.recipe_mass_basis,
            converted_assay=assay,
            effective_constituents=effective,
            constituent_floors=dict(x.constituent_floors),
            floor_applied_elements=sorted(
                element for element in assay if effective[element] > assay[element]
            ),
            term_contributions=contributions,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Floors apply after conversion to the recipe mass basis; original measured composition is retained.",
            "Effective constituents are algebraic inputs, not a renormalized physical alloy composition.",
            "No empirical constants, support limits, cracking probability or acceptance classification are embedded.",
        ),
    )


class SteelCompositionIndexRecipe(CorrelationRequest):
    method: Literal["J", "X", "RCS", "K"]
    chemistry: dict[str, Nonnegative] = Field(min_length=1, max_length=60)
    input_mass_basis: Literal["mass_fraction", "mass_percent", "mass_ppm"]
    recipe_mass_basis: Literal["mass_fraction", "mass_percent", "mass_ppm"]
    coefficients: dict[str, float] = Field(min_length=1, max_length=4)
    normalization: Positive
    constant_offset: float
    output_unit: str = Field(min_length=1)

    @model_validator(mode="after")
    def declared_method_shape(self):
        required = {
            "J": {"Mn", "Si", "P", "Sn"},
            "X": {"P", "Sb", "Sn", "As"},
            "RCS": {"Cr", "Mo", "V"},
            "K": {"Pb", "Bi", "Sb"},
        }[self.method]
        if not required <= self.chemistry.keys():
            raise ValueError("all elements required by the selected steel index need explicit assays")
        expected_coefficients = {"product_scale"} if self.method == "J" else required
        if set(self.coefficients) != expected_coefficients:
            raise ValueError("coefficient keys must exactly match the selected index structure")
        limit = {"mass_fraction": 1.0, "mass_percent": 100.0, "mass_ppm": 1e6}[self.input_mass_basis]
        if any(v > limit for v in self.chemistry.values()) or math.fsum(self.chemistry.values()) > limit:
            raise ValueError("sum of supplied composition exceeds its declared mass basis")
        return self


def steel_composition_index(x: SteelCompositionIndexRecipe) -> Calculation:
    scales = {"mass_fraction": 1.0, "mass_percent": 100.0, "mass_ppm": 1e6}
    multiplier = scales[x.recipe_mass_basis] / scales[x.input_mass_basis]
    assay = {element: value * multiplier for element, value in x.chemistry.items()}
    if any(value > 0 and assay[element] == 0 for element, value in x.chemistry.items()):
        return Calculation(status="out_of_scope", values={"reason": "mass-basis conversion underflow"})
    try:
        if x.method == "J":
            raw = x.coefficients["product_scale"] * (assay["Mn"] + assay["Si"]) * (assay["P"] + assay["Sn"])
        else:
            raw = math.fsum(coefficient * assay[element] for element, coefficient in x.coefficients.items())
        value = x.constant_offset + raw / x.normalization
        if not math.isfinite(value):
            raise OverflowError
    except (OverflowError, ValueError):
        return Calculation(
            status="out_of_scope", values={"reason": "declared recipe exceeds finite arithmetic support"}
        )
    return Calculation(
        values=dict(
            method=x.method,
            index_value=value,
            output_unit=x.output_unit,
            recipe_mass_basis=x.recipe_mass_basis,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Named composition-index structure with caller-owned coefficients, normalization, assay basis and offset; no built-in empirical coefficients or acceptance limits.",
            "No embrittlement, cracking, transition-temperature, life or failure-probability prediction is implied.",
        ),
    )


class PipingDisplacementAllowance(CorrelationRequest):
    variant: Literal["base", "with_sustained_stress"]
    cold_allowable_Pa: Positive
    hot_allowable_Pa: Positive
    cycle_reduction_factor: Positive
    cold_multiplier: Nonnegative
    hot_multiplier: Nonnegative
    sustained_stress_Pa: Nonnegative | None = None

    @model_validator(mode="after")
    def require_selected_variant(self):
        if (self.variant == "with_sustained_stress") != (self.sustained_stress_Pa is not None):
            raise ValueError("only the sustained-stress variant requires a sustained stress input")
        return self


def piping_displacement_allowance(x: PipingDisplacementAllowance) -> Calculation:
    allowance = x.cycle_reduction_factor * (
        x.cold_multiplier * x.cold_allowable_Pa
        + x.hot_multiplier * x.hot_allowable_Pa
        - (x.sustained_stress_Pa or 0.0)
    )
    if allowance < 0:
        return Calculation(
            status="out_of_scope",
            values={"signed_allowance_Pa": allowance},
            notes=("The declared rule gives a negative allowance; it is not clipped to zero.",),
        )
    return Calculation(
        values={
            "allowable_displacement_stress_range_Pa": allowance,
            "variant": x.variant,
            "record_sha256": x.basis.record_sha256,
        }
    )


class WeldCoolingCorrelation(CorrelationRequest):
    heat_flow_dimension: Literal[2, 3]
    preheat_temperature_K: Positive
    lower_temperature_K: Positive
    upper_temperature_K: Positive
    net_heat_input_J_m: Positive
    plate_thickness_m: Positive | None = None
    shape_factor: Positive
    coefficient_reference_temperature_K: Positive
    coefficient_at_reference: Positive
    coefficient_temperature_slope_per_K: float
    coefficient_unit: Literal["s*m*K/J", "s*m^4*K^2/J^2"]
    minimum_valid_preheat_K: Positive
    maximum_valid_preheat_K: Positive

    @model_validator(mode="after")
    def validate_correlation_support(self):
        if not self.preheat_temperature_K < self.lower_temperature_K < self.upper_temperature_K:
            raise ValueError("preheat must be below both ordered cooling thresholds")
        if not self.minimum_valid_preheat_K <= self.preheat_temperature_K <= self.maximum_valid_preheat_K:
            raise ValueError("preheat lies outside the caller correlation support")
        if self.heat_flow_dimension == 2:
            if self.plate_thickness_m is None or self.coefficient_unit != "s*m^4*K^2/J^2":
                raise ValueError("2D correlation requires thickness and its explicit coefficient unit")
        elif self.plate_thickness_m is not None or self.coefficient_unit != "s*m*K/J":
            raise ValueError("3D correlation excludes thickness and requires its explicit coefficient unit")
        return self


def weld_cooling_correlation(x: WeldCoolingCorrelation) -> Calculation:
    # Evaluate the declared relation without overflowing intermediate powers or
    # losing a small reciprocal-temperature difference to cancellation.
    coefficient_exact = Rational(x.coefficient_at_reference) + Rational(
        x.coefficient_temperature_slope_per_K
    ) * (Rational(x.preheat_temperature_K) - Rational(x.coefficient_reference_temperature_K))
    if coefficient_exact <= 0:
        return Calculation(status="out_of_scope", values={"reason": "nonpositive_effective_coefficient"})
    power = 1 if x.heat_flow_dimension == 3 else 2
    low_delta = Rational(x.lower_temperature_K) - Rational(x.preheat_temperature_K)
    high_delta = Rational(x.upper_temperature_K) - Rational(x.preheat_temperature_K)
    driving = low_delta ** (-power) - high_delta ** (-power)
    heat = Rational(x.net_heat_input_J_m)
    if power == 2:
        heat = (heat / Rational(x.plate_thickness_m)) ** 2
    interval_exact = coefficient_exact * heat * driving * Rational(x.shape_factor)
    try:
        coefficient = float(coefficient_exact)
        interval = float(interval_exact)
        if not math.isfinite(coefficient) or not math.isfinite(interval) or coefficient == 0 or interval == 0:
            raise ArithmeticError
    except ArithmeticError:
        return Calculation(status="out_of_scope", values={"reason": "numeric_range"})
    return Calculation(
        values={
            "cooling_interval_s": interval,
            "effective_coefficient": coefficient,
            "coefficient_unit": x.coefficient_unit,
            "heat_flow_dimension": x.heat_flow_dimension,
            "record_sha256": x.basis.record_sha256,
        }
    )


class FluxMoistureHydrogen(CorrelationRequest):
    combined_water_mass_fraction: float = Field(ge=0, le=1)
    absorbed_water_mass_fraction: float = Field(ge=0, le=1)
    water_vapor_partial_pressure_Pa: Nonnegative
    intercept_m3_H2_kg_deposit: float
    combined_water_coefficient_m3_H2_kg_deposit: float
    absorbed_water_coefficient_m3_H2_kg_deposit: float
    vapor_coefficient_m3_H2_kg_deposit_Pa: float
    maximum_valid_combined_water_fraction: float = Field(ge=0, le=1)
    maximum_valid_absorbed_water_fraction: float = Field(ge=0, le=1)
    maximum_valid_vapor_pressure_Pa: Positive
    gas_volume_reference_temperature_K: Positive
    gas_volume_reference_pressure_Pa: Positive

    @model_validator(mode="after")
    def validate_moisture_support(self):
        if (
            self.combined_water_mass_fraction > self.maximum_valid_combined_water_fraction
            or self.absorbed_water_mass_fraction > self.maximum_valid_absorbed_water_fraction
            or self.water_vapor_partial_pressure_Pa > self.maximum_valid_vapor_pressure_Pa
        ):
            raise ValueError("moisture/vapor inputs exceed the declared empirical support")
        return self


def flux_moisture_hydrogen(x: FluxMoistureHydrogen) -> Calculation:
    estimate = (
        x.intercept_m3_H2_kg_deposit
        + x.combined_water_coefficient_m3_H2_kg_deposit * x.combined_water_mass_fraction
        + x.absorbed_water_coefficient_m3_H2_kg_deposit * x.absorbed_water_mass_fraction
        + x.vapor_coefficient_m3_H2_kg_deposit_Pa * x.water_vapor_partial_pressure_Pa
    )
    if estimate < 0:
        return Calculation(status="out_of_scope", values={"signed_estimate_m3_H2_kg_deposit": estimate})
    return Calculation(
        values={
            "hydrogen_volume_m3_H2_kg_deposit": estimate,
            "hydrogen_volume_ml_H2_100g_deposit": estimate * 100_000.0,
            "gas_volume_reference_temperature_K": x.gas_volume_reference_temperature_K,
            "gas_volume_reference_pressure_Pa": x.gas_volume_reference_pressure_Pa,
            "record_sha256": x.basis.record_sha256,
        }
    )


class CouplingPressure(CorrelationRequest):
    outside_diameter_m: Positive
    thread_root_diameter_m: Positive
    yield_strength_Pa: Positive
    declared_strength_factor: Positive

    @model_validator(mode="after")
    def valid_annulus(self):
        if self.thread_root_diameter_m >= self.outside_diameter_m:
            raise ValueError("thread-root diameter must be smaller than coupling outside diameter")
        return self


def coupling_pressure(x: CouplingPressure) -> Calculation:
    pressure = (
        x.declared_strength_factor
        * x.yield_strength_Pa
        * (1.0 - x.thread_root_diameter_m / x.outside_diameter_m)
    )
    return Calculation(values={"coupling_pressure_Pa": pressure, "record_sha256": x.basis.record_sha256})


class ThreadConnectionPressure(CorrelationRequest):
    outside_diameter_m: Positive
    seal_pitch_diameter_m: Positive
    elastic_modulus_Pa: Positive
    diametral_taper_m_m: Positive
    power_turn_count: Positive
    thread_pitch_m_per_turn: Positive

    @model_validator(mode="after")
    def valid_connection(self):
        if self.seal_pitch_diameter_m >= self.outside_diameter_m:
            raise ValueError("seal pitch diameter must be below outside diameter")
        return self


def thread_connection_pressure(x: ThreadConnectionPressure) -> Calculation:
    ratio = x.seal_pitch_diameter_m / x.outside_diameter_m
    pressure = (
        x.elastic_modulus_Pa
        * x.diametral_taper_m_m
        * x.power_turn_count
        * (x.thread_pitch_m_per_turn / (2.0 * x.seal_pitch_diameter_m))
        * (1.0 - ratio * ratio)
    )
    return Calculation(
        values={"connection_pressure_resistance_Pa": pressure, "record_sha256": x.basis.record_sha256}
    )


class CarbonIndexTerm(Contract):
    term_id: str = Field(min_length=1)
    coefficient: float
    numerator_element: str | None = None
    denominator_element: str | None = None


class CarbonIndexResponse(Contract):
    offset: float
    amplitude: float
    slope_per_carbon_mass_percent: float
    center_carbon_mass_percent: Nonnegative
    minimum_valid_carbon_mass_percent: Nonnegative
    maximum_valid_carbon_mass_percent: Positive


class CarbonEquivalentRecipe(CorrelationRequest):
    method_id: str = Field(min_length=1)
    chemistry_mass_percent: dict[str, Nonnegative] = Field(min_length=1, max_length=40)
    base_carbon_multiplier: float
    terms: tuple[CarbonIndexTerm, ...] = Field(min_length=1, max_length=100)
    carbon_response: CarbonIndexResponse | None = None

    @model_validator(mode="after")
    def validate_chemistry_and_recipe(self):
        if (
            "C" not in self.chemistry_mass_percent
            or sum((Rational(value) for value in self.chemistry_mass_percent.values()), Rational(0)) > 100
        ):
            raise ValueError("explicit carbon and a valid mass-percent composition are required")
        if len({term.term_id for term in self.terms}) != len(self.terms):
            raise ValueError("carbon-index term IDs must be unique")
        for term in self.terms:
            for element in (term.numerator_element, term.denominator_element):
                if element is not None and element not in self.chemistry_mass_percent:
                    raise ValueError("every recipe element must have an explicit assay; missing is not zero")
            if (
                term.denominator_element is not None
                and self.chemistry_mass_percent[term.denominator_element] == 0
            ):
                raise ValueError("a reciprocal/ratio term cannot use a zero assay as denominator")
        if self.carbon_response is not None:
            response = self.carbon_response
            if (
                not response.minimum_valid_carbon_mass_percent
                <= self.chemistry_mass_percent["C"]
                <= response.maximum_valid_carbon_mass_percent
            ):
                raise ValueError("carbon is outside the caller response support")
        return self


def carbon_equivalent_recipe(x: CarbonEquivalentRecipe) -> Calculation:
    contributions = {}
    for term in x.terms:
        numerator = (
            1.0 if term.numerator_element is None else x.chemistry_mass_percent[term.numerator_element]
        )
        denominator = (
            1.0 if term.denominator_element is None else x.chemistry_mass_percent[term.denominator_element]
        )
        exact = Rational(term.coefficient) * Rational(numerator) / Rational(denominator)
        try:
            value = float(exact)
        except OverflowError:
            return Calculation(
                status="out_of_scope",
                values={"method_id": x.method_id},
                notes=("A declared index contribution exceeds numeric support.",),
            )
        if exact != 0 and value == 0.0:
            return Calculation(
                status="out_of_scope",
                values={"method_id": x.method_id},
                notes=("A nonzero index contribution underflows numeric support.",),
            )
        contributions[term.term_id] = value
    response_factor = 1.0
    if x.carbon_response is not None:
        r = x.carbon_response
        response_factor = r.offset + r.amplitude * math.tanh(
            r.slope_per_carbon_mass_percent * (x.chemistry_mass_percent["C"] - r.center_carbon_mass_percent)
        )
    try:
        index = x.base_carbon_multiplier * x.chemistry_mass_percent["C"] + response_factor * math.fsum(
            contributions.values()
        )
    except (OverflowError, ValueError):
        index = math.inf
    if not math.isfinite(response_factor) or not math.isfinite(index):
        return Calculation(
            status="out_of_scope",
            values={"method_id": x.method_id},
            notes=("The declared response or combined index exceeds numeric support.",),
        )
    return Calculation(
        status="computed" if index >= 0 else "out_of_scope",
        values={
            "method_id": x.method_id,
            "carbon_index_mass_percent": index,
            "unscaled_term_contributions": contributions,
            "carbon_response_factor": response_factor,
            "record_sha256": x.basis.record_sha256,
        },
        notes=(
            "A declared composition index is not weldability, preheat selection or cracking probability.",
        ),
    )


def specifications() -> tuple[ModelSpec, ...]:
    def effectiveness_context(x, context):
        if x.asset_id != context.asset_id:
            raise ValueError("effectiveness asset must match the run context")

    assumptions = (
        "Inputs, coefficients, unit conventions, applicability and use rights are caller-reviewed and digest-pinned.",
        "No standard parameter table, grade factor, automatic rule choice, rounding or procedure approval is inferred.",
    )
    return tuple(
        ModelSpec(
            model_id,
            contract,
            evaluator,
            units,
            assumptions,
            (
                {
                    "welding.carbon_equivalent_recipe": "caller_declared_carbon_index_recipe",
                    "materials.composition_index_recipe": "caller_composition_index_polynomial",
                    "materials.steel_composition_index": "caller_named_steel_composition_indices",
                    "fabrication.friction_resolved_bolt_torque": "screw_thread_and_bearing_friction_equilibrium",
                }.get(model_id, SOURCE_ID),
            ),
            version="0.1.2"
            if model_id
            in {
                "materials.declared_chemical_analysis_comparison",
                "materials.composition_index_recipe",
                "materials.floored_composition_index_recipe",
            }
            else "0.1.1"
            if model_id
            in {
                "welding.carbon_equivalent_recipe",
                "welding.cooling_time_correlation",
                "materials.declared_chemical_analysis_comparison",
                "materials.composition_index_recipe",
                "materials.floored_composition_index_recipe",
            }
            else "0.1.0",
            qualification="user_model",
            context_validator=effectiveness_context
            if model_id == "maintenance.declared_equipment_effectiveness"
            else None,
        )
        for model_id, contract, evaluator, units in (
            (
                "welding.conductivity_preheat_correlation",
                ConductivityPreheatCorrelation,
                conductivity_preheat_correlation,
                {
                    "conductivity_reference_temperature_K": "K",
                    "temperature_offset_K": "K",
                    "correlation_preheat_temperature_K": "K",
                },
            ),
            (
                "degradation.declared_temperature_rate_factor",
                DeclaredTemperatureRateFactor,
                declared_temperature_rate_factor,
                {
                    "temperature_K": "K",
                    "reference_temperature_K": "K",
                    "equivalent_time_rate_multiplier": "1",
                    "natural_log_rate_multiplier": "1",
                },
            ),
            (
                "testing.mating_brinell_hardness_difference",
                MatingBrinellHardnessDifference,
                mating_brinell_hardness_difference,
                {
                    "signed_first_minus_second_HBW": "HBW point",
                    "comparison_interval_lower_HBW": "HBW point",
                    "comparison_interval_upper_HBW": "HBW point",
                },
            ),
            (
                "welding.declared_flux_basicity_ratio",
                DeclaredFluxBasicityRatio,
                declared_flux_basicity_ratio,
                {
                    "basicity_ratio": "1",
                    "weighted_numerator": "caller_mass_basis",
                    "weighted_denominator": "caller_mass_basis",
                },
            ),
            (
                "welding.declared_consumable_deposition_rate",
                DeclaredConsumableDepositionRate,
                declared_consumable_deposition_rate,
                {
                    "arc_on_feed_mass_rate_kg_s": "kg/s",
                    "arc_on_deposited_feed_mass_rate_kg_s": "kg/s",
                    "clock_average_deposited_feed_mass_rate_kg_s": "kg/s",
                },
            ),
            (
                "maintenance.declared_equipment_effectiveness",
                DeclaredEquipmentEffectiveness,
                declared_equipment_effectiveness,
                {
                    "availability_fraction": "1",
                    "performance_ratio": "1",
                    "quality_fraction": "1",
                    "equipment_effectiveness": "1",
                },
            ),
            (
                "maintenance.declared_pareto_summary",
                DeclaredParetoSummary,
                declared_pareto_summary,
                {"total_measure": "caller_declared", "ranked_categories[].fraction_of_total": "1"},
            ),
            (
                "welding.well_mixed_gas_purge",
                WellMixedGasPurge,
                well_mixed_gas_purge,
                {
                    "history[].end_time_s": "s",
                    "history[].volume_exchanges": "1",
                    "final_component_mole_fraction": "mole fraction",
                },
            ),
            (
                "materials.declared_analysis_tolerance_recipe",
                DeclaredAnalysisToleranceRecipe,
                declared_analysis_tolerance_recipe,
                {"permitted_variation_mass_fraction": "mass fraction"},
            ),
            (
                "materials.declared_chemical_analysis_comparison",
                DeclaredChemicalAnalysisComparison,
                declared_chemical_analysis_comparison,
                {
                    "comparisons[].effective_minimum_mass_fraction": "mass fraction",
                    "comparisons[].effective_maximum_mass_fraction": "mass fraction",
                    "sum_comparisons[].summed_mass_fraction": "mass fraction",
                    "sum_comparisons[].summed_expanded_uncertainty_bound": "mass fraction",
                    "linear_comparisons[].linear_expression_value": "1",
                    "linear_comparisons[].expanded_interval_bound": "1",
                },
            ),
            (
                "materials.resin_hdt_headroom",
                ResinHdtHeadroom,
                resin_hdt_headroom,
                {
                    "test_flexural_stress_Pa": "Pa",
                    "hdt_headroom_K": "K",
                    "headroom_surplus_K": "K",
                    "declared_headroom_satisfied": "1",
                },
            ),
            (
                "creep.declared_log_slope_rupture_factor",
                DeclaredLogSlopeRuptureFactor,
                declared_log_slope_rupture_factor,
                {"uncapped_factor": "1", "capped_factor": "1", "controlling_terms": "1"},
            ),
            (
                "materials.temperature_trend_strength_scaling",
                TemperatureTrendStrengthScaling,
                temperature_trend_strength_scaling,
                {
                    "reference_temperature_K": "K",
                    "evaluation_temperature_K": "K",
                    "trend_ratio": "1",
                    "trend_ratio_representable": "1",
                    "scaled_reference_strength_Pa": "Pa",
                },
            ),
            (
                "structural.planar_stress_linearization",
                PlanarStressLinearization,
                planar_stress_linearization,
                {
                    "thickness_m": "m",
                    "membrane_stress_Pa": "Pa",
                    "bending_stress_at_start_Pa": "Pa",
                    "bending_stress_at_end_Pa": "Pa",
                    "membrane_force_per_unit_width_N_m": "N/m",
                    "bending_moment_per_unit_width_N": "N",
                    "maximum_absolute_residual_stress_Pa": "Pa",
                },
            ),
            (
                "structural.mean_shear_stress",
                MeanShearStress,
                mean_shear_stress,
                {"signed_mean_shear_stress_Pa": "Pa"},
            ),
            (
                "structural.declared_shell_characteristic_lengths",
                DeclaredShellCharacteristicLengths,
                declared_shell_characteristic_lengths,
                {"sqrt_radius_thickness_m": "m", "declared_lengths_m.*": "m"},
            ),
            (
                "flow.homogeneous_no_slip_mixture_density",
                HomogeneousNoSlipMixtureDensity,
                homogeneous_no_slip_mixture_density,
                {
                    "mixture_density_kg_m3": "kg/m^3",
                    "total_mass_flow_kg_s": "kg/s",
                    "total_volume_flow_m3_s": "m^3/s",
                },
            ),
            (
                "flow.declared_inverse_sqrt_density_velocity",
                DeclaredInverseSqrtDensityVelocity,
                declared_inverse_sqrt_density_velocity,
                {"velocity_descriptor_m_s": "m/s"},
            ),
            (
                "degradation.device_pressure_drop_cavitation_index",
                DevicePressureDropCavitationIndex,
                device_pressure_drop_cavitation_index,
                {
                    "device_pressure_drop_cavitation_index": "1",
                    "inlet_to_outlet_pressure_drop_Pa": "Pa",
                    "inlet_vapor_pressure_margin_Pa": "Pa",
                },
            ),
            (
                "creep.zener_hollomon_parameter",
                ZenerHollomonParameter,
                zener_hollomon_parameter,
                {
                    "material_condition_id": "1",
                    "strain_rate_definition_id": "1",
                    "activation_energy_basis_id": "1",
                    "record_sha256": "1",
                    "temperature_compensation_exponent": "1",
                    "ln_z_relative_to_1_s_1": "1",
                    "z_s_1": "1/s",
                    "z_representable": "1",
                },
            ),
            (
                "thermal.thickness_scaled_rate_limit",
                ThicknessScaledRateLimit,
                thickness_scaled_rate_limit,
                {
                    "component_id": "1",
                    "procedure_id": "1",
                    "rate_direction": "1",
                    "record_sha256": "1",
                    "rule_active": "1",
                    "maximum_rate_K_s": "K/s",
                    "uncapped_rate_K_s": "K/s",
                    "uncapped_rate_representable": "1",
                    "controlling_terms": "1",
                },
            ),
            (
                "welding.declared_hydrogen_susceptibility_index",
                DeclaredHydrogenSusceptibilityIndex,
                declared_hydrogen_susceptibility_index,
                {
                    "material_condition_id": "1",
                    "hydrogen_definition_id": "1",
                    "hydrogen_input_kind": "1",
                    "hydrogen_unit_token": "1",
                    "record_sha256": "1",
                    "index_value": "caller_declared",
                    "composition_contribution": "caller_declared",
                    "hydrogen_contribution": "caller_declared",
                    "log10_hydrogen_ratio": "1",
                },
            ),
            (
                "inspection.hot_tap_branch_test_pressure_cap",
                HotTapBranchTestPressureCap,
                hot_tap_branch_test_pressure_cap,
                {
                    "host_component_id": "1",
                    "branch_component_id": "1",
                    "host_external_capacity_record_id": "1",
                    "branch_test_limit_record_id": "1",
                    "maximum_test_pressure_Pa_abs": "Pa",
                    "governing_limits": "1",
                    "proposed_external_pressure_difference_Pa": "Pa",
                    "pressure_cap_margin_Pa": "Pa",
                    "proposed_pressure_within_declared_upper_limits": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "inspection.indication_window_accumulation",
                IndicationWindowAccumulation,
                indication_window_accumulation,
                {
                    "physical_scope_id": "1",
                    "coordinate_frame_id": "1",
                    "coordinate_origin_id": "1",
                    "overlap_semantics": "1",
                    "record_sha256": "1",
                    "maximum_accumulated_length_m": "m",
                    "maximizing_start_ranges_m": "m",
                    "representative_window_start_m": "m",
                    "representative_window_end_m": "m",
                    "representative_indication_overlaps": "mixed",
                    "evaluated_breakpoint_count": "1",
                },
            ),
            (
                "thermal.piecewise_thickness_soak_duration",
                PiecewiseThicknessSoakDuration,
                piecewise_thickness_soak_duration,
                {
                    "component_id": "1",
                    "procedure_id": "1",
                    "record_sha256": "1",
                    "band_contributions": "mixed",
                    "recipe_soak_time_s": "s",
                    "required_soak_time_s": "s",
                    "controlling_terms": "1",
                },
            ),
            (
                "structural.pressure_temperature_ramp_limits",
                PressureTemperatureRampLimits,
                pressure_temperature_ramp_limits,
                {
                    "history_id": "1",
                    "component_id": "1",
                    "metal_temperature_location_id": "1",
                    "pressure_location_id": "1",
                    "clock_basis": "1",
                    "record_sha256": "1",
                    "interval_results": "mixed",
                    "exceeded_interval_indices": "1",
                    "all_intervals_within_declared_rate_limits": "1",
                },
            ),
            (
                "inspection.declared_impact_subsize_requirements",
                DeclaredImpactSubsizeRequirements,
                declared_impact_subsize_requirements,
                {
                    "method_id": "1",
                    "material_condition_id": "1",
                    "specimen_geometry_definition_id": "1",
                    "record_sha256": "1",
                    "width_ratio": "1",
                    "required_mean_energy_J": "J",
                    "required_individual_energy_J": "J",
                    "required_test_temperature_K": "K",
                    "temperature_reduction_K": "K",
                    "interpolation_width_bracket_m": "m",
                },
            ),
            (
                "materials.scaled_strength_minimum",
                ScaledStrengthMinimum,
                scaled_strength_minimum,
                {
                    "material_condition_id": "1",
                    "temperature_K": "K",
                    "scaled_strength_candidates_Pa": "Pa",
                    "minimum_scaled_strength_Pa": "Pa",
                    "governing_candidate_ids": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "chemistry.solution_concentration_conversion",
                SolutionConcentrationConversion,
                solution_concentration_conversion,
                {
                    "component_id": "1",
                    "solution_state_id": "1",
                    "mass_fraction": "1",
                    "mass_concentration_kg_m3": "kg/m^3",
                    "amount_concentration_mol_m3": "mol/m^3",
                    "pure_component_volume_per_final_solution_volume": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.bolt_reference_torque_scaling",
                BoltReferenceTorqueScaling,
                bolt_reference_torque_scaling,
                {
                    "bolt_id": "1",
                    "record_sha256": "1",
                    "reference_record_digest": "1",
                    "stress_scale_ratio": "1",
                    "target_torque_N_m": "N*m",
                },
            ),
            (
                "inspection.blind_indicator_hole_ligament",
                BlindIndicatorHoleLigament,
                blind_indicator_hole_ligament,
                {
                    "component_id": "1",
                    "physical_location_id": "1",
                    "hole_id": "1",
                    "remaining_ligament_m": "m",
                    "remaining_wall_fraction": "1",
                    "depth_to_reference_required_wall_ratio": "1",
                    "positive_blind_ligament_present": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.friction_resolved_bolt_torque",
                FrictionResolvedBoltTorque,
                friction_resolved_bolt_torque,
                {
                    "bolt_id": "1",
                    "thread_raising_torque_N_m": "N*m",
                    "bearing_friction_torque_N_m": "N*m",
                    "target_torque_N_m": "N*m",
                    "lead_angle_rad": "rad",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.pipe_bend_wall_allowance",
                PipeBendWallAllowance,
                pipe_bend_wall_allowance,
                {
                    "component_id": "1",
                    "scenario_id": "1",
                    "wall_after_retention_m": "m",
                    "available_wall_after_allowance_m": "m",
                    "required_wall_m": "m",
                    "signed_wall_margin_m": "m",
                    "retention_trace": "mixed",
                    "record_sha256": "1",
                },
            ),
            (
                "thermal.thickness_soak_duration",
                ThicknessSoakDuration,
                thickness_soak_duration,
                {
                    "component_id": "1",
                    "procedure_id": "1",
                    "proportional_soak_time_s": "s",
                    "required_soak_time_s": "s",
                    "controlling_terms": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.tube_expansion_wall_reduction",
                TubeExpansionWallReduction,
                tube_expansion_wall_reduction,
                {
                    "tube_id": "1",
                    "tubesheet_hole_id": "1",
                    "original_wall_thickness_m": "m",
                    "expanded_wall_thickness_m": "m",
                    "initial_diametral_clearance_m": "m",
                    "wall_reduction_fraction": "1",
                    "wall_reduction_percent": "%",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.tube_bend_preform_thickness",
                TubeBendPreformThickness,
                tube_bend_preform_thickness,
                {
                    "tube_id": "1",
                    "preform_wall_thickness_m": "m",
                    "curvature_allowance_multiplier": "1",
                    "added_wall_allowance_m": "m",
                    "record_sha256": "1",
                },
            ),
            (
                "fabrication.governing_thickness_recipe",
                GoverningThicknessRecipe,
                governing_thickness_recipe,
                {
                    "component_id": "1",
                    "joint_geometry_id": "1",
                    "material_condition_id": "1",
                    "purpose_id": "1",
                    "selected_geometry_case_id": "1",
                    "governing_thickness_m": "m",
                    "output_reference_id": "1",
                    "expression_trace": "mixed",
                    "record_sha256": "1",
                },
            ),
            (
                "materials.steel_composition_index",
                SteelCompositionIndexRecipe,
                steel_composition_index,
                {
                    "method": "1",
                    "index_value": "caller_declared",
                    "output_unit": "1",
                    "recipe_mass_basis": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "materials.floored_composition_index_recipe",
                FlooredCompositionIndexRecipe,
                floored_composition_index_recipe,
                {
                    "index_value": "caller_declared",
                    "output_unit": "1",
                    "index_id": "1",
                    "recipe_mass_basis": "1",
                    "converted_assay": "caller_declared_mass_basis",
                    "effective_constituents": "caller_declared_mass_basis",
                    "constituent_floors": "caller_declared_mass_basis",
                    "floor_applied_elements": "1",
                    "term_contributions": "caller_declared",
                    "record_sha256": "1",
                },
            ),
            (
                "materials.composition_index_recipe",
                CompositionIndexRecipe,
                composition_index_recipe,
                {
                    "index_value": "caller_declared",
                    "output_unit": "1",
                    "index_id": "1",
                    "recipe_mass_basis": "1",
                    "converted_assay": "caller_declared_mass_basis",
                    "term_contributions": "caller_declared",
                    "record_sha256": "1",
                },
            ),
            (
                "design.relief_pressure_envelope",
                ReliefPressureEnvelope,
                relief_pressure_envelope,
                {
                    "maximum_set_gauge_pressure_Pa": "Pa",
                    "maximum_peak_gauge_pressure_Pa": "Pa",
                    "set_pressure_margin_Pa": "Pa",
                    "peak_pressure_margin_Pa": "Pa",
                    "declared_rule_outcome": "1",
                    "gauge_reference_id": "1",
                    "scenario_id": "1",
                    "record_sha256": "1",
                },
            ),
            (
                "welding.carbon_equivalent_recipe",
                CarbonEquivalentRecipe,
                carbon_equivalent_recipe,
                {"carbon_index_mass_percent": "mass percent"},
            ),
            (
                "piping.displacement_stress_allowance",
                PipingDisplacementAllowance,
                piping_displacement_allowance,
                {"allowable_displacement_stress_range_Pa": "Pa"},
            ),
            (
                "welding.cooling_time_correlation",
                WeldCoolingCorrelation,
                weld_cooling_correlation,
                {"cooling_interval_s": "s"},
            ),
            (
                "welding.flux_moisture_hydrogen",
                FluxMoistureHydrogen,
                flux_moisture_hydrogen,
                {"hydrogen_volume_m3_H2_kg_deposit": "m^3 H2/kg deposit"},
            ),
            (
                "inspection.coupling_pressure",
                CouplingPressure,
                coupling_pressure,
                {"coupling_pressure_Pa": "Pa"},
            ),
            (
                "inspection.thread_connection_pressure",
                ThreadConnectionPressure,
                thread_connection_pressure,
                {"connection_pressure_resistance_Pa": "Pa"},
            ),
        )
    )
