"""Independent focused checks for the crevice, finite-plane GSA and DEIS APIs.

Execute on an isolated compute-node snapshot. Raw DEIS acquisition goes to a
separate private directory, never to this source tree or the result records.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import urllib.request
import zipfile

from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.models.crevice_kinetic_network import (
    CreviceAqueousKineticNetwork,
    CreviceKineticInterval,
    CreviceKineticReaction,
    CreviceKineticSpecies,
    CreviceKineticTerm,
    solve_crevice_aqueous_kinetic_network,
)
from matintegrity.models.ince_glinka_gsa import InceGlinkaGSACalculation, ince_glinka_gsa_parameter
from matintegrity.zenodo_deis_import import (
    ARCHIVE_BYTES,
    ARCHIVE_SHA256,
    DEIS_MEMBERS,
    EXPECTED_MATRIX_SHAPE,
    EXPECTED_MEMBERS,
    DeisMatrixMember,
    ZenodoDeisArchiveAuditRequest,
    ZenodoDeisArchiveManifest,
    audit_zenodo_deis_archive_request,
    inspect_zenodo_deis_archive,
    iter_zenodo_deis_rows,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODEL_IDS = (
    "chemistry.crevice_aqueous_kinetic_network",
    "fatigue.ince_glinka_generalized_strain_amplitude",
    "data.zenodo_deis_archive_structure",
)
SOURCE_PATHS = (
    "src/matintegrity/models/crevice_kinetic_network.py",
    "src/matintegrity/models/ince_glinka_gsa.py",
    "src/matintegrity/zenodo_deis_import.py",
)
CONTRACTS = (
    CreviceAqueousKineticNetwork, CreviceKineticInterval, CreviceKineticReaction,
    CreviceKineticSpecies, CreviceKineticTerm, InceGlinkaGSACalculation,
    DeisMatrixMember, ZenodoDeisArchiveAuditRequest, ZenodoDeisArchiveManifest,
)


def crevice_checks():
    import numpy as np
    from scipy.linalg import expm

    evidence = {"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated numerical conservation cases.", "sha256": "c" * 64, "license_id": "CC0-1.0"}
    base = {
        "assessment_id": "synthetic-kinetic", "asset_id": "synthetic-asset",
        "physical_scope_id": "synthetic-mixed-volume", "clock_id": "synthetic-seconds",
        "control_volume_m3": 1.0,
        "species": [{"species_id": name, "charge_number": 0, "elemental_composition": {"X": 1.0}, "initial_concentration_mol_m3": initial} for name, initial in (("A", 2.0), ("B", 0.5))],
        "maximum_step_s": 0.1, "relative_tolerance": 1e-10, "absolute_tolerance_mol_m3": 1e-12,
        "temperature_support_min_K": 290.0, "temperature_support_max_K": 310.0,
        "model_provider_id": "synthetic", "model_revision": "1", "evidence": [evidence], "usage_rights_evidence": [evidence],
        "reaction_network_and_conservation_reviewed": True, "kinetic_parameter_units_and_calibration_reviewed": True,
        "mixed_volume_and_exchange_boundary_reviewed": True, "temperature_knot_mapping_and_parameter_support_reviewed": True,
        "usage_rights_reviewed": True, "computational_use_authorized": True,
    }
    cases = []
    for solver in ("BDF", "Radau"):
        for factor in (0.0, 1.0, 25.0):
            forward, reverse = [factor * 2.0, factor * 0.1], [factor * 0.5, factor * 0.03]
            intervals = [{"interval_id": "i0", "start_time_s": 0.0, "end_time_s": 3.0, "temperature_K": 300.0, "exchange_flow_m3_s": 0.2, "bulk_concentration_mol_m3_by_species": {"A": 1.0, "B": 3.0}},
                         {"interval_id": "i1", "start_time_s": 3.0, "end_time_s": 7.0, "temperature_K": 300.0, "exchange_flow_m3_s": 0.8, "bulk_concentration_mol_m3_by_species": {"A": 2.0, "B": 1.0}}]
            reactions = [{"reaction_id": "A-to-B", "reactants": [{"species_id": "A", "stoichiometric_coefficient": 1}], "products": [{"species_id": "B", "stoichiometric_coefficient": 1}], "forward_rate_constant_by_interval": forward, "reverse_rate_constant_by_interval": reverse, "forward_rate_constant_units": "1/s", "reverse_rate_constant_units": "1/s"}]
            payload = base | {"solver_method": solver, "intervals": intervals, "reactions": reactions}
            result = solve_crevice_aqueous_kinetic_network(CreviceAqueousKineticNetwork.model_validate_json(json.dumps(payload)))
            assert result.status == "computed" and result.values["full_requested_history_completed"], result.model_dump(mode="json")
            reference = np.array([2.0, 0.5, 0.0, 0.0, 0.0, 1.0])
            errors = []
            for index, (interval, row) in enumerate(zip(intervals, result.values["history"], strict=True)):
                kf, kr, exchange = forward[index], reverse[index], interval["exchange_flow_m3_s"]
                ba, bb = interval["bulk_concentration_mol_m3_by_species"].values()
                matrix = np.zeros((6, 6))
                matrix[0, [0, 1, 5]] = [-kf-exchange, kr, exchange*ba]
                matrix[1, [0, 1, 5]] = [kf, -kr-exchange, exchange*bb]
                matrix[2, [0, 5]] = [-exchange, exchange*ba]
                matrix[3, [1, 5]] = [-exchange, exchange*bb]
                matrix[4, [0, 1]] = [kf, -kr]
                previous = reference.copy()
                reference = expm(matrix * (interval["end_time_s"]-interval["start_time_s"])) @ reference
                actual = [row["concentration_mol_m3_by_species"][key] for key in ("A", "B")]
                actual += [row["net_exchange_mol_m3_by_species"][key] for key in ("A", "B")]
                actual += [row["reaction_extent_mol_m3_by_reaction"]["A-to-B"]]
                expected = np.concatenate((reference[:2], reference[2:5]-previous[2:5]))
                assert np.allclose(actual, expected, rtol=3e-7, atol=2e-9), (solver, factor, actual, expected.tolist())
                errors.append(float(np.max(np.abs(np.asarray(actual)-expected))))
            assert max(abs(value) for value in result.values["species_inventory_closure_residual_mol_m3"].values()) < 2e-8
            cases.append({"solver": solver, "rate_multiplier": factor, "maximum_interval_errors": errors})
    payload["reaction_network_and_conservation_reviewed"] = False
    assert solve_crevice_aqueous_kinetic_network(CreviceAqueousKineticNetwork.model_validate_json(json.dumps(payload))).status == "needs_data"
    return {"independent_reference": "augmented linear matrix exponential, including exchange and reaction ledgers", "cases": cases, "review_gate": True}


def gsa_checks():
    import numpy as np

    def tensor_matrix(row):
        xx, yy, zz, xy, yz, zx = row
        return np.array([[xx, xy, zx], [xy, yy, yz], [zx, yz, zz]], dtype=float)
    def tensor_components(matrix):
        return [float(matrix[0, 0]), float(matrix[1, 1]), float(matrix[2, 2]), float(matrix[0, 1]), float(matrix[1, 2]), float(matrix[2, 0])]
    q = math.sqrt(0.5)
    planes = [{"plane_id": "x", "normal": [1.0, 0.0, 0.0], "in_plane_direction": [0.0, 1.0, 0.0]},
              {"plane_id": "diag", "normal": [q, q, 0.0], "in_plane_direction": [-q, q, 0.0]},
              {"plane_id": "z", "normal": [0.0, 0.0, 1.0], "in_plane_direction": [1.0, 0.0, 0.0]}]
    stress = [[100e6, 20e6, -5e6, 30e6, 5e6, 0.0], [-100e6, -10e6, 5e6, -30e6, -5e6, 0.0], [100e6, 20e6, -5e6, 30e6, 5e6, 0.0]]
    elastic = [[0.001, -0.0002, 0.0, 0.002, 0.0001, 0.0], [-0.001, 0.0002, 0.0, -0.002, -0.0001, 0.0], [0.001, -0.0002, 0.0, 0.002, 0.0001, 0.0]]
    plastic = [[0.0002, -0.0001, 0.0, 0.0003, 0.00005, 0.0], [-0.0002, 0.0001, 0.0, -0.0003, -0.00005, 0.0], [0.0002, -0.0001, 0.0, 0.0003, 0.00005, 0.0]]
    payload = {"assessment_id": "synthetic-gsa", "physical_scope_id": "synthetic-only", "material_condition_id": "synthetic-material", "location_id": "synthetic-location", "source_provider_id": "synthetic", "source_provider_revision": "1", "configuration_sha256": "d"*64, "sample_ids": ["s0", "s1", "s2"], "stress_tensor_components_Pa": stress, "elastic_strain_tensor_components": elastic, "plastic_strain_tensor_components": plastic, "candidate_planes": planes, "shear_fatigue_strength_coefficient_Pa": 100e6, "axial_fatigue_strength_coefficient_Pa": 200e6, "maximum_stress_closure_error_Pa": 0.0, "maximum_elastic_strain_closure_error": 0.0, "maximum_plastic_strain_closure_error": 0.0, "representative_cycle_and_tensor_convention_reviewed": True, "elastic_plastic_decomposition_reviewed": True, "plane_grid_support_reviewed": True, "material_parameter_basis_and_units_reviewed": True, "source_use_rights_reviewed": True, "computational_use_authorized": True, "evidence": [{"source_id": "synthetic", "origin": "synthetic", "citation": "Fabricated finite-plane tensor checks."}]}
    result = ince_glinka_gsa_parameter(InceGlinkaGSACalculation.model_validate_json(json.dumps(payload)))
    assert result.status == "computed"
    expected = {}
    matrices = [np.asarray([tensor_matrix(row) for row in history]) for history in (stress, elastic, plastic)]
    for plane in planes:
        normal, direction = np.asarray(plane["normal"]), np.asarray(plane["in_plane_direction"])
        sn = np.einsum("i,tij,j->t", normal, matrices[0], normal)
        tau = np.einsum("i,tij,j->t", direction, matrices[0], normal)
        en = [np.einsum("i,tij,j->t", normal, array, normal) for array in matrices[1:]]
        shear = [2*np.einsum("i,tij,j->t", direction, array, normal) for array in matrices[1:]]
        amplitude = lambda values: float(np.ptp(values))*0.5
        expected[plane["plane_id"]] = float(np.max(np.abs(tau)))/100e6*amplitude(shear[0])+amplitude(shear[1])+float(np.max(sn))/200e6*amplitude(en[0])+amplitude(en[1])
    for row in result.values["candidate_planes"]:
        assert math.isclose(row["gsa_parameter"], expected[row["plane_id"]], rel_tol=1e-12, abs_tol=1e-15)
    assert math.isclose(result.values["maximum_gsa_parameter"], max(expected.values()), rel_tol=1e-12)
    rotation = np.array([[q, -q, 0.0], [q, q, 0.0], [0.0, 0.0, 1.0]])
    rotated = json.loads(json.dumps(payload))
    for key, array in zip(("stress_tensor_components_Pa", "elastic_strain_tensor_components", "plastic_strain_tensor_components"), matrices, strict=True):
        rotated[key] = [tensor_components(rotation @ row @ rotation.T) for row in array]
    for plane in rotated["candidate_planes"]:
        plane["normal"] = (rotation @ np.asarray(plane["normal"])).tolist()
        plane["in_plane_direction"] = (rotation @ np.asarray(plane["in_plane_direction"])).tolist()
    transformed = ince_glinka_gsa_parameter(InceGlinkaGSACalculation.model_validate_json(json.dumps(rotated)))
    assert transformed.status == "computed"
    for row in transformed.values["candidate_planes"]:
        assert math.isclose(row["gsa_parameter"], expected[row["plane_id"]], rel_tol=1e-12, abs_tol=1e-15)
    analytic_cases = []
    for name, component, stress_amp, elastic_amp, plastic_amp, expected_parameter in (
        ("pure-axial", 0, 100e6, 0.001, 0.0002, 0.0007),
        ("pure-tensor-shear", 3, 50e6, 0.002, 0.0003, 0.0026),
    ):
        simple = json.loads(json.dumps(payload))
        simple["candidate_planes"] = [planes[0]]
        for key, amplitude in (("stress_tensor_components_Pa", stress_amp), ("elastic_strain_tensor_components", elastic_amp), ("plastic_strain_tensor_components", plastic_amp)):
            simple[key] = []
            for sign in (1.0, -1.0, 1.0):
                tensor = [0.0]*6
                tensor[component] = sign*amplitude
                simple[key].append(tensor)
        simple_result = ince_glinka_gsa_parameter(InceGlinkaGSACalculation.model_validate_json(json.dumps(simple)))
        assert simple_result.status == "computed"
        assert math.isclose(simple_result.values["maximum_gsa_parameter"], expected_parameter, rel_tol=1e-12)
        analytic_cases.append({"case": name, "expected_parameter": expected_parameter})
    over_budget = json.loads(json.dumps(payload))
    over_budget["maximum_plane_sample_evaluations"] = len(planes)*len(payload["sample_ids"]) - 1
    try:
        InceGlinkaGSACalculation.model_validate_json(json.dumps(over_budget))
    except ValidationError:
        pass
    else:
        raise AssertionError("plane/sample workload budget was not enforced")
    payload["stress_tensor_components_Pa"][-1][0] += 1.0
    unclosed = ince_glinka_gsa_parameter(InceGlinkaGSACalculation.model_validate_json(json.dumps(payload)))
    assert unclosed.status == "needs_data"
    return {"finite_plane_expected_parameters": expected, "rotation_invariance": True, "analytic_cases": analytic_cases,
            "plane_sample_budget_rejection": True, "unclosed_cycle_rejected": True, "life_or_acceptance_validation": False}


def deis_checks():
    catalog = json.loads((ROOT / "data/catalogs/datasets.json").read_text(encoding="utf-8"))
    dataset = next(row for row in catalog["datasets"] if row["id"] == "az-we43-az31-molybdate-eis")
    assert dataset["license"] == "CC0-1.0" and dataset["acquisition_policy"] == "allowed"
    asset = next(row for row in dataset["assets"] if row["filename"] == "Dataset_CorSci.zip")
    assert asset["bytes"] == ARCHIVE_BYTES and asset["max_bytes"] == ARCHIVE_BYTES
    assert asset["url"] == "https://zenodo.org/api/records/10482561/files/Dataset_CorSci.zip/content"
    private = Path(os.environ["MATINTEGRITY_PRIVATE_DATA"]).resolve()
    assert not private.is_relative_to(ROOT.resolve()), "raw acquisition directory must be outside the source snapshot"
    private.mkdir(parents=True, exist_ok=True)
    path = private / "Dataset_CorSci.zip"
    if not path.exists():
        temporary = private / "Dataset_CorSci.download-part"
        count = 0
        request = urllib.request.Request(asset["url"], headers={"User-Agent": "matintegrity-pinned-cc0-validation/1"})
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            while chunk := response.read(1024*1024):
                count += len(chunk)
                if count > ARCHIVE_BYTES:
                    raise ValueError("provider asset exceeds pinned byte budget")
                output.write(chunk)
        assert count == ARCHIVE_BYTES
        temporary.replace(path)
    raw_archive = path.read_bytes()
    assert len(raw_archive) == ARCHIVE_BYTES and hashlib.sha256(raw_archive).hexdigest() == ARCHIVE_SHA256
    assert "md5:" + hashlib.md5(raw_archive, usedforsecurity=False).hexdigest() == asset["checksum"]
    manifest = inspect_zenodo_deis_archive(path)
    restored = ZenodoDeisArchiveManifest.model_validate_json(manifest.model_dump_json())
    assert restored == manifest
    audits = []
    with zipfile.ZipFile(path) as archive:
        assert set(archive.namelist()) == EXPECTED_MEMBERS
        for member in manifest.matrices:
            raw = archive.read(member.member_path)
            assert hashlib.sha256(raw).hexdigest() == member.member_sha256
            reference_rows = raw.decode("utf-8-sig").splitlines()
            assert len(reference_rows) == EXPECTED_MATRIX_SHAPE[0]
            numeric_hash = hashlib.sha256()
            row_count = 0
            for index, row in enumerate(iter_zenodo_deis_rows(path, manifest, member.member_path)):
                reference = tuple(float(token) for token in reference_rows[index].split("\t"))
                assert len(reference) == EXPECTED_MATRIX_SHAPE[1] and row == reference
                assert all(math.isfinite(value) for value in row)
                numeric_hash.update(struct.pack("<" + str(len(row)) + "d", *row))
                row_count += 1
            assert row_count == member.row_count
            audits.append({"member": member.member_path, "member_sha256": member.member_sha256,
                           "rows": row_count, "columns": member.column_count, "ordered_float64_stream_sha256": numeric_hash.hexdigest()})
    forged = manifest.model_dump(mode="json")
    forged["matrices"][0]["row_count"] -= 1
    try:
        next(iter_zenodo_deis_rows(path, ZenodoDeisArchiveManifest.model_validate_json(json.dumps(forged)), next(iter(DEIS_MEMBERS))))
    except ValueError:
        pass
    else:
        raise AssertionError("forged member manifest accepted")
    request = ZenodoDeisArchiveAuditRequest(assessment_id="pinned-cc0-structure", local_archive_path=str(path), local_only_archive_path_reviewed=True, cc0_dataset_reuse_basis_reviewed=True, computational_use_authorized=True)
    result = audit_zenodo_deis_archive_request(request)
    assert result.status == "computed" and result.values["raw_measurements_returned"] is False
    return {"archive_sha256": ARCHIVE_SHA256, "archive_bytes": ARCHIVE_BYTES, "dataset_license_id": "CC0-1.0",
            "member_count": len(EXPECTED_MEMBERS), "matrix_streams": audits, "forged_manifest_rejected": True,
            "raw_measurements_exported": False, "axes_units_or_physical_validity_inferred": False}


def schema_checks():
    records = []
    for contract in CONTRACTS:
        actual = json.loads((ROOT / "docs/schemas" / (contract.__name__ + ".json")).read_text(encoding="utf-8"))
        assert actual == contract.model_json_schema(), contract.__name__
        records.append({"contract": contract.__name__, "schema_sha256": canonical_digest(actual)})
    return {"contracts": records}


def catalog_checks():
    from matintegrity.registry import default_registry
    registry = default_registry()
    catalog = json.loads((ROOT / "data/catalogs/capabilities.json").read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in catalog["capabilities"]}
    sources = json.loads((ROOT / "data/catalogs/sources.json").read_text(encoding="utf-8"))
    source_ids = {row["id"] for row in sources["sources"]}
    records = []
    for identifier in MODEL_IDS:
        assert identifier in registry.list_models() and identifier in rows
        description = registry.describe(identifier)
        assert description["input_schema"] == rows[identifier]["input_schema"]
        for source in rows[identifier]["source_ids"]:
            assert source in source_ids, (identifier, source)
        parents = [row["id"] for row in rows.values() if row["id"] != identifier and identifier in json.dumps(row)]
        assert parents, identifier
        records.append({"model_id": identifier, "parent_capabilities": parents, "source_ids": rows[identifier]["source_ids"]})
    for name in ("capabilities", "datasets", "sources"):
        assert (ROOT / "data/catalogs" / (name + ".json")).read_bytes() == (ROOT / "src/matintegrity/catalog_data" / (name + ".json")).read_bytes()
    return {"models": records, "package_catalog_sync": True}


def source_checks():
    from scripts.hpc_run_task import source_tree_digest
    for name in SOURCE_PATHS:
        ast.parse((ROOT / name).read_text(encoding="utf-8"), filename=name)
    digest, count = source_tree_digest(ROOT)
    assert not (ROOT / "data/raw/az-we43-az31-molybdate-eis/Dataset_CorSci.zip").exists()
    return {"source_tree_sha256": digest, "source_file_count": count, "ast_paths": SOURCE_PATHS, "raw_archive_absent_from_source": True}


def main():
    tasks = {"crevice": crevice_checks, "gsa": gsa_checks, "deis": deis_checks,
             "schemas": schema_checks, "catalog": catalog_checks, "source": source_checks}
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=tasks, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        details = tasks[args.task]()
    except Exception as exc:
        args.output.write_text(json.dumps({"task": args.task, "status": "failed", "exception_type": type(exc).__name__, "message": str(exc)}, indent=2), encoding="utf-8")
        raise
    args.output.write_text(json.dumps({"task": args.task, "status": "passed", "details": details,
        "meaning": "limited numerical/software/archive-contract checks; no independent physical qualification"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
