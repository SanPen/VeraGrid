# 📏 Linear analysis

Linear analysis in VeraGrid provides a fast approximation of power transfer impacts using sensitivity factors instead of
solving the full non-linear power flow every time. It is especially useful for screening studies, contingency analysis,
time-series approximations, and transfer sensitivity calculations.

The most important outputs are:

- **PTDF**: Power Transfer Distribution Factors
- **LODF**: Line Outage Distribution Factors

These factors describe how injections or outages propagate through branch flows.

## What The Study Evaluates

The linear analysis approximates the network around its base operating point and computes:

- branch flow sensitivities to bus injections
- branch flow sensitivities to line outages
- approximate branch active powers
- approximate branch loading

Compared with a full AC power flow, the linear model is much faster and is therefore well suited for:

- contingency screening
- sensitivity studies
- linear time-series flow approximation
- remedial action logic such as SRAP

It is not intended to replace the non-linear power flow in all situations. Its main value is speed and interpretability.

## PTDF And LODF

### PTDF

The **Power Transfer Distribution Factor** matrix tells how a change in injection at a bus affects the flow of each
branch.

In practice, PTDF answers questions such as:

- if I inject more power at this bus, which lines will pick up the transfer?
- which branches are most sensitive to a given transfer?
- how can I approximate branch flows over time without repeatedly running a full non-linear solver?

### LODF

The **Line Outage Distribution Factor** matrix tells how the outage of one branch redistributes flow on the remaining
branches.

In practice, LODF answers questions such as:

- what happens to branch flows if one line is disconnected?
- which outages are likely to create overloads elsewhere?
- how severe is a given N-1 branch outage from a flow redistribution perspective?

## Available Outputs

The `LinearAnalysisResults` object exposes:

- `PTDF`: Power transfer distribution factors
- `LODF`: Line (actually all branches with impedance) distribution factors.
- `HvdcDF`: HVDCLines distribution factors (sensitivity to the set power)
- `HvdcODF`: HVDCLines outage distribution factors.
- `VscDF`: VSC converters distribution factors (sensitivity to the set power)
- `VscODF`: VSC converters outage distribution factors.
- `Sf`: approximate branch active power flow
- `loading`: approximate branch loading
- `Sbus`: bus power injections

The result model also exposes tabular views through `mdl()` for:

- `ResultTypes.PTDF`
- `ResultTypes.LODF`
- `ResultTypes.HvdcPTDF`
- `ResultTypes.HvdcODF`
- `ResultTypes.VscPTDF`
- `ResultTypes.VscODF`
- `ResultTypes.BranchActivePowerFrom`
- `ResultTypes.BranchLoading`

## Main Options

![](figures/settings-pf.png)

The linear analysis options are:

- `distribute_slack`:
  whether the slack effect is distributed across buses instead of concentrated at one reference
- `correct_values`:
  whether the analysis should apply internal corrections for out-of-range values
- `ptdf_threshold`:
  PTDF sparsification threshold
- `lodf_threshold`:
  LODF sparsification threshold

For most workflows, `distribute_slack` and `correct_values` are the most relevant settings.

## Snapshot Linear Analysis

This is the standard single-state linear study.



Using the simplified API:

```python
import os
import VeraGridEngine as gce

folder = os.path.join('..', 'Grids_and_profiles', 'grids')
fname = os.path.join(folder, 'IEEE 5 Bus.xlsx')

main_circuit = gce.open_file(fname)

results = gce.linear_power_flow(grid=main_circuit)

print("Bus results:\n", results.get_bus_df())
print("Branch results:\n", results.get_branch_df())
print("PTDF:\n", results.mdl(gce.ResultTypes.PTDF).to_df())
print("LODF:\n", results.mdl(gce.ResultTypes.LODF).to_df())
```

Using the driver directly:

```python
import os
import VeraGridEngine as gce

folder = os.path.join('..', 'Grids_and_profiles', 'grids')
fname = os.path.join(folder, 'IEEE 5 Bus.xlsx')

main_circuit = gce.open_file(fname)

options_ = gce.LinearAnalysisOptions(distribute_slack=False, correct_values=True)

drv = gce.LinearAnalysisDriver(grid=main_circuit, options=options_)
drv.run()

print("Bus results:\n", drv.results.get_bus_df())
print("Branch results:\n", drv.results.get_branch_df())
print("PTDF:\n", drv.results.mdl(gce.ResultTypes.PTDF).to_df())
print("LODF:\n", drv.results.mdl(gce.ResultTypes.LODF).to_df())
```

Output:

