# ANDES versus VeraGrid: RMS time-domain benchmark

For the exact execution order, start with [README.md](README.md).

This benchmark compares fixed-step RMS trajectories calculated by VeraGrid
with saved ANDES trajectories for Kundur, IEEE14, IEEE39, NPCC140 and WECC179.
The runners load committed `.veragrid` cases from `src/tests/data/dynamics_andes/`.
`generate_fixtures.py` constructs these cases outside the benchmark.

Each case has one runner in its own system folder under `RMS/`. The runner
executes two separate scenarios and compares each one immediately
after the VeraGrid simulation:

- **base:** 1 ms step, 1 s horizon and a `1e-4` pu initial rotor-speed
  perturbation;
- **event:** 1 ms step, 2 s horizon and an additive `1e-4` pu rotor-speed state
  step at `t = 0.2 s`.

Both use fixed-step Backward Euler and a nonlinear tolerance of `1e-6`.

## Directory layout

Each runner writes only inside its own case directory:

```text
<SYSTEM>/
├── run_<SYSTEM>_rms.py
└── results/
    ├── ANDES/
    │   ├── base/
    │   └── event/
    ├── VeraGrid/
    │   ├── base/
    │   └── event/
    ├── comparison/
        ├── base/
        └── event/
    └── timing_summary.txt
```

The five runners are:

| Case | Runner |
|---|---|
| Kundur | `RMS/Kundur/run_Kundur_rms.py` |
| IEEE14 | `RMS/IEEE14/run_IEEE14_rms.py` |
| IEEE39 | `RMS/IEEE39/run_IEEE39_rms.py` |
| NPCC140 | `RMS/NPCC140/run_NPCC140_rms.py` |
| WECC179 | `RMS/WECC179/run_WECC179_rms.py` |

Open the required runner in PyCharm and use **Run** with the repository root as
the working directory. The saved ANDES trajectories must already exist. Generate them with
`RMS/generate_andes_rms_results.py`. Reference generation is separate from
VeraGrid simulation and comparison.

## Comparison contract

For each scenario, the runner:

1. loads the saved network and dynamic models;
2. performs the authoritative power flow used to initialize RMS;
3. initializes and integrates the VeraGrid RMS problem;
4. verifies convergence and the complete requested time grid;
5. aligns every common physical state with its ANDES counterpart;
6. removes only the common rotor-angle reference offset;
7. reports total, per-segment and per-state errors; and
8. saves representative trajectories and timing figures.

ANDES-only `BusFreq`, zero-time-constant and limiter auxiliary states are
reported as unmatched instead of being paired with unrelated VeraGrid states.

## Trajectory agreement results

The values below are **absolute errors**, not relative errors or percentages.
For every scenario, the difference is calculated as
`VeraGrid state value - ANDES state value` after aligning the common physical
states and removing the single common rotor-angle reference offset.

- **Maximum absolute error:** largest `abs(VeraGrid - ANDES)` value across all
  matched states and all stored time samples.
- **Absolute RMSE:** `sqrt(mean((VeraGrid - ANDES)^2))`, calculated jointly
  across all matched states and all stored time samples.

The values retain the native units of the compared state variables (mainly per
unit, with rotor angles in radians). Because the global metrics combine several
state types, they do not have one common physical unit. Per-state absolute and
normalized errors are available in each scenario's
`results/comparison/<SCENARIO>/per_state_error_metrics.csv` file. The table
below does not use the normalized RMSE column.

| Case | Base maximum absolute error | Base absolute RMSE | Event maximum absolute error | Event absolute RMSE |
|---|---:|---:|---:|---:|
| Kundur | `4.614090e-7` | `1.634310e-7` | `4.614090e-7` | `1.623597e-7` |
| IEEE14 | `1.169618e-4` | `1.189578e-5` | `1.169618e-4` | `8.522585e-6` |
| IEEE39 | `5.694499e-6` | `7.339123e-7` | `5.694629e-6` | `7.339001e-7` |
| NPCC140 | `4.776740e-7` | `6.554336e-8` | `4.777500e-7` | `6.554303e-8` |
| WECC179 | `1.535531e-3` | `4.515396e-5` | `1.535531e-3` | `3.827806e-5` |

The largest IEEE14 differences are localized in zero-time-constant ESST3A
`LAW2` states. The largest WECC179 differences occur in ESST3A and the IEEEG1
limiter chain; VeraGrid represents the normal interior-limiter branch, while
ANDES includes additional valve-rate and anti-windup behavior.


