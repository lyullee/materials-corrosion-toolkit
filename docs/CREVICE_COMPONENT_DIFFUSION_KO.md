# 틈새 1차원 성분 확산 계산

## 목적

`transport.crevice_component_diffusion_1d`는 틈 입구부터 막힌 끝단까지 형성되는 **사용자 정의 스칼라 성분**의 농도 구배를 계산한다. 기존 완전혼합 inventory 계산과 외부 CFD 결과 수용 인터페이스 사이의 간극을 채우는 내부 수치 API다.

이 모델이 운반하는 값은 개별 이온이라고 자동 해석되지 않는다. 예를 들어 사용자는 분석 성분, 보존 원소 inventory 또는 별도로 정의한 유효 염 성분을 선택할 수 있다. `component_id`와 `component_definition`에 그 의미를 기록해야 한다.

## 지배식과 경계조건

상수 단면의 1차원 좌표에서 다음 수지를 푼다.

\[
\frac{\partial C}{\partial t}=D\frac{\partial^2 C}{\partial x^2}+S
\]

- `C`: 사용자 정의 성분 농도, mol/m³
- `D`: interval별 유효 확산계수, m²/s
- `S`: cell별 체적 source, mol/m³/s
- 입구 `x=0`: interval별 고정 농도
- 끝단 `x=L`: 무유속

공간은 cell-centered finite volume, 시간은 backward Euler로 이산화한다. 각 사용자 interval은 `maximum_internal_step_s` 이하의 동일한 내부 step으로 분할한다. interval 안에서 `D`, 입구 농도와 source는 일정하다.

입구 face는 첫 cell 중심까지 반 cell 거리로 계산한다. 따라서 입구 전달량은 각 내부 step 끝의 농도를 사용한 implicit flux와 정확히 같은 이산 수지에 들어간다. 모델은 다음 잔차를 interval마다 보고한다.

\[
r=\Delta n-n_{mouth}-n_{source}
\]

`maximum_relative_mass_balance_error`를 넘으면 결과를 `out_of_scope`로 중단한다.

## 입력 근거와 지원범위

각 interval은 하나의 `CreviceComponentDiffusionSupport`에 연결된다. support에는 다음 정보가 고정된다.

- 성분·재료상태·bulk solution·geometry의 정확한 ID
- 온도, gap, 확산계수와 최대 지원 농도 범위
- provider ID, 버전, 모델 digest와 calibration 설명
- 공개 또는 사용자 소유 evidence

유효 interval은 provider-state digest를 반드시 가진다. support가 없거나 ID가 맞지 않거나 검토 gate가 열리지 않으면 `needs_data`다. 검토된 온도·gap·확산계수·입구 또는 초기 농도가 support 밖이면 `out_of_scope`이며 외삽하지 않는다. 계산 중 농도가 최대 지원값을 넘어도 동일하게 중단한다.

## API 사용 경계

이 API는 다음을 계산하지 않는다.

- 이온 전기이동과 전기중성 결합
- 개별 수용액 종분화, activity coefficient, pH
- 균일반응, 가수분해, 침전 또는 기체 교환
- 전극반응, mixed potential, 전류 또는 금속손실
- gap 변화, 벽면 이동 또는 국부 유동장
- 틈새부식 개시, 성장, 수명, 확률 또는 합격 판정

이 효과가 중요하면 별도 aqueous mass-action, electrochemical, kinetic-network 또는 외부 CFD provider 결과와 digest-pinned 방식으로 연결해야 한다. 특히 전하를 띤 개별 종을 독립 Fick 확산으로 해석해서는 안 된다.

## Python 연결

직접 Python 호출은 `CreviceComponentDiffusionHistory`를 구성하고 `crevice_component_diffusion_history()`에 전달한다. Registry 통합 후에는 모델 ID `transport.crevice_component_diffusion_1d`를 사용한다. `RunContext.asset_id`, `location_id`, `time_basis`는 각각 입력의 asset, location, `clock_id`와 정확히 일치해야 한다.

주요 출력은 다음과 같다.

- cell 중심 좌표
- 사용자 clock knot별 농도 profile과 총 mol inventory
- interval별 입구 전달량, 체적 source 전달량, inventory 변화와 수지 잔차
- 내부 step 수와 최대 상대 수지오차
- 농도 history의 canonical SHA-256

모든 출력은 계산 재현과 다른 모듈 연결을 위한 screening record다. 현장 건전성 또는 규격 적합성 결론이 아니다.
