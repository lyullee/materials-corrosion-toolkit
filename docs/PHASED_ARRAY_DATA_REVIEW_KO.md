# 위상배열 초음파 공개자료 검토

검토 기준일은 2026년 10월 27일이다. 공개 권리, 실제 물리 시편, 원 acquisition, augmentation,
provider partition과 독립 truth를 분리했다.

## ML-NDT

공식 GitHub 저장소 `iikka-v/ML-NDT`의 고정 commit
`6fb6aee456e64add656d1beb4e414639b13df278`은 LGPL-3.0을 표시한다. Git tree 전수 metadata에서
data blob은 804개, 2,628,979,711바이트이며 training 199 batch와 validation 2 batch가 있다. 각 batch는
`.bins`, `.meta`, `.jsons`, `.labels` 한 세트이고 `.meta`는 UInt16 `256 x 256 x 100`을 선언한다.

연계 공개 연구에 따르면 원 acquisition은 한 316L austenitic butt-weld pipe의 1.6, 4.0, 8.6 mm
thermal-fatigue crack 세 개, TRS phased-array와 한 선택 각도에서 왔다. 공개 영상은 virtual-flaw
implantation/scaling, rectification, crop과 256×256 downsampling을 거쳤다. 따라서 20,100개의 공개
영상 또는 201개 batch를 독립 시편·독립 물리 crack이나 raw FMC로 세지 않는다. provider training/
validation 이름도 source physical independence를 증명하지 않는다. 원 저장소 전체는 공개 배포물에
복제하지 않고 catalog에는 metadata-only로 기록했다. `ml_ndt_data.py`의 local-clone reader는 고정
commit을 호출자가 확인한 경로만 읽고 네 sidecar/payload 정합성과 SHA-256을 감사한다. 이는 취득이나
재배포 기능이 아니며, byte order가 meta에 없다는 사실도 유지한다.

## Strathclyde probe-localization 자료

University of Strathclyde 공식 record `10.15129/bfb5a77d-dabe-4be4-82c9-b10e8c237dea`는 CC BY 4.0,
98.9 MB `PAUT.zip`과 weld-material localization 목적을 명시한다. landing page에는 provider checksum이
없고 현재 자동 요청은 Cloudflare 403 challenge를 받으므로 취득 성공으로 세지 않는다. lawful download가
가능해지면 probe/wedge/law/encoder/시편과 image mapping을 먼저 감사한다.

## 보류 자료

- TYUST-PAUT는 논문 승인 뒤 공개 예정이며 현재 신청·승인 방식이라 공개 재현 자료로 등록하지 않는다.
- Bristol crack-characterization 자료는 Non-Commercial Government Licence라 공개·상업 겸용 배포
  목표의 기본 자료로 선택하지 않는다.
- Zenodo acoustic-lens pipe 자료는 12.6 GB지만 record 화면과 API에서 명시적 license가 확인되지 않아
  권리 확정 전 자동 취득하지 않는다.

현재 계약 검증은 authored arithmetic identity다. 실제 probe field, wedge/focal-law, encoder와
waveform reader, TFM reconstruction 및 physical-specimen holdout 검증은 별도 후속 작업이다.
