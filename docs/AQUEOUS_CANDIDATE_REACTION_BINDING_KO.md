# 수용액 균형 후보와 평형 반응 계약 연결

`bind_aqueous_candidate_reactions()`는 `chemistry.aqueous_reaction_candidate_enumeration`의 계산 결과 중 caller가 직접 선택한 균형 후보를 `AqueousEquilibriumReaction` 형식으로 변환하는 Python API다. 후보 결과, 후보 ID와 전체 SHA-256을 대조하므로 배열 순번이 아니라 digest lineage로 입력 후보를 고정한다.

각 선택에는 고유 reaction ID, forward/reverse 방향, 온도, `log10(K)` 및 parameter set/record 식별자를 지정한다. 요청에는 downstream mass-action system의 목표 온도와 molarity 표준상태도 선언하며, 모든 선택 온도가 허용차 안에서 일치해야 한다. Evidence에는 parameter set ID와 동일한 `source_id`, 해당 record와 일치하는 SHA-256을 넣는다. 역방향을 선택한 경우에만 생성물·반응물 부호와 `log10(K)` 부호를 뒤집는다.

## 처리 순서

1. 후보 계산 결과가 `computed`인지, 열거 입력 digest가 요청과 일치하는지 확인한다.
2. 각 후보 payload의 SHA-256과 digest 기반 ID를 재계산해 요청에 지정된 후보와 일치하는지 확인한다.
3. 사용자의 반응 선택 및 평형상수 검토 확인을 요구한다. 검토 확인이 없으면 `needs_data`와 빈 반응 목록을 반환한다.
4. `reactions`에는 `AqueousEquilibriumReaction`에 바로 맞는 필드만 반환하고, 후보/parameter provenance는 별도 `reaction_lineage`에 둔다. 계보에는 원 상수와 적용 부호, 생성 반응 payload digest가 포함된다. 부호 관례는 생성물 양수·반응물 음수이며 반응 방향별 `log10(K)`를 적용한다.

## 사용 예

```python
from matintegrity.contracts import Evidence
from matintegrity.models.aqueous_mass_action import (
    AqueousCandidateReactionBindingRequest,
    AqueousCandidateReactionSelection,
    bind_aqueous_candidate_reactions,
)

# candidate_result는 앞 단계 enumerate_aqueous_reaction_candidates()의 결과다.
candidate = candidate_result.values["candidate_reactions"][0]
record_sha = "a" * 64  # 합성 예제용; 실제 parameter record의 SHA를 입력해야 한다.
request = AqueousCandidateReactionBindingRequest(
    binding_id="example-binding",
    candidate_enumeration_input_sha256=candidate_result.values["input_sha256"],
    target_mass_action_temperature_K=298.15,
    target_activity_standard_state="molarity_1_mol_L",
    selections=(AqueousCandidateReactionSelection(
        candidate_id=candidate["candidate_id"],
        candidate_sha256=candidate["candidate_sha256"],
        reaction_id="caller-reviewed-reaction-1",
        direction="candidate_forward",
        log10_equilibrium_constant=-14.0,
        temperature_K=298.15,
        equilibrium_parameter_set_id="synthetic-equilibrium-record",
        equilibrium_record_id="record-1",
        equilibrium_record_sha256=record_sha,
    ),),
    reaction_selection_and_constant_reviewed=True,
    evidence=(Evidence(
        source_id="synthetic-equilibrium-record",
        origin="synthetic",
        citation="합성 예제의 요청 계약을 보이기 위한 가상 자료 식별자",
        sha256=record_sha,
    ),),
)
bound = bind_aqueous_candidate_reactions(candidate_result, request)
```

## 적용 한계

이 API는 후보 반응이 실제 화학적으로 가능하다고 판정하지 않는다. 반응 방향·평형상수·온도 적용성은 caller가 선택하고 근거를 제공해야 한다. 결과의 `reactions` 배열은 `AqueousEquilibriumReaction` 계약 형식이고, `reaction_lineage`는 반응별 자료 계보다. 요청의 목표 온도와 표준상태는 mass-action 입력과 반드시 같아야 한다. 산화환원 전자수지, 용매/기체/고체상 생성, 반응 메커니즘, kinetics 또는 부식 속도는 추론하지 않는다. 실행 시험과 parameter-based 검증은 별도 검증 계획에서 수행한다.

요청 계약 스키마: [`AqueousCandidateReactionBindingRequest`](schemas/AqueousCandidateReactionBindingRequest.json), [`AqueousCandidateReactionSelection`](schemas/AqueousCandidateReactionSelection.json).

바인딩 결과를 solver 입력으로 조립할 때는 `AqueousMassActionSystemAssemblyRequest`와 `assemble_aqueous_mass_action_system()`을 사용한다. 이 요청은 반응 외 species/constraints, activity provider, 평형 provider configuration, solver 제한, review flags 및 Evidence를 보유한다. 조립기는 대상 온도와 표준상태를 다시 대조하고 bound reactions를 `AqueousEquilibriumReaction`으로 파싱한다. 각 반응의 payload SHA, 방향별 상수 부호, 후보 계산 결과 digest와 parameter Evidence도 재확인한다. 완성된 `mass_action_system` 사전은 registry에 전달 가능한 입력 모양이며, `equilibrium_record_digest`는 반응 lineage 목록의 canonical SHA-256이다. 별도 `reaction_lineage`도 결과와 함께 보관한다.

조립 요청 스키마: [`AqueousMassActionSystemAssemblyRequest`](schemas/AqueousMassActionSystemAssemblyRequest.json). 합성 전체 경로는 [`aqueous_candidate_mass_action_pipeline.py`](../examples/aqueous_candidate_mass_action_pipeline.py)에 있다. 이 연결은 solver를 실행하거나 convergence를 보증하지 않는다.
