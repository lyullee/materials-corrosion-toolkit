# Zenodo 316L 염화나트륨 분극 자료 판독기

## 자료와 권리

이 모듈은 Zenodo 자료 버전 2, DOI [10.5281/zenodo.15284154](https://doi.org/10.5281/zenodo.15284154)의 316L 스테인리스강 거시 분극 원시 곡선만 읽는다. Zenodo 레코드 API는 공개 접근 및 CC BY 4.0을 표시한다. 출처 표기와 라이선스 링크, 변경 고지를 유지해야 한다. 관련 논문의 데이터 이용 안내는 [논문 DOI](https://doi.org/10.1038/s41529-025-00594-7)에서 확인한다.

원본 압축 파일은 저장소에서 제외되는 `data/raw/zenodo-15284154-316l-pp.zip`에 보관한다. 고정된 파일 크기는 7,170,288 bytes, 제공자 MD5는 `794769a9ba3698c2d0bcfd25c45c11b5`, 로컬 SHA-256은 `006cf12b8cd3e04ec4732114abdcef8cd4a78579add3319919256fe8c2fc8fd1`이다. 판독기는 파일명과 세 해시 기준이 일치할 때만 자료를 연다. 원자료와 행별 관측값을 패키지, 테스트 픽스처, 공개 예제 또는 기본 계산 결과로 복사하지 않는다.

## 포함된 측정 자료

자료 설명은 316L 시편의 NaCl 수용액에서 수행한 거시 동전위 분극 시험 84개를 제시한다. 농도별 곡선은 0.005 M, 0.01 M, 0.05 M에 각각 28개다. 압축 파일의 원시 `.txt` 파일은 농도 폴더 아래에 있고, 각 파일은 `time/s`, `Ewe/V`, `<I>/mA` 세 측정 열을 가진다. 헤더의 마지막 탭은 빈 열 표시이므로 판독기는 헤더를 확인한 뒤 데이터 행의 세 숫자 열만 처리한다. 농도 폴더, 원 파일명, 원 행 순서를 결과에 보존한다. 별도 CSV descriptor 파일은 원시 측정 열이 아니므로 이 판독기에서 읽지 않는다.

## 사용과 한계

`Polarization316LReadAuthorization`에 DOI에 대한 출처 표시, 계산 이용 허용, 로컬 전용 허용을 명시하고 `iter_polarization_316l_raw_rows`에 로컬 압축 경로를 넘긴다. 반복 곡선은 한 연구의 같은 재료·시험 맥락 내 반복이며, 서로 독립적인 84개 재료 시편을 뜻하지 않는다. 이 판독기는 전위 기준을 변환하지 않고, 시편 면적을 이용한 전류밀도 계산을 하지 않으며, descriptor를 재계산하거나 재해석하지 않는다.

측정 열만으로 일반 부식률, 공식/공식전위 기준의 보편 임계값, 현장 부식률, 수명, 합격 판정 또는 고장확률을 추론하지 않는다. 시험 장치와 시편 이력, 면적 보정, 반복 간 독립성, 원본 연구의 분석 정의를 별도로 검토하기 전에는 모델 보정·검증의 독립 표본으로 취급하지 않는다. 공개 배포 전에는 프로젝트의 제3자 자료 고지와 변경 내용 표기를 함께 검토한다.

## 구현 연결

이 모듈은 `matintegrity.polarization_316l_raw_row.v1` 행 계약과 `data.zenodo_316l_polarization_typed_rows` 메타데이터 감사 API를 제공한다. 중앙 레지스트리에 `polarization_316l_typed_rows` 모듈을 등록하고, 데이터셋 ID 및 source ID를 generated catalog/source snapshot에 싱크해야 한다. 공개 JSON Schema는 `Polarization316LRawRow`, `Polarization316LReadAuthorization`, `Polarization316LArchiveAuditRequest`에 대해 생성한다. 스키마 및 레지스트리 연결 전에는 `matintegrity.evaluate`의 공개 모델 API에서 자동 발견된다고 간주하지 않는다.
