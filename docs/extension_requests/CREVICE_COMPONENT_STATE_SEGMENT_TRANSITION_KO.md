# Crevice variable-geometry segment consumer 확장 요청

MatIntegrity의 `integration.crevice_component_state_segment_transition`은 committed component-state BDF 결과에서 다음 고정-geometry segment용 BDF request를 만든다. 소비자는 다음 lineage를 함께 보존한다.

- source request, full Calculation digest, committed 상태 및 component-ledger closure
- exact boundary time, invariant cell ID/order 및 component basis
- caller geometry receipt/Evidence와 volume identity (`length × width × aperture`)
- 셀별 최종 component moles를 다음 구간 초기 inventory로 전달한 기록
- 새 segment BDF request와 geometry/volume snapshot digest

Geometry는 caller/provider가 계산한 값이다. API가 corrosion/precipitation law에서 geometry를 추론했다고 해석하면 안 된다. 이 계약은 segment 경계에서의 operator split이며, interval 내 moving-boundary feedback, mesh remap, pore/deposit morphology, fully coupled pressure-flow, risk probability, life 또는 qualification을 제공하지 않는다.
