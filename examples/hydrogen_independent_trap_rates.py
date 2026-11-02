"""Synthetic independent capture/release histories; no material calibration is claimed."""

import copy
import json

from hydrogen_slab import EVIDENCE, INPUTS

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

payload = copy.deepcopy(INPUTS)
payload["detailed_balance_rate_ratio_reviewed"] = False
payload["traps"][0].update(
    rate_model="independent_frequencies",
    release_frequency_per_s=[0.1, 0.1, 0.2, 0.3],
    independent_rate_histories_reviewed=True,
    rate_evidence=[EVIDENCE],
)

if __name__ == "__main__":
    result = default_registry().run_json(
        "transport.hydrogen_slab_kinetic",
        json.dumps(payload),
        RunContext(
            asset_id="synthetic-slab",
            location_id="wall",
            time_basis="elapsed from synthetic charging start",
        ),
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "trap_rates": [
                    {
                        "trap_id": trap["trap_id"],
                        "rate_model": trap["rate_model"],
                        "rate_history_digest": trap["rate_history_digest"],
                    }
                    for trap in result.values.get("traps", [])
                ],
                "mass_error": result.values.get("relative_mass_balance_error"),
            },
            indent=2,
        )
    )
