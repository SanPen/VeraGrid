# ANDES versus VeraGrid: RMS small-signal benchmark

For the exact execution order, start with [README.md](README.md).

This benchmark compares the RMS linearization calculated by VeraGrid with
saved results from ANDES. It covers the Kundur two-area system, IEEE14,
IEEE39, NPCC140 and WECC179.

Each case has one explicit runner in its own system folder. Running that file loads
the saved case, solves the VeraGrid power flow, calculates the complete small-signal
spectrum, writes the VeraGrid results and compares them with the saved ANDES
results for the same case. The `.veragrid` fixtures are stored in `src/tests/data/dynamics_andes/` and
created by the separate `generate_fixtures.py` authoring script.

## Directory layout

For every case, the result directory has the same structure:

```text
<SYSTEM>/
├── run_<SYSTEM>_small_signal.py
├── system construction files
└── results/
    ├── ANDES/       Saved reference calculation
    ├── VeraGrid/    Result produced by the case runner
    ├── comparison/  Numerical differences, report and PNG figures
    └── timing_summary.txt
```

The five runners are:

| Case | Runner |
|---|---|
| Kundur | `small_signal/Kundur/run_Kundur_small_signal.py` |
| IEEE14 | `small_signal/IEEE14/run_IEEE14_small_signal.py` |
| IEEE39 | `small_signal/IEEE39/run_IEEE39_small_signal.py` |
| NPCC140 | `small_signal/NPCC140/run_NPCC140_small_signal.py` |
| WECC179 | `small_signal/WECC179/run_WECC179_small_signal.py` |

Every runner contains one execution function with the same five numbered
stages: build the case, solve power flow, calculate the spectrum, save the
numerical files and compare against ANDES. Device declarations are stored in
the matching `<case>_benchmark_case.py` file.

Open the required runner in PyCharm and use **Run** with the repository root as
the working directory. The runner expects the matching `ANDES/` directory to exist. The reference is
created separately with `generate_andes_small_signal_results.py`. Reference
generation is separate from VeraGrid simulation and comparison.

## Comparison contract

The comparison follows four stages in order:

1. verify that both linearizations start from the same solved power-flow
   operating point;
2. align the common physical differential states and report excluded
   implementation-specific states;
3. compare the state matrices and match every eigenvalue one-to-one in the
   complex plane;
4. compare participation factors for non-repeated modes.

Repeated WECC179 modes remain in the eigenvalue comparison and spectrum. Their
individual participation vectors are excluded because a repeated eigenspace
does not have a unique eigenvector basis.

## Numerical results

Each benchmark run writes the numerical files under the corresponding
`VeraGrid/` and `comparison/` directories and writes the case's
`results/timing_summary.txt`.

| Case | Modes | Mean eigenvalue error | Maximum eigenvalue error | Relative matrix error | Relative participation error |
|---|---:|---:|---:|---:|---:|
| Kundur | 8 | 0.000036% | 0.000070% | `1.692291e-10` | `2.502877e-5` |
| IEEE14 | 56 | 0.000001% | 0.000009% | `1.835490e-9` | `0` |
| IEEE39 | 130 | 0.000012% | 0.000074% | `6.902046e-8` | `7.682958e-6` |
| NPCC140 | 334 | <0.000001% | 0.000008% | `5.657571e-8` | `2.248776e-6` |
| WECC179 | 507 | 0.000040% | 0.000559% | `6.023567e-7` | `3.075126e-5` |

The solved bus voltages are checked only as a prerequisite for the dynamic
comparison. Their detailed differences remain in each case's
`results/comparison/comparison_report.txt`; they are not small-signal results
and are therefore not included in the summary tables here.

## Timing interpretation

`ANDES/VG` is ANDES seconds divided by VeraGrid seconds. A value above one is
the factor by which VeraGrid was faster; a value below one means ANDES was
faster.

The timing boundary starts when the steady-state operating point is already
available. The primary comparison is the **small-signal calculation**, measured
after each engine has prepared and initialized its own problem. One additional
workflow total is reported:

- **Post-power-flow workflow total** = engine-specific post-power-flow
  preparation + small-signal calculation.

Case/model construction and power flow are prerequisites and are outside the
total. Script overhead, warm-up calls, ANDES–VeraGrid comparison, PNG
generation and result export are also excluded. The workflow total measures
the elapsed normal path of each engine after power flow, but their preparation
components are not equivalent internal operations. ANDES reuses pregenerated
numerical functions, whereas VeraGrid constructs and numerically compiles the
RMS problem in the measured preparation phase. All values are wall-clock
times, not CPU times.

