"""Synthetic transient gas-mixture history handoff to CoolProp request records."""

from matintegrity.adapters import (
    co2_mixture_fugacity_requests_from_history,
    read_co2_mixture_history_csv,
)
from matintegrity.contracts import Evidence


csv_bytes = (
    "sample_id,time_s,pressure_abs_Pa,temperature_K,valid,H2,CO2,CH4\n"
    "sample-0,0,200000,310,true,0.80,0.10,0.10\n"
    "sample-1,1,210000,312,true,0.78,0.12,0.10\n"
    "sample-invalid,2,,,false,0.70,,0.10\n"
).encode("utf-8")

history = read_co2_mixture_history_csv(
    csv_bytes,
    history_id="synthetic-psa-history",
    asset_id="synthetic-asset",
    location_id="synthetic-product-header",
    stream_id="synthetic-product",
    clock_id="synthetic-cycle-clock",
    origin="model_prediction",
    case_id="synthetic-case", case_input_digest="1" * 64,
    solver_revision="synthetic-psa-revision", sample_id_column="sample_id",
    time_seconds_column="time_s", absolute_pressure_pa_column="pressure_abs_Pa",
    temperature_kelvin_column="temperature_K", validity_column="valid",
    component_columns={"Hydrogen": "H2", "CarbonDioxide": "CO2", "Methane": "CH4"},
)

batch = co2_mixture_fugacity_requests_from_history(
    history,
    backend="HEOS",
    composition_review_id="synthetic-review",
    composition_reviewed=True,
    mixture_eos_applicability_reviewed=True,
    single_phase_gas_or_supercritical_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-psa-export",
        origin="synthetic",
        citation="Synthetic software-interface example only",
        license_id="CC0-1.0",
    ),),
)

print(batch)
