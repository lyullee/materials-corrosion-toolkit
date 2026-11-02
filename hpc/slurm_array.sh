#!/usr/bin/env bash
#SBATCH --job-name=matintegrity-verify
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --mem=4G
#SBATCH --output=hpc-results/slurm-%A_%a.out

set -euo pipefail

: "${MATINTEGRITY_PROJECT:?Set MATINTEGRITY_PROJECT to the repository checkout}"
: "${MATINTEGRITY_PYTHON:?Set MATINTEGRITY_PYTHON to the prepared Python executable}"
: "${SLURM_ARRAY_TASK_ID:?Slurm array index is required}"

task_count="$("${MATINTEGRITY_PYTHON}" -c 'import json,sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))["tasks"]))' "${MATINTEGRITY_PROJECT}/hpc/task_manifest.json")"
submit_dir="${SLURM_SUBMIT_DIR:-$PWD}"
if ! [[ "${task_count}" =~ ^[1-9][0-9]*$ ]] || (( SLURM_ARRAY_TASK_ID >= task_count )); then
  echo "invalid Slurm array index ${SLURM_ARRAY_TASK_ID} for manifest task count ${task_count}" >&2
  exit 2
fi

result_root="${submit_dir}/hpc-results/${SLURM_ARRAY_JOB_ID}"
task_result="${result_root}/task-${SLURM_ARRAY_TASK_ID}"
scratch_root="${SLURM_TMPDIR:-/tmp}/${USER}/matintegrity-${SLURM_ARRAY_JOB_ID}-${SLURM_ARRAY_TASK_ID}"
mkdir -p "${task_result}" "${scratch_root}"
rsync -a \
  --exclude '.venv' \
  --exclude 'wheelhouse' \
  --exclude 'hpc-results' \
  --exclude 'data/raw' \
  --exclude 'data/derived' \
  --exclude 'data/evidence' \
  "${MATINTEGRITY_PROJECT}/" "${scratch_root}/project/"
mkdir -p "${scratch_root}/project/data"
for private_data in raw derived evidence; do
  if [[ -d "${MATINTEGRITY_PROJECT}/data/${private_data}" ]]; then
    ln -s "${MATINTEGRITY_PROJECT}/data/${private_data}" \
      "${scratch_root}/project/data/${private_data}"
  fi
done
cd "${scratch_root}/project"
"${MATINTEGRITY_PYTHON}" scripts/hpc_run_task.py \
  --task-index "${SLURM_ARRAY_TASK_ID}" \
  --output-dir "${task_result}"
