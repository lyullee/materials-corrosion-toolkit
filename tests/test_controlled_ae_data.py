from __future__ import annotations

import hashlib

import pytest

from matintegrity.controlled_ae_data import read_controlled_ae_waveform


def _waveform(tmp_path, *, bad_magic=False, bad_channel=False, bad_value=False):
    path = tmp_path / "C_A1_S09_TR_1.txt"
    samples = ["bad" if bad_value and index == 3 else "0.001" for index in range(16384)]
    lines = [
        "other" if bad_magic else "[FILEINFO]",
        "File: synthetic.tradb",
        "SampleRate[Hz]: 5000000",
        "SetsOnFile: 1",
        "Samples: 16384",
        "[SETINFO]",
        "Set: 1",
        "Index: 1",
        "Time: 0 00:00:00 000,0000",
        f"Channel: {10 if bad_channel else 9}",
        "PreTriggerSamples: 2000",
        "Data: Amplitude [mV]",
        "[DATA]",
        *samples,
        "[ENDDATA]",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_preserves_waveform_without_picking_arrival(tmp_path):
    path, digest = _waveform(tmp_path)
    values, record = read_controlled_ae_waveform(path, expected_sha256=digest)
    assert values.size == 16384
    assert record.sensor_channel == 9
    assert record.sample_rate_Hz == 5_000_000
    assert record.localization_use_status == "raw_waveform_no_arrival_pick"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"bad_magic": True}, "layout differs"),
        ({"bad_channel": True}, "channels differ"),
        ({"bad_value": True}, "nonnumeric"),
    ],
)
def test_reader_rejects_changed_or_invalid_waveform(tmp_path, kwargs, message):
    path, digest = _waveform(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        read_controlled_ae_waveform(path, expected_sha256=digest)


def test_reader_rejects_digest_mismatch(tmp_path):
    path, _ = _waveform(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        read_controlled_ae_waveform(path, expected_sha256="0" * 64)
