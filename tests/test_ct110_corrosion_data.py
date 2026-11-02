import pytest

from matintegrity.ct110_data import read_ct110_weld_corrosion_dataset
from matintegrity.models.corrosion import MaterialCorrosionRateContrast


def test_bundled_ct110_dataset_is_typed_attributed_and_si_ready():
    dataset = read_ct110_weld_corrosion_dataset()
    assert dataset.source.license == "CC BY 4.0"
    assert len(dataset.observations) == 6
    assert dataset.physical_specimen_ids_available is False
    assert dataset.replicate_counts_available is False
    assert dataset.uncertainty_available is False
    contrast = dataset.contrast_input("temperature-60-C")
    assert isinstance(contrast, MaterialCorrosionRateContrast)
    assert contrast.numerator_material_id == "CT110-weld-metal"
    assert contrast.reference_material_id == "CT110-base-metal"
    assert contrast.condition_signature["temperature_C"] == 60
    assert contrast.source_group_id == dataset.source_group_id


def test_unknown_ct110_comparison_id_is_not_silently_substituted():
    dataset = read_ct110_weld_corrosion_dataset()
    with pytest.raises(KeyError, match="not-a-provider-row"):
        dataset.contrast_input("not-a-provider-row")
