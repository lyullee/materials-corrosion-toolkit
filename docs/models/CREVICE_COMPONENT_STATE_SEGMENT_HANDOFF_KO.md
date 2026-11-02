# Crevice component-state BDF 구간 경계 handoff

## 목적과 계약 경계

`integration.crevice_component_state_segment_handoff`는 하나의 `CreviceComponentStateBDFRequest`와 그 요청으로 계산한 `Calculation` 결과를 함께 받아, 결과의 최종 시점 inventory를 다음 고정기하 segment의 초기 상태 후보로 전달한다. phase molar volume과 gap 점유 여부, 셀 형상 자료는 caller 입력이며 모두 digest와 Evidence로 묶는다.

이 API는 BDF 요청을 수정하거나 source chemistry를 다시 계산하지 않는다. BDF stage/RHS 안에서 aperture를 갱신하는 moving-boundary solver라고 주장하지 않는다. 출력은 다음 고정기하 요청을 사람이 별도로 작성할 때 사용할 후보 값이다.

## 입력과 fail-closed 조건

- source request와 result의 assessment ID가 같아야 한다.
- source request는 `instantaneous_solid_equilibrium` mode여야 한다. aqueous-only 입력은 `out_of_scope`다.
- source result의 `input_sha256`은 `canonical_digest(source_bdf_request.model_dump(mode="json"))`와 같아야 한다.
- source `Calculation.status`, `values.committed`, `values.all_component_ledgers_close`는 모두 성공/true여야 한다.
- 별도 source-result SHA-256은 `Calculation.model_dump()` 전체를 묶으며 BDF 모델 ID와 결과 해시가 일치하는 Evidence가 필요하다. request, result, Evidence가 모두 일치하지 않으면 거절한다.
- source state basis는 `total_aqueous_plus_candidate_solid`여야 한다.
- 요청 cell 순서는 BDF request와 result에 있는 순서에 정확히 일치해야 한다. BDF phase-set receipt의 phase 순서도 caller molar-volume/occupancy 입력과 일치해야 한다.
- `target_segment_start_time_s`는 source 결과의 마지막 `time_s`와 정확히 같아야 한다.
- geometry digest는 `cell_ids`, `cell_length_m`, `transverse_width_m`, `initial_aperture_m`를 순서대로 묶는다. phase digest는 phase ID, molar volume, `occupies_gap` flag를 순서대로 묶는다. 각각 일치하는 Evidence SHA-256가 필요하다.
- `uniform_within_cell_coverage_reviewed`와 `geometry_and_phase_mapping_reviewed`는 true여야 한다. 처리량은 `maximum_work_operations`로 제한한다.

## 계산 방법

BDF의 `solid_phase_inventory_mol_by_cell_phase_time`에서 마지막 knot의 상별 몰수를 가져온다. `occupies_gap=true`인 상에 대해서만 caller 제공 몰부피를 곱해 cell별 고체 체적을 계산한다.

```text
V_solid[i] = sum_phase(n_final[i, phase] * molar_volume[phase])  # occupies_gap 상만
aperture_next[i] = aperture_initial[i] - V_solid[i] / (cell_length[i] * transverse_width[i])
cross_section_next[i] = transverse_width[i] * aperture_next[i]
liquid_volume_next[i] = cross_section_next[i] * cell_length[i]
```

새 aperture는 유한한 양수여야 한다. `width × length × aperture 감소량`과 gap 점유 고체 체적의 폐쇄 오차도 제한한다. face 단면적은 cell center의 단면적을 내부 face에서 비균일 cell 길이로 가중해 선형 보간한다. 양 끝 face에는 첫/마지막 cell 단면적을 사용한다.

각 component에 대해 BDF `component_ledgers[].inventory_mol_by_time_and_cell[마지막 시점]` 값을 그대로 보존해 `next_initial_total_component_moles_mol_by_component_cell`로 반환한다. 이전 구간 initial inventory와 final inventory가 같다고 가정하지 않으며, BDF에서 발생한 transport/reaction 변화는 원래 ledger가 기록한다.

## 출력 및 사용

- `next_initial_total_component_moles_mol_by_component_cell`
- `next_cell_aperture_m`, `next_cell_cross_section_m2`
- `next_cell_solution_volume_m3` 및 `next_cell_solution_volume_L`
- `next_face_area_m2_by_face`
- source digest, 정확한 segment start 시각, component/phase/cell IDs, geometry closure 잔차

`committed=false` 또는 `status=needs_data`이면 downstream 고정기하 계산에 쓰지 않는다. 성공이어도 `qualification_claimed=false`다.

## 가정과 제한

- cell 내부 침전 분포는 균일하다고 caller가 검토해야 한다.
- 고체 상의 gap 체적 점유는 caller가 상별 boolean으로 선언한다. 부피, 점유, 반응성, 용해도 또는 핵생성은 이 모듈에서 추론하지 않는다.
- 횡방향 폭과 cell 길이는 segment 경계에서 유지된다. 침전 이외의 변형, 거칠기, crack, 압축성, 유체 유동 재해석은 포함하지 않는다.
- 결과는 다음 고정기하 구간에 대한 경계 전달이며 BDF 내부 geometry feedback이 아니다.

## 개발 및 검증 상태

API 코드와 이 계약 설명은 독립적으로 작성했다. 이 변경에서는 테스트, 패키징, 중앙 registry/schema/catalog 등록 및 HPC 계산을 실행하지 않았다. 실행 검증은 별도 작업이 필요하다.
