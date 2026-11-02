# 원통형 wet-CO₂ 공간 전기화학과 감육 기하 반복 연결

`integration.wet_co2_cylindrical_geometry_coupled_history`는 caller가 제공한 BV reaction set, aqueous species formula, boundary history, 원통형 초기/scale geometry를 사용해 제한된 damped-Picard 반복을 수행한다. 각 반복에서 공간 transient species transport와 공통 혼합전위를 전체 exact-knot 시간 이력에 대해 다시 계산하고, reaction extent로부터 누적 alloy-element release 및 원통 bore radius target을 구한다. target geometry가 다음 trial로 들어가며 고정점 잔차가 geometry·element inventory 기준을 만족한 뒤에만 strict geometry closure 모드로 마지막 계산을 한 번 더 수행한다.

이 계산은 기본 spatial finite-volume evaluator 및 그 trial-result 인터페이스를 실제로 반복 호출한다. 결과를 받아 외부에서 설명만 붙이는 adapter가 아니다. 다만 사용자 parameter와 고정된 exact-knot inputs에 대한 계산이라는 점, 아래의 고정 scale inventory 한계는 유지된다.

## 기본 사용 흐름

먼저 `WetCo2CylindricalSpatialMixedPotential`에 같은 asset/location/time basis의 species·초기 radial profile·alloy record·exact-knot BC/BV calibration·geometry history를 입력한다. geometry history는 time zero에 zero wall recession으로 시작해야 한다. 이어 해당 요청을 `WetCo2CylindricalGeometryCoupledHistory.spatial_request`에 넣고 반복/완화/수렴 공차와 각 review gate를 선언한다. 일반 `default_registry()` 등록은 별도 중앙 통합 단계에서 수행한다.

```python
from matintegrity.wet_co2_cylindrical_geometry_coupled_history import (
    WetCo2CylindricalGeometryCoupledHistory,
    evaluate_wet_co2_cylindrical_geometry_coupled_history,
)

campaign = WetCo2CylindricalGeometryCoupledHistory(
    assessment_id="asset-location-run-001",
    spatial_request=spatial_request,
    maximum_geometry_iterations=24,
    geometry_relaxation_factor=0.5,
    absolute_bore_radius_tolerance_m=2e-9,
    relative_bore_radius_tolerance=1e-7,
    absolute_wall_inventory_tolerance_mol_m=1e-12,
    relative_wall_inventory_tolerance=1e-8,
    maximum_iteration_work_units=20_000_000,
    scale_inventory_is_caller_fixed_at_each_knot_reviewed=True,
    exact_knot_radius_reconstruction_reviewed=True,
    spatial_bv_model_and_boundary_applicability_reviewed=True,
    element_to_alloy_release_mapping_reviewed=True,
    geometry_and_scale_axisymmetry_reviewed=True,
    no_inter_knot_or_qualification_claim_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_wet_co2_cylindrical_geometry_coupled_history(campaign)
```

실제 parameter와 evidence는 예시값을 복사하지 말고 caller 검토 자료를 사용한다. raw provider assets는 기존 data-rights 정책에 따라 배포물과 분리한다.

## 계산 연결과 digest

1. 기존 cylinder geometry evaluator로 caller seed geometry를 확인하고 time-zero metal recession이 0인지 검사한다.
2. trial마다 per-knot bore radius를 steel inner radius로 역변환한다. caller scale inventory와 molar volume은 각 knot에서 고정 입력으로 둔다. 변환한 steel recession 이력은 비음수·비감소여야 하고 외경 안에 있어야 한다.
3. trial history를 새 digest로 고정한다. Evidence는 `model_prediction` 기원, 새 내부 trial-history ID, 상위 원자료 citation 및 caller license 참조로 다시 기록한다. 원 provider의 새 측정으로 표시하지 않는다.
4. exact geometry digest, radius path, source request digest, iteration 번호로 `fixed_point_input_sha256`를 만든다. 기존 spatial evaluator를 geometry trial mode로 실행한다.
5. spatial solver는 각 interval의 BDF transient radial species balance를 풀고 그 integration states에서 caller BV branch를 공통 zero-net-current potential에 결합한다. species/aqueous charge/aqueous element 잔차는 trial에서도 그대로 fail-closed 검사한다.
6. BV reaction extent에서 alloy element release를 누적한다. 내면 강재 radius는 `sqrt(r0² + released_mass_per_length/(pi*density))`로 계산하고, 각 knot에 caller 고정 scale volume을 빼 bore radius target을 재구성한다. 외경을 소진하거나 수학적 bore가 0 이하가 되면 실패한다.
7. trial 입력 geometry와 release로 인한 geometry 차이, per-element inventory 잔차, 호출/result digest를 보존한다. 완화는 bore radius 대신 steel inner radius 좌표에서 적용해 단조 recession 조건을 유지한다.
8. geometry와 원소 수지 공차를 모두 만족하면 trial result를 최종으로 승격하지 않고, 동일 geometry에서 기본 strict spatial evaluator를 한 번 더 실행한다. 이 마지막 수지 검사도 계산돼야 최종 `computed`가 된다.

## 수지와 수렴 값

- 고정점 residual은 각 exact knot의 `target_bore_radius_m - trial_input_bore_radius_m` 최대 절대값이다. 성공은 absolute+relative 길이 공차 아래를 요구한다.
- 원소 잔차는 기존 trial model의 `initial wall element inventory - trial geometry wall element inventory - cumulative reaction-derived release`다. 각 element·knot별로 절대 공차와 초기 벽 inventory에 대한 상대 공차를 적용한다.
- trial 동안 aqueous species inventory, electric charge, aqueous element balance, BV calibration support, reaction direction, finite/nonnegative concentration, finite geometry 및 wall release의 부호 조건은 여전히 검사된다.
- 최종 strict solve는 실제 trial geometry의 steel element inventory와 계산 방출량이 공간 evaluator의 wall closure limit을 만족하는지 재검사한다. strict 재검사가 실패하면 바깥 trial 수렴값과 무관하게 최종 계산은 거부된다.
- 반복 한도, work estimate, SciPy solver 도달 실패, 수지 불일치 및 부적합 geometry는 완료 prefix와 함께 실패 상태로 반환한다. 부분 이력을 완성 수명/감육 결과로 사용해서는 안 된다.

## 정해진 scope와 남은 gap

- Scale phase moles와 molar volume은 caller가 시간 knot마다 준 이력으로 고정한다. scale 석출/용해, 종속 scale reaction kinetics, 확산 제한 성장/박리, morphology 및 wall adhesion을 이번 outer loop에서 재계산하지 않는다.
- 각 시간 구간 내 geometry는 기존 spatial solver의 left-held exact-knot 규칙이다. 기록되지 않은 구간별 shape 변화나 시간 crossing을 추론하지 않는다.
- 원통/축대칭/균일 alloy·밀도·recession, radial discretization, BV branch calibration, surface reaction area와 species stoichiometry의 적용성은 caller review에 의존한다.
- 자동 aqueous network/speciation/activity law나 상 발견/선택은 제공하지 않는다. caller의 species, activity/transport/BV inputs에 내재한 불확실성을 제거하지 않는다.
- 비수렴은 `out_of_scope` 진단만 제공한다. 이 방법의 contraction, uniqueness, 안정성 또는 오류 bound는 증명하지 않는다. relaxation과 공차는 계산 제어 parameter이며 실험 uncertainty가 아니다.
- 실제 소재·유체의 독립 실험 비교, 다른 electrochem solver와 benchmark, mesh/time-step sensitivity, parameter identifiability, field-transfer 및 code qualification은 이후 검증 과제다.
