# 크리비스 1차원 중성종 반응–확산

## 목적

`integration.crevice_neutral_reactive_transport_1d`는 고정된 1차원 간극에서 사용자 선언 중성종의 확산과 공간 국소 가역 질량작용 반응을 하나의 초기값 문제로 함께 적분한다. 기존 완전혼합 반응망과 단일 성분 확산 모델을 분리해 순차 호출할 때 생기는 공간 반응률 손실을 줄이는 계산 경로다.

## 입력 계약

`CreviceNeutralReactiveTransportRequest`에는 셀 수와 형상, 셀별 초기 농도, 종별 일정 확산계수, 원소 조성, 정확한 시간 knot, 입구 농도 이력, 가역 반응의 양쪽 반응물/생성물과 전·역 속도상수 이력을 넣는다. 각 반응은 원소별 보존을 만족해야 하며 속도상수 값과 단위, 메커니즘 및 보정 support는 caller가 검토하고 근거·사용조건을 결속한다.

계산 중 `J_i = -D_i ∂c_i/∂x` 면 flux와 각 셀의 가역 질량작용 생성률을 같은 미분방정식에 결합한다. 속도상수와 입구 농도는 출력 knot 사이 선형 보간을 사용한다. 입구는 Dirichlet 경계, 막힌 끝은 무유량 경계다. SciPy BDF stiff integrator가 caller가 지정한 knot에서 상태를 반환한다.

## 결과와 보존량

결과는 각 knot의 종별 셀 농도·총 몰 재고·입구 순전달량·누적 반응 순전달량을 보존한다. 종별 전 유한체적 몰수지 잔차를 출력해 수치 적분 장부를 검토할 수 있다. 작은 잔차는 방정식의 수치 적분만 반영하며 기구 타당성이나 실험 적합을 증명하지 않는다.

## 제한

- 화학종은 중성으로 선언한다. 전기이동, 영 전류 closure, 이온 활동도와 pH는 범위 밖이다.
- 일정 확산계수·고정 형상·한 액상상의 반응-수송만 포함한다. 대류, 이동 경계, 열전달, 벽 반응 및 계면 전하를 다루지 않는다.
- rate law는 caller가 제공한 가역 질량작용 식이다. 자동 반응발견, 속도상수 추정, 상변화·침전 선택, 부식률·금속손실·수명·확률·합격 판단은 하지 않는다.
- 실제 데이터, grid/time 수렴과 독립 반응-수송 실험 검증이 필요하다.

## API 식별자

- Model ID: `integration.crevice_neutral_reactive_transport_1d`
- 입력: `CreviceNeutralReactiveTransportRequest`
- 종 contract: `ReactiveTransportSpecies`
- 반응 contract: `ReactiveTransportReaction`, `ReactiveTransportTerm`
- 계산기: `solve_crevice_neutral_reactive_transport(request)`
- Source IDs: `caller_crevice_neutral_reaction_diffusion_network`, `caller_crevice_reactive_transport_mouth_history`, `finite_volume_diffusion_with_local_reversible_mass_action`
