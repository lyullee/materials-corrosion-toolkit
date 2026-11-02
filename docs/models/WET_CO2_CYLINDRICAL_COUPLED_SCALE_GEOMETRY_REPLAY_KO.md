# 원통형 wet-CO2 스케일 성장 geometry 반복 계산

## 목적

`integration.wet_co2_cylindrical_coupled_scale_geometry_replay`는 caller가 설정한 geometry, transient species transport, multilayer steady diffusion, wall saturation 및 한 상의 diffusion-limited growth ledger를 한정된 Picard 반복으로 재실행한다. 각 반복에서 이전 장부의 선택 상별 축방향 단위 길이당 재고를 geometry로 반영하고, 해당 geometry에 맞춰 후속 모델 요청을 digest와 함께 다시 구성한다.

이 계산은 독립 모듈들을 묶는 제한적 반복기다. 완전 동시 방정식 해법 또는 검증된 wet-CO2 부식 예측기로 취급해서는 안 된다.

## 계약과 사용

- 계약: `WetCo2CylindricalCoupledScaleGeometryReplay`
- 실행 함수: `evaluate_wet_co2_cylindrical_coupled_scale_geometry_replay`
- 모델 명세: `specifications()`
- 입력에는 `geometry_seed`, `transient_transport_template`, `multilayer_transport_template`, `saturation_kinetics_template`, `diffusion_limited_growth_template`가 필요하다.
- 모든 템플릿은 caller가 값·물성·반응식·계수·Evidence·review gates를 명시해 구성한다.
- 반복 수는 1~50으로 제한하며 상 재고의 knot별 절대/상대 허용오차를 입력한다.
- 선택 상의 ID는 각 geometry 및 saturation/kinetics/growth 템플릿에서 동일해야 한다.
- kinetics flux가 inner wetted area 기준인지, 기록 계보가 보존되는지, 반복 예산이 적절한지 검토 승인이 필요하다.

## 반복 순서와 커밋 조건

각 반복은 다음 순서다.

1. 현재 상별 몰수 이력으로 geometry를 평가한다.
2. 같은 geometry와 digest로 transient cylindrical species transport 및 steady multilayer diffusion resistance를 각각 평가한다.
3. transient 결과를 선택 고체의 caller activity/Ksp 및 caller scale kinetics에 연결한다.
4. kinetics 석출률을 수송 공급량으로 제한하고 용해율은 그대로 두는 phase inventory ledger를 계산한다.
5. 장부가 반환한 선택 상 재고 이력을 다음 geometry 후보로 만들고 이전 geometry와 knot별 차이를 검사한다.

모든 knot가 `abs_tol + rel_tol × max(|new|, |old|)`보다 작은 차이를 보인 경우에만 후보 geometry를 전체 수렴 결과로 반환한다. 수렴하지 않으면 후보는 downstream 사용 결과로 커밋하지 않는다. 가장 최근 반복에서 수렴한 선행 knot는 `committed_prefix_inventory_rows`에 진단용으로 남기며 전체 해답과 구분한다. 하위 계산 실패 시에도 마지막 진단 prefix와 실패 결과를 보존한다.

## 보존 범위와 한계

선택 상의 재고만 반복에서 바꾼다. 벽 후퇴와 다른 고체상 재고는 seed 이력을 유지한다. 하위 모델은 반복마다 순차 실행하며 반복 내부에서 서로의 상태를 동시에 조정하지 않는다. 공급 한도는 caller의 고정된 diffusivity, bulk concentration, saturation/Ksp 기록 및 stoichiometry에 종속된다. 시간 간격은 하위 scale ledger가 선언한 왼쪽 knot 고정 속도 규칙을 따른다.

미수렴 후보는 반환 geometry로 쓰지 않는다. 수렴 기준을 만족해도 이는 선언된 모델 간 잔차 조건만 확인한 것이며 물성의 정확도, scale 안정성, 실제 부식률, 보호 효율, 수명 또는 현장 안전성을 보증하지 않는다. 자동 speciation, 상 발견, 계수 추정, 전위/전류 피드백, phase 전환, 파손/박리, 적응 시간망 또는 validation data 대체는 하지 않는다.

## 계보와 향후 검증 계획

source IDs는 `caller_cylindrical_geometry_iteration_seed`, `bounded_picard_replay_of_caller_transport_saturation_and_scale_growth`다. 매 반복의 geometry/transport/multilayer/saturation/growth 결과 digest와 knot별 최대 재고 잔차를 기록한다. 반복 geometry의 파생 Evidence는 모델 예측으로 표시하며 seed history의 license ID를 보존한다.

구현과 문서만 작성했으며 테스트, 패키징, HPC 계산은 하지 않았다. 이후 검증은 고정점 toy case 수렴, 비수렴 budget 종료 및 후보 미커밋, 첫 실패 하위 모듈에서 성공 prefix 보존, exact knot/상 ID/digest 불일치 차단, zero/negative inventory 고갈, 여러 상 중 선택 상만 갱신, iteration budget 및 tolerance 변화에 따른 결정성, coupled residual 독립 재계산을 포함해야 한다.
