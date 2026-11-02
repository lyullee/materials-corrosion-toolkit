# Wet-CO₂ 계산 결과의 원소 재고 handoff

`wet_co2_elemental_phase_handoff`는 이미 계산된 aqueous species/solid phase 시간 이력을 받아, caller가 지정한 화학식 원소수와 cell solution volume으로 원소별 재고를 계산한다. 이 API는 평형상수·화학종·반응식·수송을 다시 계산하지 않는다. 공급자 출력 ID에 원소 조성을 연결하는 책임과 해당 매핑의 검토는 호출자에게 있다.

## 입력 계약

- `source_values`: phase/transport 계산의 `Calculation.values`와 같은 payload
- `source_result_digest`: `canonical_digest(source_values)` 값. payload 변경 시 재계산한다.
- `cell_solution_volume_m3`: 각 cell의 solution volume. 계산 output에 없는 기하량이므로 caller가 근거와 함께 제공한다.
- `components`: 모든 aqueous species ID와 solid phase ID 각각에 대한 명시적 원소수 매핑
- provider ID/revision, source result digest, matching Evidence와 mapping review flags
- 선택적으로 upstream `AssessmentResult` 및 전체 result SHA-256. 제공하면 computed status, input/context digest, values payload digest, asset/location/time basis를 함께 대조한다.

현재 연결 규격은 `species_ids`, `solid_species_ids`, `elapsed_time_s`, `concentration_after_phase_mol_m3`, `solid_moles_per_solution_volume_mol_m3`, `status`를 사용한다. 농도와 고체 재고는 각 cell에서 mol/m³로 해석한다. aqueous 배열 축은 `[time][species][cell]`, solid 배열 축은 `[time][cell][phase]`다. cell volume을 곱해 전체 mol 재고를 계산한다.

## 결과 및 한계

원소별 aqueous, solid, combined inventory와 최초 시점 대비 combined 변화량을 반환한다. 원소 재고 변화는 경계 유입·유출, 벽 반응, 기체상, 흡착상, 부피 변화 등 빠진 inventory pool을 자동으로 보정하지 않는다. 따라서 이 변화량만으로 보존 여부나 부식량을 판정하지 말고, 필요한 외부 경계 flux와 기타 상을 별도 대조해야 한다. 공식/부피 매핑 검토가 빠지면 `needs_data`; source가 계산 완료 상태가 아니거나 배열이 맞지 않으면 `out_of_scope`를 반환한다.

이 모듈은 provider-neutral 후처리 경계다. CoolProp, 평형 solver 또는 chemistry provider를 필수 의존성으로 추가하지 않는다.

기본 registry 이름은 `integration.wet_co2_elemental_phase_handoff`다. `RunContext`의 asset/location/time basis는 요청 입력 identity와 같아야 한다. source time은 유한한 단조 증가 벡터이며 농도/재고 입력은 비음수 유한값이어야 한다. 이를 통과해도 원소 재고 closure를 검증한 것은 아니다.

계산 결과는 formula mapping, solution-volume vector, Evidence 전체의 독립 digest도 함께 기록한다. 원소식은 최소 한 원자를 포함해야 하고 source clock은 0초부터 유한한 증가 순서여야 한다. 각 cell/time 원소 재고는 기여항에 대해 `math.fsum`으로 누산한다.
