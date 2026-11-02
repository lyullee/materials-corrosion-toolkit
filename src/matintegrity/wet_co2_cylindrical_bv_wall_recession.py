"""Map computed BV alloy release into an exact-knot cylindrical wall-radius history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_spatial_mixed_potential import (
    MODEL_ID as SPATIAL_MIXED_POTENTIAL_MODEL_ID,
    WetCo2CylindricalSpatialMixedPotential,
)
from .wet_co2_cylindrical_scale_geometry import evaluate_wet_co2_cylindrical_scale_geometry_history

MODEL_ID = "integration.wet_co2_cylindrical_bv_wall_recession"
SOURCE_ID = "computed_bv_alloy_element_release_to_cylindrical_recession"


class WetCo2CylindricalBVWallRecession(Contract):
    """Evidence-bound transfer from a computed electrochemical loss to exact radii."""

    schema_version: Literal["matintegrity.wet_co2_cylindrical_bv_wall_recession.v1"] = (
        "matintegrity.wet_co2_cylindrical_bv_wall_recession.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_mixed_potential_request: WetCo2CylindricalSpatialMixedPotential
    spatial_mixed_potential_result: Calculation
    spatial_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    maximum_radius_geometry_residual_m: Positive
    computed_result_and_source_mapping_reviewed: bool
    recession_only_and_no_wall_deposition_reviewed: bool
    axisymmetric_uniform_alloy_density_mapping_reviewed: bool
    computational_use_authorized: bool


def evaluate_wet_co2_cylindrical_bv_wall_recession(
    request: WetCo2CylindricalBVWallRecession,
) -> Calculation:
    """Reconstruct bore radii from integrated reaction extents and alloy atom release.

    Inventories are per unit axial length. For each knot the exact relation is
    pi*(r_k**2-r_0**2) = released_mass_per_length / density.
    """
    source_request = request.spatial_mixed_potential_request
    source_result = request.spatial_mixed_potential_result
    source_values = source_result.values
    result_digest = canonical_digest(source_result.model_dump(mode="json"))
    input_digest = canonical_digest(source_request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "spatial_result_sha256": request.spatial_result_sha256,
        "spatial_mixed_potential_input_sha256": input_digest,
        "geometry_input_sha256": canonical_digest(source_request.geometry.model_dump(mode="json")),
        "asset_id": source_request.geometry.asset_id,
        "location_id": source_request.geometry.location_id,
        "time_basis_id": source_request.geometry.time_basis_id,
        "radius_method": "exact_axisymmetric_annular_volume_from_integrated_BV_element_release",
    }
    if (source_result.status != "computed"
            or source_values.get("model_id") != SPATIAL_MIXED_POTENTIAL_MODEL_ID
            or source_values.get("input_sha256") != input_digest
            or result_digest != request.spatial_result_sha256):
        return Calculation(status="needs_data", values=base | {
            "reason": "computed_spatial_result_identity_or_digest_mismatch",
        })
    review_fields = {
        "computed_result_and_source_mapping_reviewed": request.computed_result_and_source_mapping_reviewed,
        "recession_only_and_no_wall_deposition_reviewed": request.recession_only_and_no_wall_deposition_reviewed,
        "axisymmetric_uniform_alloy_density_mapping_reviewed": request.axisymmetric_uniform_alloy_density_mapping_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in review_fields.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    geometry_request = source_request.geometry
    geometry_result = evaluate_wet_co2_cylindrical_scale_geometry_history(geometry_request)
    if geometry_result.status != "computed":
        return Calculation(status=geometry_result.status, values=base | {
            "reason": "caller_geometry_history_not_computed",
            "geometry_status": geometry_result.status,
        })
    source_history = source_values.get("history")
    intervals = source_values.get("interval_ledger")
    knots = source_request.knots
    if not isinstance(source_history, list) or len(source_history) != len(knots):
        return Calculation(status="needs_data", values=base | {"reason": "spatial_result_exact_knot_history_missing"})
    if not isinstance(intervals, list) or len(intervals) != len(knots) - 1:
        return Calculation(status="needs_data", values=base | {"reason": "spatial_result_interval_extents_missing"})
    if len(geometry_result.values.get("history", [])) != len(knots):
        return Calculation(status="out_of_scope", values=base | {"reason": "source_geometry_knot_alignment_failed"})
    initial_geometry_radius = geometry_result.values["history"][0]["bore_radius_m"]
    if abs(initial_geometry_radius - geometry_request.initial_inner_radius_m) > request.maximum_radius_geometry_residual_m:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "initial_geometry_is_not_the_declared_unrecessed_radius",
            "declared_initial_radius_m": geometry_request.initial_inner_radius_m,
            "geometry_initial_radius_m": initial_geometry_radius,
        })

    species = {row.species_id: row for row in source_request.species}
    wall_element_ids = {row.element_id for row in source_request.wall_elements}
    atomic_weights = {row.element_id: row.atomic_molar_mass_kg_mol for row in source_request.wall_elements}
    if not wall_element_ids or not math.isclose(
        math.fsum(row.alloy_mass_fraction for row in source_request.wall_elements), 1.0,
        rel_tol=1e-10, abs_tol=1e-10,
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "wall_alloy_element_mapping_is_incomplete",
        })

    reaction_maps = []
    for knot in knots:
        mapping = {}
        for reaction in knot.reactions:
            element_yield = {element: 0.0 for element in wall_element_ids}
            for sid, stoich in reaction.stoichiometric_species_coefficients.items():
                if sid not in species:
                    return Calculation(status="out_of_scope", values=base | {
                        "reason": "reaction_species_mapping_missing", "species_id": sid,
                    })
                for element in wall_element_ids:
                    element_yield[element] += stoich * species[sid].elemental_composition.get(element, 0.0)
            if any(not math.isfinite(value) or value < -1e-12 for value in element_yield.values()):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "reaction_mapping_contains_wall_element_deposition_or_nonfinite_yield",
                    "reaction_id": reaction.reaction_id,
                    "element_release_mol_per_extent": element_yield,
                })
            mapping[reaction.reaction_id] = element_yield
        if not any(value > 0.0 for yields in mapping.values() for value in yields.values()):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "exact_knot_has_no_mapped_wall_dissolution_branch",
                "time_s": knot.time_s,
            })
        reaction_maps.append(mapping)

    initial_radius = geometry_request.initial_inner_radius_m
    outer_radius = geometry_request.outer_radius_m
    density = source_request.wall_density_kg_m3
    cumulative_release = {element: 0.0 for element in wall_element_ids}
    radius_history = [{
        "time_s": knots[0].time_s,
        "bore_radius_m": initial_radius,
        "wall_recession_m": 0.0,
        "cumulative_wall_element_release_mol_m": dict(cumulative_release),
        "geometry_radius_m": initial_geometry_radius,
        "geometry_radius_residual_m": initial_geometry_radius - initial_radius,
    }]
    interval_ledger = []
    for i, interval in enumerate(intervals):
        try:
            extents = interval["reaction_extent_mol_m"]
            if set(extents) != set(reaction_maps[i]):
                raise ValueError("interval reaction extent IDs differ from exact left-knot BV branches")
            increment = {element: 0.0 for element in wall_element_ids}
            for reaction_id, extent in extents.items():
                if not math.isfinite(extent):
                    raise ValueError("nonfinite reaction extent is outside recession-only mapping")
                yields = reaction_maps[i][reaction_id]
                if extent < 0.0 and any(value > 1e-12 for value in yields.values()):
                    raise ValueError("reverse alloy-dissolution extent implies wall deposition, which is unsupported")
                for element, yield_per_extent in reaction_maps[i][reaction_id].items():
                    increment[element] += yield_per_extent * max(0.0, extent)
            if any(not math.isfinite(value) or value < 0.0 for value in increment.values()):
                raise ValueError("wall-element release increment must be finite and nonnegative")
            for element, value in increment.items():
                cumulative_release[element] += value
            released_mass_per_length = math.fsum(
                cumulative_release[element] * atomic_weights[element] for element in wall_element_ids
            )
            area_change_m2_per_m = released_mass_per_length / density
            radius_squared = initial_radius**2 + area_change_m2_per_m / math.pi
            radius = math.sqrt(radius_squared)
            if not math.isfinite(radius) or radius < initial_radius:
                raise ArithmeticError("computed bore radius is nonfinite or below the initial radius")
            if radius >= outer_radius:
                raise ValueError("recession consumes the complete declared wall thickness")
            geom_knot = geometry_result.values["history"][i + 1]
            expected_radius = geom_knot["bore_radius_m"]
            residual = radius - expected_radius
            if not math.isfinite(residual) or abs(residual) > request.maximum_radius_geometry_residual_m:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "BV_release_derived_radius_disagrees_with_supplied_geometry_history",
                    "failed_interval_index": i,
                    "derived_bore_radius_m": radius,
                    "supplied_geometry_radius_m": expected_radius,
                    "radius_residual_m": residual,
                    "history_prefix": radius_history,
                })
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "wall_release_to_radius_mapping_failed_closed",
                "failed_interval_index": i,
                "detail": str(error),
                "history_prefix": radius_history,
            })
        radius_history.append({
            "time_s": knots[i + 1].time_s,
            "bore_radius_m": radius,
            "wall_recession_m": radius - initial_radius,
            "cumulative_wall_element_release_mol_m": dict(cumulative_release),
            "geometry_radius_m": expected_radius,
            "geometry_radius_residual_m": residual,
        })
        interval_ledger.append({
            "start_time_s": knots[i].time_s,
            "end_time_s": knots[i + 1].time_s,
            "wall_element_release_increment_mol_m": increment,
            "cumulative_released_mass_kg_m": released_mass_per_length,
            "annular_area_removed_m2_per_m": area_change_m2_per_m,
        })
    return Calculation(status="computed", values=base | {
        "history": radius_history,
        "interval_ledger": interval_ledger,
        "maximum_absolute_radius_geometry_residual_m": max(
            abs(row["geometry_radius_residual_m"]) for row in radius_history
        ),
        "coupling_scope": "exact_knot_one_way_recession_mapping_for_spatial_result_replay",
        "qualification": "not an iterative moving-boundary electrochemical solver or design-life qualification",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalBVWallRecession,
        evaluator=evaluate_wet_co2_cylindrical_bv_wall_recession,
        units={
            "history[].time_s": "s",
            "history[].bore_radius_m": "m",
            "history[].wall_recession_m": "m",
            "history[].cumulative_wall_element_release_mol_m": "mol/m",
            "interval_ledger[].wall_element_release_increment_mol_m": "mol/m",
            "interval_ledger[].cumulative_released_mass_kg_m": "kg/m",
            "interval_ledger[].annular_area_removed_m2_per_m": "m",
        },
        assumptions=(
            "Integrated reaction extents and explicit aqueous elemental stoichiometry determine the alloy-element release per unit axial length.",
            "A uniform axisymmetric alloy with fixed caller density is mapped to bore radius by exact annular volume conservation at aligned knots.",
            "The mapping supports recession only and must agree with the separately supplied geometry history within a caller tolerance.",
            "The result replays one spatial mixed-potential calculation; it does not iterate electrochemistry on the newly generated geometry.",
        ),
        source_ids=(SOURCE_ID, "caller_calibrated_butler_volmer_reaction_set", "caller_wet_co2_initial_cylindrical_pipe_geometry"),
        qualification="user_model",
    ),)
