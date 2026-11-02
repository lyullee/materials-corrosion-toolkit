"""Compose an explicit absorbed fire-flux history with multilayer transient conduction."""

from pydantic import Field, model_validator

from .contracts import Contract, Fraction, Nonnegative, canonical_digest
from .models.thermal_transient import ThermalBoundary, TransientConduction1D, transient_conduction_1d


class FireThermalResponse(Contract):
    scenario_id: str = Field(min_length=1)
    incident_flux_W_m2: tuple[Nonnegative, ...] = Field(min_length=2)
    absorbed_fraction: tuple[Fraction, ...] = Field(min_length=2)
    incident_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    protection_material_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    thermal_model: TransientConduction1D
    incident_absorption_and_exposed_face_reviewed: bool

    @model_validator(mode="after")
    def clock(self):
        if len(self.incident_flux_W_m2) != len(self.thermal_model.time_s) or len(
            self.absorbed_fraction
        ) != len(self.thermal_model.time_s):
            raise ValueError("fire flux and absorption must align with the conduction clock")
        if self.thermal_model.left_boundary.kind != "prescribed_heat_flux":
            raise ValueError("exposed left face must explicitly declare prescribed net heat flux")
        return self


def evaluate_fire_thermal_response(request: FireThermalResponse) -> dict:
    base = dict(
        scenario_id=request.scenario_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        thermal_result=None,
    )
    if not request.incident_absorption_and_exposed_face_reviewed:
        return base
    flux = [
        incident * fraction
        for incident, fraction in zip(request.incident_flux_W_m2, request.absorbed_fraction, strict=True)
    ]
    original = request.thermal_model
    boundary = ThermalBoundary(
        boundary_id=original.left_boundary.boundary_id,
        kind="prescribed_heat_flux",
        heat_flux_into_solid_W_m2=flux,
    )
    payload = original.model_dump(mode="python")
    payload["left_boundary"] = boundary.model_dump(mode="python")
    model = TransientConduction1D.model_validate(payload)
    result = transient_conduction_1d(model)
    return base | dict(
        status=result.status,
        thermal_result=result.model_dump(mode="json"),
        applied_net_flux_W_m2=flux,
        basis="Caller net absorbed flux is prescribed at the exposed face; the caller must include any reradiation or external cooling in that net boundary definition. No fire curve, intumescence or ablation law is inferred.",
    )
