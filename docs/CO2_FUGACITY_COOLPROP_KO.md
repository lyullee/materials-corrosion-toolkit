# CoolProp 기반 CO₂ fugacity 공급자

## 목적과 경계

`thermo.co2_fugacity_coolprop`은 사용자가 제공한 온도와 절대 CO₂ 부분압에서 선택 의존성 CoolProp의 순수 CO₂ 상태방정식을 평가해 fugacity coefficient와 fugacity를 돌려준다. `thermo.co2_mixture_fugacity_coolprop`은 CoolProp이 지원하는 caller-specified mixture EOS와 성분별 mole fraction, 전체 절대압에서 CO₂ component fugacity를 계산한다. 두 결과는 기존 `chemistry.fixed_fugacity_carbonate_equilibrium`에 필요한 기상 fugacity와 provider 계보 필드를 구성할 수 있다.

순수 성분 계산기의 압력은 혼합물 전체압이 아닌 절대 CO₂ 부분압이다. mixture 계산기는 CO₂ 부분압을 `mole_fraction_CO2 × total_pressure`로 기록하고 CoolProp mixture EOS에서 CO₂ 성분 fugacity를 읽는다. 조성, 각 이원계 상호작용계수 가용성, 혼합물 EOS 적합성, 기체 단일상 여부는 호출자가 근거와 함께 검토해야 한다. CoolProp이 해당 조성/상태를 계산하지 못하면 대체 EOS나 이상혼합 가정으로 전환하지 않는다. 두 경로 모두 수용액, Henry 상수, carbonate 평형, 부식 속도 및 건전성 판정은 계산하지 않는다. 검토 flag는 검토 수행의 독립된 증거가 아니다.

CoolProp API는 순수 경로에서 `AbstractState.update(PT_INPUTS, p, T)`, 혼합 경로에서 조성 설정 후 동일한 PT update와 CO₂ 성분 `fugacity_coefficient(i)`, `fugacity(i)`를 사용한다. CoolProp phase enum이 gas, supercritical gas, supercritical 중 하나가 아니면 계산은 `out_of_scope`로 종료하고 fugacity를 내지 않는다. 허용 phase label은 상태 분류일 뿐 사용 범위의 실험 자격화나 EOS 오차 상한을 뜻하지 않는다.

## Python 사용

```python
from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.co2_fugacity import (
    coolprop_co2_fugacity_to_aquasoldb_fields,
    coolprop_co2_fugacity_to_carbonate_fields,
)
from matintegrity.registry import default_registry

inputs = {
    "assessment_id": "synthetic-co2-state-01",
    "temperature_K": 333.15,
    "co2_partial_pressure_Pa": 2.0e5,
    "backend": "HEOS",
    "pure_component_approximation_reviewed": True,
    "single_phase_gas_or_supercritical_reviewed": True,
    "review_id": "caller-review-example",
    "evidence": [{
        "source_id": "authored-example",
        "origin": "synthetic",
        "citation": "Synthetic API example; not experimental data",
    }],
}
context = RunContext(
    asset_id="synthetic-asset",
    location_id="synthetic-location",
    time_basis="synthetic-state",
)
result = default_registry().run("thermo.co2_fugacity_coolprop", inputs, context)
carbonate_gas_fields = coolprop_co2_fugacity_to_carbonate_fields(result.values)
aquasoldb_comparison_fields = coolprop_co2_fugacity_to_aquasoldb_fields(result.values)
혼합기체 입력은 `CoolPropCo2MixtureFugacityRequest`를 사용한다. `components=("CarbonDioxide", "Nitrogen")`, `mole_fractions=(0.8, 0.2)`, `total_pressure_Pa=...`와 조성/EOS/phase 세 review flag를 공급해 `thermo.co2_mixture_fugacity_coolprop`으로 실행한다. CO₂ index와 부분압은 component 목록에서 계산된다. 실행 가능한 합성 입력은 `examples/model_inputs.json`과 생성 모델 reference에 있다.
```

설치 시 이 기능이 필요하면 `pip install 'matintegrity[thermo]'`를 사용한다. 기본 패키지에서 CoolProp은 import되지 않으며 라이브러리가 없으면 API가 `needs_data`와 누락 의존성 이름을 반환한다. 결과 필드 묶음만 carbonate 입력에 복사하고, 나머지 carbonate, Henry, 알칼리도 입력은 각자의 검토된 출처로 채운다. 온도가 서로 다른 상수/용해도 기록은 기존 모델에서 자동 보정되지 않는다.

`coolprop_co2_fugacity_to_aquasoldb_fields`는 같은 provider 결과를 `AquaSolDBFixedFugacityComparisonInput`의 fugacity·온도·provider 계보 필드명으로 변환한다. 이는 비교 입력 전체를 만들지 않는다. 선택된 관측 행, 독립 Henry record, 물 질량농도 변환, 불확도와 원 논문 인용/권리 검토는 호출자가 별도로 제공해야 한다. AquaSolDB 값을 이용해 fugacity나 Henry 계수를 맞추지 않는다.

## 출력과 재현성

