import numpy as np
import pytest

from matintegrity.calibration import fit_censored_sn
from matintegrity.thermo import ThermoRequest, fluid_state


def test_censored_fit_recovers_known_population():
    rng = np.random.default_rng(249)
    stress = np.exp(rng.uniform(np.log(0.7e8), np.log(2e8), 6000))
    life = 1e6 * (1e8 / stress) ** 4 * np.exp(rng.normal(0, 0.45, 6000))
    censor = life > 4e5
    observed = np.minimum(life, 4e5)
    fit = fit_censored_sn(stress, observed, censor)
    assert fit["exponent"] == pytest.approx(4.0, abs=0.2)
    assert fit["median_reference_cycles"] == pytest.approx(1e6, rel=0.08)
    assert fit["log_life_sigma"] == pytest.approx(0.45, abs=0.04)


def test_coolprop_published_water_boiling_reference_and_hydrogen():
    water = fluid_state(ThermoRequest(fluid="Water", pressure_Pa=101325.0, vapor_quality=0.0))
    assert 950 < water["properties"]["density_kg_m3"] < 970
    hydrogen = fluid_state(ThermoRequest(fluid="Hydrogen", pressure_Pa=1e6, temperature_K=300.0))
    assert 0.5 < hydrogen["properties"]["density_kg_m3"] < 1
    assert hydrogen["coolprop_version"]
