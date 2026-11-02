# 외부 crevice flow/CFD solver 결과 교환

`integration.external_crevice_solver_receipt`는 solver 실행 자체를 대체하지 않고, 외부 결과를 기존 restricted-transport 소비자와 연결하기 전에 provenance와 grid mapping을 정규화한다.

## Provider 입력 계약

`ExternalCreviceSolverHistory`에는 provider ID/revision/run ID, 원 결과 SHA-256과 일치하는 `Evidence`, mesh revision, coordinate-system ID, caller time-basis ID, aperture-history 결과와 SHA-256을 넣는다. 좌표 원점은 crevice mouth, 양의 축 방향은 mouth-to-tip으로 고정하고 pressure/velocity/length/time 단위는 각각 Pa, m/s, m, s를 받는다. 시간별 각 cell aperture는 digest-pinned geometry history의 모든 knot와 정확히 일치해야 한다. Cell 폭과 face 위치, face별 압력 및 속도 cardinality도 각각 cell count와 cell count+1로 맞춰야 한다.

모든 데이터 mapping·face 순서/부호·mesh/geometry revision·시각 정렬·piecewise-linear 보간·계산 사용 승인을 review flag로 요구한다. 공급자의 원래 배열 순서나 부호를 자동 추측하지 않는다. 외부 file parser가 필요하면 공급자별 converter가 원자료 digest와 row/face mapping을 보존해야 한다.

## Python 연결

```python
from matintegrity.models.external_crevice_solver import (
    ExternalCreviceSolverHistory,
    ExternalCreviceVelocityProvider,
)
from matintegrity.restricted_transport import solve_restricted_transport

receipt = ExternalCreviceSolverHistory.model_validate(provider_payload)
velocity = ExternalCreviceVelocityProvider(receipt)
result = solve_restricted_transport(
    transport_request,
    reaction_callback,
    axial_advection_velocity=velocity,
)
```

`ExternalCreviceVelocityProvider`는 face velocity를 exact provider knot 사이에서만 선형 보간하고 receipt 시간 범위를 벗어난 요청은 예외로 거절한다. callback의 `configuration_sha256`, `provider_id`, `source_sha256`는 기존 transport lineage와 일치하도록 제공한다. 소비 요청에는 callback 모드와 유동 연속성·시간가변 유동·역류 및 distal boundary 검토를 적용해야 한다. pressure field는 정규화 receipt에 보존되지만 별도 압력-유동 관계 없이 속도로 변환하지 않는다. geometry가 변하는 경우 고정 mesh 결과를 다른 geometry에 재사용하지 말고 일치하는 geometry revision receipt를 제공한다.

## 현재 범위

내장 구현은 provider-neutral typed receipt와 기존 Python callback 소비 계약까지 연결한다. provider별 CSV/VTK/HDF5 parser, 공간 보간/re-meshing, solver 실행 제어, wall shear/확산계수 변환, 격자수렴·질량보존 검증, turbulence/비뉴턴/압축성 유동은 포함하지 않는다. 합성 fixture는 실행 또는 CFD 검증 증거가 아니다. 적어도 한 provider의 실제 receipt를 확보하고 consumer를 실행해 round-trip과 보존 관계를 확인하기 전에는 end-to-end exchange 완료나 검증된 CFD 연동이라고 해석하지 않는다.
