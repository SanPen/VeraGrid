#!/bin/bash -l
#SBATCH --job-name=stamp-vg-series
#SBATCH --output=stamp_vg_series_%j.out
#SBATCH --error=stamp_vg_series_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodelist=cetus
#SBATCH --mem=8G
#SBATCH --time=00:30:00

source /usr/share/modules/init/bash
module use /opt/modulefiles
set -euo pipefail
: "${BENCH_STAGE:?Set BENCH_STAGE to the staged benchmark directory}"
export STAMP_ROOT="$HOME/STAMP_Public"
export BENCH_OUTPUT_DIR="${BENCH_OUTPUT_DIR:-$BENCH_STAGE/results}"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export NUMBA_CACHE_DIR="/tmp/numba-$USER-$SLURM_JOB_ID"
export MPLCONFIGDIR="/tmp/mpl-$USER-$SLURM_JOB_ID"
mkdir -p "$BENCH_OUTPUT_DIR" "$NUMBA_CACHE_DIR" "$MPLCONFIGDIR"
printf 'job_id=%s\nnode=%s\n' "$SLURM_JOB_ID" "$(hostname)"

if [[ "${BENCH_ONLY_VERAGRID:-0}" != 1 ]]; then
    module load matlab2025b
    matlab -singleCompThread -batch "run('$BENCH_STAGE/benchmarks/stamp_wscc/benchmark_stamp_time_series.m')"
fi

module purge
module load python3.12
export PYTHONPATH="$HOME/venvs/veragrid-benchmark/lib/python3.12/site-packages:$BENCH_STAGE/vendor:$BENCH_STAGE/src:$BENCH_STAGE/benchmarks/stamp_wscc"
/opt/python3/python3.12/bin/python \
    "$BENCH_STAGE/benchmarks/stamp_wscc/run_time_series.py" \
    --duration 0.3 --step 1e-5 \
    --tolerance "${BENCH_TOLERANCE:-1e-8}" \
    --output-dir "$BENCH_OUTPUT_DIR"
