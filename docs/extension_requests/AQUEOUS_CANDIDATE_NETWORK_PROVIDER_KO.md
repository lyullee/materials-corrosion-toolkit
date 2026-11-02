# 확장 요청: aqueous candidate network workflow provider 연결

## 구현된 core 경계

`integration.aqueous_candidate_network_workflow`는 사용자 제공 종·원소식·전하를 대상으로 제한된 반응 후보 균형 열거, 사용자가 Evidence로 선택한 방향/logK 바인딩, 단일상 mass-action 입력 조립을 순서대로 수행한다. 각 stage input/result digest를 보존한다. Workflow는 조립 artifact를 반환하고 평형 해를 계산하지 않는다.

## 외부 세션 요청

1. 공개 thermodynamic/provider 자료를 읽는 얇은 reader를 추가하고 각 logK record의 species reaction, 방향, 온도 구간, 표준상태, source record digest와 이용조건을 Evidence로 연결한다.
2. provider별 speciation solver consumer를 추가해 assembled system을 풀고, solver/version/configuration, convergence criteria와 balance residual을 `AssessmentResult`에 고정한다.
3. upstream computed activity history와 downstream Nernst, transport, precipitation/scale 및 corrosion 모델 사이에 clock·temperature·species·phase identity를 검증하는 adapters를 만든다.
4. 행렬이 과소결정/과잉결정이거나 solver가 수렴하지 않으면 해를 만들어내지 말고 실패 이유와 지원 범위를 반환한다.
5. 공개 데이터 사용조건과 third-party code license를 출처마다 따로 검토한다. 외부 PDF 문구/표/코드 복사는 포함하지 않는다.

## 검증 증거

최소한 잘 알려진 공개 aqueous benchmark를 source-rights를 확인해 재계산하고, 별도의 hand-calculated reaction/balance fixtures로 잔차와 elemental/charge balance를 검증한다. 이 요청서는 core에서 이 검증이 끝났다고 주장하지 않는다.
