# 한강 독립 검증 작업 제출 상태

현재 source snapshot의 원격 전송과 SHA-256 대조를 마쳤다. 계산 작업은 아직 제출되지 않았다. 로컬 비동기 dispatcher가 사용자 QoS 제출 여유를 확인한 뒤 한 개의 병렬 bundle을 제출하도록 실행 중이다. 개발 작업은 이 대기와 독립적으로 계속한다.

- 원격 staging: `/scratch/HPC_USER/matintegrity-20261030T144649Z`
- 고정 archive SHA-256: `021ec1d43427fbb3d4735c9db10613316927a0e305afa88e862c8edb236aaad7`
- source 선택: 기존 공개 allowlist, 2,162개 파일, gzip 5,124,052 bytes. Raw/derived/evidence와 제한된 상위 폴더 자료는 전송하지 않았다.
- 제출 receipt: `hpc-results/hangang-dispatch-20261030T144649Z/dispatch.json`. 파일별 해시, 선택 task indices, 마지막 scheduler 확인 및 발급 job ID를 보존한다.
- 현재 account: `na1620`; 허용 CPU partition: `5thEx_cpu`. `showappl`의 재료공학/in-house 코드 분류를 사용한다.
- Scheduler QoS는 사용자당 제출/실행 5개 제한이다. 확인 시 다른 작업 5개가 점유 중이며 이 프로젝트 dispatcher는 이를 취소하거나 수정하지 않는다.

기존 manifest 142개 중 full pytest shard 8개와 독립 command 49개를 선택했다. Full shard와 겹치는 집중 pytest 85개는 이번 묶음에서 중복 실행하지 않는다. 선택 indices는 `0-51,55,60,77,126,138`이다. 기존 source manifest는 변경하지 않았다. 따라서 기존 142개 전체를 요구하는 collector를 이 subset 결과에 그대로 적용하면 누락을 보고하는 것이 정상이다. 이번 묶음의 완료 조건은 receipt의 57개 선택 indices와 task별 결과를 대조해야 한다.

한 개의 allocation에서 16개 task를 병행한다. Task마다 기존 Slurm runner를 별도 scratch 경로로 실행하고 task별 `result.json`과 launch log를 남긴다. 환경 준비도 계산노드 allocation에서 수행한다. Runtime freeze는 staging root에 기록한다. 전체 bundle log는 `bundle-JOB_ID.log`, task 결과는 `project/hpc-results/JOB_ID/`에 생성한다. 실패 task는 제외하거나 통과로 바꾸지 않는다. 원자료가 필요한 작업은 데이터 미전송으로 실패/미완료할 수 있으며 별도 원자료 확보 과제다.

Dispatcher는 공유 연결만 사용하고 새 SSH/인증을 시도하지 않는다. 60초 간격으로 scheduler capacity를 확인하며 슬롯이 열리면 제출하고 종료한다. 공유 연결 실패 시 자동 재로그인을 시도하지 않는다. 제출 여유가 8시간 내 열리지 않으면 제출하지 않은 상태로 종료한다. 최신 실제 상태와 job ID는 문서의 고정 설명보다 receipt와 scheduler를 우선한다.

계산·수치 검증 결과는 아직 없다. 전체 범위 완료나 물리적 validation을 증명하는 기록이 아니다.
