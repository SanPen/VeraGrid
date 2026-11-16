"""Summarize the saved same-node STAMP and VeraGrid WSCC trajectories."""

from pathlib import Path
import csv

import numpy as np


root = Path(__file__).parent / "results" / "multivac_time_series"
stamp = np.loadtxt(root / "stamp_trajectory.csv", delimiter=",")
veragrid = np.loadtxt(root / "veragrid_trajectory.csv", delimiter=",", skiprows=1)
assert np.isclose(stamp[0, 0], 0) and np.isclose(veragrid[0, 0], 0)
assert np.isclose(stamp[-1, 0], 0.3) and np.isclose(veragrid[-1, 0], 0.3)
assert np.all(np.diff(stamp[:, 0]) > 0) and np.all(np.diff(veragrid[:, 0]) > 0)
assert np.isclose(stamp[0, 1], 1, atol=1e-6)
assert np.isclose(veragrid[0, 1], 1, atol=1e-6)

with (root / "stamp_timing.csv").open(newline="") as stream:
    stamp_seconds = [float(row["simulation_seconds"]) for row in csv.DictReader(stream)]
with (root / "veragrid_timing.csv").open(newline="") as stream:
    veragrid_timing = next(csv.DictReader(stream))

error = np.interp(stamp[:, 0], veragrid[:, 0], veragrid[:, 1]) - stamp[:, 1]
stamp_median = float(np.median(stamp_seconds))
veragrid_seconds = float(veragrid_timing["simulation_seconds"])
print(f"STAMP warmed simulations (s): {stamp_seconds}")
print(f"STAMP median (s): {stamp_median:.6f}")
print(f"VeraGrid simulation (s): {veragrid_seconds:.6f}")
print(f"VeraGrid setup (s): {float(veragrid_timing['setup_seconds']):.6f}")
print(f"Simulation time ratio, VeraGrid/STAMP median: {veragrid_seconds / stamp_median:.3f}")
print(f"SG1 speed RMSE (pu): {np.sqrt(np.mean(error**2)):.9g}")
print(f"SG1 speed max error (pu): {np.max(np.abs(error)):.9g}")

for tolerance in ("1e-8", "1e-6"):
    folder = root / f"tol_{tolerance}"
    if not folder.exists():
        continue
    candidate = np.loadtxt(folder / "veragrid_trajectory.csv", delimiter=",", skiprows=1)
    with (folder / "veragrid_timing.csv").open(newline="") as stream:
        timing = next(csv.DictReader(stream))
    candidate_error = np.interp(stamp[:, 0], candidate[:, 0], candidate[:, 1]) - stamp[:, 1]
    print(f"VeraGrid tolerance {tolerance}: simulation {float(timing['simulation_seconds']):.6f} s, "
          f"RMSE {np.sqrt(np.mean(candidate_error**2)):.9g} pu, "
          f"max error {np.max(np.abs(candidate_error)):.9g} pu")
