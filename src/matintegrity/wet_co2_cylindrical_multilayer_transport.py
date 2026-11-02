from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalScaleGeometryHistory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)

MODEL_ID = "integration.wet_co2_cylindrical_multilayer_transport_resistance"
GEOMETRY_SOURCE_ID = "degradation.wet_co2_cylindrical_scale_geometry_history"
DIFFUSIVITY_SOURCE_ID = "caller_cylindrical_phase_solution_diffusivity_records"
METHOD_SOURCE_ID = "cylindrical_multilayer_radial_diffusion_resistance"


class WetCo2LayerSpeciesDiffusivity(Contract):
    phase_id: str = Field(min_length=1, max_length=160)
    species_id: str = Field(min_length=1, max_length=160)
    diffusivity_m2_s: Positive


class WetCo2SolutionSpeciesDiffusivity(Contract):
    species_id: str = Field(min_length=1, max_length=160)
    diffusivity_m2_s: Positive


class WetCo2CylindricalMultilayerTransportKnot(Contract):
    time_s: float = Field(ge=0.0)
    solution_film_thickness_m: Positive
    scale_diffusivities: tuple[WetCo2LayerSpeciesDiffusivity, ...] = Field(min_length=1, max_length=2048)
    solution_diffusivities: tuple[WetCo2SolutionSpeciesDiffusivity, ...] = Field(min_length=1, max_length=64)
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def bind_parameter_record(self):
        payload = {
            "time_s": self.time_s,
            "solution_film_thickness_m": self.solution_film_thickness_m,
            "scale_diffusivities": [row.model_dump(mode="json") for row in self.scale_diffusivities],
            "solution_diffusivities": [row.model_dump(mode="json") for row in self.solution_diffusivities],
        }
        if canonical_digest(payload) != self.parameter_record_sha256:
            raise ValueError("parameter digest must bind the exact knot, film and diffusivity records")
        if not any(row.sha256 == self.parameter_record_sha256 and row.license_id for row in self.parameter_evidence):
            raise ValueError("licensed Evidence must pin the complete knot transport parameter record")
        if len({(row.phase_id, row.species_id) for row in self.scale_diffusivities}) != len(self.scale_diffusivities):
            raise ValueError("scale diffusivity phase/species pairs must be unique")
        if len({row.species_id for row in self.solution_diffusivities}) != len(self.solution_diffusivities):
            raise ValueError("solution-film species diffusivities must be unique")
        return self


