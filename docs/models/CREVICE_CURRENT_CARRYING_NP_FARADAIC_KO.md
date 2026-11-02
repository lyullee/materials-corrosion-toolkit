# 전류 전달형 크리비스 Nernst–Planck/Faradaic 연성

## 목적과 범위

`integration.crevice_current_carrying_np_faradaic`는 셀별 활동도 기반 반응수송, 가변 단면적, 전해질 전위, 혼합전위 Butler–Volmer 가지, 수용액 평형 및 유한 고체 inventory를 연성하는 계산 코어다. 반응식, 종 조성·전하·확산계수·활동도, Faradaic 가지와 외부 원소 저장고, 전도도 매핑, 형상 이력 및 사용 적합성 판단은 호출자가 제공한다. 자동 반응·상 발견이나 재료 적격성 판정은 하지 않는다.

## 전류의 두 경로

전해질 내부 면의 이온 전류와 금속/용액 계면의 Faradaic 벽 전류는 서로 다른 ledger다.

- 내부 면의 이온 전류는 종 플럭스에서 계산한다: `I_face = F A_face Σ_i z_i J_i`.
- 각 내부 면의 migration 항은 셀 전위차를 사용한다: `J_i = -D_i[∇c_i + c_i∇ln(γ_i) + z_i c_i(F/RT)∇φ] + u c_i,upwind`.
- 전극 벽 전류는 혼합전위 해의 가지 전류밀도와 반응면적에서 얻는다. 이것은 면 플럭스로 더하지 않고, `extent = j A_reactive Δt/(nF)`로 각 셀의 수용액 종 source에 반영한다.
- 혼합전위 해가 각 셀에서 요구하는 `I_right - I_left = I_wall` 관계와 이온 inventory/charge balance가 동시에 맞아야 한다. 단순히 전류값을 NP 플럭스에 덮어씌우지 않고, 구성식에서 계산한 `FΣzJ A`가 목표 전류와 일치하지 않으면 실패한다.

## 공간·전기 경계

셀 0 전위를 각 절점의 기준으로 고정한다(`φ[0]=0 V`). 절점 사이에서 전위와 면전류를 선형 보간해 BDF 내부 계산에 사용한다. 입구와 막힌 끝은 모두 전기적으로 절연된 조건으로 둔다. 입구의 이온 이동전위 기울기는 전체 종 플럭스가 지정 경계에서 무전류가 되도록 계산하며, 막힌 끝의 종 플럭스는 0이다. 외부 전극 전류를 경계로 흘려보내는 모델은 지원하지 않는다.

혼합전위 입력의 셀 순서·길이·시간·온도·초기 개구 면적이 chemistry/transport와 일치해야 한다. 요청에는 전류 부호, 면적 매핑, 전위 게이지, 전하 저장 생략 및 적용 범위 검토 확인이 포함되어야 한다.

## 계산 순서

1. 첫 절점에서 호출자 화학으로 수용액/고체 상태와 활동도계수를 계산한다.
2. 그 조성·전도도에서 셀별 혼합전위와 내부 면전류를 계산한다.
3. 각 시간 구간에서 가변 셀 부피와 면적 이력을 사용해 종 몰수를 보존하는 BDF 수송을 적분한다. 활동도계수와 온도 등 knot 자료는 구간 내 선형/고정 보간 규약을 따른다.
4. 기본 `endpoint_trapezoid` 모드는 기존대로 구간 후단에 Faradaic source를 적용한다. 선택형 `bdf_stage_linear_current`는 구간 양 끝 혼합전위 가지전류를 시간 선형 보간해 BDF 내부 stage에서 종 source와 extent를 적분한다. 더 강한 선택형 `bdf_stage_spatial_mixed_potential`은 각 BDF RHS 평가에서 현재 농도와 보간 활동도계수로 Nernst 평형전위를 다시 계산하고, 해당 조성의 이온 몰전도도와 보간 개구를 사용해 공간 Ohmic/Butler–Volmer 문제를 다시 푼다. 그 stage 가지전류로 source와 extent를 함께 적분하며, 외부 원소 reservoir 변화도 같은 extent를 사용한다.
5. 끝 절점의 수용액·고체 화학을 다시 풀고, 혼합전위와 transport endpoint를 반복해 전위·가지전류·면전류·화학 조성이 수렴할 때만 해당 구간을 커밋한다.
6. 종 몰수, 전류, 원소 total(수용액+고체+외부 reservoir)을 점검한다. 어느 budget이든 초과하거나 closure가 실패하면 완료 상태를 내지 않고 이미 승인된 구간 prefix와 실패 반복 진단을 반환한다.

기존 요청과의 호환성을 위해 기본 적분 모드는 `endpoint_trapezoid`다. 선형 stage 방식은 `faradaic_source_integration_mode="bdf_stage_linear_current"`와 `bdf_stage_linear_current_source_reviewed=True`를 함께 지정한다. 공간 재해결 방식은 `faradaic_source_integration_mode="bdf_stage_spatial_mixed_potential"`, 두 review 플래그(`bdf_stage_linear_current_source_reviewed`, `bdf_stage_spatial_mixed_potential_reviewed`) 모두 참이어야 한다. 각 구간 stage 비선형 반복은 `maximum_total_mixed_potential_function_evaluations` 공통 budget에서 차감된다. 새 입력 해시는 모드 선택을 포함한다.

