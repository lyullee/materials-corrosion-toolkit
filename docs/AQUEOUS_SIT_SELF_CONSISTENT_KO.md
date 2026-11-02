# 수용액 SIT 활동도–질량작용 자기일관 결합

`chemistry.aqueous_sit_self_consistent_speciation`는 caller가 작성한 단일 액상 질량작용·수지 시스템을 반복해 풀고, 각 해의 농도를 molality로 환산하여 Specific Ion Interaction Theory(SIT) 활동도 계수를 갱신한다. 종·반응·평형상수·분석 수지·Debye–Hückel A·방향별 epsilon 상호작용은 모두 호출자 데이터다. 자동 화학종/반응 생성은 하지 않는다.

## 반복 흐름

1. 현재 species activity coefficient로 기존 `aqueous_mass_action_speciation`을 실행한다.
2. 계산된 `concentration_mol_L`을 `water_mass_per_solution_volume_kg_L`로 나눠 molality를 얻는다.
3. 종 전체에서 `I = 0.5 Σ mᵢ zᵢ²`와 `Σ mᵢ zᵢ`를 계산한다. 이온강도는 caller limit을 넘을 수 없고 limit 자체도 6 mol/kg-water 이하로 제한된다.
4. caller가 제공한 온도별 Debye–Hückel A와 directional SIT interaction table로 각 종 gamma를 계산한다.
5. SIT가 돌려주는 `gamma_m`은 molality 표준상태 계수다. 기존 질량작용 solver의 1 mol/L 표준상태에 맞추기 위해 `gamma_c = gamma_m / w`로 변환한다. 여기서 `w`는 kg-water/L-solution이다. `ln(gamma_c)` 공간에 caller damping을 적용하며 최대 절대 log-gamma 고정점 잔차가 선언 tolerance 이내일 때만 converged equilibrium을 반환한다.

각 반복의 이온강도·전하 잔차·내부 solver 잔차를 기록한다. 내부 해 실패, SIT support 초과, charge tolerance 위반, 비유한 상태 또는 outer iteration budget 소진은 부분 최종 해를 평형 결과로 승격하지 않는다.

## 입력·계보 조건

기존 질량작용 API는 1 mol/L 기준 무차원 활동도를 사용하고 SIT 계산은 kg-water 기준 molality를 사용한다. 활동도 등식 `gamma_c c = gamma_m m` 및 `m = c/w`에 따라 질량작용에 전달하는 계수는 `gamma_c = gamma_m/w`다. 호출자는 용액 부피당 물 질량과 그 환산을 제공·검토해야 하며 용액 밀도만으로 물의 질량을 추정하지 않는다. 결과에는 두 계수 기준을 모두 보존한다. A 값에는 Evidence source, provider/revision, configuration digest와 record digest를 연결한다. 각 directional epsilon 항목도 Evidence source 및 provider record ID를 가져야 한다. 미기록 방향 항은 0으로 취급되므로 상호작용 집합의 완전성과 적용성을 사용자가 확인해야 한다.

반복 결과는 입력 전체 digest, interaction parameter digest, source-record 매핑 digest, evidence bundle digest를 보존한다. 평형계수와 상호작용 값은 별도로 검토된 입력이며, 이 API는 source를 다운로드하거나 실험값의 자격화를 주장하지 않는다.

## 적용 경계

이 계산은 caller가 선언한 하나의 액상, 고정된 액상 종 목록, 주어진 질량작용 반응과 수지식 안에서 활동도와 평형을 반복 결합한다. 자동 반응/상 탐색, gas/solid phase, 침전·용해 kinetic law, 농축 전해질 범위를 벗어난 모델, 염석, 전극 kinetics, scale 보호 또는 부식률을 추론하지 않는다. 수렴 상태도 SIT parameter set과 시스템의 물리적 적합성·독립 검증을 의미하지 않는다.

`examples/aqueous_sit_self_consistent.py`는 project-authored synthetic data를 사용한 API 배선만 보여준다. 예제 계수는 물성값·설계 권고값·검증 근거가 아니다. 계산 테스트와 실험 비교는 별도의 승인된 검증 단계에 남아 있다.

## 제한 수송기 연결

`build_sit_transport_activity_callback()`은 같은 SIT 요청을 제한 수송기용 `activity_coefficients(time_s, concentration_mol_m3)` callback으로 바꾼다. 배열은 species × mouth-plus-cell 순서이며 수송 온도와 종 순서를 요청의 질량작용 계와 정확히 맞춰야 한다. 각 위치에서 mol/m³를 molality로 변환하고 국소 이온강도와 지정된 상한을 확인한 뒤 동일한 온도별 A 및 방향별 epsilon 식을 적용한다. 이 adapter는 각 위치의 gamma만 계산하며 수송 중 질량작용 재평형이나 국소 전하 균형을 강제하지 않는다.

callback configuration digest는 입력 요청, 계수 provider 및 record, 종 순서, 온도, 표준상태를 묶는다. 결과에는 해당 digest와 SIT interaction/Evidence lineage digest가 기록된다. `RestrictedTransportRequest.activity_configuration_sha256`에는 callback의 `configuration_sha256`을 설정해야 한다. 이는 소프트웨어 입력 일관성 추적이며 외부 parameter의 진위·적합성 검증이나 결합 수송-화학 모델의 물리 검증을 의미하지 않는다.

caller가 고체별 용해도곱, 고체 활동도 항, 온도, 표준상태와 검토 상태를 `AqueousSaturationScreen`에 제공하면 `build_sit_transport_saturation_callback()`이 SIT 활동도를 포화비로 바꾸어 competing-solid kinetic transport callback으로 연결한다. caller는 별도로 종량론과 phase-specific rate law를 제공해야 한다. 이 조합은 수송 구간 뒤의 cell state에서 포화비를 계산하고 explicit transport-then-kinetics 방식으로 다음 구간 고체 inventory에 반영한다. 구간 내부 상변화, 자동 상 선택, 실시간 평형 재계산이나 완전 동시 연성은 수행하지 않는다. 합성 연결 예시는 `examples/aqueous_sit_self_consistent.py`에 있으며 예시 계수와 Ksp는 물리값이 아니다.

결합 kinetic 결과의 `saturation_activity_provider_lineage`는 SIT provider/revision/configuration, record, 원 요청, 종 순서, 온도, epsilon parameter digest와 Evidence digest를 보존하고 별도 aggregate digest를 제공한다. 이는 caller가 campaign의 포화도·속도 계산 경로를 재현할 입력 계보이지 원 데이터의 진위 인증이나 해당 속도 모델의 검증은 아니다.
