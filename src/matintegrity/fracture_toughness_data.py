"""Read the pinned transition-fracture-toughness workbook without inferring missing units."""

from __future__ import annotations

import hashlib
import io
import math
import zipfile
from pathlib import Path

SHEETS = {"Table A.2": "training", "Table A.3": "test"}
EXPECTED_HEADERS = {
    "B4": "No.",
    "C4": "wt%",
    "D4": "K",
    "E4": "MPa",
    "F4": "CT",
    "G4": "SEB",
    "H4": "PCCv",
    "I4": "W",
    "J4": "B",
    "K4": "a",
    "L4": "MPam1/2",
    "M4": "Material",
}
SPECIMEN_TYPES = ("CT", "SEB", "PCCv")
ARTICLE_DOI = "10.1016/j.engfailanal.2020.104458"

ARTICLE_REFERENCE_CATALOG = {
    "ref-6": {
        "bibliographic_id": "doi:10.1016/j.tafmec.2019.01.027",
        "identity_status": "resolved_doi",
        "publication_license_id": "CC-BY-NC-ND-4.0",
        "observation_rights_status": "unresolved",
    },
    "ref-8": {
        "bibliographic_id": "doi:10.1177/1687814019870897",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-16": {
        "bibliographic_id": None,
        "identity_status": "bibliography_only",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-17": {
        "bibliographic_id": None,
        "identity_status": "bibliography_only",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-18": {
        "bibliographic_id": "doi:10.1016/j.jnucmat.2015.06.009",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-19": {
        "bibliographic_id": "doi:10.1016/j.engfracmech.2005.07.008",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-20": {
        "bibliographic_id": "doi:10.11484/jaea-data-code-2018-013",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-21": {
        "bibliographic_id": "doi:10.1016/j.engfailanal.2015.08.046",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
    "ref-22": {
        "bibliographic_id": "doi:10.1007/s12206-015-0907-2",
        "identity_status": "resolved_doi",
        "publication_license_id": None,
        "observation_rights_status": "unresolved",
    },
}

# Independently transcribed article-table group labels. These are article-local
# reference numbers, not resolved literature identifiers or redistribution grants.
ARTICLE_SOURCE_GROUPS = {
    "A508C": (0.19, "A508C", "ref-16", "article_table_exact"),
    "SFVQ1A": (0.18, "SFVQ1A", "ref-17", "article_table_exact"),
    "20MnMoNi55": (0.20, "20MnMoNi55", "ref-18", "article_table_exact"),
    "A533B": (0.24, "A533B", "ref-16", "article_table_exact"),
    "SQV2A-heat1": (0.22, "SQV2A heat 1", "ref-17", "article_table_exact"),
    "SQV2A-heat2": (0.22, "SQV2A heat 2", "ref-17", "article_table_exact"),
    "JRQ": (0.18, "JRQ", "ref-20", "article_table_exact"),
    "S275JR": (0.18, "S275JR", "ref-21", "article_table_exact"),
    "S355J2": (0.20, "S355J2", "ref-21", "article_table_exact"),
    "S460M": (0.12, "S460M", "ref-22", "article_table_exact"),
    "S690Q": (0.15, "S690Q", "ref-22", "article_table_exact"),
    "SCM440": (0.39, "SCM440", "ref-6", "article_table_exact"),
    # The workbook label and carbon value differ slightly from article-table S55C, 0.54 wt%.
    "S55CFY2012": (0.55, "S55C", "ref-8", "probable_name_variant"),
}


def resolve_article_source_group(material_label: str, carbon_wt_percent: float) -> dict[str, str | None]:
    """Resolve only the compilation article's material-group label.

    This deliberately does not resolve a physical specimen or an underlying-literature
    identifier. A known label with a different carbon value is retained as a mismatch.
    """
    group = ARTICLE_SOURCE_GROUPS.get(material_label)
    if group is None:
        return {
            "article_source_group_id": None,
            "article_source_group_status": "unresolved",
            "article_source_material_label": None,
            "article_reference_bibliographic_id": None,
            "article_reference_identity_status": "unresolved_source_group",
            "article_reference_publication_license_id": None,
            "article_reference_observation_rights_status": "unresolved",
        }
    expected_carbon, source_material, reference, status = group
    if not math.isclose(carbon_wt_percent, expected_carbon, rel_tol=0.0, abs_tol=1e-12):
        status = "material_condition_mismatch"
        reference = None
    reference_record = ARTICLE_REFERENCE_CATALOG.get(reference, {})
    return {
        "article_source_group_id": (None if reference is None else f"doi:{ARTICLE_DOI}#{reference}"),
        "article_source_group_status": status,
        "article_source_material_label": source_material,
        "article_reference_bibliographic_id": reference_record.get("bibliographic_id"),
        "article_reference_identity_status": reference_record.get(
            "identity_status", "unresolved_source_group"
        ),
        "article_reference_publication_license_id": reference_record.get("publication_license_id"),
        "article_reference_observation_rights_status": reference_record.get(
            "observation_rights_status", "unresolved"
        ),
    }


def _finite_number(value: object, *, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric, not boolean")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _workbook_member(archive: zipfile.ZipFile) -> str:
    members = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
    if len(members) != 1:
        raise ValueError(f"expected one xlsx member, found {len(members)}")
    return members[0]


def _assign_condition_groups(
    frame,
    *,
    relative_tolerance: float,
    absolute_tolerance_m: float,
) -> None:
    """Assign source-specific geometry groups without claiming specimen independence."""
    frame["condition_group_id"] = None
    frame["condition_group_status"] = "unresolved_dimension_unit"
    frame["condition_group_W_center_m"] = None
    frame["condition_group_B_center_m"] = None
    frame["condition_group_physical_independence_reviewed"] = False
    if frame[["W_m", "B_m"]].isna().any(axis=None):
        return

    for (material, specimen_type), subset in frame.groupby(["material_label", "specimen_type"], sort=True):
        geometries = sorted(set(zip(subset.W_m, subset.B_m, strict=True)))
        clusters: list[list[tuple[float, float]]] = []
        geometry_cluster: dict[tuple[float, float], int] = {}
        for width, thickness in geometries:
            for cluster_index, cluster in enumerate(clusters):
                anchor_width, anchor_thickness = cluster[0]
                width_tolerance = max(absolute_tolerance_m, relative_tolerance * abs(anchor_width))
                thickness_tolerance = max(absolute_tolerance_m, relative_tolerance * abs(anchor_thickness))
                if (
                    abs(width - anchor_width) <= width_tolerance
                    and abs(thickness - anchor_thickness) <= thickness_tolerance
                ):
                    cluster.append((width, thickness))
                    geometry_cluster[(width, thickness)] = cluster_index
                    break
            else:
                geometry_cluster[(width, thickness)] = len(clusters)
                clusters.append([(width, thickness)])

        centers = {
            index: (
                sum(width for width, _ in cluster) / len(cluster),
                sum(thickness for _, thickness in cluster) / len(cluster),
            )
            for index, cluster in enumerate(clusters)
        }
        for row_index in subset.index:
            cluster_index = geometry_cluster[(frame.at[row_index, "W_m"], frame.at[row_index, "B_m"])]
            width_center, thickness_center = centers[cluster_index]
            frame.at[row_index, "condition_group_id"] = (
                f"{material}|{specimen_type}|geometry-{cluster_index + 1:02d}"
            )
            frame.at[row_index, "condition_group_status"] = "geometry_condition_only"
            frame.at[row_index, "condition_group_W_center_m"] = width_center
            frame.at[row_index, "condition_group_B_center_m"] = thickness_center


def read_fracture_toughness_temperature(
    path: str | Path,
    *,
    temperature_unit_override: str | None = None,
    dimension_unit_override: str | None = None,
    apply_article_dimension_review: bool = True,
    condition_group_relative_tolerance: float = 0.03,
    condition_group_absolute_tolerance_m: float = 1e-4,
):
    """Read reported KJc observations while preserving the provider's train/test split.

    The workbook labels the temperature column ``K`` although the published cells include
    negative values. The associated article describes the model's tested-temperature feature
    and material temperature ranges in degrees Celsius, so the pinned source defaults to that
    independently reviewed interpretation. A caller may still supply an explicit ``degC`` or
    ``K`` override for a reviewed derivative workbook; invalid Kelvin values are rejected.
    W, B and a have no workbook-adjacent unit label. The article defines these dimensions,
    identifies T-size thicknesses in millimetres, and the complete workbook thickness scale
    matches those definitions. The reviewed default is therefore millimetres. A caller can
    disable that review or explicitly override a reviewed derivative workbook. Condition
    groups use material label, specimen type, W and B only as leakage-control strata. The
    source-specific 3% relative and 0.1 mm absolute defaults consolidate small reported
    nominal-geometry variations; they do not identify physical specimens or independent tests.
    """
    if temperature_unit_override not in {None, "degC", "K"}:
        raise ValueError("temperature_unit_override must be None, 'degC' or 'K'")
    if dimension_unit_override not in {None, "mm", "m"}:
        raise ValueError("dimension_unit_override must be None, 'mm' or 'm'")
    if not isinstance(apply_article_dimension_review, bool):
        raise TypeError("apply_article_dimension_review must be boolean")
    condition_group_relative_tolerance = _finite_number(
        condition_group_relative_tolerance, field="condition-group relative tolerance"
    )
    condition_group_absolute_tolerance_m = _finite_number(
        condition_group_absolute_tolerance_m, field="condition-group absolute tolerance"
    )
    if condition_group_relative_tolerance < 0 or condition_group_absolute_tolerance_m < 0:
        raise ValueError("condition-group tolerances must be nonnegative")

    import openpyxl
    import pandas as pd

    source = Path(path)
    archive_sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
    with zipfile.ZipFile(source) as archive:
        member = _workbook_member(archive)
        payload = archive.read(member)
    workbook = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=False, keep_links=False)
    if set(workbook.sheetnames) != set(SHEETS):
        raise ValueError("fracture-toughness workbook sheet names changed")

    records = []
    for sheet_name, partition in SHEETS.items():
        sheet = workbook[sheet_name]
        for coordinate, expected in EXPECTED_HEADERS.items():
            if sheet[coordinate].value != expected:
                raise ValueError(f"fracture-toughness header changed at {sheet_name}!{coordinate}")
        expected_record_id = 1
        for source_row, cells in enumerate(
            sheet.iter_rows(min_row=5, min_col=2, max_col=13, values_only=True), start=5
        ):
            if all(value is None for value in cells):
                break
            if any(value is None for value in cells):
                raise ValueError(f"partial fracture-toughness row at {sheet_name}!{source_row}")
            record_id = _finite_number(cells[0], field="reported record ID")
            if record_id != expected_record_id or not record_id.is_integer():
                raise ValueError(f"non-contiguous record ID at {sheet_name}!{source_row}")
            carbon_wt_percent = _finite_number(cells[1], field="carbon wt%")
            reported_temperature = _finite_number(cells[2], field="reported temperature")
            yield_strength_MPa = _finite_number(cells[3], field="yield strength")
            flags = tuple(_finite_number(value, field="specimen-type flag") for value in cells[4:7])
            if any(flag not in {0.0, 1.0} for flag in flags) or sum(flags) != 1:
                raise ValueError(f"specimen type must be one-hot at {sheet_name}!{source_row}")
            specimen_type = SPECIMEN_TYPES[flags.index(1.0)]
            dimensions = tuple(_finite_number(value, field="reported dimension") for value in cells[7:10])
            toughness_MPa_sqrt_m = _finite_number(cells[10], field="reported KJc")
            material_label = str(cells[11]).strip()
            if not material_label:
                raise ValueError(f"material label is empty at {sheet_name}!{source_row}")
            article_source_group = resolve_article_source_group(material_label, carbon_wt_percent)

            temperature_interpretation = temperature_unit_override or "article_degC"
            temperature_K = None
            if temperature_interpretation in {"degC", "article_degC"}:
                temperature_K = reported_temperature + 273.15
            elif temperature_interpretation == "K":
                temperature_K = reported_temperature
            if temperature_K is not None and temperature_K <= 0:
                raise ValueError("temperature interpretation produced a nonpositive absolute temperature")

            dimension_unit_basis = "unresolved"
            dimension_scale = None
            if dimension_unit_override == "mm":
                dimension_scale = 1e-3
                dimension_unit_basis = "override_mm"
            elif dimension_unit_override == "m":
                dimension_scale = 1.0
                dimension_unit_basis = "override_m"
            elif apply_article_dimension_review:
                dimension_scale = 1e-3
                dimension_unit_basis = "article_mm"
            normalized_dimensions = (
                (None, None, None)
                if dimension_scale is None
                else tuple(value * dimension_scale for value in dimensions)
            )
            records.append(
                {
                    "source_id": "fracture-toughness-temperature",
                    "source_partition": partition,
                    "source_sheet": sheet_name,
                    "source_row": source_row,
                    "reported_record_id": int(record_id),
                    "observation_id": f"{partition}:{int(record_id)}",
                    "material_label": material_label,
                    "carbon_wt_percent": carbon_wt_percent,
                    "carbon_mass_fraction": carbon_wt_percent / 100.0,
                    "reported_temperature": reported_temperature,
                    "reported_temperature_unit_label": "K",
                    "temperature_K": temperature_K,
                    "temperature_unit_override": temperature_unit_override,
                    "temperature_unit_basis": temperature_interpretation,
                    "yield_strength_MPa": yield_strength_MPa,
                    "yield_strength_Pa": yield_strength_MPa * 1e6,
                    "specimen_type": specimen_type,
                    "reported_CT_flag": int(flags[0]),
                    "reported_SEB_flag": int(flags[1]),
                    "reported_PCCv_flag": int(flags[2]),
                    "reported_W": dimensions[0],
                    "reported_B": dimensions[1],
                    "reported_a": dimensions[2],
                    "reported_dimension_unit_label": None,
                    "W_m": normalized_dimensions[0],
                    "B_m": normalized_dimensions[1],
                    "a_m": normalized_dimensions[2],
                    "dimension_unit_override": dimension_unit_override,
                    "dimension_unit_basis": dimension_unit_basis,
                    "reported_KJc_MPa_sqrt_m": toughness_MPa_sqrt_m,
                    "reported_KJc_Pa_sqrt_m": toughness_MPa_sqrt_m * 1e6,
                    "physical_specimen_id": None,
                    "underlying_literature_id": None,
                    **article_source_group,
                }
            )
            expected_record_id += 1

    frame = pd.DataFrame.from_records(records)
    if frame.empty or not frame.observation_id.is_unique:
        raise ValueError("fracture-toughness observations must have unique partition-local identities")
    _assign_condition_groups(
        frame,
        relative_tolerance=condition_group_relative_tolerance,
        absolute_tolerance_m=condition_group_absolute_tolerance_m,
    )
    frame.attrs.update(
        source_id="fracture-toughness-temperature",
        source_doi="10.17632/2vkgrbsy8j.1",
        source_archive_sha256=archive_sha256,
        source_member=member,
        source_member_sha256=hashlib.sha256(payload).hexdigest(),
        license_id="CC-BY-4.0",
        workbook_formula_execution=False,
        temperature_basis=(
            "workbook label K conflicts with negative values; associated article DOI "
            "10.1016/j.engfailanal.2020.104458 describes the tested-temperature feature and "
            "material ranges in degrees Celsius, which is the default reviewed interpretation"
        ),
        temperature_source_doi=ARTICLE_DOI,
        source_group_basis=(
            "article-local material/reference groups from the associated article table; these labels "
            "do not establish row-level literature identity, specimen identity or reuse permission"
        ),
        reference_catalog_basis=(
            "bibliographic identifiers resolve article-local references where a persistent identifier was "
            "verified; publication licenses and underlying-observation redistribution rights remain separate"
        ),
        dimension_basis=(
            "source workbook has no adjacent unit label for W, B and a; the associated article defines "
            "the dimensions and T-size thicknesses in millimetres, and all workbook thicknesses match "
            "that scale; callers can disable the article review or override a reviewed derivative workbook"
        ),
        observation_identity=(
            "partition-local table row only; no physical specimen identifier or underlying-literature "
            "row mapping is supplied"
        ),
        condition_group_basis=(
            "material label, specimen type and reviewed SI width/thickness tolerance cluster; groups are "
            "source-specific leakage-control strata, not physical specimen identities"
        ),
        condition_group_relative_tolerance=condition_group_relative_tolerance,
        condition_group_absolute_tolerance_m=condition_group_absolute_tolerance_m,
        limitations=[
            "Training and test partitions are preserved and are not relabeled as independent specimens.",
            "Geometry condition groups occur across provider partitions and are leakage-control strata, not evidence of independent train/test specimens.",
            "The workbook temperature label conflicts with the associated article; both the source label and the reviewed interpretation remain explicit.",
            "Reported KJc is retained as a compiled value; this reader does not decide test validity or convert it into a service lower bound.",
            "Dataset-level licensing does not resolve redistribution rights for each underlying literature observation.",
            "Article-local source groups are screening links only; probable variants and unresolved labels require primary-source review.",
            "No source formula, model prediction, standard acceptance rule or FAD boundary is executed or reconstructed.",
        ],
    )
    return frame
