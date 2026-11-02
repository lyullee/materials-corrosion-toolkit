"""Nonexecuted local example for the typed pressure-decay sample adapter."""

from pathlib import Path

from matintegrity.pressure_decay_leak_data import (
    PressureDecayLeakReadAuthorization,
    iter_pressure_decay_leak_samples,
)

archive = Path("data/raw/zenodo-20582921-pressure-decay/DataSet Temperatue-Pressure.xlsx")
authorization = PressureDecayLeakReadAuthorization(
    attribution="Mičian and Koňár, Zenodo DOI 10.5281/zenodo.20582921, CC BY 4.0",
    computational_use_authorized=True,
    local_only_authorized=True,
)

# Keep consumption lazy. Do not treat the gauge-pressure history as a leak rate.
for row in iter_pressure_decay_leak_samples(archive, authorization=authorization):
    print(row.series_id, row.sample_index, row.time_s, row.temperature_K, row.pressure_Pa)