### 순수 CO₂ fugacity 시간 이력

`thermo.co2_pure_fugacity_history`는 ordered `time_s`와 같은 길이의 `CoolPropCo2FugacityRequest` tuple을 받아 각 절점에서 순수 성분 evaluator를 적용한다. 한 history 안에서는 CoolProp backend를 고정하고 시계/상태 정렬 review 및 RunContext asset/location/time basis 일치를 요구한다. 첫 `needs_data`, `out_of_scope` 또는 CoolProp의 표준 계산 예외에서 멈추고 성공한 절점 prefix, 실패 index/time 및 provider 오류 종류를 반환한다. 유효한 첫 절점에서 backend 상태 객체를 한 번 만들고 이후 절점에는 `update()`를 호출해 재사용한다. 시간 사이 상태는 보간하지 않는다. 이는 순수 CO₂ 근사와 기체/초임계 phase 검토 아래의 caller 요청 PT 상태를 평가하며 혼합물 EOS 상호작용, aqueous equilibrium 또는 부식 응답을 만들지 않는다. 합성 두 점 입력은 `examples/model_inputs.json`에 추가했으며 CoolProp 설치/수치 실행은 검증하지 않았다.

후속 검증에서는 단일 절점, 여러 절점 계보 유지, review 누락, CoolProp dependency 부재, 비기체 phase 실패 prefix, provider exception prefix, 시간 중복/역순, backend 혼합 거부, RunContext 불일치 및 point-budget 제한을 분리해 확인한다. Pure model의 계산 검증과 history sequencing/prefix 계약 검증은 각각 별도로 수행한다. 아직 실행한 검증은 없다.

### 혼합기체 CO₂ fugacity 시간 이력

`thermo.co2_mixture_fugacity_history`는 순서가 고정된 성분 목록을 공유하는 `CoolPropCo2MixtureFugacityRequest` tuple을 받아 각 절점의 온도·전체압력·몰분율을 평가한다. 조성은 절점별로 바뀔 수 있고, EOS 상태 객체는 첫 검토 통과 지점에서 한 번 만든 뒤 각 지점에서 몰분율과 PT 상태를 갱신해 재사용한다. 각 절점의 조성/EOS 적용성/기체상 review가 필요하다. 첫 `needs_data`, `out_of_scope` 또는 표준 provider 예외에서 멈추며 성공 prefix, 실패 위치, 요청 digest를 보존한다. component 목록/순서나 backend 변경, 시간 중복·역순, RunContext 불일치는 계약에서 차단한다. 혼합물의 binary interaction parameter 적합성은 caller 검토 대상이며 계산기가 이상혼합 fallback이나 시간 보간을 사용하지 않는다. 합성 2점 입력은 `examples/model_inputs.json`에 두었고 계산 및 CoolProp 설치 검증은 보류했다.

결과에는 `co2_fugacity_Pa`, CO₂ 부분압, 무차원 fugacity coefficient, phase index/label, provider ID, CoolProp version/revision, 설정 digest와 계산 record digest가 포함된다. 혼합 결과에는 전체 압력, 성분 목록과 몰분율, CO₂ 성분 index, `mixture_fugacity_computed=True`도 기록한다. adapter는 fugacity와 provider 식별/계보 필드만 반환한다. 실행 환경과 입력을 함께 보존하고, registry `AssessmentResult`의 `input_digest`도 저장한다.

## 근거와 검증 범위

CoolProp AbstractState 문서의 저수준 상태 갱신·성분 fugacity property 및 phase enum, 공식 혼합물 문서의 mole fraction·binary interaction 경계를 참고해 별도 호출 코드를 작성했다. CoolProp 자체 구현의 소스나 문장, 수치표를 복사하지 않았다. focused 회귀는 입력 review gate, 계산 유한성, provider digest, carbonate/AquaSolDB adapter와 phase 경계를 다룬다. 실제 mixture reference/실험 비교 및 독립 자격화는 별도 작업이다.

`scripts/validate_co2_fugacity.py`는 순수 성분 저압 이상기체 극한 `|phi - 1| <= 1e-4`, `f = phi * p_CO2` 항등식, 초임계 상태 통과, 압축 액상 배제, 저압 CO2/N2 mixture component fugacity identity 및 두 carbonate/AquaSolDB adapter lineage를 확인하고 입력·허용오차·관측값·provider digest를 JSON으로 남긴다. manifest command로 실행하면 이 JSON stdout 전체가 `hpc-results/<job>/task-126/result.json`의 해당 command `output`에 보존된다. 합성/상태방정식 내부 일관성 검사이며 독립 기준 EOS·실험 비교가 아니다.

공식 근거: [CoolProp AbstractState API](https://coolprop.org/_static/doxygen/html/class_cool_prop_1_1_abstract_state.html), [CoolProp Low-Level API와 mixture fractions](https://coolprop.org/coolprop/LowLevelAPI.html), [CoolProp mixture 모델·상평형 한계](https://coolprop.org/fluid_properties/Mixtures). AquaSolDB reader/comparison scope: [AquaSolDB 자료 설명](WET_CO2_DATA_KO.md).

