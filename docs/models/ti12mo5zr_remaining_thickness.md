# Ti-12Mo-5Zr 등가 잔여두께 history adapter

## 목적

이 adapter는 `corrosion.ti12mo5zr_aesec_signed_equivalent_penetration`에서 이미 계산된 `AssessmentResult`를 받아, caller 승인 초기 두께에서 source의 양의 누적 등가침투량만 뺀 exact-knot history를 제공합니다. provider time 좌표를 바꾸거나 중간 시점 데이터를 생성하지 않습니다.

음의 signed penetration과 부호 net ledger는 그대로 전달하지만 초기 두께에 다시 더하지 않습니다. 양수 손실 누적량이 어느 knot에서든 초기 두께보다 크면 잔여두께는 음수가 되므로 결과를 만들지 않고 fail-closed 합니다.

## digest 및 context 검증

호출자는 세 개의 별도 digest를 input으로 고정해야 합니다.

1. `expected_assessment_input_digest`: AssessmentResult의 model ID/version, 입력과 RunContext로 registry와 동일한 방식으로 재구성한 값과 result의 `input_digest`가 같아야 합니다.
2. `expected_assessment_result_digest`: 전체 JSON AssessmentResult의 canonical SHA-256이어야 합니다.
3. `expected_mass_balance_result_digest`: AssessmentResult `values.mass_balance`를 typed `Ti12Mo5ZrMassBalanceResult`로 검증한 JSON payload의 canonical SHA-256이어야 합니다.

두 번째와 세 번째 digest는 서로 다릅니다. 같은 객체에서 즉시 계산한 뒤 그대로 승인하면 독립 확인이 되지 않으므로, 별도 receipt/검토 단계에서 승인한 digest를 전달하십시오. 결과에는 세 digest와 원 archive/member/row digests, baseline Evidence digest, density Evidence digest가 포함됩니다.

요청에 AssessmentResult와 동일한 `expected_run_context`를 넣어야 합니다. ModelSpec 바깥 `RunContext`도 같은 값이어야 합니다. 기본 asset/location/time basis 등 어느 하나라도 다르면 실패합니다.

## caller 승인과 가정

필수 입력은 양수 초기 두께 및 이를 뒷받침하는 `Evidence`, uniform area basis 승인, density/material 적용성 승인, 계산 사용·로컬 처리 승인입니다. 이전 mass-balance 결과의 density Evidence 역시 원 AssessmentResult 입력과 재검증합니다. 이 모듈은 벽 두께의 시편별 형상/측정값이나 비파괴검사 결과를 대신하지 않습니다.

두께 변환은 uniform area-averaged equivalent assumption을 상속합니다. 따라서 아래 용도에 사용하지 않습니다.

- 국부 부식/피팅의 최대 깊이 또는 위치별 잔여벽두께 주장
- 허용 두께·구조 건전성 합격 판정
- 수명·remaining life, failure probability, FTA 위험도 산정
- 부호 음의 물질이동에 따른 thickness restoration

## API 식별

- 함수: `matintegrity.ti12mo5zr_remaining_thickness.build_remaining_thickness_history`
- ModelSpec ID: `corrosion.ti12mo5zr_uniform_equivalent_remaining_thickness`
- contracts: `matintegrity.ti12mo5zr_remaining_thickness_request.v1`, `matintegrity.ti12mo5zr_remaining_thickness_knot.v1`, `matintegrity.ti12mo5zr_remaining_thickness_history.v1`
- source IDs: `zenodo-ti12mo5zr-aqueous-corrosion`, `caller-baseline-thickness-evidence`, `caller-density-evidence`

실행하지 않은 호출 예제는 `examples/ti12mo5zr_remaining_thickness_local.py`입니다. 테스트, 모델/데이터 계산, package 작업은 이 변경에서 수행하지 않았습니다.