```text
Bus results:
        Vm   Va       P    Q
Bus 0  1.0  0.0  2.1000  0.0
Bus 1  1.0  0.0 -3.0000  0.0
Bus 2  1.0  0.0  0.2349  0.0
Bus 3  1.0  0.0 -0.9999  0.0
Bus 4  1.0  0.0  4.6651  0.0

Branch results:
                  Pf   loading
Branch 0-1  2.497192  0.624298
Branch 0-3  1.867892  0.832394
Branch 0-4 -2.265084 -0.828791
Branch 1-2 -0.502808 -0.391900
Branch 2-3 -0.267908 -0.774300
Branch 3-4 -2.400016 -1.000006

PTDF:
               Bus 0     Bus 1     Bus 2  Bus 3     Bus 4
Branch 0-1  0.193917 -0.475895 -0.348989    0.0  0.159538
Branch 0-3  0.437588  0.258343  0.189451    0.0  0.360010
Branch 0-4  0.368495  0.217552  0.159538    0.0 -0.519548
Branch 1-2  0.193917  0.524105 -0.348989    0.0  0.159538
Branch 2-3  0.193917  0.524105  0.651011    0.0  0.159538
Branch 3-4 -0.368495 -0.217552 -0.159538    0.0 -0.480452

LODF:
            Branch 0-1  Branch 0-3  Branch 0-4  Branch 1-2  Branch 2-3  Branch 3-4
Branch 0-1   -1.000000    0.344795    0.307071   -1.000000   -1.000000   -0.307071
Branch 0-3    0.542857   -1.000000    0.692929    0.542857    0.542857   -0.692929
Branch 0-4    0.457143    0.655205   -1.000000    0.457143    0.457143    1.000000
Branch 1-2   -1.000000    0.344795    0.307071   -1.000000   -1.000000   -0.307071
Branch 2-3   -1.000000    0.344795    0.307071   -1.000000   -1.000000   -0.307071
Branch 3-4   -0.457143   -0.655205    1.000000   -0.457143   -0.457143   -1.000000
```

## Time-Series Linear Analysis

The time-series driver uses the same linear sensitivity idea to approximate branch flows over many time steps.

This is useful when:

- the grid topology does not change significantly
- you want a fast approximation of flow evolution over time
- you want to compare linear and non-linear flow tracking

The time-series driver is `LinearAnalysisTimeSeriesDriver`.

```python
import VeraGridEngine as gce

grid = gce.open_file("IEEE39_1W.veragrid")

drv = gce.LinearAnalysisTimeSeriesDriver(grid=grid)
drv.run()

print(drv.results.Sf)
print(drv.results.loading)
```

## Linear vs Non-Linear Comparison

One of the most common uses of the linear model is to compare it against a Newton-Raphson time-series power flow.

```python
import os
from matplotlib import pyplot as plt
import VeraGridEngine as gce

plt.style.use('fivethirtyeight')

folder = os.path.join('..', 'Grids_and_profiles', 'grids')
fname = os.path.join(folder, 'IEEE39_1W.veragrid')
main_circuit = gce.open_file(fname)

ptdf_driver = gce.LinearAnalysisTimeSeriesDriver(grid=main_circuit)
ptdf_driver.run()

pf_options_ = gce.PowerFlowOptions(solver_type=gce.SolverType.NR)
ts_driver = gce.PowerFlowTimeSeriesDriver(grid=main_circuit, options=pf_options_)
ts_driver.run()

fig = plt.figure(figsize=(30, 6))
ax1 = fig.add_subplot(131)
ax1.set_title('Newton-Raphson based flow')
ax1.plot(ts_driver.results.Sf.real)
ax1.set_ylabel('MW')
ax1.set_xlabel('Time')

ax2 = fig.add_subplot(132)
ax2.set_title('PTDF based flow')
ax2.plot(ptdf_driver.results.Sf.real)
ax2.set_ylabel('MW')
ax2.set_xlabel('Time')

ax3 = fig.add_subplot(133)
ax3.set_title('Difference')
diff = ts_driver.results.Sf.real - ptdf_driver.results.Sf.real
ax3.plot(diff)
ax3.set_ylabel('MW')
ax3.set_xlabel('Time')

fig.set_tight_layout(tight=True)

plt.show()
```

![PTDF flows comparison.png](figures/PTDF_flows_comparison.png)

This comparison is important because it shows where the linear model is accurate enough for screening and where the
full non-linear power flow is still necessary.

## SRAP: Automatic Power Reduction System

The Automatic Power Reduction System, or **SRAP**, is a linear sensitivity-based mechanism used in contingency analysis
to determine whether an overload can be dismissed by corrective generation re-dispatch.

![](figures/settings-con.png)

![](figures/SRAP.png)

The idea is simple:

- a contingency produces an overload on a monitored branch
- a set of generators has known sensitivities with respect to that overload
- available upward or downward redispatch is combined with those sensitivities
- if the overload can be removed within the allowed corrective margin, the contingency can be dismissed

Example:

Imagine that a line overloads by 5 MW after a contingency. Three plants are identified as significant for relieving
that overload:

- plant 1: generating 80 MW, with PTDF sensitivity `0.11`
- plant 2: generating 30 MW, with PTDF sensitivity `0.09`
- plant 3: generating 50 MW, with PTDF sensitivity `0.07`

Assume the SRAP limit is 90 MW of redispatch.

We build arrays ordered by sensitivity:

- `sensitivity = [0.11, 0.09, 0.07]`
- `p_available = [80, 30, 30]`

