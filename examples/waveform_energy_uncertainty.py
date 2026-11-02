"""Synthetic example; values are illustrative and are not welding procedure limits."""

from matintegrity.contracts import Evidence
from matintegrity.models.fabrication import WaveformEnergy
from matintegrity.waveform_energy_uncertainty import (
    WaveformEnergyUncertainty,
    evaluate_waveform_energy_uncertainty,
    waveform_energy_covariance_digest,
)

waveform = WaveformEnergy(
    time_s=[0.0, 0.1, 0.2],
    voltage_V=[20.0, 22.0, 21.0],
    current_A=[100.0, 110.0, 105.0],
    efficiency=0.8,
    travel_distance_m=0.004,
)
order = (
    "voltage_V[0]", "voltage_V[1]", "voltage_V[2]",
    "current_A[0]", "current_A[1]", "current_A[2]",
    "efficiency", "travel_distance_m",
)
units = ("V", "V", "V", "A", "A", "A", "1", "m")
variances = (0.04, 0.04, 0.04, 1.0, 1.0, 1.0, 0.0004, 1e-8)
covariance = tuple(
    tuple(variances[i] if i == j else 0.0 for j in range(len(order)))
    for i in range(len(order))
)
source_id = "synthetic_waveform_covariance"
revision = "example-v1"
record_id = "example-record"
license_id = "CC0-1.0"
digest = waveform_energy_covariance_digest(
    waveform, order, units, covariance, source_id, revision, record_id
)
request = WaveformEnergyUncertainty(
    assessment_id="synthetic-waveform-uncertainty",
    waveform=waveform,
    covariance_coordinate_order=order,
    covariance_coordinate_unit_tokens=units,
    input_covariance=covariance,
    covariance_source_id=source_id,
    covariance_provider_revision=revision,
    covariance_record_id=record_id,
    covariance_sha256=digest,
    covariance_usage_license_id=license_id,
    evidence=(Evidence(
        source_id=source_id, origin="synthetic", citation="Synthetic diagonal covariance for example use",
        license_id=license_id, sha256=digest,
    ),),
    covariance_order_and_units_reviewed=True,
    waveform_clock_treated_exact_reviewed=True,
    first_order_linearization_and_local_support_reviewed=True,
    computational_use_authorized=True,
)
print(evaluate_waveform_energy_uncertainty(request).model_dump(mode="json"))
