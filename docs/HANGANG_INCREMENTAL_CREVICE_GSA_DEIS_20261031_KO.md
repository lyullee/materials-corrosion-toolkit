# Crevice·GSA·DEIS 증분 검증 작업

이 묶음은 기존 가스켓·평면 scale 검증과 별도 source snapshot 및 별도 job을 사용한다. 기존 job `1185188`과 앞선 incremental dispatcher/snapshot을 변경하지 않는다. 전체 pytest, 전체 모델 예제 또는 이전 계산 사례를 반복하지 않는다.

검증 명령은 `scripts/hpc_incremental_crevice_gsa_deis_20261031.py`이며 여섯 독립 작업을 제공한다.

1. `crevice`: 선형 가역 A↔B 반응과 두 구간의 mixed-volume exchange를 BDF/Radau로 풀고, 별도의 확장 행렬 지수해와 농도·exchange ledger·반응 extent를 대조한다. 0/중간/빠른 반응계수와 검토 누락 게이트를 포함한다. 합성 원소/전하 수지는 실제 화학종의 반응성 증거가 아니다.
2. `gsa`: 명시된 finite plane에서 NumPy tensor contraction으로 독립 계산한 식과 결과를 비교한다. 순수 축 및 tensor shear의 알려진 값, 동일 회전에 대한 값의 보존, planes×samples 예산 거부와 미폐합 cycle 거부를 검사한다. 수명이나 재료 qualification은 평가하지 않는다.
3. `deis`: 데이터 catalog의 허용된 CC0 Zenodo asset을 계산노드의 별도 private-data 경로에 byte 상한을 두고 취득한다. Source snapshot에는 raw/evidence를 넣지 않는다. ZIP 크기·SHA-256·공급자 MD5·정확한 member 집합·member SHA·54×8640 matrix schema·stream 순서/값을 대조하고 변조 manifest를 거부하는지 확인한다. 결과에는 hash와 형상만 남기고 pointwise 값은 출력하지 않는다. 축/단위/스펙트럼 경계 또는 부식 해석을 추정하지 않는다.
4. `schemas`: 아홉 신규 계약의 실행 가능한 schema와 저장된 JSON을 대조한다.
5. `catalog`: 세 모델의 registry/schema/상위 capability/source ID 연결과 설치용 catalog 동기화를 대조한다.
6. `source`: 세 구현 파일 AST, 공개 allowlist source digest와 source tree 내 raw archive 부재를 확인한다.

DEIS pinned asset은 `10.5281/zenodo.10482561`의 `Dataset_CorSci.zip`, 30,886,921 bytes, SHA-256 `38d69f883ede6caaf988c3af9dd56f34c071f97b668d93fad778428c26dbed7c`다. 네트워크/취득 실패를 importer 검증 성공으로 처리하지 않는다. 다운로드는 검증 준비 단계의 명시적 동작이며 importer API 자체에는 네트워크 동작을 추가하지 않는다. 원자료는 source archive나 공개 배포물로 복사하지 않는다.

작업별 scratch를 분리하고 최대 여섯 작업을 한 allocation에서 병행한다. Runtime freeze, task log, JSON 결과, 결과 hash 및 summary를 보존한다. 실제 source archive SHA와 파일별 hash, stage, task 선택 및 job ID는 `hpc-results/hangang-incremental-wave2-*/dispatch.json`에 기록한다. Source snapshot 이후 수정은 별도 후속 묶음으로 추적한다.

기존 CPU 공유 연결의 `run.sh cpu`만 사용하고 재인증하지 않는다. 사용자 QoS가 꽉 차면 로컬 비동기 capacity dispatcher가 허용 슬롯을 기다리는 동안 개발을 계속한다. 다른 프로젝트 job이나 앞선 snapshot을 변경하지 않는다. 이 문서는 검증 결과가 아니며 결과가 없는 항목을 완료로 집계하지 않는다.