## Timing results

Each engine executes ten complete repetitions for every scenario. The reported
duration is the arithmetic mean and its uncertainty is the sample standard
deviation. Each engine directory writes the individual observations to
`timing_samples.csv`, the complete descriptive statistics to
`timing_statistics.csv`, and the means consumed by the comparator to
`timings.csv`. The phase comparison is written to
`results/comparison/<SCENARIO>/timing_comparison.csv`; both scenarios are also
consolidated in `results/timing_summary.txt`.

Every repetition rebuilds or reloads the case and creates a new dynamic
problem. Run one complete ANDES generator and the matching VeraGrid runner on
the same machine under comparable system load. The timing values characterize
that measured environment and are not general performance guarantees. The
benchmark records the installed ANDES version in the result metadata.

The numerical timing tables in this Markdown report are curated report
artifacts transcribed from the generated comparison CSV files. They report
`mean ± sample standard deviation` for the ten repetitions.

`ANDES/VG` is calculated as `ANDES seconds / VeraGrid seconds`. A value above
one is the factor by which VeraGrid was faster; a value below one means ANDES
was faster.

The directly comparable calculation stage is **RMS integration**, measured
after each engine has prepared and initialized its own problem. A separate
**post-power-flow workflow total** adds that engine-specific preparation to the
integration time. This workflow total answers how long each normal software
path takes after a solved power flow, but it is not a comparison of equivalent
internal preparation operations: ANDES reuses pregenerated numerical
functions, whereas VeraGrid constructs and compiles `RmsProblemDae` here.

Case/model construction and power flow are prerequisites and are outside the
reported calculation and workflow totals. Script overhead, ANDES–VeraGrid
comparison, PNG generation and result export are also excluded. Export time is
kept only as a phase-level diagnostic. The power-flow diagnostic always uses
the second solve in both engines; the first solve is excluded. All values are
wall-clock times, not CPU times.

### RMS integration: directly comparable calculation

| Case | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Kundur | 5.414615 ± 1.856615 | 3.965593 ± 1.153345 | 1.365 | 6.762453 ± 2.805028 | 6.974620 ± 0.538050 | 0.970 |
| IEEE14 | 18.688004 ± 1.788384 | 6.015145 ± 1.375258 | 3.107 | 30.499956 ± 1.724160 | 10.418102 ± 0.838289 | 2.928 |
| IEEE39 | 7.224755 ± 3.466185 | 11.845605 ± 0.964343 | 0.610 | 15.262547 ± 1.414052 | 22.604439 ± 1.445518 | 0.675 |
| NPCC140 | 7.142562 ± 1.037540 | 30.571816 ± 13.414692 | 0.234 | 12.916480 ± 1.299054 | 78.756701 ± 4.986353 | 0.164 |
| WECC179 | 15.428264 ± 1.357984 | 49.741284 ± 1.043232 | 0.310 | 64.333863 ± 15.846082 | 92.207225 ± 1.309779 | 0.698 |

### Post-power-flow workflow totals (architecture-dependent)

| Case | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Kundur | 5.518729 ± 1.841457 | 4.822109 ± 1.269407 | 1.144 | 6.827898 ± 2.838630 | 7.583715 ± 0.546392 | 0.900 |
| IEEE14 | 18.809339 ± 1.788085 | 7.739914 ± 1.383769 | 2.430 | 30.824915 ± 1.546609 | 12.313081 ± 0.836796 | 2.503 |
| IEEE39 | 7.313634 ± 3.501322 | 15.305193 ± 1.000791 | 0.478 | 15.376218 ± 1.329599 | 25.835393 ± 1.267568 | 0.595 |
| NPCC140 | 7.236551 ± 1.016468 | 41.612193 ± 16.829092 | 0.174 | 13.073083 ± 1.560770 | 91.578962 ± 5.824346 | 0.143 |
| WECC179 | 15.526179 ± 1.354005 | 66.135862 ± 1.832948 | 0.235 | 64.506117 ± 15.895182 | 108.385250 ± 1.543091 | 0.595 |

The base scenario simulates 1 s using 1,000 fixed steps. The event scenario
simulates 2 s using 2,000 fixed steps and splits the integration at `t = 0.2 s`
to apply the state discontinuity. Event and base totals therefore do not
represent the same amount of work and should not be compared as if the event
were only an additional callback.

### Phase-level timing comparison

The phase boundaries are the same for both engines:

