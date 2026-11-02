"""Synthetic wiring for location-wise B-dot coefficients in restricted transport."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from matintegrity import build_bdot_transport_activity_callback
from matintegrity.models.aqueous_activity_iteration import AqueousBdotIteration


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "examples" / "model_inputs.json"
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    request = AqueousBdotIteration.model_validate(
        payload["models"]["chemistry.aqueous_bdot_self_consistent_speciation"]
    )
    species_ids = tuple(row.species_id for row in request.system.species)
    callback = build_bdot_transport_activity_callback(
        request,
        transport_species_ids=species_ids,
        temperature_K=request.system.temperature_K,
    )

    # Fabricated concentrations only illustrate the callback's species × location shape.
    concentrations_mol_m3 = np.zeros((len(species_ids), 2), dtype=float)
    gamma_m = callback(0.0, concentrations_mol_m3)
    print({
        "provider_id": callback.provider_id,
        "configuration_sha256": callback.configuration_sha256,
        "species_ids": callback.species_ids,
        "gamma_m_species_by_location": gamma_m.tolist(),
        "interpretation": "synthetic callback wiring only; not validated chemistry",
    })


if __name__ == "__main__":
    main()
