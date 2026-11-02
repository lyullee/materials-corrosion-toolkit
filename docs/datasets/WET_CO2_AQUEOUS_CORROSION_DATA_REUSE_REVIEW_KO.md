# 습윤 CO₂·수용액 부식 공개 데이터 재사용 검토

- 조사일: 2026-10-31
- 조사 범위: 공개 원자료, 명시적 CC0/CC-BY 라이선스, 재료·시편 정보, 시험 용액과 노출 조건, 직접 파일 주소와 공개 체크섬
- 카탈로그 비교: 상위 작업 폴더에서 확인한 후보를 이 저장소의 기존 카탈로그에 통합했다. 원자료 파일은 배포물 밖의 `data/raw/` 로컬 캐시에 둔다.
- 결론: **CC BY 4.0이며 습윤 CO₂ 수용액에서 실제 중량감량 부식 시험의 supporting data를 제공하는 재사용 후보를 확인했다.** 다만 파일을 아직 받지 않아 셀/열 수준 내용과 반복시험 구조는 미확인이다. 자료는 원문에 명시된 좁은 조건의 benchmark/calibration 후보로만 취급한다.

## 카탈로그에 기록한 후보: CT110 코일드 튜빙 용접부 고온·고압 CO₂ 시험

- 출판사 논문: [PLOS ONE 원문](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0244237), DOI [10.1371/journal.pone.0244237](https://doi.org/10.1371/journal.pone.0244237)
- 데이터 레코드: [PLOS Figshare supporting dataset](https://plos.figshare.com/articles/dataset/S1_File_-/13628192), DOI [10.1371/journal.pone.0244237.s017](https://doi.org/10.1371/journal.pone.0244237.s017)
- 직접 파일 URL: <https://ndownloader.figshare.com/files/26155592>
- 라이선스: Figshare 공개 API 레코드에서 **CC BY 4.0** 확인. 논문도 Creative Commons Attribution 라이선스로 공개되었다고 명시한다. 재배포·가공 시 저자/출처를 표시하고 라이선스 조건을 지킨다.
- 파일 메타데이터: `pone.0244237.s017.xlsx`, 9,331 bytes. Figshare 공개 메타데이터가 제공한 `supplied_md5`와 `computed_md5`가 모두 `95fa4a025f4afe1aac1b5de41c420160`으로 일치한다. 이 값은 원격 레코드의 MD5 무결성 확인값이며, 로컬에서 다운로드한 파일의 해시를 계산한 것은 아니다.
- 시험 재료: CT110 코일드 튜빙의 용접 금속(WM)과 모재(BM). 논문은 원 튜빙 외경 50.8 mm, 벽 두께 4.4 mm, 시험편 크기 81 × 20 × 2 mm와 재료 조성 주요 항목을 제공한다. 용접부가 시험편 중앙에 오도록 채취했고 연마 순서도 설명한다.
- 부식 노출: 가스전 수질을 바탕으로 한 수용액, pH 5.6, 총압 4 MPa, CO₂ 분압 또는 온도 조건을 바꾸어 96시간 고온·고압 반응기 노출을 수행하고 중량감량법으로 부식률을 산출한다. 논문은 온도 30/60/90°C 비교와 CO₂ 분압 0.1/0.2/0.3 MPa 비교를 보고한다. 이온 농도는 Ca²⁺ 7.03, Mg²⁺ 0.76, SO₄²⁻ 0.67, HCO₃⁻ 0.90, Cl⁻ 60.0 g/L로 제시된다.
- 목적 적합성: 실측 wet-CO₂ 부식률 및 용접부-모재 차이의 조건부 보정/비교에 적합한 후보. 특히 염화물 농도가 높은 수용액 및 고압·고온 조건 모델의 좁은 benchmark에 쓸 수 있다.
- 파일 검사: 2026-10-31 공식 Figshare 파일을 로컬에서 확인했다. 파일 크기는 9,331 bytes, publisher MD5는 `95fa4a025f4afe1aac1b5de41c420160`, 관측한 local SHA-256은 `8e6ce76d2e67f9a24af1ccfadebc4453e5601c3a7694c7f4bf3d56d259145470`이다. 첫 worksheet에는 온도 열과 WM/BM 부식률 열이 있는 세 데이터 행이 있고, 나머지 두 worksheet는 비어 있다. 열 이름·단위·원행 및 셀 계보를 보존하는 local typed reader를 만들었으며, 원 XLSX나 점별 측정값은 공개 배포물에 넣지 않는다.
- 제한: 단일 CT110 소재 계열과 특정 가스전 기반 수용액에 한정된다. 시험은 96시간의 정적 반응기 노출이며 유속·침식 효과를 검증하지 않는다. 온도와 CO₂ 분압 값들은 각각 다른 조건을 고정한 비교군이지 전 조합 요인 설계가 아니다. 공개 시험 설명에서 독립 반복 수를 확인하지 못했고 workbook도 반복 개수를 증명하지 않는다. 따라서 일반 탄소강, 장기 운전, 현장 수명 예측으로 확대 주장하지 않는다.

## 유력하지만 파일 메타데이터 확인을 더 해야 하는 후보

### MDEA 수용액의 CO₂ 포화 탄소강 전기화학 임피던스

- Mendeley 공식 레코드: [버전 3](https://data.mendeley.com/datasets/6tscvfjycn/3), DOI [10.17632/6tscvfjycn.3](https://doi.org/10.17632/6tscvfjycn.3)
- 관련 출판사 논문: [Corrosion Science 논문 및 Data Availability](https://www.sciencedirect.com/science/article/pii/S0010938X22007776), DOI [10.1016/j.corsci.2022.110859](https://doi.org/10.1016/j.corsci.2022.110859)
- Mendeley 레코드는 탄소강 전극을 80°C CO₂ 포화 수용성 MDEA에 노출한 EIS의 미가공 실험 자료와 시뮬레이션 자료가 함께 포함되고 CC BY 4.0이라고 밝힌다. 출판사 초록은 pH 7.9–8.6 조건, FeCO₃ 막과 산소 유입 영향 및 원자료의 Mendeley 위치를 설명한다.
- wet CO₂의 보호성 부식 생성물/전기화학 응답 모델에 기술적으로 유망하다. 다만 이 조사 시점에 공식 Mendeley 파일별 직접 URL, 크기, checksum과 버전 3의 전체 파일 manifest를 안정적으로 확보하지 못했고, 해당 논문 방법에 있는 시험 전극 상세 사양도 여기서 검증하지 못했다. 파일 단위 증거가 모일 때까지 카탈로그에는 올리지 않았다. 해당 데이터는 실측값과 시뮬레이션값을 명확히 분리해야 한다.

### Cr–Mo 저합금강 열처리·CO₂ 부식 자료

- 공식 레코드: [Mendeley Data](https://data.mendeley.com/datasets/j4vfxfnt9j/1), DOI [10.17632/j4vfxfnt9j.1](https://doi.org/10.17632/j4vfxfnt9j.1)
- 레코드는 CO₂ 부식 저항에 관한 자료와 CC BY 4.0 라이선스를 표시하고, 텍스트, 전자현미경 이미지, potentiostat 원자료 파일을 안내한다. 열처리된 Cr–Mo 저합금강이라는 재료 범위는 관련 연구 제목으로 확인된다.
- 직접 파일별 크기/hash와 specimen·노출 조건의 완전한 표를 이 조사에서 검증하지 못해 카탈로그에는 등록하지 않았다. 보정 데이터 후보로 승격하기 전에 관련 논문 시험조건과 원자료 파일 manifest 확인이 필요하다.

## 제외한 자료와 이유

- [NORSOK M-506 CO₂ pipeline corrosion simulation dataset](https://data.mendeley.com/datasets/4nydhxjymw/1): CC BY 4.0이지만 243개 값은 NORSOK 모델과 Monte Carlo로 생성된 시뮬레이션 결과다. 실험이나 현장 측정이 아니므로 실측 검증 데이터로 쓰지 않는다. 모델 입력/출력 예제 또는 구현 비교용으로만 별도 분류할 수 있다.
- [Heterogenous CO₂ Corrosion Dataset](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/1ZIEO4): NLM 카탈로그는 CC0라고 표시하지만 설명은 문헌 기반 field/simulated/experimental 자료가 섞여 있다고만 한다. 조사 과정에서 Harvard Dataverse의 원 레코드·파일 manifest·자료별 출처를 직접 확인하지 못했다. 2차 카탈로그 설명만으로 원자료의 권리와 provenance가 충분하다고 판단하지 않아 등록하지 않는다.
- [Dryad: CO₂ corrosion on downhole tools](https://datadryad.org/dataset/doi%3A10.5061/dryad.fn1r084): 실험 부식률 데이터 설명 및 단일 DOCX 파일은 확인했으나, 이 조사에서 레코드의 명시적인 CC0/CC-BY 라이선스 문구와 시험 시편/노출 조건 상세를 확인하지 못했다. 라이선스와 metadata 확인 전에는 사용하지 않는다.
- [Mendeley: coiled tubing weld corrosion supplementary data](https://plos.figshare.com/articles/dataset/S1_File_-/13628192)는 위 카탈로그 항목으로 등록했다. [NLM Dataset Catalog](https://datasetcatalog.nlm.nih.gov/dataset?q=0000978267)는 CC BY 4.0의 PLOS supplementary XLSX임을 보조적으로 보여주며, 공식 Figshare API metadata에서 직접 asset, 크기, MD5, license를 교차 확인했다.

## 데이터 재사용 및 보정 경계

1. 원자료는 ignored `data/raw/` 경로에서 해시 고정해 검사한다. 카탈로그에는 공식 레코드·다운로드 URL·publisher checksum과 별도로 관측한 local SHA-256을 기록하며 원 XLSX는 저장소 배포 경로에 포함하지 않는다.
2. CC BY 4.0은 재사용을 허용하지만 저자/출처 표시가 필요하다. 논문 문장이나 표를 복사해 모델 문서에 옮기지 않는다. 수치 데이터의 출처, 변환, 단위, 불확도와 재배포한 변경 사항을 명시한다.
3. publisher MD5와 local SHA-256은 각각 제공자 파일 동일성의 참고와 local copy 계보에 사용한다. 시트/열 구조만 확인했으며 셀 값은 모델 calibration이나 성능평가에 사용하지 않았다. 후속 적용 전 원행 의미, 단위, 반복 설계, 조건 대응과 측정 불확도를 연구자가 검토해야 한다.
4. 측정 자료는 모델 검증의 한 사례이지, 특정 재료/환경에서의 설계 허가나 보편적인 부식률 예측 정확도를 보장하지 않는다.

## 확인에 사용한 공식/원 출처

- <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0244237>
- <https://plos.figshare.com/articles/dataset/S1_File_-/13628192>
- <https://api.figshare.com/v2/articles/13628192>
- <https://data.mendeley.com/datasets/6tscvfjycn/3>
- <https://www.sciencedirect.com/science/article/pii/S0010938X22007776>
- <https://data.mendeley.com/datasets/j4vfxfnt9j/1>
- <https://data.mendeley.com/datasets/4nydhxjymw/1>
- <https://datadryad.org/dataset/doi%3A10.5061/dryad.fn1r084>
