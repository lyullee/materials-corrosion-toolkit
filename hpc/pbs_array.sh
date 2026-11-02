#!/usr/bin/env bash
#PBS -N matintegrity-verify
#PBS -q normal
#PBS -A etc
#PBS -l select=1:ncpus=1
#PBS -l walltime=12:00:00
#PBS -j oe
#PBS -J 0-141%16

set -euo pipefail

: "${MATINTEGRITY_PROJECT:?Set MATINTEGRITY_PROJECT to the staged project}"
: "${MATINTEGRITY_VENV:?Set MATINTEGRITY_VENV to the prepared virtual environment}"
: "${PBS_ARRAY_INDEX:?PBS array index is required}"
: "${PBS_JOBID:?PBS job identifier is required}"

source /etc/profile.d/modules.sh
module purge
module load python/3.12.5

python_executable="${MATINTEGRITY_VENV}/bin/python"
test -x "${python_executable}"
task_count="$("${python_executable}" -c 'import json,sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))["tasks"]))' "${MATINTEGRITY_PROJECT}/hpc/task_manifest.json")"
if ! [[ "${task_count}" =~ ^[1-9][0-9]*$ ]] || (( PBS_ARRAY_INDEX >= task_count )); then
  echo "invalid PBS array index ${PBS_ARRAY_INDEX} for manifest task count ${task_count}" >&2
  exit 2
fi

array_job_id="${PBS_JOBID%%[*}"
result_root="${MATINTEGRITY_PROJECT}/hpc-results/${array_job_id}"
task_result="${result_root}/task-${PBS_ARRAY_INDEX}"
scratch_base="${TMPDIR:-/scratch/${USER}/matintegrity-tmp}"
scratch_root="${scratch_base}/${array_job_id}-${PBS_ARRAY_INDEX}"
project_copy="${scratch_root}/project"

mkdir -p "${task_result}" "${project_copy}"
rsync -a \
  --exclude '.venv' \
  --exclude 'hpc-results' \
  --exclude 'data/raw' \
  --exclude 'data/derived' \
  --exclude 'data/evidence' \
  "${MATINTEGRITY_PROJECT}/" "${project_copy}/"

mkdir -p "${project_copy}/data"
for private_data in raw derived evidence; do
  if [[ -d "${MATINTEGRITY_PROJECT}/data/${private_data}" ]]; then
    ln -s "${MATINTEGRITY_PROJECT}/data/${private_data}" \
      "${project_copy}/data/${private_data}"
  fi
done

cd "${project_copy}"
"${python_executable}" scripts/hpc_run_task.py \
  --task-index "${PBS_ARRAY_INDEX}" \
  --output-dir "${task_result}"


