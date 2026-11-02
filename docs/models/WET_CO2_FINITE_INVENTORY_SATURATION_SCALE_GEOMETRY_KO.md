# 유한 액상재고 기반 포화도·스케일 kinetics·원통 형상 연결

## 목적

`integration.wet_co2_finite_inventory_saturation_scale_geometry`는 finite-liquid bulk/wall inventory 결과에서 선택한 고체상의 wall saturation을 계산하고, caller가 기존 `CallerSurfaceScaleKinetics`에 제공한 계수로 precipitation/dissolution을 계산한 뒤, 원통형 phase inventory와 모든 반응물의 wall-liquid 외부 exchange가 닫히는지 검사한다. 통과하면 상 두께 이력을 기존 cylindrical annular geometry handoff로 변환한다.

이 조합 경로는 현재의 finite inventory → saturation → kinetics → geometry 연결 공백을 다룬다. 새 활동도 모델, Ksp, 상 선택, kinetics 또는 물질전달식을 만들지 않는다.

## API와 입력

- 요청 계약: `WetCo2FiniteInventorySaturationScaleGeometry`
- 외부 wall exchange 계약: `WetCo2FiniteLiquidWallExchange`
- 평가 함수: `evaluate_wet_co2_finite_inventory_saturation_scale_geometry`
- catalog 명세: `specifications()`

단일 고체상으로 범위를 제한한다. geometry seed는 그 고체상 하나만 선언해야 한다. 각 dissolution-product 종마다 기존 finite-liquid transfer result 하나를 제공하고, geometry/asset/location/assessment 및 정확한 시간 knot가 일치해야 한다. 각 knot에서 농도는 mol/m³, compartment 유한 재고는 기존 ledger가 계산한 값이다.

caller는 종 전하·원소식, 중성 고체식, 각 용질 활동도 계수, 해당 시간의 log10(Ksp), 물성/평형 provider record, `CallerSurfaceScaleKinetics` 요청, 그리고 scale 반응이 아닌 wall 외부 몰 교환을 명시한다. 활동도와 용해상수 records는 제공자·기록 ID·해시·Evidence가 고정된 기존 `WetCo2CylindricalPhaseActivityKnot` 계약을 사용한다. 선택 고체의 용해 생성물 계수는 charge와 element가 고체식에 맞게 균형을 이루어야 한다.

## 계산과 폐쇄

wall-compartment 농도 `C_i`를 mol/L로 변환하고 활동도 계수 `γ_i`와 함께 `a_i=γ_i C_i`로 둔다. 고체 용해 생성물 지수 `ν_i`에 대해 `SI=Π_i a_i^ν_i/Ksp`를 knot별 계산한다. 시간 구간은 양 끝 SI를 caller 검토 아래 기존 `CallerSurfaceScaleKinetics`에 넘긴다. kinetics가 계산한 areal precipitation/dissolution 결과는 단일 조밀 상 두께 이력이 된다.

두 독립 폐쇄가 모두 허용오차 안이어야 한다.

1. initial seed phase inventory가 kinetics initial thickness가 뜻하는 cylindrical inventory와 일치하고, 각 구간의 annular phase inventory 변화가 areal kinetics net moles × 해당 구간 시작점의 전체 bore wetted area와 일치한다.
2. 각 용질 종의 finite-liquid ledger wall external change가 `caller nonreaction wall exchange + ν_i (dissolved − precipitated) × segment area`와 일치한다. bulk/wall compartment transfer와 총 유한재고 폐쇄는 입력 finite-liquid ledgers에서 이미 확인되며, 이 bridge는 추가된 phase reaction 부분을 검사한다.

두 폐쇄 중 하나라도 실패하면 해당 geometry/재고 결과를 정상 계산으로 반환하지 않는다. 완료된 경우 산출 saturation, kinetics 결과, cylindrical geometry, 종별 반응 교환 잔차와 upstream digests를 함께 반환한다.

## 제한

액상 내 자동 speciation, activity coefficient 계산, Ksp 추정, 자동 상 탐색/경쟁, 임의 반응식 균형화, kinetics 상수 추정, 확산 제한, 동시 재계산을 하지 않는다. 한 개의 중성 고체, 한 개의 조밀 연속 환형 상과 caller 지정 면적 기준만 지원한다. 모든 finite-liquid ledger의 external wall changes는 이미 해당 reaction change와 nonreaction source/sink의 합을 포함해야 한다. concentration/volume histories가 phase reaction을 반영하지 않는 경우 closure가 거부한다.

계산은 exact knot에만 수행하며 활동도·Ksp·온도와 비선형 saturation 경로 사이를 자동 보간하지 않는다. 이 결과는 caller 가정과 입력 데이터의 수치적 일관성을 검사하는 모델 조합일 뿐, 부식속도, 보호성 scale, 재료수명 또는 현장 성능을 검증하지 않는다.

## 계보와 검증 상태

source IDs: `caller_cylindrical_finite_liquid_inventory_results`, `caller_finite_inventory_wall_activity_and_ksp_records`, `caller_surface_scale_kinetics_configuration`, `caller_cylindrical_scale_geometry_seed`, `finite_liquid_to_solid_reaction_stoichiometric_closure`. 결과는 finite inventory result, geometry, kinetics request, activity/Ksp record와 caller exchange Evidence digest를 유지한다.

구현과 설명서만 추가했으며 테스트·패키징·HPC 검증은 실행하지 않았다. 후속 검증에는 단일염 SI, 한 반응물 precipitation/dissolution 수지, phase thickness와 annular inventory 폐쇄, 각 용질 wall exchange closure, 초기 inventory 불일치, 상 선택·시간점·provider digest 불일치, saturation path review gate 및 과포화 수치범위 차단을 포함해야 한다.
