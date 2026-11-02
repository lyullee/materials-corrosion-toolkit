# 방사선투과검사 공개자료 검토

검토 기준일은 2026년 10월 27일이다. 공개 주소가 있다는 사실과 공개 배포 가능한 권리, 물리 시편의
독립성, 촬영조건 및 결함 truth는 서로 다른 항목으로 판정했다.

## X-weld Zenodo 후보

Zenodo record `10.5281/zenodo.10618962`는 API metadata에서 open access와 Apache-2.0을 표시하며,
`my_dataset.zip` 475,303,436바이트와 MD5 `ab70472fc2229ea07d46e37c18c974fe`를 제공한다. 그러나
description, 시편 ID, source-detector 기하, detector, exposure, IQI, label 정의와 독립 truth가 없다.
따라서 `data/catalogs/datasets.json`에 기본 비활성 선택 자료로만 등록했다. 원자료를 받더라도 해시와
file-level provenance 검토 전에는 검출·크기·POD·합격 검증에 사용하지 않는다.

## 제외 또는 보류한 후보

- GDXray 공식 조건은 연구·교육 목적의 무료 사용만 허용하고 재배포와 상업 이용을 금지한다. 공개
  패키지나 자동 다운로드 catalog에 넣지 않는다.
- RIAWELC 저장소는 24,407개의 224×224 PNG와 네 class를 설명하지만 LICENSE 파일이 없고 README의
  무료 공개 표현만 있다. 명시적 재배포·상업 이용 조건을 확인하기 전에는 catalog에 넣지 않는다.
- WDXI를 가리키는 문헌 링크는 현재 표면 결함 dataset 링크 모음으로 redirect되며, 그 저장소의 MIT
  라이선스는 연결된 제3자 dataset 권리까지 자동 확장하지 않는다.
- SWRD 공개 저장소의 안내는 라이선스 문구가 추후 교체되어야 한다고 명시하므로 권리 확정 자료로
  취급하지 않는다.

현재 공개 권리, 물리 시편 ID, 촬영기하, 지시 annotation, 독립 reference truth를 동시에 갖춘 RT 자료는
확보하지 못했다. 이 공백 때문에 이번 단계의 검증은 독립적으로 작성한 pinhole 수학 identity와 계약
검사이며 실험 검증이 아니다. 후보가 추가되면 source/image/crop/physical-specimen 계층을 먼저 감사한
뒤 calibration과 holdout을 물리 시편 단위로 분리한다.
