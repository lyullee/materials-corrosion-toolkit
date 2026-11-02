# Ordered multiaxial cycle block result summary

`CycleBlockResultSummaryRequest` connects one stateful multiaxial damage result with its exact bound request and `MultiaxialCycleBlockReceipt`. It checks the result digest, request digest, receipt digest, provider lineage and ordered block identities before grouping the existing per-cycle result rows by source block.

For each block, the API reports the number of receipt cycles and computed cycles, whether the block completed, cycle IDs, elapsed sequence bounds, summed per-cycle sequence damage and the endpoint states when the whole block completed. A stopped upstream calculation retains only its computed prefix; an incomplete block never receives a terminal state that the result did not provide.

The adapter does not rerun the damage provider, change cycle ordering, infer a fatigue law, calculate remaining life or failure probability, establish physical validation, or qualify the source solver. Damage remains on the upstream provider's declared basis.

```python
from matintegrity.multiaxial_cycle_block_result_summary import (
    CycleBlockResultSummaryRequest,
    summarize_cycle_block_damage,
)

request = CycleBlockResultSummaryRequest(
    receipt=cycle_receipt,
    bound_request=bound_damage_request,
    stateful_result=damage_result,
    stateful_result_sha256=canonical_digest(damage_result),
)
block_summary = summarize_cycle_block_damage(request)
```

The result digest must be computed from the exact JSON-native result object. Keep the full upstream request, receipt and result alongside the summary so downstream integrations can independently resolve every digest.
