"""Compare the measured five- and twenty-second WECC 240 timing baselines."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent / "results"
FIVE = ROOT / "five_second_wecc"
TWENTY = ROOT / "ten_run_timing"
COLORS = {"VeraGrid": "#127c92", "Julia": "#c65b37"}


def warm(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame.case == "wecc_240"]
    assert sorted(frame.repetition.tolist()) == list(range(1, 11)), path
    assert frame.select_dtypes("number").notna().all().all(), path
    return frame[frame.repetition > 1]


def fmt(frame: pd.DataFrame, column: str) -> str:
    values = frame[column]
    return f"{values.median():.2f} [{values.quantile(.1):.2f}, {values.quantile(.9):.2f}]"


def main() -> None:
    data = {
        (5, "VeraGrid"): warm(FIVE / "veragrid.csv"),
        (5, "Julia"): warm(FIVE / "julia.csv"),
        (20, "VeraGrid"): warm(TWENTY / "veragrid.csv"),
        (20, "Julia"): warm(TWENTY / "julia.csv"),
    }
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 160})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5), layout="constrained")
    for ax, column, title in (
        (axes[0], "integration_s", "Integration only"),
        (axes[1], "total_s", "Complete setup and integration"),
    ):
        for engine in ("VeraGrid", "Julia"):
            medians = [data[horizon, engine][column].median() for horizon in (5, 20)]
            ax.plot((5, 20), medians, marker="o", markersize=8, linewidth=2,
                    color=COLORS[engine], label=engine)
            for horizon in (5, 20):
                values = data[horizon, engine][column]
                x = horizon + (-.35 if engine == "VeraGrid" else .35)
                ax.scatter([x] * len(values), values, s=13, alpha=.4,
                           color=COLORS[engine])
        ax.set(xlabel="Simulated seconds", ylabel="Measured seconds", title=title)
        ax.set_xticks((5, 20))
        ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.suptitle("WECC 240: nine warm runs per horizon (dots) and medians (lines)")
    fig.savefig(FIVE / "horizon_comparison.png", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), layout="constrained")
    phase_specs = (
        ("VeraGrid", ("rhs_evaluation_s", "jacobian_evaluation_s", "linear_solver_s", "other_integration_s"),
         ("RHS", "Jacobian", "Factorization + solve", "Other")),
        ("Julia", ("rhs_evaluation_s", "jacobian_evaluation_s", "unattributed_integration_s"),
         ("RHS callback", "Jacobian callback", "Unattributed*")),
    )
    palette = ("#27839a", "#e49c46", "#665b98", "#b6bec6")
    for ax, (engine, columns, labels) in zip(axes, phase_specs):
        bottom = np.zeros(2)
        for idx, (column, label) in enumerate(zip(columns, labels)):
            heights = np.array([data[horizon, engine][column].median() for horizon in (5, 20)])
            ax.bar(("5 s", "20 s"), heights, bottom=bottom, color=palette[idx], label=label)
            bottom += heights
        ax.set(ylabel="Median integration seconds", title=engine)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle("Where integration time grows as the horizon increases")
    fig.savefig(FIVE / "phase_growth.png", bbox_inches="tight")
    plt.close(fig)

    lines = [
        "# WECC 240: five-second baseline and horizon study",
        "",
        "The WECC 240 line trip occurs at `t = 1 s`. Each engine ran ten fresh simulations at each horizon. Tables show the median [10th, 90th percentile] over nine warm runs; the first run is retained in the raw data. See [methods](METHODS.md) for solver settings and reproduction.",
        "",
        "![Five- and twenty-second timing comparison](horizon_comparison.png)",
        "",
        "| Horizon | VeraGrid integration (s) | Julia integration (s) | Julia / VeraGrid | VeraGrid total (s) | Julia total (s) | VeraGrid RMSE (p.u.) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for horizon in (5, 20):
        v, j = data[horizon, "VeraGrid"], data[horizon, "Julia"]
        lines.append(f"| {horizon} s | {fmt(v, 'integration_s')} | {fmt(j, 'integration_s')} | "
                     f"{j.integration_s.median()/v.integration_s.median():.2f}× | "
                     f"{fmt(v, 'total_s')} | {fmt(j, 'total_s')} | {v.rmse.median():.3g} |")
    lines += ["", "![Growth by measured integration phase](phase_growth.png)", "",
              "| Engine and phase | 5 s median | 20 s median | Added time |",
              "|---|---:|---:|---:|"]
    phase_rows = (
        ("VeraGrid RHS", "VeraGrid", "rhs_evaluation_s"),
        ("VeraGrid Jacobian", "VeraGrid", "jacobian_evaluation_s"),
        ("VeraGrid factorization + solve", "VeraGrid", "linear_solver_s"),
        ("VeraGrid other", "VeraGrid", "other_integration_s"),
        ("Julia RHS callback", "Julia", "rhs_evaluation_s"),
        ("Julia Jacobian callback", "Julia", "jacobian_evaluation_s"),
        ("Julia unattributed*", "Julia", "unattributed_integration_s"),
    )
    for label, engine, column in phase_rows:
        five = data[5, engine][column].median()
        twenty = data[20, engine][column].median()
        lines.append(f"| {label} | {five:.2f} s | {twenty:.2f} s | {twenty-five:+.2f} s |")
    v5, v20 = data[5, "VeraGrid"], data[20, "VeraGrid"]
    j5, j20 = data[5, "Julia"], data[20, "Julia"]
    lines += [
        "",
        f"VeraGrid accepted a median of {v5.accepted_steps.median():.0f} steps at five seconds and {v20.accepted_steps.median():.0f} at twenty seconds. With the same maximum internal step, the extra 15 simulated seconds add approximately {v20.accepted_steps.median()-v5.accepted_steps.median():.0f} accepted steps. Its additional integration time is {v20.integration_s.median()-v5.integration_s.median():.2f} s, versus {j20.integration_s.median()-j5.integration_s.median():.2f} s for Julia. The measured phase growth indicates that VeraGrid's repeated RHS evaluations account for much of the narrowing advantage. This is an inference from phase times; the Julia linear-solver time is not isolated.",
        "",
        "*Julia unattributed time includes linear solves, solver control, event handling, output, and timing overhead. It is not a linear-solver measurement. The implementations use different adaptive algorithms. The speed comparison must be read with trajectory error: VeraGrid RMSE is measured against the committed Julia reference over each horizon, using the same `1e-6` absolute and `1e-3` relative BDF tolerances at both horizons.*",
        "",
        "Raw measurements: [`julia.csv`](julia.csv), [`veragrid.csv`](veragrid.csv). The [ten-run timing report](../ten_run_timing/RESULTS.md) includes the other cases.",
        "",
        "## Numba compiled follow-up",
        "",
        "The [Numba compiled WECC comparison](../numba_comp_wecc/RESULTS.md) shows preliminary 5- and 20-second runs of the fixed compiled RHS backend, including a timing plot and phase breakdown. It uses two warm compiled runs per horizon; the tables above retain the original nine-warm-run baseline.",
    ]
    methods = [
        "# WECC 240 five-second benchmark methods",
        "",
        "[Results and plots](RESULTS.md).",
        "",
        "## Setup and timing",
        "",
        "The line trip occurs at `t = 1 s`. VeraGrid loads the committed `.veragrid` fixture and runs `PowerBalanceVectorized` with adaptive BDF1–5 and sparse LU. Julia builds the matching model through PowerSystemCaseBuilder and runs PowerSimulationsDynamics.jl with Sundials IDA. Both save results every `0.01 s` and cap internal steps at `0.01 s`. VeraGrid BDF absolute and relative tolerances are `1e-6` and `1e-3`. The engines ran sequentially on the same host, ten fresh runs each. Repetition 1 is cold; summaries use repetitions 2–10.",
        "",
        "VeraGrid times RHS evaluation, Jacobian evaluation, and sparse factorization plus triangular solve separately inside integration. Julia times RHS and Jacobian callbacks; its unattributed integration time includes linear solves, solver control, event handling, output, and timing overhead. Julia linear-solver time is not isolated. Total time includes setup and simulation build. VeraGrid RMSE compares the trajectory against the committed Julia reference CSV, rather than a trajectory regenerated in this run.",
        "",
        "## Raw measurements and reproduction",
        "",
        "The five-second measurements are [`julia.csv`](julia.csv) and [`veragrid.csv`](veragrid.csv). The [ten-run timing report](../ten_run_timing/RESULTS.md) contains its own CSVs and additional plots. Both benchmark scripts live in `benchmarks/powersystems_julia/`.",
        "",
        "```bash",
        "julia --startup-file=no --project=\"../power systems julia\" benchmarks/powersystems_julia/measure_ten_julia.jl wecc_240 5.0 benchmarks/powersystems_julia/results/five_second_wecc/julia.csv 10",
        "PYTHONPATH=src:. /home/pablo/myenv/bin/python benchmarks/powersystems_julia/measure_ten_veragrid.py --case wecc_240 --duration 5 --repetitions 10 --output benchmarks/powersystems_julia/results/five_second_wecc/veragrid.csv",
        "PYTHONPATH=src:. /home/pablo/myenv/bin/python benchmarks/powersystems_julia/plot_wecc_horizons.py",
        "```",
    ]
    results = "\n".join(lines) + "\n"
    (FIVE / "RESULTS.md").write_text(results)
    v5, j5 = data[5, "VeraGrid"], data[5, "Julia"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for ax, column, title in ((axes[0], "integration_s", "Integration"),
                              (axes[1], "total_s", "Complete run")):
        ax.bar(("VeraGrid", "Julia"),
               (v5[column].median(), j5[column].median()),
               color=(COLORS["VeraGrid"], COLORS["Julia"]))
        ax.set(ylabel="Seconds", title=title)
        ax.grid(axis="y", alpha=.2)
    fig.suptitle("WECC 240: five-second simulation, warm-run medians")
    fig.savefig(FIVE / "five_second_comparison.png", bbox_inches="tight")
    plt.close(fig)
    root_results = f"""# WECC 240: five-second RMS benchmark

