"""Plot the preliminary WECC Numba compiled backend comparison from saved CSVs."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RESULTS = Path(__file__).resolve().parent / "results"
OUT = RESULTS / "numba_comp_wecc"
COLORS = {"Vectorized": "#127c92", "Numba compiled": "#7354a3", "Julia": "#c65b37"}


def warm(path: Path, expected: int) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame.case == "wecc_240"]
    assert sorted(frame.repetition.tolist()) == list(range(1, expected + 1)), path
    assert frame.select_dtypes("number").notna().all().all(), path
    return frame[frame.repetition > 1]


def main() -> None:
    data = {
        (5, "Vectorized"): warm(RESULTS / "five_second_wecc" / "veragrid.csv", 10),
        (5, "Numba compiled"): warm(OUT / "five_second.csv", 3),
        (5, "Julia"): warm(RESULTS / "five_second_wecc" / "julia.csv", 10),
        (20, "Vectorized"): warm(RESULTS / "ten_run_timing" / "veragrid.csv", 10),
        (20, "Numba compiled"): warm(OUT / "twenty_second.csv", 3),
        (20, "Julia"): warm(RESULTS / "ten_run_timing" / "julia.csv", 10),
    }
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 160})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5), layout="constrained")
    for ax, column, title in ((axes[0], "integration_s", "Integration"),
                              (axes[1], "total_s", "Setup + integration")):
        for horizon, center in ((5, 0), (20, 1)):
            for offset, engine in ((-.25, "Vectorized"), (0, "Numba compiled"),
                                   (.25, "Julia")):
                values = data[horizon, engine][column]
                x = center + offset
                ax.bar(x, values.median(), width=.22, color=COLORS[engine],
                       label=engine if horizon == 5 else None)
                ax.scatter(np.full(len(values), x), values, color="black", s=9, alpha=.5)
        ax.set(xticks=(0, 1), xticklabels=("5 s horizon", "20 s horizon"),
               ylabel="Wall seconds", title=title)
        ax.grid(axis="y", alpha=.2)
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("WECC 240: warm-run medians (bars) and individual runs (dots)")
    fig.savefig(OUT / "backend_comparison.png", bbox_inches="tight")
    plt.close(fig)

    def median(horizon: int, engine: str, column: str) -> float:
        return float(data[horizon, engine][column].median())

    lines = [
        "# WECC 240: Numba compiled RHS comparison",
        "",
        "The full-vectorized Numba compiled backend was tested on the same line-trip case as the [five-second baseline](../five_second_wecc/RESULTS.md) and [twenty-second report](../ten_run_timing/RESULTS.md). The original VeraGrid and Julia baselines have nine warm runs each; the new Numba backend has **two warm runs** after one cold run at each horizon. These are preliminary timings, not a ten-run replacement for the baselines. [Methods and reproduction](METHODS.md).",
        "",
        "![Integration and complete-run comparison](backend_comparison.png)",
        "",
        "| Horizon | Engine | Integration | RHS | Factorization + solve | Problem build | Complete run |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for horizon in (5, 20):
        for engine in ("Vectorized", "Numba compiled", "Julia"):
            linear = (f"{median(horizon, engine, 'linear_solver_s'):.2f} s"
                      if engine != "Julia" else "Not isolated")
            build_col = "problem_build_s" if engine != "Julia" else "simulation_build_s"
            lines.append(
                f"| {horizon} s | {engine} | {median(horizon, engine, 'integration_s'):.2f} s | "
                f"{median(horizon, engine, 'rhs_evaluation_s'):.2f} s | {linear} | "
                f"{median(horizon, engine, build_col):.2f} s | "
                f"{median(horizon, engine, 'total_s'):.2f} s |"
            )
    lines.extend([
        "",
        f"At 20 seconds, the Numba compiled RHS takes **{median(20, 'Numba compiled', 'rhs_evaluation_s'):.2f} s** versus **{median(20, 'Vectorized', 'rhs_evaluation_s'):.2f} s** for the original vectorized path. Its largest measured integration phase is sparse factorization and solve: **{median(20, 'Numba compiled', 'linear_solver_s'):.2f} s**, about **{100*median(20, 'Numba compiled', 'linear_solver_s')/median(20, 'Numba compiled', 'integration_s'):.0f}%** of integration. Problem build is the largest complete-run phase at **{median(20, 'Numba compiled', 'problem_build_s'):.2f} s**. Total time improves versus the original VeraGrid path at 20 seconds, but the longer build makes the 5-second complete run slower. Julia remains faster on complete-run time at both horizons.",
        "",
        f"The Numba backend and original vectorized path both accepted **525** steps at 5 seconds and **2,025** at 20 seconds, with no rejected steps. Their measured trajectory RMSE against the committed Julia reference agrees at **{median(5, 'Numba compiled', 'rmse'):.3g} p.u.** and **{median(20, 'Numba compiled', 'rmse'):.3g} p.u.** respectively.",
        "",
        "Raw Numba measurements: [`five_second.csv`](five_second.csv) and [`twenty_second.csv`](twenty_second.csv). The original VeraGrid and Julia CSVs are linked from the baseline reports.",
    ])
    (OUT / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(OUT / "RESULTS.md")


if __name__ == "__main__":
    main()
