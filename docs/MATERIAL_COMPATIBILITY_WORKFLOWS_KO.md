# 재료 compatibility와 제조품질 증거 워크플로

이 문서의 계산기는 사용자가 소유·검토한 qualification envelope와 기록을 구조화한다. 재료별 허용표, 설계규격 수치 또는 합격 규칙은 포함하지 않는다.

## Polymer

`materials.polymer_compatibility_envelope_match`는 grade, condition, medium, concentration unit과 mechanical-loading descriptor를 exact match한다. Lot은 exact-lot declaration이 기본이며, grade-level envelope는 호출자가 lot transfer를 별도로 검토한 경우에만 후보가 된다. 온도, 절대압, 농도와 누적 노출시간이 한 envelope 안에 모두 들어가야 한다. 복수 후보가 동시에 맞으면 임의 선택하지 않고 `needs_data`, identity는 맞지만 범위가 벗어나면 `out_of_scope`다.

이 모델은 swelling, permeation, chemical reaction, degradation rate, mechanical-property retention, lifetime 또는 혼합물 상호작용을 계산하지 않는다.

## Composite

`materials.composite_compatibility_assessment`는 laminate, resin, fiber, manufacturing condition, layup과 environment identity를 qualification envelope와 비교한다. Service exposure의 온도·moisture mass fraction·절대압·누적시간을 기록하고, coupon과 source group의 calibration/holdout partition을 보존한다. 같은 source group이 두 partition에 나타나거나 한 partition 근거가 없으면 완전한 결과를 만들지 않는다.

이 모델은 laminate micromechanics, ply stress, strength knockdown, delamination growth, fatigue 또는 service lifetime을 예측하지 않는다.

## Casting과 forging 품질기록

`materials.casting_forging_quality_record`는 component·heat·manufacturing route, heat-treatment 이력, inspection region coverage와 indication을 연결한다. 정량 관측은 measurement definition, exact unit, expanded uncertainty와 caller limit를 함께 보존한다. 관측 uncertainty interval이 사용자 최대값을 넘는지와 nominal 비교를 구분한다. 정성 관측은 수치로 변환하지 않는다.

결과는 inspection evidence accounting이며 defect criticality, fracture driving force, remaining life 또는 acceptance 판정이 아니다.

## Bonded layer

`materials.bonded_layer_integrity_assessment`는 substrate/layer/interface/process/lot identity, region coverage, bond strength 또는 interface indication과 expanded uncertainty를 caller-owned requirement에 비교한다. Caller disposition은 만족·불만족·미확정 상태별로 분리해 보존한다. 이 결과는 delamination growth, interface fracture, residual stress, lifetime 또는 code acceptance가 아니다.

## Under-insulation exposure

`degradation.under_insulation_exposure_history`는 explicit interval의 surface temperature, wetness state와 insulation condition이 caller-owned exposure definition에 동시에 포함되는 시간을 합산한다. 총 분류시간과 최대 연속시간을 반환하며 invalid·uncovered time은 분류하지 않는다.

`under_insulation_inputs_from_condensation_result`는 완전한 `fabrication.insulation_condensation_exposure` 결과만 받아 보수적 결로 가능 interval을 caller CUI 정의에 전달한다. 원 결과 digest와 source model ID를 보존하고 상태 의미를 “측정 습윤 또는 실제 물 유입이 아닌 열역학적 결로 가능성”으로 고정한다.

분류시간은 CUI corrosion rate, metal loss, SCC initiation, remaining life 또는 failure probability가 아니다. 다음 단계의 손상 모델에는 독립 보정자료와 정확한 물리 위치·재료·inspection evidence가 필요하다.

## 외부 모듈 연결

각 결과는 원 identity, status, 누락 또는 범위 밖 사유를 유지한다. 위험성 평가나 FTA에 연결하려면 별도 adapter에서 사건 정의, 기간, 조건부 기준, 관측 불확실성과 calibration 근거를 명시한다. `computed` 또는 envelope match를 합격·정상·고장확률로 재명명하지 않는다.
