# 임계면 피로 계수 API

## 목적과 현재 범위

세 계산기는 외부 시험·FE·노치해석 모듈이 제공한 국부 응력·변형률 텐서 한 주기를 사용자가
선언한 유한한 평면 후보에 투영한다. `fatigue.critical_plane_factors`는 선언한 한 면내 방향의
성분 범위를 사용한다. `fatigue.critical_plane_vector_path_factors`는 그 방향과 평면 안의
직교 보완 방향으로 2차원 전단벡터 경로를 만들고 표본쌍의 최대 Euclidean chord 절반을
진폭으로 사용한다. `fatigue.critical_plane_minimum_enclosing_circle_factors`는 같은 이산
전단벡터들을 모두 포함하는 최소 원의 반지름을 별도 진폭으로 사용한다. 각 후보에 FS·SWT
계수를 계산하고 두 계수의 최대 후보 ID를 따로 반환한다.

이 모듈은 임계면 계산의 중간 계층이다. 연속 구면 탐색, 노치근 응력/변형률 해석,
비비례 추가경화 모델, cycle extraction, 재료 수명곡선 적합, 수명·강도·합격 또는 고장확률은
제공하지 않는다. FS와 SWT가 서로 다른 평면을 선택할 수 있으므로 하나의 공통 임계면으로
강제하지 않는다.

## 입력 계약

구조·FE·노치해석 모듈과의 중립 연동에는 `LocalTensorHistory`와
`critical_plane_inputs_from_local_tensor_history`를 사용한다. 이 경로는 공급자/solver 판본,
solution revision, mesh와 field location, 공간 평균 방식, 표본 시계, 전역 좌표 기저,
stress/strain measure, 입력 shear convention, 원본 SHA-256과 설정 digest를 계산 입력에
남긴다. engineering shear만 명시적으로 tensor shear로 변환하며 다른 measure는 추정 변환하지
않는다. 계약 통과는 FE 정확도·mesh 수렴·노치근 장의 물리적 자격을 뜻하지 않는다.

응력과 변형률은 같은 sample 순서의 대칭 텐서이며 각 행은 다음 순서다.

```text
[xx, yy, zz, xy, yz, zx]
```

변형률의 비대각 성분은 engineering shear가 아닌 tensor shear다. 따라서 평면 법선 `n`과
면내 방향 `m`에서 engineering shear strain은 `2 m·epsilon·n`으로 계산한다. 모든 `n`, `m`은
사용자가 정규화한 3성분 단위벡터여야 하고 서로 직교해야 한다. 모듈은 잘못된 방향을 조용히
정규화하지 않는다.

`history_id`, `material_condition_id`, `location_id`, `tensor_source_id`와 고유 `sample_ids`를
보존한다. 첫 행과 마지막 행의 대칭 텐서 Frobenius 차이가 사용자가 선언한 응력·변형률 폐합
허용오차를 모두 만족하고 `representative_cycle_declared=true`여야 범위를 계산한다. 그렇지
않으면 `needs_data`이며 후보 계수는 비워 둔다.

```python
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

result = default_registry().run(
    "fatigue.critical_plane_factors",
    inputs,
    RunContext(
        asset_id="coupon-or-component",
        location_id="qualified-local-point",
        time_basis="one reviewed representative cycle",
    ),
)
```

전체 JSON 입력은 `examples/model_inputs.json`과 생성된 `MODEL_REFERENCE_KO.md`에서 확인한다.

## 계산 convention

각 후보에 대해 법선 응력·법선 변형률, 한 방향의 전단응력·engineering 전단변형률을 투영하고
각 범위의 절반을 진폭으로 둔다. FS는 사용자가 공급한 무차원 계수와 정규화 응력을 사용한다.
SWT는 최대 인장 법선응력과 법선변형률 진폭의 곱으로 기록한다. 전 주기가 압축이면 인장
기여는 0으로 두며 이 결과에서 수명을 역산하지 않는다.

기본 계산기의 전단 진폭은 하나의 `m` 방향 성분 범위다. 벡터 경로 계산기는 `m`과
`n × m` 성분을 함께 사용하므로 `m`의 회전·반전에 불변이다. 모든 표본쌍을 직접 비교하므로
시간·평면당 계산량은 표본 수의 제곱에 비례하고, 결과에는 지배 chord 양 끝의 sample ID를
남긴다. 이는 기록된 이산 표본의 최대 chord이며 표본 사이 continuous-time 극값, minimum
enclosing circle, rainflow 또는 다른 path-range 정의와 동일하지 않다.

