"""Provider-specific fatigue observations, kept apart from supplied fitted curves."""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np

from .contracts import check_finite


def _fabest_comment_review(comment: object) -> tuple[tuple[str, ...], float | None]:
    """Return lexical review flags without turning free text into test validity."""
    if comment is None or not str(comment).strip() or str(comment).strip() == "-":
        return (), None
    text = str(comment).strip()
    lowered = text.casefold()
    tags = []
    patterns = (
        ("reported_no_crack", r"\bno (?:visible )?crack(?: found)?\b"),
        ("reported_thread_damage", r"\bthread"),
        ("reported_grip_fretting", r"gripping section.*fretting"),
        ("reported_excluded", r"^excluded\b"),
        ("reported_mistake", r"\bmistake\b"),
        ("reported_possible_buckling", r"\bbuckling\??"),
        ("reported_crack_or_break", r"\b(?:crack|broken)\b"),
    )
    for tag, pattern in patterns:
        if re.search(pattern, lowered):
            if tag == "reported_crack_or_break" and "reported_no_crack" in tags:
                continue
            tags.append(tag)
    temperature_match = re.fullmatch(r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*degc\s*", lowered)
    temperature = None if temperature_match is None else float(temperature_match.group(1))
    if temperature is not None:
        tags.append("reported_comment_temperature")
    return tuple(tags), temperature


def read_fabest(path: str | Path) -> dict:
    """Read the numerical observation sections without executing workbook macros."""
    import openpyxl
    import pandas as pd

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_vba=False)
    observations, groups, static = [], [], []
    try:
        for name in workbook.sheetnames:
            if not re.fullmatch(r"FAB\d{3}", name) or name == "FAB501":
                continue
            rows = list(workbook[name].iter_rows(values_only=True))
            if rows[0][5] != "point ID" or rows[2][7] != "amplitude [MPa]":
                raise ValueError(f"FABEST observation header or unit changed in {name}")
            cycle_columns = [i for i, value in enumerate(rows[0]) if value == "number of cycles"]
            if len(cycle_columns) != 1 or cycle_columns[0] not in {11, 15}:
                raise ValueError(f"unrecognized fatigue channel layout in {name}")
            cycle_column = cycle_columns[0]
            channel_starts = [7] if cycle_column == 11 else [7, 11]
            metadata = {row[0]: row[1] for row in rows if len(row) > 1 and isinstance(row[0], str)}
            group = dict(
                group_id=name,
                material_id=metadata.get("MAT_NAME"),
                specimen_description=metadata.get("SPECIMEN"),
                load_reference=metadata.get("SP_LOADS"),
                acquisition_description=metadata.get("SRC_TYPE"),
                original_reference=metadata.get("ID_REF"),
                reported_end_criterion=metadata.get("END"),
                reported_end_parameter=metadata.get("END_PAR"),
                end_criterion_status="reported" if metadata.get("END") is not None else "absent",
                channel_modes=[str(rows[1][i]) for i in channel_starts],
                observation_rows=0,
                fitted_curve_rows_excluded=0,
            )
            in_observations = True
            for number, row in enumerate(rows[3:], 4):
                point = row[5]
                if point is not None and not str(point).startswith(name + "_"):
                    in_observations = False
                if not point or not str(point).startswith(name + "_"):
                    continue
                if not in_observations:
                    group["fitted_curve_rows_excluded"] += 1
                    continue
                endpoint = row[cycle_column + 2]
                if endpoint not in {"finished", "interrupted", None}:
                    raise ValueError(f"unresolved endpoint flag in {name} row {number}")
                channels = []
                for start in channel_starts:
                    if rows[2][start] != "amplitude [MPa]" or rows[2][start + 1] != "mean value [MPa]":
                        raise ValueError("FABEST channel units changed")
                    values = row[start : start + 4]
                    if not all(
                        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                        for v in values
                    ):
                        raise ValueError(f"incomplete fatigue channel in {name} row {number}")
                    amplitude, mean, frequency, phase = (float(v) for v in values)
                    if amplitude < 0 or frequency < 0:
                        raise ValueError("negative amplitude or frequency")
                    channels.append(
                        dict(
                            mode=str(rows[1][start]),
                            stress_amplitude_Pa=amplitude * 1e6,
                            stress_range_Pa=2 * amplitude * 1e6,
                            mean_stress_Pa=mean * 1e6,
                            frequency_Hz=frequency,
                            phase_rad=math.radians(phase),
                            stress_ratio=None
                            if mean + amplitude == 0
                            else (mean - amplitude) / (mean + amplitude),
                        )
                    )
                cycles = row[cycle_column]
                break_cycles = row[cycle_column + 1]
                if cycles is not None and (
                    not isinstance(cycles, (int, float)) or not math.isfinite(cycles) or cycles <= 0
                ):
                    raise ValueError("positive recorded endpoint cycles required")
                if break_cycles is not None and (
                    not isinstance(break_cycles, (int, float))
                    or not math.isfinite(break_cycles)
                    or break_cycles <= 0
                ):
                    raise ValueError("positive reported break cycles required")
                comment = row[cycle_column + 3] if len(row) > cycle_column + 3 else None
                comment_tags, comment_temperature_degC = _fabest_comment_review(comment)
                label_has_letter_suffix = bool(re.search(r"\d[A-Z]$", str(point)))
                if endpoint == "finished" and break_cycles is not None:
                    endpoint_contract_status = "reported_break_cycle"
                elif endpoint == "interrupted" and break_cycles is None:
                    endpoint_contract_status = "reported_interruption"
                elif endpoint is None and break_cycles is None:
                    endpoint_contract_status = "unresolved"
                else:
                    endpoint_contract_status = "conflicting_provider_fields"
                if comment_tags or label_has_letter_suffix:
                    calibration_role = "needs_specimen_protocol_review"
                elif endpoint_contract_status == "reported_break_cycle":
                    calibration_role = "candidate_failure_observation"
                elif endpoint_contract_status == "reported_interruption":
                    calibration_role = "candidate_censored_observation"
                else:
                    calibration_role = "unresolved_endpoint"
                record = dict(
                    source_id="fabest",
                    source_sheet=name,
                    source_row=number,
                    group_id=name,
                    specimen_id=str(point),
                    cycles_to_end=None if cycles is None else float(cycles),
                    cycles_to_reported_break=None if break_cycles is None else float(break_cycles),
                    reported_endpoint=endpoint,
                    provider_interrupted=endpoint == "interrupted",
                    endpoint_contract_status=endpoint_contract_status,
                    calibration_role=calibration_role,
                    row_valid=cycles is not None
                    and endpoint is not None
                    and any(c["stress_amplitude_Pa"] > 0 for c in channels),
                    channels=channels,
                    comment=None if comment is None else str(comment),
                    comment_review_tags=comment_tags,
                    reported_comment_temperature_degC=comment_temperature_degC,
                    specimen_label_suffix_status=(
                        "letter_suffix_semantics_unresolved" if label_has_letter_suffix else "none"
                    ),
                    physical_specimen_independence_reviewed=False,
                    endpoint_needs_review=comment is not None and str(comment).strip() not in {"", "-"},
                )
                check_finite(record)
                if str(point).endswith("_Rm"):
                    static.append(record)
                else:
                    observations.append(record)
                    group["observation_rows"] += 1
            groups.append(group)
        low_cycle = []
        if "FAB501" in workbook.sheetnames:
            rows = list(workbook["FAB501"].iter_rows(values_only=True))
            if rows[15][4:8] != ("Specimen ID", "εa [-]", "σa [MPa]", "Nf [cycles to failure]"):
                raise ValueError("FABEST strain-life observation schema changed")
            for number, row in enumerate(rows[16:], 17):
                if row[4] is None:
                    continue
                strain, stress, life = (float(v) for v in row[5:8])
                if not all(math.isfinite(v) and v > 0 for v in (strain, stress, life)):
                    raise ValueError("positive strain-life observations required")
                low_cycle.append(
                    dict(
                        source_id="fabest",
                        source_sheet="FAB501",
                        source_row=number,
                        specimen_id=str(row[4]),
                        strain_amplitude=strain,
                        stress_amplitude_Pa=stress * 1e6,
                        cycles_to_reported_failure=life,
                    )
                )
        frame = pd.DataFrame(observations)
        if frame.empty or frame.specimen_id.duplicated().any():
            raise ValueError("FABEST requires nonempty uniquely named observation rows")
        return dict(
            source_id="fabest",
            groups=groups,
            observations=frame,
            static_reference_points=static,
            strain_life_observations=pd.DataFrame(low_cycle),
            macro_execution=False,
            qualification="Provider finish/interruption state and the separate reported-break cycle are preserved. Letter suffixes are not called retests, interruption is not automatically called a runout, and free-text screening tags do not decide validity. Fitted values are excluded and no cross-group or physical-specimen independence is inferred.",
        )
    finally:
        workbook.close()


def summarize_recorded_bam_cycles(loaded: dict):
    """Compute recorded path work without differentiating a rounded time clock."""
    import pandas as pd

    frame = loaded["waveform"]
    required = {"cycle", "time_s", "stress_Pa", "strain_fraction", "temperature_K"}
    if not required <= set(frame):
        raise ValueError("normalized BAM waveform required")
    rows = []
    for cycle, part in frame.groupby("cycle", sort=False):
        stress = part.stress_Pa.to_numpy()
        strain = part.strain_fraction.to_numpy()
        rows.append(
            dict(
                cycle=int(cycle),
                observations=len(part),
                time_start_s=float(part.time_s.iloc[0]),
                time_end_s=float(part.time_s.iloc[-1]),
                stress_range_Pa=float(np.ptp(stress)),
                strain_range=float(np.ptp(strain)),
                signed_path_work_J_m3=float(np.trapezoid(stress, strain)),
                endpoint_stress_difference_Pa=float(stress[-1] - stress[0]),
                endpoint_strain_difference=float(strain[-1] - strain[0]),
                minimum_temperature_K=float(part.temperature_K.min()),
                maximum_temperature_K=float(part.temperature_K.max()),
            )
        )
    return pd.DataFrame(rows)
