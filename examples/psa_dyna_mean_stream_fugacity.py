"""Synthetic PSA-Dyna cycle-mean stream handoff to a CoolProp request."""

from matintegrity.adapters import co2_mixture_fugacity_requests_from_psa_dyna_mean_stream
from matintegrity.contracts import Evidence


report = {
    "schema": "dynamic-psa-mean-stream/v1",
    "case": {"case_id": "synthetic-case", "sha256": "1" * 64},
    "result": {"sha256": "2" * 64},
    "upstream_gate_observations": {"source_code_zip_sha256": "3" * 64},
    "dwsim_input_payload": {
        "schema": "dynamic-psa-dwsim-mean-stream-input/v1",
        "status": "prepared_closed_pending_qualification",
        "components": ["H2", "CO2", "CH4"],
        "streams": {
            "PRODUCT": {
                "molar_flow_mol_s": 0.01,
                "mole_fractions": [0.80, 0.10, 0.10],
                "pressure_bar": 15.0,
                "temperature_k": 310.0,
                "enthalpy_flow_w": None,
                "state_basis": "synthetic phase-aligned cycle-mean state",
            },
        },
        "units": {
            "molar_flow": "mol/s",
            "mole_fraction": "1",
            "pressure": "bar",
            "temperature": "K",
            "enthalpy_flow": "W",
        },
        "release_flags": {"dwsim_transfer_allowed": False},
    },
}

batch = co2_mixture_fugacity_requests_from_psa_dyna_mean_stream(
    report,
    stream_ids=("PRODUCT",),
    backend="HEOS",
    composition_review_id="synthetic-mean-stream-review",
    absolute_pressure_basis_reviewed=True,
    composition_reviewed=True,
    mixture_eos_applicability_reviewed=True,
    single_phase_gas_or_supercritical_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-psa-dyna-export",
        origin="synthetic",
        citation="Synthetic interface example only",
        license_id="CC0-1.0",
    ),),
)

print(batch.model_dump(mode="json"))
