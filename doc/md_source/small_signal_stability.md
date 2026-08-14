# Small-Signal Stability Analysis

RMS small-signal stability analysis linearizes the RMS dynamic model around one operating point and computes the corresponding eigenvalues and modal information.

Before running the RMS small-signal assessment, a power-flow solution must exist because the RMS model is initialized from that operating point.

## RMS Workflow

The RMS small-signal driver follows two stages.

1. Build and initialize the RMS DAE model from the grid and the power-flow results.
2. Evaluate the linearization at the requested assessment time.

If `ss_assessment_time == 0.0`, the linearization is computed directly at the initialized RMS operating point.

If `ss_assessment_time > 0.0`, the driver first runs an RMS simulation from `t = 0` up to the requested assessment instant, and then linearizes the model at that dynamic state.

## Settings

This is the Small-Signal settings page:

![](figures/smallsignal_settings.png)

### Small-signal settings

- **Assessment time (s)**: Time instant where the linearization is evaluated.
- **Modes**: Number of eigenvalues to compute.

The `Modes` option selects the numerical path used by the driver.

- If `k = 0`, all available modes are computed with the dense algorithm.
- If `k >= n - 1`, where `n = number of states + number of differential variables`, the driver also falls back to the dense algorithm.
- If `0 < k < n - 1`, the sparse algorithm is used and returns only `k` modes.

### RMS settings used by the assessment

When `ss_assessment_time > 0.0`, the RMS simulation settings become part of the workflow because the system must first be simulated to the target instant.

- **Integration method**: RMS time-domain integrator used before linearization.
  - `DynamicIntegrationMethod.DaeBackEuler`
- **Time step (s)**: RMS integration step used to reach the assessment time.
- **Maximum iterations**: Nonlinear iterations allowed inside each implicit RMS step.
- **Initialization method**: RMS initialization strategy used to build the operating point before the simulation starts.
  - For example: `RmsInitializationMethod.PseudoTransient`
  - Or: `RmsInitializationMethod.Explicit`
- **Simulation time**: Must be consistent with the requested assessment time when the RMS simulation is used.
- **Verbose**: Controls the amount of printed diagnostic information.

The small-signal driver currently advances the pre-assessment RMS simulation with the RMS integration method selected in `RmsOptions` and then evaluates the Jacobians at the requested time.

## Numerical Formulation

The RMS small-signal implementation supports two related formulations.

### Standard formulation

When the RMS model has no differential-variable block in the generalized sense, the driver builds the classical reduced state matrix

$$
A = fx - fy \, gy^{-1} \, gx
$$

from the DAE Jacobians.

The eigenanalysis is then the standard problem

$$
A v = \lambda v
$$

In this case:

- the state matrix stored in the results is the reduced state matrix
- participation factors are computed from the left and right eigenvectors of `A`
- the participation-factor rows usually align with the RMS state variables

### Generalized formulation

When the RMS model includes differential variables that must be retained explicitly, the driver solves the generalized eigenvalue problem

$$
A v = \lambda E v
$$

using the matrices returned by `problem.get_static_state_matrix(x, dx)` and `problem.get_E_matrix(x, dx)`.

In this case:

- the state matrix stored in the results corresponds to the unreduced generalized linearization matrix used for the eigenanalysis
- participation factors are computed with the generalized normalization

$$
w_i^T E v_i = 1
$$
- the participation-factor rows and state-matrix axes can include both state and algebraic variables

This is why the results object also stores:

- `stat_vars_array`
- `algebraic_vars_array`

Those arrays identify how the result tables must be labelled in standard and generalized cases.

## Dense vs Sparse Calculation

The RMS driver exposes two eigensolution paths.

### Dense calculation

Dense calculation is used when all modes are requested.

- It computes the complete eigenvalue spectrum.
- It is the path used when `k = 0`.
- It is also used when `k` is large enough that sparse extraction is no longer meaningful.
- For the standard formulation it solves the full eigenproblem of the reduced matrix.
- For the generalized formulation it solves the dense generalized eigenproblem.

Dense calculation is the correct choice when:

- the full modal spectrum is required
- a complete participation-factor matrix is needed
- the model is small or medium enough that a full solve is affordable

### Sparse calculation

Sparse calculation is used when only a subset of modes is requested.

- It computes only `k` eigenvalues.
- It is used when `0 < k < n - 1`.
- It relies on sparse linear algebra and shift-and-invert style operators.
- It is the preferred path for large RMS models when only the dominant modes are needed.

Sparse calculation is the correct choice when:

- the model is large
- only a limited number of electromechanical or critical modes are required
- full-spectrum dense analysis would be unnecessarily expensive

## Results

The RMS small-signal study currently provides the following main results.

- **Modes**: Eigenvalue table with real part, imaginary part, damping ratio, and oscillation frequency.
- **Participation factors**: Normalized participation-factor matrix. Row `k`, column `i` gives the participation of variable `k` in mode `i`.
- **State matrix**: Linearized state or generalized system matrix used by the modal analysis.
- **Right eigenvectors**: Right eigenvector matrix associated with the computed modes.
- **S-domain plot**: Eigenvalue plot in the complex plane.
  - The imaginary axis can be shown in `rad/s` or `Hz`.

