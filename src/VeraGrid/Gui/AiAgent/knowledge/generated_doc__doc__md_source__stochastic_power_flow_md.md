# Official VeraGrid Doc: Stochastic Power Flow

- Original source path: `doc/md_source/stochastic_power_flow.md`
- Knowledge kind: official documentation

## Document Content

# 🎲 Stochastic power flow


Precision
Monte carlo standard deviation to achieve.
The number represents the exponent of the precision.
i.e. 3 corresponds to 1e-3

Max. Iterations
Maximum iterations for Monte Carlo sampling
if the simulation does not achieve the selected standard deviation.

Samples
Number of samples for the latin hypercube sampling.

Additional islands until stop
When simulating the blackout cascading, this is the number of islands
that determine the stop of a simulation

## API

```python
import VeraGridEngine as vg

# import some grid with time series
grid = vg.open_file("IEEE39_1W.veragrid")

# Define the power flow options to use
pf_options = vg.PowerFlowOptions()

# declare the driver
drv = vg.StochasticPowerFlowDriver(
    grid=grid,
    options=pf_options,
    sampling_points=1000,
    simulation_type=vg.StochasticPowerFlowType.LatinHypercube)
drv.run()
```
