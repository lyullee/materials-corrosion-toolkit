# 제작·보존 증거 워크플로

황화물 환경 applicability 비교(`degradation.sulfidation_exposure_applicability`)는 각 envelope가 인용하는 qualification record 자체도 재료/condition, sulfur quantity 정의, 온도·절대압력, 유동·침적, 노출시간의 선언 범위와 맞는지 확인한다. record identity나 조건이 envelope support 밖이면 일치한 운전환경이 있어도 그 envelope를 적용하지 않는다. 이는 사용자 소유 evidence의 내부 범위 일관성 점검으로, rate law나 규격 기준을 포함하지 않는다.

## Caller-licensed joint efficiency

`fabrication.joint_efficiency_declaration`은 joint configuration, welding process, material group과 examination method가 정확히 맞는 사용자 규칙 하나를 선택한다. 규칙에는 rule-set ID, revision, content digest, provider state와 계산 이용권한 근거가 필요하다. 실제 examination record의 physical scope와 extent 정의를 유지하며 rule support 안에서만 선언된 factor를 반환한다. 범위 미달에는 factor를 보간·대체하지 않고 `examination_extent_not_satisfied`와 `None`을 반환한다. 이 결과는 weld strength, pressure capacity, inspection reliability 또는 code acceptance가 아니다.

## Gasket-joint evidence

`fabrication.gasket_joint_evidence`는 직접 측정한 bolt preload 기록의 평균·모집단 표준편차·변동계수를 계산하고 gasket seating 및 relaxation provider evidence와 연결한다. Torque, friction 또는 geometry로 preload를 역산하지 않으며 미검토·누락 기록을 정상값으로 채우지 않는다. 이 결과는 누설률, 체결 합격, 장기 밀봉 성능 또는 규격 적합성이 아니다.

## Forming qualification

`fabrication.forming_qualification`은 component/material/product/thickness/direction, cold/hot mode와 forming method, caller-defined deformation metric, 시간순 forming·post-forming heat-treatment interval을 qualification evidence에 비교한다. Metric을 형상에서 자동 재구성하지 않고 property change나 code limit를 만들지 않는다.

## Tube bundle과 cryogenic valve

`fabrication.tube_bundle_integrity_evidence`는 exchanger/bundle/tube/row 위치, tube geometry, support/baffle/vibration descriptor, operating interval, inspection·vibration observation과 caller plug/repair/retube/monitor disposition을 별도 기록한다. 처분 기록을 모델 결정으로 해석하지 않는다. `fabrication.cryogenic_valve_evidence`는 valve body/seat/stem/seal identity, medium·pressure basis와 thermal-pressure-actuation cycle, leakage/torque/function observation을 유지한다. `below_detection`은 0이 아니며 service leakage나 reliability를 의미하지 않는다.

이 문서는 제작·용접 단계의 관측과 사용자 소유 요구조건을 분리해 기록하는 계산기를 설명한다. 모든 비교 경로는 규격 수치나 합격 기준을 내장하지 않는다.

## 방화 보호 열유속 연계

`fabrication.fire_protection_boundary_history`는 입사 열유속, 피복 상태, provider 지원영역과 노드별 전달률을 받는다. 선형 보간된 두 이력의 적을 구간에서 정확히 적분하고 `ThermalBoundary(kind="prescribed_heat_flux")`와 호환되는 조각을 반환한다. 지원범위 밖 열유속이나 상태는 외삽하지 않는다. 표준 화재곡선, 복사/대류 생성, 피복 물성·열화·spalling, 온도 해석과 합격판정은 후속 provider의 책임이다.

## 표면 청정도

`fabrication.surface_cleanliness_assessment`는 준비 면적, 검사 면적, 관측 metric과 expanded uncertainty, 호출자 요구조건을 연결한다. maximum 조건에는 `관측값 + 불확실성`, minimum 조건에는 `관측값 - 불확실성`을 사용해 보수적인 비교값을 만든다. metric·면적·단위가 정확히 일치하지 않으면 자동 변환하거나 추정하지 않는다. 검사하지 않은 면적과 요구조건에 대응하는 관측 누락을 별도로 남긴다.

결과는 사용자가 선언한 요구조건과의 비교일 뿐 coating 수명, 부착력, 부식속도 또는 설계규격 합격 판정이 아니다.