1. **Case/model preparation (excluded prerequisite):** ANDES loads the case and
   creates model objects; VeraGrid loads the saved `MultiCircuit` and RMS models.
2. **Warm power flow (excluded prerequisite):** the second converged solve in
   each engine supplies the operating point used by the RMS equations.
3. **Engine-specific post-power-flow preparation:** ANDES `system.setup()` and
   `TDS.init()` reuse numerical functions generated before this phase;
   VeraGrid constructs, initializes and compiles `RmsProblemDae`, then
   allocates the solver and time grid. These are normal workflow stages, not
   equivalent internal operations.
4. **RMS integration:** all fixed Backward Euler steps over the requested
   horizon, including the event split when applicable.
5. **Result export (excluded diagnostic):** writing the trajectory files read
   by the comparator; this is outside the benchmark total.
6. **Workflow overhead (excluded diagnostic):** script time between explicit
   phase timers.

Rows marked **subcomponent** are already inside engine-specific preparation or
RMS integration. They explain where time is spent but must not be added again.
ANDES does not expose timers equivalent to VeraGrid's RHS, Jacobian and linear
solver breakdown, so those cells are dashes. The preparation row also omits
`ANDES/VG`, because its internal operations are not equivalent.

#### Kundur

| Phase | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Case/model preparation (excluded) | 0.707481 ± 0.713088 | 0.053587 ± 0.036401 | 13.202586 | 0.851818 ± 1.640693 | 0.042165 ± 0.004073 | 20.201793 |
| Warm power flow (excluded) | 0.013999 ± 0.003881 | 0.022066 ± 0.005369 | 0.634417 | 0.012637 ± 0.006830 | 0.025117 ± 0.005561 | 0.503108 |
| Engine-specific post-power-flow preparation | 0.104114 ± 0.029494 | 0.856516 ± 0.749028 | -- | 0.065445 ± 0.040528 | 0.609095 ± 0.044339 | -- |
| ↳ ANDES system setup (subcomponent) | 0.075439 ± 0.016309 | -- | -- | 0.049450 ± 0.034578 | -- | -- |
| ↳ ANDES TDS initialization (subcomponent) | 0.028675 ± 0.018524 | -- | -- | 0.015995 ± 0.008058 | -- | -- |
| ↳ VeraGrid RMS problem build and initialization (subcomponent) | -- | 0.856413 ± 0.749037 | -- | -- | 0.608977 ± 0.044348 | -- |
| ↳ VeraGrid solver and time-grid allocation (subcomponent) | -- | 0.000103 ± 0.000029 | -- | -- | 0.000118 ± 0.000030 | -- |
| RMS integration | 5.414615 ± 1.856615 | 3.965593 ± 1.153345 | 1.365399 | 6.762453 ± 2.805028 | 6.974620 ± 0.538050 | 0.969580 |
| ↳ VeraGrid RHS evaluation (subcomponent) | -- | 2.871941 ± 0.716241 | -- | -- | 5.296063 ± 0.487841 | -- |
| ↳ VeraGrid Jacobian assembly (subcomponent) | -- | 0.005760 ± 0.002038 | -- | -- | 0.004571 ± 0.000937 | -- |
| ↳ VeraGrid linear solver (subcomponent) | -- | 0.533153 ± 0.244729 | -- | -- | 0.794231 ± 0.080505 | -- |
| Result export | 0.288321 ± 0.060077 | 0.567124 ± 0.210182 | 0.508392 | 0.781089 ± 1.384985 | 1.135713 ± 0.156899 | 0.687752 |
| Workflow overhead (excluded) | 0.038386 ± 0.058280 | 0.001769 ± 0.000666 | 21.698116 | 0.025988 ± 0.018170 | 0.001807 ± 0.000266 | 14.378442 |
| **Post-power-flow workflow total** | **5.518729 ± 1.841457** | **4.822109 ± 1.269407** | **1.144464** | **6.827898 ± 2.838630** | **7.583715 ± 0.546392** | **0.900337** |

#### IEEE14

