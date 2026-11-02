# 가스켓 조인트 볼트 반복응력 손상 선별

## 목적과 경계

`fabrication.gasket_bolt_cyclic_damage`는 계산 완료된 다중 볼트 가스켓 조인트 시간 이력에서 볼트별 명목 인장응력 시계열을 가져와 rainflow cycle을 세고, 사용자가 제공한 재료 상태별 Basquin 곡선으로 선형 Miner 손상 지표를 산정한다. 입력 하중 결과와 피로 곡선 모두 digest로 고정하며, 피로자료는 제공자·개정·재료 상태·라이선스가 Evidence에 연결되어야 한다.

이 모듈은 피로 허용기준이나 누설/씰 합격을 정의하지 않는다. 결과는 별도로 검토된 재료 데이터와 반복 이력에 조건부인 손상 선별이다.

## 입력 데이터

- `fabrication.gasket_multi_bolt_sector_equilibrium`의 계산 완료 `AssessmentResult`와 canonical SHA-256 digest. 모든 step은 시간 순으로 정렬되어 있고 각 step이 같은 볼트 식별자를 가져야 한다.
- 볼트별 재료/열처리 등 condition ID, reference stress range, reference cycle count, Basquin exponent, tensile ultimate strength. 각 곡선의 값은 joint-history digest에 묶인 calibration record digest와 provider/revision/Evidence/license로 고정한다.
- 이력 scope, 명목응력 산출에 쓰인 단면적·볼트 식별자, 재료 상태·온도 적용성, 자료 권리, cycle boundary 및 반복 운전 기록 해석에 대한 명시적 검토 플래그.
- 명시적 damage limit. 이는 결과에 대조하는 caller 기준일 뿐 코드 허용한도나 설계 합격 기준을 뜻하지 않는다.

## 계산 흐름과 식

상류 joint solver가 볼트 `b`에 대해 knot별 축력을 유효 인장 단면적으로 나누어 기록한 명목응력 `σ_b(t)`를 입력으로 사용한다. 본 모듈은 응력/변형률 해석을 재수행하지 않는다.

1. 각 볼트 응력 배열에 rainflow cycle counting을 적용한다. 이력의 시작/끝 경계 및 한 번의 이력이 몇 회 반복되는지는 caller가 정한다. 결과의 잔여 half-cycle count도 보존한다.
2. cycle stress range `Δσ`와 mean `σ_m`에서 `σ_a=Δσ/2`를 구한다. 인장 mean에만 Goodman 변환 `σ_a,eq = σ_a / (1 − max(σ_m,0)/S_u)`를 적용한다. 여기서 `S_u`는 caller가 공급한 인장강도다. 이에 대응하는 등가 완전 반전 범위는 `Δσ_eq=2σ_a,eq`다.
3. 사용자 calibration에 명시된 Basquin 관계 `N_f=N_ref(Δσ_ref/Δσ_eq)^m`로 cycle life를 추정하고 `D_b=Σ(n_i/N_{f,i})`를 산출한다. 손상 limit 대비 margin 및 비율은 별도 표시한다.

등가 범위가 0인 cycle은 손상 0으로 취급한다. cycle mean이 입력된 `S_u` 이상이면 Goodman 변환이 정의되지 않으므로 해당 볼트 결과를 범위 밖으로 반환한다.

## 통합 방법

Python에서 `GasketBoltCyclicDamage`를 생성하고 `evaluate_gasket_bolt_cyclic_damage(request)`를 호출한다. `specifications()`는 중앙 ModelSpec 등록에 사용할 수 있다. 상류 API의 결과 JSON, 볼트 ID, 단면적 및 각 재료 곡선의 적합 범위를 가져오는 importer/adapter는 별도로 구성할 수 있다.

결과의 bolt별 cycle 상세, `linear_miner_damage`, `damage_margin`, `fraction_of_declared_damage_limit`, governing bolt ID는 FTA 또는 다른 위험성 평가 모듈의 입력 feature/event 조건으로 연결할 수 있다. 이 모듈은 위험도나 사건확률을 직접 산출하지 않는다.

## 제한 및 후속 검증 항목

- 명목 축응력만 사용한다. 나사산/좌면 응력집중, 편심·굽힘, 국부 소성, 잔류응력, fretting, 부식, 수소취화는 계산하지 않는다.
- 하중 이력이 실제 반복 서비스 대표성을 갖는지, 고온/저온에서 자료가 적용되는지, 이력 반복 횟수와 경계가 적절한지는 caller 책임이다.
- Goodman과 Basquin 적용범위, cycle counting 구현/버전, Miner 선형 누적의 적합성은 별도 비교·검증되어야 한다. 이 조합을 보편적인 파손법칙으로 간주하지 않는다.
- 구조 건전성 합격, 체결부 수명, 누설, 개별 볼트 파손 시점, 불확실성 또는 파손확률을 추론하지 않는다.
- 수치 단위는 SI(Pa, cycle)로 정규화해 넣고, 원천 곡선의 원단위 변환과 데이터 사용권한을 기록한다.
