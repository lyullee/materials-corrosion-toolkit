# 두 신규 계산기의 한강 증분 검증

기존 한강 job `1185188`의 source snapshot 이후 추가된 두 계산기를 별도 snapshot과 별도 job으로 검증한다. 기존 job과 그 staging/환경/결과는 변경하지 않는다. 전체 pytest shard나 집중 회귀 묶음을 다시 제출하지 않는다.

대상은 `chemistry.planar_scale_diffusion_reaction_history`와 `fabrication.gasket_leakage_map_fit`이다. 계수와 입력은 모두 검증용 합성값이며 실험 관측값, 권장값 또는 재료 적용 근거가 아니다.

`scripts/hpc_incremental_20261030.py`가 다음 다섯 작업을 제공한다.

- `scale`: 양/음/0의 구동력에 대한 SciPy ODE 수치해와 폐형식의 비교, 완전 소진 시각, 검토 누락 게이트, 온도 지원범위 거부를 검사한다.
- `fit`: 알려진 양의 bilinear 함수를 복원하고, holdout 값 변경이 fitted map에 영향을 주지 않는지, source partition 위반 거부와 rank 부족 상태를 검사한다.
- `schemas`: 네 신규 계약의 현행 `model_json_schema()`와 저장된 공개 JSON schema를 대조한다.
- `catalog`: 두 계산기의 registry/schema/상위 capability 연결과 설치용 catalog 동기화를 대조한다.
- `source`: 두 신규 모듈 AST와 공개 allowlist의 source tree digest를 확인한다.

각 작업은 계산노드에서 별도 scratch 사본으로 실행하며 개별 JSON 결과, 출력 log와 결과 해시를 남긴다. 다섯 작업은 독립적으로 병행한다. 실패한 작업을 통과로 바꾸거나 제거하지 않는다. 결과가 없는 작업은 완료로 집계하지 않는다.

각 실행의 실제 archive SHA-256, 파일별 SHA-256, 원격 stage, job ID와 제출 상태는 `hpc-results/hangang-incremental-*/dispatch.json`이 기록한다. 이 문서는 결과 보고서가 아니다. Schema/catalog 재생성은 로컬 정적 산출물 갱신이며 모델 계산 검증과 구분한다. Source snapshot을 만든 뒤 발생한 구현 변경은 후속 증분으로 다룬다.

제출은 기존 CPU 공유 연결을 `run.sh cpu`로만 사용한다. `5thEx_cpu`의 사용자 QoS 제출 한도에 여유가 없으면 로컬 비동기 dispatcher가 capacity를 확인하고 여유가 생겼을 때 한 job을 제출한다. 다른 프로젝트 job은 변경하지 않으며 새 SSH나 인증은 시도하지 않는다. 검증 job의 종료를 기다리지 않고 개발을 병행한다.

이 검사들은 제한된 수학/소프트웨어/계보 계약을 평가한다. 서비스 데이터 calibration, 독립 실험 검증, scale 보호성·부식속도 또는 가스켓 sealing acceptance의 qualification을 제공하지 않는다.