| Phase | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Case/model preparation (excluded) | 0.678834 ± 0.347049 | 0.191414 ± 0.132215 | 3.546412 | 0.497263 ± 0.102914 | 0.161849 ± 0.040094 | 3.072388 |
| Warm power flow (excluded) | 0.014491 ± 0.003389 | 0.023742 ± 0.006440 | 0.610377 | 0.013017 ± 0.003025 | 0.027322 ± 0.010435 | 0.476410 |
| Engine-specific post-power-flow preparation | 0.121336 ± 0.012349 | 1.724769 ± 0.120161 | -- | 0.324958 ± 0.687262 | 1.894979 ± 0.214050 | -- |
| ↳ ANDES system setup (subcomponent) | 0.072375 ± 0.014125 | -- | -- | 0.278895 ± 0.676031 | -- | -- |
| ↳ ANDES TDS initialization (subcomponent) | 0.048961 ± 0.009082 | -- | -- | 0.046064 ± 0.012063 | -- | -- |
| ↳ VeraGrid RMS problem build and initialization (subcomponent) | -- | 1.724680 ± 0.120158 | -- | -- | 1.894832 ± 0.214046 | -- |
| ↳ VeraGrid solver and time-grid allocation (subcomponent) | -- | 0.000090 ± 0.000020 | -- | -- | 0.000147 ± 0.000043 | -- |
| RMS integration | 18.688004 ± 1.788384 | 6.015145 ± 1.375258 | 3.106825 | 30.499956 ± 1.724160 | 10.418102 ± 0.838289 | 2.927592 |
| ↳ VeraGrid RHS evaluation (subcomponent) | -- | 4.644179 ± 0.810093 | -- | -- | 8.243595 ± 0.521795 | -- |
| ↳ VeraGrid Jacobian assembly (subcomponent) | -- | 0.006688 ± 0.004123 | -- | -- | 0.004855 ± 0.000895 | -- |
| ↳ VeraGrid linear solver (subcomponent) | -- | 0.611454 ± 0.288712 | -- | -- | 0.935325 ± 0.171505 | -- |
| Result export | 0.911584 ± 0.021237 | 1.254667 ± 0.448386 | 0.726554 | 1.874785 ± 0.078450 | 2.434696 ± 0.251812 | 0.770028 |
| Workflow overhead (excluded) | 0.021446 ± 0.003709 | 0.002011 ± 0.000336 | 10.662098 | 0.044599 ± 0.005621 | 0.002021 ± 0.000422 | 22.068990 |
| **Post-power-flow workflow total** | **18.809339 ± 1.788085** | **7.739914 ± 1.383769** | **2.430174** | **30.824915 ± 1.546609** | **12.313081 ± 0.836796** | **2.503428** |

#### IEEE39

| Phase | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Case/model preparation (excluded) | 0.450657 ± 0.103407 | 0.185857 ± 0.047158 | 2.424745 | 0.512287 ± 0.517226 | 0.172268 ± 0.015986 | 2.973770 |
| Warm power flow (excluded) | 0.017360 ± 0.009930 | 0.023333 ± 0.003337 | 0.744008 | 0.011159 ± 0.006251 | 0.026704 ± 0.001922 | 0.417886 |
| Engine-specific post-power-flow preparation | 0.088878 ± 0.038949 | 3.459587 ± 1.336747 | -- | 0.113671 ± 0.165880 | 3.230953 ± 0.914298 | -- |
| ↳ ANDES system setup (subcomponent) | 0.048653 ± 0.021118 | -- | -- | 0.033164 ± 0.018165 | -- | -- |
| ↳ ANDES TDS initialization (subcomponent) | 0.040225 ± 0.019306 | -- | -- | 0.080507 ± 0.162967 | -- | -- |
| ↳ VeraGrid RMS problem build and initialization (subcomponent) | -- | 3.459491 ± 1.336749 | -- | -- | 3.230815 ± 0.914291 | -- |
| ↳ VeraGrid solver and time-grid allocation (subcomponent) | -- | 0.000097 ± 0.000029 | -- | -- | 0.000139 ± 0.000017 | -- |
| RMS integration | 7.224755 ± 3.466185 | 11.845605 ± 0.964343 | 0.609910 | 15.262547 ± 1.414052 | 22.604439 ± 1.445518 | 0.675201 |
| ↳ VeraGrid RHS evaluation (subcomponent) | -- | 10.261001 ± 0.869552 | -- | -- | 19.742042 ± 1.148018 | -- |
| ↳ VeraGrid Jacobian assembly (subcomponent) | -- | 0.011177 ± 0.002531 | -- | -- | 0.010922 ± 0.001410 | -- |
| ↳ VeraGrid linear solver (subcomponent) | -- | 0.769579 ± 0.143964 | -- | -- | 1.408106 ± 0.324632 | -- |
| Result export | 1.392268 ± 0.620150 | 2.599903 ± 0.042185 | 0.535508 | 2.184169 ± 0.532716 | 5.522851 ± 1.099194 | 0.395479 |
| Workflow overhead (excluded) | 0.011877 ± 0.005527 | 0.002131 ± 0.000201 | 5.572439 | 0.015315 ± 0.002422 | 0.002123 ± 0.000189 | 7.212636 |
| **Post-power-flow workflow total** | **7.313634 ± 3.501322** | **15.305193 ± 1.000791** | **0.477853** | **15.376218 ± 1.329599** | **25.835393 ± 1.267568** | **0.595161** |