## 화학 세정

`fabrication.chemical_cleaning_envelope`는 순서가 정해진 세정 단계의 solution ID, chemical family, 농도 질량분율, 절대온도, pH와 시간을 호출자 소유 compatibility envelope와 비교한다. 한 단계 한계와 동일 envelope ID에 누적된 시간 한계를 따로 계산한다. 겹친 단계 시계는 거절하고, 무효 단계·미연결 envelope·검토 누락은 `needs_data`로 중지한다.

이 계산은 혼합 반응, 국부 농도, 금속 부식률, 잔류물, rinse 효과 또는 절차 적합성을 예측하지 않는다.

## 저장·보존

`fabrication.storage_preservation_history`는 시간 구간별 온도, 상대습도와 보존상태를 사용자 선언 범위에 비교한다. 유효하지 않은 구간과 기록 공백은 정상 구간으로 보간하지 않고 각각의 지속시간으로 보존한다. 범위 밖 총시간과 최대 연속시간, 점검 사이 간격과 사용자 선언 최대 간격 초과시간을 반환한다. 자산·위치 ID는 `RunContext`와 일치해야 한다. 결과의 `environment_timeline`은 증거 구간, inspection 경계, 명시적 기록 공백마다 horizon을 분할해 observed/invalid/uncovered 상태, 원 interval ID, missing basis 및 온도·습도·보존상태별 선언 한계 이탈을 제공한다. `inspection_schedule`은 각 연속 점검 간격과 허용 간격 초과량을 해당 시간 범위와 함께 돌려준다. 두 표는 원자료를 보간하거나 손상·부식·수명을 예측하지 않는다.

노출시간 요약은 손상률, 부식량, 잔여수명 또는 실패확률이 아니다. 보존 재료와 포장 방식의 성능 근거는 별도 데이터 공급자가 제공해야 한다.

## Coating qualification

`fabrication.coating_qualification_assessment`는 coating system·lot·substrate·exposure와 specimen source group을 calibration/holdout partition에 고정한다. DFT, adhesion 또는 사용자 metric의 값·expanded uncertainty·exact unit token을 caller-owned one-sided limit에 비교한다. 동일 source group이 두 partition을 넘으면 거절한다. 이 결과는 실험 관측 요약이며 현장 수명이나 부식률 예측이 아니다.

## Thermal-spray condition

`fabrication.thermal_spray_condition`는 coating system, spray process, feedstock lot, substrate condition, surface preparation과 deposition pass group을 region별로 고정한다. Qualification과 production 관측의 source group은 겹칠 수 없고, layer thickness·porosity·bond strength·oxide content·roughness 또는 user metric은 exact definition·unit·expanded uncertainty로 비교한다. Examined-area fraction은 coverage일 뿐 수명·부식률·구조성능 또는 합격의 대리값이 아니다.

## 시험수 수질

`inspection.test_water_quality_summary`는 시험 시작·종료, 요구 sampling location, 최대 sampling gap과 시료별 온도·pH·conductivity·chloride를 기록한다. 한계는 material condition에 결속된 사용자 envelope다. 표본 사이 수질을 보간하거나 규제 한계, 부식률 또는 미생물 상태를 생성하지 않는다.

## 운송·인양·설치

`fabrication.transport_erection_history`는 활동 coverage와 point metric, 사용자 limit, 요구 inspection stage 및 caller disposition을 분리한다. 기록 공백, invalid observation, 미등록 metric, unit mismatch와 inspection stage 누락은 `needs_data`다. Shock나 tilt 관측으로 결함 크기·손상률·잔여수명을 추정하지 않는다.

## 용접 소모재 compatibility

`welding.consumable_compatibility`는 production weld의 base-material condition pair, consumable lot, process와 service environment를 caller-owned declaration에 exact match한다. 선언 온도범위에 service range가 포함되는지도 별도로 반환한다. 재료 pair 순서만 비방향성으로 정규화하며 fuzzy designation, 대체재, 기계적 성질, 내식성, weldability와 규격 합격은 만들지 않는다.

## Preheat procedure envelope

