"""Illustrate SCC-to-FTA contract wiring with synthetic values only."""

from __future__ import annotations

import json

from matintegrity.contracts import Evidence
from matintegrity.models.chloride_scc import scc_crack_velocity_history
from matintegrity.scc_fta_binding import (
    SCCFaultTreeBindingRequest,
    SCCFaultTreeProbabilityInput,
    bind_scc_crack_advance_probability_to_fta,
)

from scc_crack_velocity_history import build_synthetic_request


if __name__ == "__main__":
    source_request = build_synthetic_request()
    source_result = scc_crack_velocity_history(source_request)
    binding = bind_scc_crack_advance_probability_to_fta(
        SCCFaultTreeBindingRequest(
            scc_request=source_request,
            scc_result=source_result,
            crack_advance_limit_m=2.0e-8,
            limit_evidence=Evidence(
                source_id="synthetic_crack_advance_limit",
                origin="synthetic",
                citation="Synthetic instructional limit; not an engineering criterion.",
                license_id="MIT",
                sha256=None,
            ),
            probability_input=SCCFaultTreeProbabilityInput(
                event_id="synthetic-scc-crack-limit",
                failure_mode="Synthetic crack-advance limit event",
                condition_id="synthetic-scc-limit-v1",
                condition_statement="The synthetic cumulative crack advance reaches the synthetic limit.",
                probability=0.03,
                probability_meaning="conditional_first_failure_in_period",
                conditioning="Synthetic inputs only; probability is an illustration, not a model output.",
                probability_scope_id="synthetic-scc-example-period",
                probability_evidence=(Evidence(
                    source_id="synthetic_period_probability",
                    origin="synthetic",
                    citation="Synthetic illustrative probability; not a risk estimate.",
                    license_id="MIT",
                    sha256=None,
                ),),
                rights_boundary="local_only",
            ),
        )
    )
    if hasattr(binding, "basic_event"):
        print(json.dumps({
            "basic_event": binding.basic_event.model_dump(mode="json"),
            "calculation": binding.calculation.model_dump(mode="json"),
        }, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(binding.model_dump(mode="json"), indent=2, ensure_ascii=False))
