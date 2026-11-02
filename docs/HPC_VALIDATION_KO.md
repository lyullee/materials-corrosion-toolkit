# 누리온·HPC 병렬 검증

## 현재 검증 묶음

현재 manifest에는 142개 작업(배열 인덱스 0–141)이 있다. `scripts/validate_hpc_manifest.py`와 `scripts/validate_pbs_manifest.py`는 작업 정의, 배열 범위 및 동시성 상한을 점검한다. DefDAP 1.3 기반 Oxford EBSD reader 회귀는 batch107이고, 별도 reader validation command가 Aalto 공개 ZIP의 세 map shape·grid-step 숫자·label histogram 폐합을 확인하도록 등록했다. 실제 원자료 reader command는 `ebsd` 선택 extra가 필요하므로 누리온 venv는 `python -m pip install -e '.[science,thermo,dev,ebsd]'`로 준비해야 한다. 검증은 형식 판독과 집계 진단에 한정하며 phase identity·physical grid unit·ROI·불확도를 승인하지 않는다. 계산/회귀 작업은 아직 제출하지 않았다.

batch65는 AquaSolDB 고정 archive digest·CSV schema, CO₂ record filtering, flags/metadata 보존, digest/schema 거절과 안전하지 않은 ZIP 경로를 검사하도록 등록했다. 테스트는 로컬과 누리온 모두 아직 실행하지 않았다.

batch64는 고정 fugacity 탄산계 평형의 합성 종분포, 알칼리도 민감도, 검토 게이트 및 온도·용매 적용 경계를 검사하도록 추가했다.

`hpc/task_manifest.json`은 전체 pytest node ID를 8개 결정론적 shard로 나누고, 집중 pytest와 독립 검증·원자료 감사를 추가한다. 현재 140개 작업은 shard 8개, 집중 pytest와 독립 검증 command로 구성된다. `scripts/validate_hpc_manifest.py`는 manifest 구조 및 PBS/Slurm 런타임 index guard를 확인한다. 제출자는 `0–139` 범위의 scheduler array를 지정해야 하고 각 실행 script가 manifest 상한을 다시 검사한다. Neuber-to-strain-life 연결 회귀는 batch50, PBS 병렬 bundle 범위 회귀는 batch51, 결과 collector 무결성 회귀는 batch52, 균일/시간·공간 변화율장 프로파일 용량 회귀는 batch53과 batch54, chronoamperometry 극성 전하 적분 회귀는 batch55, 직교 불균일 두께 지도와 유한저항 갈바닉 결합은 각각 batch56·57, 탄산계 알칼리도 종분포는 batch58, Davies 활동도 계수와 이온목록 전하수지는 batch59에 있다. batch60은 CC BY CT110 용접금속/모재 부식속도 대비 계산 회귀이며, batch61은 설치 자료 reader·출처·해시·typed adapter 회귀다. batch62는 사용자 반복 시편 입력의 부식속도 요약 계약과 분위수 계산 회귀다. batch63은 선택 경험 분위수로 선형 두께 시나리오를 만들 때의 provenance와 review gate 회귀다. batch71은 완전 rate-scenario 입력·가중 초과질량·두께 소진 상태를, batch72는 HPC manifest 사전검사를, batch73은 caller 기준에 대한 under-deposit 환경이력 comparison을 검증하고, batch97은 storage-preservation 시간축의 uncovered/invalid 구간·inspection ID 연결·한계 이탈 타임라인을 검사하고, batch98은 모든 task 결과의 release allowlist 전체(코드·문서·검증 fixture·공개 카탈로그)를 기준으로 source-tree SHA-256과 파일 수를 기록하고 focused pytest 경로의 존재 및 project-root containment를 검사한다. 이는 배포 가능한 snapshot과 HPC 실행 입력을 같은 파일 집합으로 묶는다. PBS와 Slurm 모두 raw/derived/evidence를 scratch로 복제하지 않고 원 project 경로를 링크한다. 결과 수집기는 manifest와 함께 source digest도 단일값으로 강제한다. batch99는 확장 요청서 색인 완전성을, batch100은 데이터 카탈로그의 권리·취득정책·제공자 checksum 상태와 로컬 파일 대조를, batch101은 선택 허용 자산의 명시적 취득 조건을, batch102는 권리 검토 날짜 freshness 회귀를, batch103은 원본/패키지 카탈로그 동기화를 검사한다. batch107 Oxford EBSD reader adapter 회귀와 실제 archive reader validation command, batch108 상지도 topology descriptor 회귀와 batch109 Morrow/SWT 평균응력 수명 회귀와 batch110 pCN subset simulation 회귀를 추가해 manifest는 142개 작업(0–141)이다.

