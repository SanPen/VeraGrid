# ANDES versus VeraGrid dynamics benchmarks

This benchmark suite compares VeraGrid and ANDES on the Kundur, IEEE14,
IEEE39, NPCC140 and WECC179 systems. It covers RMS time-domain simulation and
RMS small-signal stability, including numerical agreement and computation
times.

Use the Python environment where VeraGrid and ANDES are installed and keep the
VeraGrid repository root as the working directory.

The five VeraGrid fixtures are stored in `src/tests/data/dynamics_andes/`.
To refresh them after changing a case builder, run `generate_fixtures.py` once.
The benchmark runners do not call that authoring script.

There are always two benchmark steps:

1. Generate the saved ANDES reference.
2. Run the matching VeraGrid file. That same file saves the VeraGrid result,
   compares it with ANDES and creates the comparison PNG files.

The comparison scripts do **not** need to be run separately.

Every generator and case runner performs **10 complete repetitions
automatically**. Run each listed file once; do not launch it manually ten
times. The repetition count is the visible `repetitions: int = 10` line near
the start of its execution function.

## Files to run, in order

### Small signal

First open `small_signal/generate_andes_small_signal_results.py`. The system
is selected near the top of the file with one line:

```python
SYSTEM = "all"
```

`"all"` generates all five systems. Use `SYSTEM = "IEEE14"` to generate only
IEEE14. Run that file. Then run these five files, from top to bottom. Each file
loads its saved `.veragrid` system, runs VeraGrid, saves the numerical result and creates the
comparison figures:

1. `small_signal/Kundur/run_Kundur_small_signal.py`
2. `small_signal/IEEE14/run_IEEE14_small_signal.py`
3. `small_signal/IEEE39/run_IEEE39_small_signal.py`
4. `small_signal/NPCC140/run_NPCC140_small_signal.py`
5. `small_signal/WECC179/run_WECC179_small_signal.py`

### RMS time domain

First open `RMS/generate_andes_rms_results.py`. The system and scenario are
selected near the top of the file:

```python
SYSTEM = "all"
SCENARIO = "all"
```

With both values at `"all"`, the file generates every system and both the
`base` and `event` scenarios. Run that file.

Then run the five VeraGrid benchmarks. Each file runs both the `base` and
`event` scenarios and compares both results:

1. `RMS/Kundur/run_Kundur_rms.py`
2. `RMS/IEEE14/run_IEEE14_rms.py`
3. `RMS/IEEE39/run_IEEE39_rms.py`
4. `RMS/NPCC140/run_NPCC140_rms.py`
5. `RMS/WECC179/run_WECC179_rms.py`

## Run only one system

For IEEE14 small signal:

1. Set `SYSTEM = "IEEE14"` near the top of
   `generate_andes_small_signal_results.py` and run that file.
2. Run `small_signal/IEEE14/run_IEEE14_small_signal.py`.

For IEEE14 RMS:

1. Set `SYSTEM = "IEEE14"` near the top of
   `generate_andes_rms_results.py`. Leave `SCENARIO = "all"` to
   generate both scenarios, and run the file.
2. Run `RMS/IEEE14/run_IEEE14_rms.py`.

Choose the matching system name and `run_<SYSTEM>_*.py` file for the other systems.

The ANDES generator is required whenever benchmark timings are refreshed,
because both engines must contribute ten repetitions from the same machine and
measurement session. It may be skipped only when the saved ANDES artifacts
already follow this ten-repetition protocol and only VeraGrid needs to be
regenerated.

In PyCharm, open the corresponding `.py` file and use **Run**. Set the
repository root as the working directory. None of the generator or `run_*`
files needs script parameters.

## Result locations

Small signal writes:

```text
small_signal/<SYSTEM>/
├── run_<SYSTEM>_small_signal.py
└── results/
    ├── ANDES/       Reference generated once
    ├── VeraGrid/    VeraGrid benchmark calculation
    ├── comparison/  Error tables, report and PNG figures
    └── timing_summary.txt
```

RMS writes:

```text
RMS/<SYSTEM>/
├── run_<SYSTEM>_rms.py
└── results/
    ├── ANDES/base/ and ANDES/event/
    ├── VeraGrid/base/ and VeraGrid/event/
    ├── comparison/base/ and comparison/event/
    └── timing_summary.txt
```

A benchmark run writes numerical CSV/JSON results into these folders. Every
system also gets a `results/timing_summary.txt`: small signal contains its
complete phase breakdown, while RMS consolidates both the base and event
breakdowns in one file. Each timing summary distinguishes the directly
comparable calculation from the architecture-dependent post-power-flow
workflow total and states exactly which operations belong to every phase.
Subcomponent rows are
diagnostic detail already included in a parent phase, not extra time to add.
The output artifacts include
representative PNG figures and the summary tables presented in the two
Markdown reports. The benchmark does not create or require `.veragrid`
snapshots.

Each engine result directory contains three timing levels:

- `timing_samples.csv` contains every measured phase from repetitions 1 to 10;
- `timing_statistics.csv` contains the sample count, arithmetic mean, sample
  standard deviation, median, minimum and maximum for every phase;
- `timings.csv` for RMS, or `timings_results_<ENGINE>_<CASE>.csv` for small
  signal, exposes the arithmetic means used by the comparator.

The comparison CSV files, timing summaries and timing figures use the mean of
the ten repetitions. Their uncertainty is the sample standard deviation
(`ddof=1`). RMS timing bars show mean ± sample standard deviation; the
small-signal timing table shows the same pair numerically. Median, minimum and
maximum remain available in `timing_statistics.csv` for diagnosing noisy or
atypical runs.

Each repetition starts from a newly built or newly loaded case and a new
dynamic problem. Small signal also executes one excluded warm-up calculation
inside every repetition and measures the second calculation for both engines.
The last repetition supplies the numerical trajectories, matrices and
eigenvalues used for the agreement comparison; these deterministic numerical
results are not averaged.

The directly comparable calculation stage is **RMS integration** for the
time-domain benchmark and **small-signal calculation** for the modal benchmark.
The separate **post-power-flow workflow total** adds each engine's own
preparation stage. That total measures practical elapsed workflow time, but its
preparation components are not internally equivalent: ANDES reuses
pregenerated numerical functions, whereas VeraGrid constructs and compiles the
RMS problem at this point. Case/model construction and power flow remain
excluded. Result-file export is retained only as a diagnostic phase and is not
added to a benchmark total. Script overhead, warm-ups, comparison and figure
generation also remain outside. All reported durations are wall-clock times,
not CPU times.

For methodology and benchmark results, see [small_signal.md](small_signal.md)
and [rms.md](rms.md).
