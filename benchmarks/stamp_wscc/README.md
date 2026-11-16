# STAMP WSCC small-signal benchmarks

These scripts compare VeraGrid with the six-bus WSCC SG/GFOR/GFOL case in
`STAMP_Public`. Both saved VeraGrid grids use the **nonlinear** GFOR and GFOL
models. The runners do not launch STAMP or MATLAB; they load committed fixtures
and compare newly computed VeraGrid modes with STAMP's exported CSV.

## Layout

| File | Purpose |
|---|---|
| `run_rms.py` | Loads the 88-state RMS grid, initializes its dynamic network from power flow, calculates eigenvalues, matches all STAMP RMS modes, and times the dense eigensolver. |
| `run_emt.py` | Loads the nonlinear EMT grid, solves one 50 Hz orbit (with optional Newton shooting), calculates Floquet exponents, and matches a selected rightmost subset with the STAMP RMS modes. |
| `benchmark_stamp_time_series.m` | Builds the STAMP nonlinear Simulink model, runs a Load-1 step, and records a warmed simulation trajectory and three timings. |
| `run_time_series.py` | Runs the equivalent load step with the VeraGrid RMS model and records its trajectory and timing. |
| `benchmark_multivac_time_series.sh` | Slurm job that runs both implementations sequentially on the same Multivac node. |
| `compare_time_series.py` | Checks the saved per-unit speed trajectories and prints timing and error summaries. |
| `plot_spectrum.py` | Plots the saved nonlinear EMT result against STAMP RMS with a full-mode panel and a rightmost-mode zoom. |
| `generate_fixtures.py` | Authoring script to export the grids into the neighboring `STAMP_Public/veragrid_stamp/data/`, copy them here, and copy the STAMP CSV. |
| `src/tests/data/stamp_wscc/` | Committed input grids, STAMP eigenvalue and runtime CSVs, and the corrected nonlinear EMT periodic state. This is input storage, not a pytest suite. |

## Run

From the VeraGrid repository root, in an environment with VeraGrid dependencies:

```bash
python3 benchmarks/stamp_wscc/run_rms.py
VERAGRID_EMT_INIT_CACHE_DIR=/tmp/veragrid-emt-init \
VERAGRID_JIT_CACHE_DIR=/tmp/veragrid-jit \
python3 benchmarks/stamp_wscc/run_emt.py --iterations 0
```

For the WSCC time-series comparison, stage this VeraGrid checkout and the
neighboring `STAMP_Public` checkout on Multivac, set `BENCH_STAGE` to the
staged VeraGrid directory, then submit
`sbatch benchmarks/stamp_wscc/benchmark_multivac_time_series.sh` from that
directory. The job requires MATLAB/Simulink 2025b on `cetus`, Python 3.12,
the VeraGrid dependencies in
`$HOME/venvs/veragrid-benchmark/lib/python3.12/site-packages`, and `fmpy`
either there or in `$BENCH_STAGE/vendor`. Its output directory is
`$BENCH_STAGE/results`. Set `BENCH_ONLY_VERAGRID=1` when resubmitting just
the VeraGrid half after a completed STAMP run.

The time-series event is a 1% increase in Load-1 conductance at 0.01 s, with
a 0.3 s simulation interval. STAMP applies a parallel resistance step with
`DR=0.01`; VeraGrid updates `Load1.G0` to 1.01 times its initialized value.
Both use a fixed `1e-5 s` integration step and record the SG1 speed. STAMP's
Simulink solver is explicit `ode1`; VeraGrid uses implicit backward Euler with
Newton tolerance `1e-8` by default and at most 100 iterations. These are different
solvers, so their elapsed times reflect the stated implementations and are not
a matched-solver speed ratio. STAMP records three timed simulations after an
untimed warm-up with Fast Restart; VeraGrid currently records one simulation.
The STAMP model build and first Simulink compilation are excluded from the
timed samples. VeraGrid's power flow, dynamic setup, and event creation are
reported separately from its simulation time.

### Recorded Multivac result (2026-10-28)

