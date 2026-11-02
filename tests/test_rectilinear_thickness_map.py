import pytest
from pydantic import ValidationError

from matintegrity.models.rectilinear_thickness_map import (
    RectilinearThicknessMap,
    rectilinear_thickness_map,
    specifications,
)


def map_input(**updates):
    values = {
        "x_cell_edges_m": [0.0, 1.0, 3.0],
        "y_cell_edges_m": [0.0, 1.0, 4.0],
        "cell_thickness_m": [[0.005, None], [0.004, 0.008]],
        "reference_thickness_m": 0.01,
        "reporting_threshold_m": 0.006,
        "threshold_comparison": "less_than",
    }
    values.update(updates)
    return RectilinearThicknessMap(**values)


def test_nonuniform_areas_weight_mean_loss_missing_and_connected_area():
    result = rectilinear_thickness_map(map_input())
    assert result.values["total_map_area_m2"] == pytest.approx(12.0)
    assert result.values["observed_area_m2"] == pytest.approx(10.0)
    assert result.values["missing_area_m2"] == pytest.approx(2.0)
    assert result.values["observed_area_fraction"] == pytest.approx(10.0 / 12.0)
    assert result.values["area_weighted_mean_observed_thickness_m"] == pytest.approx(0.0065)
    assert result.values["net_observed_loss_volume_m3"] == pytest.approx(0.035)
    assert result.values["connected_threshold_component_areas_m2"] == pytest.approx([4.0])
    assert result.values["threshold_cell_area_m2"] == pytest.approx(4.0)
    assert result.values["interpolation_performed"] is False


def test_diagonal_cells_are_separate_and_actual_component_areas_are_retained():
    result = rectilinear_thickness_map(map_input(cell_thickness_m=[[0.005, 0.01], [None, 0.005]]))
    assert result.values["connected_threshold_component_areas_m2"] == pytest.approx([6.0, 1.0])
    assert result.values["connected_threshold_component_count"] == 2
    assert result.values["connectivity"] == "four_neighbour_shared_edge"


def test_eight_neighbour_connectivity_merges_diagonal_cells():
    result = rectilinear_thickness_map(
        map_input(
            cell_thickness_m=[[0.005, 0.01], [None, 0.005]],
            connectivity="eight_neighbour",
        )
    )
    assert result.values["connected_threshold_component_areas_m2"] == pytest.approx([7.0])
    assert result.values["connected_threshold_component_count"] == 1
    assert result.values["connectivity"] == "eight_neighbour_shared_edge_or_corner"


def test_threshold_comparison_is_explicit_at_equality():
    strict = rectilinear_thickness_map(map_input(cell_thickness_m=[[0.006, None], [None, None]]))
    inclusive = rectilinear_thickness_map(
        map_input(
            cell_thickness_m=[[0.006, None], [None, None]],
            threshold_comparison="less_than_or_equal",
        )
    )
    assert strict.values["connected_threshold_component_count"] == 0
    assert inclusive.values["connected_threshold_component_areas_m2"] == pytest.approx([1.0])


@pytest.mark.parametrize(
    "updates, message",
    [
        ({"x_cell_edges_m": [0.0, 1.0, 1.0]}, "strictly increasing"),
        ({"cell_thickness_m": [[0.005, None]]}, "one row per y interval"),
        ({"cell_thickness_m": [[None, None], [None, None]]}, "at least one observed"),
        ({"cell_thickness_m": [[-0.001, None], [None, None]]}, "greater than or equal"),
    ],
)
def test_edges_shape_observation_and_nonnegative_thickness_are_strict(updates, message):
    with pytest.raises(ValidationError, match=message):
        map_input(**updates)


def test_local_model_specification_reports_scope_and_source():
    spec = specifications()[0]
    assert spec.model_id == "geometry.rectilinear_thickness_map"
    assert spec.input_type is RectilinearThicknessMap
    assert spec.source_ids == ("authored_rectilinear_thickness_map_cell_area_balance",)