![](figures/SDomain_plot_VeraGrid.png)

### Result interpretation notes

- `damping_ratios` and `conjugate_frequencies` are reported for oscillatory modes.
- Non-oscillatory modes keep `NaN` entries in those vectors.
- In generalized RMS cases, result tables can include algebraic variables in addition to state variables.

<!-- BEGIN RESULTS REGISTERED PROPERTIES -->

## Registered Result Properties

### `SmallSignalStabilityRmsResults` registered properties

The RMS small-signal stability result stores modal, matrix, and labeling data for the current linearization.

| Property | Type | Description |
|----------|------|-------------|
| `stat_vars_array` | `StrVec` | Labels of the RMS state variables used to annotate result tables. |
| `algebraic_vars_array` | `StrVec` | Labels of the RMS algebraic variables used when generalized results include algebraic rows or columns. |
| `eigenvalues` | `Vec` | Eigenvalues of the linearized RMS system. |
| `participation_factors` | `Mat` | Normalized participation-factor matrix relating variables to modes. |
| `damping_ratios` | `Vec` | Damping ratio of each oscillatory mode. Non-oscillatory modes remain `NaN`. |
| `conjugate_frequencies` | `Vec` | Oscillation frequency of each oscillatory mode in hertz. Non-oscillatory modes remain `NaN`. |
| `state_matrix` | `Mat` | Linearized matrix used by the RMS modal analysis. |
| `right_eigenvectors` | `Mat` | Right eigenvector matrix associated with the computed modes. |

### `SmallSignalStabilityEmtResults` registered properties

The EMT small-signal stability result stores multiplier, eigenvalue, and participation-factor data.

| Property | Type | Description |
|----------|------|-------------|
| `multipliers` | `CxVec` | Discrete-time multipliers from the EMT small-signal analysis. |
| `eigenvalues` | `CxVec` | Eigenvalues of the linearized system. |
| `participation_factors` | `Mat` | Participation-factor matrix relating states or variables to modes. |

### `EraMatrixPencilResults` registered properties

The ERA matrix pencil result stores modal estimates and reconstruction diagnostics.

| Property | Type | Description |
|----------|------|-------------|
| `eigenvalues_s` | `CxVec` | Estimated continuous-time eigenvalues in the s-domain. |
| `frequencies_hz` | `Vec` | Mode frequencies in hertz. |
| `damping_ratios` | `Vec` | Damping ratio for each identified mode. |
| `is_stable` | `BoolVec` | Stability flag for each identified mode. |
| `residues` | `CxMat` | Modal residues estimated by the ERA matrix pencil method. |
| `modal_energy` | `Vec` | Estimated energy contribution of each mode. |
| `reconstruction_errors` | `Vec` | Signal reconstruction error for each selected model order. |
| `band_low_hz` | `Vec` | Lower frequency bound used for modal selection. |
| `band_high_hz` | `Vec` | Upper frequency bound used for modal selection. |
| `selected_orders` | `IntVec` | Model orders selected by the ERA matrix pencil analysis. |
| `observable_count_per_mode` | `IntVec` | Number of observed signals contributing to each mode. |

### `RmsResults` registered properties

The RMS result stores the simulated variable values.

| Property | Type | Description |
|----------|------|-------------|
| `values` | `Vec` | Simulated values matrix for the registered dynamic variables. |

### `EmtResults` registered properties

The EMT result stores the simulated variable values.

| Property | Type | Description |
|----------|------|-------------|
| `values` | `Vec` | Simulated values matrix for the registered dynamic variables. |
<!-- END RESULTS REGISTERED PROPERTIES -->

## API

The maintained RMS small-signal example is `trunk/dynamics/small_signal/rms_kundur_small_signal.py`. The pattern below follows the current driver usage.

