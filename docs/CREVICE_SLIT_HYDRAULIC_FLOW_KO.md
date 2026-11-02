# 가변 개구부 슬릿 유동 계산

`corrosion.planar_slit_hydraulic_flow`는 압력차가 주어진 긴 평행판 틈새에서 정상·비압축성·뉴턴 유체의 층류 유량을 계산하고, 결과를 `RestrictedTransportRequest.axial_advection_velocity_m_s`에 연결할 수 있도록 셀 면 속도를 반환한다.

시간별 `PlanarSlitApertureHistory`가 있으면 `corrosion.planar_slit_hydraulic_history`에 전체 history 결과와 그 canonical SHA-256, 같은 시각 수의 압력차 배열, 압력 이력 source digest를 준다. 정적 유체 물성 source digest도 명시한다. 이 adapter는 각 geometry knot의 개구부에서 정상 유동을 다시 계산하고 시각별 pressure, flow, face velocity를 보존한다. 모든 knot가 계산범위를 만족할 때만 전체 history가 `computed`다. 각 face velocity 행을 해당 고정 geometry의 수송 계산에 연결해 순차 operator-split 반복을 구성할 수 있다.

## 모델

셀 `i`의 길이 `L_i`, 개구부 `h_i`, 폭 `w`, 점도 `mu`에 대해 넓은 슬릿 근사를 적용한다.

```text
R_i = 12 mu L_i / (w h_i^3)
R_total = sum(R_i)
Q = delta_P / R_total
u_i = Q / (w h_i)
```

셀은 유압 저항 직렬로 연결되며 `Q`는 모든 셀에서 같다. 내부면 개구부는 인접 셀 중심 사이를 셀 길이로 가중 선형 보간하고, 면 속도는 `Q/(w h_face)`로 계산한다. 셀별 압력 강하를 누적해 경계 압력을 재구성한다. 이 계산은 균일한 단면의 전체 길이 적분을 위한 감산 모델이다.

## 입력과 연결

- 미터 단위 셀 길이와 개구부, 횡방향 폭
- 부호 있는 입구-출구 압력차 `Pa`(양수는 mouth-to-tip, 음수는 tip-to-mouth, 0은 정체), 동점도가 아닌 동적점도 `Pa s`, 밀도 `kg/m3`
- 유체 물성 source의 SHA-256, history 모드에서는 별도 pressure-history source SHA-256
- 기하/압력 경계, 유체 물성, 완전 발달 층류 가정에 대한 caller 검토
- 선택적으로 `PlanarSlitApertureHistory` 결과 전체를 `aperture_history_result`로 전달하고 그 canonical digest를 `geometry_source_sha256`에 고정
- history 계산에서는 압력과 aperture clock이 knot별로 정렬된다는 별도 검토

정상 계산 결과의 `transport_face_velocity_m_s`는 수송 계산의 `axial_advection_velocity_m_s`에 대응한다. 이어서 `axial_advection_provider_id`에는 `flow_id`, `axial_advection_configuration_sha256`에는 `input_sha256`을 연결한다. history 결과는 같은 속성들을 각 `flow_snapshots` 행에 보존한다. 압력차 부호는 face velocity 부호로 전달되며 Reynolds 판정에는 속도 크기를 사용한다. 정적 또는 시간변화 속도 중 어느 경로든 음의 말단 face velocity가 있으면 `axial_flow_reversal_and_tip_boundary_reviewed=true`와 종 순서가 맞는 `tip_advection_inflow_mol_m3`가 필요하다. mouth/tip 유입 농도는 caller의 별도 경계자료이며 압력 이력에서 추정하지 않는다. 수송 쪽 연속성·시간변화·유동방향·말단 유입 농도 검토는 각각의 수송 계약에서 선언해야 한다. 0 압력차는 0 유량의 유효 상태다.

Registry 결과를 쓸 때 `matintegrity.bind_planar_slit_hydraulic_snapshot(request, history_assessment, history_result_sha256, snapshot_index)`는 전체 assessment digest와 등록 input digest를 확인한 뒤 선택 snapshot의 signed velocity, flow ID, snapshot input digest, 전체 upstream result digest, history source 시각 및 time-basis ID를 transport request에 설정한다. history와 snapshot 상태, face 수, 중복 advection provider도 검사한다. 역류면 기존 distal-inflow 검토 및 농도 입력이 있어야 한다. 이 함수는 농도 경계나 연속성 검토를 대신 설정하지 않으며 계산을 실행하지 않고 검증된 새 요청 객체를 반환한다. 선택한 snapshot이 요청된 fixed-geometry segment에 해당하는지 caller가 시간축에 따라 결정해야 한다.

연속한 모든 history interval을 잇는 입력이 준비되면 `matintegrity.bind_planar_slit_hydraulic_history_series(segment_requests, history_assessment, history_result_sha256)`를 쓴다. 요청 개수는 인접 knot 쌍 수와 같아야 하며 각 transport request의 local output clock은 0부터 대응하는 history interval 길이까지 정확히 이어져야 한다. interval 시작 knot의 velocity snapshot을 고정해 묶는다. 각 segment에서 geometry/flow를 고정하는 operator-split 가정과 각 요청의 반응·농도 초기조건은 caller가 별도로 정한다. 반환은 transport 요청들의 tuple이며 transport 계산을 수행하지 않는다.

## 적용성 및 한계

병렬판 근사는 최소 폭/개구부 비가 20 이상이고 Reynolds 수가 caller가 낮춰 지정할 수 있는 상한 1000 이하일 때만 결과 상태를 `computed`로 준다. Reynolds 수는 `D_h=2wh/(w+h)` 직사각형 수력직경으로 표시한다. 압축성, 비뉴턴 유변학, 과도 관성, 입·출구 손실, 거칠기, 난류, 횡방향 유동, 응력으로 인한 개구부 변화와 시간 내 유동-부식 동시 결합은 풀지 않는다. 각 항목의 물성·압력·기하 근거와 수치 한계는 caller가 검토해야 한다. 계산기 종료는 모델의 실험 검증이나 특정 재료/설비의 적합성 승인이 아니다.

합성 입력 형태는 [`examples/crevice_hydraulic_flow.py`](../examples/crevice_hydraulic_flow.py)에서 확인한다. 예시 숫자는 권장 운전조건이나 실측자료가 아니다. 시간별 결과는 knot 사이 압력·유동을 풀지 않으며 완전 연성 계산으로 해석할 수 없다.
