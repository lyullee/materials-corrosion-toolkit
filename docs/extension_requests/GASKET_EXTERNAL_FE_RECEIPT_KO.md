# 후속 세션 확장 요청: 외부 FE receipt와 가스켓 접촉 응답 provider

이 문서는 다른 세션/저장소에서 구현할 수 있는 연동 명세입니다. 이 요청서 작성은 외부 solver 실행, provider 구현 또는 실물 결과 접수를 뜻하지 않습니다. 현 consumer는 caller가 제공한 계산결과와 source/config digest를 검증하는 경계입니다.

## A. 외부 flange compliance receipt

기존 consumer는 `ExternalFlangeComplianceBinding` 및 `reduce_external_flange_contact_compliance()`입니다. provider adapter는 다음 정보를 가진 receipt를 작성해야 합니다.

1. Solver 이름·revision, mesh와 좌표계, load case, 경계조건, 모델 설정 identity, 입력·원결과 digest.
2. flange contact reduction에 필요한 tangent stiffness matrix를 `incremental_stiffness_matrix`로 제공하고, 행렬 위치·DOF 단위가 N/m인지, component order와 원 배열 digest를 기록.
3. mesh node identity와 stiffness 행·열의 translational DOF ordering을 잇는 명시적 변환표와 그 SHA-256.
4. 고정 지지점, gasket contact node, normal translation component, closure sign을 별도로 명시.
5. receipt consumer에서 확인할 fixture 입력/결과와 최소 한 개의 reduced compliance 산출물.
6. 독립 추출 결과와 공개 가능한 작은 linear-elastic case 대조, load/reaction balance, reduced operator conditioning 보고.
7. 혼합 rotation/translation 단위, load-case 불일치, DOF 순서 변경, singular/unconstrained operator를 탐지하는 검토 기록.

상용 solver 결과 파일이나 제한된 입력자료는 공개 배포물에 넣지 않습니다. 코드와 result data의 재사용 권리는 각각 확인합니다.

## B. `GasketContactStateGridSweep` callback receipt

현재 `fabrication.gasket_contact_state_grid_sweep`는 다음 입력을 caller가 이미 검토했다는 전제로 외부 callback을 호출합니다.

- 계산 완료된 flange contact-history `AssessmentResult`와 그 전체 SHA-256 및 `input_digest`.
- `physical_scope_id`, 대상 `node_id`, source `RunContext`.
- source history 시간지지 구간의 처음·끝과 정확히 일치하는 엄격 증가 `probe_times_s`, caller 검토 `maximum_probe_gap_s`, 최대 callback 평가 수.
- solver provider ID, revision, configuration SHA-256.

이 API는 사용자가 고른 격자를 전수 완전 탐색이라고 간주하지 않습니다. caller maximum gap은 선택한 시간 분해능일 뿐, 전이 오차한계나 숨은 전이가 없다는 증명이 아닙니다.

### B-1. Query 필드

각 callback은 한 시각의 `ExternalContactStateGridQuery`를 받습니다. provider는 해당 query의 값과 digest가 정확히 일치하는 계산만 반환해야 합니다.

- `schema_version`
- `assessment_id`
- `source_contact_history_sha256`
- `physical_scope_id`
- `asset_id`, `location_id`, `time_basis`
- `context_sha256` — source `RunContext`의 canonical digest
- `node_id`, `query_time_s` — 요청한 정확한 시각
- `provider_id`, `provider_revision`, `provider_configuration_sha256`
- `query_sha256` — 위 query contract를 JSON으로 직렬화한 뒤 `query_sha256` 필드만 제외하고 계산한 canonical SHA-256

`maximum_probe_gap_s`, 전체 격자와 remaining evaluation count는 개별 query 필드가 아닙니다. caller가 전체 실행을 통제하며, provider가 격자 정보를 필요로 하면 provider configuration 또는 별도 실행 manifest에 그 입력 전체를 digest-bound로 기록해야 합니다.

### B-2. Response receipt 필드

각 query에는 다음 필드를 갖춘 `ExternalContactStateGridResponse` 한 건을 반환합니다.

- `schema_version`, 정확히 같은 `query_sha256`, `source_contact_history_sha256`
- 정확히 같은 `provider_id`, `provider_revision`, `provider_configuration_sha256`
- 정확히 같은 `physical_scope_id`, `asset_id`, `location_id`, `time_basis`, `context_sha256`
- 정확히 같은 `node_id`, `time_s == query_time_s`
- `contact_state`: `open` 또는 `closed`
- `evidence`: provider를 식별하는 행을 포함한 하나 이상의 `Evidence`; 최소한 한 행의 `source_id`는 요청 provider ID와 같아야 함
- `result_sha256` — response JSON에서 `result_sha256` 필드만 제외한 canonical payload의 SHA-256; Evidence를 포함한 응답 전체 계보를 결속