이전 누리온 작업 `24229540.pbs`는 구형 소스 스냅샷으로 종료했고, 당시 2,333개 테스트 중 25개 실패와 exit status 123을 기록했다. 현재 수정 사항은 그 작업에 포함되지 않는다. 이전 127개 작업 묶음은 manifest와 예제 구조만 정적으로 확인했으며 회귀 실행 및 누리온 제출은 하지 않았다. 결과를 검토할 때는 이번 manifest digest와 source revision이 결과 파일에 기록된 값과 맞는지 확인한다.

## PBS 한 노드 병렬 실행

`hpc/pbs_bundle.sh`는 PBS 노드 하나를 요청하고 작업 목록을 manifest에서 읽는다. 기본 병렬도는 16개이며 `MATINTEGRITY_PBS_WORKERS`로 1–64 사이에서 조정한다. 각 task는 독립 project snapshot에서 실행되고 결과는 `hpc-results/<PBS_JOBID>/task-<index>/`에 기록된다. 모든 작업이 끝나면 bundle이 collector를 실행해 누락·실패·manifest 불일치를 집계한다.

클러스터에 저장소 스냅샷과 의존성이 준비된 뒤 실행 환경을 지정한다.

이 manifest 전체는 `science`, `thermo`, `dev` 선택 의존성을 포함한 환경에서 실행한다. 특히 CO₂ fugacity validation은 CoolProp을 필수 검사한다. 실행 환경을 만들 때 `python -m pip install -e "[science,thermo,dev]"`를 사용하고, 실행 전 `python -c 'import CoolProp; print(CoolProp.__version__)'`로 provider 설치를 확인한다. HPC task는 의존성을 자동 설치하거나 네트워크를 사용하지 않는다.

```bash
export MATINTEGRITY_PROJECT=/path/to/matintegrity
export MATINTEGRITY_VENV=/path/to/venv
export MATINTEGRITY_PBS_WORKERS=16
cd "$MATINTEGRITY_PROJECT"
qsub hpc/pbs_bundle.sh
```

PBS queue, account, module, walltime과 노드 자원은 대상 계정 정책에 맞게 제출 전에 검토한다. 이 문서는 계정값이나 인증정보를 저장하지 않는다. 이 저장소의 `pbs_bundle.sh` header는 프로젝트 사용자가 확인해야 하는 site-specific 설정을 포함한다.

## PBS array 또는 Slurm array

`hpc/pbs_array.sh`는 PBS array index 하나당 manifest task 하나를 실행하고 최대 16개 array element를 동시 실행한다. 모든 element가 끝난 뒤 `hpc/pbs_collect.sh`를 별도 collector job으로 실행한다. `hpc/slurm_array.sh`도 manifest task를 하나씩 실행한다. 작업 수가 바뀌면 submit command의 배열 상한을 최신 manifest와 맞춘 뒤 preflight를 통과시킨다. 실행 script는 index가 manifest 작업 수 안에 있는지 재확인한다.

```bash
"$MATINTEGRITY_VENV/bin/python" scripts/validate_hpc_manifest.py
qsub hpc/pbs_array.sh
# array 종료 후 scheduler가 반환한 base job ID를 지정
export MATINTEGRITY_ARRAY_JOB_ID=JOB_ID
qsub hpc/pbs_collect.sh
```

## 결과 형식과 집계 조건

`scripts/hpc_run_task.py`는 task index/name, manifest SHA-256, Python·플랫폼·핵심 package 버전, 각 subprocess의 명령·종료코드·출력 digest를 `result.json`에 쓴다. pytest 작업은 `junit.xml`도 생성한다. collector는 기대된 모든 index의 결과가 있는지, 결과 schema와 index/name/digest가 일치하는지, command 수와 명령별 종료코드가 task 상태와 맞는지 확인한다. pytest 작업의 JUnit 누락·손상도 실패로 집계한다. 누락이나 불일치가 하나라도 있으면 summary의 `problems`와 `failed_task_indices`에 남기고 종료코드 1을 반환한다.

