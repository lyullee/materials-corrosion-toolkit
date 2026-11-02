# 수용액 화학·speciation·transport 결과 경계 audit

`integration.electrochemical_chemistry_boundary_audit`는 이미 계산된 여러 `AssessmentResult`를 순서대로 받아, chemistry/speciation/transport handoff에서 상태 identity와 species disposition이 사라지지 않았는지 검사하는 provider-neutral lineage API다. 새 평형이나 activity coefficient를 계산하지 않으며, 입력 데이터를 자동으로 화학적으로 해석하지 않는다.

## 단계별 field path 선언

각 `ChemistryBoundaryStage`는 허용 model ID, 전체 result와 SHA-256, 입력 digest, 그리고 다음 값을 실제 AssessmentResult JSON에서 읽을 경로로 선언한다.

- zero-based ordered `elapsed_time_s` knot vector와 같은 길이의 `temperature_K`
- material condition, solvent 및 activity standard-state 식별자
- 단계가 출력한 ordered species ID 목록
- 후속 단계가 소비하는 species ID 목록(선택 단계에서는 생략 가능)

Field path는 JSON object key 이름으로 구성한다. 배열을 지나가야 할 때 `"*"` token을 사용한다. 예를 들어 `("values", "history", "*", "time_s")`는 각 history row의 `time_s`를 읽는다. 경로는 실행 가능한 식이 아니며, 존재하지 않는 키나 배열이 아닌 곳의 wildcard는 실패한다. 공급자별 출력 구조가 달라 어떤 경로를 선택할지는 caller가 해당 schema와 result를 검토해 선언한다.

Audit는 각 upstream `AssessmentResult`의 input digest를 `model_id`, model version, inputs 및 context에서 재계산하고 전체 result SHA와 비교한다. 모든 stage가 같은 asset/location/time basis, 정확히 같은 time knots와 온도, material condition, solvent 및 standard state를 사용해야 한다. 변경이 필요한 solvent/standard state 변환은 이 audit가 처리하지 않으며 변환된 upstream 계산 결과를 별도 stage로 넣어야 한다.

## Species handoff

인접 stage마다 각 upstream output species를 하나씩 `SpeciesHandoff`로 처리한다. 이름만 바뀐 경우는 `renamed`, 반응/모델 변환을 거친 경우는 `reaction_transformed`, carry되지 않는 종은 근거와 검토를 포함해 `intentionally_excluded`로 선언한다. 모든 target identity는 unique해야 하고, downstream consumed species는 앞 stage에서 매핑되어야 한다. Mapping record SHA를 `Evidence`에 연결한다.

이는 traceability와 누락 표시다. 반응량론, 원소·전하 보존, aqueous charge balance, 질량 보존, 평형 또는 transfer law를 검증하는 것은 아니다. 변환의 과학적 정당성은 해당 chemistry/transport 모델과 별도 계산·자료에서 입증해야 한다.

결과는 각 stage의 source/result/input/context digest, 선택한 field paths, 정규화 상태값과 각 handoff mapping, aggregate `chain_sha256`를 보존한다. 불일치가 있으면 요청 검증 단계에서 거절되고, 계산 결과로 승격되지 않는다.

## 현재 한계

이 audit는 출력 field path를 caller가 제공해야 하며 자동 model-output schema discovery를 하지 않는다. time/temperature의 완전 일치를 요구하고 보간·단위변환·standard-state 변환을 하지 않는다. 따라서 code wiring은 데이터 경계 감사를 지원하지만 일반적인 WCO2 reaction network discovery, activity law, chemistry-transport 동시 연성 또는 qualified corrosion prediction을 완성하지 않는다.
