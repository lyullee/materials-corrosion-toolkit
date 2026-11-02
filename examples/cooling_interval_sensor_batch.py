"""Synthetic example of cooling-interval evaluation for multiple sensors."""

from matintegrity.models.thermohistory import (
    CoolingIntervalSensorBatch,
    CoolingIntervalSensorBranch,
    CoolingIntervalSensorTrace,
    cooling_interval_sensor_batch,
)


request = CoolingIntervalSensorBatch(
    time_s=(0, 2, 4, 6, 8),
    sensor_traces=(
        CoolingIntervalSensorTrace(
            sensor_id="tc-a",
            location_id="weld-centerline",
            temperature_K=(900, 750, 600, 450, 300),
        ),
        CoolingIntervalSensorTrace(
            sensor_id="tc-b",
            location_id="heat-affected-zone",
            temperature_K=(850, 700, 550, 400, 280),
        ),
    ),
    branches=(
        CoolingIntervalSensorBranch(
            branch_id="centerline-range",
            sensor_id="tc-a",
            upper_temperature_K=800,
            lower_temperature_K=500,
        ),
        CoolingIntervalSensorBranch(
            branch_id="haz-range",
            sensor_id="tc-b",
            upper_temperature_K=750,
            lower_temperature_K=450,
        ),
    ),
)

result = cooling_interval_sensor_batch(request)
print(result.model_dump_json(indent=2))
