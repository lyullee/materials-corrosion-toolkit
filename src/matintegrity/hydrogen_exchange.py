"""Provider-neutral exchange contracts for hydrogen material-transport histories."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class HydrogenTransportHistory(Contract):
    """A digest-bound, unit-explicit snapshot of a successful 1-D transport run.

    The contract transports solver output; it does not qualify material coefficients,
    convert the result into damage, or claim agreement with an experiment.
    """

    schema_version: Literal["matintegrity.hydrogen_transport_history.v1"] = (
        "matintegrity.hydrogen_transport_history.v1"
    )
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    result_id: str = Field(min_length=1)
    native_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    carrier: Literal["atomic_hydrogen", "molecular_hydrogen"]
    carrier_molar_mass_kg_mol: Positive
    geometry: Literal["planar", "spherical_shell"]
    trap_population_ids: list[str]
    elapsed_time_origin_id: str = Field(min_length=1)
    time_s: list[Nonnegative] = Field(min_length=2)
    face_positions_m: list[Nonnegative] = Field(min_length=4)
    cell_centers_m: list[Positive] = Field(min_length=3)
    face_areas_m2: list[Positive] = Field(min_length=4)
    cell_volumes_m3: list[Positive] = Field(min_length=3)
    mobile_entity_mol_m3: list[list[float]]
    trapped_entity_mol_m3: list[list[list[float]]]
    left_integrated_coordinate_flow_mol: list[float]
    right_integrated_coordinate_flow_mol: list[float]
    wall_inventory_mol: list[Nonnegative]
    wall_inventory_residual_mol: list[float]
    total_inventory_residual_mol: list[float]
    left_surface_inventory_mol: list[Nonnegative] | None = None
    right_surface_inventory_mol: list[Nonnegative] | None = None
    concentration_numerical_tolerance_mol_m3: Nonnegative
    function_evaluations: int = Field(ge=1)
    coefficient_basis: str = Field(min_length=1)
    boundary_basis: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def aligned_and_bound(self, info: ValidationInfo):
        nt = len(self.time_s)
        cells = len(self.cell_centers_m)
        traps = len(self.trap_population_ids)
        if len(set(self.trap_population_ids)) != traps or any(
            not value.strip() for value in self.trap_population_ids
        ):
            raise ValueError("trap population IDs must be nonempty and unique")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("transport time must be strictly increasing")
        if len(self.face_positions_m) != cells + 1 or len(self.face_areas_m2) != cells + 1:
            raise ValueError("transport faces must contain exactly one more entry than cells")
        if len(self.cell_volumes_m3) != cells:
            raise ValueError("transport cell volumes must align with cell centers")
        if any(b <= a for a, b in zip(self.face_positions_m, self.face_positions_m[1:], strict=False)):
            raise ValueError("transport face positions must be strictly increasing")
        for index, center in enumerate(self.cell_centers_m):
            if not self.face_positions_m[index] < center < self.face_positions_m[index + 1]:
                raise ValueError("each transport center must lie inside its control volume")
        if len(self.mobile_entity_mol_m3) != nt or any(
            len(row) != cells for row in self.mobile_entity_mol_m3
        ):
            raise ValueError("mobile concentration must have shape time by cell")
        if len(self.trapped_entity_mol_m3) != nt or any(
            len(time_row) != traps or any(len(row) != cells for row in time_row)
            for time_row in self.trapped_entity_mol_m3
        ):
            raise ValueError("trapped concentration must have shape time by trap by cell")
        tolerance = self.concentration_numerical_tolerance_mol_m3
        concentrations = [value for row in self.mobile_entity_mol_m3 for value in row]
        concentrations.extend(
            value for time_row in self.trapped_entity_mol_m3 for row in time_row for value in row
        )
        if any(value < -tolerance for value in concentrations):
            raise ValueError("transport concentration exceeds the declared negative numerical tolerance")
        histories = (
            self.left_integrated_coordinate_flow_mol,
            self.right_integrated_coordinate_flow_mol,
            self.wall_inventory_mol,
            self.wall_inventory_residual_mol,
            self.total_inventory_residual_mol,
            self.left_surface_inventory_mol,
            self.right_surface_inventory_mol,
        )
        if any(values is not None and len(values) != nt for values in histories):
            raise ValueError("transport histories must align with the shared time vector")
        if any(not value.strip() for value in self.limitations):
            raise ValueError("transport limitations must be nonempty statements")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("hydrogen transport payload digest does not match its content")
        return self


def hydrogen_transport_history(**payload: Any) -> HydrogenTransportHistory:
    """Build a normalized history and bind its complete payload to a SHA-256 digest."""

    unsigned = HydrogenTransportHistory.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    normalized = HydrogenTransportHistory.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )
    return normalized