Both simulations ran on `cetus` with one requested CPU and one thread for
MATLAB/BLAS. STAMP ran in Slurm job `82605`; the VeraGrid portion was rerun in
job `82607` at Newton tolerance `1e-9` after correcting the remote Python environment. The STAMP setup
took 349.266 s. Its three timed simulations took 29.231, 13.328, and 12.576 s
(median **13.328 s**). VeraGrid setup took 17.396 s and its one simulation took
**128.156 s**. The simulation-only time ratio is **9.616** for
VeraGrid/STAMP median with these different solvers and timing sample counts.
The first timed STAMP run is noticeably slower than the other two despite the
untimed warm-up; all three samples are retained.

STAMP exported SG1 speed in electrical rad/s. The saved STAMP trajectory is
converted to per unit by dividing by `2*pi*50`, as the MATLAB runner now does.
At STAMP's 0.1 ms output times, VeraGrid's per-unit SG1 speed has an RMSE of
`7.43e-8 pu` and maximum absolute difference of `1.82e-7 pu`. Both traces
start at 1 pu and end near 0.999926 pu. The saved CSV files are in
`results/multivac_time_series/`; rerun the summary with:

```bash
python3 benchmarks/stamp_wscc/compare_time_series.py
```

The recorded timing excludes STAMP model generation and first Simulink
compilation, and excludes VeraGrid power flow and event setup. It therefore
describes repeated simulation cost, not end-to-end time. STAMP uses explicit
Euler and VeraGrid uses implicit backward Euler; the result does not isolate
framework overhead from the cost of the numerical method.

### Newton tolerance sensitivity (same node, 2026-10-28)

The VeraGrid runner accepts `--tolerance` for its Newton residual stopping
test. These additional runs used the same `cetus` node, event, solver, and
`1e-5 s` step. The `1e-8` and `1e-6` runs were Slurm jobs `82609` and `82608`,
respectively. Errors are against STAMP SG1 speed after unit conversion.

| VeraGrid Newton tolerance | Simulation time | SG1 speed RMSE | Maximum error |
|---:|---:|---:|---:|
| `1e-9` | 128.156 s | `7.43e-8 pu` | `1.82e-7 pu` |
| `1e-8` | 121.357 s | `7.43e-8 pu` | `1.82e-7 pu` |
| `1e-6` | 35.487 s | `3.66e-5 pu` | `6.78e-5 pu` |

The `1e-8` and `1e-9` VeraGrid traces differ by at most `3.35e-14 pu`.
The `1e-6` run is fast because it accepts an inaccurate response to this small
disturbance; it should not be used for the trajectory comparison. At `1e-8`,
the simulation-only time ratio to STAMP's median is **9.106**. STAMP `ode1`
has no Newton or absolute/relative error tolerance, so no VeraGrid Newton
threshold makes the solvers numerically equivalent. A matched-solver timing
comparison would require another solver implementation or a common reference
trajectory at finer step sizes.

Set `MEASURE_TIME = True` near the top of `run_rms.py` to print initialization
plus matrix construction time and the median of 20 warmed dense eigenvalue
solves during a normal script run. The saved STAMP timing CSV contains 20 warmed `eig(A)` samples
from a one-core Multivac run, excluding STAMP setup. The runner prints its
median beside the local VeraGrid median. These samples were collected on
different machines unless the VeraGrid runner is run on that same node, so the
default output is **not a measured speed ratio**. For a controlled comparison,
run VeraGrid on the same node with one BLAS thread, using the same 88-state
eigenvalue task. The STAMP SSA routine and VeraGrid initialization times have
different scopes and are not directly compared here.

The EMT run is much more expensive: it integrates a cycle, builds the full
monodromy matrix, and computes its eigenvalues. The default uses the saved
nonlinear periodic state. Use `--iterations 3` and
`--save-periodic-state PATH` to refine and inspect the orbit. The runner
prints the periodic defect and modal distances; `--output PATH` writes the
computed EMT modes as CSV. Outputs are opt-in so a benchmark run does not alter
the committed reference data.

The recorded `results/nonlinear_emt_floquet_exponents.csv` was produced from
the corrected nonlinear grid and periodic state. Regenerate the documentation
figure with `python3 benchmarks/stamp_wscc/plot_spectrum.py` after replacing
that result CSV with a fresh `run_emt.py --output` run.

## Comparison contract

The RMS runner computes the complete 88-state spectrum. It uses a one-to-one
minimum-distance assignment in the complex plane and reports the median and
maximum absolute eigenvalue difference in `s^-1`. A `1e-5 s^-1` comparison
limit is printed as a diagnostic. The saved nonlinear fixture produced a
maximum difference of `2.24427e-8 s^-1` on 2026-10-20.

