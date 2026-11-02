"""Show local implicit sensitivities for a project-authored synthetic network."""

import json
from pathlib import Path

from matintegrity.models.aqueous_mass_action import (
    AqueousMassActionSystem,
    aqueous_mass_action_speciation,
)


root = Path(__file__).resolve().parents[1]
all_inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
system = AqueousMassActionSystem.model_validate(
    all_inputs["models"]["chemistry.aqueous_mass_action_speciation"]
)
payload = system.model_dump(mode="python")
parameter_count = len(system.reactions) + len(system.constraints) + len(system.species)
payload["local_parameter_covariance"] = tuple(
    tuple(1e-8 if row == column else 0.0 for column in range(parameter_count))
    for row in range(parameter_count)
)
payload["local_parameter_covariance_reviewed"] = True
system = AqueousMassActionSystem.model_validate(payload)
result = aqueous_mass_action_speciation(system)

print("status:", result.status)
print("input digest:", result.values.get("input_digest"))
print("sensitivity status:", result.values.get("local_sensitivity_status"))
sensitivities = result.values.get("local_sensitivities")
if sensitivities is not None:
    for species in sensitivities["species"]:
        print(species["species_id"], species["d_ln_concentration_d_parameter"])
print("first-order covariance status:", result.values["local_sensitivity_covariance"]["status"])

