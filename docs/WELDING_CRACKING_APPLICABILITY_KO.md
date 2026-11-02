# 용접 균열 applicability 기록

이 문서의 모델은 사용자가 소유하고 적용성을 검토한 qualification envelope와 시험 증거에 생산 조건이 포함되는지 구조화한다. 규격 수치표, 재료 순위, 균열 발생이나 합격 판정을 제공하지 않는다.

## Solidification cracking

`welding.solidification_cracking_applicability`는 weld-metal condition, welding process, consumable classification·lot, chemistry basis/profile, thermal-history, strain과 restraint descriptor를 exact identity로 비교한다. Qualification record에는 물리 시편·source group, 시험 방법, metric 정의·단위·불확도와 provider/configuration/input/result digest가 필요하다. 결과는 chemistry limit, cracking index, 발생확률, 결함 크기나 수명이 아니다.

## Reheat cracking

`welding.reheat_cracking_applicability`는 material/weld/HAZ condition, process, heat-input 값과 단위, 시간순 thermal interval, reheat 온도·누적시간, stress 값·단위와 restraint descriptor를 caller support에 비교한다. Qualification observation의 region, specimen/source group, method, metric, uncertainty와 provider lineage를 보존한다. 열이력 지원범위 확인은 조직 변화나 균열 민감도 계산이 아니다.

## Lamellar tearing

`welding.lamellar_tearing_applicability`는 parent material, product form, directionality, governing thickness, joint geometry, through-thickness loading, restraint, process·consumable과 heat-input 범위를 비교한다. 시험 evidence는 physical specimen, source/independence group, direction, method, result unit·uncertainty를 유지한다. Through-thickness 시험값만으로 tearing 발생, 허용 이음, 수명 또는 고장확률을 만들지 않는다.

## Temper bead와 hot tap

`welding.temper_bead_qualification`은 pass 순서, layer sequence, deposition clock, heat input, interpass temperature와 temper-bead descriptor를 caller envelope에 비교한다. Hardness·microstructure·NDE observation은 물리 시편·source group, method, unit, uncertainty와 digest를 유지한다. `welding.hot_tap_applicability`는 host-pipe condition과 exact pressure basis, 운전조건·두께·형상·heat-extraction, 용접·수소관리 identity를 외부 thermal/burn-through 및 hydrogen-cracking provider 결과에 연결한다. 두 경로 모두 자체 열해석, 차트, 균열 또는 burn-through 확률을 만들지 않는다.

## Brazing과 bonding

`welding.brazing_bonding_qualification`은 순서가 있는 member material/surface identity, bonding material·lot, process·flux·atmosphere, clearance·overlap과 non-overlapping heat-pressure cycle을 비교한다. Qualification evidence의 specimen/source/independence group과 mechanical/NDE metric을 유지하며 미보고 bond strength를 추정하지 않는다.

## Peening treatment

`welding.peening_treatment_evidence`는 처리 zone, method, media lot, equipment, direction, exact intensity·coverage metric과 uncertainty를 caller envelope에 비교한다. Residual-stress observation은 coordinate frame, tensor component, depth, physical specimen, source/independence group과 partition을 유지한다. 처리 지원범위 확인은 stress redistribution, fatigue-life improvement, 균열 억제 또는 합격의 증거가 아니다.

## 상태와 후속 연결

검토 누락, unit 불일치, invalid evidence 또는 부족한 source-group coverage는 `needs_data`다. 완전히 검토된 조건이 caller support 밖이면 `out_of_scope`, 지원 안이면 `computed`다. 이 상태를 FTA basic event로 직접 사용하지 않는다. 실제 위험성 연결에는 명시적인 균열 사건 정의, 기간·conditioning, 독립 calibration/holdout, 검사 검출과 구조 한계상태 모델이 필요하다.
