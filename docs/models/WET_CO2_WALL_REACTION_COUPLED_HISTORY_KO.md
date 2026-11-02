# Wet CO₂ 유한 기상·액상·벽반응 재고 이력

`integration.wet_co2_finite_gas_wall_reaction_inventory_history`는 기존 유한 기상/변동 액상 CO₂* 수송 이력에 digest가 고정된 전기화학 anodic metal-loss 이력을 연결하고, caller가 별도로 제공한 `mol CO₂*/mol removed metal` 반응 매핑을 액상 CO₂* 소모항으로 넣어 구간별 ODE와 전체 물질수지를 다시 계산합니다.

## 입력·계보 제한

- 기상 재고 용량, 초기 액상 부피/농도, 초기 기상 fugacity, Henry 계수, 양쪽 막 전달계수, 액상 체적 flux, 유입 CO₂* 및 solver tolerance는 caller 입력이며 원자료 Evidence와 함께 제공해야 합니다.
- 벽 금속 손실은 `integration.electrochemical_partial_current_metal_loss`의 `AssessmentResult`에서 가져옵니다. AssessmentResult 전체 SHA-256과 input digest를 확인하고, metal-loss 구간 시각이 gas/liquid interval과 정확히 일치하며 전기화학의 reference/exposed area가 같은 wall patch를 나타내는지 요구합니다.
- anodic 용해 금속 몰수·질량, 금속 몰질량 및 밀도로 균일 면적 평균 벽손실을 계산합니다. cathodic equivalent 또는 signed net loss로 anodic 용해량을 대체하지 않습니다.
- 반응별 CO₂* 소비량/용해금속 몰수 비는 caller 제공입니다. 해당 데이터의 Evidence digest, reaction ID, 조건 적용성, atom/carbon balance 및 면적/부피 가산 검토가 필요합니다. 전기화학 결과에서 이 비율을 추론하지 않습니다.

## 계산

각 연속 interval에서 liquid volume per area는 caller 체적 flux에 따라 변합니다. 기존 two-film 저항결합에서 계산한 transfer flux는 `J = k_overall (H f - C_CO2*)`이며, finite gas capacity와 liquid 재고가 함께 변합니다. liquid balance에는 유입/완전혼합 유출과 외부에서 강제된 caller stoichiometric wall CO₂* sink가 포함됩니다. Electrode source interval과 완전히 맞춰진 시간 구간 안에서 source metal rate와 CO₂* sink를 piecewise constant로 둡니다. DOP853으로 각 구간을 적분하고, 음의 액상 농도에 도달하면 해당 구간을 commit하지 않습니다.

구간별 장부는 기상 재고 변화, 액상 CO₂* 재고 변화, signed waterborne inflow/outflow, wall reaction CO₂* 소비량을 연결합니다. 잔차는 `final gas+liquid inventory - initial gas+liquid inventory - signed waterborne transfer + wall CO2* consumption`이며 caller 절대/상대 tolerance를 만족해야 합니다. 실패 시 완전히 계산된 앞 구간과 최초 실패만 반환합니다.

## 해석 경계

이는 검토된 electrochemical metal-loss 결과로 강제한 operator-split 물질수지 coupling입니다. CO₂* 농도 변화가 upstream 전극 current law에 피드백하지 않으며, 동시에 전극 kinetics/수송을 푸는 모델이 아닙니다. 액상은 균일 혼합이고, 반응 sink는 neutral CO₂* 재고에 대한 caller 장부입니다. Carbonate speciation, 전체 용액 조성, 전하수지, transport PDE, scale/film 생성·접착, evolving geometry, 국부 감육, risk, remaining life와 acceptance는 계산하지 않습니다. Area-average thickness loss는 geometry/additive partial-volume 및 균일감육 검토에 한정되고 pit/crevice penetration을 뜻하지 않습니다.

계산 성공은 입력 parameter의 provenance·적용성, electrochemical kinetics의 보정, sink stoichiometry의 실험 타당성이나 독립적 corrosion qualification을 보증하지 않습니다. downstream registry API를 만들 때 원 metal-loss result digest, reaction mappings, 모든 source Evidence와 solver settings를 결과에 남기십시오.
