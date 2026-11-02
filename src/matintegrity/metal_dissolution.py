"""Faradaic recession from explicitly identified partial metal-dissolution current histories."""

import math

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class PartialMetalDissolutionHistory(Contract):
    history_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    surface_reaction_id: str = Field(min_length=1)
    provider_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    partial_anodic_current_A_m2: tuple[Nonnegative, ...] = Field(min_length=2)
    electron_count: int = Field(gt=0)
    metal_moles_per_reaction_extent: Positive = 1.0
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    dissolution_current_efficiency: float = Field(gt=0, le=1)
    partial_current_and_uniform_recession_reviewed: bool

    @model_validator(mode="after")
    def clock(self):
        if len(self.elapsed_time_s) != len(self.partial_anodic_current_A_m2) or any(
            b <= a for a, b in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("partial current and strictly increasing clock must align")
        return self


def integrate_partial_metal_dissolution(request: PartialMetalDissolutionHistory) -> dict:
    base = dict(
        history_id=request.history_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
    )
    if not request.partial_current_and_uniform_recession_reviewed:
        return base
    charge = math.fsum(
        (b - a) * (j + k) * 0.5
        for a, b, j, k in zip(
            request.elapsed_time_s[:-1],
            request.elapsed_time_s[1:],
            request.partial_anodic_current_A_m2[:-1],
            request.partial_anodic_current_A_m2[1:],
            strict=True,
        )
    )
    amount = (
        charge
        * request.dissolution_current_efficiency
        * request.metal_moles_per_reaction_extent
        / (request.electron_count * 96485.33212)
    )
    mass = amount * request.metal_molar_mass_kg_mol
    return base | dict(
        status="computed",
        partial_anodic_charge_C_m2=charge,
        metal_dissolved_mol_m2=amount,
        mass_loss_kg_m2=mass,
        uniform_recession_m=mass / request.metal_density_kg_m3,
        basis="Only explicitly identified partial anodic dissolution current is mapped; net mixed-potential current cannot substitute for this input.",
    )
