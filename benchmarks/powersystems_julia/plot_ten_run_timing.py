"""Regenerate the ten-run timing figures and result README from measured CSVs."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import platform
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "results" / "ten_run_timing"
CASES = ("2_bus", "3_bus", "ieee9", "wecc_240")
COLORS = {"VeraGrid": "#127c92", "Julia": "#c65b37"}


def quantile_text(values: pd.Series) -> str:
    return f"{values.median():.3g} [{values.quantile(.1):.3g}, {values.quantile(.9):.3g}]"


def main() -> None:
    vg = pd.read_csv(OUT / "veragrid.csv")
    jl = pd.read_csv(OUT / "julia.csv")
    for label, data in (("VeraGrid", vg), ("Julia", jl)):
        assert len(data) == 40, f"{label}: expected 40 successful samples, got {len(data)}"
        for case in CASES:
            assert sorted(data.loc[data.case == case, "repetition"].tolist()) == list(range(1, 11))
    warm_vg = vg[vg.repetition > 1]
    warm_jl = jl[jl.repetition > 1]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 160})

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), layout="constrained")
    for ax, phase, title in ((axes[0], "total_s", "Full measured workflow"),
                             (axes[1], "integration_s", "Time integration")):
        for i, case in enumerate(CASES):
            for offset, label, data in ((-.17, "VeraGrid", warm_vg), (.17, "Julia", warm_jl)):
                values = data.loc[data.case == case, phase].to_numpy()
                ax.scatter(np.full(len(values), i + offset), values,
                           color=COLORS[label], alpha=.4, s=13)
                ax.plot(i + offset, np.median(values), marker="_", markersize=17,
                        markeredgewidth=3, color=COLORS[label])
        ax.set_yscale("log")
        ax.set_xticks(range(len(CASES)), CASES)
        ax.set_ylabel("Seconds (log scale)")
        ax.set_title(title)
        ax.grid(axis="y", alpha=.2)
    for label in COLORS:
        axes[0].scatter([], [], color=COLORS[label], label=label)
    axes[0].legend(frameon=False)
    fig.suptitle("RMS benchmark: repetitions 2–10 (dots), median (bar)", fontsize=13)
    fig.savefig(OUT / "case_timing.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.5), layout="constrained")
    for label, data in (("VeraGrid", vg), ("Julia", jl)):
        frame = data[data.case == "wecc_240"].sort_values("repetition")
        ax.plot(frame.repetition, frame.total_s, marker="o", label=label,
                color=COLORS[label], linewidth=2)
    ax.set(xlabel="Repetition", ylabel="Full workflow (s)",
           title="WECC 240: cold run and nine subsequent runs")
    ax.set_xticks(range(1, 11))
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.savefig(OUT / "wecc_repetitions.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.7), layout="constrained")
    v = warm_vg[warm_vg.case == "wecc_240"]
    j = warm_jl[warm_jl.case == "wecc_240"]
    phase_parts = (
        ("RHS", "rhs_evaluation_s", "rhs_evaluation_s", "#27839a"),
        ("Jacobian", "jacobian_evaluation_s", "jacobian_evaluation_s", "#e49c46"),
        ("VeraGrid linear solve", "linear_solver_s", None, "#665b98"),
        ("VeraGrid other", "other_integration_s", None, "#b6bec6"),
        ("Julia unattributed*", None, "unattributed_integration_s", "#73857d"),
    )
    bottoms = [0.0, 0.0]
    for label, vg_col, jl_col, color in phase_parts:
        heights = [v[vg_col].median() if vg_col else 0.0,
                   j[jl_col].median() if jl_col else 0.0]
        ax.bar(("VeraGrid", "Julia / IDA"), heights, bottom=bottoms,
               color=color, label=label)
        bottoms = [a + b for a, b in zip(bottoms, heights)]
    ax.set_ylabel("Median seconds, repetitions 2–10")
    ax.set_title("WECC 240 integration work")
    ax.legend(frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.text(.5, -.02, "*Julia linear solve is included in unattributed time; it is not isolated.",
             ha="center", fontsize=9)
    fig.savefig(OUT / "wecc_integration_phases.png", bbox_inches="tight")
    plt.close(fig)

    palette = ("#27839a", "#e49c46", "#665b98", "#b6bec6")
    fig, ax = plt.subplots(figsize=(10, 4.2), layout="constrained")
    phases = (("rhs_compile_s", "RHS compilation"),
              ("jacobian_compile_s", "Jacobian compilation"),
              ("other_problem_build_s", "Other problem build"))
    bottoms = np.zeros(len(CASES))
    for idx, (column, label) in enumerate(phases):
        heights = np.array([warm_vg[warm_vg.case == case][column].median() for case in CASES])
        ax.bar(CASES, heights, bottom=bottoms, color=palette[idx], label=label)
        bottoms += heights
    ax.set(ylabel="Median seconds, repetitions 2–10", title="VeraGrid problem build components")
    ax.legend(frameon=False)
    fig.savefig(OUT / "veragrid_compilation.png", bbox_inches="tight")
    plt.close(fig)

    rows = []
    for case in CASES:
        v = warm_vg[warm_vg.case == case]
        j = warm_jl[warm_jl.case == case]
        rows.append(f"| {case} | {quantile_text(v.total_s)} | {quantile_text(j.total_s)} | "
                    f"{v.total_s.median()/j.total_s.median():.2f}× | "
                    f"{quantile_text(v.integration_s)} | {quantile_text(j.integration_s)} | "
                    f"{v.integration_s.median()/j.integration_s.median():.2f}× | "
                    f"{v.rmse.median():.3g} |")
    v = warm_vg[warm_vg.case == "wecc_240"]
    j = warm_jl[warm_jl.case == "wecc_240"]
    phase_rows = []
    for label, vc, jc in (
        ("Model/grid setup", "setup_s", "setup_s"),
        ("Simulation/problem build", "problem_build_s", "simulation_build_s"),
        ("RHS compilation", "rhs_compile_s", None),
        ("Jacobian compilation", "jacobian_compile_s", None),
        ("Integration", "integration_s", "integration_s"),
        ("RHS evaluation", "rhs_evaluation_s", "rhs_evaluation_s"),
        ("Jacobian evaluation", "jacobian_evaluation_s", "jacobian_evaluation_s"),
        ("Linear solve", "linear_solver_s", None),
    ):
        phase_rows.append(f"| {label} | {quantile_text(v[vc])} | "
                          f"{quantile_text(j[jc]) if jc else 'Not isolated'} |")
    cpu = platform.processor() or platform.machine()
    sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    report = f'''# PowerSimulationsDynamics.jl versus VeraGrid: ten-run RMS timing

Measured {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')} on `{cpu}`; VeraGrid commit `{sha}`. Each engine ran ten fresh event simulations per case, sequentially on this host. The first repetition includes cold compilation and appears in the raw CSV and WECC plot; the tables summarize repetitions 2–10. Values are median [10th, 90th percentile] seconds. Ratios are VeraGrid / Julia; values above 1 mean VeraGrid took longer.

![Case timing](case_timing.png)

| Case | VeraGrid total (s) | Julia total (s) | Ratio | VeraGrid integration (s) | Julia integration (s) | Ratio | VeraGrid RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

## WECC 240

![WECC repetitions](wecc_repetitions.png)

![WECC integration phases](wecc_integration_phases.png)

| Phase | VeraGrid (s) | Julia (s) |
|---|---:|---:|
{chr(10).join(phase_rows)}

![VeraGrid compilation](veragrid_compilation.png)

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
'''
    results, detail = report.split("The VeraGrid **RHS/Jacobian compilation**", 1)
    results += "At WECC 240, VeraGrid integration is slightly faster at twenty seconds, while its complete run takes longer because simulation build is slower. The [five-second WECC baseline](../five_second_wecc/RESULTS.md) shows a larger integration advantage and examines how it narrows with horizon. A [Numba compiled WECC follow-up](../numba_comp_wecc/RESULTS.md) reports preliminary 5- and 20-second runs after fixing the compiled backend's event-boundary handling.\n\nDetailed timing definitions and reproduction commands are in [methods](METHODS.md).\n"
    methods = "# Ten-run RMS timing methods\n\n[Results and plots](RESULTS.md).\n\n## Setup and timing\n\n"
    methods += "The VeraGrid **RHS/Jacobian compilation**" + detail
    (OUT / "RESULTS.md").write_text(results)
    (OUT / "METHODS.md").write_text(methods)
    print(OUT / "RESULTS.md")
    print(OUT / "METHODS.md")


if __name__ == "__main__":
    main()
