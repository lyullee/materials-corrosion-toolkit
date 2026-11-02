"""Basic material-test transformations and declared degradation comparisons."""

from __future__ import annotations

import math
from fractions import Fraction

from pydantic import Field

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


def _represent_material_values(values):
    result = {}
    for name, exact in values.items():
        value = float(exact)
        if not math.isfinite(value) or (exact and value == 0):
            raise ArithmeticError("required material result is not representable")
        result[name] = value
    return result


class TensilePoint(Contract):
    force_N: Nonnegative
    initial_area_m2: Positive
    extension_m: Nonnegative
    gauge_length_m: Positive
    uniform_deformation_declared: bool


class FormingAreaReduction(Contract):
    physical_specimen_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    section_pair_id: str = Field(min_length=1)
    original_area_m2: Positive
    deformed_area_m2: Positive
    same_material_section_and_measurement_basis_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


def forming_area_reduction(x: FormingAreaReduction) -> Calculation:
    identities = {
        "physical_specimen_id": x.physical_specimen_id,
        "material_condition_id": x.material_condition_id,
        "section_pair_id": x.section_pair_id,
    }
    if not x.same_material_section_and_measurement_basis_reviewed:
        return Calculation(status="needs_data", values=identities)
    ratio = x.deformed_area_m2 / x.original_area_m2
    if ratio == 0.0 or not math.isfinite(ratio):
        return Calculation(
            status="out_of_scope", values=identities, notes=("Area ratio exceeds numeric range.",)
        )
    reduction = (x.original_area_m2 - x.deformed_area_m2) / x.original_area_m2
    if not math.isfinite(100.0 * reduction):
        return Calculation(
            status="out_of_scope", values=identities, notes=("Area percentage exceeds numeric range.",)
        )
    return Calculation(
        values=identities
        | {
            "area_ratio": ratio,
            "area_reduction_fraction": reduction,
            "area_reduction_percent": 100.0 * reduction,
            "logarithmic_area_ratio": math.log(x.original_area_m2) - math.log(x.deformed_area_m2),
        },
        notes=(
            "Section growth retains a negative reduction. Area change alone establishes neither equivalent plastic strain nor heat-treatment requirements or acceptance.",
        ),
    )


def tensile_point(x: TensilePoint) -> Calculation:
    stress = Fraction(x.force_N) / Fraction(x.initial_area_m2)
    strain = Fraction(x.extension_m) / Fraction(x.gauge_length_m)
    exact = dict(engineering_stress_Pa=stress, engineering_strain=strain)
    if x.uniform_deformation_declared:
        exact["true_stress_Pa"] = stress * (1 + strain)
    try:
        values = _represent_material_values(exact)
        if x.uniform_deformation_declared:
            values["true_strain"] = math.log1p(values["engineering_strain"])
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope", values={}, notes=("Required tensile outputs exceed numeric support.",)
        )
    return Calculation(
        values=values, notes=("True-stress conversion is withheld unless uniform deformation is declared.",)
    )


class DuctilityComparison(Contract):
    baseline_elongation_fraction: Positive
    exposed_elongation_fraction: Nonnegative


def ductility_comparison(x: DuctilityComparison) -> Calculation:
    retention = Fraction(x.exposed_elongation_fraction) / Fraction(x.baseline_elongation_fraction)
    try:
        values = _represent_material_values(
            dict(ductility_retention_ratio=retention, relative_ductility_loss=1 - retention)
        )
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope", values={}, notes=("Required ductility outputs exceed numeric support.",)
        )
    return Calculation(
        values=values,
        notes=(
            "A negative loss is retained rather than clipped; specimen scatter and test conditions remain relevant.",
        ),
    )


class DissolutionCharge(Contract):
    anodic_charge_C: Nonnegative
    equivalent_weight_kg_mol_electron: Positive
    density_kg_m3: Positive
    current_efficiency: float = Field(gt=0, le=1)


def dissolution_charge(x: DissolutionCharge) -> Calculation:
    mass = (
        Fraction(x.anodic_charge_C)
        * Fraction(x.equivalent_weight_kg_mol_electron)
        * Fraction(x.current_efficiency)
        / Fraction(96485.33212331001)
    )
    try:
        values = _represent_material_values(
            dict(dissolved_mass_kg=mass, dissolved_volume_m3=mass / Fraction(x.density_kg_m3))
        )
    except (ArithmeticError, OverflowError):
        return Calculation(
            status="out_of_scope", values={}, notes=("Required dissolution outputs exceed numeric support.",)
        )
    return Calculation(
        values=values,
        notes=("Volume alone does not identify pit shape or maximum penetration.",),
    )


def specifications():
    return [
        ModelSpec(
            "fabrication.forming_area_reduction",
            FormingAreaReduction,
            forming_area_reduction,
            {
                "physical_specimen_id": "1",
                "material_condition_id": "1",
                "section_pair_id": "1",
                "area_ratio": "1",
                "area_reduction_fraction": "1",
                "area_reduction_percent": "%",
                "logarithmic_area_ratio": "1",
            },
            (
                "Matched material sections and SI areas are explicitly reviewed; no material constitutive law is inferred.",
            ),
            ("section_area_change_kinematics",),
        ),
        ModelSpec(
            "materials.tensile_point",
            TensilePoint,
            tensile_point,
            {
                "engineering_stress_Pa": "Pa",
                "engineering_strain": "1",
                "true_stress_Pa": "Pa",
                "true_strain": "1",
            },
            (
                "Gauge extension and original section are supplied; uniform-volume conversion excludes necking.",
            ),
            ("uniaxial_test_kinematics",),
            version="1.0.1",
        ),
        ModelSpec(
            "materials.ductility_retention",
            DuctilityComparison,
            ductility_comparison,
            {"ductility_retention_ratio": "1", "relative_ductility_loss": "1"},
            (
                "Matched test conditions and declared reference specimen; not a structural failure probability.",
            ),
            ("declared_property_ratio",),
            version="1.0.1",
        ),
        ModelSpec(
            "corrosion.charge_to_loss",
            DissolutionCharge,
            dissolution_charge,
            {"dissolved_mass_kg": "kg", "dissolved_volume_m3": "m^3"},
            (
                "Declared alloy dissolution equivalent and current efficiency; cathodic current is not included in anodic charge.",
            ),
            ("faraday_electrolysis",),
            version="1.0.1",
        ),
    ]
