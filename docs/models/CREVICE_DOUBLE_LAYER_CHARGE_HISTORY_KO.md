# Crevice 이중층 전하 이력

`integration.crevice_double_layer_charge_history`는 호출자가 제공한 전극 전위·활성 면적 이력과 미분용량 곡선에서 제한된 범위의 이중층 저장전하와 용량전류 이력을 계산한다.

요청에는 정확한 시간 knot과 셀 순서, knot·셀별 전위 행렬, 같은 위치의 활성 면적, 셀별 기준 전위, 공통 미분용량 곡선 `C_d(E)`가 필요하다. 전위축은 엄격히 증가해야 하며 곡선은 구간별 선형으로 해석한다. 계산기는 기준 전위부터 입력 전위까지 각 선형 구간을 정확히 적분하고 면적을 곱해 저장전하를 구한다. 구간 평균 전류는 저장전하 변화량을 경과시간으로 나눈 값이며, 기준전위 방향에 따라 부호가 달라진다.

전체 곡선과 면적·기준전위·셀·시계열 매핑은 digest로 고정된다. `Evidence`에는 API의 source ID와 이용조건 식별자가 있어야 한다. 입력 검토는 곡선의 적용성, 면적과 전위의 정합성, knot 사이 선형 충전 해석, 이중층 전류만 계산한다는 해석 경계, 계산량 제한을 명시적으로 다룬다.

## Python API와 예시

요청·결과 형식은 `CreviceDoubleLayerChargeHistoryRequest`와 `Calculation`이다. 직접 호출은 `evaluate_crevice_double_layer_charge_history`를 사용한다. `specifications()`는 schema와 catalog 생성에 모델을 등록한다.

[`examples/crevice_double_layer_charge_history.py`](../../examples/crevice_double_layer_charge_history.py)는 입력 digest를 구성하고 Python API를 호출하는 방법을 보여준다. 이 예제 숫자는 형식 설명을 위한 합성값이며 실험자료, 강재 용량 곡선, 보정 또는 검증 결과가 아니다.

## 계산 범위

이 API는 전극 전위, 활성 면적, 용량 곡선, Faradaic 전류, Nernst–Planck 이동, 혼합전위, 반응속도, 금속 손실 또는 재료 자격을 계산하지 않는다. 출력 전류는 호출자 이력에서 구한 구간 평균 이중층 충전전류다. 이를 완전한 전기화학 시뮬레이션으로 부르거나 단독으로 위험·수용성 판단에 사용하지 않는다.

## 현재 BDF 혼합전위 경로가 이 전류를 사용하지 않는 이유

선택형 component-state BDF 경로는 매 trial 조성에서 준정상 공간 혼합전위를 다시 풀고 Butler–Volmer 전류밀도에서 branch 반응 extent rate를 산출한다. 같은 RHS 평가에서 `I_right - I_left = F Σ(z_i ν_i r_i)`가 성립해야 한다. BDF 상태에는 수용액 보존 성분 재고가 있지만 계면 저장전하나 전극전위 상태는 없다. 국소 수용액 평형 템플릿은 정확한 전기중성 제약도 유지한다.

여기서 계산한 구간 평균 전류를 그 수지에 더하면 서로 다른 전기 상태, 즉 기존 solver가 대수적으로 결정한 준정상 전위와 독립적인 호출자 지정 전위 이력을 섞게 된다. 또한 내부 BDF 시간 단계에서 계면 저장전하를 일관되게 진화시킬 상태식도 없다. 따라서 용량전류를 외부 schedule로 넣으면 기존 Faradaic 전하 폐합이 깨지거나, 지배방정식을 바꾸지 않은 채 구동전위 모델로 의미가 바뀐다.

정합된 연성 모드를 만들려면 명시적인 계면전하 상태와 전위–전하 구성식, 전류 부호·기준 규약, stage 수준의 이온/Faradaic/용량 전류수지, 그리고 보존 성분·저장소 장부가 필요하다. 이 계약이 설계되기 전까지 두 API는 서로 독립으로 유지한다.

후속 solver 계약의 자세한 요구사항은 [`CREVICE_DOUBLE_LAYER_BDF_COUPLING_KO.md`](../extension_requests/CREVICE_DOUBLE_LAYER_BDF_COUPLING_KO.md)에 정리했다.
