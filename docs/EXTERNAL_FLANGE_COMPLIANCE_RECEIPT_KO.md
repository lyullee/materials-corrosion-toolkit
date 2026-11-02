# 외부 FE stiffness 결과와 flange compliance reducer 연결

`ExternalFlangeComplianceBinding`은 이미 실행된 외부 FE solver 결과를 기존 `reduce_flange_contact_compliance()`에 공급하기 위한 provider-neutral 경계다. 이 adapter는 FE mesh assembly나 해석을 수행하지 않는다.

## 필수 receipt와 매핑

입력에는 `StructuralProviderResultReceipt`가 필요하며 `analysis_kind`는 `finite_element`여야 한다. 선택 load case는 receipt 안에 있어야 하며 그 digest를 boundary-condition basis로 고정한다. `stiffness_field_id`는 한 개의 `incremental_stiffness_matrix` field로 해석되어야 한다. Field의 result location은 global, unit은 N/m, shape는 `n×n`, coordinate frame은 mesh frame과 같아야 한다. 원 배열 digest와 C/F 저장순서를 함께 고정하고, provider parser가 기존 Python API로 정규화한 square matrix의 canonical JSON SHA-256도 제출한다.

Matrix DOF는 기존 reducer 제약에 맞춰 translation x/y/z만 허용한다. 각 DOF의 node ID와 component 순서는 배열과 동일하게 제공하고 node/component 쌍은 중복될 수 없다. `mesh_node_id_map_sha256`는 provider mesh node ordering에서 축약 matrix row/column 순서로 가는 변환표 digest다. `dof_basis_transform_sha256`는 parser가 이미 적용한 provider-to-normalized basis transform record를 고정한다. adapter 자체는 이 변환표나 matrix parser를 적용하지 않는다. Fixed DOF, gasket contact node 순서, normal translation DOF와 closure sign은 각각 명시한다. 회전/translation 혼합 행렬, 축약되지 않은 일반 full FE operator, 다른 단위와 좌표 frame은 converter 쪽에서 적절히 정규화하지 않는 한 거부된다.

```python
from matintegrity.models.external_flange_compliance import (
    ExternalFlangeComplianceBinding,
    reduce_external_flange_contact_compliance,
)

binding = ExternalFlangeComplianceBinding.model_validate(provider_payload)
result = reduce_external_flange_contact_compliance(binding)
```

Wrapper는 기존 reducer 계산 결과에 provider receipt payload digest, provider input/result digest, mesh/revision, frame, load case/boundary digest, stiffness field/array/normalized-matrix digest와 ordered DOF map을 추가한다. 출력 compliance는 [flange spatial contact operator](API_KO.md)의 downstream 입력으로 사용할 수 있다. 선택한 contact DOF 순서와 접촉 normal closure sign은 downstream과 그대로 유지해야 한다.

## 리뷰 및 경계

단위/scale, 실제 boundary conditions, coordinate frame와 DOF ordering, contact normal mapping, tangent linear elasticity, 계산 사용에 각각 명시 review가 필요하다. Receipt 자체는 사용권이나 FE 결과 품질을 자동 승인하지 않는다. 안정성 검사와 positive eigenvalue/condition-number limit는 downstream compliance reducer가 수행한다. receipt evidence, solver mesh convergence, 실험 상관, gasket nonlinear contact 및 seal/leakage qualification은 별도 검토다. 상용 solver 원본 결과나 parser 출력은 repo에 포함하지 않는다.

이 adapter는 typing/lineage wiring을 제공한다. 실제 provider별 parser·normalized field digest 규약·최소 reducer consumer 실행은 그 solver의 결과 파일과 fixture가 제공된 후 연결해야 한다. 합성 payload를 통한 코드 execution/FE validation은 여기서 수행하지 않았다.