Each engine executes ten complete repetitions. The reported duration is the
arithmetic mean and its uncertainty is the sample standard deviation. Raw
observations are stored in each engine's `timing_samples.csv`; sample count,
mean, sample standard deviation, median, minimum and maximum are stored in
`timing_statistics.csv`. The values characterize the measured environment and
are not general performance guarantees. The installed ANDES version is saved
with the generated results.

The numerical timing tables in this Markdown report are curated report
artifacts transcribed from the generated comparison CSV files. They report
`mean ± sample standard deviation` for the ten repetitions.

### Small-signal calculation: directly comparable calculation

| Case | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Kundur | 0.000893 ± 0.000191 | 0.001717 ± 0.000494 | 0.520 |
| IEEE14 | 0.003304 ± 0.000737 | 0.006844 ± 0.010778 | 0.483 |
| IEEE39 | 0.304851 ± 0.093430 | 0.016564 ± 0.000904 | 18.404 |
| NPCC140 | 1.043203 ± 0.399341 | 0.253027 ± 0.086723 | 4.123 |
| WECC179 | 1.174386 ± 0.449940 | 0.428232 ± 0.160363 | 2.742 |

### Post-power-flow workflow totals (architecture-dependent)

| Case | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Kundur | 0.044340 ± 0.009668 | 0.161635 ± 0.005548 | 0.274 |
| IEEE14 | 0.067438 ± 0.006387 | 0.593131 ± 0.129084 | 0.114 |
| IEEE39 | 0.411049 ± 0.114728 | 0.892825 ± 0.097345 | 0.460 |
| NPCC140 | 1.274944 ± 0.762382 | 11.329419 ± 4.821830 | 0.113 |
| WECC179 | 1.347892 ± 0.438019 | 11.982219 ± 6.233291 | 0.112 |

The exact phase boundaries are:

1. **Case/model preparation (excluded prerequisite):** ANDES loads the case and
   creates model objects; VeraGrid loads the saved `MultiCircuit` and RMS models.
2. **Warm power flow (excluded prerequisite):** both engines execute one
   excluded solve and use the second solve to produce the operating point.
3. **Engine-specific post-power-flow preparation:** ANDES `system.setup()`,
   `TDS.init()` and benchmark state folding reuse numerical functions generated
   outside this phase; VeraGrid constructs and explicitly initializes
   `RmsProblemDae` and numerically compiles its RHS and Jacobians. These are
   normal stages in each engine's workflow, but they are not equivalent
   internal operations and their phase ratio must not be read as a like-for-like
   preparation benchmark.
4. **Small-signal calculation:** the second complete call after warm-up,
   including state matrix, eigensolution, participation factors and result
   assembly.
5. **Result export (excluded diagnostic):** writing the numerical files read by
   the comparator; this is outside the benchmark total.
6. **Workflow overhead (excluded diagnostic):** script time between explicit
   phase timers.

Rows marked **subcomponent** are already included in engine-specific
post-power-flow preparation and must not be added again. Rows marked
**excluded diagnostic** are warm profiling repeats and are outside the
workflow total. A dash means that the phase belongs to only one engine.
Power-flow time is omitted from the tables below because it is outside the
dynamic benchmark. The raw timing artifact records the second, warm solve
separately.
The preparation row shows both elapsed workflow costs but deliberately omits
`ANDES/VG`, because its internal operations are not equivalent.

Both engines execute one complete small-signal call as an excluded warm-up and
then measure a second complete call on the same initialized problem. The
**small-signal calculation** row therefore compares warm ANDES `EIG.run()` with
warm VeraGrid `SmallSignalStabilityRmsDriver.run()` under the same cache
condition. The warm-up duration is recorded separately and belongs to neither
workflow total.

The measured call includes state-matrix construction, the complete
eigensolution, left and right eigenvectors, participation factors, modal
post-processing and result-object construction. It excludes RMS-problem
preparation, file export, the ANDES–VeraGrid comparison and figure generation.
It is therefore a full calculation-stage measurement, not an isolated matrix-A
or eigensolver microbenchmark.

### Kundur timing phases

