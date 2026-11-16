# WECC 240 five-second benchmark methods

[Results and plots](RESULTS.md).

## Setup and timing

The line trip occurs at `t = 1 s`. VeraGrid loads the committed `.veragrid` fixture and runs `PowerBalanceVectorized` with adaptive BDF1–5 and sparse LU. Julia builds the matching model through PowerSystemCaseBuilder and runs PowerSimulationsDynamics.jl with Sundials IDA. Both save results every `0.01 s` and cap internal steps at `0.01 s`. VeraGrid BDF absolute and relative tolerances are `1e-6` and `1e-3`. The engines ran sequentially on the same host, ten fresh runs each. Repetition 1 is cold; summaries use repetitions 2–10.

VeraGrid times RHS evaluation, Jacobian evaluation, and sparse factorization plus triangular solve separately inside integration. Julia times RHS and Jacobian callbacks; its unattributed integration time includes linear solves, solver control, event handling, output, and timing overhead. Julia linear-solver time is not isolated. Total time includes setup and simulation build. VeraGrid RMSE compares the trajectory against the committed Julia reference CSV, rather than a trajectory regenerated in this run.

## Raw measurements and reproduction

The five-second measurements are [`julia.csv`](julia.csv) and [`veragrid.csv`](veragrid.csv). The [ten-run timing report](../ten_run_timing/RESULTS.md) contains its own CSVs and additional plots. Both benchmark scripts live in `benchmarks/powersystems_julia/`.

```bash
julia --startup-file=no --project="../power systems julia" benchmarks/powersystems_julia/measure_ten_julia.jl wecc_240 5.0 benchmarks/powersystems_julia/results/five_second_wecc/julia.csv 10
PYTHONPATH=src:. /home/pablo/myenv/bin/python benchmarks/powersystems_julia/measure_ten_veragrid.py --case wecc_240 --duration 5 --repetitions 10 --output benchmarks/powersystems_julia/results/five_second_wecc/veragrid.csv
PYTHONPATH=src:. /home/pablo/myenv/bin/python benchmarks/powersystems_julia/plot_wecc_horizons.py
```
