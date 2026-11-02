import openpyxl

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.data import read_bam_creep_fatigue
from matintegrity.fatigue_data import read_fabest, summarize_recorded_bam_cycles


def test_fabest_excludes_static_and_fitted_values_preserves_unknown_endpoint(tmp_path):
    workbook = openpyxl.Workbook()
    s = workbook.active
    s.title = "FAB001"
    s.cell(1, 6, "point ID")
    s.cell(1, 12, "number of cycles")
    s.cell(2, 8, "tension-compression")
    for column, value in [(8, "amplitude [MPa]"), (9, "mean value [MPa]")]:
        s.cell(3, column, value)
    for number, point, cycles, break_cycles, flag, comment in [
        (4, "FAB001_Rm", 0.25, 0.25, "finished", None),
        (5, "FAB001_1", 100, 100, "finished", "no crack found"),
        (6, "FAB001_2B", 1000, None, "interrupted", "214degC"),
        (7, "FAB001_3", None, None, None, None),
    ]:
        s.cell(number, 6, point)
        for col, val in [(8, 100), (9, 0), (10, 10), (11, 0), (12, cycles), (14, flag)]:
            if val is not None:
                s.cell(number, col, val)
        if break_cycles is not None:
            s.cell(number, 13, break_cycles)
        if comment is not None:
            s.cell(number, 15, comment)
    s.cell(8, 6, "Synthetic regression section")
    s.cell(9, 6, "FAB001_1E+6")
    s.cell(9, 12, 1e6)
    path = tmp_path / "synthetic.xlsx"
    workbook.save(path)
    result = read_fabest(path)
    f = result["observations"]
    assert len(f) == 3 and len(result["static_reference_points"]) == 1
    assert result["groups"][0]["fitted_curve_rows_excluded"] == 1
    assert f.channels.iloc[0][0]["stress_range_Pa"] == 200e6
    assert f.specimen_label_suffix_status.tolist() == [
        "none",
        "letter_suffix_semantics_unresolved",
        "none",
    ]
    assert f.row_valid.tolist() == [True, True, False]
    assert f.provider_interrupted.tolist() == [False, True, False]
    assert f.endpoint_contract_status.tolist() == [
        "reported_break_cycle",
        "reported_interruption",
        "unresolved",
    ]
    assert f.calibration_role.tolist() == [
        "needs_specimen_protocol_review",
        "needs_specimen_protocol_review",
        "unresolved_endpoint",
    ]
    assert f.comment_review_tags.tolist() == [
        ("reported_no_crack",),
        ("reported_comment_temperature",),
        (),
    ]
    assert f.reported_comment_temperature_degC.iloc[1] == 214
    assert not f.physical_specimen_independence_reviewed.any()
    assert result["groups"][0]["end_criterion_status"] == "absent"
    assert result["macro_execution"] is False


def test_fabest_comment_screening_does_not_decide_validity():
    from matintegrity.fatigue_data import _fabest_comment_review

    tags, temperature = _fabest_comment_review("Broken 3rd thread")
    assert tags == ("reported_thread_damage", "reported_crack_or_break")
    assert temperature is None
    tags, temperature = _fabest_comment_review("buckling?")
    assert tags == ("reported_possible_buckling",)
    assert temperature is None


def test_bam_extrema_use_explicit_units_and_no_missing_cycle_interpolation(tmp_path):
    text = (
        "Test Design\t\t\t\tSynthetic\n[MAX-MIN]\n"
        "Cycle\tStress-Max\tStress-Min\tStrain-Max\tStrain-Min\tTemperature-Max\tTemperature-Min\n"
        "No\tMPa\tMPa\t%\t%\t°C\t°C\n1\t100\t-100\t0.2\t-0.2\t620\t619\n"
        "4\t90\t-90\t0.2\t-0.2\t620\t619\n[Data]\n"
        "Time\tCycle\tStress\tStrain\tTemperature\ns\tNo\tMPa\t%\t°C\n"
        "0\t1\t0\t0\t620\n0\t1\t100\t0.2\t620\n1\t4\t-90\t-0.2\t620\n"
    )
    path = tmp_path / "synthetic.lis"
    path.write_text(text, encoding="cp1252")
    loaded = read_bam_creep_fatigue(path)
    assert loaded["cycle_extrema"].cycle.tolist() == [1, 4]
    assert loaded["cycle_extrema"].maximum_stress_Pa.iloc[0] == 100e6
    summary = summarize_recorded_bam_cycles(loaded)
    assert summary.cycle.tolist() == [1, 4]
    assert loaded["zero_duration_intervals"] == 1


def test_hysteresis_path_work_orientation_and_open_boundary():
    context = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="ordered samples")
    inputs = dict(
        stress_Pa=[0.0, 2.0, 2.0, 0.0, 0.0],
        strain_fraction=[0.0, 0.0, 3.0, 3.0, 0.0],
        cycle_boundary_declared=True,
        linear_closure_declared=False,
        maximum_endpoint_stress_difference_Pa=0.0,
        maximum_endpoint_strain_difference=0.0,
    )
    v = evaluate("fatigue.hysteresis_path", inputs, context).values
    assert v["signed_closed_cycle_work_J_m3"] == 6
    inputs["stress_Pa"] = inputs["stress_Pa"][::-1]
    inputs["strain_fraction"] = inputs["strain_fraction"][::-1]
    assert evaluate("fatigue.hysteresis_path", inputs, context).values["signed_closed_cycle_work_J_m3"] == -6
    inputs["strain_fraction"][-1] = 1.0
    assert (
        evaluate("fatigue.hysteresis_path", inputs, context).values["signed_closed_cycle_work_J_m3"] is None
    )
