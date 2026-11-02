"""Audit compiled burst data; no unqualified burst-pressure validation is inferred."""

import json
from collections import Counter
from pathlib import Path

import numpy as np

from matintegrity.burst_data import read_burst_compilation


def inspect(raw: Path):
    frame = read_burst_compilation(raw / "compiled-pipe-burst/burst-tests-v1.zip")
    field_names = list(frame.field_provenance.iloc[0])
    origins = Counter(value for row in frame.field_provenance for value in row.values())
    groups = [
        dict(
            domain=domain,
            reference=reference,
            rows=int(len(group)),
            numeric_valid_rows=int(group.numeric_geometry_material_valid.sum()),
            reference_resolved=bool(group.source_reference_resolved.all()),
        )
        for (domain, reference), group in frame.groupby(["observation_domain", "source_reference_id"])
    ]
    direct_legend_experimental_rows = int(
        (
            (frame.observation_domain == "experimental")
            & (frame.reference_mapping_status == "compilation_legend_reference")
        ).sum()
    )
    unresolved_ma13otros_rows = int(
        ((frame.observation_domain == "experimental") & (frame.source_reference_id == "Ma13Otros")).sum()
    )
    near_boundary = np.isclose(frame.reported_relative_depth, 0.8, rtol=0, atol=1e-12)
    return dict(
        rows=len(frame),
        domains={k: int(v) for k, v in frame.observation_domain.value_counts().items()},
        primary_reference_labels=int(frame.source_reference_id.nunique()),
        unresolved_reference_rows=int((~frame.source_reference_resolved).sum()),
        unresolved_reference_labels=sorted(
            frame.loc[~frame.source_reference_resolved, "source_reference_id"].unique().tolist()
        ),
        reference_mapping_status={
            k: int(v) for k, v in frame.reference_mapping_status.value_counts().items()
        },
        pressure_result_roles={k: int(v) for k, v in frame.pressure_result_role.value_counts().items()},
        physical_specimen_identity_status={
            k: int(v) for k, v in frame.physical_specimen_identity_status.value_counts().items()
        },
        underlying_observation_rights_status={
            k: int(v) for k, v in frame.underlying_observation_rights_status.value_counts().items()
        },
        ma13_article_review=dict(
            doi="10.1016/j.engfailanal.2013.03.015",
            publisher_url="https://www.sciencedirect.com/science/article/pii/S1350630713001222",
            checked_on="2026-10-27",
            publisher_reported_full_scale_test_groups=79,
            direct_legend_experimental_rows=direct_legend_experimental_rows,
            unresolved_ma13otros_rows=unresolved_ma13otros_rows,
            conclusion=(
                "The publisher page says Ma et al. collected 79 full-scale tests from published "
                "references. The compilation independently contains 79 experimental rows with direct "
                "legend references plus 23 Ma13Otros rows. Equality of the first count does not identify "
                "the 23 rows, their underlying papers, duplicates, specimens or rights; Ma13Otros remains "
                "an unresolved article-local compilation label."
            ),
        ),
        numeric_geometry_material_valid_rows=int(frame.numeric_geometry_material_valid.sum()),
        source_case_ids_unique=bool(frame.source_case_id.is_unique),
        intact_rows=int((frame.defect_depth_m == 0).sum()),
        relative_depth_above_0p8_outside_roundoff=int(
            ((frame.reported_relative_depth > 0.8) & ~near_boundary).sum()
        ),
        relative_depth_near_0p8_rows=int(near_boundary.sum()),
        source_description_deep_defect_count=19,
        depth_count_note="Actual primary-table values give 16 clearly above 0.8 and three within 1e-12 of 0.8; the provider description says 19 deeper defects. The tolerance here is a reporting audit, not an engineering acceptance rule.",
        identical_reported_input_target_rows=int(frame.identical_reported_input_and_target.sum()),
        duplicate_row_domains={
            k: int(v)
            for k, v in frame.loc[frame.identical_reported_input_and_target, "observation_domain"]
            .value_counts()
            .items()
        },
        reported_input_groups=int(frame.reported_input_digest.nunique()),
        cell_origin_counts=dict(origins),
        material_completion_by_field={
            key: sum(row[key] == "compiler_completed_material_property" for row in frame.field_provenance)
            for key in field_names
        },
        geometry_inference_by_field={
            key: sum(row[key] == "compiler_inferred_geometry" for row in frame.field_provenance)
            for key in field_names
        },
        source_groups=groups,
        source_sha256=frame.attrs["source_sha256"],
        workbook_sha256=frame.attrs["workbook_sha256"],
        supplementary_sheets_excluded=frame.attrs["supplementary_sheets_excluded"],
        diameter_basis="not_explicit_in_primary_table",
        pressure_basis="not_explicit_in_primary_table",
        qualification="Experimental-burst/FEM-failure roles, reference tier and cell-origin audit only. Material completion, inferred widths, original specimen identity, unresolved Ma13Otros underlying references and rights, diameter/pressure convention, defect topology and test protocol require review before calibration or independent pressure validation. Raw and pointwise derived observations are excluded from redistribution; no normative bulging/flow-stress table is inferred.",
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(inspect(root / "data/raw"), ensure_ascii=True, indent=2, allow_nan=False))
