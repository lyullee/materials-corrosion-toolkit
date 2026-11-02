from __future__ import annotations

import hashlib

import pytest

from matintegrity.cathodic_protection_data import read_dplot_curves


def _write_dplot(tmp_path, *, bad_magic=False, bad_value=False):
    path = tmp_path / "OCP in Test.csv"
    value = "bad" if bad_value else "-0.31"
    path.write_text(
        "\n".join(
            [
                "other" if bad_magic else "DPLOT v1.6",
                "data",
                "1",
                "2",
                f"0,{value}",
                "1,-0.32",
                " 1    0",
                "steel bar",
                "",
                "title",
            ]
        ),
        encoding="utf-8",
    )
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_preserves_native_ocp_curve(tmp_path):
    path, digest = _write_dplot(tmp_path)
    arrays, records = read_dplot_curves(path, expected_sha256=digest)
    assert len(arrays) == 1
    assert records[0].sample_count == 2
    assert records[0].x_unit == "s"
    assert records[0].y_unit == "V_vs_calomel"
    assert records[0].interpretation_status == "raw_curve_no_acceptance_or_corrosion_rate"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [({"bad_magic": True}, "DPlot layout"), ({"bad_value": True}, "nonnumeric")],
)
def test_reader_rejects_changed_or_invalid_layout(tmp_path, kwargs, message):
    path, digest = _write_dplot(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        read_dplot_curves(path, expected_sha256=digest)


def test_reader_rejects_digest_mismatch(tmp_path):
    path, _ = _write_dplot(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        read_dplot_curves(path, expected_sha256="0" * 64)
