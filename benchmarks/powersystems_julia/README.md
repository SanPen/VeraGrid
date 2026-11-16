# PowerSimulationsDynamics.jl RMS benchmarks

These benchmarks compare VeraGrid RMS small-signal eigenvalues and time series
with saved results from `PowerSimulationsDynamics.jl`, using equivalent
component models, network data, and operating points. `PowerSystems.jl`
supplies the Julia data model; the dynamic analysis itself is performed by
`PowerSimulationsDynamics.jl`.

The benchmark does not start Julia. It loads committed `.veragrid` models,
runs a fresh VeraGrid power flow and RMS analysis, then compares the calculated
modes or event trajectories with Julia CSV reference results.

## RMS timing results

The [WECC 240 five-second benchmark](RESULTS.md) presents ten runs per engine, the measured timing phases, accuracy, and a results plot. The [ten-run timing report](results/ten_run_timing/RESULTS.md) covers all four event cases. Each results page links to separate methods and reproduction instructions.

## Cases and files

| Case | Shared finite modes | Model |
|---|---:|---|
| `2_bus` | 2 | Single-machine infinite-bus system with the complete Julia generator assembly. |
| `3_bus` | 27 | Infinite bus, synchronous generator, inverter, dynamic lines, and impedance loads. |
| `ieee9` | 45 | IEEE 9-bus system with three complete PowerSystems-style generator assemblies. |
| `wecc_240` | 1,658 total; 234 compared | WECC 240-bus system with 99 active synchronous machines and 37 renewable inverter assemblies. |

The committed inputs are in `src/tests/data/powersystems_julia/`. This is the
repository's shared input-data location; these files are not pytest tests.
Each case has a `.veragrid` model and a `<case>_eigenvalues.csv` Julia
reference. `julia_small_signal_timings.csv` contains the source repo's raw
Julia timing samples. The executable benchmark is `run_small_signal.py`.

## RMS time series

`run_rms_time_series.py` compares the 2 bus, 3 bus, IEEE 9, and WECC 240 models
against saved PowerSimulationsDynamics.jl event trajectories. At 1 second it
changes the 2 bus generator mechanical torque to 0.55, the 3 bus generator
`P_ref` to 0.85, the IEEE 9 generator `P_ref` to 0.78, or trips WECC line
`1101_1401_1`. The observed quantities are respectively generator rotor angle,
bus 102 voltage magnitude, bus 5 voltage magnitude, and WECC bus 1101 voltage
magnitude. The runner interpolates VeraGrid results to the Julia
reference timestamps and reports RMSE and maximum absolute error. It also
reports model and power flow setup, RMS problem construction, and integration
time separately. It displays the saved Julia after-first-run build, compilation,
and compute times alongside those local measurements, including an observed
integration time ratio. The Julia and VeraGrid runs use different solvers,
step sizes, and environments, so the ratio is descriptive rather than a
controlled speed comparison. The optional summary CSV includes both sets of
timings and the ratio.

```bash
PYTHONPATH=src .venv/bin/python benchmarks/powersystems_julia/run_rms_time_series.py
PYTHONPATH=src .venv/bin/python benchmarks/powersystems_julia/run_rms_time_series.py \
  --case 3_bus --output /tmp/powersystems_rms.csv \
  --trajectory-dir /tmp/powersystems_rms_trajectories
```

The committed `<case>_rms_time_series.csv` files are the Julia reference
trajectories from `results/benchmarks/powersystems_<case>_time_series.csv` in
the sibling `power systems julia` checkout. Its
`scripts/benchmark_powersystems_time_domain.jl` uses Sundials IDA with a
0.02 second output interval for the 2 and 3 bus cases and 0.01 second for
IEEE 9 and WECC 240. VeraGrid uses fixed step Backward Euler at 0.0005 seconds
for 2 bus, 0.001 seconds for 3 bus and IEEE 9, and 0.01 seconds for WECC 240.
Numerical tolerances are 1e-10 for 2 and 3 bus and 1e-6 for IEEE 9 and
WECC 240. The reference solver and VeraGrid integrator
are different, so trajectory error includes integration differences.
To try an IDA-style weighted Newton correction stopping test in VeraGrid,
select `--newton-convergence ida-weighted`. This corresponds to
`RmsOptions(use_weighted_newton_correction=True,
weighted_newton_absolute_tolerance=1e-6,
weighted_newton_relative_tolerance=1e-3)`. The default remains the existing
absolute residual test. This option applies to the `PowerBalance` Backward
Euler solver; it changes Newton convergence, not the fixed-step integration
method or its lack of IDA's local error control.

