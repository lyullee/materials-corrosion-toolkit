import json

import h5py
import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.composition import ParameterProfile, WorkflowStep, run_workflow
from matintegrity.contracts import RunContext
from matintegrity.records import InspectionRecord, MaterialRecord
from matintegrity.registry import default_registry
from matintegrity.signals import (
    coqtel_electrochemistry,
    coqtel_waveform,
    inspect_coqtel_experiment,
    waveform_change,
)


def test_workflow_halts_at_noncomputed_state():
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    steps = [
        WorkflowStep(
            id="gate",
            model_id="reliability.independent_gate",
            inputs=dict(probabilities=[0.1, 0.2], gate="OR", independence_declared=False),
        ),
        WorkflowStep(id="later", model_id="fatigue.basquin", inputs={}),
    ]
    result = run_workflow(registry, steps, context)
    assert result["status"] == "needs_data" and result["halted_after"] == "gate"
    assert "later" not in result["steps"]


def test_parameter_profile_overrides_are_explicit():
    registry = default_registry()
    profile = ParameterProfile(
        profile_id="synthetic",
        model_id="fatigue.basquin",
        parameters=dict(reference_range_Pa=1e8, reference_cycles=1e6, exponent=3.0),
        source_id="synthetic",
        domain="example only",
    )
    context = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    result = profile.run(registry, {"stress_range_Pa": 2e8}, context, overrides={"exponent": 4.0})
    assert result.values["cycles_to_failure"] == 62500
    assert result.context.metadata["parameter_overrides"]["exponent"] == 4
    with pytest.raises(ValueError):
        profile.run(registry, {"stress_range_Pa": 2e8, "exponent": 4.0}, context)


def test_ec_duplicate_policy_and_unit_conversion(tmp_path):
    file = tmp_path / "sample.h5"
    with h5py.File(file, "w") as f:
        f["EC_data/EC_time"] = [1.0, 2.0, 2.0, 3.0]
        f["EC_data/EC_current"] = [0.01, 0.01, 0.01, 0.01]
        f["EC_data/EC_potential"] = [0.4, 0.4, 0.4, 0.4]
    with pytest.raises(ValueError):
        coqtel_electrochemistry(file)
    record = coqtel_electrochemistry(file, duplicate_policy="preserve_identical")
    assert record["anodic_charge_C"] == pytest.approx(1.2)
    assert record["identical_duplicate_intervals"] == 1
    with h5py.File(file, "a") as f:
        f["EC_data/EC_current"][2] = 0.02
    with pytest.raises(ValueError):
        coqtel_electrochemistry(file, duplicate_policy="preserve_identical")


def test_hdf_channel_axis_mapping(tmp_path):
    file = tmp_path / "wave.h5"
    values = np.vstack([np.arange(10) * 1e-7, np.ones(10), np.full(10, 2), np.full(10, 3), np.full(10, 4)])
    with h5py.File(file, "w") as f:
        signal = f.create_group("State_1/200kHz_5cycles")
        signal.attrs["fs"] = [10_000_000.0]
        signal.attrs["f0"] = [200_000.0]
        signal.attrs["nb_cycles"] = [5.0]
        signal["Actionneur2/measured_data_rep_1.mat"] = values
    wave = coqtel_waveform(file, state=1, actuator=2, sensor=4)
    assert np.all(wave["sensor_V"] == 4)
    assert wave["receiver_row_order"] == (1, 3, 4)
    assert wave["source_is_pinned"] is False
    assert wave["pit_dimension_status"] == "not_supplied_per_state"
    assert waveform_change(wave, wave)["relative_waveform_change"] == 0


def test_complete_coqtel_inventory_preserves_observation_boundaries(tmp_path):
    file = tmp_path / "synthetic-coqtel.h5"
    time_axis = np.arange(2000) / 2_000_000.0
    matrix = np.vstack([time_axis, np.ones(2000), np.full((3, 2000), 0.5)])
    with h5py.File(file, "w") as hdf:
        hdf.attrs["PZT_info_geo"] = np.zeros((2, 4))
        hdf["EC_data/EC_time"] = [1.0, 2.0]
        hdf["EC_data/EC_current"] = [0.01, 0.02]
        hdf["EC_data/EC_potential"] = [0.15, 0.40]
        hdf["image"] = np.zeros((3, 4, 5), dtype=np.uint8)
        for state in (1, 2):
            signal = hdf.create_group(f"State_{state}/200kHz_5cycles")
            signal.attrs["fs"] = [2_000_000.0]
            signal.attrs["f0"] = [200_000.0]
            signal.attrs["nb_cycles"] = [5.0]
            for actuator in range(1, 5):
                signal[f"Actionneur{actuator}/measured_data_rep_1.mat"] = matrix
    report = inspect_coqtel_experiment(file, require_pinned_hash=False)
    assert report["state_count"] == 2
    assert report["waveform_records"] == 8
    assert report["observational_unit"] == "one plate per HDF5 experiment"
    assert report["per_state_pit_dimension_observations"] == 0
    assert report["root_image_state_link_status"] == "not_supplied"
    with pytest.raises(ValueError, match="pinned"):
        inspect_coqtel_experiment(file)


def test_record_contracts_keep_unknown_and_reject_inconsistent_identity():
    material = MaterialRecord(
        material_id="test",
        specification="user-defined",
        grade="test",
        product_form="plate",
        condition="synthetic",
        composition_mass_fraction={"Fe": 0.99, "C": 0.01},
    )
    assert material.heat_id is None
    with pytest.raises(ValidationError):
        MaterialRecord(**dict(material.model_dump(), composition_mass_fraction={"Fe": 1.0, "C": 0.01}))
    record = dict(
        inspection_id="i",
        asset_id="a",
        location_id="b",
        measured_at="2026-10-26T00:00:00+09:00",
        method="UT",
        procedure_id="synthetic",
        outcome="no_indication",
        flaws=[dict(id="f", asset_id="a", location_id="b", kind="crack", depth_m=0.001)],
    )
    with pytest.raises(ValidationError):
        InspectionRecord.model_validate_json(json.dumps(record))