minimum-enclosing-circle 계산기는 유한 전단벡터 점군을 포함하는 가장 작은 원을 결정적으로
구한다. 결과에는 원 반지름, 제공된 면내 좌표계의 중심 성분, 원을 결정하는 최대 3개 support
sample ID를 남긴다. 반지름은 면내 좌표축의 회전·반전·이동에 불변이지만 중심 성분은 선택한
좌표계에 따라 변한다. 같은 점군의 최대 chord 절반과 두 진폭의 비도 함께 보고하되, FS에는
원 반지름만 사용한다.

원 정의는 표본 순서와 무관하므로 cycle counting이나 경로 진행방향을 표현하지 않는다. 주기
폐합 검토에는 입력 순서를 그대로 사용하며, 폐합을 통과한 뒤의 유한 점군 range만 순서에
무관하다. 정삼각형 경로에서는 원 반지름이 최대 chord 절반보다 `2/sqrt(3)`배 크고, 직선
경로에서는 두 값이 같다. 어느 정의도 표본 사이 연속 경로의 외접원이나 극값을 보장하지 않는다.

세 계산기 모두 사용자가 공급한 평면 집합만 검색한다. 벡터 경로 계산기가 면내 회전을
보존하더라도 구면 전체의 연속 임계면 탐색을 완료한 것은 아니다.

## 재현 가능한 평면 후보 생성

`fatigue.hemisphere_plane_grid`는 방향이 없는 재료 평면에서 `n`과 `-n`이 같은 평면이라는
대칭을 적용해 닫힌 상반구의 유한 후보를 만든다. 극점은 한 번만 넣고 적도에서는 반대 법선인
나머지 절반을 제외한다. 중간 위도는 선언한 짝수 방위 분할을 모두 사용한다. 결과의
`candidate_planes`는 두 계수 계산기의 입력에 그대로 넣을 수 있고 각 평면 ID의 각도는 별도
`candidate_angles`에 보존한다.

위도·방위 격자는 결정적이지만 equal-area가 아니다. `polar_step_rad`와
`azimuthal_step_rad`는 생성 간격일 뿐 최대 방향오차의 상한이 아니다. 사용자는 같은 이력에
대해 분할 수를 늘려 지배 평면과 계수의 안정성을 별도로 비교해야 한다. 생성된 면내 방향은
재현 가능한 좌표 프레임일 뿐 재료 방향을 뜻하지 않는다.

`fatigue.area_uniform_fibonacci_plane_grid`는 극점에 후보가 몰리는 위도 격자의 대안이다.
방향 없는 평면을 양의 `z` 반구 내부에서 한 번씩 표현하고, `z`를 동일 폭으로 나눈 각 층의
중점에 한 후보를 놓는다. 방위각은 golden angle만큼 증가하며 사용자가 전체 phase를 바꿀 수
있다. 각 후보의 `2π/N sr` 값은 반구 적분용 명목 가중치다. 이는 최근접 Voronoi cell의 실제
면적을 계산한 결과가 아니므로 정확한 equal-area tessellation이라고 부르지 않는다.

Fibonacci 후보는 극점과 적도를 정확히 포함하지 않고 후보 수가 늘어도 이전 후보가 유지되는
nested grid가 아니다. 따라서 candidate count 및 phase를 바꾼 결과와 위도–방위 격자의 결과를
교차 비교해야 한다. 이 방식도 covering radius, 누락된 최대값의 오차 상한 또는 연속 최적점을
제공하지 않는다.

`fatigue.critical_plane_grid_family_comparison`은 같은 tensor history를 둘 이상의 위도형 또는
Fibonacci 격자로 계산하고, 명시한 한 유한 기준 격자에 대한 FS/SWT 상대 변화와 지배 법선
회전을 기록한다. 각 생성기의 전체 정의를 결과에 남기므로 후보 수와 Fibonacci phase를
재현할 수 있다. 격자 ID는 비교 안에서 고유해야 하고 기준 ID는 실제 입력 중 하나여야 한다.

