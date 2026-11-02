import pandas as pd
import pytest

from matintegrity.data import read_galvanized_polarization


def test_polarization_preserves_current_sign_and_converts_area_units(tmp_path):
    path = tmp_path / "synthetic.xlsx"
    pd.DataFrame(
        [
            [None, "Sample test", None],
            [None, "Potential (V)", "Current (A·cm-2)"],
            [None, -0.5, -0.0001],
            [None, -0.4, 0.0002],
        ]
    ).to_excel(path, header=False, index=False)
    frame = read_galvanized_polarization(path)
    assert frame.signed_current_density_A_m2.tolist() == pytest.approx([-1.0, 2.0])
    assert frame.potential_V.tolist() == [-0.5, -0.4]
    pd.DataFrame(
        [[None, "Sample test", None], [None, "Potential (V)", "Current (mA)"], [None, -0.5, 1.0]]
    ).to_excel(path, header=False, index=False)
    with pytest.raises(ValueError, match="headings/units"):
        read_galvanized_polarization(path)
