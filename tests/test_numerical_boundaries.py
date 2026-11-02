import json
from pathlib import Path

import pytest

from matintegrity.catalogs import load_catalog
from matintegrity.contracts import RunContext
from matintegrity.data import parse_reported_value, read_bam_creep_fatigue
from matintegrity.registry import default_registry


def test_exhausted_wall_is_not_clipped_into_a_valid_forecast():
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    result = registry.run(
        "corrosion.uniform_forecast",
        dict(current_thickness_m=0.001, required_thickness_m=0.0005, rate_m_s=0.0001, horizon_s=20.0),
        context,
    )
    assert result.status == "out_of_scope"
    assert result.values["predicted_thickness_m"] is None
    assert result.values["time_to_required_s"] == 5.0
    assert result.inputs["current_thickness_m"] == 0.001


def test_equal_pressure_zero_work_and_near_isothermal_limit():
    import math

    context = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    registry = default_registry()
    base = dict(
        initial_absolute_pressure_Pa=1e6,
        final_absolute_pressure_Pa=1e6,
        initial_volume_m3=0.1,
        heat_capacity_ratio=1.00000001,
    )
    result = registry.run("inspection.gas_expansion_energy", base, context)
    assert result.values["ideal_expansion_work_J"] == 0.0
    result = registry.run(
        "inspection.gas_expansion_energy", dict(base, final_absolute_pressure_Pa=1e5), context
    )
    assert result.values["ideal_expansion_work_J"] == pytest.approx(1e5 * math.log(10), rel=1e-7)


def test_small_weibull_interval_does_not_cancel_large_age():
    context = RunContext(asset_id="a", location_id="b", time_basis="synthetic")
    result = default_registry().run(
        "reliability.weibull_interval",
        dict(shape=1.0, scale_s=1e20, current_age_s=1e20, horizon_s=1.0),
        context,
    )
    assert result.values["probability_given_survival"] == pytest.approx(1e-20, rel=1e-12, abs=0)


@pytest.mark.parametrize("value", ["1e999", ">1e999", "0 - 1e999"])
def test_out_of_range_reported_numbers_remain_unresolved(value):
    result = parse_reported_value(value)
    assert result["kind"] == "unresolved"
    json.dumps(result, allow_nan=False)


def test_bam_reader_preserves_rounding_without_inventing_a_finer_clock(tmp_path):
    text = (
        "Test Design\t\t\t\tSynthetic test\nMaterial\t\t\t\tSynthetic\n"
        "[MAX-MIN]\n[Data]\nTime\tCycle\tStress\tStrain\tTemperature\n"
        "s\tNo\tMPa\t%\t°C\n0\t1\t100\t0.1\t620\n0\t1\t101\t0.11\t620\n"
        "1\t1\t100\t0.1\t620\n"
    )
    path = tmp_path / "test.lis"
    path.write_text(text, encoding="cp1252")
    loaded = read_bam_creep_fatigue(path)
    assert loaded["zero_duration_intervals"] == 1
    assert loaded["clock_strictly_increasing"] is False
    assert loaded["waveform"].stress_Pa.iloc[1] == 101e6
    assert loaded["waveform"].strain_fraction.iloc[0] == 0.001


def test_installed_catalogs_equal_reviewed_public_catalogs():
    root = Path(__file__).resolve().parents[1]
    for name in ("capabilities", "datasets", "sources"):
        expected = json.loads((root / "data/catalogs" / f"{name}.json").read_text(encoding="utf-8"))
        assert load_catalog(name) == expected
