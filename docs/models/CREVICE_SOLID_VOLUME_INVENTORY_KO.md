# 크리비스 고체상 체적 inventory 어댑터

## 목적

고체상별 셀 inventory를 사용자가 제공한 고체 몰부피와 곱해 기준 면적당 고체 체적을 계산한다. 결과 단위는 `m3/m2`이며 길이 차원으로 표현된다. 셀별 계산 결과와 상별 기여량을 함께 반환해 후속 형상 모델이나 다른 해석 모듈에서 명시적으로 연결할 수 있다.

이 API는 제한 수송/반응/침전 모델이 아니다. 기존 kinetic 또는 equilibrium 계산의 결과를 입력으로 받아 후처리하는 adapter다. 계산 관계는 단순히 다음과 같다.

`phase_volume_per_reference_area[cell] = inventory[mol/m2] * molar_volume[m3/mol]`

서로 다른 고체상의 체적은 셀 안에서 합산하되, 셀이나 시간 단계 사이에서는 합산하지 않는다.

## 입력 계약

Python 모듈은 `matintegrity.crevice_solid_volume_inventory`이다. 주요 입력 형식은 `CreviceSolidVolumeInventoryRequest`이며 평가 함수는 `evaluate_crevice_solid_volume_inventory(request)`이다. `specifications()`는 고유 모델 식별자 `integration.crevice_solid_volume_inventory`에 typed input과 evaluator를 제공한다.

필수 입력은 다음과 같다.

- `assessment_id`, `physical_scope_id`, `elapsed_time_s`: 평가 식별자와 단일 시점
- `phase_ids`: 중복 없는 고체상 식별자 목록
- `cell_solid_inventory_mol_m2_by_phase`: 상 ID별 셀 배열. 각 값은 동일한 기준 면적에 대한 고체 물질량(`mol/m2`)
- `solid_molar_volume_m3_mol_by_phase`: 상 ID별 양의 몰부피(`m3/mol`)
- `inventory_state_sha256`: 시점/영역/상/셀 inventory/몰부피가 같은 입력 상태에 속하는지 확인하는 digest
- `evidence`: inventory와 몰부피 근거의 caller 제공 기록
- 네 review 필드: inventory 기준, 몰부피 상태·단위, 기준 면적과 셀 대응, 형상 추론 금지 검토

digest는 아래 객체의 canonical SHA-256이다. `canonical_digest` 함수로 계산할 수 있으며 튜플은 JSON 배열로 직렬화된다.

```python
from matintegrity.contracts import canonical_digest

state = {
    "physical_scope_id": "component-A/crevice-1",
    "elapsed_time_s": 3600.0,
    "phase_ids": ("solid-X",),
    "cell_solid_inventory_mol_m2_by_phase": {"solid-X": (0.01, 0.02)},
    "solid_molar_volume_m3_mol_by_phase": {"solid-X": 2.0e-5},
}
digest = canonical_digest(state)
```

최대 입력은 셀 5,000개, 상 128개, evidence 64개다. 배열 길이는 모든 상에서 일치해야 한다. 상 ID 집합은 inventory와 몰부피 양쪽에서 정확히 일치해야 한다. inventory는 유한한 비음수, 몰부피는 유한한 양수여야 한다. state digest 불일치는 계약 검증 오류로 닫힌다.

## 결과와 연결

성공 시 `cell_solid_volume_per_reference_area_m`는 셀 순서를 보존한 합계, `phase_solid_volume_per_reference_area_m`는 상별 셀 기여량, `total_solid_volume_per_reference_area_m`는 전체 셀에 대한 총합이다. 결과에는 요청 전체의 `input_sha256`와 원 inventory 상태 digest도 포함한다.

`status="needs_data"`는 review 정보가 누락됐을 때 반환한다. 계산 결과가 유한 범위를 넘으면 `status="out_of_scope"`로 닫는다. 잘못된 단위값/배열/digest는 입력 계약에서 거부한다.

후속 형상 모듈이 이 값을 간극 변화량으로 바꾸려면 벽 배치, 피복률, 공극률, 기준 면적 방향, 셀 별 대응 관계를 별도로 정의하고 review해야 한다. 이 어댑터는 침전물이 양쪽 벽에 나뉘는지, 한쪽 벽에 붙는지, 다공성인지 계산하지 않으며 개구부 폐쇄 여부도 판단하지 않는다.

## 근거와 한계

고체 inventory와 몰부피의 곱셈은 단위 일관성을 갖는 재고 환산이다. 몰부피는 상 조성, 온도, 압력, 결정상 및 적용 범위에 좌우될 수 있으므로 사용자가 각 입력 근거와 사용권한을 관리해야 한다. 코드에는 특정 물질의 몰부피 자료를 포함하지 않는다.

이 계산만으로 석출 평형, 과포화도, 반응속도, 핵생성, 입자 형상, 부착, 부식 생성물 보호성, 유로저항 또는 위험도를 주장할 수 없다. 농도 inventory(`mol/m3`)를 직접 넣지 말고, 기준 면적에 대한 양(`mol/m2`)으로 변환한 값과 대응 셀 정의를 준비해야 한다.
