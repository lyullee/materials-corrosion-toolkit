# 후속 세션 요청: WCO2 chemistry boundary model별 경로 catalog

현재 API `integration.electrochemical_chemistry_boundary_audit`는 caller가 모든 result field path와 species mapping을 지정하는 일반 감사기다. 후속 통합 세션은 실제 연결 대상 model pair별 어댑터를 추가해 path 오류를 줄일 수 있다.

현재 추가된 stage 계산 producer는 `integration.wet_co2_cylindrical_stage_speciation_scale_feedback`이다. 고정 caller 반응망의 component target을 각 BDF wall-composition stage에서 다시 구성하며, legacy fixed-activity v1, Evidence-bound Davies v2, SIT v3 및 B-dot v4 입력을 제공한다. Activity models는 상호 배타적이다. 후속 chemistry/risk 모듈은 정확한 schema version, stage activity provider/parameter digests, input/result lineage 및 `needs_data`/`out_of_scope` 상태를 보존해야 한다. 이는 자동 carbonate species·phase discovery, gas inventory, 침전 안정성 또는 corrosion-rate qualification을 대신하지 않는다.

각 pair adapter 작업:

1. upstream/downstream model ID와 정확한 schema version 기록
2. output/input field path를 schema 기반 상수로 정의하고 time, temperature, solvent, standard state, material condition, species IDs를 추출
3. upstream/downstream full result와 input digest, run context를 모두 pin
4. 종 rename/reaction mapping/exclusion 각각에 caller data record와 Evidence SHA 기록
5. 동일 clock/온도/상태뿐 아니라 pair가 요구하는 charge·element·inventory balance를 별도 계산 모델에서 검토하고 그 결과도 링크
6. representative chemistry result fixture가 준비될 때 only integration-level round-trip을 수행하고 raw/provider 권리와 calibration/holdout 구분 보존

공급자 실제 결과나 공개 dataset이 없으면 자동 species map, standard-state conversion, universal activity law 또는 물리 validation을 가정하지 않는다. 기존 공개 upstream 프로젝트 저장소를 수정했다고 보고하지 말고, 필요하면 별도 PR/확장 요청으로 제안한다.

후속 확장 포인트: `integration.aqueous_candidate_network_workflow`가 기존 stoichiometric candidate enumeration, manual Evidence-backed thermodynamic binding 및 mass-action assembly를 digest-pinned chain으로 묶는다. Provider-specific species/formula input parser나 source-record selector를 추가할 경우에도 selection/reaction direction/logK는 자동 inference 하지 말고 provider record + Evidence를 요구한다. Phase discovery, aqueous reaction feasibility and corrosion calibration remain separate provider/data work.
