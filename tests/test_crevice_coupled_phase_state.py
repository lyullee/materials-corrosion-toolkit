import pytest

from matintegrity.crevice_coupled_phase_state import CoupledPhaseStateLayout


def layout():
    return CoupledPhaseStateLayout(("A", "B"), ("salt",), ("left", "right"), ((1.0,), (2.0,)))


def test_total_state_and_same_stage_dissolved_reconstruction():
    x = layout()
    state = x.pack_initial(((10.0, 20.0), (30.0, 40.0)), ((2.0, 3.0),))
    assert state == (12.0, 23.0, 34.0, 46.0, 2.0, 3.0)
    # More solid at one trial changes dissolved components at that same trial.
    dissolved, solids = x.unpack_trial(state[:4] + (3.0, 4.0))
    assert dissolved == ((9.0, 19.0), (28.0, 38.0))
    assert solids == ((3.0, 4.0),)
    assert x.derivative(((0.0, 0.0), (0.0, 0.0)), ((1.0, -1.0),)) == (0.0, 0.0, 0.0, 0.0, 1.0, -1.0)


def test_transport_changes_total_components_without_double_counting_phase_transfer():
    x = layout()
    assert x.derivative(((-2.0, 2.0), (-4.0, 4.0)), ((3.0, 3.0),)) == (-2.0, 2.0, -4.0, 4.0, 3.0, 3.0)


def test_invalid_trials_are_never_clipped():
    x = layout()
    with pytest.raises(ValueError, match="solid trial"):
        x.unpack_trial((1.0, 1.0, 2.0, 2.0, -1.0, 0.0))
    with pytest.raises(ArithmeticError, match="consumes"):
        x.unpack_trial((1.0, 1.0, 2.0, 2.0, 2.0, 0.0))
    with pytest.raises(ValueError, match="layout"):
        x.unpack_trial((1.0,))


def test_small_dissolved_inventory_cannot_disappear_in_total_roundoff():
    x = CoupledPhaseStateLayout(("A",), ("s",), ("c",), ((1.0,),))
    with pytest.raises(ArithmeticError, match="loses"):
        x.pack_initial(((1.0,),), ((1e100,),))


def test_identity_and_matrix_layout():
    with pytest.raises(ValueError, match="unique"):
        CoupledPhaseStateLayout(("A", "A"), ("s",), ("c",), ((1.0,), (1.0,)))
    with pytest.raises(ValueError, match="map"):
        CoupledPhaseStateLayout(("A",), ("s",), ("c",), ((1.0, 2.0),))