| Phase | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Case/model preparation (excluded) | 0.308270 ± 0.213060 | 0.015123 ± 0.012669 | 20.384350 |
| Engine-specific post-power-flow preparation | 0.043447 ± 0.009649 | 0.159918 ± 0.005635 | -- |
| ↳ ANDES system setup | 0.031828 ± 0.009448 | -- | -- |
| ↳ ANDES TDS initialization | 0.011603 ± 0.002086 | -- | -- |
| ↳ ANDES benchmark state folding | 0.000016 ± 0.000004 | -- | -- |
| ↳ VeraGrid RMS problem preparation | -- | 0.159918 ± 0.005635 | -- |
| Small-signal calculation | 0.000893 ± 0.000191 | 0.001717 ± 0.000494 | 0.520056 |
| Result export | 0.024253 ± 0.005350 | 0.003859 ± 0.000894 | 6.285482 |
| Workflow overhead (excluded) | 0.001224 ± 0.000355 | 0.000478 ± 0.000053 | 2.561057 |
| **Post-power-flow workflow total** | **0.044340 ± 0.009668** | **0.161635 ± 0.005548** | **0.274324** |
| Excluded first calculation (warm-up) | 0.002697 ± 0.005827 | 0.004732 ± 0.009371 | 0.569863 |

### IEEE14 timing phases

| Phase | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Case/model preparation (excluded) | 0.452683 ± 0.145053 | 0.059998 ± 0.052593 | 7.544936 |
| Engine-specific post-power-flow preparation | 0.064134 ± 0.006234 | 0.586287 ± 0.118347 | -- |
| ↳ ANDES system setup | 0.029465 ± 0.004058 | -- | -- |
| ↳ ANDES TDS initialization | 0.034539 ± 0.005879 | -- | -- |
| ↳ ANDES benchmark state folding | 0.000130 ± 0.000050 | -- | -- |
| ↳ VeraGrid RMS problem preparation | -- | 0.586287 ± 0.118347 | -- |
| Small-signal calculation | 0.003304 ± 0.000737 | 0.006844 ± 0.010778 | 0.482768 |
| Result export | 0.038713 ± 0.009621 | 0.009013 ± 0.003337 | 4.295376 |
| Workflow overhead (excluded) | 0.001607 ± 0.000416 | 0.000520 ± 0.000082 | 3.091647 |
| **Post-power-flow workflow total** | **0.067438 ± 0.006387** | **0.593131 ± 0.129084** | **0.113698** |
| Excluded first calculation (warm-up) | 0.003351 ± 0.000725 | 0.103368 ± 0.314346 | 0.032418 |

### IEEE39 timing phases

| Phase | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Case/model preparation (excluded) | 0.684935 ± 0.447037 | 0.052313 ± 0.015070 | 13.093036 |
| Engine-specific post-power-flow preparation | 0.106198 ± 0.033765 | 0.876261 ± 0.096775 | -- |
| ↳ ANDES system setup | 0.052199 ± 0.021511 | -- | -- |
| ↳ ANDES TDS initialization | 0.053290 ± 0.014374 | -- | -- |
| ↳ ANDES benchmark state folding | 0.000709 ± 0.000140 | -- | -- |
| ↳ VeraGrid RMS problem preparation | -- | 0.876261 ± 0.096775 | -- |
| Small-signal calculation | 0.304851 ± 0.093430 | 0.016564 ± 0.000904 | 18.404064 |
| Result export | 0.121993 ± 0.020726 | 0.025671 ± 0.000925 | 4.752123 |
| Workflow overhead (excluded) | 0.001915 ± 0.000248 | 0.000591 ± 0.000049 | 3.238245 |
| **Post-power-flow workflow total** | **0.411049 ± 0.114728** | **0.892825 ± 0.097345** | **0.460391** |
| Excluded first calculation (warm-up) | 0.461423 ± 0.158739 | 0.020125 ± 0.011124 | 22.927806 |

### NPCC140 timing phases