`welding.preheat_procedure_envelope`는 material, joint, process, consumable condition, hydrogen-control과 restraint descriptor를 exact match한 뒤 thickness와 net heat-input support를 확인한다. 선택된 caller envelope의 minimum preheat와 maximum interpass에 대해 기록 margin 및 excursion duration을 반환한다. 공개 welding-code preheat table, hydrogen cracking 예측, weldability 또는 production acceptance는 제공하지 않는다.

## Local heat treatment

`welding.local_heat_treatment`는 heat-zone별 동기화 온도 센서 이력으로 가열·냉각속도, caller hold band 내 시간을 선형 구간보간으로 추정하고 센서 위치간 최대 온도구배를 계산한다. 구간 사이 온도는 선형이라는 가정을 사용하며, 샘플 사이 실제 peak·oscillation을 복원하지 못한다. 요구 한계와 heat-zone applicability는 caller envelope의 값이며 전체 metallurgical response나 절차 합격을 의미하지 않는다.

## Residual-stress evidence

`welding.residual_stress_evidence`는 측정 또는 모델 응력 component의 좌표계, 공간위치, expanded uncertainty와 provider state digest를 보존한다. 응력 중심값뿐 아니라 `stress ± expanded uncertainty` 전체 구간이 provider stress support 안에 있는지도 확인한다. 범위 밖 record/application ID를 최상위 결과에서 확인할 수 있고 partition별 ID를 별도 반환한다. 비교행은 record/support Evidence, source group, provider revision/state, record 및 calibration/holdout dataset digest를 결과로 전달한다. Application 전체 행 수와 비교 완료 수를 따로 반환하며 unmatched/ambiguous 행은 unsafe application 목록과 실패한 coverage에 포함한다. Record와 support는 같은 coordinate frame definition SHA-256 및 coordinate axis name 순서를 선언해야 하며 자동 변환/축 재배열은 하지 않는다. 차원·frame·축·성분·공간범위 제외 사유도 결과에 기록한다. Calibration/holdout metric과 허용 상한은 unit token이 일치해야 비교하며 세 partition은 source group을 공유할 수 없다. Caller support의 공간·불확도 범위와 qualification을 비교하지만 재분포, 균열 구동력, 수명과 합격을 계산하지 않는다.

## WPS qualification envelope

`welding.wps_qualification_envelope`는 production procedure·revision·양측 base-material condition·joint·process identity를 exact match한다. Numeric/categorical essential variable의 exact unit token과 지원범위, 실제 시편/test/source-group 증거 및 provider digest를 연결한다. 호출자가 제공한 qualification 범위와의 기술적 비교이며 코드표나 production acceptance가 아니다.

## Duplex phase balance

`welding.duplex_phase_balance`는 weld metal, HAZ, base material region의 상분율과 expanded uncertainty를 material/process/process-history/heat-history에 결속한다. 각 상의 불확도구간을 caller-owned regional volume-fraction envelope와 비교하지만 미측정 상, 물성, 부식·균열 또는 서비스 수명을 유추하지 않는다.

## Production-weld test evidence

`welding.production_weld_test_evidence`는 production weld·procedure revision·material/consumable lot, destructive specimen/source group과 NDE 위치를 보존한다. Method·metric definition·unit이 caller requirement와 정확히 같은 관측만 불확도구간으로 비교하고, 필요 기록수·물리 source-group 수가 부족하면 `needs_data`다. 결함분류·파괴·수명·확률을 예측하지 않는다.

## Repair-welding history

`welding.repair_welding_history`는 caller가 정의한 removal·pre-deposition inspection·deposition·heat treatment·subsequent examination 순서를 엄격한 비중첩 시계로 비교한다. 단계별 procedure/provider revision, state/configuration/input/result digest, metric envelope와 후속 검사 기록을 유지한다. 순서가 완전하다고 해서 결함 제거, repair effectiveness, 구조 건전성이나 합격을 주장하지 않는다.

## 공개 배포와 확장

관측과 요구조건에는 `Evidence`를 붙이고 원자료가 재배포 불가하면 citation·digest만 공개 계약에 남긴다. 외부 모듈은 각 Pydantic 입력 계약을 직접 만들거나 JSON schema를 사용해 데이터를 전달할 수 있다. 결과의 `status`, 누락 ID, 위반 ID와 원래 identity를 확인한 뒤 후속 위험성 평가 입력으로 명시적으로 변환한다.

