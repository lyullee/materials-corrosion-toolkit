# 크리비스 공간 혼합전위–Faradaic chemistry coupling

## API와 연동 경로

- 독립 코어 ID: `integration.crevice_faradaic_spatial_chemistry_coupling`
- 입력: `CreviceFaradaicSpatialChemistryRequest`
- 계산: `solve_crevice_faradaic_spatial_chemistry`
- Nernst 자료: `CreviceNernstBranchMap`
- Faradaic 화학양론: `CreviceFaradaicBranchMap`
- provenance source IDs: `caller_spatial_nernst_standard_potential_and_activity_quotient`, `caller_species_molar_conductivity_mapping`, `caller_faradaic_branch_species_and_reservoir_stoichiometry`, `knotwise_spatial_mixed_potential_faradaic_inventory_split`

이 모듈은 기존 variable-area 반응수송과 exact-knot chemistry를 interval 순서대로 호출하고, 각 endpoint에서 chemistry 상태로 Nernst 전위를 다시 만들고 caller Butler–Volmer 지점별 branch를 spatial mixed-potential solver에 넘긴다. branch 전류로 계산한 Faradaic 종 생성량을 endpoint에 적용한 뒤 질량작용·활동도와 finite-solid chemistry를 재해석한다. 오른쪽 knot 전류는 이 종/chemistry 갱신과 함께 bounded fixed point로 수렴시킨다.

## Nernst, conductivity, branch 매핑

각 `CreviceNernstBranchMap`은 branch별 표준전위 `E0[cell,knot]`와 수용액 무차원 활동도의 `ln(Q) = Σν_i ln(a_i)` 계수를 고정한다. 활동도는 하위 chemistry에서 계산한 `gamma_i c_i / c_standard`를 쓴다. 현재 반응 quotient convention은 `E_eq = E0 − RT/(nF) ln(Q)`이다. Standard-potential schedule 및 quotient 계수의 complete record digest와 Evidence를 요청에 포함한다.

전해질 전도도는 caller 배경 전도도와 종별 몰전도도 mapping으로 계산한다: `κ[cell,knot] = κ_background + Σ_i Λ_i[cell,knot] c_i[cell,knot]`, 여기서 `Λ`는 S·m²/mol, 농도는 mol/m³, 결과는 S/m이다. 적용성, 수용액 조성 영향과 온도 지원은 caller가 별도로 검토한다.

각 `CreviceFaradaicBranchMap`은 branch 반응 extent 1 mol에 대한 용존 종의 signed 화학양론 계수와 외부 reservoir 원소 변화를 선언한다. 전자수 `n`에 대해 전류를 `extent_rate = j A_reactive/(nF)`로 환산하고, 시간 양끝 branch 전류를 trapezoid 적분해 interval extent를 구한다. 반응별 용존 종 원소 변화와 external reservoir 원소 변화가 각 원소에서 상쇄되어야 하며, 전하 화학양론의 절댓값은 전자수와 일치해야 한다. 모델은 branch 방향을 선택하지 않으며 전류 부호와 caller 계수 부호가 정확히 맞아야 한다.

## 계산 순서와 closure

1. 시작 knot의 농도에서 기존 Davies/speciation/solid 연성 solver를 호출한다.
2. chemistry activity로 Nernst profile을 계산하고 caller conductivity 관계식으로 conductivity를 구성한다.
3. 기존 공간 Butler–Volmer/ohmic mixed-potential solver를 해당 exact knot만으로 실행한다. Geometry, cell order, kinetics record, conductivity record를 knot 입력 digest와 Evidence로 재결합한다.
4. interval에서는 기존 variable-area BDF Nernst–Planck/kinetic solver를 호출한다.
5. 왼쪽 혼합전위 branch current와 오른쪽 endpoint guessed current의 trapezoid extent를 용존 species에 반영한다. 이 Faradaic species source의 local net charge가 각 cell에서 0이어야 한다. 이어서 knot chemistry를 다시 계산하고 새 endpoint mixed potential을 구한다.
6. branch current 밀도 잔차와 aqueous/solid chemistry state 잔차가 모두 caller 허용치에 들면 해당 interval을 commit한다. Maximum endpoint iteration 또는 solver evaluation 예산 실패 시 이 interval 이후 결과를 내지 않는다.

수송 solver의 interval species ledger, local electroneutrality, zero-current residual을 이어받는다. 전체 원소 폐쇄는 aqueous+solid inventory와 mouth 유입, 수송 kinetic source, Faradaic external reservoir 변화를 합해 확인한다. Mixed-potential solver의 cell electrode-current residual도 caller tolerance를 통과해야 한다. 입력/결과 digests, Nernst/conductivity/Faradaic mapping record, knot/interval index, mixed-potential lineage, accepted interval prefix를 기록한다. negative species를 clipping하지 않는다.

## 중요한 물리 경계

기존 variable-area Nernst–Planck kernel은 모든 face에서 zero ionic current를 강제하지만, 기존 spatial ohmic mixed-potential solver는 일반적으로 비영 electrolyte face current를 계산한다. 이 두 방정식은 같은 state의 현재 구현에서 닫히지 않는다. 따라서 본 모듈은 mixed-potential 해의 face current가 caller current tolerance 이내로 0인 경우만 진행하고, 하나라도 비영이면 실패 처리한다. 따라서 spatial nonzero ohmic-current에 대응하는 electromigration coupling은 지원되지 않는다. 이를 0으로 강제해 source transport나 current를 조작하지 않는다.

Faradaic source는 interval 내부 BDF stage에 동시에 넣지 않고 endpoint trapezoid split으로 적용한다. Capacitive current, double-layer charge, 국소 금속 전도 손실, electrode film depletion, 금속 손실과 aperture 피드백은 모델링하지 않는다. Branch kinetics, equilibrium potential mapping, conductivity 및 external reservoir stoichiometry는 모두 caller-owned이고, 자동 chemistry/phase/반응 발견이나 qualification은 제공하지 않는다. 특히 비영 ohmic face-current 조건은 향후 Nernst–Planck flux 식에 mixed-potential face current를 직접 연결하는 별도 solver가 필요하다.

## 통합 상태

코어와 이 안내서는 독립 신규 파일이다. 중앙 registry, schema, catalog 또는 audit 연결은 별도 통합 단계에서 처리한다. 테스트와 패키징을 수행하지 않았다.
