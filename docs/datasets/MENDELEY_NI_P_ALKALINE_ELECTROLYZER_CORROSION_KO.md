# Ni–P 도금 강의 알칼라인 전해조 부식 자료: 메타데이터 등록

## 자료 식별

- Dataset ID: `mendeley-ni-p-alkaline-electrolyzer-corrosion`
- 제공자 기록 v1: <https://data.mendeley.com/datasets/nnjj93s2mg/1>
- DOI: <https://doi.org/10.17632/nnjj93s2mg.1>
- 제공자 API manifest: <https://data.mendeley.com/public-api/datasets/nnjj93s2mg>
- 제공자: Xukang Cao, Tongji University; 2025-09-02 공개
- 제공자 선언 이용허락: CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>)
- 현재 상태: `metadata_only`; 원자료는 취득하지 않음

## 활용 가능성

제공자는 알칼라인 전해조 조건에서 Ni–P 도금 강의 부식 연구를 뒷받침하는 자료로 설명하고, SEM·EDS·XPS·전기화학·접촉저항(ICR) 자료 유형을 명시한다. 따라서 코팅 상태·전기화학 관측·계면 저항이 함께 존재하는 후보 자료로, 재료/코팅 적용성 검토와 후속 데이터 계보 설계에 참고할 수 있다. 파일 이름만으로 시험 조건이나 관측 의미를 추론하지 않는다.

공개 API manifest는 파일 155개, 총 19,340,142 bytes와 파일별 ID·크기·SHA-256을 제공한다. 카탈로그에는 이 메타데이터만 등록했고, 내려받거나 내용을 파싱하지 않았다.

## 별도 식별된 관련 논문

Mendeley의 구조화된 related-article 필드는 비어 있지만, 제공자 설명과 논문 제목·DOI를 대조해 다음 논문을 별도 참고자료로 연결했다: Yang et al., *Electrochimica Acta* 541 (2025), article 147331, DOI [10.1016/j.electacta.2025.147331](https://doi.org/10.1016/j.electacta.2025.147331). [출판사 기록](https://www.sciencedirect.com/science/article/pii/S0013468625016883)은 실험에서 KOH 농도·온도·인가전위 효과를 다루고, 별도 유동 연성 해석도 포함한다고 요약한다. 시편은 Ni–P 코팅 탄소강으로 설명된다.

논문 요약에 기술된 시험 맥락은 파일별 매핑으로 승격하지 않는다. 개별 측정 파일의 시험조건·단위·시편·반복수·변수 정의는 아직 연결되지 않았다. 논문 전문, 표, 그림 또는 측정값은 이 프로젝트에 복사하지 않았고, 논문 이용권한은 dataset-level CC BY 4.0 선언과 별개다.

일부 폴더에는 같은 제공자 파일명이 반복된다. 카탈로그의 `filename`은 각 provider file ID를 앞에 붙인 로컬 식별 이름이며, 원래 이름은 별도 `provider_filename`에 그대로 보존한다. URL·file ID·해시는 provider API 값 그대로 유지한다. 동일한 이름이나 순서만으로 시편·조건·실험 의미를 추정하지 않는다.

## 저작권 및 배포 경계

Mendeley 기록/API는 자료 전체에 CC BY 4.0을 선언한다. 적절한 출처 표시, 라이선스 링크 및 변경 여부 표기가 필요하다. 제공자 라이선스 설명은 자료 내부에서 제3자 소유로 식별된 콘텐츠에 추가 허가가 필요할 수 있다고 경고한다. 이 프로젝트는 선언된 데이터셋 수준 조건을 개별 파일·이미지·도표의 권리 확인과 동일시하지 않는다. 따라서 현 상태에서는 메타데이터만 기록하고, 원자료나 추출 관측값을 공개 배포하지 않는다. 이 기록은 법률 검토나 권리 clearance가 아니다.

## 과학적 한계와 후속 작업

- 구조화된 related-article 필드는 비어 있다. 출판사 제목/DOI로 관련 논문을 별도 식별했지만, 시험 프로토콜 전체와 시편 대응표, 반복 수, 변수 단위 및 파일별 의미는 확인되지 않았다.
- 파일별 SHA-256은 제공자 API가 공표한 값이며, 현재 로컬 파일 digest와 대조한 결과가 아니다.
- 원자료 취득 후에는 개별 파일의 저작권·제3자 표식 검토, 표/이미지 출처 확인, 단위·시편·조건 매핑 및 독립적인 데이터 품질 검토가 필요하다.
- 사용 적합성이 확인되기 전까지 부식 속도식, 코팅 수명식, 적격성·안전성 판단 또는 FTA 확률의 보정 자료로 사용하지 않는다.

## 카탈로그 위치

- `data/catalogs/datasets.json`
- `src/matintegrity/catalog_data/datasets.json`
- 등록 ID: `mendeley-ni-p-alkaline-electrolyzer-corrosion`

원자료는 프로젝트에 내려받지 않았다. 파일 manifest는 Mendeley Data의 공개 dataset API에서 읽은 메타데이터로 한정된다.
