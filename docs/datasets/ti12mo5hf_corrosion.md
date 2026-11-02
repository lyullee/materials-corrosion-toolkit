# Ti-12Mo-5Hf 산화물/부식 공개 데이터: 로컬 사용 경계

## 출처와 권리

- 데이터셋: [Zenodo DOI 10.5281/zenodo.19462164](https://doi.org/10.5281/zenodo.19462164)
- 공식 레코드: <https://zenodo.org/records/19462164>
- 레코드에 표시된 라이선스: Creative Commons Zero v1.0 Universal (CC0-1.0)
- 제공자: Sotniczuk 등, 2026년 공개 데이터 기록
- 공개 소스/패키지에는 원본 ZIP과 README, 측정 행·이미지·표를 포함하지 않습니다. 현재 작업 PC의 무시(ignored) 처리되는 `data/raw/zenodo-ti12mo5hf-oxygen-corrosion/` 아래에 로컬 사본이 있습니다.

CC0 표시는 해당 데이터 기록의 재사용 근거로만 기록합니다. 제3자 이미지·문서의 별도 권리, 논문 본문/그림의 라이선스, 데이터에 포함되지 않은 자료의 권리를 확장해서 주장하지 않습니다. 배포 전에는 Zenodo 레코드의 현재 권리 정보와 프로젝트의 배포 정책을 다시 확인하고, 학술 이용 시 원 저작자를 인용합니다.

## 제공자 메타데이터에서 옮긴 실험 범위

제공자 README가 식별하는 합금 라벨은 `Ti12Mo5Hf`와 `Ti12Mo5Hf0.3O`입니다. 전기화학 실험은 PBS에 33 mM H2O2를 넣은 조건에서 OCP 1200초, Ag/AgCl 기준 -1 V 정전위 구간 1200초, 이어지는 OCP 관측으로 설명되어 있습니다. 별도 침지 ICP-MS 관측 시점은 2시간, 24시간 및 7일입니다. 자세한 합금 제조·측정 파일 설명은 현지 README에서 확인하십시오.

위 문장은 제공자 기술 내용을 요약·재표현한 것이며 측정값이나 연속 이력의 재구성이 아닙니다. 7일은 168시간으로 표시한 동일 시점을 뜻합니다. 두 실험 계열의 시간축을 합치지 않으며, 엑셀 열·파일명에서 합금/반복/시점 의미를 추정하지 않습니다.

## 현재 API와 제한

모듈 `matintegrity.ti12mo5hf_corrosion_data`는 아래를 제공합니다.

- `declared_conditions()`: README에서 명시한 조건 설명을 provenance-bound 계약으로 반환합니다.
- `audit_local_archive(path)`: 정확한 파일 크기와 Zenodo 게시 MD5를 확인하고 ZIP 멤버 이름·확장자·압축/비압축 크기·CRC와 컨테이너 SHA-256을 기록합니다. 압축 해제는 하지 않습니다.
- `Ti12Mo5HfArchiveAuditRequest` 및 `evaluate_archive_audit_request()`: 로컬 경로, 호출자가 고정한 SHA-256, 계산 사용 승인, 로컬 처리 승인 조건을 받아 `Calculation`으로 감사 결과를 반환합니다.
- `specifications()`: 선택적으로 등록할 수 있는 `data.zenodo_ti12mo5hf_archive_audit` ModelSpec을 노출합니다. 이 변경은 중앙 registry에 자동 등록하지 않습니다.
- 계약 ID: `matintegrity.zenodo_ti12mo5hf_condition.v1`, `matintegrity.zenodo_ti12mo5hf_archive_audit.v1`, `matintegrity.zenodo_ti12mo5hf_archive_audit_request.v1`.

ZIP 내부 표/워크시트의 컬럼 스키마는 이 구현에서 아직 매핑하지 않습니다. 파서 확장 전에는 원 자료의 단위, 결측 처리, replicate와 시편 식별, 전위·전류·용출률 정의를 각각 검토하고 버전이 지정된 스키마로 선언해야 합니다. 이 API는 부식률 계산, 합금 성능 순위, 수명 예측, 재료 적격성 판정, 불확도/규격 적합성 판정을 수행하지 않습니다.

아카이브 감사는 로컬에서만 동작합니다. 압축 폭탄을 제한하는 멤버 개수/확장 크기 상한을 가지며 경로 탈출 이름을 거부합니다. ModelSpec 경로에서는 계산 사용 및 로컬 전용 처리 승인을 명시해야 하며, 입력 SHA-256이 감사 결과와 다르면 실패합니다. 파일이 없거나 게시자 고정 MD5·바이트 수와 다르면 fail-closed 합니다. 원본을 다운로드하거나 네트워크에 접속하지 않습니다.

## 로컬 파일 설치

공식 Zenodo 레코드에서 다음 파일을 별도로 내려받아 지정 위치에 저장합니다.

```text
data/raw/zenodo-ti12mo5hf-oxygen-corrosion/Data_Zenodo_EA2026.zip
data/raw/zenodo-ti12mo5hf-oxygen-corrosion/README_EA2026.txt
```

공식 게시자가 기록한 ZIP 값은 47,558,332 bytes, MD5 `36611789e98e7608a99841541447a918`입니다. 확보한 로컬 ZIP의 SHA-256은 `0d50714744e0c6b1b2359beedde96f6b8842ad45ba19c6fcc224b90fd95d6915`입니다. README 값은 4,175 bytes, MD5 `17d39381ff21630d4cdbf1f6e9b101cf`, 로컬 SHA-256은 `71c6d8984747a6342751733d60a8b2f39cc273d5b9a8605f2f1de5e9d352017c`입니다. ZIP과 README의 실제 사본은 로컬 ignored 경로에만 있고 GitHub 공개 파일이 아닙니다. SHA-256는 동일성 추적용이며 물리적 해석이나 품질 검증을 뜻하지 않습니다.

압축 해제 없이 수행한 고정 archive audit에서 ZIP CRC/내용은 재계산하지 않고 central-directory member 목록만 확인했습니다. 51개 member와 총 130,696,187 bytes의 선언된 확장 크기가 보였고, AESEC/ICP-MS 워크북·신호, EBSD, SEM/TEM/STEM 및 TEM-EDS 계열 파일이 포함됩니다. 시트, 측정 셀, 이미지 픽셀은 열지 않았으며 구성이나 단위, replicate 의미도 추론하지 않았습니다.

## 다른 모듈과 연결

반환되는 Pydantic 계약은 외부 위험성 평가, 손상 메커니즘, Bayesian calibration 또는 FTA 계층의 입력 provenance로 연결할 수 있습니다. 데이터 집계/예측을 이 데이터 모듈에 넣기보다, 각 downstream 모델이 필요한 물리 변수와 단위, 변환 방법, 불확도를 별도 계약으로 요구하도록 합니다. central catalog/registry 등록은 별도 통합 변경으로 수행해야 합니다.

## 다음 구현 단계

1. 새 작업 환경에서 공식 Zenodo 원본을 받아 게시자 byte count/MD5와 로컬 SHA-256을 대조하고, ignored `data/raw` 아래에만 보관합니다.
2. 감사 API로 bounded member inventory와 archive digest를 남깁니다. 현재 고정본의 inventory는 이 문서에 요약돼 있습니다.
3. README가 설명하는 파일을 기준으로 워크북/시트 헤더만 조사합니다.
4. 각 표의 관측량·단위·반복·결측 규칙을 독립 검토한 후, 명시적 컬럼 매핑을 받는 bounded reader를 추가합니다.
5. 원자료 행을 복제하지 않는 synthetic example와 별도 검증 계획을 작성합니다.