공간 재해결 모드에는 별도의 선택형 B-dot 활동도계수 갱신을 붙일 수 있다. `bdf_stage_bdot_activity_by_interval`에는 시간 구간마다 `AqueousBdotIteration` 요청 하나를 지정하고 `bdf_stage_bdot_activity_reviewed=True`를 설정한다. 요청의 종 순서와 전하는 수송 종과 같아야 하며 각 구간 온도는 시스템 및 B-dot 매개변수 온도와 정확히 같아야 한다. 기존 B-dot transport adapter의 물 질량 환산, molarity/molality 표준상태, 매개변수 적용범위, 단일 액상 범위, 증거 및 SHA 검사를 통과해야 한다. `maximum_total_bdot_stage_activity_evaluations`는 해당 coefficient callback의 독립 총 호출 상한이며 각 BDF RHS에서 한 번씩 차감된다.

이 콜백은 BDF trial mouth/cell 조성에서 이온강도와 B-dot 계수를 직접 계산할 뿐, 질량작용 평형·종분화·전하중성 반복 또는 고체상 평형을 풀지 않는다. 계산된 계수는 같은 stage의 NP 활동도 구배, 균질 반응 활동도, 공간 혼합전위의 Nernst/BV 입력에 일관되게 사용된다. 정확 절점의 Davies 화학/고체평형과 그 절점 혼합전위는 기존 경로를 유지한다. 따라서 이 선택 옵션은 stage 내부 계수 갱신이며 전체 시간 구간의 단일 평형 모델을 뜻하지 않는다. interval별 계수 요청 digest와 전체 호출 횟수를 결과에 기록한다.

## 수지와 실패 기준

수용액 종의 구간 수지는 가변 부피에서 `n_end - n_start = mouth transfer + homogeneous kinetic source + Faradaic wall source`로 확인한다. 원소 수지는 수용액과 고체 inventory에 mouth/kinetic 전달 및 호출자 외부 reservoir 변화를 반영한다. 셀별 전류 폐합은 mixed-potential branch wall source와 내부 면전류 발산의 관계로 확인한다. 입력 digests, 구간 transport digest, knot chemistry/mixed-potential 결과 digest 및 반복 prefix를 계산 기록에 보존한다.

NP 확산·이동도에서 계산한 이온 전류와 호출자 전도도 모델의 Ohmic 전류가 맞지 않으면 계산은 중단한다. 특히 molar conductivity와 확산계수/활동도 모델이 서로 독립적으로 주어져 호환되지 않을 수 있다. 입력 화학 반응의 전하·원소 보존, 가지 전류 부호와 Faradaic 종량론이 맞지 않는 경우에도 사용할 수 없다.

## 모델 한계

- 이중층 용량, 전하 축적, 전자 전도체 내부 전압강하, 국소 반응기구 발견 및 절점 사이 화학 평형은 포함하지 않는다.
- 기본 모드는 endpoint trapezoid operator split을 보존한다. `bdf_stage_linear_current`는 endpoint 가지전류를 선형 보간한다. `bdf_stage_spatial_mixed_potential`은 각 BDF RHS 평가에서 공간 Ohmic/BV 방정식을 재해결한다. 두 stage 모드 모두 caller review를 요구하며 비선형 방식은 상당히 더 많은 계산량을 쓸 수 있다.
- `bdf_stage_spatial_mixed_potential`의 구간 조성은 BDF trial state이고, 활동도계수·온도·표준전위·배경전도도·molar conductivity 계수·기하학은 양 끝 knot의 호출자 자료를 시간 선형 보간한다. 자동 화학평형/상 발견은 하지 않는다. 입력 Nernst maps, conductivity law 및 BV branch parameters는 caller supplied이며 이들 사이의 물리적 적합성은 호출자가 검토해야 한다.
- 선택형 `bdf_stage_bdot_activity_by_interval`은 위의 knot-선형 활동도계수 보간을 해당 구간에서 대체한다. B-dot는 caller 제공 단일 액상 매개변수의 직접 계수식 평가이며, exact-knot Davies 고체화학과 stage B-dot 사이의 모델 차이를 사용자가 검토해야 한다. 온도 변화 구간, 종/전하 매핑 불일치, ionic-strength 지원영역 초과, evidence/standard-state 검토 누락, callback budget 초과 시 계산을 거부한다.
- 선형 stage 모드의 전위/전류와 두 endpoint 혼합전위 사이 차이는 미해결이다. 공간 재해결 모드도 준정상 전기화학만 계산하며 이중층 용량, 전하 축적, 전극/고체 내부 전압강하, kinetics calibration, 독립 검증 또는 재료 건전성 판정을 포함하지 않는다.
- Caller equilibrium chemistry/solid inventory는 exact knot에서 갱신된다. 새 공간 재해결 모드는 해당 stage 조성에서 Nernst 전위를 계산하지만 intrastage speciation/phase equilibrium은 포함하지 않는다.
- 내부 면전류와 migration 플럭스의 구성식 일치를 강제하므로, 임의의 mixed-potential current를 통과시키는 보정기가 아니다.
- 결과는 가정 의존 계산 스크리닝이며, 검증·확증 또는 재료 건전성 수용 판단이 아니다.

## API와 식별자

- 요청 모델: `CreviceCurrentCarryingNernstPlanckRequest`
- 평가 함수: `solve_crevice_current_carrying_np_faradaic`
- Model ID 후보: `integration.crevice_current_carrying_np_faradaic`
- 계약 ID: `matintegrity.crevice_current_carrying_np_faradaic.v1`

모델은 `integration.crevice_current_carrying_np_faradaic` ID로 중앙 registry/API/schema/capability/source catalog에 등록되어 있다. `matintegrity.crevice_current_carrying_np_faradaic.v1` 입력 계약을 사용하며, 이 가이드는 구현된 기본 및 review-gated 선택 모드의 범위를 설명한다. 전류 폐합을 제공하는 관련 `crevice_faradaic_spatial_chemistry_coupling`과는 별개의 transport-integrated 구현이다.