#### NPCC140

| Phase | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Case/model preparation (excluded) | 0.475921 ± 0.193164 | 0.947887 ± 0.688474 | 0.502086 | 0.444788 ± 0.193488 | 1.271799 ± 0.722100 | 0.349732 |
| Warm power flow (excluded) | 0.021804 ± 0.005646 | 0.029914 ± 0.014074 | 0.728907 | 0.023257 ± 0.009740 | 0.042952 ± 0.006246 | 0.541480 |
| Engine-specific post-power-flow preparation | 0.093989 ± 0.038868 | 11.040378 ± 4.253244 | -- | 0.156603 ± 0.280946 | 12.822261 ± 1.425917 | -- |
| ↳ ANDES system setup (subcomponent) | 0.058502 ± 0.037680 | -- | -- | 0.039225 ± 0.017740 | -- | -- |
| ↳ ANDES TDS initialization (subcomponent) | 0.035487 ± 0.007262 | -- | -- | 0.117379 ± 0.263694 | -- | -- |
| ↳ VeraGrid RMS problem build and initialization (subcomponent) | -- | 11.040249 ± 4.253203 | -- | -- | 12.822085 ± 1.425890 | -- |
| ↳ VeraGrid solver and time-grid allocation (subcomponent) | -- | 0.000128 ± 0.000064 | -- | -- | 0.000175 ± 0.000044 | -- |
| RMS integration | 7.142562 ± 1.037540 | 30.571816 ± 13.414692 | 0.233632 | 12.916480 ± 1.299054 | 78.756701 ± 4.986353 | 0.164005 |
| ↳ VeraGrid RHS evaluation (subcomponent) | -- | 28.470674 ± 12.642891 | -- | -- | 73.648554 ± 4.499490 | -- |
| ↳ VeraGrid Jacobian assembly (subcomponent) | -- | 0.038039 ± 0.014418 | -- | -- | 0.044094 ± 0.004778 | -- |
| ↳ VeraGrid linear solver (subcomponent) | -- | 1.147913 ± 0.416305 | -- | -- | 2.751529 ± 0.266381 | -- |
| Result export | 3.377710 ± 0.957777 | 7.637696 ± 3.267927 | 0.442242 | 6.203398 ± 1.240859 | 19.367823 ± 2.491876 | 0.320294 |
| Workflow overhead (excluded) | 0.014343 ± 0.006081 | 0.002693 ± 0.000796 | 5.326635 | 0.025140 ± 0.008357 | 0.004119 ± 0.001164 | 6.102987 |
| **Post-power-flow workflow total** | **7.236551 ± 1.016468** | **41.612193 ± 16.829092** | **0.173905** | **13.073083 ± 1.560770** | **91.578962 ± 5.824346** | **0.142752** |

#### WECC179

