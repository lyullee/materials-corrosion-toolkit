# CO₂ Henry 온도 보정 → 탄산염 평형 어댑터

`integration.co2_henry_temperature_to_fixed_fugacity_carbonate`는 digest가 검증된 `chemistry.co2_henry_vant_hoff_temperature_correction`의 `AssessmentResult`를 기존 `chemistry.fixed_fugacity_carbonate_equilibrium` 계산으로 전달합니다. 새 Henry 계수는 기준자료에서 추가 값을 만들지 않고, 보정 API가 산출한 계수만 사용합니다.

## 전달 전 검증

어댑터는 correction 모델 ID와 `computed` 상태, correction request의 전체 JSON 입력, AssessmentResult input digest, 단위 `mol/L/Pa`, source reference digest, 온도, 용매 조성 digest, provider configuration/revision, correction result digest 및 양의 유한 계수를 확인합니다. 결과를 검토하는 caller 승인도 요구합니다. 실패하거나 상태가 계산 완료가 아니면 탄산염 solver를 호출하지 않습니다.

파생 Henry record에는 목표 온도, 농도/fugacity 단위 관례, 동일 용매 조성 digest, correction model revision, correction `input_digest`와 `result_digest`가 들어갑니다. Henry 근거는 입력 reference의 `Evidence`와 correction output digest를 가리키는 파생 계산 Evidence를 모두 보존합니다. carbonate request의 온도는 목표 온도와 허용오차 내에서 맞아야 하고, solvent digest는 correction request와 같아야 합니다. carbonate constants 역시 기존 solver가 요청 온도와 맞는지 검사합니다.

## 계산 범위

기존 solver는 고정된 CO₂ fugacity와 Henry 관계로 용존 CO₂*를 구하고, carbonate equilibrium constants와 caller가 제공한 total alkalinity로 `CO₂*`, `HCO₃⁻`, `CO₃²⁻`, `H⁺`, `OH⁻`, 활동도 기준 pH를 풉니다. 따라서 **탄산염 부분계의 계산이며 용액 전체 조성 계산이 아닙니다.** 다른 양이온/음이온, 전하수지 기반 완전 speciation, 반응 네트워크 자동 생성, gas inventory, corrosion rate, scale, 재료 응답은 포함하지 않습니다.

새 입력은 `Co2HenryCarbonateAdapterRequest`입니다. `carbonate_equilibrium`에는 기존 carbonate 요청과 동일한 모든 필드를 제공하되 `henry`는 생략 또는 null로 둡니다. 어댑터가 digest 검증된 보정 결과로만 Henry record를 생성합니다. 대상 API 문서는 [Henry 온도 보정](CO2_HENRY_VANT_HOFF_KO.md)과 기존 고정 fugacity 탄산염 평형 문서를 함께 참조합니다.

## 코드·자료 근거

van't Hoff 관계는 IDAES 공개 열평형 문서와 NIST CODATA 기체상수 기록을 참조하며, carbonate equilibrium 계산은 기존 API와 그 근거 기록을 사용합니다. 원문 문장, 표 또는 매개변수 데이터는 포함하지 않습니다. 파생 결과 digest는 계산 lineage 식별자이며 독립 실험 검증이나 물리 qualification을 의미하지 않습니다.
