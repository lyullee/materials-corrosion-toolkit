# 연속 배관 ILI 이력 자료

## 범위와 출처

Mendeley Data `10.17632/c2h2jf5c54.1`의 CC BY 4.0 자료를 로컬 취득했다. 제공된 README와 네
workbook은 한 배관에서 네 검사 회차에 보고된 외부부식 feature 표를 담는다. 회차 표기의 `Year`는
실제 설비 연령이 아니다. 이 자료는 이미 처리·선별된 표이며 원 MFL flux, sensor channel, lift-off,
주행속도, 자화상태, 굴착 치수 또는 물리 feature의 영속 식별자를 제공하지 않는다.

원 PDF·XLSX는 `data/raw/` 아래에만 두고 source/wheel 배포에서 제외한다. 코드와 문서에는 제공자
문장을 복제하지 않고 독립적으로 작성한 필드 계약, 해시, 권리·적용 한계와 집계 감사만 남긴다.

## 고정 파일과 전수 감사

| 회차 | 파일 SHA-256 | 관측 행 | 주요 누락 |
|---:|---|---:|---|
| 1 | `68dc9b2b651f07f27b8f3a28d24f3909f74e505f9da17fa8782e750f0c3db49f` | 735,755 | seam orientation 3,604 |
| 3 | `3622b9d5689e504bd09c3cf389e2fc2b1c638fb50d13a0b290d84f3464a2f611` | 832,681 | seam orientation 전체 |
| 5 | `2e948c8f23aa0668e57798c03e4ac9b34b617c89599631c8e93da1601d63d31c` | 759,683 | seam orientation 4,224, end distance 전체 |
| 7 | `37128dfb91f40325314af71cb4e8771e76577ef3ca0f75ed5020f771b8cab462` | 870,301 | seam orientation 4,801 |

총 3,198,420행, 269,180,366바이트다. 네 파일 모두 15열 header와 회차 token이 일치했고 수식 셀과
비수치 데이터는 없었다. 보고 wall thickness는 전부 7.1 mm이고, 최대깊이 범위는 0.07–5.18 mm다.
이 사실은 자료의 품질 또는 결함 치수 정확도를 입증하지 않는다. 집계 결과는
`validation/pipeline_ili_history_audit.json`에 있다.

## Python 계약

`iter_pipeline_ili_features`는 호출자가 물리 배관 ID, 검사 회차 ID, 실제 연령으로 해석하지 않는
회차 token, 제공자 파일의 정확한 SHA-256을 명시할 때만 행을 읽는다. 필요하면 provider row 범위를
지정할 수 있다.

길이는 m, mm 열은 m, 각도는 radian으로 변환한다. 원 파일명·해시·행 번호·누락값과 음수값을
보존하며, 음수 길이·두께 계열 값은 자동 수정하지 않고 quality flag를 붙인다. workbook header,
해시 또는 회차가 다르면 중단한다. 수식은 계산하지 않으며 숫자 자리에 수식이 있으면 거절한다.

`audit_pipeline_ili_workbook`은 XLSX XML을 제한된 메모리로 순회해 header, 행 수, 누락, 최소·최대,
비수치·수식과 회차 불일치를 센다. 이 감사는 데이터 해석이나 feature matching을 수행하지 않는다.

## 금지된 추론과 후속 사용

서로 다른 회차의 같은 행 번호 또는 가까운 좌표를 같은 물리 결함으로 간주하지 않는다. 따라서 현재
API는 성장률, 부식속도, 탐지확률, sizing bias, 검사 신뢰도, 남은 수명 또는 고장확률을 계산하지 않는다.
그 계산으로 확장하려면 최소한 다음 별도 자격화가 필요하다.

1. 배관 좌표계·girth weld 정합과 회차별 위치 불확실성
2. 물리 feature identity와 split/merge/censoring 규칙
3. calibration/holdout 분할 및 동일 배관·동일 feature 누출 방지
4. 독립 굴착 또는 다른 신뢰 가능한 치수 기준
5. 검사기·모델·절차 리비전과 단위·오차모형

재현 명령은 `python scripts/inspect_pipeline_ili_data.py`다. 대용량 원파일이 없는 공개 checkout에서는
실행하지 않으며, manifest로 파일을 취득한 뒤 제공자 해시를 검증해야 한다.
