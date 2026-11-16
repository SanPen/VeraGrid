# Ten-run RMS timing methods

[Results and plots](RESULTS.md).

## Setup and timing

The VeraGrid **RHS/Jacobian compilation** numbers time `RMSCompiler` and `RMSCompilerVec` `compile_rhs` and `compile_sparse_jacobian` calls during problem construction. The Julia simulation build includes model construction, initialization, and JIT work; its RHS and Jacobian compilation cannot be isolated from that phase with this interface. VeraGrid's **linear solve** includes BDF sparse factorization and triangular solves, timed around `_factorize` and `_linear_solve`. Julia's `unattributed` integration is total integration minus timed RHS and Jacobian callbacks; it includes linear solves, solver control, event handling, output, and timing overhead. It must not be interpreted as linear solve time.

The integration phase times are descriptive, not a controlled solver-speed comparison: Julia uses adaptive Sundials IDA; VeraGrid uses its vectorized adaptive BDF1–5 implementation with a 0.01-second maximum step for WECC 240 and absolute/relative tolerances of `1e-6`/`1e-3`. The smaller cases use their Julia reference maximum steps of 0.02 or 0.01 seconds. Both run the same network scenario and event, but they solve it with different algorithms. The Julia model is built through PowerSystemCaseBuilder; VeraGrid loads a committed `.veragrid` fixture. VeraGrid RMSE compares its trajectory with the committed Julia reference CSV. WECC 240 RMSE is about `1.11e-4` p.u.; the earlier Backward Euler result in the parent README had lower RMSE with a different integrator and much longer runtime. The timing ratio should therefore be read alongside this accuracy difference. This run did not regenerate those reference trajectories.

## Reproduce

From the VeraGrid root, with no other benchmark process running:

```bash
julia --startup-file=no --project="../power systems julia" benchmarks/powersystems_julia/measure_ten_julia.jl
PYTHONPATH=src:. MPLCONFIGDIR=/tmp/mpl-veragrid /home/pablo/myenv/bin/python benchmarks/powersystems_julia/measure_ten_veragrid.py
PYTHONPATH=src:. /home/pablo/myenv/bin/python benchmarks/powersystems_julia/plot_ten_run_timing.py
```

The raw measurements are [`julia.csv`](julia.csv) and [`veragrid.csv`](veragrid.csv). Both scripts record a complete fresh setup on each repetition. VeraGrid uses `PowerBalanceVectorized`, adaptive BDF1–5, and sparse LU; Julia uses `ResidualModel` with Sundials IDA. Julia callback timers use `time_ns`; VeraGrid compiler timers use `perf_counter`, and its integration timers wrap `AdaptiveBdf15Integration` residual, Jacobian, factorization, and solve methods.
