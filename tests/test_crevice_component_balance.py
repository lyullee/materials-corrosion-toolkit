import pytest

from matintegrity.crevice_coupled_phase_state import CoupledPhaseStateLayout


def test_phase_transfer_is_not_external_source():
    layout = CoupledPhaseStateLayout(("A",), ("solid",), ("cell",), ((2.0,),))
    start = layout.pack_initial(((8.0,),), ((1.0,),))
    end = layout.pack_initial(((4.0,),), ((3.0,),))
    report = layout.component_balance(start, end, ((0.0,),), absolute_tolerance_mol=0, relative_tolerance=0)
    assert report["balanced"]
    assert report["cells"][0]["dissolved_change_mol"] == -4
    assert report["cells"][0]["solid_component_change_mol"] == 4


def test_cell_transport_cannot_be_hidden_by_global_cancellation():
    layout = CoupledPhaseStateLayout(("A",), ("solid",), ("left", "right"), ((1.0,),))
    start = layout.pack_initial(((5.0, 5.0),), ((0.0, 0.0),))
    end = layout.pack_initial(((4.0, 6.0),), ((0.0, 0.0),))
    assert not layout.component_balance(
        start, end, ((0.0, 0.0),), absolute_tolerance_mol=0, relative_tolerance=0
    )["balanced"]
    assert layout.component_balance(
        start, end, ((-1.0, 1.0),), absolute_tolerance_mol=0, relative_tolerance=0
    )["balanced"]


@pytest.mark.parametrize("tolerance", [-1, float("inf"), float("nan"), True])
def test_invalid_tolerances(tolerance):
    layout = CoupledPhaseStateLayout(("A",), ("solid",), ("cell",), ((1.0,),))
    with pytest.raises(ValueError):
        layout.component_balance(
            (1.0, 0.0), (1.0, 0.0), ((0.0,),), absolute_tolerance_mol=tolerance, relative_tolerance=0
        )
