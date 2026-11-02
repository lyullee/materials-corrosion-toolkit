"""Import caller-authored grouped specimen summaries from JSONL without unit conversion."""

from pathlib import Path

from matintegrity.models.corrosion import CorrosionRateObservation, CorrosionRateSampleSummary
from matintegrity.tabular_contract_import import (
    TabularImportProfile,
    TabularImportReport,
    read_csv_contracts,
    read_jsonl_contracts,
)

PROFILE_PATH = Path(__file__).with_name("corrosion_rate_sample_import_profile.json")
OBSERVATION_CSV_PROFILE_PATH = Path(__file__).with_name("corrosion_rate_observation_csv_profile.json")


def import_corrosion_rate_samples(
    jsonl_path: str | Path,
) -> tuple[tuple[CorrosionRateSampleSummary, ...], TabularImportReport]:
    """Read one complete sample group per JSONL line; caller supplies source provenance and units."""

    profile = TabularImportProfile.model_validate_json(PROFILE_PATH.read_text(encoding="utf-8"))
    return read_jsonl_contracts(jsonl_path, CorrosionRateSampleSummary, profile)


def import_corrosion_rate_observations_csv(
    csv_path: str | Path,
) -> tuple[tuple[CorrosionRateObservation, ...], TabularImportReport]:
    """Read one user-mapped specimen rate per CSV row; no grouping or unit conversion is inferred."""

    profile = TabularImportProfile.model_validate_json(
        OBSERVATION_CSV_PROFILE_PATH.read_text(encoding="utf-8")
    )
    return read_csv_contracts(csv_path, CorrosionRateObservation, profile)
