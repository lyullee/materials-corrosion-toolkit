# 스케일 확산 한계에서 금속 침투 상한으로의 변환

## 목적

`corrosion.scale_diffusion_metal_loss_bound`는 digest로 고정한 다층 스케일의 계산된 정상 확산 한계를 caller가 제공한 반응 화학양론 및 금속 물성에 연결해, **조건부 금속 침투율 상한**을 산출합니다. 이는 실제 부식률 예측이나 실측치가 아닙니다.

## 계산

운반 종의 면적 몰 플럭스 한계를 (J_{lim}), 반응 진행도 1몰당 생성되는 운반 종의 몰수를 ν, 반응 진행도 1몰당 용해되는 금속 원자 몰수를 (n_M), 금속 몰질량을 (M_M), 밀도를 ρ라 두면 각 caller 반응 경로에 대한 상한은 다음과 같습니다.

```text
reaction_extent_flux_ceiling = J_lim / ν
metal_mass_flux_ceiling = (J_lim / ν) * n_M * M_M
uniform_penetration_rate_ceiling = metal_mass_flux_ceiling / ρ
uniform_penetration_loss_ceiling = uniform_penetration_rate_ceiling * exposure_duration
```

여러 경로가 같은 운반 종을 생성하고 실제 분배를 알 수 없을 때는 caller가 선언한 완전한 금속 용해 생성 경로 집합 안에서 금속 몰/운반 종 몰 비가 가장 큰 경로를 전체 상한에 사용합니다. 이는 경로 확률이나 실제 반응 분배를 뜻하지 않습니다.

## 필수 데이터 및 검토

- `chemistry.layered_scale_diffusion_limit`의 `computed` AssessmentResult 전체 digest와 내부 input/context digest
- 동일한 물리 범위와 면적 기준의 운반 종 플럭스 상한
- 운반 종 생성 몰수와 금속 원자 용해 몰수의 경로별 caller 화학양론
- 공급자 revision, record ID, SHA-256, Evidence를 포함한 몰질량·밀도
- 정상 플럭스 한계가 기간 동안 유지된다는 가정, 완전한 생성 경로 집합, 균일 침식 basis, 범위·상태·기간 대응, 기타 금속 손실 경로 부재, 계산 이용 권한을 각각 검토

검토가 빠지면 계산하지 않고 `needs_data`를 반환합니다. digest·종·범위·면적이 맞지 않으면 입력 검증에서 거절합니다. overflow나 유한 수치범위 초과는 `out_of_scope`로 반환합니다.

## 적용 경계

노출 기간 동안 스케일 상태, 물성 및 계산된 정상 확산 상한이 유지된다고 caller가 판단한 경우에만 그 기간의 상한 손실을 계산합니다. 시간에 따른 스케일 갱신, 실제 전류, 지배 반응 분배, 국부 부식 배율, 부식률 추정, 남은 수명, 수용 판정 및 고장확률을 추론하지 않습니다. 복수 반응 경로가 선언됐더라도 이 API는 반응을 동시에 계산하거나 전기화학 상태를 풀지 않습니다.

## Python API 형태

```python
from matintegrity.scale_diffusion_metal_loss_bound import (
    ScaleDiffusionMetalLossBound,
    ScaleLimitedMetalDissolutionPathway,
    evaluate_scale_diffusion_metal_loss_bound,
)

request = ScaleDiffusionMetalLossBound(
    assessment_id="transport-bound-001",
    physical_scope_id="component-A",
    scale_transport_result=scale_transport_assessment,
    scale_transport_result_sha256=scale_result_digest,
    surface_area_basis_id="wetted-area-A",
    exposure_duration_s=duration_s,
    candidate_pathways=(caller_reaction_mapping,),
    sustained_steady_flux_limit_reviewed=True,
    complete_productive_branch_set_reviewed=True,
    reaction_stoichiometry_and_metal_mapping_reviewed=True,
    common_area_density_and_uniform_recession_reviewed=True,
    scope_state_and_duration_transfer_reviewed=True,
    no_other_metal_loss_path_over_duration_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_scale_diffusion_metal_loss_bound(request)
```

실제 물성, Evidence 및 화학양론은 호출자가 해당 재료와 조건에 맞게 공급해야 합니다. 코드 예시는 데이터나 재료 기준을 제공하지 않습니다.