기준은 연속 최적해가 아니라 사용자가 선택한 유한 격자다. 따라서 모든 비교가 선언 허용값
안에 들어와도 방향 오차 상한이 되지 않는다. 반대로 계산·보고가 검증돼도 엄격한 허용값은
정상적으로 `false`가 될 수 있다. 거의 같은 FS 최대값이 대칭 또는 평탄한 여러 방향에 있으면
계수 차이는 작아도 지배 법선 회전은 클 수 있다.

`fatigue.critical_plane_grid_refinement`는 그 비교를 명시적인 계산 계약으로 만든다. 한 이력과
두 단계 이상의 순서 있는 격자 정의, 사용자가 선언한 계수 상대변화·평면 회전 허용값을 받는다.
각 단계의 후보 수, 최대 FS/SWT, 지배 법선과 직전 단계 대비 변화를 모두 남긴다. 법선 회전은
방향 없는 평면에 맞게 두 법선 내적 절댓값의 예각으로 계산한다. 두 계수가 서로 다른 평면을
선택할 수 있으므로 변화와 회전을 각각 기록한다.

격자는 두 분할 수가 감소하지 않고 후보 수가 실제로 증가해야 한다. 마지막 변화가 선언값
안에 들어오더라도 이는 유한 표본의 진단 결과일 뿐, 표본 사이에 더 큰 최대가 없다는 오차
상한이나 수학적 수렴 증명이 아니다. 거의 같은 최대값이 여러 평면에 있으면 계수 변화는
작아도 선택 법선이 크게 이동할 수 있으므로 두 지표를 함께 검토한다. 시간 표본 세분화는
이 계산기와 별도의 과제다.

`fatigue.critical_plane_time_refinement`는 그 시간 과제를 별도 계약으로 처리한다. 한 tensor
source와 고정된 유한 평면 집합에 대해 같은 시작·종료 시각을 갖는 두 단계 이상의 표본 이력을
받는다. 표본 수는 단계마다 증가해야 하며, 각 이전 시각이 다음 단계에 사용자가 선언한 시간
오차 이내로 포함되어야 한다. 각 단계의 최소·최대 시간 간격, FS/SWT 최대값, 지배 법선과
직전 단계 대비 변화를 반환한다.

평면 집합을 고정하므로 이 비교는 시간 표본 효과와 평면 격자 효과를 섞지 않는다. 그러나
가장 미세한 표본 사이에서 발생하는 극값을 보지 못할 수 있으며, 중첩 표본과 작은 마지막
변화만으로 continuous-time 오차 상한이나 수렴을 얻을 수 없다. 모든 단계는 독립적으로 주기
폐합 조건을 통과해야 하며, 열린 이력은 안정성 결과를 만들지 않고 `needs_data`로 중지한다.

`fatigue.critical_plane_adaptive_search`는 하나의 위도형 또는 Fibonacci seed 격자를 먼저
계산한 뒤 FS와 SWT의 지배 법선을 서로 독립적으로 세분화한다. 매 단계는 현재 법선과 그
접평면의 결정적 원형 후보를 함께 평가한다. 다음 반경은 사용자가 선언한 감소율로 줄고,
현재 중심을 후보에 계속 포함하므로 표본화된 목적값은 감소하지 않는다. 각 단계의 반경,
후보 수, 선택 법선, 계수 상대변화와 방향 없는 평면 회전을 결과에 남긴다.

이 계산은 coarse-to-fine 비용 절감 도구이지 전역 최적화 알고리즘의 보증이 아니다. 초기
격자가 놓친 별도 최대 영역으로 이동하지 못할 수 있고 결과는 seed 계열·후보 수·phase,
초기 반경·ring 점 수·감소율에 의존한다. 마지막 단계의 변화가 선언 허용값 안이어도 국소
정체일 수 있다. 따라서 교차 격자 비교와 시간 세분화를 대체하지 않으며, 연속 방향 오차
상한·피로수명·규격 판정·독립 실험 검증을 제공하지 않는다.

## 검증과 공개 경계

