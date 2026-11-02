# 316L 준안정 공식 chronoamperometry 데이터 어댑터

## 데이터 출처와 이용 조건

Mendeley Data 버전 1의 [자료 레코드](https://doi.org/10.17632/z43xxs7hvv.1)는 316L 스테인리스강의 potentiostatic 및 potentiodynamic 시험, 그리고 potentiostatic 시험 중 동시 취득한 in-situ 영상에 관한 원자료를 제공한다. 저장소 페이지와 공개 dataset metadata API는 CC BY 4.0을 명시한다. 이 라이선스에 따라 자료 출처, 라이선스 링크, 변경 여부를 표시한다. 해당 연구 논문은 [Corrosion Science 논문 DOI](https://doi.org/10.1016/j.corsci.2020.109004)이다.

이 코드베이스에는 영상 파일을 복사하지 않는다. MPR 측정 파일 세 개만 `.gitignore` 적용 대상 `data/raw/mendeley-z43xxs7hvv/`에 둔다. 각 파일은 provider metadata가 제공한 크기와 SHA-256을 판독기에서 고정 검증한다. 측정 행, 영상 프레임, 논문 그래프 점을 공개 예제·픽스처·패키지 자산으로 복제하지 않는다.

## 원자료 파일과 형식

자료 레코드의 측정 파일은 `Sample_I_chronoamperometry.mpr`, `Sample_II_Chronoamperometry.mpr`, `Sample_III_Chronoamperometry.mpr`이다. 파일은 BioLogic EC-Lab의 이진 MPR 형식이며, 논문 원자료 페이지는 재현에 해당 계측기 소프트웨어를 사용한다고 안내한다. 각 파일의 제공자 파일 ID, 바이트 크기, SHA-256은 코드의 `_ASSETS`와 `_FILE_IDS` 상수에 기록돼 있다.

`.mpr` 내부 측정 열은 사용한 기법과 파일 버전에 따라 달라질 수 있다. 따라서 어댑터는 임의로 열 이름이나 단위를 추정하지 않는다. 호출자는 검토한 MPR 디코더를 `decoder` 인자로 주입하고, 디코더가 반환하는 각 행을 시간·전위·전류 값과 각 값의 명시 단위로 변환해야 한다. `parser_name`과 `parser_version`으로 디코더 계보를 남긴다. 이 프로젝트는 MPR 파서 코드를 복사하거나 GPL 파서를 직접 의존성으로 묶지 않는다. 다른 parser를 선택할 경우 그 도구의 라이선스와 배포 조건을 별도로 확인한다.

## 계약과 해석 제한

`MetastablePittingReadAuthorization`은 CC BY 출처 표시와 로컬 계산 이용을 명시한다. `iter_mendeley_316l_metastable_pitting_rows`는 세 원본 파일의 SHA-256을 먼저 확인한 뒤, 호출자 디코더의 행 순서를 보존하는 `MetastablePittingMeasurementRow`를 생성한다. 행 계약은 디코딩 값·단위, 원본 파일, 시편 라벨, 행 순서, parser 식별, authorization digest, 출처 증거를 함께 기록한다.

이 자료는 한 연구의 세 시험 파일이지, 모집단 수준의 독립 표본이나 316L 일반 부식률의 교정 집합이 아니다. 연구 결과는 하나의 current transient와 하나의 고유한 pit event 또는 pit site를 항상 일대일 대응시킬 수 없으며, 전기화학 전류로 계산한 용해량과 영상·실측 손상량이 일치한다고 가정할 수 없음을 보인다. 따라서 이 어댑터는 전위 기준을 바꾸거나, 면적 기준 전류밀도·pit event label·물리적 금속 손실을 계산하지 않는다. 시험 이력과 reference electrode, specimen area, 영상 동기화, 반복 설계를 별도 검토하기 전에는 위험성·수명·합격·고장확률 평가에 직접 입력하지 않는다.

## 중앙 API 연결

이 모듈은 `matintegrity.mendeley_316l_metastable_pitting_row.v1` 계약과 `iter_mendeley_316l_metastable_pitting_rows` Python API를 제공한다. 레지스트리에 등록할 evaluator는 현재 정의하지 않는다. 중앙 schema exporter에 `MetastablePittingMeasurementRow`, `MetastablePittingReadAuthorization`, `MprDecodedRecord`를 추가하고, dataset/source manifest를 generated catalog snapshot과 동기화한다. 호출 API 사용 시 MPR decoder와 열·단위 매핑을 명시적으로 주입해야 한다.
