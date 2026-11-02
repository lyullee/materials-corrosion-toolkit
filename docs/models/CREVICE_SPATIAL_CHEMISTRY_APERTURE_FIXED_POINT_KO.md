# 크리비스 chemistry–수송–aperture–hydraulics bounded fixed point

## API

- ModelSpec 후보 ID: `integration.crevice_spatial_chemistry_aperture_fixed_point`
- 요청: `CreviceSpatialChemistryApertureFixedPointRequest`
- 계산: `solve_crevice_spatial_chemistry_aperture_fixed_point`
- aperture provenance: `caller_solid_volume_to_aperture_response`
- hydraulic provenance: `caller_aperture_to_hydraulic_velocity_response`
- solver provenance: `bounded_geometry_hydraulic_chemistry_picard_iteration`

이 모듈은 기존 `CreviceSpatialChemistryTransportRequest` 계산을 bounded Picard 방식으로 반복 호출한다. 각 trial은 현재 aperture history에서 cell/face area를 만들고, 사용자가 제공한 aperture-민감도 행렬로 face velocity history를 만든 다음, variable-area Nernst–Planck 수송과 exact-knot Davies/speciation/solid equilibrium 경로를 다시 실행한다. trial chemistry의 유한 고체 재고 변화에서 계산한 새 aperture와 그 aperture로 예측한 새 hydraulic velocity가 모두 반복 입력과 일치해야 수렴한다.

## Caller가 반드시 고정할 관계식

단면적은 caller가 제공한 transverse width `w`와 trial cell aperture `h[k,i]`의 곱 `A_cell[k,i] = w h[k,i]`이다. Face aperture는 각 face의 cell-weight 행으로 계산한다: `h_face[k,j] = Σ_i W[j,i] h[k,i]`, `A_face = w h_face`. 모든 weight 행 합은 1이고, 입구 face는 첫 셀, 막힌 끝 face는 마지막 셀에 정확히 대응해야 한다. 내부 face 보간과 입구/끝 mapping은 입력에서 선언하고 검토한다.

aperture response는 exact knot의 고체 재고를 실제 liquid cell volume에 곱해 solid mol수를 만든다. knot 0의 평형 고체 몰수를 기준으로 net volume 변화 `ΔV_solid = Σ_phase (n_phase[k,i] − n_phase[0,i]) V_m,phase`를 계산한 뒤, caller의 `deposit_volume_to_gap_change_factor_by_cell`을 적용하여 `h_target[k,i] = h_initial[i] − factor[i] ΔV_solid/(w Δx)`를 만든다. 첫 knot aperture는 geometry anchor로 유지한다. 고체 몰부피, geometry factor, face-area weights, width는 별도 digest/Evidence로 고정한다. 이 mapping은 임의 보편식이 아니라 caller가 선언한 volume-to-gap response이다.

hydraulic closure는 caller 기준속도에 caller 민감도 tensor를 적용한다: `u_target[k,j] = u_base[k,j] + Σ_i J[k,j,i](h[k,i] − h_initial[i])`. `J`의 단위는 m/s/m이고, exact knot × face × cell 순서로 입력한다. 모든 blind-tip sensitivity 계수는 정확히 0이어야 한다. 이 선형 응답 밖의 pressure, viscosity, pump, momentum 또는 hydraulic law는 계산하지 않는다.

## 반복, residual, failure

각 반복에서 area schedule과 reaction schedule digest를 반영한 기존 transport-chemistry solver를 재실행한다. 그 solver는 interval별 BDF finite-volume Nernst–Planck flux, caller kinetic reaction rates, per-knot 활동도/speciation·finite-solid 평형, aqueous+solid 원소 inventory ledger와 full lineage를 반환한다. Aperture와 hydraulic 입력은 요청의 `relaxation_fraction`으로 target에 접근한다.

수렴에는 두 조건이 모두 필요하다. aperture의 최대 절대 변화가 `aperture_absolute_tolerance_m + aperture_relative_tolerance × aperture_scale` 이하여야 하고, hydraulic velocity의 최대 절대 변화가 `velocity_absolute_tolerance_m_s + velocity_relative_tolerance × velocity_scale` 이하여야 한다. transport function evaluation 총량과 iteration 수에는 caller budget이 적용된다. 하위 계산 실패, mapping 오류, 0 이하 aperture, blind-tip 속도 불일치, 예산 초과 또는 최대 반복 후 잔차 미달이면 결과를 수락하지 않는다. 완료한 각 trial의 geometry/solver digest, residual, solver 결과 digest는 순서대로 보존한다. 실패 결과에는 이 trial lineage prefix를 남기고 `committed=false`를 반환한다.

## 질량수지 및 적용 경계

각 trial의 기반 transport-chemistry 계산이 transport 구간별 종 inventory, local electroneutrality, zero-current, finite competing-solid extent 및 exact-knot aqueous+solid 원소 closure를 통과해야만 aperture update가 고려된다. 전체 fixed point도 그 계산 결과의 원소 closure history를 그대로 반환한다. 고체 몰부피를 통해 변환된 deposit는 geometry response에만 연결하며, 별도 phase kinetics·전기화학 벽 flux·혼합전위 결과를 만들지 않는다.

이 계산은 caller가 공급한 유량/속도 민감도와 solid-volume-to-gap response가 유효하다는 검증을 대신하지 않는다. 내부 구간 활동도 계수는 하위 sequential operator-split 모델에 따라 좌측 knot 값으로 고정된다. 따라서 각 BDF 내부 시점의 수송·chemistry 완전 동시수렴은 아니다. 자동 종/고체상 발견, precipitation kinetics, metal loss, morphology, aperture law 추정, pressure-driven hydraulics, corrosion-rate 또는 건전성 qualification은 범위 밖이다.

## 외부 연동

이 파일은 독립 코어로 작성했다. 중앙 registry, schema exporter, capability/source catalog 변경은 통합 단계에서 수행한다. API 연결 시 하위 `CreviceSpatialChemistryTransportRequest`의 geometry, caller kinetic schedule, aqueous activity, phase record와 rights Evidence를 유지해야 한다. 새 API는 provider coefficient와 고체 몰부피가 입력 Evidence에 허가/출처가 명시된 경우만 유효하다.
