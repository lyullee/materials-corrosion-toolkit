"""Corrosion-waveform ingestion with provider-specific axes and units made explicit."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

COQTEL_DATASET_ID = "coqtel"
COQTEL_ARTICLE_DOI = "10.1016/j.dib.2025.111393"
COQTEL_FILES = {
    "Essai_Corrosion1.h5": {
        "sha256": "8c012846e1895adbd9cd93ea20ed22f6a1780670d133cedaeb766f19f2f14715",
        "experiment_id": "coqtel-experiment-1",
        "specimen_id": "coqtel-316l-plate-1",
        "reported_anomaly_state_range": None,
    },
    "Essai_Corrosion2.h5": {
        "sha256": "8eb128fff05d21aa0d4bdf685c79ae357f60287abfa984c917ff97d85e127d68",
        "experiment_id": "coqtel-experiment-2",
        "specimen_id": "coqtel-316l-plate-2",
        "reported_anomaly_state_range": (30, 100),
    },
}


def _sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _coqtel_identity(path: Path, *, require_pinned_hash: bool) -> dict:
    digest = _sha256(path)
    reviewed = COQTEL_FILES.get(path.name)
    source_is_pinned = reviewed is not None and digest == reviewed["sha256"]
    if require_pinned_hash and not source_is_pinned:
        raise ValueError("COQTEL file name and digest do not match a pinned experiment")
    return {
        "source_sha256": digest,
        "source_is_pinned": source_is_pinned,
        "experiment_id": reviewed["experiment_id"] if source_is_pinned else "unreviewed-experiment",
        "specimen_id": reviewed["specimen_id"] if source_is_pinned else "unreviewed-specimen",
        "reported_anomaly_state_range": (
            reviewed["reported_anomaly_state_range"] if source_is_pinned else None
        ),
    }


def _state_anomaly(state: int, identity: dict) -> str:
    bounds = identity["reported_anomaly_state_range"]
    if bounds is not None and bounds[0] <= state <= bounds[1]:
        return "reported_air_bubble_interval"
    return "none_reported"


def coqtel_electrochemistry(
    path: str | Path,
    *,
    duplicate_policy: str = "reject",
    require_pinned_hash: bool = False,
) -> dict:
    import h5py

    source = Path(path)
    identity = _coqtel_identity(source, require_pinned_hash=require_pinned_hash)
    with h5py.File(source) as file:
        time = np.asarray(file["EC_data/EC_time"], float) * 60
        current = np.asarray(file["EC_data/EC_current"], float)
        potential = np.asarray(file["EC_data/EC_potential"], float)
    if len({len(time), len(current), len(potential)}) != 1 or np.any(np.diff(time) < 0):
        raise ValueError("electrochemistry observations must align on a nondecreasing clock")
    repeated = np.flatnonzero(np.diff(time) == 0)
    if duplicate_policy not in {"reject", "preserve_identical"}:
        raise ValueError("unknown duplicate timestamp policy")
    if len(repeated):
        if duplicate_policy == "reject":
            raise ValueError("duplicate EC timestamps require an explicit duplicate policy")
        if np.any(current[repeated] != current[repeated + 1]) or np.any(
            potential[repeated] != potential[repeated + 1]
        ):
            raise ValueError("same-time EC observations conflict; resolve the measurement clock first")
    if not all(np.isfinite(x).all() for x in (time, current, potential)):
        raise ValueError("nonfinite electrochemistry observations")
    state_index = np.arange(1, len(time) + 1, dtype=int)
    return dict(
        dataset_id=COQTEL_DATASET_ID,
        article_doi=COQTEL_ARTICLE_DOI,
        source_file=source.name,
        source_sha256=identity["source_sha256"],
        source_is_pinned=identity["source_is_pinned"],
        experiment_id=identity["experiment_id"],
        specimen_id=identity["specimen_id"],
        material_designation="316L" if identity["source_is_pinned"] else None,
        plate_thickness_m=0.0015 if identity["source_is_pinned"] else None,
        plate_width_m=0.080 if identity["source_is_pinned"] else None,
        plate_length_m=0.125 if identity["source_is_pinned"] else None,
        state_index=state_index,
        time_s=time,
        current_A=current,
        potential_V=potential,
        experimental_anomaly=np.asarray(
            [_state_anomaly(int(state), identity) for state in state_index], dtype=object
        ),
        signed_charge_C=float(np.trapezoid(current, time)),
        anodic_charge_C=float(np.trapezoid(np.maximum(current, 0), time)),
        source_id=COQTEL_DATASET_ID,
        duplicate_policy=duplicate_policy,
        identical_duplicate_intervals=int(len(repeated)),
        repeated_time_state_pairs=tuple(
            (int(state_index[index]), int(state_index[index + 1])) for index in repeated
        ),
        units_verified_from=f"doi:{COQTEL_ARTICLE_DOI}#data-description",
        state_alignment="EC row i corresponds to State_i",
        observational_unit="one plate per HDF5 experiment",
        pit_dimension_status="not_supplied_per_state",
        root_image_state_link_status="not_supplied",
        qualification=(
            "Electrochemical integration and state alignment only; charge and waveform state are not "
            "a measured pit radius, depth, wall loss, corrosion rate, remaining life or failure probability."
        ),
    )


def coqtel_waveform(
    path: str | Path,
    *,
    state: int,
    actuator: int,
    sensor: int,
    require_pinned_hash: bool = False,
) -> dict:
    import h5py

    if state < 1:
        raise ValueError("positive COQTEL state index required")
    if actuator not in range(1, 5) or sensor not in range(1, 5) or actuator == sensor:
        raise ValueError("distinct actuator and sensor identifiers from 1 through 4 required")
    source = Path(path)
    identity = _coqtel_identity(source, require_pinned_hash=require_pinned_hash)
    key = f"State_{state}/200kHz_5cycles/Actionneur{actuator}/measured_data_rep_1.mat"
    with h5py.File(source) as file:
        if key not in file:
            raise ValueError("requested COQTEL state or actuator is absent")
        values = np.asarray(file[key], float)
        signal_group = file[f"State_{state}/200kHz_5cycles"]
        sampling_frequency_hz = float(np.ravel(signal_group.attrs["fs"])[0])
        center_frequency_hz = float(np.ravel(signal_group.attrs["f0"])[0])
        excitation_cycles = int(np.ravel(signal_group.attrs["nb_cycles"])[0])
    if values.ndim != 2 or values.shape[0] != 5 or values.shape[1] <= 5:
        raise ValueError("unexpected HDF waveform axis layout")
    receive_index = sorted(set(range(1, 5)) - {actuator}).index(sensor) + 2
    time, drive, response = values[0], values[1], values[receive_index]
    if not np.isfinite(values).all() or np.any(np.diff(time) <= 0):
        raise ValueError("waveform time or values are invalid")
    if not np.allclose(np.diff(time), 1.0 / sampling_frequency_hz, rtol=0.0, atol=1e-15):
        raise ValueError("waveform time increments disagree with the HDF sampling frequency")
    return dict(
        time_s=time,
        actuator_V=drive,
        sensor_V=response,
        source_id=COQTEL_DATASET_ID,
        source_file=source.name,
        source_sha256=identity["source_sha256"],
        source_is_pinned=identity["source_is_pinned"],
        experiment_id=identity["experiment_id"],
        specimen_id=identity["specimen_id"],
        state=state,
        actuator_id=actuator,
        sensor_id=sensor,
        receiver_row_order=tuple(sorted(set(range(1, 5)) - {actuator})),
        sampling_frequency_Hz=sampling_frequency_hz,
        center_frequency_Hz=center_frequency_hz,
        excitation_cycles=excitation_cycles,
        experimental_anomaly=_state_anomaly(state, identity),
        amplitude_unit_status="legacy_reader_uses_volts_not_declared_by_hdf5_dataset",
        state_alignment="State_i corresponds to EC row i",
        pit_dimension_status="not_supplied_per_state",
    )


def inspect_coqtel_experiment(path: str | Path, *, require_pinned_hash: bool = True) -> dict:
    """Validate one complete pinned experiment and return only aggregate public-safe evidence."""
    import h5py

    source = Path(path)
    identity = _coqtel_identity(source, require_pinned_hash=require_pinned_hash)
    electrochemistry = coqtel_electrochemistry(
        source,
        duplicate_policy="preserve_identical",
        require_pinned_hash=require_pinned_hash,
    )
    with h5py.File(source) as file:
        states = sorted(
            (key for key in file if key.startswith("State_")),
            key=lambda key: int(key.removeprefix("State_")),
        )
        expected_states = [f"State_{index}" for index in range(1, len(states) + 1)]
        if states != expected_states or len(states) != len(electrochemistry["state_index"]):
            raise ValueError("COQTEL state names must be consecutive and align with EC rows")
        if set(file) != {"EC_data", "image", *states}:
            raise ValueError("unexpected COQTEL root object")
        geometry = np.asarray(file.attrs.get("PZT_info_geo"), float)
        if geometry.shape != (2, 4) or not np.isfinite(geometry).all():
            raise ValueError("unexpected COQTEL PZT geometry metadata")
        image = file["image"]
        if image.ndim != 3 or image.shape[0] != 3 or image.dtype != np.dtype("uint8"):
            raise ValueError("unexpected COQTEL root image layout")
        image_shape = list(image.shape)
        waveform_records = 0
        waveform_shapes = set()
        signal_definitions = set()
        for state in states:
            signal = file[f"{state}/200kHz_5cycles"]
            definition = (
                float(np.ravel(signal.attrs["f0"])[0]),
                float(np.ravel(signal.attrs["fs"])[0]),
                int(np.ravel(signal.attrs["nb_cycles"])[0]),
            )
            signal_definitions.add(definition)
            if set(signal) != {f"Actionneur{index}" for index in range(1, 5)}:
                raise ValueError("COQTEL state does not contain four actuator groups")
            for actuator in signal.values():
                if set(actuator) != {"measured_data_rep_1.mat"}:
                    raise ValueError("unexpected COQTEL actuator dataset")
                values = np.asarray(actuator["measured_data_rep_1.mat"], float)
                waveform_shapes.add(values.shape)
                if values.shape != (5, 2000) or not np.isfinite(values).all():
                    raise ValueError("invalid COQTEL waveform matrix")
                if np.any(np.diff(values[0]) <= 0):
                    raise ValueError("COQTEL waveform time decreases or repeats")
                if not np.allclose(np.diff(values[0]), 1.0 / definition[1], rtol=0.0, atol=1e-15):
                    raise ValueError("COQTEL waveform clock disagrees with sampling metadata")
                waveform_records += 1
    anomaly_states = int(
        np.count_nonzero(electrochemistry["experimental_anomaly"] == "reported_air_bubble_interval")
    )
    return {
        "dataset_id": COQTEL_DATASET_ID,
        "article_doi": COQTEL_ARTICLE_DOI,
        "source_file": source.name,
        "source_sha256": identity["source_sha256"],
        "source_is_pinned": identity["source_is_pinned"],
        "experiment_id": identity["experiment_id"],
        "specimen_id": identity["specimen_id"],
        "state_count": len(states),
        "electrochemistry_rows": len(electrochemistry["state_index"]),
        "waveform_records": waveform_records,
        "waveform_matrix_shapes": [list(shape) for shape in sorted(waveform_shapes)],
        "signal_definitions": [list(value) for value in sorted(signal_definitions)],
        "identical_duplicate_intervals": electrochemistry["identical_duplicate_intervals"],
        "reported_anomaly_state_range": identity["reported_anomaly_state_range"],
        "reported_anomaly_states": anomaly_states,
        "electrochemistry_duration_s": float(electrochemistry["time_s"][-1] - electrochemistry["time_s"][0]),
        "signed_charge_C": electrochemistry["signed_charge_C"],
        "anodic_charge_C": electrochemistry["anodic_charge_C"],
        "root_image_shape": image_shape,
        "root_image_state_link_status": "not_supplied",
        "per_state_pit_dimension_observations": 0,
        "observational_unit": "one plate per HDF5 experiment",
        "physical_specimen_independence": "two files are two specimens; states within a file are repeated",
        "qualification": electrochemistry["qualification"],
    }


def waveform_change(reference: dict, current: dict) -> dict:
    if not np.array_equal(reference["time_s"], current["time_s"]):
        raise ValueError("waveform comparison requires a common sampling clock")
    ref, signal = np.asarray(reference["sensor_V"]), np.asarray(current["sensor_V"])
    norm = float(np.linalg.norm(ref))
    if norm <= 0:
        raise ValueError("nonzero baseline waveform required")
    return dict(
        relative_waveform_change=float(np.linalg.norm(signal - ref) / norm),
        response_energy_ratio=float(np.dot(signal, signal) / np.dot(ref, ref)),
        meaning="Signal-change features; not a calibrated pit depth, POD or failure probability.",
    )
