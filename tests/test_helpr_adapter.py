import hashlib

import pytest
from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.helpr_adapter import HelprLifeCriteriaRecord, read_helpr_life_criteria_csv

REVISION = "ae12d20b6608123af41dd9d5f70db6b6547fece5"
HEADER = "a(crit),Cycles to a(crit),Cycles to 25% a(crit),Cycles to 1/2 Nc,Cycles to FAD line\n"


def read(path, **overrides):
    arguments = {
        "provider_version": "2.1.0",
        "provider_revision": REVISION,
        "analysis_id": "authored-analysis",
        "study_type": "nominal",
        "asset_id": "synthetic-pipe",
        "location_id": "synthetic-longitudinal-flaw",
        "material_condition_id": "synthetic-steel",
        "load_case_id": "synthetic-pressure-cycle",
        "sample_ids": ["nominal"],
        "provider_configuration_digest": "b" * 64,
        "units_reviewed": True,
        "missing_value_semantics": "blank or NaN is retained as unavailable or not reached pending review",
        "provider_a_crit_interpretation": "provider field retained without physical qualification",
        "provider_run_warning_codes": (),
        "provider_run_warnings_reviewed": True,
    }
    return read_helpr_life_criteria_csv(path, **(arguments | overrides))


def test_nominal_life_criteria_are_mapped_with_provider_and_asset_identity(tmp_path):
    source = tmp_path / "nominal_life_criteria.csv"
    source.write_text(HEADER + "0.008,12000,3000,6000,9000\n", encoding="utf-8")
    (record,) = read(source)
    assert record.provider_reported_a_crit_m == 0.008
    assert record.provider_reported_cycles_to_a_crit == 12000
    assert record.provider_reported_cycles_to_fad_line == 9000
    assert record.provider_revision == REVISION
    assert record.asset_id == "synthetic-pipe"
    assert record.sample_id == "nominal"
    assert record.source_content_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()
    assert record.endpoint_semantics == "model_criterion_not_observed_failure"
    assert record.probability_semantics == "none"


def test_probabilistic_rows_require_explicit_unique_sample_ids_and_preserve_missing(tmp_path):
    source = tmp_path / "probabilistic_life_criteria.csv"
    source.write_text(HEADER + "0.008,12000,3000,6000,9000\n0.009,nan,4000,,10000\n", encoding="utf-8")
    records = read(
        source,
        study_type="probabilistic",
        sample_ids=["sample-000", "sample-001"],
    )
    assert records[1].provider_reported_a_crit_m == 0.009
    assert records[1].provider_reported_cycles_to_a_crit is None
    assert records[1].provider_reported_cycles_to_half_nc is None
    assert records[1].provider_reported_cycles_to_fad_line == 10000


@pytest.mark.parametrize(
    "body",
    [
        "a(crit),Cycles to FAD line\n0.008,9000\n",
        HEADER + "0.008,-1,3000,6000,9000\n",
        HEADER + "0.008,inf,3000,6000,9000\n",
        HEADER,
    ],
)
def test_unknown_schema_empty_rows_and_invalid_values_are_rejected(tmp_path, body):
    source = tmp_path / "bad.csv"
    source.write_text(body, encoding="utf-8")
    with pytest.raises(ValueError):
        read(source)


def test_row_identity_is_never_inferred_from_position(tmp_path):
    source = tmp_path / "probabilistic_life_criteria.csv"
    source.write_text(HEADER + "0.008,1,1,1,1\n0.009,2,2,2,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="one-to-one"):
        read(source, study_type="probabilistic", sample_ids=["only-one"])
    with pytest.raises(ValueError, match="unique"):
        read(source, study_type="probabilistic", sample_ids=["same", "same"])


def test_nominal_output_cannot_silently_accept_multiple_rows(tmp_path):
    source = tmp_path / "nominal_life_criteria.csv"
    source.write_text(HEADER + "0.008,1,1,1,1\n0.009,2,2,2,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        read(source, sample_ids=["one", "two"])


def test_contract_is_strict_and_configuration_changes_record_digest(tmp_path):
    source = tmp_path / "nominal_life_criteria.csv"
    source.write_text(HEADER + "0.008,12000,3000,6000,9000\n", encoding="utf-8")
    (first,) = read(source)
    (second,) = read(source, provider_configuration_digest="c" * 64)
    assert canonical_digest(first.model_dump(mode="json")) != canonical_digest(second.model_dump(mode="json"))
    with pytest.raises(ValidationError):
        HelprLifeCriteriaRecord(**(first.model_dump() | {"unexpected": "field"}))


def test_warning_review_is_required_and_changes_record_digest(tmp_path):
    source = tmp_path / "nominal_life_criteria.csv"
    source.write_text(HEADER + "0.008,12000,3000,6000,9000\n", encoding="utf-8")
    (without_warning,) = read(source)
    (with_warning,) = read(
        source,
        provider_run_warning_codes=("provider_internal_bool_bitwise_inversion_deprecated",),
        provider_a_crit_interpretation="provider field retained after warning review",
    )
    assert with_warning.provider_run_warning_codes == ("provider_internal_bool_bitwise_inversion_deprecated",)
    assert canonical_digest(without_warning.model_dump(mode="json")) != canonical_digest(
        with_warning.model_dump(mode="json")
    )
    with pytest.raises(ValidationError):
        read(source, provider_run_warnings_reviewed=False)
