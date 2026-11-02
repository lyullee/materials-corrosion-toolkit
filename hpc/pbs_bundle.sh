#!/usr/bin/env bash
#PBS -N matintegrity-bundle
#PBS -q normal
#PBS -A etc
#PBS -l select=1:ncpus=64
#PBS -l walltime=12:00:00
#PBS -j oe

set -euo pipefail

: "${MATINTEGRITY_PROJECT:?Set MATINTEGRITY_PROJECT to the staged project}"
: "${MATINTEGRITY_VENV:?Set MATINTEGRITY_VENV to the prepared virtual environment}"
: "${PBS_JOBID:?PBS job identifier is required}"

source /etc/profile.d/modules.sh
module purge
module load python/3.12.5

python_executable="${MATINTEGRITY_VENV}/bin/python"
test -x "${python_executable}"

cd "${MATINTEGRITY_PROJECT}"
"${python_executable}" scripts/validate_hpc_manifest.py
task_count="$("${python_executable}" -c 'import json,sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))["tasks"]))' hpc/task_manifest.json)"
if ! [[ "${task_count}" =~ ^[1-9][0-9]*$ ]]; then
  echo "invalid manifest task count: ${task_count}" >&2
  exit 2
fi
workers="${MATINTEGRITY_PBS_WORKERS:-16}"
if ! [[ "${workers}" =~ ^[1-9][0-9]*$ ]] || (( workers > 64 )); then
  echo "MATINTEGRITY_PBS_WORKERS must be an integer from 1 to 64" >&2
  exit 2
fi

job_id="${PBS_JOBID%%.*}"
result_root="${MATINTEGRITY_PROJECT}/hpc-results/${job_id}"
scratch_base="${TMPDIR:-/scratch/${USER}/matintegrity-tmp}/${job_id}"
snapshot="${scratch_base}/snapshot"
mkdir -p "${result_root}" "${snapshot}"

rsync -a \
  --exclude '.venv' \
  --exclude 'wheelhouse' \
  --exclude 'hpc-results' \
  --exclude 'data/raw' \
  --exclude 'data/derived' \
  --exclude 'data/evidence' \
  "${MATINTEGRITY_PROJECT}/" "${snapshot}/"

run_task() {
  local task_index="$1"
  local task_root="${scratch_base}/task-${task_index}"
  local project_copy="${task_root}/project"
  mkdir -p "${project_copy}"
  cp -a "${snapshot}/." "${project_copy}/"
  mkdir -p "${project_copy}/data"
  for private_data in raw derived evidence; do
    if [[ -d "${MATINTEGRITY_PROJECT}/data/${private_data}" ]]; then
      ln -s "${MATINTEGRITY_PROJECT}/data/${private_data}" \
        "${project_copy}/data/${private_data}"
    fi
  done
  cd "${project_copy}"
  "${python_executable}" scripts/hpc_run_task.py \
    --task-index "${task_index}" \
    --output-dir "${result_root}/task-${task_index}"
}
export -f run_task
export MATINTEGRITY_PROJECT python_executable result_root scratch_base snapshot

set +e
seq 0 "$((task_count - 1))" | xargs -n 1 -P "${workers}" bash -c 'run_task "$1"' _
task_status=$?
"${python_executable}" "${MATINTEGRITY_PROJECT}/scripts/hpc_collect.py" \
  --results-dir "${result_root}"
collect_status=$?
set -e

if (( task_status != 0 )); then
  exit "${task_status}"
fi
exit "${collect_status}"
