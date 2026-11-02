# Crevice cell별 mass-action speciation projection

integration.crevice_local_mass_action_projection은 digest-bound transport composition 결과의 exact knot/cell마다 caller가 제공한 고정 활동도 단일 액상 mass-action 시스템을 실행한다. 기존 local speciation ledger가 계산된 입력/결과를 조립하던 것과 달리, 이 API는 cell 상태에서 linear constraint target을 만들고 solver를 호출한다.

## 계산

Transport 요약의 종 농도는 mol/m3이다. 종 ID와 순서는 cell template mass-action species와 정확히 같아야 한다. 각 선형 constraint j의 target은 caller가 선언한 계수로 다음과 같이 만든다.

target_j [mol/L] = sum_i coefficient_(j,i) * concentration_i [mol/m3] / 1000

요청의 composition_derived_constraint_ids로 선택된 target만 transport 조성에서 다시 계산한다. 다른 constraint target, template의 계수, 반응 network, 평형상수, 활동도계수, 온도, 표준상태, 상 개수, solver 제한은 유지한다. Constraint 의미 외의 화학 입력을 추정하지 않는다. Solver가 실패하면 현재 knot를 커밋하지 않고 앞서 완전히 계산된 exact-knot prefix만 반환한다.

## 호출 흐름

1. Crevice geometry/transport campaign을 계산한다.
2. CreviceTransportCompositionBridge로 exact knot별 cell volume/concentration summary를 만든다.
3. 각 summary knot의 시간과 geometry side에 맞춰 모든 cell의 CreviceMassActionProjectionCell을 준비한다.
4. cell마다 transport_cell_context_digest(summary, cell_index)와 caller-reviewed AqueousMassActionSystem을 제공한다. 각 시스템은 transported species 집합/순서와 일치하고 해당 local equilibrium에 맞는 독립 component constraints를 선언해야 한다.
5. 입력 변환 및 화학 applicability review가 끝난 요청만 registry에서 계산한다.

요청은 CreviceLocalMassActionProjectionRequest, CreviceMassActionProjectionKnot, CreviceMassActionProjectionCell로 구성한다. Request는 기존 campaign, binding result, result SHA-256, exact knot/cell template, composition_derived_constraint_ids, review flag를 요구한다. 선택한 constraint는 모든 cell/knot template에 같은 ID와 같은 term basis로 있어야 한다. 최대 10,000개의 local solve를 허용한다. 자세한 타입은 공개 JSON schema에서 확인한다.

## 출력과 범위

출력은 기존 integration.crevice_local_speciation_volume_ledger의 species per-cell inventory, charge-equivalent diagnostic, 가능한 elemental inventory와 mass-action input/result digest를 포함한다. 한 knot는 모든 cell 계산이 성공한 경우에만 커밋한다.

이 모델은 exact-knot의 독립 local equilibrium projection이다. 결과를 이후 transport interval에 되먹임하지 않으며 시간 사이 반응 속도·전달·전기화학을 풀지 않는다. 활동도 provider는 template의 고정 계수로 제한된다. 자동 종/반응망 생성, 고체상 선택·침전·용해, wall law, 감육, corrosion rate, 수명·확률·qualification은 추론하지 않는다. Component constraint basis의 화학적 의미와 complete species inventory는 caller 검토 사항이다.

## 구현 근거와 검증

Target 구성은 단위 변환과 caller 선형 constraint 계수 적용이다. 질량작용 수치 해석은 프로젝트 내 AqueousMassActionSystem solver를 사용하며 외부 thermodynamic table을 포함하지 않는다. Digest는 transport cell 상태와 각 solver input/result 계보를 묶는다.

이번 증분에서 코드와 schema를 추가했다. 수치 및 실험 검증은 별도 후속 단계다. 정적 AST/scope 감사는 파일·catalog 연결만 확인하며 solver 수렴성이나 화학적 타당성을 증명하지 않는다.