```bash
PYTHONPATH=src .venv/bin/python benchmarks/powersystems_julia/run_rms_time_series.py \
  --case wecc_240 --newton-convergence ida-weighted
```

In the WECC 240 run, weighted correction convergence gave `5.20635e-5` p.u.
trajectory RMSE and `795.52 s` integration time. The earlier residual-rule
run gave `5.20634e-5` p.u. RMSE and `435.47 s` integration time. These are
separate local runs, so their runtime difference is indicative; the weighted
test did not improve the observed trajectory error and took longer here.

Use `--rms-tolerance` to test a different absolute residual threshold while
keeping the residual-based Newton rule. The value also controls VeraGrid's
initial algebraic projection.

```bash
PYTHONPATH=src .venv/bin/python benchmarks/powersystems_julia/run_rms_time_series.py \
  --case wecc_240 --newton-convergence residual --rms-tolerance 1e-4
```

In one local WECC run at `1e-4`, integration took `124.46 s` and the bus 1101
trajectory RMSE against Julia was `3.81154e-4` p.u. Compared with the earlier
`1e-6` residual run (`435.47 s`, `5.20634e-5` p.u.), integration was about
`3.50x` faster and RMSE about `7.32x` larger. The error increase occurred
after the line trip: pre-trip RMSE stayed near `1.98e-7` p.u. The final bus
voltage change was `-6.14e-4` p.u. at `1e-4`, versus `-1.08e-3` p.u. in both
the Julia reference and VeraGrid's `1e-6` run. Thus `1e-4` materially
under-resolves this disturbance despite reporting convergence.
`julia_rms_time_series_timings.csv` is copied from
`results/benchmarks/powersystems_time_domain_timings.csv` in the sibling
checkout. The first Julia repetition includes JIT compilation; the runner
uses repetition 2 as its after-first-run timing reference.
The WECC 240 trajectory comes from the sibling checkout's
`results/wecc_240/time_series.csv`, produced by `scripts/run_wecc_240.jl`.
Its Julia timings were measured separately with `measure_wecc_julia.jl` on the
same 20 second line trip, using two sequential repetitions and temporary
simulation output directories. The second repetition is the displayed timing.
In one local run, the WECC trajectory comparison covered 2,001 samples and
gave `5.20634e-5` p.u. RMSE and `1.84318e-4` p.u. maximum absolute error.
The measured integration times were `435.47 s` for VeraGrid and `19.0482 s`
for Julia's second repetition; these are observed times for different solvers.

## Run

From the VeraGrid repository root:

```bash
python3 benchmarks/powersystems_julia/run_small_signal.py
```

Run selected cases or write a summary CSV:

```bash
python3 benchmarks/powersystems_julia/run_small_signal.py --case 3_bus
python3 benchmarks/powersystems_julia/run_small_signal.py \
  --output /tmp/powersystems_julia_small_signal.csv
```

Use `--measure-time` to run the timing comparison. The runner reports VeraGrid model loading, power flow,
and driver construction as setup time, then the median of 20 repeated
`driver.run()` calls on the initialized model. The first analysis is performed
before timing these repetitions. An optional summary CSV includes the VeraGrid
setup and SSA median plus the Julia reference SSA timing when measurement is enabled.

```bash
python3 benchmarks/powersystems_julia/run_small_signal.py \
  --case wecc_240 --measure-time --timing-runs 20 \
  --output /tmp/wecc240_timing_comparison.csv
```

The Julia reference is `small_signal_analysis(sim)` from repetition 2 in the
source timing CSV, following a first run that includes Julia compilation.
There is only **one** after-first-run Julia sample per case, versus 20 VeraGrid samples
by default. Source timings were recorded in the sibling checkout; the local
VeraGrid run may be on different hardware. These figures are informative
timings, **not a controlled speed ratio**. Julia constructs a model and
simulation in its setup phases, while this runner loads a saved `.veragrid`
file and solves power flow. The setup times are therefore shown separately.

The recorded WECC 240 repetitions are:

