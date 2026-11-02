# Crevice 전기화학 공개자료 후보 검토

- 조사일: 2026-11-01
- 목적: 공간 전류·혼합전위·Crevice 부식 관련 구현에 사용할 수 있는 공개 관측자료의 권리, 구조와 사용 범위를 선별한다.
- 현재 상태: 후보 메타데이터 조사. 원자료 다운로드·열람·파싱은 하지 않았으며 어떤 후보도 계산 검증 데이터로 채택하지 않았다.

## 우선 후보

### ETH Research Collection: 리벳 구조물 Crevice 부식 ZRA 전류

- [공식 자료 레코드](https://www.research-collection.ethz.ch/entities/researchdata/6d0846d4-b289-4dfe-885d-da089f4ff1b2), persistent identifier `20.500.11850/804107.1`.
- 검색 가능한 레코드 설명은 전극 배열 핀별 ZRA 전류 파일과 X-ray diffraction 자료를 포함한다고 한다. 시계열 표는 시간 초와 전류밀도 A/cm² 순서라고 제공자가 설명한다. 측정 기간은 2024년 6월부터 2025년 5월까지로 기록되어 있다.
- 레코드는 CC BY 4.0으로 표시되지만, 상태도 “in review”이며 제공자가 자료가 아직 검증되지 않았다고 밝힌다. 이 표시만으로 시험 설계의 적합성이나 수치 품질을 보증하지 않는다.
- 이번 조사 환경에서는 공식 레코드 본문이 HTTP 403으로 열리지 않았다. 파일 manifest, 파일별 체크섬·크기, 제공자 설명 전체와 실제 다운로드 응답을 확인하지 못했으므로 dataset catalog 및 importer에는 등록하지 않는다.
- 예상 활용 경계: 나중에 파일 접근과 메타데이터를 확인하더라도 우선은 제공자 전류밀도 이력의 보존형 reader 후보로 검토한다. 핀 위치/면적, 전극 연결, 시간 기준, 반복 실험 단위, 전류 부호, XRD 상 해석과 불확도 관계를 확인하기 전에는 혼합전위 branch kinetics 보정이나 독립 검증에 사용하지 않는다.

### Mendeley Data: Ni계 합금 Crevice 재부동태 전위

- [공식 Mendeley v1 레코드](https://data.mendeley.com/datasets/yykwcgsjkh/1), DOI [10.17632/yykwcgsjkh.1](https://doi.org/10.17632/yykwcgsjkh.1).
- 제공자는 여러 Ni계 합금을 NaCl과 황산염·몰리브데이트·질산염 억제제 환경에서 30, 60, 90 °C로 시험한 인공 Crevice의 재부동태 전위를 설명한다. 페이지는 CC BY 4.0을 선언한다.
- 레코드 본문에서 파일 목록과 파일 단위 manifest가 이 조사에서 확인되지 않았다. 공식 Mendeley API의 버전 1 파일목록 endpoint를 무인증으로 조회했을 때도 HTTP 401을 반환했다. 원본 파일, 체크섬, 크기, 시편별 단위와 상세 시험조건을 확인하기 전에는 데이터 catalog/importer를 추가하지 않는다.
- 예상 활용 경계: 조건과 endpoint가 파일 단위로 매핑되면 caller가 제시한 재부동태 기준의 제한적 비교자료가 될 수 있다. 재부동태 전위 하나만으로 과도 혼합전위, 공간 전류, 부식률, 일반화된 재료 순위 또는 파괴확률을 보정하지 않는다.

## 보조 후보

### Electrochemical metrics for corrosion-resistant alloys

- [Scientific Data 논문](https://www.nature.com/articles/s41597-021-00840-y), 보조 데이터 DOI [10.6084/m9.figshare.13611623](https://doi.org/10.6084/m9.figshare.13611623).
- DOI가 가리키는 Figshare v1 항목은 관측치 테이블이 아니라 `data.json` (6,695 bytes)과 `metadata summary.csv` (431 bytes) 두 파일을 가진 **metadata record**다. Figshare 공개 API 메타데이터는 이 두 자산의 MD5를 각각 `8ba38c30e42b239bf60f5495e65b4528`, `b81e5b90bfefb4647f0a4c8eaab3bd99`로 표시하고, 항목 라이선스는 CC0다. 이번 조사에서는 파일을 내려받거나 해석하지 않았다.
- 원 논문은 pitting/crevice potential·temperature, corrosion potential/current, passive current 및 corrosion rate를 다루는 문헌 편집 자료를 설명하지만, 해당 metadata-only DOI는 그 underlying observation tables 자체가 아니다. 이 metadata record는 exact-knot 시계열이나 실제 Crevice transport history가 아니다.
- 실제 자료 endpoint의 source row·검출 한계·시험법·실험별 조건 및 원 관측 권리를 별도로 확인해야 한다. metadata summary를 관측 데이터로 오인하거나 기존 컴파일 자료와 병합하고 동종 실험 반복으로 취급하지 않는다.

### Zenodo: Pt(111)-수용액 계면 이중층 용량 자료

- [공식 Zenodo 레코드](https://zenodo.org/records/5834860), DOI [10.5281/zenodo.5834860](https://doi.org/10.5281/zenodo.5834860).
- 공식 Zenodo API는 dataset license를 `CC-BY-4.0`으로 표시하고, `capacitance data files.zip` 한 파일(2,001,400 bytes, 게시자 MD5 `a205c0c4efb8236556c7d87c909c4e08`)을 나열한다. 레코드 설명은 논문 그림 1, 2, 3, 5, 6, S2의 원자료이며 Pt(111)-수용액 계면 대상이라고 기록한다. 별도 제공 코드 위치는 mean-field Pt 이중층/흡착수 계산이라고 식별된다.
- 2026-11-01 조회 시 API metadata만 확인했다. 프로젝트의 올바른 로컬 `data/raw/`에는 원자료를 저장하지 않았고 archive 내부 파일이나 수치 열을 확인하지 않았다. 따라서 아직 import 대상이나 계산 검증자료가 아니다.
- 활용 경계: 공개 라이선스가 확인된 파일을 추후 reader interoperability 예제로 검토할 수는 있지만 Pt(111) mean-field 값은 탄소강/스테인리스 Crevice의 차분용량으로 전용할 수 없다. 표면 조성, 결정방향, 흡착종, 용액 조성, 전위 기준, 면적 정규화 및 계산 모델 차이가 해소되지 않았으므로 어떤 부식 모델 파라미터 보정·검증에도 연결하지 않는다.

## 다음 데이터 확보 단계

1. 공식 저장소에서 version별 파일명·파일 크기·게시자 체크섬·다운로드 URL과 라이선스 고지를 확보한다.
2. 원자료를 내려받게 되면 프로젝트의 로컬 전용 `data/raw/` 경계 안에서만 보관하고, 제공자 pin과 로컬 SHA-256을 대조한다.
3. reader를 만들기 전에 열·행 단위와 물리 시편·반복·전극 셀 ID, 면적, clock, 단위, sign 및 missing-value 의미를 확인한다.
4. 권리·형식·계보가 확인된 범위만 catalog/importer로 연결하고, 데이터 설명과 계산 검증의 범위를 분리한다.

## 출처와 접근 확인

- ETH Research Collection record: <https://www.research-collection.ethz.ch/entities/researchdata/6d0846d4-b289-4dfe-885d-da089f4ff1b2> (검색 메타데이터 확인, 본문 접근은 403)
- Mendeley Data v1: <https://data.mendeley.com/datasets/yykwcgsjkh/1>
- Mendeley Data API docs: <https://data.mendeley.com/api/docs/> (dataset file listing endpoint documented; this unauthenticated query returned HTTP 401)
- Scientific Data article: <https://www.nature.com/articles/s41597-021-00840-y>
- Figshare record: <https://doi.org/10.6084/m9.figshare.13611623>
- Figshare public API metadata: <https://api.figshare.com/v2/articles/13611623> (metadata fields and file manifest only)
