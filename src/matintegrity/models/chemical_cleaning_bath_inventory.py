"""Discrete well-mixed chemical-cleaning bath component inventory bookkeeping."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

MODEL_ID = "fabrication.chemical_cleaning_bath_component_inventory"
SOURCE_ID = "caller_declared_well_mixed_solution_component_inventory_balance"


class BathComponentMass(Contract):
    component_id: str = Field(min_length=1)
    mass_kg: Nonnegative


class ChemicalCleaningBathEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    time_s: Nonnegative
    added_liquid_volume_m3: Nonnegative = 0.0
    added_components: tuple[BathComponentMass, ...] = ()
    withdrawn_liquid_volume_m3: Nonnegative = 0.0
    caller_supplied_component_consumption: tuple[BathComponentMass, ...] = ()
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_event(self):
        if self.sequence_position < 1:
            raise ValueError("event sequence positions start at one")
        for name, terms in (
            ("added component", self.added_components),
            ("consumed component", self.caller_supplied_component_consumption),
        ):
            identifiers = [term.component_id for term in terms]
            if len(identifiers) != len(set(identifiers)):
                raise ValueError(f"{name} IDs must be unique within an event")
        if (
            self.added_liquid_volume_m3 == 0
            and self.withdrawn_liquid_volume_m3 == 0
            and not self.added_components
            and not self.caller_supplied_component_consumption
        ):
            raise ValueError("an event must contain at least one inventory operation")
        return self


class ChemicalCleaningBathHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    initial_liquid_volume_m3: Positive
    initial_components: tuple[BathComponentMass, ...] = Field(min_length=1)
    initial_evidence: tuple[Evidence, ...] = Field(min_length=1)
    events: tuple[ChemicalCleaningBathEvent, ...] = ()
    component_identity_reviewed: bool
    event_order_and_volume_basis_reviewed: bool
    consumption_terms_reviewed: bool

    @model_validator(mode="after")
    def ordered_and_unique(self):
        initial_ids = [term.component_id for term in self.initial_components]
        if len(initial_ids) != len(set(initial_ids)):
            raise ValueError("initial component IDs must be unique")
        event_ids = [event.event_id for event in self.events]
        positions = [event.sequence_position for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event IDs must be unique")
        if positions != sorted(positions) or len(positions) != len(set(positions)):
            raise ValueError("events must be listed in strictly increasing sequence order")
        if any(b.time_s < a.time_s for a, b in zip(self.events, self.events[1:], strict=False)):
            raise ValueError("event times must not move backward")
        known = set(initial_ids)
        for event in self.events:
            referenced = {item.component_id for item in event.added_components}
            referenced.update(item.component_id for item in event.caller_supplied_component_consumption)
            if not referenced <= known:
                raise ValueError("event components must be declared in the initial component basis")
        return self


def chemical_cleaning_bath_component_inventory(x: ChemicalCleaningBathHistory) -> Calculation:
    """Apply caller-declared additions, mixed withdrawals, and component demands in order."""
    missing_reviews = [
        name
        for name, reviewed in (
            ("component_identity", x.component_identity_reviewed),
            ("event_order_and_volume_basis", x.event_order_and_volume_basis_reviewed),
            ("consumption_terms", x.consumption_terms_reviewed),
        )
        if not reviewed
    ]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={"history_id": x.history_id, "missing_reviews": missing_reviews},
            notes=(
                "Inventory results are withheld until the component, event, and consumption bases are reviewed.",
            ),
        )

    component_mass = {term.component_id: term.mass_kg for term in x.initial_components}
    initial_component_mass = component_mass.copy()
    liquid_volume = x.initial_liquid_volume_m3
    event_rows = []
    for event in x.events:
        # Operation order is explicit: additions, perfectly mixed liquid draw, then
        # caller-supplied species consumption at the remaining endpoint inventory.
        liquid_volume += event.added_liquid_volume_m3
        for term in event.added_components:
            component_mass[term.component_id] += term.mass_kg
        if not math.isfinite(liquid_volume) or not all(
            math.isfinite(value) for value in component_mass.values()
        ):
            return Calculation(
                status="out_of_scope",
                values={"history_id": x.history_id, "failed_event_id": event.event_id},
                notes=("Added liquid or component inventory exceeds finite numeric support.",),
            )

        if event.withdrawn_liquid_volume_m3 > liquid_volume:
            return Calculation(
                status="needs_data",
                values={
                    "history_id": x.history_id,
                    "failed_event_id": event.event_id,
                    "failure": "withdrawal_exceeds_available_liquid_volume",
                    "liquid_volume_before_withdrawal_m3": liquid_volume,
                    "requested_withdrawal_m3": event.withdrawn_liquid_volume_m3,
                    "completed_event_ids": [row["event_id"] for row in event_rows],
                },
                notes=("No later event is evaluated after an inventory shortfall.",),
            )

        withdrawn_volume = event.withdrawn_liquid_volume_m3
        if withdrawn_volume:
            draw_fraction = withdrawn_volume / liquid_volume
            withdrawn_mass = {key: value * draw_fraction for key, value in component_mass.items()}
            for key, value in withdrawn_mass.items():
                component_mass[key] -= value
            liquid_volume -= withdrawn_volume
        else:
            withdrawn_mass = {key: 0.0 for key in component_mass}

        shortage = []
        for term in event.caller_supplied_component_consumption:
            available = component_mass[term.component_id]
            if term.mass_kg > available:
                shortage.append(
                    {
                        "component_id": term.component_id,
                        "available_mass_kg": available,
                        "requested_consumption_kg": term.mass_kg,
                    }
                )
        if shortage:
            return Calculation(
                status="needs_data",
                values={
                    "history_id": x.history_id,
                    "failed_event_id": event.event_id,
                    "failure": "component_consumption_exceeds_available_inventory",
                    "shortages": shortage,
                    "completed_event_ids": [row["event_id"] for row in event_rows],
                },
                notes=("No later event is evaluated after an inventory shortfall.",),
            )

        for term in event.caller_supplied_component_consumption:
            component_mass[term.component_id] -= term.mass_kg

        if liquid_volume == 0 and any(mass > 0 for mass in component_mass.values()):
            return Calculation(
                status="needs_data",
                values={
                    "history_id": x.history_id,
                    "failed_event_id": event.event_id,
                    "failure": "positive_component_inventory_at_zero_liquid_volume",
                    "component_mass_kg": component_mass,
                    "completed_event_ids": [row["event_id"] for row in event_rows],
                },
                notes=(
                    "A dissolved concentration is undefined for positive component mass at zero liquid volume.",
                ),
            )

        concentrations = (
            {key: value / liquid_volume for key, value in component_mass.items()}
            if liquid_volume > 0
            else {key: None for key in component_mass}
        )
        if not all(value is None or math.isfinite(value) for value in concentrations.values()):
            return Calculation(
                status="out_of_scope",
                values={"history_id": x.history_id, "failed_event_id": event.event_id},
                notes=("Component concentration exceeds finite numeric support.",),
            )
        event_rows.append(
            {
                "event_id": event.event_id,
                "sequence_position": event.sequence_position,
                "time_s": event.time_s,
                "liquid_volume_m3": liquid_volume,
                "component_mass_kg": component_mass.copy(),
                "component_concentration_kg_m3": concentrations,
                "component_mass_removed_by_well_mixed_draw_kg": withdrawn_mass,
                "caller_supplied_component_consumption_kg": {
                    term.component_id: term.mass_kg for term in event.caller_supplied_component_consumption
                },
            }
        )

    final_concentration = (
        {key: value / liquid_volume for key, value in component_mass.items()}
        if liquid_volume > 0
        else {key: None for key in component_mass}
    )
    if not all(value is None or math.isfinite(value) for value in final_concentration.values()):
        return Calculation(
            status="out_of_scope",
            values={"history_id": x.history_id},
            notes=("Component concentration exceeds finite numeric support.",),
        )
    return Calculation(
        values={
            "history_id": x.history_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "clock_id": x.clock_id,
            "initial_liquid_volume_m3": x.initial_liquid_volume_m3,
            "initial_component_mass_kg": initial_component_mass,
            "event_count": len(event_rows),
            "event_history": event_rows,
            "final_liquid_volume_m3": liquid_volume,
            "final_component_mass_kg": component_mass,
            "final_component_concentration_kg_m3": final_concentration,
            "calculation_source_id": SOURCE_ID,
        },
        notes=(
            "Each liquid withdrawal is treated as perfectly mixed at the composition immediately before withdrawal.",
            "Caller-supplied component consumption is subtracted after each event withdrawal; it does not predict reaction chemistry.",
            "No precipitation, gas transfer, density change, temperature dependence, rinse effectiveness, or cleaning acceptance is inferred.",
            "Concentrations are undefined at zero liquid volume and are returned as null, not measured zero concentration.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("cleaning bath asset and location must match the run context")

    return [
        ModelSpec(
            MODEL_ID,
            ChemicalCleaningBathHistory,
            chemical_cleaning_bath_component_inventory,
            {
                "history_id": "1",
                "event_count": "1",
                "event_history": "1",
                "final_liquid_volume_m3": "m^3",
                "final_component_mass_kg": "kg",
                "final_component_concentration_kg_m3": "kg/m^3",
            },
            (
                "Component masses are caller-declared and expressed on one consistent component identity basis.",
                "The vessel is spatially uniform and each liquid withdrawal removes components in proportion to the current mixed concentration.",
                "Operation order within an event is liquid/component additions, mixed liquid withdrawal, then caller-declared component consumption.",
            ),
            (SOURCE_ID,),
            version="1.0.1",
            context_validator=same_identity,
        )
    ]