## Benchmark

This benchmark simulates the WECC 240-bus power system from `t = 0` to `t = 5 s`, with a line trip at `t = 1 s`. It compares VeraGrid's vectorized power-balance BDF integrator with PowerSimulationsDynamics.jl using Sundials IDA. Both engines record the dynamic response at `0.01 s` intervals. The comparison measures complete run time and integration time, then separates the measured RHS and Jacobian work. VeraGrid's sparse factorization and linear solve are measured separately; Julia does not expose an equivalent isolated timer here.

Each engine ran ten fresh simulations on the same host. Values below are median [10th, 90th percentile] over repetitions 2–10; the first cold run is retained in the CSVs. [Methods and reproduction](results/five_second_wecc/METHODS.md).

## What “vectorized” means here

VeraGrid sets `RmsProblemTypes.PowerBalanceVectorized`. It groups like dynamic components into array-based equation blocks, compiles their residual and sparse Jacobian, and assembles them with the network power-balance equations. The non-vectorized `PowerBalance` path instead builds and evaluates component equations individually. This benchmark times **the vectorized VeraGrid path only**; it contains no measured comparison against VeraGrid's non-vectorized path. Vectorization describes the equation assembly and evaluation, not a different physical grid or a shorter simulation.

Julia uses `ResidualModel` with Sundials IDA. The Julia results are a cross-engine comparison, not a measurement of Julia “non-vectorized” mode. Both engines model the same event, but their numerical implementations differ, so speed and trajectory error should be considered together.

