"""Narrow adapter for one pinned, public API-581 repository contract.

This module was authored from schema metadata only.  It neither imports nor
executes code from the target repository.  The selected target input records a
qualified PoF *method route*; its schema has no field for an external numeric
period PoF.  Consequently, this adapter never relabels or transfers that value.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .api581_exchange import Api581DamageExchangeRecord
from .contracts import Contract

PINNED_REPOSITORY = "lyullee/api581-risk-analysis"
PINNED_COMMIT = "7c8badb829f84b19c7b84d07fbc476601d9194eb"
PINNED_SCHEMA_PATH = "docs/python-api.schema.json"
PINNED_SCHEMA_SHA256 = "bcb2ee8ee001d26e7ca40fe69a23f31358532fd13b29634d3349a9296054b51a"
TARGET_CALCULATION_ID = "frequency/pof-method-selection"
TARGET_ADDITIONAL_PROPERTIES = False
TARGET_REQUIRED_FIELDS = ("method", "qualification_basis", "uncertainty_quantified")


class PinnedPofMethodSelectionRequest(Contract):
    """Exact minimal input accepted by the pinned method-selection schema."""

    method: Literal[
        "structural_reliability",
        "statistical_generic_data",
        "expert_judgment",
        "combined",
    ]
    qualification_basis: str = Field(min_length=1, max_length=1000)
    uncertainty_quantified: bool


def api581_pinned_method_selection_request(
    record: Api581DamageExchangeRecord,
    *,
    method: Literal[
        "structural_reliability",
        "statistical_generic_data",
        "expert_judgment",
        "combined",
    ],
    qualification_basis: str,
    uncertainty_quantified: bool,
    acknowledge_numeric_pof_not_transferred: Literal[True],
) -> PinnedPofMethodSelectionRequest:
    """Build the only semantics-preserving minimal request at the pinned boundary.

    The target request classifies a PoF methodology.  It does not accept a
    numeric PoF, damage factor, POD, or spatial probability.  A caller must
    explicitly acknowledge that limitation, and must supply the methodology
    classification rather than having it inferred from provider identifiers.
    """

    if acknowledge_numeric_pof_not_transferred is not True:
        raise ValueError("caller must acknowledge that numeric PoF is not transferred")
    if record.status != "computed":
        raise ValueError("pinned method-selection request requires a computed exchange record")
    if record.probability_of_failure is None:
        raise ValueError("a qualified conditional period PoF is required to select an external PoF route")
    if record.probability_semantics != "conditional_first_failure_in_period":
        raise ValueError("only conditional first-failure-in-period PoF evidence is eligible")
    if record.damage_factor is not None:
        raise ValueError("damage factor cannot cross the PoF method-selection boundary")
    if record.inspection_pod is not None:
        raise ValueError("inspection POD cannot cross the PoF method-selection boundary")
    if record.spatial_exceedance_probability is not None:
        raise ValueError("spatial exceedance probability cannot cross the PoF method-selection boundary")

    return PinnedPofMethodSelectionRequest(
        method=method,
        qualification_basis=qualification_basis,
        uncertainty_quantified=uncertainty_quantified,
    )