```bash
"$MATINTEGRITY_VENV/bin/python" scripts/hpc_collect.py \
  --results-dir "hpc-results/JOB_ID"
```

결과는 `hpc-results/` 아래에 두며 공개 배포물에는 넣지 않는다. private raw/derived/evidence data는 HPC 정책이 허용하는 제한 storage에 준비한다. task 사본에서는 이 세 경로를 제외하고, 원래 project에 존재할 때만 같은 상대경로의 symlink로 연결한다. 결과 archive에는 원자료를 복사하지 않는다.

## 균열성장 시나리오 병렬 map/reduce

`fracture.tabulated_crack_growth_scenario_ensemble`의 각 완전입력 행은 서로 독립적으로 계산할 수 있다. `scripts/crack_scenario_job.py`는 안정적인 0-based index 한 개를 평가해 scenario ID, deterministic-input SHA-256, evaluator ID·revision·configuration SHA-256과 result SHA-256을 가진 JSON 한 개를 만든다. 시나리오가 `N`개라면 제출할 때 `--array=0-(N-1)`을 명시한다. 예제 파일은 전체 model example 문서이거나 ensemble 계약 하나만 담은 JSON일 수 있다.

```bash
export MATINTEGRITY_SCENARIO_ENSEMBLE=/absolute/path/to/scenario-ensemble.json
export MATINTEGRITY_EVALUATOR_REVISION=git-commit-or-release-id
export MATINTEGRITY_EVALUATOR_CONFIG_SHA256=64_HEX_CONFIGURATION_DIGEST
export MATINTEGRITY_SCENARIO_COUNT=N
sbatch --array=0-$((MATINTEGRITY_SCENARIO_COUNT-1)) \
  --account=YOUR_ACCOUNT --partition=YOUR_PARTITION \
  hpc/crack_scenario_array.sh
```

모든 배열 작업이 끝난 뒤 정확한 job 결과 폴더를 집계한다.

```bash
"$MATINTEGRITY_PYTHON" scripts/crack_scenario_reduce.py \
  --ensemble "$MATINTEGRITY_SCENARIO_ENSEMBLE" \
  --evaluations-dir "hpc-results/crack-scenarios-JOB_ID" \
  --output "hpc-results/crack-scenarios-JOB_ID/reduction.json" \
  --evaluator-id matintegrity-tabulated-growth \
  --evaluator-revision "$MATINTEGRITY_EVALUATOR_REVISION" \
  --evaluator-configuration-sha256 "$MATINTEGRITY_EVALUATOR_CONFIG_SHA256"
```

reducer는 manifest와 평가 ID 집합이 정확히 같은지, 입력 digest와 evaluator identity가 모두 같은지 검사한다. 누락·추가·중복·다른 리비전은 입력 검증 오류다. `execution_failed`, `invalid_input`, `needs_data`, `out_of_scope` 행은 삭제하지 않고 모든 집계를 보류한다. 이 절차는 병렬 실행 교환계약이며 클러스터 스케줄러, 입력분포, 물리모델 또는 시나리오 확률을 자격화하지 않는다.

## 확장 원칙

고비용 Monte Carlo, bootstrap, 격자·시간 수렴은 각각 독립 task로 manifest에 추가한다. 난수 작업은 task·replicate ID에서 결정한 seed를 결과에 기록하고, 배열 개수 변경으로 기존 replicate seed가 바뀌지 않게 한다. MPI나 GPU는 실제 알고리즘이 이를 사용하는 작업에만 별도 resource profile을 둔다. 동일 파일에 여러 작업이 쓰지 않으며 제한 원자료는 클러스터 정책이 허용한 storage에만 둔다.








batch108은 합성 상지도 연결성·범주 경계 길이 회귀다. 회귀는 실행하지 않았다.


batch109는 caller 보정 Morrow 및 SWT strain-life 회귀로, 0 평균응력 관계·인장/압축 반응·최대응력 제한·cycle support·적용성 review gate를 확인하도록 등록했다. 실행하지 않았다.


batch110은 seeded pCN subset simulation의 재현성, conditional threshold, callback 검토 gate, threshold 정체와 limit-state 입력 유효성 확인용이다. 로컬이나 누리온에서 실행하지 않았다.