consumer는 source/query/context/node/time/provider identity, revision과 configuration digest, Evidence 출처, result digest가 모두 맞을 때만 sample을 채택합니다. 누락, 예외 또는 불일치가 있으면 그 전까지의 검증된 prefix와 첫 실패를 `needs_data`로 보존합니다. provider 출력이 source time grid나 원래 history와 다른 solver 설정에서 계산됐다면 기존 result의 일부인 것처럼 응답해서는 안 됩니다.

### B-3. 산출물 의미

모든 응답이 확인되면 consumer는 호출된 grid 순서의 상태표와, 인접 probe 시각 사이에서 `open`/`closed`가 바뀐 bracket을 반환합니다. sample 중복·누락을 허용하지 않습니다. 각 bracket에는 lower/upper 시각과 양 endpoint query digest를 남깁니다.

- 동일 상태 endpoint 사이의 숨은 전이를 배제하지 않습니다.
- 여러 상태 변화가 관측되면 모두 bracket으로 보고하지만, 미관측 변화가 없다고 증명하지 않습니다.
- bracket 내부를 보간하지 않고 `event_time_s`는 계산하지 않습니다.
- 이 callback은 FE solver를 포함하지 않으며 contact state만 요청합니다. local stress, leakage, seal performance, acceptance, failure probability, code compliance를 산출하지 않습니다.

한 개 bracket의 시간을 좁히는 별도 consumer `fabrication.gasket_contact_transition_refinement`는 caller가 단일 단조 전이 가정을 검토한 경우에만 midpoint solver callback을 반복합니다. grid sweep과 그 refinement API는 다른 질의/응답 schema를 사용합니다. 어느 API도 수학적으로 정확한 사건 시각을 보증하지 않습니다.

## C. Provider가 제출해야 할 기술 work product

Grid receipt만으로는 FE 모델이나 응답의 유효성을 보증할 수 없습니다. 아래 자료를 함께 제공해야 합니다.

### C-1. FE 해석과 local stress

- 모델 범위, 형상/mesh revision, 재료·접촉·bolt·gasket constitutive input, 조립 및 하중 시퀀스, 지지·경계조건과 solver settings.
- mesh convergence, nonlinear contact convergence, load/reaction balance, 접촉 보완조건 및 잔차의 수치 진단.
- local stress 결과의 node/element/region identity, tensor component order, 단위, coordinate frame, 위치(적분점/절점/평균/외삽), stress recovery 및 부호·선형화 기준.
- 원 입력·결과의 해시와 각 파생 결과의 config/result digest. 결과 파일을 공개할 수 없다면 비공개 원자료의 digest, 공개 가능한 파생 receipt와 사용 권한 경계를 제공.

소프트웨어는 이 결과를 자동으로 생성하지 않습니다. provider가 결과를 보유하지 않았으면 `missing`으로 보고하고 값을 채워 넣지 않습니다.

### C-2. 시간 보간·전이 root 정확도

- 실제 solver 평가 시각, 출력 격자, state 판정 기준, 중간 시각 질의가 동일한 모델 설정과 하중 경로를 유지한다는 설명.
- 시간 격자 세분화에 따른 상태 변화와 contact-force/gap 잔차의 비교, solver tolerance, 최대 간격, 평가 예산 및 종료 기준.
- 단일 전이 가정이 적용되는 각 interval의 근거. 복수·재진입 전이가 가능한 영역이면 추가 solver sampling으로 분리하거나 불확실 bracket을 보고.
- root refinement를 수행하면 bracket 양 끝, endpoint state, 폭, 반복/evaluation 수, 수렴 잔차와 더 엄격한 시간 tolerance에서의 안정성 비교를 보존.
- 시간 tolerance는 수치 bracket 폭 기준으로 명시합니다. root의 수학적 exactness나 모델의 실제 물리시간 정확도를 주장하지 않습니다.

provider가 숨은 전이를 배제할 근거가 없으면 해당 응답은 유한 grid 관측으로만 표기하고 completeness를 `unknown`으로 둡니다. 표본 사이의 상태를 임의 선형 보간해 이벤트를 만들지 않습니다.

### C-3. 재료 및 seal 기준

- 기준 문서/출처, revision·절·표 식별자, 사용 권한 및 Evidence.
- 적용 재료·gasket type, geometry, 온도, 유체, 차압, 조립 상태와 허용 적용범위.
- 실링 합격 조건과 decision logic은 사용권과 적용성 검토가 완료된 권한 있는 provider 자료로 제출합니다. 표준/상용 기준값을 이 코드에 복사하거나 이름만 보고 추정하지 않습니다.
- 기준이 없거나 적용범위가 불명확하면 `not supplied`/`not qualified`로 기록하고, 코드가 acceptance를 임의 산출하지 않게 합니다.

## D. 공개·연동 범위

공개 코드에는 외부 solver protocol, 공개 가능한 합성 fixture, receipt schema와 digest 검증 예시만 둡니다. 상용 결과 파일, 제한자료, 승인표 또는 제3자 point data는 사용 권한이 별도로 확인되지 않는 한 저장소에 포함하지 않습니다. 실제 provider 구현·FE solve·criteria qualification이 완료되기 전에는 adapter receipt를 물리 검증이나 설계 승인으로 표현하지 않습니다.
