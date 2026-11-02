# Crevice hydraulic advection downstream 확장 요청

MatIntegrity component-state BDF의 선택형 hydraulic input은 transient planar-slit inertance 결과를 고정 geometry에서 성분 advection RHS와 양쪽 reservoir ledger에 연결한다. Downstream 소비자는 다음을 보존해야 한다.

- hydraulic request/result 및 BDF request/result digest와 commit status
- 공통 clock, cell/species 순서, aperture·solution-volume snapshot
- inlet/outlet reservoir concentration schedule Evidence와 electroneutrality review
- signed flow, upwind convention, 각 side별 component/element/charge amount
- 내부 migration/diffusion current 및 Faradaic source와 hydraulic advection을 구분하는 source identity

현재 지원은 고정 aperture/volume다. 소비자는 이 결과를 variable-volume 또는 moving-boundary 모델이라고 해석하지 말고, 자체의 geometry evolution·mesh remap·pressure-flow feedback을 별도 모델로 연결해야 한다. 확률·손상률·수명·qualification은 도출되지 않는다.
