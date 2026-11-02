# BAM CMSX-6 크리프 LIS 로컬 reader

## 데이터셋과 범위

- 데이터셋: BAM Reference Data: Creep of Single-Crystal Ni-Based Superalloy CMSX-6
- 고정한 기록: [Zenodo record 14750432](https://zenodo.org/records/14750432), DOI `10.5281/zenodo.14750432`
- 선택 asset: `Vh5205_C-97.LIS`
- 카탈로그 pin: 360,637 bytes, provider-reported MD5 `c9a1e0cf2430762634b8da84cfe10fdd`
- 로컬 위치: `data/raw/cmsx6-creep/Vh5205_C-97.LIS`
- API: `matintegrity.cmsx6_creep_lis_typed_rows`

이 reader는 catalog에 고정한 단일 `.LIS`만 받아 파일명, 바이트 길이, MD5를 확인하고, 검증한 입력의 SHA-256을 함께 기록한다. 파일의 줄 순서·물리 줄 번호·탭 구분 원문 토큰을 보존한다. 표 구간은 헤더의 label/symbol/unit 원문과 위치별 값을 연결하고, 정수·소수점·유럽식 소수 콤마를 각각 원형 토큰을 유지한 채 선택적으로 `float`로 읽는다. 소수 콤마 숫자의 단위 해석이나 물성 의미는 추가하지 않는다. 비수치, 빈 값, 열 정렬 오류도 원문을 유지한다.

## 라이선스와 재사용 범위

Zenodo 데이터셋 레코드는 CC BY 4.0으로 카탈로그에 기록되어 있다. 사용 시 데이터 큐레이터·수집자·연구자·감독자·연구기관의 기여를 포함한 출처 표기, 라이선스 링크, 수정 여부 표시를 유지한다. 권장 표기: “L. Ávila Calderón et al., *BAM Reference Data: Creep of Single-Crystal Ni-Based Superalloy CMSX-6*, Zenodo, DOI 10.5281/zenodo.14750432, CC BY 4.0; locally parsed into typed rows.” 정확한 contributor 및 버전 정보는 원본 Zenodo 기록을 확인한다.

이 권리는 데이터셋 기록에 적용되는 조건이다. 그 기록이 참조하는 시험 표준, 기술도면, 별도 보고서 및 기타 문서의 저작권·이용조건을 확장하지 않는다. 이 구현과 문서에는 그러한 문서의 문장·표·한계값을 복사하지 않는다. parser는 코드로만 공개할 수 있도록 만들었고, 원본 관측 파일을 저장소의 배포 경로에 넣지 않는다. underlying data의 재사용은 해당 Zenodo asset의 데이터 라이선스와 출처 표기 범위로 한정하고 별도 문서 권리와 구분한다.

## Python 사용

```python
from matintegrity.cmsx6_creep_lis_typed_rows import (
    CMSX6LISReadAuthorization,
    iter_cmsx6_creep_lis_rows,
)

authorization = CMSX6LISReadAuthorization(
    attribution=(
        "L. Ávila Calderón et al., BAM CMSX-6 creep reference data, "
        "Zenodo DOI 10.5281/zenodo.14750432, CC BY 4.0"
    ),
    computational_use_authorized=True,
    local_only_authorized=True,
)

for row in iter_cmsx6_creep_lis_rows(
    "data/raw/cmsx6-creep/Vh5205_C-97.LIS",
    authorization=authorization,
):
    if row.row_kind == "data":
        # Keep raw tokens and source ordering with every downstream transformation.
        consume(row)
```

반환 타입 `CMSX6LISTypedRow`에는 데이터셋/파일 식별자, 로컬 전용 표시, caller attribution 및 authorization digest, 원문 줄·토큰, parse 상태, 줄 해시와 `Evidence`가 있다. `audit_cmsx6_creep_lis(CMSX6LISReadRequest(...))`는 값 줄을 돌려주지 않고 local pin 및 줄 개수 요약만 반환한다.

`data/raw` 원본을 직접 복사하거나 전송하는 코드는 reader에 포함하지 않는다. 호출자는 CC BY 표기와 관측 자료 이용 근거를 후속 산출물에도 전달해야 한다. `computational_use_authorized=True`와 `local_only_authorized=True`는 호출자가 해당 조건을 확인했다는 선언이며, 법률 판단 또는 자료 소유권을 API가 부여하는 것은 아니다.

## 해석 금지 및 한계

- `.LIS` 라인의 label, symbol, unit token은 원문 필드로만 제공한다. reader는 행을 시험 절차 합격, 재료 적격성, 설계 허용치 또는 규격 검증으로 해석하지 않는다.
- 숫자 파싱은 문법 변환뿐이다. 시험 시계 변환, strain 정의 선택, 온도 보정, 응력 재계산, 크리프 법칙 적합, 외삽, 파단수명·손상 추정은 수행하지 않는다.
- 단일 고정 asset reader이며 데이터셋 전체를 합치거나 시험 간 독립성·재현성을 주장하지 않는다.
- provider-pinned MD5는 해당 카탈로그 파일 snapshot 일치 검사다. 보안상 충돌 저항성 보장을 대신하지 않는다. reader는 별도 SHA-256도 계산해 로컬 호출/다운스트림 추적에 사용한다.
- 코드, 문서, wheel/source archive에 원본 데이터·시험 표준·기술도면·보고서가 포함되지 않도록 한다.

## 출처와 개발 메모

원본 출처·버전: [Zenodo 14750432](https://zenodo.org/records/14750432). CC BY 4.0 조건: [Creative Commons license](https://creativecommons.org/licenses/by/4.0/). 데이터셋과 함께 게재된 데이터 설명 논문은 별도 저작물이며, Zenodo 기록과 논문의 라이선스/버전 관계를 각각 확인한다. 이 parser는 저작물 본문을 변환·복제하지 않고 선택된 local `.LIS`의 행 구조와 provenance를 노출한다.

원본 asset은 `data/raw/cmsx6-creep/`의 local-only 자료다. 이 문서와 parser는 원본 줄, 관측값, 논문 문장을 포함하지 않는다. 기능 테스트, 데이터 행 개수 확인, 수치 모델 실행 및 package build는 별도 검증 작업에서 수행한다.
