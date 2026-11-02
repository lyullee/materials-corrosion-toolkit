# 온도별 수용액 평형 이력과 고체 포화도 screening

`integration.aqueous_vant_hoff_saturation_history`는 계산 완료된 `integration.aqueous_mass_action_vant_hoff_history` 결과의 각 절점 활동도를, 사용자가 직접 고른 고체 후보와 해당 온도에서 적용 가능한 `log10(Ksp)` 데이터에 연결한다. 반응망/상 자동 발견은 하지 않으며 기존 온도별 평형 계산을 재실행하거나 변경하지 않는다.

## 입력 계약

- `equilibrium_history`는 registry가 반환한 전체 `AssessmentResult`여야 한다. `equilibrium_history_sha256`에는 해당 JSON 결과의 canonical digest를 제공한다. 모델은 result digest와 registry input/context digest를 모두 확인한다. Digest는 내용 동일성과 연결을 확인할 뿐, 서명·생성자 인증이나 계산의 물리적 정당성을 증명하지 않는다.
- `solubility_by_knot`은 upstream 이력의 각 시각에 하나씩 정확히 대응한다. 시각은 일치해야 하고, 각 후보의 source-record 온도 지원은 해당 절점 온도를 포함해야 한다. 모델은 절점 사이 `Ksp` 보간을 하지 않는다.
- 각 절점에서 후보 고체 ID와 활동도곱 양론 항은 전체 history에 걸쳐 같은 순서·정의로 유지한다. `CandidateSolid`는 caller가 제공한 `log10(Ksp)`, 활동도곱 항 및 solubility source-record ID를 담는다.
- 측정/open-dataset `Evidence`는 원 파일 SHA-256이 필요하고, 공개 데이터는 라이선스 식별자도 필요하다. `data_sha256`는 절점별 solubility 입력 묶음 digest이므로, 원 파일 해시가 있다면 Evidence에도 별도로 둔다.
- 비영(非零) 활동도/`Ksp` bound는 입력 의미에 대한 review gate가 필요하다. 이 API는 선언된 log bound를 deterministic interval로만 전달한다.
- RunContext는 upstream 이력의 asset/location/time basis와 같아야 한다.

## 출력과 범위

각 절점은 기존 `chemistry.aqueous_saturation_screen`를 사용해 개별 `log10(Q/Ksp)`와 선언된 구간 분류를 반환한다. 시간별 절점 결과와 upstream·solubility digest를 보존한다. 한 절점이라도 미해결이면 전체 결과 status를 `needs_data` 또는 `out_of_scope`로 유지한다.

Supersaturation은 안정상 선택, 침전량, 핵생성 또는 성장속도가 아니다. 반응-확산 동시해석, 액상/기상 분배, 고체 inventory 변화, scale 보호, 부식률·수명 및 물리 qualification은 계산하지 않는다. Caller가 넣은 후보와 열용해도 데이터의 적합성 책임은 caller에게 있다.

## 계산 흐름 예

```python
from matintegrity.models.aqueous_vant_hoff_saturation import (
    AqueousSolubilityKnot,
    AqueousVanTHoffSaturationHistory,
    TemperatureSupportedCandidate,
)
from matintegrity.registry import default_registry
from matintegrity.contracts import RunContext, canonical_digest

registry = default_registry()
context = RunContext(asset_id="coupon-1", location_id="cell-1", time_basis="elapsed-time-s")
equilibrium = registry.run(
    "integration.aqueous_mass_action_vant_hoff_history",
    caller_vant_hoff_input,
    context,
)
request = AqueousVanTHoffSaturationHistory(
    assessment_id="coupon-1-saturation-history",
    equilibrium_history=equilibrium,
    equilibrium_history_sha256=canonical_digest(equilibrium.model_dump(mode="json")),
    solubility_by_knot=caller_temperature_supported_ksp_rows,
    complete_species_inventory_reviewed=True,
    compatible_standard_states_reviewed=True,
    equilibrium_constants_temperature_reviewed=True,
)
screen = registry.run(
    "integration.aqueous_vant_hoff_saturation_history", request, context
)
```

예시의 `caller_vant_hoff_input`과 `caller_temperature_supported_ksp_rows`는 반드시 사용자가 구성해야 한다. 예제 변수는 범용 표준물질·용해도 값을 뜻하지 않는다. 라이선스/근거가 확인된 공개 solubility dataset이 승인되기 전까지 이 입력은 caller/user 자료를 통해서만 공급한다.
