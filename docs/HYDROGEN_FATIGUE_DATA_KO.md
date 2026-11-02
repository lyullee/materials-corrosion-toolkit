# 4130X 수소가스 피로균열성장 자료

## 출처와 권리 경계

HyMatBase record `j1e8n-2bz97`은 Sandia의 quenched-and-tempered 4130X 압력용기강 자료와
`1211_NIB10_fra_fat.xlsx`를 공개 다운로드한다. 제공자 MD5
`74f2cf9105be68334c5e67cd91a6c191`과 로컬 파일이 일치한다. 그러나 record의 Rights 항목은 비어
있으므로 원 workbook과 점별 표를 재배포하지 않는다. 공개 패키지에는 출처·고정 해시·독립 reader,
집계 감사와 적용 한계만 포함한다.

## 확인된 구조

workbook은 재료, 환경, 파괴, 피로, plot의 다섯 sheet 이름을 갖는다. 피로 sheet에는 다음 네 curve가
있다.

| 응력비 R | 주파수 Hz | 점 수 |
|---:|---:|---:|
| 0.1 | 0.1 | 67 |
| 0.1 | 1.0 | 79 |
| 0.5 | 0.1 | 62 |
| 0.5 | 1.0 | 63 |

총 271개 점의 보고 범위는 ΔK 9.0593–33.452 MPa√m, da/dN
7.3406×10⁻⁹–4.0967×10⁻⁶ m/cycle이다. 재료 token은 4130X, 제품 형태는 vessel, temper는 Q&T,
미세조직 표기는 tempered martensite이며 curve orientation은 CL이다. 이들은 provider workbook의
표기이며 독립 재료·시편 확인 결과가 아니다.

중요하게도 HyMatBase record는 수소 압력을 4,500,000 Pa로 표시하지만 workbook은 45 MPa로
표시한다. 두 값은 10배 다르다. reader는 workbook 값을 고치지 않고 두 값을 별도 필드로 보존하며,
호출자가 충돌을 명시적으로 승인하지 않으면 읽기를 중지한다. record의 25 °C와 workbook의 `RT`
token도 별도로 유지하고 `RT`를 임의의 정확 온도로 변환하지 않는다.

## Python API

`read_hymatbase_hydrogen_fatigue`는 고정 SHA-256, source group ID, 물리 material-condition ID,
record의 압력·온도 근거와 압력 충돌 승인을 요구한다. 반환값은 다음 두 계약이다.

- `HydrogenFatigueSeries`: 환경, R, 주파수, method token, 열 위치, 충돌과 자격 상태
- `HydrogenFatigueGrowthPoint`: 원 행, SI ΔK와 da/dN, source digest와 미확정 시편 identity

workbook 수식은 실행하지 않는다. 데이터 열의 수식, 한쪽만 누락된 ΔK/da/dN 쌍, 비양수·비유한 값,
header·sheet·hash 변경은 거절한다. `audit_hymatbase_hydrogen_fatigue`는 점별 값을 배포하지 않고
curve 수·점 수·범위·수식 수와 충돌 상태를 집계한다.

## 사용 금지와 다음 단계

271개 행을 271개 독립 시편으로 세지 않는다. workbook에는 curve별 물리 시편 ID, 반복 관계,
전처리·종료·유효성 판정과 불확실성이 충분히 연결돼 있지 않다. 현재 자료는 다음을 자격화하지 않는다.

- 서비스용 Paris 또는 다른 성장곡선
- 수소 압력·주파수·응력비 효과의 일반화
- 균열 closure·threshold·retardation
- FAD, 잔여수명, 검사주기 또는 고장확률
- 규격 적합성이나 4130 계열 전체의 재료 호환성

다음 단계는 관련 1차 시험 문헌과 record 관리기관에서 압력 불일치를 확인하고, 각 curve의 물리 시편,
시험 순서·K-gradient·유효구간·검열·불확실성을 자격화한 뒤 calibration/holdout을 설계하는 것이다.
재현 명령은 `python scripts/inspect_hymatbase_hydrogen_fatigue.py`, 집계 결과는
`validation/hymatbase_4130x_hydrogen_fatigue_audit.json`이다.