| Phase | Base ANDES mean ± std (s) | Base VG mean ± std (s) | Base ANDES/VG | Event ANDES mean ± std (s) | Event VG mean ± std (s) | Event ANDES/VG |
|---|---:|---:|---:|---:|---:|---:|
| Case/model preparation (excluded) | 0.609311 ± 0.338478 | 1.223058 ± 0.217041 | 0.498186 | 2.754308 ± 5.874513 | 1.318748 ± 0.160102 | 2.088579 |
| Warm power flow (excluded) | 0.005064 ± 0.001439 | 0.045473 ± 0.007952 | 0.111361 | 0.009714 ± 0.003736 | 0.047159 ± 0.003368 | 0.205975 |
| Engine-specific post-power-flow preparation | 0.097915 ± 0.025465 | 16.394578 ± 1.064780 | -- | 0.172254 ± 0.065361 | 16.178025 ± 0.642735 | -- |
| ↳ ANDES system setup (subcomponent) | 0.043644 ± 0.010824 | -- | -- | 0.083471 ± 0.035865 | -- | -- |
| ↳ ANDES TDS initialization (subcomponent) | 0.054271 ± 0.016299 | -- | -- | 0.088783 ± 0.030544 | -- | -- |
| ↳ VeraGrid RMS problem build and initialization (subcomponent) | -- | 16.394460 ± 1.064772 | -- | -- | 16.177856 ± 0.642724 | -- |
| ↳ VeraGrid solver and time-grid allocation (subcomponent) | -- | 0.000118 ± 0.000023 | -- | -- | 0.000169 ± 0.000034 | -- |
| RMS integration | 15.428264 ± 1.357984 | 49.741284 ± 1.043232 | 0.310170 | 64.333863 ± 15.846082 | 92.207225 ± 1.309779 | 0.697710 |
| ↳ VeraGrid RHS evaluation (subcomponent) | -- | 46.402634 ± 1.051873 | -- | -- | 86.406703 ± 1.222817 | -- |
| ↳ VeraGrid Jacobian assembly (subcomponent) | -- | 0.062388 ± 0.028651 | -- | -- | 0.051029 ± 0.004970 | -- |
| ↳ VeraGrid linear solver (subcomponent) | -- | 1.733330 ± 0.049897 | -- | -- | 3.028449 ± 0.074888 | -- |
| Result export | 4.004400 ± 1.207394 | 11.599637 ± 0.884120 | 0.345218 | 18.202422 ± 5.703137 | 22.658188 ± 0.676017 | 0.803349 |
| Workflow overhead (excluded) | 0.015387 ± 0.004447 | 0.003801 ± 0.000457 | 4.047831 | 0.084000 ± 0.027006 | 0.003832 ± 0.000385 | 21.920702 |
| **Post-power-flow workflow total** | **15.526179 ± 1.354005** | **66.135862 ± 1.832948** | **0.234762** | **64.506117 ± 15.895182** | **108.385250 ± 1.543091** | **0.595156** |

### Interpretation of the measured RMS timings

VeraGrid is faster for IEEE14, where the integration phase is approximately
three times faster than ANDES in both scenarios. Kundur is effectively close:
the mean favors VeraGrid slightly in the base scenario and ANDES slightly in
the event scenario, while the observed standard deviations overlap.

ANDES is faster in the directly comparable integration stage for IEEE39,
NPCC140 and WECC179. For NPCC140 and WECC179, VeraGrid integration is dominated
by RHS evaluation: approximately 93% of its integration time in both large
systems. Jacobian assembly is small in these measurements, and the linear solve
is a secondary cost; neither is the principal integration bottleneck.

The broader post-power-flow workflow also favors ANDES for those systems, but
its preparation difference must be interpreted only as normal-path elapsed
time. ANDES setup and initialization reuse pregenerated numerical functions,
whereas VeraGrid performs RMS-problem construction and numerical compilation
inside the measured phase. The preparation timings are therefore shown without
a ratio and are not evidence of one engine executing the same operation faster.

Some measurements are noisy. Notably, NPCC140 VeraGrid base and WECC179 ANDES
event have large standard deviations, and some preparation phases show
different timing regimes between repetitions. Their means describe these ten
observations, but small differences or ratios near one should not be treated as
stable rankings without controlling background system load more tightly.


## Result figures

Each scenario's `comparison/` directory contains the trajectory error envelope,
segment comparison, timing comparison and a representative-state trajectory
figure. The selected states are those that make the largest or most informative
physical differences visible.

### Kundur

![Kundur representative RMS states](RMS/Kundur/results/comparison/base/representative_state_trajectories.png)

![Kundur representative RMS event states](RMS/Kundur/results/comparison/event/representative_state_trajectories.png)

### IEEE14

![IEEE14 representative RMS states](RMS/IEEE14/results/comparison/base/representative_state_trajectories.png)

![IEEE14 representative RMS event states](RMS/IEEE14/results/comparison/event/representative_state_trajectories.png)

### IEEE39

![IEEE39 representative RMS states](RMS/IEEE39/results/comparison/base/representative_state_trajectories.png)

![IEEE39 representative RMS event states](RMS/IEEE39/results/comparison/event/representative_state_trajectories.png)

### NPCC140

![NPCC140 representative RMS states](RMS/NPCC140/results/comparison/base/representative_state_trajectories.png)

![NPCC140 representative RMS event states](RMS/NPCC140/results/comparison/event/representative_state_trajectories.png)

### WECC179

![WECC179 representative RMS states](RMS/WECC179/results/comparison/base/representative_state_trajectories.png)

![WECC179 representative RMS event states](RMS/WECC179/results/comparison/event/representative_state_trajectories.png)
