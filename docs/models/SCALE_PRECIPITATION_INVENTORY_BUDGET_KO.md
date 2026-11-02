# 스케일 석출량과 수용액 반응물 재고 대조

## 목적

`chemistry.scale_precipitation_inventory_budget`는 이미 계산된 단일상 스케일 두께 이력의 **총 석출량**을 caller가 제공한 반응물 재고·구간 공급량과 화학양론으로 대조하는 유한 재고 장부입니다. 업스트림 스케일 이력의 계산 결과를 변경하지 않습니다.

## 필요한 입력

- `chemistry.caller_surface_scale_kinetics`의 완료된 AssessmentResult와 결과 전체 SHA-256
- 동일 물리 범위에 적용할 노출 면적 및 출처 Evidence
- 각 제한 반응물 종의 초기 사용 가능 몰수, Evidence, 스케일 화학식 단위당 필요한 몰수
- 스케일 이력의 모든 계산 구간에 대응하는 반응물 보충 몰수와 Evidence
- 화학양론, 면적·범위 대응, 재고 접근 가능성, 구간 공급 기록, 총 석출량 장부, 계산 이용 권한에 대한 별도 review

계산 이력은 초기 절점 뒤 각 구간에 `precipitated_mol_m2`와 고유 `interval_id`를 포함해야 합니다. 각 반응물에 대해 스케일 이력과 같은 순서·개수의 공급 항목을 입력해야 합니다.

## 계산과 중단 규칙

구간의 gross 스케일 석출 몰수는 `precipitated_mol_m2 × exposed_area_m2`로 정의합니다. 각 caller 선언 화학양론에 따라 필요한 반응물 몰수를 산출하고, 이전 잔고와 해당 구간의 공급량에서 차감합니다. 한 종이라도 공급 가능량보다 요구량이 크면 그 구간은 장부에 반영하지 않고 `out_of_scope`, 최초 부족 구간, 종별 부족량 및 완료된 구간 접두부를 반환합니다.

스케일 용해는 이미 생성된 스케일을 감소시키지만 수용액 반응물이 재생되는지는 계산하지 않으므로 이 장부에서 용해를 반응물 공급원으로 계산하지 않습니다.

## 해석 경계

이는 유한한 화학양론적 재고 대조입니다. 용액 종분화, 활동도, 고체 평형, 물질전달, 침전 속도식, 경쟁상, 반응물 접근성, 부식률, 벽두께 감소, 수용성 또는 고장확률을 계산하지 않습니다. `computed`는 **사용자가 공급한 스케일 결과와 재고 입력 사이에 이 장부가 산출됐음**만 뜻하며, upstream 스케일 kinetics의 물리적 타당성을 검증하지 않습니다.

## Python API 형태

```python
from matintegrity.scale_precipitation_inventory_budget import (
    ScalePrecipitationInventoryBudget,
    evaluate_scale_precipitation_inventory_budget,
)

request = ScalePrecipitationInventoryBudget(
    assessment_id="scale-inventory-audit-001",
    physical_scope_id="component-A",
    scale_history_result=scale_assessment,
    scale_history_result_sha256=scale_result_digest,
    exposed_area_m2=exposed_area,
    exposed_area_record_id="area-record-1",
    exposed_area_evidence=(area_evidence,),
    limiting_reactants=(caller_species_inventory,),
    scale_formula_stoichiometry_reviewed=True,
    inventory_accessibility_and_interval_supply_reviewed=True,
    scale_history_scope_and_area_mapping_reviewed=True,
    gross_precipitation_only_no_dissolution_credit_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_scale_precipitation_inventory_budget(request)
```

위 코드는 계약 객체의 사용 형태만 제시합니다. 실제 재고, 화학양론, 면적 및 증거는 호출자가 해당 공정과 자료에 맞게 공급해야 합니다.
