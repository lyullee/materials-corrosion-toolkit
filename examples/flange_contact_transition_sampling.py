"""Wire caller-reviewed time sampling into the synthetic flange gasket example."""

import json
from pathlib import Path

from matintegrity.models.flange_nonlinear_viscoelastic import (
    FlangeNonlinearViscoelasticContactHistory,
    flange_nonlinear_viscoelastic_contact_history,
)


fixture = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))
raw = fixture["models"]["fabrication.flange_nonlinear_viscoelastic_contact_history"]
request = FlangeNonlinearViscoelasticContactHistory.model_validate(
    raw
    | {
        "maximum_contact_transition_step_s": 600.0,
        "contact_transition_time_sampling_reviewed": True,
        "contact_transition_time_tolerance_s": 1e-3,
        "single_contact_transition_per_refined_interval_reviewed": True,
        "maximum_transition_refinement_solves": 100,
        "maximum_transition_refinement_work_units": 50_000_000,
    }
)
result = flange_nonlinear_viscoelastic_contact_history(request)
print(result.model_dump(mode="json"))
