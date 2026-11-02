"""Previously unexecuted branches found by the prepublication static audit."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.crevice_campaign import solve_crevice_transport_recession_feedback
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def test_zero_solid_stage_builds_species_index_from_explicit_order():
    from matintegrity.wet_co2_cylindrical_stage_kinetic_scale_feedback import _stage_fluxes

    fluxes, saturation = _stage_fluxes(
        SimpleNamespace(),
        [],
        0,
        0.0,
        [0.1, 0.2],
        1,
        ["authored-A", "authored-B"],
        {},
        [1.0, 2.0],
        1.0,
        1.0,
        1.0,
        [],
    )
    assert fluxes == [] and saturation == []


@pytest.mark.parametrize(
    "provider", ["geometry_aware_chemistry_provider", "geometry_aware_solid_deposition_provider"]
)
def test_recession_feedback_accepts_declared_provider_arguments_and_rejects_untyped_provider(provider):
    result = solve_crevice_transport_recession_feedback(
        campaign_id="authored",
        geometry=None,
        base_transport_request=None,
        feedback=None,
        output_times_s=(0.0, 1.0),
        exact_time_geometry_remap_reviewed=False,
        fixed_geometry_within_interval_reviewed=False,
        cell_inventory_remap_reviewed=False,
        callback_global_time_mapping_reviewed=False,
        reaction=lambda time, concentration: concentration,
        **{provider: object()},
    )
    assert result["status"] == "needs_data"
    assert "typed geometry-aware" in result["reason"]


def test_condensate_each_interval_uses_its_own_density_before_computing_thickness():
    intervals = []
    for i, density in enumerate((1000.0, 500.0)):
        digest = canonical_digest(dict(index=i, density=density, flux=0.1))
        intervals.append(
            dict(
                start_time_s=float(i),
                end_time_s=float(i + 1),
                net_retained_water_mass_flux_kg_m2_s=0.1,
                liquid_water_density_kg_m3=density,
                flux_provider_id="authored-flux",
                flux_provider_revision="1",
                flux_configuration_sha256=digest,
                flux_result_sha256=digest,
                density_provider_id="authored-density",
                density_provider_revision="1",
                density_record_sha256=digest,
                evidence=[
                    dict(
                        source_id=source,
                        origin="synthetic",
                        citation="Authored inventory-density arithmetic",
                        sha256=digest,
                    )
                    for source in ("authored-flux", "authored-density")
                ],
                interval_state_and_units_reviewed=True,
            )
        )
    payload = dict(
        assessment_id="authored",
        asset_id="authored",
        location_id="authored",
        physical_scope_id="authored",
        wall_patch_id="authored",
        condition_id="authored",
        initial_water_areal_inventory_kg_m2=0.0,
        intervals=intervals,
        fixed_wall_patch_and_area_basis_reviewed=True,
        net_flux_includes_retention_drainage_and_evaporation_reviewed=True,
        uniform_film_thickness_interpretation_reviewed=True,
        no_lateral_water_exchange_reviewed=True,
        calculation_use_authorized=True,
    )
    result = default_registry().run_json(
        "integration.wet_co2_condensate_film_history",
        json.dumps(payload),
        RunContext(asset_id="authored", location_id="authored", time_basis="elapsed seconds"),
    )
    assert result.status == "computed", result.values
    assert result.values["final_water_areal_inventory_kg_m2"] == pytest.approx(0.2)
    assert result.values["final_uniform_equivalent_film_thickness_m"] == pytest.approx(0.2 / 500.0)
    ledger = result.values["interval_ledger"]
    assert ledger[0]["uniform_equivalent_film_thickness_end_m"] == pytest.approx(0.1 / 1000.0)
    assert ledger[1]["uniform_equivalent_film_thickness_start_m"] == pytest.approx(0.1 / 500.0)


def test_activity_temperature_slices_cover_system_temperature_without_name_error():
    data = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]
    payload = copy.deepcopy(data["chemistry.aqueous_tabulated_activity_speciation"])
    temperature = payload["system"]["temperature_K"]
    for curve in payload["species_activity_curves"]:
        points = curve.pop("points")
        curve["temperature_slices"] = [
            dict(temperature_K=t, points=points) for t in (temperature - 10.0, temperature + 10.0)
        ]
    registry = default_registry()
    request = registry.input_type("chemistry.aqueous_tabulated_activity_speciation").model_validate_json(
        json.dumps(payload)
    )
    assert request.system.temperature_K == temperature
