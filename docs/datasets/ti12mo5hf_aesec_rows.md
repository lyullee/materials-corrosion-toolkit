# Ti-12Mo-5Hf AESEC 워크북 로컬 행 reader

## 출처·라이선스·원본 위치

- 데이터 출처: [Zenodo DOI 10.5281/zenodo.19462164](https://doi.org/10.5281/zenodo.19462164)
- 공식 레코드는 제공 데이터에 CC0-1.0을 선언합니다. 사용자는 배포/연구 적용 전에 원 레코드의 권리·인용 안내를 확인하십시오.
- ZIP 및 워크북은 저장소 추적/패키지 자료에 포함하지 않습니다. 무시 처리되는 `data/raw/zenodo-ti12mo5hf-oxygen-corrosion/`의 로컬 ZIP만 reader에 전달합니다.
- 컨테이너 고정 SHA-256: `0d50714744e0c6b1b2359beedde96f6b8842ad45ba19c6fcc224b90fd95d6915` (47,558,332 bytes).

## 구현한 범위

신규 모듈 `matintegrity.ti12mo5hf_aesec_rows`는 두 개의 제공자 계산 결과 워크북만 허용합니다. archive SHA-256, 내부 멤버 크기·SHA-256, 시트명, 표 크기와 정확한 원본 첫 행 라벨을 확인합니다. ZIP을 디스크에 풀지 않고 XLSX 바이트를 제한된 메모리 버퍼로 열며, `openpyxl`의 read-only 행 반복자를 통해 공급자 셀을 원 순서·결측 형태 그대로 전달합니다.

| 원본 멤버 | 바이트 | SHA-256 | 시트 크기 |
| --- | ---: | --- | ---: |
| `AESEC/Ti12Mo5Hf.xlsx` | 260,255 | `ebb6feb5a8413a045f947b511b3859185ce7471ada408faba2cbb50c6b7f87be` | 5,076 × 7 |
| `AESEC/Ti12Mo5Hf0.3O.xlsx` | 266,785 | `1b417efd20b85deaa8f27c1459332af71ad7d9dd4ebfd5efd29cbba1f3676567` | 5,075 × 7 |

시트 첫 행은 시간(초), Ti/Hf/Mo 용출률(ng·s⁻¹·cm⁻²), Ag/AgCl 기준 전위(V), 두 전류 밀도 열(µA/cm²)을 표기합니다. 원본 헤더 텍스트는 row contract에도 보존됩니다. API는 값을 시간·전위 구간으로 분할하지 않으며 단위 환산, 결측 대체, 필터링, 곡선 맞춤, 부식률 추론 또는 시편별 성능 비교를 하지 않습니다. 제공자가 계산 결과로 명시한 열도 독립 검증된 값으로 간주하지 않습니다.

행 contract `matintegrity.zenodo_ti12mo5hf_aesec_row.v1`는 각 행의 source row number, 원 셀 배열, archive/member 해시와 라이선스·DOI provenance를 제공합니다. 입력 contract `matintegrity.zenodo_ti12mo5hf_aesec_request.v1`에는 로컬 경로와 명시적인 계산 사용·로컬 전용 승인이 필요합니다. 세션/API 호출자는 행 객체를 다룰 권리와 목적에 맞는 downstream 해석 책임을 가집니다.

## ICP-MS 워크북을 파싱하지 않은 이유

ICP-MS 시트에는 농도 헤더의 ppm 단위와 원소가 표시되어 있으나, 한 시트 안에서 반복 시료 행과 평균·표준편차 요약 열이 병렬로 섞여 있습니다. 시료 라벨은 재료, 노출 시점 및 반복을 문자열로 합쳐 저장하고 있으며, 제공자 README의 7일 표기와 라벨의 `7dni` 표기 등 정규화 규칙을 reader가 임의로 부여하면 안 됩니다. 계산식 셀도 있어 표시값과 계산 재현성 확인이 필요합니다. 따라서 이 버전은 ICP-MS 구조를 조사만 했고 parser/schema를 내놓지 않습니다. 후속 구현에는 명시적 시료-시점 사전, formula/cache 처리 정책, replicate/통계량 정의에 대한 검토가 필요합니다.

AESEC 원시 intensity 파일은 헤더에 강도 단위·검량 관계가 충분히 드러나지 않아 이 reader의 대상에서 제외했습니다. DTA 원본 파일도 별도 파서 계약 없이 혼합하지 않습니다.

## 호출 방법

`examples/ti12mo5hf_aesec_rows_local.py`는 실행하지 않은 사용 예입니다. optional `science` extra의 `openpyxl`이 필요합니다. 호출자는 명시적으로 원본 local-only 사용을 승인해야 합니다. ZIP 누락, 컨테이너/멤버 digest 불일치, 헤더나 shape 변경, 승인 누락 시 reader는 fail-closed 합니다. 네트워크·압축 해제·원자료 복제·계산은 수행하지 않습니다.