Then we compute the contribution `f = sensitivity * p_available`.

If the resulting corrective capability is larger than the overload, the contingency can be considered solvable by SRAP
and may be dismissed from the critical set.

A contingency study with SRAP activated can be run as follows:

```python
con_options = ContingencyAnalysisOptions()
con_options.use_srap = True
con_options.engine = ContingencyEngine.Linear

con_drv = ContingencyAnalysisDriver(
    grid=grid,
    options=con_options,
    engine=EngineType.VeraGrid
)

con_drv.run()
```

## Interpretation Notes

- Large PTDF absolute values indicate strong sensitivity of a branch to injections at a bus.
- Large LODF absolute values indicate strong flow redistribution after the outage of another branch.
- Linear branch loadings are very useful for screening, but not all overloads found linearly will match the exact
  non-linear AC solution.
- Time-series linear analysis is often good for ranking and trend analysis, even when exact MW values differ somewhat
  from Newton-Raphson.

## Benchmark

### Linear Algebra Frameworks Benchmark

#### IEEE 39 1-year time series

The experiment measures the time taken by the time-series simulation using different linear algebra solvers.

The power flow tolerance is set to `1e-4`.

The time in seconds taken using each solver is:

|         | KLU   | LAPACK | ILU   | SuperLU | Pardiso |
|---------|-------|--------|-------|---------|---------|
| Test 1  | 82.03 | 82.10  | 81.79 | 82.88   | 93.23   |
| Test 2  | 80.22 | 80.84  | 81.71 | 81.37   | 95.29   |
| Test 3  | 79.53 | 82.32  | 82.75 | 80.98   | 92.62   |
| Test 4  | 80.06 | 82.66  | 82.14 | 80.17   | 97.60   |
| Test 5  | 80.07 | 80.51  | 81.94 | 80.03   | 93.39   |
| Average | 80.38 | 81.68  | 82.07 | 81.09   | 94.42   |

#### 2869 Pegase 1-week time series

The experiment measures the time taken by the time-series simulation using different linear algebra solvers.

The power flow tolerance is set to `1e-4`.

The time in seconds taken using each solver is:

|         | KLU   | LAPACK | ILU   | SuperLU | Pardiso |
|---------|-------|--------|-------|---------|---------|
| Test 1  | 2.46  | 2.50   | 2.52  | 2.48    | 2.54    |
| Test 2  | 2.35  | 2.31   | 2.36  | 2.32    | 2.59    |
| Test 3  | 2.40  | 2.42   | 2.46  | 2.46    | 2.46    |
| Test 4  | 2.33  | 2.31   | 2.34  | 2.33    | 2.42    |
| Test 5  | 2.31  | 2.32   | 2.45  | 2.33    | 2.51    |
| Average | 2.37  | 2.37   | 2.43  | 2.39    | 2.51    |

From these tests, the solvers are roughly equivalent for this type of simulation, except Pardiso, which performs
worse than the others in these specific benchmarks.

<!-- BEGIN RESULTS REGISTERED PROPERTIES -->

## Registered Result Properties

### `LinearAnalysisResults` registered properties

The snapshot linear analysis result stores sensitivity matrices and the base linearized operating point.

| Property | Type | Description |
|----------|------|-------------|
| `branch_names` | `StrVec` | Names aligned with branch-indexed result arrays. |
| `bus_names` | `StrVec` | Names aligned with bus-indexed result arrays. |
| `bus_types` | `IntVec` | Bus type code used by the solved numerical model. |
| `PTDF` | `Mat` | Power transfer distribution factor matrix. |
| `LODF` | `Mat` | Line outage distribution factor matrix. |
| `HvdcDF` | `Mat` | HVDC power-transfer sensitivity matrix. |
| `HvdcODF` | `Mat` | HVDC outage distribution factor matrix. |
| `VscDF` | `Mat` | VSC power-transfer sensitivity matrix. |
| `VscODF` | `Mat` | VSC outage distribution factor matrix. |
| `Sf` | `Vec` | Complex branch power flow at the from side. |
| `Sbus` | `Vec` | Complex bus power injection. |
| `voltage` | `CxVec` | Complex bus voltage solution. |
| `loading` | `Vec` | Branch loading result. |

### `LinearAnalysisTimeSeriesResults` registered properties

The time-series linear analysis result stores linearized voltages, injections, flows, losses, and loading over time.

| Property | Type | Description |
|----------|------|-------------|
| `branch_names` | `StrVec` | Names aligned with branch-indexed result arrays. |
| `bus_names` | `StrVec` | Names aligned with bus-indexed result arrays. |
| `bus_types` | `IntVec` | Bus type code used by the solved numerical model. |
| `voltage` | `CxMat` | Complex bus voltage solution. |
| `Sf` | `CxMat` | Complex branch power flow at the from side. |
| `S` | `CxMat` | Complex bus power result matrix. |
| `losses` | `CxMat` | Complex branch losses. |
| `loading` | `CxMat` | Branch loading result. |
<!-- END RESULTS REGISTERED PROPERTIES -->