`scripts/validate_critical_plane.py`는 폐쇄 단축 이력의 축방향 SWT, 45도 평면의 FS, 순수
tensor shear의 engineering shear 변환과 비스듬한 2차원 전단벡터 chord를 독립 폐형식 값과
대조한다. 면내 기준축의 회전·반전 불변성과 collinear 경로에서 두 계산기의 일치도 검사한다.
전용 계약 검사는 열린 주기, 중복 ID, 길이가 맞지 않는 텐서, 비단위·비직교 평면을 거절한다.
이는 수학·소프트웨어 검증이며 연속시간/평면 수렴, 재료 보정이나 독립 실험 검증이 아니다.

`scripts/validate_critical_plane_minimum_enclosing_circle.py`는 닫힌 정삼각형 전단 경로의
원 반지름, 최대 chord 절반, `2/sqrt(3)` 비와 세 support ID를 독립 평면기하와 대조한다.
계약 검사는 직선 경로의 두 진폭 일치, 불규칙 점군에 대한 1·2·3점 exhaustive 후보 해,
면내 축 회전·반전, 점 순서·좌표 이동·스케일 불변성을 추가로 확인한다. 이는 유한 점군
알고리즘 검증이며 연속시간 range, cycle counting, 방향 수렴, 수명 보정 또는 실험 검증이 아니다.

`scripts/validate_plane_grid.py`는 폐형식 후보 수, 단위 법선·면내 방향, 직교성과 정확한 법선
부호 중복 부재를 검사한다. 이는 유한 격자 기하 검사이며 equal-area 성질, 구면 covering
radius, 격자 세분화 수렴 또는 연속 최적점을 증명하지 않는다.

`scripts/validate_fibonacci_plane_grid.py`는 `z` 층 중점, golden angle, 명목 가중치 합 `2π`,
단위·직교 프레임과 중복 부재를 검사한다. 명목 가중치로 `z`와 `z²`를 적분해 각각 해석값과
유한 midpoint 합을 대조한다. 이 검사는 Voronoi cell 면적, covering radius나 연속 최적점을
검증하지 않는다.

`scripts/validate_critical_plane_grid_family_comparison.py`는 단축 해석해를 정확히 포함하는
241개 위도형 기준과 서로 다른 phase의 128개 Fibonacci 격자 두 개를 비교한다. 상대 변화
계산은 독립식과 일치하지만, 1° 법선 기준 등 엄격한 선언 기준은 의도대로 미충족이다. 이는
비교 계약 검증과 사용자 기준 충족이 별개임을 확인하며 연속 최적점을 검증하지 않는다.

`scripts/validate_plane_grid_refinement.py`는 해석적으로 지배 방향을 포함하는 단축 폐쇄 이력을
13·57·241개 후보의 중첩 격자에 적용해 모든 단계의 FS/SWT 최대값과 변화 보고를 독립식과
대조한다. 이는 포함된 방향과 보고 계약의 검사이지 포함되지 않은 방향의 오차나 연속 최적점의
검증이 아니다.

`scripts/validate_critical_plane_time_refinement.py`는 위상이 이동된 해석적 sine 주기를 고정된
두 평면에서 5·9·17·33개 중첩 표본으로 계산한다. 각 이산 최대값을 독립 표본식과 대조하고
이 예제에서 연속 sine 한계로 접근하는지 확인한다. 이는 일반 파형의 표본 사이 오차 상한이나
실험 검증이 아니다.

`scripts/validate_critical_plane_adaptive_search.py`는 Cartesian 축과 일치하지 않는 단축
폐쇄 이력을 16개 Fibonacci seed와 6단계 tangent-ring 탐색에 적용한다. SWT 연속 최댓값과
법선을 폐형식 값에 대조하고, FS 연속 최댓값은 단축 목적함수의 독립 정상조건 해와 비교한다.
또한 중심 유지로 두 목적값이 seed보다 작아지지 않는지 확인한다. 이는 이 합성 목적함수의
수학·추적 계약 검사이며 일반 이력의 전역 최적, 수렴, 보정 또는 실험 타당성 증명이 아니다.

Fatemi–Socie 원 논문과 Smith–Watson–Topper 원 논문은 계산 개념과 서지 확인에만 사용했다.
논문 문장·그림·표·데이터·코드는 배포물에 포함하지 않았고, 텐서 투영과 검사는 독립 작성했다.
ECP 공개자료에는 이 API가 요구하는 국부 tensor history가 없으므로 provider factor에서 역으로
텐서를 만들거나 새 구현의 독립 정답으로 사용하지 않는다.

