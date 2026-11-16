# WECC 240 Numba compiled backend methods

[Results and plot](RESULTS.md).

The Numba compiled runs use `rms_problem_dae_full_vectorized_numba_comp.RmsProblemDaeFullVec` with the same committed WECC 240 `.veragrid` fixture, line trip at `t = 1 s`, `AdaptiveBdf15Integration`, sparse LU, 0.01-second maximum step and output interval, and BDF absolute/relative tolerances of `1e-6`/`1e-3` as the original VeraGrid runs. The benchmark's `--backend numba-full-vectorized` option selects this class directly. It does not change the default backend or the original CSVs.

The compiled problem reports the trip as a forced BDF boundary. Without that boundary, BDF rejected 42 steps at `t = 1 s` and reduced its step below representable precision. The compiled class also skips model classes without equation entries while preparing kernels. These fixes are needed for this WECC case to converge.

Each horizon has three fresh sequential runs of the compiled backend, with repetitions 2–3 summarized as warm runs. The original vectorized and Julia comparison uses ten runs each, with repetitions 2–10 summarized. `integration_s` covers BDF integration; its `rhs_evaluation_s`, `jacobian_evaluation_s`, and `linear_solver_s` timers are measured separately. `linear_solver_s` includes sparse factorization and triangular solves. `problem_build_s` includes preparation and compilation of the Numba compiled problem, so the `rhs_compile_s` and `jacobian_compile_s` columns alone do not describe its full compilation cost. `total_s` includes fixture and power-flow setup, problem build, and integration. RMSE compares the saved bus trajectory against the committed Julia reference CSV.

From the VeraGrid repository root:

```bash
PYTHONPATH=src:. MPLCONFIGDIR=/tmp/mpl-veragrid /home/pablo/myenv/bin/python benchmarks/powersystems_julia/measure_ten_veragrid.py --case wecc_240 --duration 5 --repetitions 3 --backend numba-full-vectorized --output benchmarks/powersystems_julia/results/numba_comp_wecc/five_second.csv
PYTHONPATH=src:. MPLCONFIGDIR=/tmp/mpl-veragrid /home/pablo/myenv/bin/python benchmarks/powersystems_julia/measure_ten_veragrid.py --case wecc_240 --duration 20 --repetitions 3 --backend numba-full-vectorized --output benchmarks/powersystems_julia/results/numba_comp_wecc/twenty_second.csv
PYTHONPATH=src:. MPLCONFIGDIR=/tmp/mpl-veragrid /home/pablo/myenv/bin/python benchmarks/powersystems_julia/plot_numba_comp_wecc.py
```
