# 확장 요청: component-state BDF fixed-segment handoff

## 목표

Standalone API `integration.crevice_component_state_segment_handoff`를 공식 model registry, schema export 및 catalog에 연결한다. 계산 모듈은 기존 BDF request/result pair를 검증해 다음 고정기하 구간의 후보 inventory와 geometry를 반환한다.

## 등록 대상

- 모듈: `matintegrity.crevice_component_state_segment_handoff`
- 요청: `CreviceComponentStateSegmentHandoffRequest`
- 계산 함수: `solve_crevice_component_state_segment_handoff`
- 모델 ID: `integration.crevice_component_state_segment_handoff`
- source ID: `caller_mapped_component_state_bdf_fixed_segment_handoff`

## 연동 규약

1. `source_bdf_request`와 `source_bdf_result`는 동일 계산이어야 한다. 결과 `values.input_sha256`은 직렬화된 request의 canonical digest와 맞아야 하며, full `Calculation.model_dump()` result digest와 BDF model-ID Evidence를 함께 검증한다.
2. result `Calculation.status="computed"`, `committed=true`, `all_component_ledgers_close=true`와 total aqueous-plus-solid state basis가 확인된 경우만 처리한다.
3. input request solid mode는 `instantaneous_solid_equilibrium`이어야 한다. aqueous-only는 out-of-scope로 반환된다.
4. 출력 component inventory와 geometry는 다음 BDF 고정기하 요청에 수동 전달할 후보 값이다. 이 모듈에서 다음 request 객체를 만들거나 원본을 변경하지 않는다.
5. 모델 설명에서 stage-level moving boundary 또는 BDF RHS feedback이라고 기술하지 않는다.
6. registry 연결 시 `qualification_claimed=false`, 단위, caller 입력 가정, fail-closed 조건을 노출한다.

## 주요 산출

- 최종 BDF total component inventory를 보존한 다음 구간 initial inventory 후보
- cell별 gap-occupying solid volume, 새 aperture, cross-section, solution volume
- cell center 선형 보간으로 계산한 face area
- 정확한 source time/digest/ordered IDs와 solid volume-aperture closure 잔차

단위: component/solid inventory `mol`, molar volume `m^3/mol`, time `s`, length `m`, area `m^2`, solution volume `m^3`/`L`.

## 검증 전제

phase molar volume/occupancy map과 geometry input은 각각 canonical digest 및 Evidence로 묶인다. source BDF result도 input request digest와 paired verification을 거친다. 본 코드 변경은 테스트·패키징·HPC 및 중앙 catalog/schema 작업을 수행하지 않았으므로, registry merge 전 실행 테스트가 필요하다.
