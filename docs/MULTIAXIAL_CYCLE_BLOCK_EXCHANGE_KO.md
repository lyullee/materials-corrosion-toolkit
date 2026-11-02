# 순서 보존 다축 피로 cycle-block 교환

`MultiaxialCycleBlockReceipt`는 외부 해석/신호 처리기가 제공한 ordered tensor-cycle block을 기존 `CallerStatefulMultiaxialDamageRequest`에 연결한다. 각 block에는 zero-based sequence index, cycle 목록의 digest, 원 block digest와 시작/끝 material-state identity digest가 포함된다. receipt는 stress/strain 원본 ID와 digest, 재료 조건, 위치, clock, shear convention 및 provider Evidence를 보존한다.

`bind_ordered_multiaxial_cycle_blocks(request, receipt)`는 block을 입력 순서로 펼친 cycle payload가 실제 stateful request와 정확히 같은지 확인한다. stress/strain source, 재료/위치와 convention이 다른 경우 거절한다. block index가 0부터 이어져야 하고 ID가 고유해야 하며 모든 state endpoint가 앞·뒤 block 사이에서 일치해야 한다. 결과 request에는 receipt digest, provider ID/revision/run ID/result digest, block order, clock ID, source material state의 처음/끝 identity가 추가된다. stateful evaluator 결과에 이 lineage가 포함된다.

```python
from matintegrity.multiaxial_cycle_exchange import bind_ordered_multiaxial_cycle_blocks

bound_request = bind_ordered_multiaxial_cycle_blocks(stateful_request, cycle_receipt)
damage_result = evaluate_caller_stateful_multiaxial_damage(bound_request, damage_provider)
```

이 material-state identity는 cycle source가 선언한 source-state bookkeeping이지 callback의 내부 fatigue state vector와 동일하다고 가정하지 않는다. 이 binding은 cycle을 정렬·보간·복구하지 않는다. 순서 없는 집계 cycle count, gap이 난 source state, digest가 다른 cycle payload는 사용할 수 없다. 실제 외부 cycle parser/provider receipt와 numerical sequence comparison은 별도 검증 대상이다.
