# 표 입력 기반 aqueous activity 반복

`chemistry.aqueous_tabulated_activity_speciation`는 caller가 종별로 제공한 activity coefficient 표와 기존의 caller 정의 질량작용/선형 제약계를 반복 결합한다. 데이터 입력은 표 온도, species ID, ionic strength (mol/kg water), 양의 무차원 activity coefficient knot로 구성한다. 외부 측정/공개 dataset 표의 각 knot는 `source_id`와 `source_record_id`를 함께 보존해야 한다. `source_id`는 같은 요청의 Evidence `source_id`와 일치해야 하며, 해당 Evidence는 `measured` 또는 `open_dataset` origin이어야 한다. 공개 dataset Evidence는 citation 및 license/reuse policy도 밝혀야 한다. 선언한 계산 온도는 aqueous system 온도와 정확히 일치해야 한다. 기존 고정 온도 표는 온도 slice가 없는 ionic-strength 표로 입력한다. 온도 의존 표는 종별로 최소 두 온도의 `AqueousActivityCoefficientTemperatureSlice`를 제공하며 각 slice가 0부터 요청 ionic-strength 상한까지 덮어야 한다. `ln(gamma)`는 기본 구간 선형 또는 명시 검토된 SciPy PCHIP으로 ionic strength 및 필요시 온도축에서 보간하며, 두 축 모두 외삽하지 않는다. 전체 표 knot 수는 기본 250,000개까지 받고 `maximum_activity_table_points`로 caller가 10,000,000개까지 명시 상향할 수 있다.

반복 단계는 현재 gamma를 사용해 `aqueous_mass_action_speciation`을 풀고, caller가 제공한 물 질량 환산으로 종 농도를 molality로 바꿔 이온강도와 전하 잔차를 계산한다. 종별 표에서 현재 온도·이온강도의 목표 `ln(gamma)`를 읽고 caller damping fraction으로 log 공간 업데이트를 수행한다. 보간은 기본 `piecewise_linear`이며, 선택적 `shape_preserving_pchip`은 선택 의존성 SciPy의 `PchipInterpolator`를 각 축에 적용하고 외삽하지 않는다. PCHIP 선택에는 `interpolation_method_reviewed=true`와 `matintegrity[science]` 설치가 필요하다. SciPy가 없으면 명시적인 의존성 오류로 닫는다. 표의 물리적 타당성을 추가로 보장하지 않는다. 고정점 잔차가 선언 허용치 안에 들고, 이온강도 및 전하 잔차 제한을 만족할 때만 계산된 speciation을 반환한다. 입력 표·활동도 공급자·평형 상수 공급자·물 환산 정보는 digest와 lineage로 보존된다. 결과에는 정규화된 표 전체의 digest, 행 source/record 연결표의 digest 및 Evidence 묶음의 별도 SHA-256을 기록한다. 결과에는 citation/license 포함 table Evidence, 종별 표 모드, 각 온도 slice의 이온강도 범위·점 개수·source record ID의 개수와 digest, 표 전체 점 개수 budget, 실제 계산 온도·이온강도 평가점 및 적용한 보간 방식을 기록한다. 온도와 이온강도 사이 보간은 caller table 위의 수학적 선택이며, 실제 전해질의 온도 응답을 모델로 검증하지 않는다.

## 입력 및 해석

검토용 합성 입력은 `examples/model_inputs.json`의 `chemistry.aqueous_tabulated_activity_speciation` 항목이다. 공개 계산 계약 `AqueousTabulatedActivityIteration`은 `activity_table_temperature_K`와 species별 `AqueousSpeciesActivityCurve`/`AqueousActivityCoefficientPoint`를 받는다. 정확한 온도 일치는 검사하지만 용매·염 조성·압력·실험 계수표의 출처와 농도 표준상태 적합성은 별도 review 및 caller 책임으로 남는다. species 식별자와 charge/element inventory, 평형상수, mass/charge 제약은 기존 `AqueousMassActionSystem`에 별도로 정확히 기입한다.

온도별 표 구조만 보려면 `examples/temperature_dependent_activity_table.py`를 참고한다. 이 예제 수치는 오직 API 배선 표본이며 실측 계수나 검증 기준으로 쓰지 않는다.

보간 선택 배선은 `examples/aqueous_activity_interpolation.py`를 참고한다. 기존 예제 입력의 표본을 `shape_preserving_pchip` 모드로 읽고 review flag를 설정할 뿐, 계산이나 표 적합성 검증을 수행하지 않는다. 실제 평가에 이 모드를 선택하면 SciPy가 포함되는 `science` extra가 필요하다.

같은 표를 restricted transport의 migration activity callback으로 연결할 때는 `build_tabulated_activity_transport_callback(request, transport_species_ids=..., temperature_K=...)`를 사용한다. 생성 callback은 transport 입력의 activity provider ID/configuration digest와 일치하는 속성을 가지며, 종 순서가 정확히 같아야 한다. Transport 결과에도 원 speciation request digest, 표 내용/행 계보/Evidence digest와 interpolation method가 전달된다. transport 농도 배열(mol/m³)을 물 질량 환산값으로 molality로 바꾸어 입구와 각 셀의 ionic strength를 계산하고, 주어진 종별 표에서 `gamma`를 읽는다. 표 지지범위 밖 상태, 선언 이온강도 상한 초과, 비유한 농도는 오류로 거부한다. 단일 system 온도에 고정되며 시간별·온도별 유동 변화, 용매/염 변화, migration 외의 계면 전기화학 효과를 자동 추론하지 않는다. transport 계약에서도 `activity_chemical_potential_and_tracer_diffusivity_reviewed`를 명시해야 한다.

Python 조합 예:

```python
from matintegrity.models.aqueous_tabulated_activity import (
    build_tabulated_activity_transport_callback,
)

activity_callback = build_tabulated_activity_transport_callback(
    activity_request,
    transport_species_ids=transport_request.species_ids,
    temperature_K=activity_request.system.temperature_K,
)
result = solve_restricted_transport(
    transport_request,
    reaction=reaction_callback,
    activity_coefficients=activity_callback,
)
```

이 예는 입력 계약의 공급자 ID와 configuration digest가 transport 요청과 일치해야 한다. 전기적 migration을 함께 계산하면 transport 요청의 온도와 전위/전하 review도 별도로 충족해야 한다.

이 경로는 임의 표를 보간하는 사용자 확장 지점이지 전해질 이론, 표준 활동도 모델, 희석/농축 용액 물성 또는 문헌 데이터의 자격화가 아니다. 표 작성·온도와 용매 이전·기준상태 매핑·물 질량/부피 환산은 caller 책임이다. 한 번의 계산은 하나의 aqueous system 온도·용매 조건과 caller가 명시한 종만 다루며, 온도별 표는 그 단일 system 온도에서 계수를 평가하기 위한 입력이다. 자동 전하 보정, gas/solid phase, 경쟁 침전, scale 성장, kinetics, corrosion rate 및 acceptance는 계산하지 않는다. 반복이 발산하거나 표 지원범위를 넘으면 마지막 iterate를 평형 결과로 승격하지 않는다.