```python
from pathlib import Path

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.enumerations import (
    DynamicIntegrationMethod,
    RmsInitializationMethod,
)
from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import (
    PowerFlowDriver,
    PowerFlowOptions,
)
from VeraGridEngine.Simulations.Rms.rms_options import RmsOptions
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_driver import (
    SmallSignalStabilityRmsDriver,
)
from VeraGridEngine.Simulations.SmallSignalStabilityRms.small_signal_options import (
    RmsSmallSignalStabilityOptions,
)


grid_path = Path("..") / "Grids_and_profiles" / "grids" / "IEEE39_1W.veragrid"
grid = gce.open_file(str(grid_path))

# The RMS small-signal assessment always starts from one solved power flow.
pf_options = PowerFlowOptions(solver_type=gce.SolverType.NR, verbose=False)
power_flow = PowerFlowDriver(grid=grid, options=pf_options)
power_flow.run()
pf_results = power_flow.results

# RMS options are only used when the assessment time is strictly positive,
# because the driver must simulate the RMS model up to that instant before
# building the linearization.
rms_options = RmsOptions(
    time_step=0.001,
    simulation_time=5.0,
    max_iter=1000,
    integration_method=DynamicIntegrationMethod.DaeBackEuler,
    initialization_method=RmsInitializationMethod.PseudoTransient,
    verbose=0,
)

# k = 0 requests the complete eigenvalue spectrum.
sss_options = RmsSmallSignalStabilityOptions(
    k=0,
    ss_assessment_time=0.0,
    verbose=1,
)

driver = SmallSignalStabilityRmsDriver(
    grid=grid,
    rms_options=rms_options,
    sss_options=sss_options,
    pf_results=pf_results,
)
driver.run_small_signal_stability()

results = driver.results

eigenvalues = np.asarray(results.eigenvalues, dtype=complex)
participation = np.asarray(results.participation_factors, dtype=float)
damping_ratios = np.asarray(results.damping_ratios, dtype=float)
frequencies_hz = np.asarray(results.conjugate_frequencies, dtype=float)
state_matrix = np.asarray(results.state_matrix)
right_eigenvectors = np.asarray(results.right_eigenvectors, dtype=complex)
state_labels = np.asarray(results.stat_vars_array, dtype=str)
algebraic_labels = np.asarray(results.algebraic_vars_array, dtype=str)
```

### Assessment at a nonzero time

To linearize the system at a later instant, keep the same workflow and change the assessment time.

```python
sss_options = RmsSmallSignalStabilityOptions(
    k=20,
    ss_assessment_time=5.0,
    verbose=1,
)
```

In that case, the driver first runs the RMS simulation to `t = 5.0 s` and then computes the modal analysis there.

## Benchmark

### Running ANDES

Thanks to its symbolic precision and reliable numerical performance, ANDES provides a great baseline for stability analysis in contemporary power system studies. That's why VeraGrid uses ANDES as its benchmark for small-signal analysis. Of course, VeraGrid successfully reproduces all eigenvalue placements from ANDES.

VeraGrid loads ANDES models by opening json files. Naturally, VeraGrid replicates all eigenvalue results from ANDES across standard benchmarks like the Kundur two area system with consistent accuracy and sub-second performance.

This is the code to get ANDES results:

```python
"""
To run this script andes must be installed (pip install andes)
"""
import andes
import time
import pandas as pd
import numpy as np

def stability_andes():

   ss = andes.load('Gen_Load/kundur_ieee_no_shunt.json', default_config=True)
   n_xy = len(ss.dae.xy_name)
   print(f"Andes variables = {n_xy}")
   ss.files.no_output = True

   # fix P & Q load ANDES
   ss.PQ.config.p2p = 1.0
   ss.PQ.config.p2i = 0
   ss.PQ.config.p2z = 0

   ss.PQ.config.q2q = 1.0
   ss.PQ.config.q2i = 0
   ss.PQ.config.q2z = 0

   dae = ss.dae

   # Run PF
   ss.PFlow.config.tol = 1e-8
   ss.PFlow.run()

   #Run Small-Signal Stability analysis
   eig = ss.EIG
   eig.run()

   df_Eig = pd.DataFrame(eig.mu)
   df_Eig.to_csv("Eigenvalues_results_Andes.csv", index=False, header=False)

   df_pfactors = pd.DataFrame(eig.pfactors.T)
   df_pfactors.to_csv("pfactors_results_Andes.csv", index=False, header=False, float_format="%.10f")

    return eig.mu, eig.pfactors
```

Comparing the case of Kundur two-area system VeraGrid gets exactly the same results.

![](figures/andes_vs_veragrid_kundur.png)

The following plot template is used to compare results.

```python
import matplotlib.pyplot as plt
import numpy as np

x1 = VeraGrid_Eig.real
y1 = VeraGrid_Eig.imag
x2= Andes_Eig.real
y2 = Andes_Eig.imag
slope = 1 / 0.05
x_z = np.linspace(-200, 0, 400)
y_z = slope * x_z
# Plot the two lines (positive and negative imaginary axis)
plt.plot(x_z, y_z, '--', color='grey', label='$\lambda$ = 5%')
plt.plot(x_z, -y_z, '--', color='grey')
plt.scatter(x2, y2, marker='o', color='orange', label='Andes')
plt.scatter(x1, y1, marker='x', color='blue', label='VeraGrid')
plt.xlabel("Re [s -1]")
plt.ylabel("Im [s -1]")
plt.title("Stability plot")
margin_x = (x1.max() - x1.min()) * 0.1
margin_y = (y1.max() - y1.min()) * 0.1
x_min = x1.min() - margin_x
x_max = x1.max() + margin_x
y_min = y1.min() - margin_y
y_max = y1.max() + margin_y
plt.xlim([x_min, x_max])
plt.ylim([y_min, y_max])
plt.axhline(0, color='black', linewidth=1)
plt.axvline(0, color='black', linewidth=1)
plt.legend(loc='upper left', ncol=2)
plt.tight_layout()
plt.show()
```

Where `VeraGrid_Eig` and `Andes_Eig` are numpy arrays with the eigenvalues results from the VeraGrid and Andes stability assessments respectively.
