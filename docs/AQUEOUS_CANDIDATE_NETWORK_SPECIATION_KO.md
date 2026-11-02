# Aqueous candidate workflow to speciation adapter

`integration.aqueous_candidate_network_speciation` receives a computed `AssessmentResult` from `integration.aqueous_candidate_network_workflow` and the canonical SHA-256 of that complete result. It verifies model identity, computed status, workflow input/context digest, full result digest, the computed assembly stage, and the mass-action system digest. When invoked through `ModelRegistry`, its `RunContext` must match the workflow's asset, location and time basis.

The adapter calls the established `aqueous_mass_action_speciation()` calculator with exactly the assembled `AqueousMassActionSystem`; it does not rebuild equations or modify activities, temperature, coefficients or standard state. The result retains workflow, enumeration, binding, assembly, system and speciation digests plus the upstream context through the registry result. A downstream chemistry-boundary audit can use this result with caller-declared paths and state mapping.

## Scope limits

The solver uses the upstream fixed activity coefficients, selected reaction direction/equilibrium constants, constraints, initial activities, tolerances and phase assumptions. This composition does not discover missing species/reactions, choose phases, assign thermodynamic constants, add gas/solid/precipitation phases, derive kinetics, estimate corrosion, or qualify a material. `needs_data` and `out_of_scope` from the existing solver are preserved.

Numerical correctness, benchmark comparison and provider calibration remain unverified here. No tests or numerical examples were executed for this adapter.

Workflow 단계 상태: enumeration/binding이 computed가 아니면 그 status를 유지하고 후속 단계를 실행하지 않는다. completed_stages, stopped_stage, unexecuted_stages 및 failed_stage_result_sha256를 확인한다. 모든 입력 단계 해시는 남기지만 미실행 단계의 result와 result digest는 null이다. 입력 해시 존재는 해당 단계 실행을 뜻하지 않는다. Assembly까지 실행했어도 미완료이면 stopped_stage는 assembly이고 completed_stages에는 앞의 두 단계만 남는다. 정상 조립도 speciation 계산 완료나 실험 qualification을 뜻하지 않는다.

Speciation handoff는 workflow 원 입력을 strict JSON 계약으로 다시 읽고 workflow ID/configuration digest와 enumeration/binding/assembly 각각의 computed 상태·입력 해시·결과 해시를 대조한다. 바깥 AssessmentResult 해시를 새로 계산한 것만으로 내부 단계 불일치를 허용하지 않는다. 이 계보 검사는 결과의 계산 재현이나 물리 qualification을 대체하지 않는다.

후보 열거는 signature bucket의 ordered-pair 수를 단조 누적하여 budget 초과가 확정되면 조기에 중단한다. 이때 required_candidate_pair_checks_lower_bound는 필요한 연산 수의 하한이며 전체 개수가 아니다. side_enumeration_complete=false를 확인하며 부분 후보를 후속 binding에 사용하지 않는다. 정상 결과의 side_enumeration_complete=true는 선언된 유한 stoichiometric 검색 완료만 뜻한다.

候補比較は同一 signature 内の非同一 unordered pairを一度だけ評価する。方向正規化・primitive係数・最終sortを維持し、逆方向重複と必ず棄却されるself-pairを省略する。既存candidate_pair_checksは互換性のためordered/self込みの予算基準を維持し、実際の比較数をevaluated_unordered_pair_checksに分けて記録する。性能向上幅と候補一致は未検証。