## Results

![Five-second comparison](results/five_second_wecc/five_second_comparison.png)

| Measure | VeraGrid | Julia |
|---|---:|---:|
| Integration | {fmt(v5, 'integration_s')} s | {fmt(j5, 'integration_s')} s |
| Complete run | {fmt(v5, 'total_s')} s | {fmt(j5, 'total_s')} s |

VeraGrid integration is **{j5.integration_s.median()/v5.integration_s.median():.2f}× faster**. Its complete run is slower because setup and simulation build take longer. VeraGrid trajectory RMSE against the committed Julia reference is **{v5.rmse.median():.3g} p.u.**

| Integration phase | VeraGrid median | Julia median |
|---|---:|---:|
| RHS evaluation | {v5.rhs_evaluation_s.median():.2f} s | {j5.rhs_evaluation_s.median():.2f} s |
| Jacobian evaluation | {v5.jacobian_evaluation_s.median():.2f} s | {j5.jacobian_evaluation_s.median():.2f} s |
| Factorization and linear solve | {v5.linear_solver_s.median():.2f} s | Not isolated |

Julia's remaining integration time includes linear solves and other solver work; it is not a separate linear-solve measurement. Raw measurements: [VeraGrid CSV](results/five_second_wecc/veragrid.csv) and [Julia CSV](results/five_second_wecc/julia.csv).

The [Numba compiled WECC follow-up](results/numba_comp_wecc/RESULTS.md) compares the fixed compiled RHS backend at 5 and 20 seconds, with a plot and phase timings. Its two warm runs per horizon are preliminary and separate from the ten-run baseline above.
"""
    (FIVE.parent.parent / "RESULTS.md").write_text(root_results)
    (FIVE / "METHODS.md").write_text("\n".join(methods) + "\n")
    print(FIVE / "RESULTS.md")
    print(FIVE.parent.parent / "RESULTS.md")
    print(FIVE / "METHODS.md")


if __name__ == "__main__":
    main()