The EMT runner converts one-period Floquet multipliers to exponents with
`log(mu)/T`, then folds STAMP RMS frequencies into the 50 Hz Floquet frequency
interval. It compares the **10 rightmost STAMP modes** by one-to-one complex
assignment against the full EMT spectrum. These 10 cover the modes through
approximately `-1.62 s^-1` in the STAMP reference. The nonlinear fixture's
corrected orbit closed within `9.8e-10` after three shooting iterations. The
maximum distance for these 10 modes is `0.00204335 s^-1`; the dominant mode
differs by `0.0001083 s^-1`. Modes farther left remain outside this comparison
because very small multipliers degrade exponent precision, and the EMT model
has additional states with no RMS counterpart.

The earlier `STAMP_Public/scripts/stamp_wscc_emt_floquet_exponents.csv` came
from the **linearized-deviation** converter wrapper used by
`solve_veragrid_stamp_wscc_emt_periodic.py`. A first nonlinear run showed a
much larger `0.0819 s^-1` gap over the same 10 modes. Its EMT wrapper had
omitted the synchronous generator's speed reference and used fixed `1.0 pu`
instead. Passing the generator speed to the wrapped nonlinear RMS equations
reduced that gap to the value above; the corrected fixture and periodic state
were then regenerated. The comparisons remain specific to this WSCC case and
solver configuration.

## Fixture provenance

The reference CSV is copied from
`STAMP_Public/STAMP/02_results/multivac/WSCC_SG_GFOR_GFOL_eigenvalues.csv`.
The STAMP runtime samples are copied from
`STAMP_Public/STAMP/02_results/comparison/benchmark_stamp_multivac.csv`,
generated by `STAMP_Public/STAMP/benchmark_wscc_stamp.m`. That script times
`eig(A)` on its assembled 88-state STAMP matrix; the VeraGrid runner times
`scipy.linalg.eigvals` on its assembled 88-state RMS matrix. The original
STAMP run used the linearized converter realization, while the saved VeraGrid
fixture uses nonlinear converters. Their small-signal spectra match closely,
but this difference in model realization remains part of the timing provenance.
The RMS grid is generated by `build_stamp_wscc_grid(dynamic_lines=True,
full_dynamic_network=True, nonlinear_converters=True)`; the EMT grid by
`build_stamp_wscc_emt_grid(nonlinear_converters=True)`.

The source `.veragrid` models and nonlinear periodic state are also saved in
`STAMP_Public/veragrid_stamp/data/`. The local `STAMP_Public` checkout was at commit
`f132f36e4787c469e009af00c7b8d5993e334163` when these fixtures were
exported. It had uncommitted model changes, so that commit alone does not
reconstruct the grids. The source SHA-256 values are:

| Source file | SHA-256 |
|---|---|
| `veragrid_stamp/wscc_case.py` | `1aea4a879f5a9d7d7aaabfedf06a3a793ee8556ebe7877f4f7507f07d336d96b` |
| `veragrid_stamp/emt_case.py` | `1af695c926105f0c3708602931e0c83349b0725dc15e1f1006766a0b6903ca85` |
| `veragrid_stamp/emt_nonlinear_converters.py` | `3a2ae31888824b84074209f861e16e242ad31e988305e72ee565f7857be10438` |
| STAMP eigenvalue CSV | `ffbff5ac13cef88ca6ec70baa32483fdc66f9c18d93560209c05fbdcc52ce092` |

The exporter sets `R0=R2=0`, `X0=X2=1e6` per generator. This supplies an
effectively open zero- and negative-sequence path for the current three-phase
power-flow initialization while retaining the balanced operating point. It
does not alter the reference STAMP CSV.

To refresh the grids from the sibling checkout, run from the VeraGrid root:

```bash
PYTHONPATH=src:../STAMP_Public python3 benchmarks/stamp_wscc/generate_fixtures.py
```

If the EMT model changes, rerun shooting and replace `emt_periodic_x0.csv`
only after checking its variable count, orbit defect, and modal comparison.

Related formulation context and plots are in
[`doc/md_source/dynamic_benchmarks.md`](../../doc/md_source/dynamic_benchmarks.md#3-stamp-comparison).
