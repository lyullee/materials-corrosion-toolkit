# Scale 소진 underflow 전용 소형 증분

이 snapshot은 최신 `scale_reaction_demand_balance.py`, 직접 import에 필요한 최소 package 파일, 해당 모델 설명서와 두 schema, MIT 고지 및 전용 검증 명령만 담는다. 전체 저장소 snapshot이나 full pytest가 아니다. 기존 scale-demand/wave2 및 이전 job과 stage는 변경하지 않는다.

`scripts/hpc_scale_underflow_delta_20261031.py`의 `numeric`과 `static` 두 독립 작업을 병행한다. 양의 초기 두께와 매우 큰 소비항에서 수학적으로 양인 소진 시각이 float 0으로 내려가는 두 경우(공급 0/공급 양수)를 계산이 거부하는지 확인한다. 정상 소진 시각은 선형해 또는 별도 quadrature와 비교하고, 두 계수가 모두 0일 때 작은 두께를 그대로 보존하는지 확인한다. 모두 합성 수치 경계 사례다.

Premature zero-thickness guard는 source AST 존재를 확인한다. 이 묶음에서 해당 guard가 실제로 발동하는 수치 입력을 검증했다고 주장하지 않는다. 두 exported schema와 runtime contract 및 snapshot 파일별 hash를 대조하며 raw/evidence를 넣지 않는다.

정확한 파일 목록·archive SHA-256·stage·job ID는 `hpc-results/hangang-scale-underflow-*/dispatch.json`에 보존한다. 사용 중인 CPU 공유 연결의 `run.sh cpu`만 사용하고 QoS capacity가 없으면 비동기 제출 dispatcher가 대기하는 동안 개발을 계속한다. 기존 job이나 다른 프로젝트 작업은 변경하지 않고, 새 인증은 시도하지 않는다.

검증 결과가 생기기 전에는 통과나 물리적 validation으로 집계하지 않는다. 이 작은 dependency closure를 전체 API registry/catalog 검증의 근거로 사용하지 않는다.
