import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.grain_planimetry import (
    GrainCountField,
    GrainPlanimetrySummary,
    grain_planimetry_summary,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        physical_specimen_id="sample",
        material_condition_id="condition",
        phase_id="phase",
        counting_procedure_id="authored",
        calibration_id="authored",
        reference_number=0,
        reference_areal_density_per_m2=2,
        number_increment_per_density_doubling=1,
        fields=(
            GrainCountField(
                field_id="field",
                physical_specimen_id="sample",
                image_sha256="a" * 64,
                counting_region_id="region",
                specimen_plane_area_m2=1,
                effective_grain_count=8,
            ),
        ),
        specimen_area_boundary_counting_and_nonoverlap_reviewed=True,
        population_and_number_calibration_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        GrainPlanimetrySummary.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return GrainPlanimetrySummary(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored counts",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_density_number_and_mean_area():
    result = grain_planimetry_summary(request())
    assert result.values["areal_grain_density_per_m2"] == 8
    assert result.values["calibrated_grain_number"] == 2
    assert result.values["mean_planar_area_per_grain_m2"] == 0.125


def test_pool_counts_and_areas_instead_of_averaging_field_densities():
    first = request().fields[0]
    second = first.model_copy(
        update=dict(
            field_id="other", image_sha256="b" * 64, specimen_plane_area_m2=3, effective_grain_count=4
        )
    )
    result = grain_planimetry_summary(request(fields=(first, second)))
    assert result.values["areal_grain_density_per_m2"] == 3


def test_small_density_contrast_is_not_erased_by_log_subtraction():
    field = request().fields[0].model_copy(update=dict(effective_grain_count=math.nextafter(1, 2)))
    result = grain_planimetry_summary(request(fields=(field,), reference_areal_density_per_m2=1))
    assert result.values["calibrated_grain_number"] == pytest.approx(
        math.log1p(math.ulp(1)) / math.log(2), abs=0
    )


@pytest.mark.parametrize("change", [dict(physical_specimen_id="wrong"), dict(field_id="renamed")])
def test_wrong_specimen_or_duplicate_physical_region_rejected(change):
    first = request().fields[0]
    with pytest.raises(ValueError):
        request(fields=(first, first.model_copy(update=change)))


def test_zero_counts_and_unreviewed_population_remain_missing_data():
    field = request().fields[0].model_copy(update=dict(effective_grain_count=0))
    assert grain_planimetry_summary(request(fields=(field,))).status == "needs_data"
    assert (
        grain_planimetry_summary(request(population_and_number_calibration_reviewed=False)).status
        == "needs_data"
    )


def test_density_overflow_withholds_numeric_summary():
    field = (
        request()
        .fields[0]
        .model_copy(update=dict(effective_grain_count=1e308, specimen_plane_area_m2=1e-308))
    )
    result = grain_planimetry_summary(request(fields=(field,)))
    assert result.status == "out_of_scope"
    assert "calibrated_grain_number" not in result.values


def test_number_scale_product_overflow_can_cancel_with_offset():
    field = request().fields[0].model_copy(update=dict(effective_grain_count=1))
    result = grain_planimetry_summary(
        request(
            fields=(field,),
            reference_areal_density_per_m2=4,
            reference_number=1e308,
            number_increment_per_density_doubling=1e308,
        )
    )
    assert result.status == "computed"
    assert result.values["calibrated_grain_number"] == -1e308


def test_nonzero_number_underflow_is_not_reported_as_zero():
    field = request().fields[0].model_copy(update=dict(effective_grain_count=1))
    result = grain_planimetry_summary(
        request(
            fields=(field,),
            reference_areal_density_per_m2=1.25,
            reference_number=0,
            number_increment_per_density_doubling=5e-324,
        )
    )
    assert result.status == "out_of_scope"
    assert "calibrated_grain_number" not in result.values


def test_registry_python_json_exchange():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="authored", location_id="sample", time_basis="synthetic")
    assert (
        registry.run("testing.grain_planimetry_summary", x, context).model_dump()
        == registry.run_json("testing.grain_planimetry_summary", x.model_dump_json(), context).model_dump()
    )
