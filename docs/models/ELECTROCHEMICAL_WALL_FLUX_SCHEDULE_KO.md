# 전기화학 금속 손실 이력에서 틈새 벽면 플럭스 공급자 만들기

`build_electrochemical_wall_flux_schedule()`는 계산된 `integration.electrochemical_partial_current_metal_loss` 결과를 `solve_crevice_transport_recession_feedback()`의 `wall_surface_flux` callback 계약으로 바꾼다. 각 시간 구간에서 원 결과의 `anodic_metal_removal_mol`을 구간 길이와 caller가 평가한 branch 공통 노출 면적으로 나눠 몰 플럭스 밀도를 만든다. 그 플럭스를 동일한 local average로 각 transport cell에 반복하고, 결과의 금속 종 외 다른 종은 0으로 둔다.

## 입력과 연결

1. 계산 완료 상태의 `AssessmentResult`와 전체 결과의 canonical SHA-256을 제공한다.
2. transport의 순서 있는 `species_ids`, 셀 수, source-clock origin 결정, 모든 branch가 같은 노출 면적 basis를 쓴다는 검토, 전역 평균을 각 cell의 국부 플럭스로 적용한다는 검토를 기록한다.
3. callback의 `provider_id`, `provider_revision`, `configuration_sha256`를 `RestrictedTransportRequest`의 `wall_surface_provider_id`, revision/설정 계약과 일치시킨다. 기존 request가 갖는 `wall_surface_flux_basis_reviewed` 및 metal dissolution 리뷰도 요구된다.
4. callback은 global elapsed seconds를 받는다. upstream 이력이 0초가 아닌 source origin이면 명시된 origin review를 거쳐 첫 절점을 elapsed 0초에 둔다. 시간 외삽은 오류다.

반환 배열은 `(species, cell)` 순서이고 `mol m-2 s-1`이다. 양의 값은 원 계산에서 caller가 금속 용출로 매핑한 양극 branch만 뜻한다. 음극 금속 등가량이나 signed net loss를 용출 source로 사용하지 않는다.

이 adapter는 upstream electrochemical history를 transport 농도·전위에 되먹임하지 않는다. caller가 승인한 공통 면적 평균 flux density를 cell마다 적용하는 일방향 연결이다. moving aperture에서 transport가 적분하는 실제 벽 면적은 upstream 고정 기준 면적과 달라질 수 있으므로, 변화 형상에서는 계산된 누적 몰수가 upstream 금속 손실 장부와 같다고 보장하지 않는다. 모든 branch의 노출 면적과 cell-local 매핑이 합당하지 않으면 이 adapter를 사용하지 않는다. 이는 전류 분포 모델, 동시 유동·화학·형상 해석, 부식 수명, 자격화가 아니다.

테스트, 계산, 예제 실행 및 독립 물리 검증은 수행되지 않았다.
