# Sandia HELPR 연동 요청

## 목적

HELPR의 수소 혼합가스 배관 균열성장·파괴평가 결과를 MatIntegrity의 재료·부위·하중·근거
계약과 연결한다. HELPR는 별도 환경에서 실행하며 MatIntegrity는 HELPR 계산식, 설계곡선,
규격 표 또는 계수를 복제하지 않는다. 검토 기준은 공식 `v2.1.0`, commit
`ae12d20b6608123af41dd9d5f70db6b6547fece5`다.

## 현재 가능한 경계

HELPR `CrackEvolutionAnalysis.save_results`가 생성하는
`nominal_life_criteria.csv`와 `probabilistic_life_criteria.csv`를
`read_helpr_life_criteria_csv`로 읽는다. 지원하는 열은 다음 다섯 개로 제한한다.

- `a(crit)`
- `Cycles to a(crit)`
- `Cycles to 25% a(crit)`
- `Cycles to 1/2 Nc`
- `Cycles to FAD line`

CSV에는 실행 리비전·설정 digest·자산·부위·재료·하중 case·물리 표본 ID가 없으므로 호출자가
이 값을 별도로 검토해 제공한다. 열 이름이 달라진 공급자 버전은 추정해서 읽지 않는다.
빈 값과 NaN은 0, runout 또는 무한수명으로 바꾸지 않고 `None`으로 보존한다. 각 값은 HELPR
모델 기준 도달값이며 관측 파단, 규격 합격, 잔여수명 보증 또는 고장확률이 아니다.
호출자는 공급자 실행에서 나온 모든 경고를 검토한 안정적인 코드로 전달하고 `a(crit)`의
실행별 의미를 명시한다. 대표 실행에서는 파괴저항에 도달하지 않아 공급자가 `a/t=0.8`을
사용했으므로 해당 값을 파괴저항 교차 깊이라고 해석하지 않는다.

## HELPR 측에 권장하는 추가 export

향후 상대 저장소 또는 별도 wrapper에서 다음 manifest를 CSV와 함께 내보내면 수동 입력을 줄일
수 있다.

- HELPR 버전, Git commit, Python·의존성 버전
- 분석 ID, 무작위 seed, deterministic/aleatory/epistemic 표본 정의
- 입력·설정의 canonical digest와 사용한 crack-growth, SIF, FAD, residual-stress 방법 ID
- 자산·부위·재료 상태·하중 case·표본 ID
- 압력의 절대/게이지/차압 기준, 온도·길이·응력·cycle 단위
- 각 종료 기준의 정의와 값이 비어 있는 원인
- 구조화된 경고 코드와 경고가 영향을 주는 결과 필드
- 원 결과 파일별 SHA-256

기존 CSV만 사용할 때는 MatIntegrity 계약에 이 정보를 명시적으로 공급한다. 서로 다른 HELPR
버전의 열이나 의미를 한 분석으로 합치지 않는다.

## 외부 피로균열성장 curve 공급 확장 요청

상대 모듈이 사용자 supplied da/dN–ΔK curve를 지원할 경우, 수치 배열만 받지 말고 다음 manifest를
함께 내보내거나 입력 digest에 포함해야 한다.

- 원 자료·파일·sheet·series ID와 content SHA-256
- 재료 heat/condition, product form, orientation과 물리 시편 ID 또는 명시적 미제공 상태
- 기체 조성, 압력의 absolute/gauge 및 partial/total 기준, 온도, R, 주파수와 K-gradient
- ΔK·da/dN 단위, closure/threshold 처리, interpolation·extrapolation·종료 정책
- curve별 calibration/holdout·유효성·불확실성과 공급자 판본
- 원자료 충돌 목록과 각 충돌에 대한 승인 ID

현재 HyMatBase 4130X 자료는 record 4.5 MPa와 workbook 45 MPa가 충돌하고 물리 시편 ID가 없어 이
경로의 인수 자료가 아니다. 상대 모듈은 이런 curve를 자동 보정값이나 기본값으로 선택해서는 안 된다.
MatIntegrity는 해결된 curve manifest만 전달하고, HELPR 결과 수신 시 사용된 curve digest를 다시
대조한다. 이 확장은 규격 curve나 HELPR 내부 구현을 MatIntegrity로 복제하라는 요청이 아니다.

## 인수 시험

1. 고정 HELPR 버전·commit과 동일 입력 설정은 동일 configuration digest를 사용한다.
2. CSV 바이트가 바뀌면 `source_content_sha256`이 바뀐다.
3. 자산·부위·재료·하중 또는 표본 mapping이 없으면 수신하지 않는다.
4. 열 추가·삭제·이름 변경은 자동 추정하지 않고 새 공급자 스키마 검토를 요구한다.
5. 빈 값·NaN·미도달·계산 실패를 0 cycle, runout, 파단 또는 확률로 바꾸지 않는다.
6. 확률 연구의 행 순서를 물리 시편 ID로 사용하지 않고 명시적 고유 sample ID를 공급한다.
7. 대표 실제 export를 고정한 통합 시험과 별도 실험 검증을 각각 기록한다.
8. 공급자 경고를 버리거나 성공 상태에 흡수하지 않고, 경고 검토와 `a(crit)` 해석을 수신
   레코드 digest에 포함한다.

현재 `validation/helpr_adapter_contract.json`은 작성된 CSV로 수신 계약만 검사한다.
`validation/helpr_provider_review.json`은 제외된 공식 checkout의 버전·라이선스·출력 코드를
감사한다. `validation/helpr_end_to_end.json`은 공식 v2.1.0 대표 실행의 설정·환경·출력 해시,
결측 criterion과 검토된 경고 코드를 공개하되 원 CSV를 재배포하지 않는다. 어느 기록도 HELPR
물리모델이나 특정 배관의 적합성을 재검증하지 않는다.
