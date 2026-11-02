"""Show reviewed time-varying caller flange compliance on a synthetic fixture."""

import json
from pathlib import Path

from matintegrity.models.flange_nonlinear_viscoelastic import (
    FlangeNonlinearViscoelasticContactHistory,
    flange_nonlinear_viscoelastic_contact_history,
)

fixture = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))
raw = fixture["models"]["fabrication.flange_nonlinear_viscoelastic_contact_history"]
base = raw["flange_relative_compliance_matrix_m_N"]
factors = tuple(1.0 + 0.1 * index for index in range(len(raw["times_s"])))
compliance_history = tuple(
    tuple(tuple(factor * value for value in row) for row in base)
    for factor in factors
)
request = FlangeNonlinearViscoelasticContactHistory.model_validate(
    raw
    | {
        "flange_relative_compliance_history_m_N": compliance_history,
        "compliance_history_interpolation_reviewed": True,
    }
)
result = flange_nonlinear_viscoelastic_contact_history(request)
print(result.model_dump(mode="json"))
