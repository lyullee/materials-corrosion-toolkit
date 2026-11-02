# 크리비스 공간 반응수송과 셀별 수용액·고체 평형 연성

## 모델 식별 및 API

- 예정 ModelSpec ID: `transport.crevice_spatial_activity_solid_nernst_planck_1d`
- 입력: `CreviceSpatialChemistryTransportRequest`
- 시간 knot 입력: `CreviceChemistryKnot`
- 계산 함수: `solve_crevice_spatial_chemistry_transport`
- provenance source IDs: `caller_cellwise_aqueous_and_solid_equilibrium_by_knot`, `sequential_variable_volume_nernst_planck_and_local_chemistry_operator_split`

이 모델은 기존 variable-area activity-corrected reactive transport solver를 각 인접 knot 구간에서 재실행하고, 각 endpoint에서 caller 지정 Davies 질량작용 수용액 평형과 finite competing-solid 평형을 계산한다. 계산된 수용액 농도, 활동도, 고체 inventory가 다음 구간의 초기 상태가 된다. 따라서 수송 flux와 chemistry는 상태를 통해 연속 결합된다. chemistry와 BDF 내부 stage를 동시에 푸는 monolithic nonlinear solver는 아니다.

## 입력 계약과 데이터 구조

`transport`에는 `VariableAreaCreviceActivityReactiveTransportRequest`가 들어간다. 시간 knot별 cell/face 단면적, face 속도, mouth 농도, diffusivity, activity schedule 및 선택된 kinetic reaction schedule은 기존 variable-area transport 계약을 따른다. 면적은 양수여야 하고, cell volume 변화와 유량 연속성을 기존 solver가 확인한다. area history digest는 provider, revision, configuration, exact knot, cell/face 면적에 결합된다.

`chemistry_by_knot`은 transport knot과 같은 길이·순서를 가져야 한다. 각 knot는 정확한 `knot_index`, `time_s` 및 transport 셀 순서와 일치하는 `CreviceCellActivitySolidInput`을 요구한다. 모든 knot/cell에서 transport species, mass-action species, solid equilibrium aqueous species ID, 전하 및 원소식은 같아야 한다. Mass-action 입력은 `molarity_1_mol_L`; 농도 제약은 mol/L, transport 농도와 고체상 재고는 mol/m³ 단위다. 변환은 정확한 `1000 L/m³` 배율로 처리한다.

모든 원소식에 대해 caller의 선형 수용액 제약 행렬이 해당 원소 inventory 벡터를 span하는지 rank 조건으로 검사한다. 이 gate는 수송으로 바뀐 종 농도에서 다음 knot의 보존 제약 목표를 구성할 수 있는지 확인한다. 전기적 charge/element-balanced kinetic reaction과 중성 고체 반응의 검사는 기존 하위 모델에 맡긴다. 어떤 종, 반응, K, 고체 후보도 자동으로 만들거나 발견하지 않는다.

## 계산 순서

1. 첫 exact knot의 transport 초기 농도를 각 cell mass-action 선형 제약 목표로 투영한다. caller가 준 cell/knot 활동도 및 solid 후보와 재고로 활동도-고체 고정점을 계산한다.
2. 각 연속 knot 구간에서 기존 variable-area BDF solver를 실행한다. 기존 유한체적 분자수 보존식은 cell volume, face area와 caller 지정 Nernst–Planck flux를 사용한다. 각 open face는 확산·대류와 활동도 구배가 들어간 flux를 계산하고, zero-current closure가 face potential gradient를 결정한다. 입구 mouth boundary는 caller가 주고 blind tip flux는 0이다.
3. 현재 구간의 좌측 knot에서 계산한 각 cell 활동도 계수를 구간 내 상수로 사용한다. caller kinetic reaction network가 있으면 기존 solver가 그 반응 속도를 BDF 수송 방정식과 함께 적분한다.
4. 구간 endpoint에서 계산된 cell 농도를 다음 exact-knot activity/speciation/solid solver 입력으로 바꾸고, 고체 재고를 직전 knot 결과로 갱신한다. 제약 목표는 endpoint 종 농도의 caller 선형 조합으로 구성한다.
5. 기존 하위 solver의 BDF 함수 평가 예산, Davies/질량작용 수렴조건, 고체 active-set sweep 한도와 외부 총 함수평가 한도를 모두 적용한다. 임의의 subinterval 면적과 kinetic reaction record digest/Evidence도 원 일정을 슬라이스한 값으로 재계산한다.

## 보존, lineage, 실패 처리

각 구간 결과에는 실제 interval transport input/result digest, geometry interval digest, chemistry input/output digest, knot index/time, 수송 함수평가 횟수를 기록한다. 전체 결과에는 aqueous+solid을 합산한 원소 inventory, mouth 유입 및 kinetic reaction source 누계, 원소 closure 잔차를 각 knot에 기록한다. Solid phase solver는 aqueous/solid extent balance와 saturation complementarity를 확인하고, transport solver는 species inventory·local charge·face current를 확인한다.

하위 수송·chemistry solver 실패, 원소 balance 허용치 초과, 총 함수평가 예산 초과 때는 상태를 `needs_data` 또는 `out_of_scope`로 fail-closed 한다. 이전까지 완료된 knot 상태만 `accepted_knot_prefix`로 보존하며 실패 구간 이후 상태를 수락하지 않는다. `all_requested_knots_completed`가 true일 때만 전체 결과를 committed 결과로 간주할 수 있다.

## 해석 한계 및 남은 연성 공백

- 활동도 계수는 좌측 knot chemistry 결과에서 가져와 구간 내 일정하게 둔다. 내부 BDF stage에서 ionic strength/Davies 및 mass-action을 재계산하지 않으므로 시간 내부 활동도는 고정점 수렴 결과가 아니다.
- 고체 전이는 exact knot에서 순간 평형으로 반영한다. nucleation delay, metastability, precipitation/dissolution kinetics, deposits morphology는 계산하지 않는다.
- 기존 caller kinetic reaction은 transport 구간 중 적분되지만 solid phase와 electrochemical current의 연속 반응속도/source 항으로 만들지 않는다.
- mixed-potential solver, electrochemical wall flux, metal loss, crevice aperture update와 geometry feedback에는 연결하지 않는다. geometry는 caller history로 고정된 입력이다.
- transport solver의 local electroneutrality와 zero-current 가정 및 one-liquid scope를 이어받는다. 부식건전성 적합성 판정이나 물리적 검증으로 해석할 수 없다.

다음 물리 결합 단계는 knot 내부 활동도-수송 반복 수렴, solid transfer kineticization, mixed-potential/Faradaic species source balance, deposit volume-to-aperture geometry mapping을 독립된 contracts와 검증으로 추가해야 한다.

## 등록과 연구용 안내

ModelSpec은 위 ID, 입력 contract, evaluator, mol/m³·mol 단위를 제공한다. 기존 고정점 모듈의 registry 연결은 별도 관리된다. 통합 시 `registry.default_registry()`가 `crevice_spatial_chemistry_transport.specifications()`를 호출하도록 연결하고, schemas/catalog를 같은 source IDs와 assumptions로 재생성해야 한다. 공개 데이터/공정 chemistry는 caller가 Evidence와 사용권을 함께 공급해야 하며, 이 API는 입력자료 사용허가를 대신하지 않는다.

설명은 자체 서술로 작성했으며 외부 교재 문장을 포함하지 않는다.
