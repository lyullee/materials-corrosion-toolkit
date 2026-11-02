# 전류 전달형 크리비스의 개구·수송·Faradaic 고정점

## 계산 목표

`integration.crevice_current_carrying_aperture_feedback`는 caller가 제공한 침전/용해 부피-개구 민감도와 개구-면속도 민감도를 사용해, 가변 형상 Nernst–Planck 수송, 공간 혼합전위, Faradaic 벽 source, 정확 시간 절점의 수용액/고체 화학을 하나의 제한된 반복 계산으로 연결한다. 새 반응, 고체상, 수리 법칙 또는 기구를 검색하지 않는다.

## 반복 상태와 계산 순서

각 반복은 현재 개구 이력으로 셀·면 단면적을 만들고, caller 선형 민감도에서 축방향 face velocity를 갱신한다. 면적 digest와 Evidence를 새 시험 geometry에 맞춰 다시 묶은 후 전류 전달형 solver를 전체 요청 시간구간에 대해 다시 계산한다. 각 절점의 끝 상태에는 수용액 종과 유한 고체 inventory, Faradaic extent 및 혼합전위/이온 면전류가 포함된다.

고체 부피 변화는 caller가 제공한 상별 몰부피와 cell plan area를 통해 target aperture로 변환한다. Trial aperture는 relaxation 계수로 완화한다. aperture와 face velocity의 최대 잔차가 각각 절대/상대 허용오차 안에 들어올 때만 전체 이력이 커밋된다. 수렴에 실패하면 계산 결과는 실패 상태이며, 수용된 interval은 없고 각 시도 input/result/geometry digest와 잔차를 `iteration_prefix`에 남긴다.

## Caller 입력 계약

- `CreviceCurrentCarryingNernstPlanckRequest`: 현재전달형 다종 수송과 Faradaic/혼합전위/화학 연성 설정
- 상별 양의 고체 몰부피와 digest/Evidence
- cell별 고체 부피에서 aperture로 가는 양의 mapping 계수, cell plan-area mapping 및 그 digest/Evidence
- exact knot × face × cell의 hydraulic velocity sensitivity와 Evidence/digest; blind-tip velocity 증분은 0이어야 한다
- face-to-cell 면적 보간 가중치. 모든 행의 합은 1이고 mouth/tip은 인접 셀에 고정 매핑한다
- 개구/수리 고정점 허용오차, 반복 및 총 transport/mixed-potential solver 예산
- caller 물리 매핑, mesh, 전류 경계, solver 예산 및 사용 허가 확인

Molar-volume map은 caller가 사용하는 고체상 전체와 일치해야 한다. 모든 형상/수리 반응은 제한된 선형 민감도 mapping이다. 별도의 pressure-flow 또는 deposition morphology 모델을 내장하지 않는다.

## 전류와 형상의 결합 경계

각 geometry trial은 독립적으로 기존 current-carrying NP/Faradaic 계산을 재실행한다. 내부 면 이온 전류는 `F A_face Σ z_i J_i`로 계산되고 전위 기울기 이동항과 맞아야 한다. 계면 Faradaic 벽 전류는 종 source와 고체/수용액 inventory 변화로 따로 처리된다. 혼합전위 face current와 NP constitutive flux가 일치하지 않으면 그 geometry trial부터 실패한다.

Exact knot 사이 면적과 속도는 현재 core의 규약에 따라 선형 보간된다. 매 outer iteration에서 얻은 endpoint 고체 inventory를 반영해 그 보간 geometry 전체를 다시 수송/전기화학 계산한다. 다만 BDF 내부 stage마다 누적 precipitation으로 geometry를 즉시 갱신하는 완전 동시 연속시간 해석은 아니다. 끝 절점 고체량 기반 fixed-point feedback이며, endpoint 전후의 operator split과 고정점 반복을 사용한다.

## 예산·실패·출력

요청은 전체 geometry 반복 budget을 두고, 매 시도에 남은 transport와 mixed-potential evaluation budget을 전달한다. 어느 한쪽 예산을 초과하거나 전류 전달 solver가 실패하면 계산은 fail closed다. 고정점에 수렴하지 않아도 결과를 물리 계산 성공으로 표시하지 않는다. 성공 결과에는 수렴 geometry와 velocity, aperture/velocity residual, 각 iteration digest 계보, 마지막 current-carrying 계산 전체 결과 및 누적 solver 호출 수가 포함된다.

수치 잔차가 작다는 사실은 caller mapping 또는 원료 물성의 타당성, 계산 검증, 독립 실험 일치, 재료 qualification을 의미하지 않는다. caller 선형 민감도는 초기 geometry 부근의 응답으로만 적용 가능하며, 비선형 또는 큰 aperture 변화에서 외삽하지 않아야 한다.

## 범위 제한

- 고체 몰부피, aperture mapping, face area weights, hydraulic sensitivity, kinetics, 전도도와 화학은 caller 소유다.
- 전체 시간 이력을 반복하는 knotwise fixed-point wrapper다. BDF 내부 stage의 precipitation-geometry 동시 상태 적분은 구현하지 않았다.
- double-layer charging, 유체 압력상태 방정식, 벽/금속 전위 손실, 반응/상 자동 발견 및 qualification은 포함하지 않는다.

## API 식별

- Model ID: `integration.crevice_current_carrying_aperture_feedback`
- Request: `CreviceCurrentCarryingApertureFeedbackRequest`
- Evaluator: `solve_crevice_current_carrying_aperture_feedback`
- Contract: `matintegrity.crevice_current_carrying_aperture_feedback.v1`
