# 다축 McDiarmid 고주기 피로 강도 스크린

## 목적과 모델 식별자

`fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen`은 caller가 제공한 3차원 응력 이력 표본과 후보면 집합을 대상으로, 각 면의 전단 트랙션 변화와 최대 법선응력을 결합한 McDiarmid 고주기 강도 지수를 계산합니다. caller가 재료·조건에 적합하다고 검토한 균열 케이스 A/B의 완전교번 비틀림 강도와 인장강도를 사용합니다. 최대 지수 면과 단위 없는 여유를 표시합니다.

## 구현한 관계와 이산 계산

선택한 평면 단위법선을 `n`, 응력텐서를 `σ`라 하면 각 이력 표본에서 트랙션 `t = σ n`, 법선응력 `σn = n·t`, 면내 전단 트랙션 `τ = t − σn n`을 계산합니다. 한 평면에서 기록된 모든 전단 트랙션 벡터 쌍 간 최대 거리를 `Δτmax`로 두고 `τa = Δτmax/2`로 정의합니다. 면별 지수는 아래와 같습니다.

```text
index = τa / tA_or_B + max(σn) / (2 σUTS)
screen_margin = 1 - index
```

최댓값은 입력한 후보면과 시간 표본에서만 찾습니다. 이는 공개된 면 기반 강도식에 caller가 유한 표본 경로를 적용한 제한된 스크린입니다. 시간 사이 최적화나 연속 구면에서의 최대값을 보장하지 않습니다.

## 필요한 입력과 증거

- 물리 범위·재료 상태·반복 하중 구간을 특정한 대칭 응력텐서 표본과 시간 순서
- 적용 방향을 caller가 검토한 후보면 단위법선
- 케이스 A 또는 B, 해당 케이스와 재료 조건에 맞는 완전교번 비틀림 피로강도 및 인장강도
- 응력 표본, 후보면, 재료 강도·상태·균열 케이스를 각각 묶는 제공자 revision, SHA-256 및 사용권 Evidence
- 텐서 부호·단위, 반복 주기 대표성, 재료 조건, 후보면/표면 방향, 데이터 적용성 및 계산 사용의 명시적 검토

Evidence digest는 모델 입력 데이터의 동일성을 고정합니다. 출처나 물성치의 진실성·대표성·시험 적합성을 자동 검증하지 않습니다.

## 적용 경계

- 계산값은 유한한 표본/면 집합에 대한 McDiarmid 형식의 고주기 강도 지수입니다. 수명, 누적 Miner 손상, 균열 전파, 확률 또는 설계코드 합격을 산출하지 않습니다.
- 전단 진폭은 표본 전단 트랙션 벡터의 유클리드 직경 절반으로 계산합니다. 별도 이력 보간·주기 검출·비례/비비례 계수 보정은 하지 않습니다.
- 후보면은 caller가 제공하므로 면 격자 오차나 면 방향 누락을 보정하지 않습니다. 격자 수렴성과 하중 주기 완결성은 사용자 검토 대상입니다.
- crack case A/B 선택, 비틀림 강도, 인장강도 및 그 시험 조건의 실제 적용 가능성은 caller 책임입니다. 인장강도가 음의 법선응력 기여를 상쇄할 수 있는 정의를 그대로 유지하므로 입력 조건과 해당 criterion의 용도를 검토해야 합니다.

## 독립 공개 참고자료와 source ID

아래 문헌은 강도식 형태와 균열 케이스 구분을 확인하기 위해 참고했습니다. 코드는 문헌의 문장이나 구현을 복사하지 않고 입력 계약, 유한 표본 계산, 면별 설명 및 적용 한계를 독립적으로 구성했습니다.

- D. L. McDiarmid, “A General Criterion for High Cycle Multiaxial Fatigue Failure,” *Fatigue & Fracture of Engineering Materials & Structures* 14 (1991), 429–453. [DOI: 10.1111/j.1460-2695.1991.tb00673.x](https://doi.org/10.1111/j.1460-2695.1991.tb00673.x)
- D. L. McDiarmid, “A Shear Stress Based Critical-Plane Criterion of Multiaxial Fatigue Failure for Design and Life Prediction,” *Fatigue & Fracture of Engineering Materials & Structures* 17 (1994), 1475–1484. [DOI: 10.1111/j.1460-2695.1994.tb00789.x](https://doi.org/10.1111/j.1460-2695.1994.tb00789.x)

카탈로그 source ID 제안:

- `mcdiarmid_shear_stress_critical_plane_1994`
- `caller_multiaxial_stress_tensor_history`
- `caller_mcdiarmid_case_torsion_and_tensile_strengths`
- `finite_sampled_shear_traction_diameter_and_normal_stress_screen`

## Python API

```python
from matintegrity.models.multiaxial_mcdiarmid_limit_screen import (
    McDiarmidCriticalPlaneLimitScreen,
    evaluate_mcdiarmid_finite_plane_limit_screen,
)

result = evaluate_mcdiarmid_finite_plane_limit_screen(request)
```

입력 스키마는 `matintegrity.multiaxial_mcdiarmid_finite_plane_limit_screen.v1`입니다. 모델 ID와 source ID를 프로젝트 레지스트리·schema·capability 카탈로그에 연결할 때는 각각 코드 계약의 해당 이름을 사용합니다.
