"""Caller-parameterized diffusion resistance through a layered protective scale."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class ScaleTransportLayer(Contract):
    layer_id: str = Field(min_length=1)
    thickness_m: Nonnegative
    effective_diffusivity_m2_s: Positive
    solution_to_layer_partition_coefficient: Positive


class LayeredScaleDiffusionLimit(Contract):
    schema_version: Literal["matintegrity.layered_scale_diffusion_limit.v1"] = (
        "matintegrity.layered_scale_diffusion_limit.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    solution_condition_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    scale_state_id: str = Field(min_length=1)
    transported_species_id: str = Field(min_length=1)
    surface_area_basis_id: str | None = Field(default=None, min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transport_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    scale_history_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    scale_history_time_s: Nonnegative | None = None
    scale_history_model_id: str | None = None
    scale_history_phase_id: str | None = None
    scale_history_layer_id: str | None = None
    scale_history_covered_area_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    scale_history_mapping_reviewed: bool | None = None
    bulk_concentration_mol_m3: Nonnegative
    interface_concentration_mol_m3: Nonnegative
    bare_film_thickness_m: Positive
    bare_diffusivity_m2_s: Positive
    covered_area_fraction: float = Field(ge=0.0, le=1.0)
    layers: tuple[ScaleTransportLayer, ...] = Field(min_length=1, max_length=20)
    electron_equivalents_per_mole: Positive
    concentration_basis_and_partition_reviewed: bool
    effective_diffusivity_support_reviewed: bool
    area_coverage_and_uniform_parallel_path_reviewed: bool
    electron_equivalent_mapping_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_state(self):
        if self.interface_concentration_mol_m3 > self.bulk_concentration_mol_m3:
            raise ValueError("the declared interface concentration must not exceed the bulk concentration")
        ids = [layer.layer_id for layer in self.layers]
        if len(ids) != len(set(ids)):
            raise ValueError("scale layer IDs must be unique and ordered as the caller transport path")
        values = (
            self.bulk_concentration_mol_m3,
            self.interface_concentration_mol_m3,
            self.bare_film_thickness_m,
            self.bare_diffusivity_m2_s,
            self.covered_area_fraction,
            self.electron_equivalents_per_mole,
        )
        if any(not math.isfinite(value) for value in values):
            raise ValueError("transport state values must be finite")
        lineage = (
            self.scale_history_result_digest,
            self.scale_history_time_s,
            self.scale_history_model_id,
            self.scale_history_phase_id,
            self.scale_history_layer_id,
            self.scale_history_mapping_reviewed,
        )
        if any(value is not None for value in lineage) and any(value is None for value in lineage):
            raise ValueError("scale-history provenance fields must be supplied together")
        if self.scale_history_result_digest is not None and not self.scale_history_mapping_reviewed:
            raise ValueError("linked scale history requires an explicit reviewed phase-to-layer mapping")
        if self.scale_history_model_id == "chemistry.caller_scale_coverage_kinetics":
            if self.scale_history_covered_area_fraction is None:
                raise ValueError("linked coverage kinetics must retain the selected covered-area fraction")
        elif self.scale_history_covered_area_fraction is not None:
            raise ValueError("covered-area fraction lineage is only valid for a coverage-history model")
        if self.scale_history_time_s is not None and not math.isfinite(self.scale_history_time_s):
            raise ValueError("scale-history time must be finite")
        for layer in self.layers:
            if not all(math.isfinite(value) for value in (
                layer.thickness_m,
                layer.effective_diffusivity_m2_s,
                layer.solution_to_layer_partition_coefficient,
            )):
                raise ValueError("layer thickness, diffusivity and partition coefficient must be finite")
            if layer.thickness_m < 0:
                raise ValueError("layer thickness cannot be negative")
        return self


def layered_scale_diffusion_limit(x: LayeredScaleDiffusionLimit) -> Calculation:
    """Return a diffusion-limited flux bound for parallel covered and bare areas.

    Each declared layer contributes ``L / (D_eff K)`` resistance. Covered and
    uncovered patches are mixed in parallel using the caller area fraction.
    This is a mass-transfer upper bound, not a corrosion-rate prediction.
    """
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "physical_scope_id": x.physical_scope_id,
        "substrate_condition_id": x.substrate_condition_id,
        "solution_condition_id": x.solution_condition_id,
        "scale_state_id": x.scale_state_id,
        "scale_phase_id": x.scale_phase_id,
        "transported_species_id": x.transported_species_id,
        "surface_area_basis_id": x.surface_area_basis_id,
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "source_sha256": x.source_sha256,
        "condition_sha256": x.condition_sha256,
        "transport_configuration_sha256": x.transport_configuration_sha256,
        "scale_history_result_digest": x.scale_history_result_digest,
        "scale_history_time_s": x.scale_history_time_s,
        "scale_history_model_id": x.scale_history_model_id,
        "scale_history_phase_id": x.scale_history_phase_id,
        "scale_history_layer_id": x.scale_history_layer_id,
        "scale_history_covered_area_fraction": x.scale_history_covered_area_fraction,
        "scale_history_mapping_reviewed": x.scale_history_mapping_reviewed,
        "input_sha256": digest,
    }
    reviews = {
        "concentration_basis_and_partition_reviewed": x.concentration_basis_and_partition_reviewed,
        "effective_diffusivity_support_reviewed": x.effective_diffusivity_support_reviewed,
        "area_coverage_and_uniform_parallel_path_reviewed": x.area_coverage_and_uniform_parallel_path_reviewed,
        "electron_equivalent_mapping_reviewed": x.electron_equivalent_mapping_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    delta = x.bulk_concentration_mol_m3 - x.interface_concentration_mol_m3
    try:
        bare_resistance = x.bare_film_thickness_m / x.bare_diffusivity_m2_s
        layer_resistances = [
            layer.thickness_m / (
                layer.effective_diffusivity_m2_s * layer.solution_to_layer_partition_coefficient
            )
            for layer in x.layers
        ]
        covered_resistance = bare_resistance + math.fsum(layer_resistances)
        bare_flux = delta / bare_resistance
        covered_flux = delta / covered_resistance
        area_average_flux = (
            x.covered_area_fraction * covered_flux
            + (1.0 - x.covered_area_fraction) * bare_flux
        )
        current_density = 96485.33212 * x.electron_equivalents_per_mole * area_average_flux
        reduction = 0.0 if bare_flux == 0 else 1.0 - area_average_flux / bare_flux
        outputs = (bare_resistance, covered_resistance, bare_flux, covered_flux, area_average_flux, current_density, reduction)
        if not all(math.isfinite(value) and value >= 0 for value in outputs[:-1]) or not math.isfinite(reduction):
            raise ArithmeticError("layered transport result is outside finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error)})

    return Calculation(values=base | {
        "driving_concentration_difference_mol_m3": delta,
        "bare_film_resistance_s_m": bare_resistance,
        "scale_layer_resistances_s_m": layer_resistances,
        "covered_path_resistance_s_m": covered_resistance,
        "bare_area_flux_limit_mol_m2_s": bare_flux,
        "covered_area_flux_limit_mol_m2_s": covered_flux,
        "area_average_flux_limit_mol_m2_s": area_average_flux,
        "area_average_diffusion_limited_current_density_A_m2": current_density,
        "flux_limit_reduction_fraction_vs_bare_film": reduction,
        "covered_area_fraction": x.covered_area_fraction,
        "layer_ids_in_transport_order": [layer.layer_id for layer in x.layers],
        "transport_model": "steady_series_diffusion_resistance_with_parallel_area_mixing",
    }, notes=(
        "Flux and Faraday-equivalent current are diffusion-limited upper bounds conditional on the caller concentration, partition, diffusivity, layer and area inputs.",
        "The calculation does not determine scale morphology or coverage, solve electrochemical charge balance or Butler-Volmer kinetics, or predict an actual corrosion current, metal loss, protection factor, life or acceptance.",
    ))


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "chemistry.layered_scale_diffusion_limit",
            LayeredScaleDiffusionLimit,
            layered_scale_diffusion_limit,
            {
                "driving_concentration_difference_mol_m3": "mol/m3",
                "bare_film_resistance_s_m": "s/m",
                "scale_layer_resistances_s_m[]": "s/m",
                "covered_path_resistance_s_m": "s/m",
                "bare_area_flux_limit_mol_m2_s": "mol/m2/s",
                "covered_area_flux_limit_mol_m2_s": "mol/m2/s",
                "area_average_flux_limit_mol_m2_s": "mol/m2/s",
                "area_average_diffusion_limited_current_density_A_m2": "A/m2",
                "flux_limit_reduction_fraction_vs_bare_film": "1",
                "covered_area_fraction": "1",
                "scale_history_covered_area_fraction": "1",
            },
            (
                "Caller-supplied layered effective diffusivity, partition coefficients, thickness, concentration endpoints and covered-area fraction define a steady diffusion-limit bound.",
                "The result is not a Butler-Volmer or corrosion-rate solution and does not infer scale formation, morphology, adhesion or protection from scale thickness.",
            ),
            ("caller_layered_scale_diffusion_limit",),
            qualification="user_model",
        )
    ]
