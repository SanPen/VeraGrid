# 🎲 Stochastic power flow

The stochastic power flow in VeraGrid evaluates the network under many sampled operating points instead of solving only
one deterministic case. Its purpose is to estimate how uncertainty in injections propagates to voltages, branch flows,
loading, and losses.

Rather than asking "what happens for one dispatch and one load level?", this study asks "what is the distribution of
results over many plausible operating points?".

## What The Study Evaluates

For each sampled operating point, VeraGrid runs a power flow and stores the resulting:

- bus injections
- bus voltages
- branch powers
- branch loadings
- branch losses

After all samples are processed, the study compiles aggregate statistics and distribution views, such as:

- average voltage
- voltage standard deviation
- voltage CDF
- branch loading average
- branch loading standard deviation
- branch loading CDF
- branch losses average and CDF

This makes the study useful for uncertainty analysis, risk screening, and probabilistic operating assessment.

## Where The Uncertainty Comes From

The stochastic input builder uses the grid time-series information:

- fixed injections are sampled from empirical cumulative distributions built from the time-series profiles
- dispatchable injections are reconstructed from the sampled fixed injections through a regression model
- the dispatchable part is then scaled so that sampled demand and generation remain balanced

In practice, this means the stochastic study is not generating arbitrary random injections. It is generating injections
consistent with the historical or profile-based operating patterns already present in the grid model.

## Sampling Modes

VeraGrid currently supports two sampling modes:

- **Monte Carlo**:
  random sampling from the empirical distributions
- **Latin Hypercube**:
  stratified sampling designed to cover the input space more evenly with fewer samples

The corresponding API enum is `StochasticPowerFlowType`:

- `StochasticPowerFlowType.MonteCarlo`
- `StochasticPowerFlowType.LatinHypercube`

![](figures/settings-ml.png)

In general:

- use **Monte Carlo** when you want a straightforward random simulation
- use **Latin Hypercube** when you want better coverage of the sampled uncertainty space for a fixed sample budget

## Main Parameters

- **`mc_tol`**:
  convergence target for the Monte Carlo error indicator
- **`batch_size`**:
  batch size parameter for the simulation workflow
- **`sampling_points`**:
  maximum number of sampled operating points
- **`simulation_type`**:
  sampling method, either Monte Carlo or Latin Hypercube
- **`options`**:
  the deterministic power flow options used for each sampled operating point

The study stores all sampled points and then compiles summary statistics from them.

## Reported Results

The `StochasticPowerFlowResults` object stores the sampled raw data as well as compiled aggregate outputs.

### Raw Sampled Arrays

- `S_points`: sampled bus power injections
- `V_points`: sampled bus voltages
- `Sbr_points`: sampled branch powers
- `loading_points`: sampled branch loadings
- `losses_points`: sampled branch losses

### Compiled Aggregate Arrays

- `voltage`: average bus voltage magnitude
- `sbranch`: average branch active power
- `loading`: average branch loading
- `losses`: average branch losses

### Convergence Series

The result object also stores the evolution of averages and variances as the number of samples increases:

- `v_avg_conv`, `v_std_conv`
- `s_avg_conv`, `s_std_conv`
- `l_avg_conv`, `l_std_conv`
- `loss_avg_conv`, `loss_std_conv`

These are useful to assess whether the stochastic estimates are stabilizing as more samples are added.

## Distribution Views

The stochastic result model exposes several result tables through `mdl()`:

- `ResultTypes.BusVoltageAverage`
- `ResultTypes.BusVoltageStd`
- `ResultTypes.BusVoltageCDF`
- `ResultTypes.BusPowerCDF`
- `ResultTypes.BranchPowerAverage`
- `ResultTypes.BranchPowerStd`
- `ResultTypes.BranchPowerCDF`
- `ResultTypes.BranchLoadingAverage`
- `ResultTypes.BranchLoadingStd`
- `ResultTypes.BranchLoadingCDF`
- `ResultTypes.BranchLossesAverage`
- `ResultTypes.BranchLossesStd`
- `ResultTypes.BranchLossesCDF`

The CDF results are especially useful when the question is probabilistic, for example:

- what is the probability that a branch exceeds 100% loading?
- how likely is a bus voltage to fall below a threshold?
- how dispersed are branch losses under uncertain operating conditions?

## Additional Helper Methods

The results object includes a few practical helper methods:

- `get_index_loading_cdf(max_val=1.0)`:
  finds branches whose loading distribution exceeds a threshold and returns their indices and associated probabilities
- `query_voltage(power_array)`:
  estimates voltages for a new injection vector using a regression model trained on the sampled points

The first helper is particularly relevant for risk screening and is also reused by the cascading simulation.

## Interpretation Notes

- A low average branch loading does not necessarily mean low risk if the loading CDF has a long upper tail.
- A small voltage standard deviation means the bus voltage is robust to the sampled uncertainty.
- A broad CDF spread usually indicates that the corresponding variable is highly sensitive to uncertain injections.
- The quality of the stochastic study depends strongly on the quality and representativeness of the time-series data.

As with any probabilistic study, the outputs are only as meaningful as the input distributions.

## API

Using the driver directly:

```python
import VeraGridEngine as vg
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_driver import (
    StochasticPowerFlowDriver,
    StochasticPowerFlowType,
)

grid = vg.open_file("my_grid.veragrid")

drv = StochasticPowerFlowDriver(
    grid=grid,
    options=PowerFlowOptions(),
    sampling_points=1000,
    simulation_type=StochasticPowerFlowType.LatinHypercube,
)
drv.run()

results = drv.results

print("Average bus voltage magnitudes:", results.voltage)
print("Average branch loading:", results.loading)
print("Average branch losses:", results.losses)
```

Using plain Monte Carlo sampling:

```python
import VeraGridEngine as vg
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Stochastic.stochastic_power_flow_driver import (
    StochasticPowerFlowDriver,
    StochasticPowerFlowType,
)

grid = vg.open_file("my_grid.veragrid")

drv = StochasticPowerFlowDriver(
    grid=grid,
    options=PowerFlowOptions(),
    mc_tol=1e-3,
    sampling_points=5000,
    simulation_type=StochasticPowerFlowType.MonteCarlo,
)
drv.run()

print("Computed samples:", drv.results.points_number)
print("Error series length:", len(drv.results.error_series))
```

Getting a result table:

```python
from VeraGridEngine.enumerations import ResultTypes

table = results.mdl(ResultTypes.BranchLoadingCDF)
print(table.data)
```

Finding overloaded branches probabilistically:

```python
idx, val, prob, loading = results.get_index_loading_cdf(max_val=1.0)

print("Candidate branch indices:", idx)
print("Overload probabilities:", prob)
```

The main constructor arguments are:

- `grid`: the `MultiCircuit` network model
- `options`: power flow options
- `mc_tol`: Monte Carlo convergence tolerance
- `batch_size`: batch size parameter
- `sampling_points`: maximum number of samples
- `simulation_type`: `StochasticPowerFlowType.MonteCarlo` or `StochasticPowerFlowType.LatinHypercube`

## Practical Guidance

- Use **Latin Hypercube** when you want a compact but well-spread exploration of uncertainty.
- Use a larger `sampling_points` value when estimating tail probabilities or overload risk.
- Check the CDF outputs, not only the averages, when the study is meant for risk assessment.
- Make sure the grid contains representative time-series data, otherwise the sampled operating points will not be
  meaningful.
- Use the deterministic power flow first if you need to debug convergence issues before launching the stochastic study.