class WetCo2CylindricalMultilayerTransportResistance(Contract):
    """Compute species-specific radial resistance through phase layers and liquid film."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_multilayer_transport_resistance.v1"] = (
        "matintegrity.wet_co2_cylindrical_multilayer_transport_resistance.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    geometry: WetCo2CylindricalScaleGeometryHistory
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species_ids: tuple[str, ...] = Field(min_length=1, max_length=64)
    layer_order_steel_to_bore: tuple[str, ...] = Field(min_length=1, max_length=32)
    knots: tuple[WetCo2CylindricalMultilayerTransportKnot, ...] = Field(min_length=1, max_length=5000)
    radial_layer_order_reviewed: bool
    dense_scale_and_solution_film_reviewed: bool

    @model_validator(mode="after")
    def exact_records_and_combinations(self):
        if canonical_digest(self.geometry.model_dump(mode="json")) != self.geometry_sha256:
            raise ValueError("geometry digest differs from nested cylindrical geometry contract")
        phase_ids = {row.phase_id for row in self.geometry.phases}
        species = set(self.species_ids)
        if len(species) != len(self.species_ids) or not species:
            raise ValueError("species IDs must be unique and non-empty")
        if set(self.layer_order_steel_to_bore) != phase_ids or len(self.layer_order_steel_to_bore) != len(phase_ids):
            raise ValueError("radial layer order must contain every geometry phase exactly once")
        if tuple(row.time_s for row in self.knots) != tuple(row.time_s for row in self.geometry.history):
            raise ValueError("transport parameter knots must exactly match geometry history times")
        expected_layers = {(phase_id, species_id) for phase_id in phase_ids for species_id in species}
        for knot in self.knots:
            actual_layers = {(row.phase_id, row.species_id) for row in knot.scale_diffusivities}
            if actual_layers != expected_layers or {row.species_id for row in knot.solution_diffusivities} != species:
                raise ValueError("each knot needs a complete phase-by-species and solution-film diffusivity table")
        return self


def evaluate_wet_co2_cylindrical_multilayer_transport_resistance(
    request: WetCo2CylindricalMultilayerTransportResistance,
) -> Calculation:
    """Return exact cylindrical diffusion resistance and equivalent mass-transfer coefficients."""
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.geometry.asset_id,
        "location_id": request.geometry.location_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "geometry_sha256": request.geometry_sha256,
        "source_ids": [GEOMETRY_SOURCE_ID, DIFFUSIVITY_SOURCE_ID, METHOD_SOURCE_ID],
    }
    if not request.radial_layer_order_reviewed or not request.dense_scale_and_solution_film_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "reviewed_radial_order_dense_scale_and_film_basis_required",
        })
    geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(request.geometry)
    if geometry.status != "computed":
        return Calculation(status=geometry.status, values=base | {
            "reason": "nested_cylindrical_scale_geometry_not_computed",
            "geometry_status": geometry.status,
            "geometry_values": geometry.values,
        })
    phase_map = {row.phase_id: row for row in request.geometry.phases}
    density = [{(row.phase_id, row.species_id): row.diffusivity_m2_s for row in knot.scale_diffusivities}
               for knot in request.knots]
    solution_d = [{row.species_id: row.diffusivity_m2_s for row in knot.solution_diffusivities}
                  for knot in request.knots]
    state_rows = []
    for index, (geometry_row, knot) in enumerate(zip(geometry.values["history"], request.knots, strict=True)):
        steel_inner = float(geometry_row["steel_inner_radius_m"])
        cursor = steel_inner
        interfaces = {}
        phase_inventory = geometry_row["phase_inventory_mol_m_by_phase"]
        for phase_id in request.layer_order_steel_to_bore:
            phase_volume_per_m = float(phase_inventory[phase_id]) * phase_map[phase_id].molar_volume_m3_mol
            radius_sq = cursor * cursor - phase_volume_per_m / math.pi
            if not math.isfinite(radius_sq) or radius_sq <= 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "scale_phase_volume_eliminates_positive_inner_radius",
                    "failed_knot_index": index,
                    "phase_id": phase_id,
                })
            inner = math.sqrt(radius_sq)
            interfaces[phase_id] = {"outer_radius_m": cursor, "inner_radius_m": inner}
            cursor = inner
        bore = float(geometry_row["bore_radius_m"])
        if not math.isclose(cursor, bore, rel_tol=1e-9, abs_tol=1e-12):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "ordered_phase_interfaces_do_not_close_to_geometry_bore",
                "failed_knot_index": index,
                "interface_bore_radius_m": cursor,
                "geometry_bore_radius_m": bore,
            })
        film_outer = bore + knot.solution_film_thickness_m
        species_rows = {}
        for species_id in request.species_ids:
            terms = []
            for phase_id in request.layer_order_steel_to_bore:
                outer = interfaces[phase_id]["outer_radius_m"]
                inner = interfaces[phase_id]["inner_radius_m"]
                if outer > inner:
                    terms.append(math.log(outer / inner) / density[index][(phase_id, species_id)])
            terms.append(math.log(film_outer / bore) / solution_d[index][species_id])
            log_diffusivity_integral_s_m2 = math.fsum(terms)
            resistance_s_m = bore * log_diffusivity_integral_s_m2
            coefficient = 1.0 / resistance_s_m
            if not math.isfinite(coefficient) or coefficient <= 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "cylindrical_layer_transport_coefficient_outside_finite_support",
                    "failed_knot_index": index,
                    "species_id": species_id,
                })
            species_rows[species_id] = {
                "inner_area_resistance_s_m": resistance_s_m,
                "log_diffusivity_integral_s_m2": log_diffusivity_integral_s_m2,
                "inner_area_mass_transfer_coefficient_m_s": coefficient,
                "layer_inner_area_resistance_s_m": {
                    phase_id: (bore * math.log(interfaces[phase_id]["outer_radius_m"] /
                                        interfaces[phase_id]["inner_radius_m"]) /
                               density[index][(phase_id, species_id)]
                               if interfaces[phase_id]["outer_radius_m"] > interfaces[phase_id]["inner_radius_m"]
                               else 0.0)
                    for phase_id in request.layer_order_steel_to_bore
                },
                "solution_film_inner_area_resistance_s_m": bore * math.log(film_outer / bore) / solution_d[index][species_id],
            }
        state_rows.append({
            "time_s": knot.time_s,
            "bore_radius_m": bore,
            "steel_inner_radius_m": steel_inner,
            "solution_film_outer_radius_m": film_outer,
            "phase_interfaces_steel_to_bore": interfaces,
            "species_transport": species_rows,
            "parameter_record_sha256": knot.parameter_record_sha256,
        })
    return Calculation(values=base | {
        "status": "computed",
        "geometry_result_sha256": canonical_digest(geometry.model_dump(mode="json")),
        "knot_count": len(state_rows),
        "layer_order_steel_to_bore": list(request.layer_order_steel_to_bore),
        "history": state_rows,
        "method": "steady_radial_cylindrical_multilayer_resistances_in_series.v1",
        "limitations": [
            "Diffusivities are caller-supplied constants per phase/species at each exact knot; no chemistry or property law is inferred.",
            "Layers are assumed dense, continuous, fully covering, radially ordered and axisymmetric.",
            "The reported coefficient is a steady diffusion resistance bound for the declared layers and solution film; no transient storage, reaction, electrochemical current, porosity, cracking or spallation is solved.",
            "No interpolation is performed between knots and this output does not feed an electrode kinetic solver automatically.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalMultilayerTransportResistance,
        evaluator=evaluate_wet_co2_cylindrical_multilayer_transport_resistance,
        units={
            "history[].species_transport.*.inner_area_resistance_s_m": "s/m",
            "history[].species_transport.*.log_diffusivity_integral_s_m2": "s/m^2",
            "history[].species_transport.*.inner_area_mass_transfer_coefficient_m_s": "m/s",
            "history[].phase_interfaces_steel_to_bore.*.outer_radius_m": "m",
            "history[].phase_interfaces_steel_to_bore.*.inner_radius_m": "m",
        },
        assumptions=(
            "Piecewise constant caller diffusivities are combined as exact logarithmic cylindrical resistances in series.",
            "The scale layers occupy the supplied steel-to-bore order and close exactly to the geometry bore radius.",
            "The solution film is represented as one concentric cylindrical layer outside the scale bore.",
        ),
        source_ids=(GEOMETRY_SOURCE_ID, DIFFUSIVITY_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    )]