| Phase | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Case/model preparation (excluded) | 0.495710 ± 0.145471 | 0.836118 ± 0.299301 | 0.592871 |
| Engine-specific post-power-flow preparation | 0.231741 ± 0.430342 | 11.076392 ± 4.742415 | -- |
| ↳ ANDES system setup | 0.175876 ± 0.411569 | -- | -- |
| ↳ ANDES TDS initialization | 0.055744 ± 0.020969 | -- | -- |
| ↳ ANDES benchmark state folding | 0.000122 ± 0.000077 | -- | -- |
| ↳ VeraGrid RMS problem preparation | -- | 11.076392 ± 4.742415 | -- |
| Small-signal calculation | 1.043203 ± 0.399341 | 0.253027 ± 0.086723 | 4.122888 |
| Result export | 0.472218 ± 0.072028 | 0.557524 ± 0.236240 | 0.846992 |
| Workflow overhead (excluded) | 0.002478 ± 0.000545 | 0.001678 ± 0.000516 | 1.476782 |
| **Post-power-flow workflow total** | **1.274944 ± 0.762382** | **11.329419 ± 4.821830** | **0.112534** |
| Excluded first calculation (warm-up) | 1.267758 ± 0.556008 | 0.255225 ± 0.093350 | 4.967220 |

### WECC179 timing phases

| Phase | ANDES mean ± std (s) | VeraGrid mean ± std (s) | ANDES/VG |
|---|---:|---:|---:|
| Case/model preparation (excluded) | 0.690487 ± 0.209349 | 1.446129 ± 1.278574 | 0.477473 |
| Engine-specific post-power-flow preparation | 0.173506 ± 0.066723 | 11.553987 ± 6.075203 | -- |
| ↳ ANDES system setup | 0.073154 ± 0.030091 | -- | -- |
| ↳ ANDES TDS initialization | 0.098308 ± 0.037698 | -- | -- |
| ↳ ANDES benchmark state folding | 0.002044 ± 0.001050 | -- | -- |
| ↳ VeraGrid RMS problem preparation | -- | 11.553987 ± 6.075203 | -- |
| Small-signal calculation | 1.174386 ± 0.449940 | 0.428232 ± 0.160363 | 2.742408 |
| Result export | 1.919998 ± 0.973777 | 1.090569 ± 0.478865 | 1.760547 |
| Workflow overhead (excluded) | 0.003387 ± 0.000710 | 0.001807 ± 0.000944 | 1.874084 |
| **Post-power-flow workflow total** | **1.347892 ± 0.438019** | **11.982219 ± 6.233291** | **0.112491** |
| Excluded first calculation (warm-up) | 1.537091 ± 1.059676 | 0.436794 ± 0.165856 | 3.519031 |

## Interpretation of the measured small-signal timings

The architecture-dependent post-power-flow workflow total favors ANDES in all
five systems. This does not establish that ANDES performs the same preparation
faster: the two engines do different work inside that phase and place numerical
generation at different points in their lifecycle. The total is useful only as
the elapsed time of each engine's normal path from a solved power flow to a
small-signal result.

Once both problems are already initialized and warmed, the directly comparable
calculation gives a different result. ANDES is faster for Kundur and IEEE14,
but VeraGrid is about 18.4 times faster for IEEE39, 4.1 times faster for
NPCC140 and 2.7 times faster for WECC179. VeraGrid therefore does not lose the
large-system comparison in the state-matrix/eigenvalue calculation. The
difference in the broader workflow total occurs before that calculation, in
engine-specific preparation that must not be interpreted as a phase-for-phase
speed ratio.

The high standard deviations for NPCC140 and WECC179 preparation show that
those timings changed substantially between repetitions. IEEE14's VeraGrid
small-signal calculation also contains an isolated slow observation. The mean
is the agreed summary statistic, but the accompanying deviation must be kept
when interpreting these results.

## Result figures

Every `comparison/` directory contains the complete s-domain spectrum plus
state-matrix, participation-factor and timing diagnostics. Figures are saved
before any optional interactive display so that a normal run always leaves a
reviewable result.

### Kundur

![Kundur ANDES and VeraGrid eigenvalues](small_signal/Kundur/results/comparison/sdomain_eigenvalues.png)

### IEEE14

![IEEE14 ANDES and VeraGrid eigenvalues](small_signal/IEEE14/results/comparison/sdomain_eigenvalues.png)

### IEEE39

![IEEE39 ANDES and VeraGrid eigenvalues](small_signal/IEEE39/results/comparison/sdomain_eigenvalues.png)

### NPCC140

![NPCC140 ANDES and VeraGrid eigenvalues](small_signal/NPCC140/results/comparison/sdomain_eigenvalues.png)

### WECC179

![WECC179 ANDES and VeraGrid eigenvalues](small_signal/WECC179/results/comparison/sdomain_eigenvalues.png)
