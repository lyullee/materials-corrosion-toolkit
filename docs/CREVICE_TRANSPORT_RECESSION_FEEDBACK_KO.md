# 수송 기반 틈부식 간극 되먹임

`solve_crevice_transport_recession_feedback`는 이미 제공되는 고정 형상 보존 수송 계산과 cellwise 금속 벽 ledger를 순차적으로 연결한다. 호출자는 `PlanarSlitGeometry`, `RestrictedTransportRequest`, `CreviceTransportRecessionFeedback`, 계산 시각 및 수송 callback을 공급한다.

## 계산 순서

1. 기본 설정에서는 연속 출력 시각 사이에서 현재 셀별 aperture를 고정해 restricted transport를 계산한다. 선택적으로 `maximum_geometry_update_step_s`를 지정하면 각 출력 구간을 그 최대 간격 이하의 내부 구간으로 나눠 형상을 더 자주 갱신한다.
2. 선택한 금속 종의 구간 누적 벽 유입량을 셀별로 읽는다. 양의 signed ledger는 용액 방향 금속 용출로 해석하도록 caller가 검토해야 한다.
3. 축 단면 기준 ledger를 reactive wall area 기준으로 바꾸고 금속 몰질량/밀도로 나누어 signed 셀 평균 recession을 계산한다.
4. 금속 제거를 양의 recession으로 두고, 양면이 반응하면 검토된 동일 recession 가정으로 간극을 넓힌다. 재석출은 음의 recession으로 간극을 줄인다. 갱신 간극은 caller의 aperture 지원 범위 안이어야 한다.
5. 다음 수송 구간을 위해 각 셀 농도를 새 셀 부피에 맞춰 재조정하여 cellwise inventory를 보존한다.

## 구간 내부 간극 되먹임 옵션

`within_segment_geometry_feedback_enabled=true`를 선택하면 위의 기본 구간별 고정형상 계산 대신 각 시간 구간 안에서 제한된 끝점 고정점 반복을 사용한다. 현재 셀 간극에서 시작해 끝 간극 추정치를 만들고, 시작·끝 단면적과 반응 벽면/부피 이력을 선형으로 구성한다. `solve_restricted_transport()`는 움직이는 셀 부피에 따른 보존항 `-C (dV/dt)/V`와 시간별 벽면적을 사용해 해당 경로의 농도와 signed 금속 벽 원장을 계산한다. 셀별 원장을 몰질량·밀도·반응 벽면 기준면적으로 변환해 다음 끝 간극을 예측하고, 선언된 relaxation으로 추정치를 갱신한다.

각 반복의 입력·결과 digest와 상대 끝점 잔차를 남긴다. 잔차가 `within_segment_relative_aperture_tolerance` 이내일 때만 해당 수송 구간을 확정한다. 비수렴, 지원 aperture 이탈 또는 적응형 aperture 변화 제한 초과 때는 그 구간의 상태를 반영하지 않는다. 옵션에는 geometry feedback 검토, 별도 수렴 검토, 결정적 callback 재평가 검토, `maximum_geometry_update_step_s`, `maximum_relative_aperture_change_per_segment`, 반복 횟수·완화율·잔차 허용치와 전체 구간 예산이 필요하다. 선형 간극 경로는 수치 반복을 위한 caller가 승인한 근사 이력이며, solver가 물리적 경계 궤적을 추론하지 않는다.

기본 fixed-point 옵션은 축방향 advection을 허용하지 않는다. 별도 `within_segment_hydraulic_feedback_enabled=true`를 켠 경우에만 steady slit hydraulics의 start/end 해를 연결해 구간 내부 유동을 제한적으로 반영한다. 이 선택에도 transient momentum이나 완전한 pressure-flow-geometry 연성은 포함되지 않는다. 화학 평형·표면 반응계수도 간극 변화에 따라 갱신하지 않는다.

선택적 `steady_hydraulic_recalculation_enabled` 모드는 caller가 제공한 pressure-drop history, fluid-property source digest, 점도·밀도와 모델 가정 review를 받아 steady planar-slit face velocity를 함께 계산한다. 초기 속도는 첫 transport segment에 적용하고, 각 accepted geometry/pressure knot에서 다시 계산한 속도는 다음 segment의 정적 advection field로 전달한다. 압력 이력은 원래 요청 output clock과 정확히 일치해야 한다. 별도 advection velocity/provider는 함께 지정할 수 없다. 내부 시간 세분화 또는 adaptive aperture rejection을 함께 쓸 때는 `pressure_history_interpolation="piecewise_linear"`와 `pressure_interpolation_reviewed=true`를 명시해야 한다. 선언된 압력 knot 사이에서만 선형 보간하며 외삽하지 않는다. 각 유동 결과는 사용한 양쪽 pressure knot와 보간 분율을 기록한다. 이는 입력 압력의 표본 재구성 가정이지 과도 압력 모델이 아니다.

### 구간 내부 steady-hydraulic endpoint coupling

