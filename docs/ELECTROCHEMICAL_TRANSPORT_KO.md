# 전기화학 경계가 결합된 제한형 수송

`electrochemistry.restricted_transport_campaign`은 고정된 1차원 finite-volume 격자에서 caller가 정의한 균질 질량작용 반응과 Butler–Volmer 경계반응을 결합한다. 팁(격자 말단) 반응은 기존 경계 flux로, 분포형 벽 반응은 격자 셀별 국부 용액전위를 사용하는 벽 flux로 계산한다.

## 입력 구성

Python 호출은 `ElectrochemicalTransport` 입력 계약을 사용하며 `assemble_electrochemical_transport()`로 질량작용망, 운반 입력, 반응표와 digest를 묶을 수 있다. 레지스트리에서는 JSON 입력을 직접 전달한다. `transport`에는 종 순서, 전하수, 유효 확산계수, 셀 초기농도, 시간 격자, 반응망 digest와 명시적인 전위 모델이 필요하다. 모든 반응 속도상수·반응 방향·농도 의존 법칙은 caller가 제공하고 적용 조건을 검토해야 한다.

벽 반응을 활성화하려면 `wall_surface_reactions`에 반응을 지정하고 `transport.wall_area_per_volume_m2_m3`에 셀별 실제 반응면적/체적을 입력한다. 벽 반응의 별도 provider ID, 반응 구성 digest, `wall_surface_flux_basis_reviewed`, `wall_surface_composition_and_reference_reviewed`, `equipotential_wall_and_metal_potential_reviewed`가 필요하다. 한 개의 `metal_potential_V`가 모든 셀의 금속 전위를 대표한다고 명시적으로 가정하므로, 축방향 전위강하나 국부 금속전위가 중요하면 이 모델을 적용하지 않는다. 용액전위는 입력된 prescribed field 또는 Poisson 계산의 셀별 결과를 사용한다.

선택적 다상 조합은 `solve_electrochemical_transport(request, phase_transport=competitive_request, ...)`에 `CompetitiveSolidEquilibriumTransport`를 전달한다. 수송 구간의 균질반응과 electrode boundary kinetics를 계산한 뒤 각 출력 knot에서 caller가 선언한 경쟁 중성 고체상 Davies, SIT 또는 B-dot 평형을 cell별로 적용한다. 종·전하·원소 구성, transport request, 활동도 provider/configuration digest 및 물리적 scope를 일치시켜야 한다. 결과 lineage의 `adapter_type`과 `phase_activity_model`에서 선택한 활동도 법칙을 구분한다. 이는 순차 operator split이며 동시 transport–phase–electrode solve나 precipitation kinetics가 아니다. 기존 단일 고체상 `EquilibriumReactiveTransport` 입력도 계속 사용할 수 있다.

```python
from matintegrity.electrochemical_transport import solve_electrochemical_transport

campaign = solve_electrochemical_transport(
    electrochemical_request,
    phase_transport=competitive_phase_request,
    activity_coefficients=activity_callback,
    axial_advection_velocity=velocity_callback,
)
```

`competitive_phase_request.transport`는 `electrochemical_request.transport`와 완전히 같아야 한다. 반응망의 `elemental_composition`이 phase의 모든 수용 종에 대해 제공돼야 하며, 활동도 callback의 configuration digest는 transport와 phase Davies/SIT/B-dot 설정에 고정된 값과 일치해야 한다. SIT 입력은 각 cell에서 같은 Evidence-linked interaction set을, B-dot 입력은 온도 지지와 종별 Evidence-linked A/B·ion-size·b 계수 세트를 사용해야 한다. 둘 다 검토된 물 질량 및 1 mol/L reference-concentration basis를 필요로 한다. Callback 인수는 필요한 경우 생략할 수 있지만, transport가 해당 공급자를 선언한 경우에는 제공해야 한다.

결과의 `surface_history`는 반환된 output-knot 농도와 전위로 반응식을 다시 평가한 진단이다. 경쟁 고체상 투영을 쓴 경우 projection 이후 상태를 사용하므로 실제 수송 적분 중 누적된 경계 flux와 같다고 해석하면 안 된다. 이 의미는 `surface_history_basis`에도 기록된다. 실제 경계 물질수지는 `transport_result`의 적분 ledger를 사용한다.

다상 조합 결과의 `phase_transport_lineage`에는 operator-split 유형, campaign/physical-scope ID, phase/transport request digest, activity provider/configuration digest, 고체상 ID, 온도 및 적용 review flag가 요약된다. 전체 입력 identity는 최상위 `input_sha256`에도 결합된다.

동일 요청에서 내장 벽 반응과 외부 `wall_surface_flux` callback을 동시에 지정하면 거절한다. 이는 면적당 flux가 이중으로 더해지는 것을 방지한다. caller 농도 kinetic law는 반응 ID별 support 범위를 벗어나면 계산을 중단한다. 셀마다 signed 종 flux를 벽 면적/체적으로 변환해 수송원의 물질수지 ledger에 넣는다.

## 지원 범위와 미지원 범위

이 API는 고정 격자·고정 형상에서 선언된 종, 반응, 전위 경계조건과 caller 보정 Butler–Volmer 반응의 조성/전위 응답을 계산한다. 기하 remapping API는 별도의 후속 계산으로 조합할 수 있지만 여기서 반응과 움직이는 경계를 완전 연성으로 풀지는 않는다. 다상 침전·용해 kinetics, 보호 피막 성장/파괴, 자동 반응망 생성, 보편적 wet-CO₂ 보정, 국부 금속전위 계산, 공학 규격 판정 또는 재료 자격화를 제공하지 않는다.

## 사용 전 검토

종·전하수·반응 화학량론과 전자수 일치, 농도 기준상태, 전극 기준전위, kinetics 보정자료와 support, 확산계수, 전위모델, 벽면적/체적, 셀 locality 및 금속 등전위 가정을 검토하고 각 digest와 review flag를 같은 입력 버전에 고정한다. 예제는 합성 fixture이며 검증 결과가 아니다. 수치/독립 자료 검증은 `docs/VALIDATION_KO.md`와 HPC manifest의 해당 항목이 완료될 때까지 미검증으로 취급한다.
