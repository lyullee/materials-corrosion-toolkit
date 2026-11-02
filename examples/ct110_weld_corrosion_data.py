"""Run a cited bundled CT110 weld/base descriptive contrast through the registry."""

from matintegrity.contracts import Evidence, RunContext
from matintegrity.ct110_data import read_ct110_weld_corrosion_dataset
from matintegrity.registry import default_registry

dataset = read_ct110_weld_corrosion_dataset()
comparison_id = "temperature-60-C"
observation = next(row for row in dataset.observations if row.comparison_id == comparison_id)
provider_file = dataset.source.provider_files[0]
result = default_registry().run(
    "corrosion.material_rate_contrast",
    dataset.contrast_input(comparison_id),
    RunContext(
        asset_id="CT110-literature-example",
        location_id=observation.condition_group_id,
        time_basis="reported 96 h exposure",
        evidence=(
            Evidence(
                source_id="ct110_weld_corrosion_supplement",
                origin="open_dataset",
                citation=dataset.source.attribution,
                license_id="CC-BY-4.0",
                sha256=provider_file.sha256,
            ),
        ),
    ),
)
print(result.model_dump_json(indent=2))