within-segment geometry fixed-point와 steady hydraulics를 함께 연결하려면 `within_segment_hydraulic_feedback_enabled=true` 및 `within_segment_hydraulic_velocity_path_reviewed=true`를 선언한다. steady hydraulics, piecewise-linear pressure history와 그 review, flow-continuity review도 필요하다. 각 geometry/metal-flux 반복에서 solver는 현재 accepted 시작 aperture의 steady face velocity와 추정 끝 aperture·끝 압력의 새 steady face velocity를 계산한다. 수송 callback에는 두 velocity vector 사이의 시간 선형 경로를 전달하고, 해당 경로의 provider/configuration/source-result digest를 저장한다. 벽 금속 원장에서 예측한 새 끝 aperture로 hydraulic endpoint를 다시 계산하며, geometry fixed-point tolerance를 만족한 구간만 commit한다.

재사용 가능한 `PlanarSlitEndpointVelocityPath` contract가 두 endpoint의 global time, 동일 face grid 속도 배열, 계산 결과·입력 digest, 압력 source와 보간 lineage를 묶는다. 이 객체는 restricted-transport callback으로 직접 전달할 수 있고 `provider_id`, `configuration_sha256`, `source_sha256`를 제공한다. 호출 시 segment-local elapsed time을 요구하고 검토 interval 밖 외삽을 거절한다.

속도 경로의 시간 선형성은 계산 결과가 아니라 caller가 승인해야 하는 모델 가정이다. 실제 속도가 aperture·pressure 경로를 따라 선형이라는 보장은 없고, 단면별 steady flow 계산을 과도 유동 해석으로 바꾸지 않는다. 어느 endpoint face에서든 역류가 있으면 reviewed reversal과 distal inflow concentration을 요구한다. 범위 밖 pressure 표본, 지원 범위 이탈, callback 실패 또는 iteration 예산 초과는 해당 구간을 미확정으로 남기고 앞서 commit된 prefix를 보존한다. transient momentum, within-segment pressure dynamics, chemical equilibrium/kinetics feedback 및 qualification은 지원하지 않는다.

| 설정 | 용도 | 필요한 선언 |
|---|---|---|
| `pressure_history_interpolation="exact_requested_knots"` | 요청된 geometry/transport knot에서만 유동 재계산 | `pressure_interpolation_reviewed=false`; geometry 내부분할·adaptive aperture refinement 미사용 |
| `pressure_history_interpolation="piecewise_linear"` | 내부 geometry-update 시각의 압력 계산 | `pressure_interpolation_reviewed=true`; 압력 이력은 요청 clock의 모든 knot와 정렬 |

압력 보간은 내부 segment의 끝 형상을 다음 구간에 적용하기 위한 단계별 경계 입력이다. pressure 자체의 급변, 지연, 유동 관성은 추정하지 않는다. 결과 `steady_hydraulic_history`의 각 record에서 `pressure_interpolation_lineage`의 원본 pressure 표본 시간·index와 보간 분율을 확인한다.

추가 적응형 제어를 사용하려면 `maximum_relative_aperture_change_per_segment`를 지정한다. 계산된 구간의 최대 셀별 상대 aperture 변화 `max_i(|h_i,new-h_i,old|/h_i,old)`가 이 값을 넘으면 해당 수송/기하 시도는 미확정 상태로 버리고 중간 시각에서 구간을 이등분해 두 하위 구간을 처음부터 계산한다. 이를 켜면 기하 갱신 정책 검토와 callback 재평가 결정성 검토, `maximum_adaptive_aperture_refinements` 및 전체 `maximum_internal_segments` 예산이 필요하다. 출력은 거절 시도의 시각·변화량·한도·제안 분할시각·시도 결과 digest와 실제 수락된 시간 격자를 보존한다. 기준 상태, 농도와 ledger는 하위 구간 계산이 성공하기 전까지 바뀌지 않는다.

## 필수 검토

모델은 금속 원자 1개/선택 종 1 mol 가정, 모든 선택 벽 flux의 금속 용출/재석출 의미, slit-to-wall 면적 mapping, 지정된 transport-clock 정렬과 선택한 구간 내 형상 정책의 적합성 review를 요구한다. 내부 간격 기능을 켜면 사용자가 시간 표본화 적합성을 검토해야 한다. `maximum_internal_segments`는 전체 내부 구간 수를 제한한다. 두 broad face를 사용하면 양면 recession 동일성도 별도로 확인한다. 외부 callback은 구간 시작 시각을 더한 전역 campaign 시간을 받으며, 지정된 입구 농도 이력은 원래 출력 시각 사이에서 선형 보간한다.

## 범위와 제한

기본 경로와 steady slit 유동 경로는 구간별 operator split이며 각 수송 계산은 해당 구간 시작 간극을 유지한다. 선택적 fixed-point 경로는 승인된 선형 aperture 이력으로 단면적 이동항을 반영하지만, 유동·압력·화학·상변화와 동시 연성은 해결하지 않는다. 시간간격, 반복 허용치와 상대 aperture 업데이트 한도를 줄여 민감도를 조사할 수 있지만, 이를 완전한 moving-boundary 해석으로 간주하면 안 된다. 계수 보정·실험 qualification, 부식률 판정, 잔여수명이나 합격 기준은 계산하지 않는다. 결과는 검토된 caller 모델에 대한 수치 시나리오다.

계산 테스트 및 물리 qualification은 아직 수행하지 않았다. 본 API 사용 전 전체 회귀와 독립 기준해/실측 비교를 수행해야 한다.

Synthetic wiring example: `examples/crevice_endpoint_hydraulic_feedback.py`. It deliberately uses illustrative values and callbacks; replace them with source-bound inputs and reviewed material/fluid assumptions before use. Running the example performs a model calculation and does not constitute validation.
