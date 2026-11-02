# Dryad downhole-tool CO₂ 부식 자료 후보 검토

## 후보 식별

- 자료명: *Data from: Mechanism and modelling of CO₂ corrosion on downhole tools*
- 저장소 DOI: [10.5061/dryad.fn1r084](https://doi.org/10.5061/dryad.fn1r084)
- 연결 논문: Wang et al., *Mechanism and modelling of CO₂ corrosion on downhole tools*, Royal Society Open Science (2019), [PMC 원문](https://pmc.ncbi.nlm.nih.gov/articles/PMC6502365/)
- 저장소에 표시된 파일: `Date.docx` 한 개, 17.74 KB
- 저장소의 데이터 라이선스: Dryad 데이터셋 CC0 waiver. 출판 논문과 그 안의 표·그림 권리는 별도로 취급한다.

## 기존 wet-CO₂ 자료와의 차이

현재 프로젝트의 주요 자료 경로는 NORSOK M-506 기반으로 생성된 파이프라인 시뮬레이션 격자와 CT110 코일드 튜빙 용접부/모재의 좁은 실험 자료다. 이 후보는 유정용 재료를 대상으로 한 CO₂ 부식 실험 자료로 설명되어 있어, 강재 등급 및 고온·고압 유정 환경을 보완할 가능성이 있다. 연결 논문은 N80, J55, 질화·나노처리 재료와 니켈 도금 재료를 다루고 여러 온도와 CO₂ 분압의 실험을 설명한다.

저장소 기록의 간략 설명만으로는 파일 안의 실제 행, 시험 조건별 범위, 반복시험 구조, 기록이 실험값인지 계산값인지, 현재 프로젝트의 문헌 compilation과 겹치는지 확인할 수 없다. 논문에서 적용한 예측 범위를 저장소 파일의 실험 범위라고 간주하지 않는다. 따라서 이 등록은 **후보 메타데이터**이며 수치 데이터, typed row API, 학습·보정 fixture가 아니다.

## 권리와 재사용 기준

Dryad 정책은 공개 데이터 파일을 CC0 waiver로 배포하며, 제출자가 CC0 배포에 필요한 권리를 보유하거나 확보했음을 보증하도록 요구한다. 따라서 저장소가 선언한 데이터 파일 자체는 재사용 후보로 볼 수 있다. 프로젝트에는 DOI·저자·저장소 출처·라이선스를 남긴다. CC0 선언은 연결 논문, 그 안의 문장·그림·표, 또는 데이터 행이 재인용한 다른 자료까지 포괄하는 것으로 확대 해석하지 않는다.

원본 DOCX는 이번 검토에서 내려받거나 열지 않았으며, 표 값과 문서 콘텐츠를 저장소에 복제하지 않는다. 이후 데이터 접근을 구현한다면 호출자 로컬에서 권리·파일 digest·열 구조를 확인하고 원본을 배포 산출물에서 제외한다. 행 단위 데이터가 제3자 출처를 편집한 것인지 명확하지 않으면 해당 행은 재사용하지 않고 unresolved 상태로 둔다.

## 출처에서 확인한 범위

Dryad의 레코드는 파일을 데이터 접근 대상으로 제시하고 데이터셋을 인용하는 형식을 제공한다. 연결된 논문은 실험을 고온·고압 용기에서 72시간 수행했고 CO₂ 분압 및 온도 영향을 비교했다고 설명한다. 논문 본문에는 20–130 °C 및 12–28 MPa CO₂ 분압에서 모델을 적용한 내용도 있으나, 이는 모든 저장소 데이터 행의 범위를 뜻하지 않는다. 파일의 개별 조건과 관측 종류는 별도 검토 전까지 미확정이다.

## 추후 확인 항목

1. Dryad가 제공하는 최신 파일 목록·버전·파일 단위 권리표시를 확인한다.
2. 파일을 로컬 임시 영역에서만 열어 시트/표 구조, 행 수, 조건 변수, 누락·중복 및 source citations 유무를 요약한다. 행 값과 표 문구는 공개 문서에 기록하지 않는다.
3. 기존 wet-CO₂ compilation 및 소스 크로스워크와 재료/시험/출처 수준의 중복을 점검한다.
4. 각 행을 실험 관측, 재료 분석 또는 계산 출력으로 분리하고, 원 논문에 재수록된 값과 Dryad 원작성 데이터의 권리 경계를 확인한다.
5. 조건과 출처가 충분히 식별된 경우에만 reader 또는 데이터 검증 모델을 별도 제안한다. 이 자료만으로 모델 보정, 예측 정확도, 수명 또는 위험 확률을 주장하지 않는다.

## 근거 링크

- [Dryad 데이터셋 레코드](https://datadryad.org/dataset/doi:10.5061/dryad.fn1r084)
- [Dryad 파일 제출/CC0 안내](https://datadryad.org/help/submission_steps/files)
- [Dryad 데이터셋 정책](https://datadryad.org/publication_policy)
- [Royal Society Open Science 논문 원문(PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6502365/)
