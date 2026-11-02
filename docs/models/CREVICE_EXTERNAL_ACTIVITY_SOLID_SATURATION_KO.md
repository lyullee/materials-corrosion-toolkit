# 외부 활동도 crevice 결과의 셀별 고체 포화도 screen

`integration.crevice_external_activity_local_solid_saturation`는 계산된 `integration.crevice_local_external_activity_projection` 결과에서 caller가 지정한 exact knot의 각 cell을 기존 aqueous saturation screen에 전달한다. 입력 projection request/result와 result digest, 전체 knot 수 및 commit count, transport binding, cell index·state digest, provider identity/revision/configuration/parameter digest를 모두 맞춰야 한다. 셀마다 외부 활동도 반복 횟수, 최종 log-gamma 잔차가 선언한 tolerance 이하인지, 마지막 응답 및 전체 transcript SHA-256이 있는지도 확인한다.

각 셀에서 활동도는 molarity 1 mol/L standard state의 `aᵢ = γᵢ cᵢ/(1 mol/L)`로 구성한다. 후보 고체의 활동도 항, Ksp, source Evidence, 동일 knot의 공통 온도 및 standard-state 적합성은 caller가 제공한다. 기존 saturation 계산기를 재사용하며 셀을 혼합하지 않는다.

첫 비계산 cell에서 중단하고 성공한 cell prefix와 첫 실패를 반환한다. 이 모델은 후보별 saturation ratio만 평가한다. 고체상 선택, 석출량, 침전·용해 kinetics, 핵생성, 간극 형상 변화 또는 부식률은 추론하지 않으며, source 근거와 온도·표준상태 적용성 및 모델의 수치/실험 qualification은 별도 검토 대상이다.

결과 `values`는 상위 transport campaign의 `physical_scope_id`, 선택한 절점의 `elapsed_time_s`, 후보 고체 ID 순서 및 cell별 candidate 결과를 함께 보존한다. 따라서 여러 시간 절점의 결과와 각 결과 digest를 모으면 `integration.crevice_saturation_exposure_history`에 직접 연결할 수 있다. 이 후속 계산은 시작시각 0과 엄격한 시간 증가, 모든 절점에서 동일한 candidate/cell 순서를 요구한다. 연결은 포화비 이력 비교에 한정되며 상 선택이나 시간 사이 보간을 추가하지 않는다.
