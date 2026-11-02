import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.materials import FormingAreaReduction, forming_area_reduction
from matintegrity.registry import default_registry


def request(original=1e-4, deformed=8e-5, reviewed=True):
    return FormingAreaReduction(
        physical_specimen_id="specimen",
        material_condition_id="condition",
        section_pair_id="pair",
        original_area_m2=original,
        deformed_area_m2=deformed,
        same_material_section_and_measurement_basis_reviewed=reviewed,
        evidence=({"source_id": "authored", "origin": "synthetic", "citation": "synthetic geometry"},),
    )


@pytest.mark.parametrize("scale", [1e-200, 1.0, 1e200])
def test_area_reduction_is_scale_invariant(scale):
    result = forming_area_reduction(request(scale, 0.8 * scale))
    assert result.status == "computed"
    assert result.values["area_reduction_fraction"] == pytest.approx(0.2)
    assert result.values["area_reduction_percent"] == pytest.approx(20.0)
    assert result.values["logarithmic_area_ratio"] == pytest.approx(math.log(1.25))


def test_growth_retains_signed_reduction_and_review_is_required():
    assert forming_area_reduction(request(1.0, 2.0)).values["area_reduction_percent"] == -100.0
    assert forming_area_reduction(request(reviewed=False)).status == "needs_data"


@pytest.mark.parametrize("original,deformed", [(1e-300, 1e300), (1e300, 1e-300), (1.0, 1e307)])
def test_unrepresentable_ratios_or_percentages_are_out_of_scope(original, deformed):
    assert forming_area_reduction(request(original, deformed)).status == "out_of_scope"


def test_registry_python_json_exchange():
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    value = request()
    direct = registry.run("fabrication.forming_area_reduction", value, context)
    serialized = registry.run_json("fabrication.forming_area_reduction", value.model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()
    assert direct.status == "computed"
