# 경쟁 고체상 활동도 평형과 제한 수송의 operator split

integration.competitive_solid_equilibrium_transport는 CompetitiveSolidEquilibriumTransport와 solve_competitive_solid_equilibrium_transport()로 호출하는 callback 기반 Python interface다. ModelRegistry.run() 계산기처럼 reaction·activity callback을 감추지 않는다. 호출 시 시간 의존 reaction(time_s, species_by_cell)을 직접 전달하고 필요하면 tip/wall flux, axial velocity와 activity-coefficient callback도 함께 전달한다. Callback 제공자 식별자와 configuration digest는 안쪽 RestrictedTransportRequest에 고정한다.

시작점에서 각 cell의 caller-declared 경쟁 중성 순수 고체상 및 Davies, SIT 또는 B-dot 평형을 먼저 계산한다. 이후 각 선언 출력 구간을 고정 geometry로 수송하고, 구간 끝마다 cell의 수용액 농도와 각 고체상 inventory를 다음 평형 입력으로 전달한다. 각 cell은 동일한 순서의 후보상, phase law/Ksp와 활동도·물 변환 설정을 사용해야 한다. transport activity callback의 provider ID 및 configuration digest는 phase activity 입력과 일치해야 하며 두 경로의 표준상태·계수 basis가 맞는다는 caller review가 필요하다. SIT의 directional interaction/Evidence set 및 B-dot의 종별 이온 크기·b 계수·Evidence는 모든 cell에서 동일하게 고정된다.

용존 종의 source는 침전 extent의 반대 부호를 적용하고, cell volume/reference area를 곱해 phase source로 집계한다. transport mouth/tip/reaction/wall ledger와 phase source ledger를 분리 보존하고, 초기 projection을 포함한 aqueous inventory closure를 확인한다. interval 내에 transport와 평형은 서로 순차 적용되므로 operator-splitting 오차를 제공하지 않는다. 고체상은 immobile이며 geometry는 고정이다. phase callback 중 하나라도 계산을 완료하지 못하면 이후 interval은 진행하지 않는다.

이 조합은 caller가 제공한 상 목록 중 중성 pure solid만 다루며, 전체 speciation, 상 자동 발견, 핵생성 또는 precipitation kinetic law, moving boundary, 동시 수송-반응 solve, 보호 scale 모델, 자격화된 corrosion rate를 제공하지 않는다. Davies wiring request는 `examples/competitive_solid_equilibrium_transport.py`, SIT 예제는 `examples/competitive_solid_sit_transport.py`, B-dot 예제는 `examples/competitive_solid_bdot_transport.py`에 있다. 예제는 입력 contract만 출력하며 callback 수치 계산을 실행하지 않는다. 기존 `transport_activity_to_phase_davies_mapping_reviewed` 필드명은 입력 호환성을 위해 남아 있으며 세 활동도 법칙에서 표준상태·parameter-basis review를 기록한다.


입력에는 physical_scope_id를 두어 평가 대상 경계를 고정한다. phase solver가 계산한 모든 species concentration과 phase inventory는 다음 구간을 실행하기 전에 새 계약으로 구성된다. 후속 interval에서 transport, 모든 cell phase projection, 네 aggregate source ledger와 cell별 wall ledger가 모두 유효할 때만 상태를 commit한다. 이후 단계가 실패하면 이전 완료 knot prefix와 실패 interval의 partial_step을 별도 반환한다.

Callback builder가 온도·종 순서·원 요청 등을 포함한 별도 configuration digest를 생성하면 transport_activity_adapter_configuration_sha256에 callback.configuration_sha256를 지정하고, 안쪽 transport.activity_configuration_sha256에도 같은 값을 기록한다. Phase 요청의 configuration_sha256는 원 파라미터 설정 해시로 유지한다. 별도 adapter digest를 생략하면 기존 직접 해시 일치를 요구한다. Provider ID는 항상 같아야 하며 두 경로의 물 변환·온도·표준상태·계수 basis 대응은 caller가 검토한다. 결과는 transport adapter와 phase parameter 설정 해시를 각각 보존한다.

별도 adapter digest 경로는 callback의 phase_parameter_configuration_sha256, species_ids, temperature_K 메타데이터를 필수 대조한다. SIT/B-dot는 provider revision과 parameter record digest도 대조한다. 내장 SIT/B-dot builder가 원 parameter configuration digest를 해당 메타데이터로 제공한다. Custom callback도 동일 속성을 명시해야 한다. 이 검사는 입력 계보 일치 검사이며 활동도 물리 타당성을 검증하지 않는다.

SIT/B-dot 별도 adapter 경로는 물 질량/용액 부피, Debye–Hückel A와 실제 ordered parameter 배열 digest도 비교한다. B-dot에서는 B 상수도 비교한다. 동일 record digest 문자열만으로 서로 다른 수치 계수 배열을 허용하지 않는다. 배열 순서까지 보존하므로 caller는 두 경로의 parameter 행을 같은 순서로 제공해야 한다.

Python 연결에는 bind_competitive_solid_transport_activity(request, callback)를 사용할 수 있다. 이 함수는 provider와 원 phase 설정 해시를 먼저 대조하고, callback configuration digest를 transport와 adapter 필드에 함께 기록한 뒤 전체 중첩 입력을 strict Python validation으로 재구성한다. model_copy(update=...)의 검증 생략을 피하며 원 요청을 수정하지 않는다. callback 평가나 평형 계산은 수행하지 않는다. 실행 시에는 solve_competitive_solid_equilibrium_transport(bound_request, ..., activity_coefficients=callback)로 동일 callback을 전달한다.

```python
from matintegrity.models.aqueous_activity_iteration import build_bdot_transport_activity_callback
from matintegrity.multiphase_equilibrium_transport import (
    bind_competitive_solid_transport_activity,
    solve_competitive_solid_equilibrium_transport,
)

# phase_transport_request and aqueous_bdot_request are caller-reviewed inputs.
# Their species order, temperature, water conversion and parameter set must agree.
callback = build_bdot_transport_activity_callback(
    aqueous_bdot_request,
    transport_species_ids=phase_transport_request.transport.species_ids,
    temperature_K=phase_transport_request.uniform_temperature_K,
)
bound_request = bind_competitive_solid_transport_activity(
    phase_transport_request, callback,
)
# Pass the caller's reviewed reaction function when calculation is requested.
# result = solve_competitive_solid_equilibrium_transport(
#     bound_request, reaction=reaction, activity_coefficients=callback,
# )
```

SIT 사용 시 builder만 build_sit_transport_activity_callback로 교체하고 대응하는 AqueousSITIteration 입력을 제공한다. 위 코드는 사용자 입력의 연결 순서를 설명하며 합성 실험이나 수치 검증 결과가 아니다.
