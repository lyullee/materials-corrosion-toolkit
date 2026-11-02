# Activity coefficient를 사용한 균질 반응속도 보정

전기화학 수송은 기본적으로 기존 mass-action rate constants와 농도를 사용한다. 선택적으로 입력에서 `homogeneous_reaction_activity_correction_reviewed=True`를 선언하면 `solve_electrochemical_transport()`에 전달한 `activity_coefficients(time_s, species_by_cell_concentration_mol_m3)` 결과를 적용해 반응률 평가 직전에 각 종 농도를 `gamma_i × c_i`로 보정한다. 이 보정은 균질 bulk reaction source에만 적용되며 Butler–Volmer 표면 속도식에는 적용되지 않는다.

## 적용 조건

- `RestrictedTransportRequest`의 activity provider ID와 configuration SHA-256을 먼저 고정하고, 같은 identity/digest를 가진 callback을 계산에 전달한다.
- callback은 입력과 같은 `(species, cell)` shape의 finite positive coefficient 배열을 반환해야 한다. callback lineage의 provider revision은 출력에 기록된다.
- 명시적인 activity correction review 외에도 기존 mass-action rate basis review, transport activity/chemical-potential review와 각 표면 반응의 검토 조건을 유지한다.
- 보정하지 않는 기존 요청은 농도 기반 mass-action 동작을 그대로 사용한다.

## 범위와 한계

`gamma × concentration`은 caller가 제공한 농도 기반 kinetics에 대한 유효농도 보정이다. rate constant 단위와 수치는 원래 caller calibration 그대로 유지된다. 이 계산은 표준상태 변환, mass-action 평형활동도, 전이상태 이론, ionic-strength dependent rate law, rate constant 재보정, 자동 반응망 선택을 제공하지 않는다. activity coefficient와 속도식이 동일한 실험/모델 정의에 맞는지, 이 곱셈 보정이 해당 kinetics에 타당한지는 caller가 검토해야 한다. 계수와 농도 곱 또는 downstream rate가 finite numeric support를 넘으면 solver가 실패로 처리한다.

기본 callback builder는 `mass_action_callback(network, activity_coefficients=gamma_callback)`이며, 완성된 수송 조합은 `ElectrochemicalTransport`의 별도 검토 gate를 요구한다. Python adapter는 이 선택을 명시하고 exact provider ID 및 digest가 request에 고정된 것과 일치해야 한다.
