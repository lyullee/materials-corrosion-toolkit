from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_shear_limited_scale_removal import (
    WetCo2CylindricalShearLimitedScaleRemoval,
    WetCo2ScaleShearKnot,
    evaluate_wet_co2_cylindrical_shear_limited_scale_removal,
)

MODEL_ID = "integration.wet_co2_cylindrical_hydraulics_to_scale_removal"
HYDRAULICS_MODEL_ID = "integration.wet_co2_cylindrical_steady_hydraulics"
HYDRAULICS_SOURCE_ID = "caller_cylindrical_steady_hydraulics_result"
REMOVAL_SOURCE_ID = "caller_calibrated_cylindrical_scale_shear_removal_request"


class WetCo2CylindricalHydraulicsToScaleRemoval(Contract):
    """Bind one computed pipe hydraulics history into an unchanged shear-removal request."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_hydraulics_to_scale_removal.v1"] = (
        "matintegrity.wet_co2_cylindrical_hydraulics_to_scale_removal.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    hydraulics_result: Calculation
    hydraulics_evidence: Evidence
    shear_removal_request: WetCo2CylindricalShearLimitedScaleRemoval
    same_scope_and_area_basis_reviewed: bool

    @model_validator(mode="after")
    def bind_hydraulics_result(self):
        if self.hydraulics_result.status != "computed":
            raise ValueError("cylindrical hydraulics result must be computed")
        if self.hydraulics_result.values.get("model_id") != HYDRAULICS_MODEL_ID:
            raise ValueError("source result must come from the cylindrical steady hydraulics evaluator")
        digest = canonical_digest(self.hydraulics_result.model_dump(mode="json"))
        if self.hydraulics_evidence.source_id != HYDRAULICS_MODEL_ID or self.hydraulics_evidence.sha256 != digest:
            raise ValueError("Evidence must pin the exact hydraulic result and model ID")
        if not self.hydraulics_evidence.license_id:
            raise ValueError("hydraulic result Evidence must state its use license")
        hydraulic_values = self.hydraulics_result.values
        request = self.shear_removal_request
        if hydraulic_values.get("assessment_id") != self.assessment_id or request.assessment_id != self.assessment_id:
            raise ValueError("hydraulics and shear-removal request must share the assessment ID")
        if (hydraulic_values.get("asset_id") != request.geometry.asset_id
                or hydraulic_values.get("location_id") != request.geometry.location_id):
            raise ValueError("hydraulics and scale-removal request must share asset/location scope")
        if hydraulic_values.get("geometry_result_sha256") != canonical_digest(
            request.geometry_result.model_dump(mode="json")
        ):
            raise ValueError("hydraulics and scale-removal request must use the same computed geometry result")
        hydraulic_rows = hydraulic_values.get("history", [])
        expected_times = tuple(row.time_s for row in request.geometry.history)
        if tuple(float(row["time_s"]) for row in hydraulic_rows) != expected_times:
            raise ValueError("hydraulic wall-shear knots must exactly match scale-removal geometry knots")
        if tuple(float(row["time_s"]) for row in request.geometry_result.values.get("history", [])) != expected_times:
            raise ValueError("scale-removal geometry result must use the same exact knot schedule")
        return self


def evaluate_wet_co2_cylindrical_hydraulics_to_scale_removal(
    request: WetCo2CylindricalHydraulicsToScaleRemoval,
) -> Calculation:
    """Map explicit hydraulic shear magnitude while preserving caller detachment calibration."""
    hydraulic_rows = request.hydraulics_result.values["history"]
    hydraulic_digest = canonical_digest(request.hydraulics_result.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.shear_removal_request.geometry.asset_id,
        "location_id": request.shear_removal_request.geometry.location_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "hydraulics_result_sha256": hydraulic_digest,
        "detachment_law_record_sha256": request.shear_removal_request.detachment_law_record_sha256,
        "source_ids": [HYDRAULICS_SOURCE_ID, REMOVAL_SOURCE_ID],
    }
    if not request.same_scope_and_area_basis_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "hydraulic_to_detachment_scope_and_inner_area_basis_review_required",
        })
    new_knots = []
    provenance_rows = []
    for row in hydraulic_rows:
        magnitude = float(row["wall_shear_stress_magnitude_Pa"])
        time_s = float(row["time_s"])
        signed = float(row["signed_wall_shear_stress_Pa"])
        knot_payload = {"time_s": time_s, "wall_shear_stress_Pa": magnitude}
        knot_digest = canonical_digest(knot_payload)
        new_knots.append(WetCo2ScaleShearKnot(
            time_s=time_s,
            wall_shear_stress_Pa=magnitude,
            record_sha256=knot_digest,
            evidence=(Evidence(
                source_id=MODEL_ID,
                origin="model_prediction",
                citation=(f"Absolute wall-shear magnitude mapped unchanged from hydraulic result {hydraulic_digest}; "
                          f"signed source value {signed} Pa retained in adapter lineage."),
                license_id=request.hydraulics_evidence.license_id,
                sha256=knot_digest,
            ),),
        ))
        provenance_rows.append({
            "time_s": time_s,
            "signed_wall_shear_stress_Pa": signed,
            "wall_shear_stress_magnitude_Pa": magnitude,
            "hydraulic_parameter_record_sha256": row.get("hydraulic_parameter_record_sha256"),
            "mapped_shear_knot_sha256": knot_digest,
        })
    payload = request.shear_removal_request.model_dump(mode="json")
    payload["shear_history"] = [row.model_dump(mode="json") for row in new_knots]
    try:
        bound_request = WetCo2CylindricalShearLimitedScaleRemoval.model_validate(payload)
    except ValueError as exc:
        return Calculation(status="needs_data", values=base | {
            "reason": "hydraulic_shear_history_did_not_bind_to_scale_removal_contract",
            "detail": str(exc),
            "hydraulic_shear_mapping": provenance_rows,
        })
    removal = evaluate_wet_co2_cylindrical_shear_limited_scale_removal(bound_request)
    return Calculation(status=removal.status, values=base | {
        "hydraulic_shear_mapping": provenance_rows,
        "mapped_wall_shear_interpretation": "explicit_hydraulic_wall_shear_magnitude_Pa",
        "signed_hydraulic_shear_is_retained_as_lineage_and_not_used_as_a_signed_removal_rate": True,
        "detachment_calibration_unchanged": True,
        "detachment_law_record_sha256_after_mapping": bound_request.detachment_law_record_sha256,
        "scale_removal_result": removal.model_dump(mode="json"),
        "limitations": [
            "The adapter maps the hydraulics model's explicit nonnegative wall-shear magnitude without changing threshold, coefficient, exponent, or law digest.",
            "Signed shear is retained as source lineage; the threshold removal law consumes magnitude only.",
            "A caller must review common scope and inner wetted-area basis; the adapter does not infer a conversion between different stress bases.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalHydraulicsToScaleRemoval,
        evaluator=evaluate_wet_co2_cylindrical_hydraulics_to_scale_removal,
        units={
            "hydraulic_shear_mapping[].time_s": "s",
            "hydraulic_shear_mapping[].signed_wall_shear_stress_Pa": "Pa",
            "hydraulic_shear_mapping[].wall_shear_stress_magnitude_Pa": "Pa",
            "scale_removal_result.values.history[].actual_detachment_mol_m": "mol/m",
        },
        assumptions=(
            "The hydraulic and shear-removal contracts share exact scope, geometry result digest and time knots.",
            "The removal request's calibration fields remain unchanged; only the shear schedule is populated from explicit hydraulic magnitudes.",
            "The caller approves the mapping and area basis before calculation.",
        ),
        source_ids=(HYDRAULICS_SOURCE_ID, REMOVAL_SOURCE_ID),
        qualification="user_model",
    )]
