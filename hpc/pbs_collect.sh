#!/usr/bin/env bash
#PBS -N matintegrity-collect
#PBS -q normal
#PBS -A etc
#PBS -l select=1:ncpus=1
#PBS -l walltime=01:00:00
#PBS -j oe

set -euo pipefail

: "${MATINTEGRITY_PROJECT:?Set MATINTEGRITY_PROJECT to the staged project}"
: "${MATINTEGRITY_VENV:?Set MATINTEGRITY_VENV to the prepared virtual environment}"
: "${MATINTEGRITY_ARRAY_JOB_ID:?Set the parent PBS array job identifier}"

source /etc/profile.d/modules.sh
module purge
module load python/3.12.5

python_executable="${MATINTEGRITY_VENV}/bin/python"
results_dir="${MATINTEGRITY_PROJECT}/hpc-results/${MATINTEGRITY_ARRAY_JOB_ID}"
cd "${MATINTEGRITY_PROJECT}"
"${python_executable}" scripts/hpc_collect.py --results-dir "${results_dir}"

