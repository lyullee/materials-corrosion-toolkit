# Crevice 공간 셀별 mass-action 계산 workflow

## 목적과 범위

`integration.crevice_spatial_mass_action_workflow`는 고정된 transport campaign의 각 정확 시점·셀에 대해 호출자가 작성한 `AqueousMassActionSystem`을 기존 aqueous mass-action solver로 계산하고, 모든 계산이 완료된 뒤 기존 `integration.crevice_local_speciation_volume_ledger`를 호출합니다. 기존 ledger가 요구하던 “각 셀 solver 별도 실행 및 결과 전달”을 하나의 명시적 API 경로로 묶습니다.

이 workflow는 transport 데이터를 화학 입력으로 자동 변환하지 않습니다. 세포 간 이동·혼합·평형, 액상/고체상 변화, 구간 간 kinetic continuity, 부식률 또는 재료 손실을 계산하지 않습니다. 매 셀은 독립적으로 풀리고, 마지막 ledger는 그 농도에 caller가 지정한 셀 부피를 곱해 inventory를 기록합니다.

## 입력

- `ledger_request`: 기존 `CreviceLocalSpeciationLedgerRequest`. 정확한 transport composition bridge와 계산 결과, 모든 transport knot·cell, 각 셀의 mass-action 시스템, 셀 transport context digest, 검토 플래그를 포함합니다.
- `aqueous_mass_action_result` 칸은 빈 객체여야 합니다. workflow가 기존 solver의 결과로 채웁니다.
- 각 셀 시스템에는 화학종, 반응, 로그 평형상수, activity coefficient, 온도, 제약식, standard state, provider/evidence lineage 및 적용성 검토를 모두 명시합니다. 셀마다 assessment ID는 고유해야 합니다.
- `local_solver_execution_authorized`, `cell_specific_chemistry_mapping_reviewed`: 계산 실행과 운송 셀별 chemistry mapping의 caller 검토입니다. 거짓이면 계산하지 않고 `needs_data`를 반환합니다.

운송 셀 농도를 mass-action 제약식으로 바꾸는 규칙은 제공하지 않습니다. 각 제약식의 의미와 단위가 해당 셀 상태에 맞는지 호출자가 확인하고 해당 시스템에 입력해야 합니다.

## 계산 흐름

1. 입력 workflow digest와 고정된 transport lineage를 기록합니다.
2. knot index 순서, 각 knot의 cell index 순서로 기존 `aqueous_mass_action_speciation`을 호출합니다.
3. 첫 비계산 결과에서 멈추고 성공한 결과 prefix 및 실패한 knot/cell/result를 반환합니다. 불완전 셀 집합으로 ledger를 만들지 않습니다.
4. 모든 셀이 계산되면 각 결과를 원래 ledger request에 넣고 기존 `assemble_crevice_local_speciation_ledger`를 호출합니다. 이 단계가 농도·metadata 정합성, transport context digest, volume inventory 및 knot completeness를 확인합니다.

## Python API

```python
from matintegrity.crevice_spatial_mass_action_workflow import (
    CreviceSpatialMassActionWorkflow,
    solve_crevice_spatial_mass_action_workflow,
)

request = CreviceSpatialMassActionWorkflow.model_validate(payload)
calculation = solve_crevice_spatial_mass_action_workflow(request)
```

공용 registry 등록은 중앙 통합 작업에서 `specifications()`로 수행합니다.

## 결과와 제한

계산 완료 시 결과에는 셀별 요청·solver 결과 digest, 계산 상태와 최종 ledger result가 포함됩니다. 특정 셀 solver가 실패하면 downstream ledger는 `None`이며, 해당 결과는 평가가 완료된 셀 prefix로만 해석해야 합니다. 모든 계산 완료 후에도 ledger는 inventory bookkeeping일 뿐, 전하중성·원소수지·교차 셀 혼합을 자동으로 부과하거나 검증하지 않습니다. 실제 적용 전에는 반응 네트워크, 평형 데이터, 단위와 적용 범위를 별도로 검토해야 합니다.
