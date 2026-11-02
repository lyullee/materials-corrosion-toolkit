"""Digest-pinned integration of mixed-potential species fluxes between declared knots."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Positive, canonical_digest
from ..registry import ModelSpec


class CreviceElectrochemicalInventoryIntegration(Contract):
    schema_version: Literal["matintegrity.crevice_electrochemical_inventory_integration.v1"] = (
        "matintegrity.crevice_electrochemical_inventory_integration.v1"
    )
    assessment_id: str = Field(min_length=1)
    mixed_potential_result: AssessmentResult
    mixed_potential_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_area_m2: Positive
    piecewise_linear_flux_between_knots_reviewed: bool
    constant_reference_area_reviewed: bool
    stoichiometric_inward_sign_convention_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_source_result(self):
        result = self.mixed_potential_result
        if result.model_id != "electrochemistry.crevice_mixed_potential_history" or result.status != "computed":
            raise ValueError("a computed crevice mixed-potential history is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("mixed-potential assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.mixed_potential_result_sha256:
            raise ValueError("mixed-potential result digest mismatch")
        history = result.values.get("mixed_potential_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("mixed-potential result must contain at least two knots")
        if result.values.get("mixed_potential_history_sha256") != canonical_digest(history):
            raise ValueError("mixed-potential history digest mismatch")
        if result.values.get("reference_area_m2") != self.reference_area_m2:
            raise ValueError("integration area must equal the mixed-potential history area basis")
        times = []
        for index, row in enumerate(history):
            if not isinstance(row, dict):
                raise ValueError("mixed-potential knots must be objects")
            time_s = row.get("time_s")
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s):
                raise ValueError("each knot requires a finite time_s")
            times.append(float(time_s))
            branches = row.get("reaction_responses")
            if not isinstance(branches, list) or not branches:
                raise ValueError("each knot requires reaction responses")
            for branch in branches:
                if not isinstance(branch, dict) or not isinstance(branch.get("reaction_id"), str) or not branch["reaction_id"].strip():
                    raise ValueError("each reaction response requires a nonempty reaction_id")
                fluxes = branch.get("reference_area_species_flux_mol_m2_s")
                if not isinstance(fluxes, dict) or not fluxes:
                    raise ValueError("each branch requires species fluxes on the reference-area basis")
                for species, flux in fluxes.items():
                    if not isinstance(species, str) or not species.strip() or isinstance(flux, bool) or not isinstance(flux, (int, float)) or not math.isfinite(flux):
                        raise ValueError("species flux keys and values must be finite and valid")
            if index and times[-1] <= times[-2]:
                raise ValueError("mixed-potential time knots must strictly increase")
        first_ids = tuple(row["reaction_id"] for row in history[0]["reaction_responses"])
        if len(first_ids) != len(set(first_ids)):
            raise ValueError("reaction IDs must be unique")
        first_species = {
            row["reaction_id"]: tuple(sorted(row["reference_area_species_flux_mol_m2_s"]))
            for row in history[0]["reaction_responses"]
        }
        for row in history[1:]:
            branches = row["reaction_responses"]
            if tuple(branch.get("reaction_id") for branch in branches) != first_ids:
                raise ValueError("reaction identity and ordering must remain stable across knots")
            for branch in branches:
                species = tuple(sorted(branch["reference_area_species_flux_mol_m2_s"]))
                if species != first_species[branch["reaction_id"]]:
                    raise ValueError("species flux mapping must remain stable across knots")
        return self


def _positive_linear_integral(start: float, end: float, duration: float) -> float:
    """Exact integral of max(f, 0) for the linear segment joining endpoint rates."""
    if start >= 0.0 and end >= 0.0:
        return duration * (start + end) / 2.0
    if start <= 0.0 and end <= 0.0:
        return 0.0
    if start > 0.0:
        positive_fraction = start / (start - end)
        return duration * start * positive_fraction / 2.0
    positive_fraction = end / (end - start)
    return duration * end * positive_fraction / 2.0


def integrate_crevice_electrochemical_inventory(
    x: CreviceElectrochemicalInventoryIntegration,
) -> Calculation:
    result = x.mixed_potential_result
    history = result.values["mixed_potential_history"]
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": result.values["asset_id"],
        "location_id": result.values["location_id"],
        "physical_scope_id": result.values["physical_scope_id"],
        "clock_id": result.values["clock_id"],
        "reference_area_m2": x.reference_area_m2,
        "mixed_potential_result_sha256": x.mixed_potential_result_sha256,
        "mixed_potential_history_sha256": result.values["mixed_potential_history_sha256"],
        "integration_method": "exact_piecewise_linear_flux_integral_between_declared_knots",
        "area_basis": "constant caller reference area from upstream mixed-potential result",
    }
    reviews = {
        "piecewise_linear_flux_between_knots_reviewed": x.piecewise_linear_flux_between_knots_reviewed,
        "constant_reference_area_reviewed": x.constant_reference_area_reviewed,
        "stoichiometric_inward_sign_convention_reviewed": x.stoichiometric_inward_sign_convention_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    area = x.reference_area_m2
    cumulative: dict[str, dict[str, dict[str, float]]] = {}
    intervals = []
    for left, right in zip(history, history[1:]):
        duration = right["time_s"] - left["time_s"]
        branch_rows = []
        for left_branch, right_branch in zip(
            left["reaction_responses"], right["reaction_responses"], strict=True
        ):
            reaction_id = left_branch["reaction_id"]
            species_rows = []
            cumulative.setdefault(reaction_id, {})
            left_fluxes = left_branch["reference_area_species_flux_mol_m2_s"]
            right_fluxes = right_branch["reference_area_species_flux_mol_m2_s"]
            for species in sorted(left_fluxes):
                start, end = left_fluxes[species], right_fluxes[species]
                signed = duration * (start + end) / 2.0 * area
                inward = _positive_linear_integral(start, end, duration) * area
                outward = _positive_linear_integral(-start, -end, duration) * area
                state = cumulative[reaction_id].setdefault(species, {"signed_mol": 0.0, "inward_mol": 0.0, "outward_mol": 0.0})
                state["signed_mol"] += signed
                state["inward_mol"] += inward
                state["outward_mol"] += outward
                if not all(math.isfinite(value) for value in (signed, inward, outward, *state.values())):
                    return Calculation(status="out_of_scope", values=base | {
                        "failed_interval_start_s": left["time_s"],
                        "failed_interval_end_s": right["time_s"],
                        "failure_reason": "integrated_species_inventory_exceeds_numeric_range",
                        "computed_prefix": intervals,
                    })
                species_rows.append({
                    "species_id": species,
                    "signed_net_transfer_mol": signed,
                    "inward_transfer_mol": inward,
                    "outward_transfer_mol": outward,
                    "cumulative_signed_net_transfer_mol": state["signed_mol"],
                    "cumulative_inward_transfer_mol": state["inward_mol"],
                    "cumulative_outward_transfer_mol": state["outward_mol"],
                })
            branch_rows.append({"reaction_id": reaction_id, "species_transfer": species_rows})
        intervals.append({
            "start_time_s": left["time_s"],
            "end_time_s": right["time_s"],
            "start_temperature_K": left["temperature_K"],
            "end_temperature_K": right["temperature_K"],
            "reaction_species_transfer": branch_rows,
        })
    return Calculation(values=base | {
        "interval_inventory_transfer": intervals,
        "cumulative_inventory_transfer_by_reaction": cumulative,
        "inventory_transfer_sha256": canonical_digest({"intervals": intervals, "cumulative": cumulative}),
    }, notes=(
        "Signed branch species flux is integrated exactly for the caller-reviewed linear reconstruction between supplied knots; positive values follow the upstream inward-species sign convention.",
        "The result is a surface-area-scaled transfer amount, not a concentration, bulk inventory, metal-loss depth, corrosion rate, phase state or acceptance finding. Transport volume, stoichiometric phase selection and subsequent material-loss interpretation remain the receiving module's responsibility.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.crevice_electrochemical_inventory_transfer",
        CreviceElectrochemicalInventoryIntegration,
        integrate_crevice_electrochemical_inventory,
        {
            "reference_area_m2": "m2",
            "interval_inventory_transfer[].start_time_s": "s",
            "interval_inventory_transfer[].end_time_s": "s",
            "interval_inventory_transfer[].start_temperature_K": "K",
            "interval_inventory_transfer[].end_temperature_K": "K",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].signed_net_transfer_mol": "mol",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].inward_transfer_mol": "mol",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].outward_transfer_mol": "mol",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_signed_net_transfer_mol": "mol",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_inward_transfer_mol": "mol",
            "interval_inventory_transfer[].reaction_species_transfer[].species_transfer[].cumulative_outward_transfer_mol": "mol",
            "cumulative_inventory_transfer_by_reaction.*.*.signed_mol": "mol",
            "cumulative_inventory_transfer_by_reaction.*.*.inward_mol": "mol",
            "cumulative_inventory_transfer_by_reaction.*.*.outward_mol": "mol",
        },
        (
            "Only a computed digest-pinned crevice mixed-potential result is accepted, and the exact upstream reference-area basis is reused.",
            "Between adjacent declared knots, each species flux is reconstructed as a straight line and integrated exactly; this policy requires explicit caller review and does not establish the true within-interval kinetics.",
            "The output is an area-scaled species transfer ledger and is not bulk concentration, metal loss, corrosion rate, protection, risk or acceptance.",
        ),
        ("crevice_mixed_potential_species_flux_interval_inventory_transfer",),
        qualification="user_model",
    )]