| Repetition | Build (`s`) | Initialization (`s`) | Eigenanalysis (`s`) | Total (`s`) |
|---:|---:|---:|---:|---:|
| 1 | `31.714824363` | `45.742284239` | `3.897299308` | `81.35440791` |
| 2, after first run | `0.065261647` | `8.768723888` | `3.152680851` | `11.986666386` |

On the same machine, the recorded VeraGrid run used 20 after-first-run repetitions and
had a `4.5152 s` median eigenanalysis time. Julia's after-first-run eigenanalysis took
`3.15268 s`, so VeraGrid took `1.4321x` as long for this 1,658-mode case. The
VeraGrid setup time was `38.6599 s`; setup is reported separately because the
two programs construct and initialize their models differently.

The benchmark exposes both VeraGrid SSA solvers:

```bash
# Complete dense spectrum
python3 benchmarks/powersystems_julia/run_small_signal.py \
  --case wecc_240 --ssa-variant dense

# 100 modes closest to the sparse solver's shift targets
python3 benchmarks/powersystems_julia/run_small_signal.py \
  --case wecc_240 --ssa-variant sparse --sparse-modes 100

# Run and time both variants
python3 benchmarks/powersystems_julia/run_small_signal.py \
  --case wecc_240 --ssa-variant both --sparse-modes 100 \
  --measure-time --timing-runs 20
```

The recorded dense solve calculated all 1,658 modes in a `4.5152 s` median.
The sparse solve requested 100 modes and took `3.38921 s`, a `1.3323x`
speedup. The sparse modes were assigned against the full Julia spectrum; its
recorded maximum distance was `2.61e-6 s^-1`. Julia's saved `3.15268 s`
measurement is a dense full-spectrum analysis, so it is compared directly
only with VeraGrid dense SSA.

The same run can be configured directly near the top of `run_small_signal.py`:

```python
DEFAULT_CASES = ("wecc_240",)
DEFAULT_SSA_VARIANT = "both"
DEFAULT_SPARSE_MODES = 100
MEASURE_TIME = True
TIMING_RUNS = 20
```

With those values, `python3 benchmarks/powersystems_julia/run_small_signal.py`
runs the equivalent configuration without additional arguments. Explicit
command-line options override these defaults.
The recorded VeraGrid dense and sparse measurements are stored in
`veragrid_small_signal_timings.csv`; normal benchmark runs calculate fresh
values and do not use that file as an input.

The WECC timing rows were recorded in the sibling PowerSystems.jl environment
and are retained when the fixtures are refreshed.

## Comparison contract

For each case, the runner:

1. loads the saved `.veragrid` model;
2. solves its power flow with fixed Newton-Raphson options;
3. reports the maximum RMS state and algebraic initialization residuals;
4. computes either the complete dense RMS spectrum or the requested sparse modes;
5. performs a one-to-one minimum-cost assignment in the complex plane; and
6. reports the median, maximum, rightmost-mode, and five largest assigned
   modal distances in `s^-1`; and
7. reports VeraGrid SSA timings beside the saved Julia timing reference.

This is a reporting benchmark rather than a pytest assertion. Equal mode
counts establish that the same retained dimension was compared, but they do
not establish numerical agreement by themselves.

The three small cases compare every finite mode. WECC 240 calculates the full
1,658-mode spectrum, then assigns the 234 Julia modes with
$\operatorname{Re}(\lambda)\geq-0.1\ \mathrm{s}^{-1}$ against the full
VeraGrid spectrum. This explicit window covers the right edge used for the
small-signal stability conclusion. The compact native port eliminates Julia's
descriptor constraints and retains the locally active control branches;
strongly damped modes outside the window are outside its comparison contract.
In sparse mode, every returned VeraGrid mode is assigned one-to-one against
the full Julia reference spectrum. The default sparse request is 100 modes,
which is deliberately larger than this case's 85-mode zero eigenvalue cluster.

The fixture run recorded on 2026-10-20 produced:

| Case | Modes | Median distance (`s^-1`) | Maximum distance (`s^-1`) | Rightmost-mode distance (`s^-1`) |
|---|---:|---:|---:|---:|
| Two bus | 2 | `1.23331e-10` | `1.23331e-10` | `1.23331e-10` |
| Three bus | 27 | `6.80355e-7` | `5.28905e-6` | `8.88666e-8` |
| IEEE 9 | 45 | `2.43174e-7` | `1.11982e-4` | `1.11982e-4` |
| WECC 240 stability window | 234 of 1,658 | `1.0e-10` | `7.64296e-4` | `1.0e-10` |

