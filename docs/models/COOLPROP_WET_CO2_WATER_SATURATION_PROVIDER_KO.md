# CoolProp 순수 물 포화수증기 fugacity provider

## API

- 타입: `CoolPropPureWaterSaturationFugacityRequest`
- 호출: `pure_water_saturated_vapor_fugacity_from_coolprop(request)`
- Provider ID: `thermo.coolprop_pure_water_saturated_vapor_fugacity`
- Source ID: `coolprop_pure_water_saturated_vapor_state`

요청에는 내부 벽면 온도(K), CoolProp backend(기본 `HEOS`), caller가 선언한 fugacity 절대 bound(Pa), 그리고 응축상이 순수 물로 취급 가능한지 검토한 flag를 넣는다. CoolProp은 함수 실행 시점에만 lazy import된다. 설치되지 않았거나 backend가 포화 기상 fugacity 계수를 지원하지 않으면 포화압만 대신 돌려주지 않고 오류로 중단한다.

provider는 CoolProp의 `AbstractState`를 만들고 `(Q=1,T=T_wall)` 포화수증기 상태에서 압력과 무차원 fugacity coefficient를 읽는다. 출력은

```text
f_water,sat = p_sat · φ_water,vapor
```

이다. CoolProp의 공식 문서는 포화상에서 vapor quality `Q=1`로 증기 상태를 선택하는 방식을 설명하며, `AbstractState`는 무차원 fugacity coefficient accessor를 제공한다. [CoolProp 포화상태 문서](https://coolprop.org/coolprop/HighLevelAPI), [AbstractState API](https://coolprop.org/_static/doxygen/html/class_cool_prop_1_1_abstract_state.html).

## Wet-CO₂ condensate API 연결

반환 dictionary에 `WetCo2CondensateStateRequest`의 `condensate_water_equilibrium_fugacity_at_wall_Pa`, `wall_equilibrium_fugacity_absolute_bound_Pa`, `water_property_provider_id`, `water_property_provider_revision`, `water_configuration_sha256`, `water_result_sha256` 필드가 있다. `water_provider_evidence`는 요청의 Evidence에 추가한다. CO₂ fugacity와 Henry 자료 Evidence는 별도 provider/record에서 추가해야 한다. property configuration과 result digest에는 backend, fluid, 벽면 온도, quality, CoolProp 버전·revision, bound 및 결과값이 포함된다.

간단 연결 예:

```python
water_state = pure_water_saturated_vapor_fugacity_from_coolprop(
    CoolPropPureWaterSaturationFugacityRequest(
        wall_temperature_K=wall_temperature_K,
        backend="HEOS",
        caller_absolute_bound_Pa=declared_bound_Pa,
        pure_water_condensate_phase_applicability_reviewed=True,
    )
)

condensate_request = WetCo2CondensateStateRequest(
    # ... caller-owned asset, state, CO2 fugacity, Henry data and reviews ...
    condensate_water_equilibrium_fugacity_at_wall_Pa=(
        water_state["condensate_water_equilibrium_fugacity_at_wall_Pa"]
    ),
    wall_equilibrium_fugacity_absolute_bound_Pa=(
        water_state["wall_equilibrium_fugacity_absolute_bound_Pa"]
    ),
    water_property_provider_id=water_state["water_property_provider_id"],
    water_property_provider_revision=water_state["water_property_provider_revision"],
    water_configuration_sha256=water_state["water_configuration_sha256"],
    water_result_sha256=water_state["water_result_sha256"],
    evidence=(water_state["water_provider_evidence"], co2_evidence, henry_evidence),
)
```

## 범위 및 데이터 경계

- 계산 대상은 순수 물의 포화증기 fugacity다. CoolProp saturation pressure에 기상 fugacity coefficient를 곱하며 total gas mixture의 수증기 fugacity를 계산하지 않는다. 실제 gas-side water fugacity는 혼합기체 EOS/provider 값으로 별도 공급해야 한다.
- 혼합물/용액 속 물의 활동도는 계산하지 않는다. 염수, MEG/TEG, 유기 응축액에서는 이 pure-water 결과를 실제 액상 평형 fugacity로 간주하지 말고 activity-aware property provider를 사용한다.
- CO₂ EOS/fugacity, CO₂ Henry 계수, 응축량·속도, droplet 체류, pH와 부식률은 계산하지 않는다. CO₂ EOS 결과가 필요한 경우 지원 basis를 명시한 별도 CO₂ provider API를 사용한다.
- 절대 bound는 caller가 외부 근거로 정한다. 코드가 CoolProp 불확도나 일반적인 수치 오차를 자동 생성하지 않는다.
- 순수 물 응축상 적용성 flag, fugacity 표준상태 일치, gas mixture 속 실제 water fugacity와 pressure 적합성은 caller가 확인한다.

## 선택 의존성과 라이선스

Core import는 CoolProp에 의존하지 않는다. 이 함수를 호출할 때만 `CoolProp` Python package가 필요하다. CoolProp은 MIT 라이선스를 표기한다([공식 저장소](https://github.com/CoolProp/CoolProp)). 본 provider는 제3자 코드나 CoolProp 물성 표를 복사·재배포하지 않고 해당 라이브러리에 계산을 위임한다. CoolProp package와 배포본의 실제 license notice를 함께 보존해야 한다.

별도 수치 검증은 수행하지 않았다. 사용 전 선택한 backend의 물 fugacity coefficient 지원과 운영 범위 내 출력은 전체 검증 단계에서 확인해야 한다.

## Caller-reviewed 단일상 P–T 물성

기존 포화증기 함수와 별개로 `CoolPropPureWaterSinglePhaseStateRequest` / `pure_water_single_phase_state_from_coolprop()`를 사용할 수 있다. 기대상을 `liquid`, `gas`, `supercritical_liquid`, `supercritical_gas`, `supercritical` 중 하나로 명시하고 `pure_water_and_phase_applicability_reviewed=True`를 설정한다. CoolProp이 반환한 상 분류가 caller 선언과 다르거나 상태가 2상이면 중단한다.

```python
state = pure_water_single_phase_state_from_coolprop(
    CoolPropPureWaterSinglePhaseStateRequest(
        temperature_K=temperature_K,
        pressure_Pa=absolute_pressure_Pa,
        backend="HEOS",
        expected_phase="liquid",
        pure_water_and_phase_applicability_reviewed=True,
    )
)
```

결과에는 순수 물 밀도, 비엔탈피, 정압비열, 점도, 열전도도, 음속, 압축성계수와 provider/runtime/result digest가 포함된다. registry ID는 `thermo.coolprop_pure_water_single_phase_state`다. 이후 수송 계산에서 이 값을 물성 입력으로 사용할 때는 해당 온도·압력·상태 범위를 제공받는 모델의 공간·시간 조건에 적용할 수 있는지 별도로 검토해야 한다. 이 API는 염·산·글리콜 혼합물, 2상 상태, 계면 전달, 물성 외삽, 유동 상관식 또는 부식 법칙을 만들지 않는다.

상 코드는 CoolProp `AbstractState.phase()`를 그대로 기록하고, CoolProp이 판정한 상이 호출자 선언과 일치하는지 검사한다. phase enum은 저수준 Python API의 `CoolProp.CoolProp.phases.iphase_*` 이름을 사용한다. 액상·기상·2상·초임계 분류와 `PT_INPUTS` 입력 순서는 [공식 Low-Level API 문서](https://coolprop.org/coolprop/LowLevelAPI.html)에 따른다. phase를 강제로 지정하지 않으므로 잘못 선언한 phase를 EOS 입력으로 강제하지 않고 provider의 P–T flash 결과를 검토한다.
