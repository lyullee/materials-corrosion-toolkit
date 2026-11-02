# 층상 scale 확산 상한과 전기화학 표면 반응 연결

`ScaleLimitedSurfaceFlux`는 완료된 `chemistry.layered_scale_diffusion_limit` 결과를 특정 전기화학 경계의 대상 종 생성 상한으로 연결한다. 단일 종은 `ElectrochemicalTransport.scale_limited_surface_flux`에 넣고, 추가 종별·경계별 제한은 `additional_scale_limited_surface_fluxes` tuple 또는 `assemble_electrochemical_transport(..., additional_scale_limited_surface_fluxes=...)`로 구성한다. 기존 단일 binding 입력은 계속 지원한다.

## 입력 lineage와 검토

Binding은 전체 `AssessmentResult`와 그 canonical SHA-256, physical scope, substrate/solution condition, scale phase/state, 수송 종, 선택적 `surface_area_basis_id`, 적용 경계(`tip` 또는 `wall`) 및 제한할 reaction IDs를 보존한다. 결과 digest와 모델 ID, `mol/m2/s` 단위를 확인하고 scale 결과의 scope/state/species/면적 basis 필드가 요청과 정확히 일치해야 한다. 같은 경계에 여러 종 상한을 적용할 때는 모든 binding이 동일하고 명시적인 surface-area basis ID를 가져야 한다. 제한 reaction ID는 선택 경계에서 대상 종을 어느 반응 방향으로든 생성할 수 있는 caller 지정 reaction set 전체와 일치해야 한다.

호출자는 complete reaction-set, 동일 physical scope, flux/current 표면적 기준, scale 상태가 계산 horizon 동안 고정된다는 가정 및 금속/용액 전위 reference compatibility를 검토해야 한다. 검토가 빠지면 결과에 각 binding의 `missing_reviews` 이름을 포함해 계산을 보류한다. 계층 상한의 유효 시간을 넘는 transport에 이를 연결하지 않는다.

## 적용 방식

각 Butler–Volmer 평가점에서 선택 반응들의 대상 종 총 생성률을 모든 가능한 반응 방향에 대해 합산한다. 합이 층상 계산의 caller area-average flux limit 이하이면 반응률을 그대로 둔다. 상한을 넘으면 화학량론 계수 부호로 대상 종 생성 방향을 정해 해당 anodic 또는 cathodic partial-current branch에 공통 감쇠계수를 적용하고 반대 branch는 유지한다. 조정된 순전류에서 반응 진행률과 모든 화학량론 종 flux를 다시 계산하므로 각 반응의 전자·종 비율을 보존한다. 자유부식 모드에서는 감쇠된 반응 집합으로 순전류가 0이 되는 전위를 다시 찾고, caller 공통 지원 구간에서 근을 bracket하지 못하면 계산을 제한한다.

결과 diagnostics에는 각 제한 종별 입력 상한, 제한 전/후 총 생성 flux, 감쇠계수, scale-state/result digest, 실제 호출 경계와 limiter 적용 빈도를 기록한다. 한 반응 branch가 여러 제한 종을 생성하면 그 branch에는 종별 계산 배율 중 가장 작은 값을 한 번 적용한다. 따라서 binding 나열 순서에 결과가 의존하지 않는다. 기존 `scale_limiter_diagnostics`와 `scale_transport_flux_limit`은 단일 binding일 때 유지되고, 전체 기록은 `scale_limiter_diagnostics_by_species`와 `scale_transport_flux_limits`에 제공된다. Tip과 wall의 반응집합은 서로 분리하여 제한한다.

## 물리 범위

이는 고정된 확산 상한을 선택한 표면 반응 집합에 적용하는 보수적 limiter composition이다. 실제 시간변화 피복률, 비균일 scale morphology, 종별 다층 확산과 Butler–Volmer의 완전 동시 해, scale 형성/용해 kinetics와 coverage 업데이트, transport 이동경계, 부식률 qualification 또는 보호율을 계산하지 않는다. `computed`는 caller scale upper bound와 caller electrode reaction set을 결합해 수치적으로 평가했다는 뜻일 뿐, 실제 scale 보호를 입증하지 않는다.

실행 및 독립 물리 qualification은 후속 검증 과제로 남는다.
