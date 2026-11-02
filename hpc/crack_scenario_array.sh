#!/usr/bin/env bash
#SBATCH --job-name=matintegrity-crack-scenarios
#SBATCH --cpus-per-task=1
#SBATCH --time=02:00:00
#SBATCH --mem=2G
#SBATCH --output=hpc-results/crack-scenario-%A_%a.out

set -euo pipefail

: "${MATINTEGRITY_PROJECT:?Set MATINTEGRITY_PROJECT to the repository checkout}"
: "${MATINTEGRITY_PYTHON:?Set MATINTEGRITY_PYTHON to the prepared Python executable}"
: "${MATINTEGRITY_SCENARIO_ENSEMBLE:?Set MATINTEGRITY_SCENARIO_ENSEMBLE to an absolute JSON path}"
: "${MATINTEGRITY_EVALUATOR_REVISION:?Set the source or release revision}"
: "${MATINTEGRITY_EVALUATOR_CONFIG_SHA256:?Set the evaluator configuration SHA-256}"

submit_dir="${SLURM_SUBMIT_DIR:-$PWD}"
result_root="${submit_dir}/hpc-results/crack-scenarios-${SLURM_ARRAY_JOB_ID}"
mkdir -p "${result_root}"

cd "${MATINTEGRITY_PROJECT}"
"${MATINTEGRITY_PYTHON}" scripts/crack_scenario_job.py \
  --ensemble "${MATINTEGRITY_SCENARIO_ENSEMBLE}" \
  --scenario-index "${SLURM_ARRAY_TASK_ID}" \
  --output "${result_root}/scenario-$(printf '%06d' "${SLURM_ARRAY_TASK_ID}").json" \
  --evaluator-id matintegrity-tabulated-growth \
  --evaluator-revision "${MATINTEGRITY_EVALUATOR_REVISION}" \
  --evaluator-configuration-sha256 "${MATINTEGRITY_EVALUATOR_CONFIG_SHA256}"
