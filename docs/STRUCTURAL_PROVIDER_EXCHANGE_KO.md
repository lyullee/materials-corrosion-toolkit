# 교체형 구조해석 provider 교환

이 문서의 모델은 외부 구조해석기와 형상 provider의 결과를 재현 가능한 identity·digest·qualification evidence에 결속한다. 계약 통과는 해석자료 배선을 확인할 뿐 메시 적격성, 설계규격 합격이나 물리 검증을 뜻하지 않는다.

## Finite-element result exchange

`structural.finite_element_result_exchange`는 analysis/model/mesh revision, coordinate frame, node·element·region identity digest, element family, material assignment, load/boundary case와 result field metadata를 보존한다. Field는 step, time 또는 frequency, location, averaging, scalar/vector/tensor definition, unit, components, array shape/order/content digest를 갖는다. 대형 배열은 계약에 복제하지 않는다. Verification source group은 calibration/holdout/application partition을 넘을 수 없다.

## External-pressure provider

`structural.external_pressure_provider_evidence`는 shell/material/thickness, extensible geometry metric, boundary/support/load case, `external_minus_internal_pressure` 등 명시적 pressure basis와 measured imperfection field를 external result에 연결한다. Eigen-buckling과 nonlinear-limit 결과를 구분하며 mesh, geometry/material/imperfection/boundary/load model identity와 solver digests를 유지한다. 결과값은 allowable pressure나 collapse probability가 아니다.

## Nozzle local-stress provider

`structural.nozzle_local_stress_provider_evidence`는 vessel/nozzle/opening geometry, material, coordinate frame, signed load component와 exact unit, mesh/result location/spatial averaging, tensor·linearized·caller metric representation을 보존한다. Calibration과 holdout source group을 분리한다. Provider stress는 proprietary stress index, fatigue usage 또는 code acceptance로 자동 변환되지 않는다.

## Heat-exchanger geometry provider

`fabrication.heat_exchanger_geometry_evidence`는 shell, tube layout, tubesheet와 baffle record를 유지한다. Tube coordinate payload는 coordinate frame, component order, tube ordering, shape와 SHA-256 digest로 연결하고 pattern이나 tube count에서 좌표를 만들지 않는다. Metrology evidence는 physical specimen/source group과 observed/provider value, unit, uncertainty를 보존한다. 이 경로는 heat transfer, vibration, flow, stress 또는 structural capacity를 계산하지 않는다.

## Pitting FFS provider

`structural.pitting_ffs_provider_evidence`는 검사로 정의된 pit field, geometry·material·load identity와 외부 FFS 결과를 provider revision·입력·출력 digest 및 qualification/holdout evidence에 결속한다. 자체 FFS 식, 허용용량, 합격, 성장률이나 잔여수명을 계산하지 않는다. 결과를 소비하는 모듈은 동일한 pit representation과 적용범위를 확인해야 한다.

## Creep-fatigue interaction provider

`structural.creep_fatigue_interaction_provider_evidence`는 creep quantity와 fatigue quantity의 정의·단위를 분리하고, block의 시간·온도·stress/strain/cycle descriptor를 exact interaction basis에 결속한다. 공급자가 보고한 interaction result와 불확도를 그대로 교환하며 독립적인 선형 손상합이나 수명 환산을 만들지 않는다. Calibration과 holdout source group은 물리적으로 독립이어야 한다.

## 후속 adapter

소비 모듈은 provider result digest와 동일한 geometry/mesh/load identity를 요구해야 한다. Result를 FTA 또는 기간 고장확률에 연결하려면 별도의 한계상태, 불확실성, calibration/holdout, 사건 기간과 conditioning 계약이 필요하다.
