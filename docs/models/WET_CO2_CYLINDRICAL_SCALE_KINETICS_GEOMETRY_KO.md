# 원통형 스케일 두께에서 상별 보어 형상으로 전달

## 목적

`integration.wet_co2_cylindrical_scale_kinetics_to_geometry`는 이미 계산된 상별 스케일 두께 이력과 별도의 금속 벽 후퇴 이력을 한 원통 좌표계의 형상·상별 재고로 변환한다. 기존 kinetics 모델의 결과를 수송 모델이 소비할 수 있는 기하 상태로 넘기는 결정론적 어댑터다.

## API

- 입력: `WetCo2CylindricalScaleKineticsGeometryHandoff`
- 실행: `evaluate_wet_co2_cylindrical_scale_kinetics_geometry_handoff(request)`
- 카탈로그 명세: `specifications()`
- 입력 `geometry`는 초기 치수, 상별 몰부피, 정렬된 시간점과 caller 제공 벽 후퇴를 포함한다.
- `phase_kinetics_results`에는 각 선언 상에 대한 계산 완료 `Calculation`을 제공한다. 일반 단일상 스케일 kinetics 결과와 원통 포화도 어댑터의 중첩 kinetics 결과를 읽는다.
- `layer_order_steel_to_bore`는 강재 표면에서 보어 쪽으로 향하는 방사 순서를 고정한다.
- 두 검토 플래그가 모두 참이어야 계산한다. 모든 상 두께 이력의 시간점이 geometry 이력과 정확히 같아야 한다.

각 상의 국부 두께 \(t_i\)를 방사 층 순서대로 적용한다. 상 층 경계 반지름을 \(r_o,r_i\), 축 길이를 1 m, 상 몰부피를 \(V_{m,i}\)라 하면 다음 식으로 단위 길이당 상 부피와 몰수를 계산한다.

\[
V_i' = \pi(r_o^2-r_i^2), \qquad n_i' = V_i'/V_{m,i}.
\]

벽 후퇴는 kinetics에서 추론하지 않고 geometry 입력의 caller 이력을 그대로 쓴다. 모든 방사 층이 조밀하고 연속적이라고 보는 가정 아래 최종 보어 반지름과 면적, 젖은 둘레, 전체 및 상별 부피를 반환한다.

## 계보와 사용 제한

결과에는 전체 입력 해시, geometry record 해시, phase kinetics 계산별 해시, 고정 source ID (`caller_cylindrical_scale_geometry_record`, `caller_scale_thickness_kinetics_history`, `cylindrical_annular_layer_inventory_geometry_handoff`)를 포함한다. 결과 생성은 원본 데이터의 라이선스나 실험적 적합성을 확장하지 않는다.

이 모듈은 열역학, 석출 속도, 전기화학, 금속 손실률을 계산하지 않는다. 두께 시간점 사이를 보간하지 않고, 스케일이 수송을 변경하도록 반복 계산하지도 않는다. 환형 상이 조밀하고 서로 연속하며 축대칭이라는 조건은 사용자가 확인해야 한다. 기공률, 박리, 균열, 혼합/비연속층, 원주 방향 불균일은 표현하지 않는다. 입력 방사 순서에 따라 상별 재고가 달라질 수 있으므로 순서 근거를 별도로 검토한다.

## 검토 및 검증 계획

구현 단계에서는 코드를 추가했으며 검증을 실행하지 않았다. 후속 검증은 (1) 단일 층의 원통 환형 부피와 평면 한계, (2) 다층 두께 합과 상별 부피 합 폐쇄, (3) 시간점 불일치 및 음수/비유한 두께 거부, (4) 벽 후퇴와 층 합이 보어를 소진하는 경계, (5) 층 순서 민감도, (6) 기존 transient transport geometry 입력으로의 왕복 연결을 포함해야 한다. 이는 향후 검증 항목이며 현재 검증 통과를 뜻하지 않는다.
