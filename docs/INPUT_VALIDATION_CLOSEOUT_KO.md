# 핵심 물리 입력검증 진행 현황

기준일: 2026-11-02  
대상: `tests/data/core_physics_missing_input_targets.json`의 116개 모델

## 최신 확인 결과

| 확인 항목 | 결과 | 의미 |
|---|---:|---|
| 필수 입력 누락·null·타입·선언된 제약 검사 | **116개 대상의 입력 계약 검사 통과** | 빈 입력 및 잘못된 값 거부를 자동 검사했다. 계산의 물리적 정확성을 뜻하지 않는다. |
| 유효 기준 입력 | **115/116개** | 자체 작성 계약 fixture이며 실험 데이터가 아니다. |
| Review gate 동작 | **102/102 적용 모델**, 410개 표적 probe 행 | Sines 3개 flag는 완전 입력 registry 시험이 아니라 evaluator 단위검사로 확인했다. |
| 필드 간 일관성 | **106개 검사 + 10개 해당 없음 + 0개 미분류** | 116개 범위를 모두 분류했다. |
| 필수 Evidence 제거 검사 | **235개 변형 / 84개 모델** | Sines 관측 Evidence는 유효 baseline이 아닌 불완전 입력 뼈대에서 제거 거부를 확인했다. |
| 단위 문자열 불일치 | **1개 모델, 3개 token 사례** | 문자열 단위 token이 있는 모델 기준. 나머지 inventory 표시는 수치 단위·review·budget 항목이다. |
| 네 입력검증 시험 파일 | **12,125 passed, 0 failed, 3 skipped (38.32초)** | 2026-11-02 최신 실행 결과. |

감사 수치는 다음 명령으로 재현한다.

    .venv\Scripts\python.exe -X utf8 scripts\audit_core_physics_input_coverage.py

시험 수치는 다음 명령의 최신 실행 결과다.

    .venv\Scripts\python.exe -X utf8 -m pytest -q tests\test_core_physics_missing_input_contracts.py tests\test_core_physics_review_gates.py tests\test_core_physics_cross_field_inputs.py tests\test_erosion_corrosion_power_law.py

## 현재 남은 입력검증

`fatigue.multiaxial_sines_life_fit`은 측정 또는 공개 dataset 계보가 있는 피로시험 자료를 요구한다. 저장소의 ECP 공개 피로자료에는 실험 수명은 있지만 독립 물리 시편 ID와 원 tensor 이력이 없어 완전한 정상 입력을 만들 수 없다. 따라서 positive baseline의 registry 수용과 end-to-end 계산은 확인하지 않았다. 대신 필수 Evidence 제거는 불완전 입력 계약 probe로, 3개 review gate는 evaluator 단위검사로 확인했다. 이 구분은 허위 측정값이나 출처를 만들지 않으면서 입력 거부 계약을 검사한다.

## 이번 시험이 증명하지 않는 것

이 결과는 부식·피로 등 계산식의 물리적 정확성, 공개 실험 데이터에 대한 예측 성능, 현장 보정, 시스템 간 전체 통합 또는 안전·건전성 판정 자격을 증명하지 않는다. 유효 fixture는 계약과 입력검사 용도이며 실험 검증 자료가 아니다.

## 근거 파일

- 대상 목록: `tests/data/core_physics_missing_input_targets.json`
- 계약 인벤토리: `tests/data/core_physics_input_contract_inventory.json`
- 기준 입력: `tests/data/core_physics_valid_input_baselines.json`
- Evidence 변형 manifest: `tests/data/core_physics_evidence_removal_probe_manifest.json`
- Review probe 결과: `tests/data/core_physics_review_gate_probe_results.json`
- Cross-field 거부 사례: `tests/data/core_physics_cross_field_rejection_cases.json`
- Coverage 감사: `scripts/audit_core_physics_input_coverage.py`
- 상세 작업 이력: `../analysis/CORE_PHYSICS_INPUT_VALIDATION_PROGRESS_20261102.md`