The Julia two-bus source has a small but finite Thevenin reactance of
`5e-6` pu; fixture generation retains it rather than replacing the source with
an ideal voltage constraint. The Julia three-bus ZIP loads normalize their impedance terms by the squared
power-flow voltage magnitude. Fixture generation applies the same normalization
to VeraGrid's shunt admittances; without it, the two programs solve different
operating points even though their nominal load powers are equal. The IEEE 9
reference contains a large positive real mode near `+2009.315 s^-1`, which
VeraGrid reproduces within approximately `1.12e-4 s^-1`. This benchmark reports
that reference model as provided and does not interpret it as a generally
stable IEEE 9 configuration. The absolute difference of that stiff mode is
approximately `5.57e-8` relative to its magnitude. The Julia residual model
stores its rectangular network admittance matrix in `Float32`, so differences
at this scale are consistent with network-coefficient rounding amplified by
the fast `1e-4`-second AVR states.

The WECC fixture stores the RAW operating-point load powers in
`wecc_240_static_loads.csv`. The runner restores them for the fresh power-flow
solve and then applies the saved constant-impedance RMS convention. The
recorded maximum state and algebraic initialization residuals are `1.13e-13`
and `5.97e-12`. Fixture construction excludes six inactive RAW generators and
reduces ten IEEEST descriptor models to their finite five-state realization,
giving the same 1,658 finite modes as Julia.

## Reference generation and provenance

The Julia results came from the sibling `power systems julia` repository:

```bash
julia --project=. scripts/run_2_bus.jl
julia --project=. scripts/run_3_bus.jl
julia --project=. scripts/run_ieee9.jl
julia --project=. scripts/run_wecc_240.jl
```

The recorded Julia environment contains:

- `PowerSystems.jl` 5.12.2
- `PowerSimulationsDynamics.jl` 0.16.2
- `PowerSystemCaseBuilder.jl` 2.6.0

The source repository was at commit
`121f89751738d930315bf31c96f40f4834b357ae` when the fixtures were
exported. The relevant model, runner, template, and result files were clean at
that commit. The reference CSV hashes are:

| File | SHA-256 |
|---|---|
| `2_bus_eigenvalues.csv` | `be24c11a5a14a9f096cddecd74b5c569fb6cb9d88fff459ab29cf3d73506b95e` |
| `3_bus_eigenvalues.csv` | `ec70adadef689f8acf6544ccfddde7cb58da7863820315a18ea3245637a72aa5` |
| `ieee9_eigenvalues.csv` | `003fe6343d91067e518f29be0904189223cbe50cae81d06f476ee2d84c7632c5` |
| `wecc_240_eigenvalues.csv` | `d26a98ad8dc51f3aef19846e80c7be8900317162e10ad63a0e2c04a563b1cf5f` |
| `wecc_240_static_loads.csv` | `5108de741f0d336b04f29eb2e69e05ba5584dfa2458c2a48f4c0a5afc8a3d28f` |
| `julia_small_signal_timings.csv` | `61d0af2d96cdb23fc4eaf568b977d6f147fe91180b04e7fcd1ed047ddf80a9b3` |
| `veragrid_small_signal_timings.csv` | `6413002a71afc7847b2b671059b93c42871cbad857b909b9f5b003a58505f0a4` |

The timing CSV is copied from
`power systems julia/results/benchmarks/powersystems_small_signal_timings.csv`,
generated by `scripts/benchmark_powersystems_small_signal.jl`. The WECC rows
were recorded in the sibling PowerSystems.jl environment and are preserved
when fixtures are refreshed. The first repetition includes compilation and is
retained for provenance but is not used as the after-first-run SSA reference.

`generate_fixtures.py` rebuilds the `.veragrid` files from that sibling
checkout and refreshes the four eigenvalue CSVs and the timing CSV:

```bash
PYTHONPATH="src:../power systems julia/scripts:../power systems julia/src" \
python3 benchmarks/powersystems_julia/generate_fixtures.py
```

The broader interpretation and published spectrum figure are in
[`doc/md_source/dynamic_benchmarks.md`](../../doc/md_source/dynamic_benchmarks.md#4-powersimulationsdynamicsjl-comparison).
