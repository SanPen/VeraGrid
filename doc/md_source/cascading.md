# 🎢 Cascading

The cascading study in VeraGrid simulates progressive branch outages after an initial disturbance. Its purpose is to
study how an overloaded network can deteriorate step by step, potentially splitting into islands and causing a broader
blackout than the original triggering event.

At each cascade step, VeraGrid runs a network simulation, identifies the branches to remove, updates the topology, and
repeats the process until the stopping criterion is reached.

## What The Study Evaluates

A cascading simulation is not a long-term reliability Monte Carlo study. It is a sequential contingency propagation
study:

- an initial outage or set of outages is applied, or the cascade starts from the current network state
- the network is solved
- overloaded branches are selected for removal
- the topology is updated and the network is solved again
- the process continues until the system has split enough or the step limit is reached

This is useful when you want to understand whether a local disturbance stays local or propagates through the network.

## How The Cascade Advances

The current implementation removes **branches** during the cascade.

Two main execution styles are available:

- **PowerFlow**:
  the cascade is driven by a standard power flow result at each step
- **LatinHypercube**:
  the cascade is driven by stochastic loading information from the Latin Hypercube stochastic power flow

The driver supports two related execution patterns:

- **Full cascade run** with `run()`:
  repeatedly solves and removes branches until the stopping criterion is met
- **Step-by-step cascade** with `perform_step_run()`:
  executes a single cascade step, useful for interactive workflows

## Branch Removal Logic

The branch removal policy depends on the path used by the driver:

### Step-By-Step Mode

When `perform_step_run()` is used:

- on the first step, the explicitly provided `triggering_idx` is removed if given
- otherwise, branches with loading above `1.0` are removed
- if no branch exceeds `1.0`, the most loaded branch is removed

### Full Cascade Mode

When `run()` is used:

- if the selected cascade mode provides overload probabilities, branches with overload probability above the configured
  threshold are removed
- if no branch passes that threshold, the algorithm falls back to removing one branch based on the most critical
  loading condition

This means the study is designed to force cascade progression even when the system is close to criticality but no
branch crosses the main probabilistic criterion.

## Stopping Criterion

The full cascade run stops when the network has split into enough islands or the step counter reaches the internal
limit derived from:

- the initial number of islands
- `max_additional_islands`
- the number of buses, used as a safety bound

In practice, `max_additional_islands` controls how much topological fragmentation is allowed before the cascade is
considered complete.

## Result Object

The cascading study returns a `CascadingResults` object. It stores one event per cascade step.

Each event contains:

- the indices of the removed branches
- the simulation results used at that step
- the removal criterion that was applied

The result object provides a few practical helpers:

- `results.events`:
  raw list of cascade events
- `results.get_failed_idx()`:
  flat array with the indices of all removed branches
- `results.get_table()`:
  summary table with the cascade step, number of failed elements, and criterion used

## Interpretation Notes

- A short cascade with only one or two steps usually means the initial disturbance remains contained.
- A long cascade with many removals indicates strong topological or loading sensitivity.
- If the cascade rapidly creates islands, the system is structurally vulnerable to fragmentation.
- If most removals happen because of fallback criteria rather than strong overload probability, the case is near
  critical but not necessarily dominated by one obvious branch overload.

The outputs should be interpreted together with the underlying power flow or stochastic power flow results at each step.

## API

Using the driver directly:

```python
import VeraGridEngine as vg
from VeraGridEngine.enumerations import CascadeType
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Reliability.blackout_driver import CascadingDriver

grid = vg.open_file("my_grid.veragrid")

drv = CascadingDriver(
    grid=grid,
    options=PowerFlowOptions(),
    triggering_idx=[0],
    max_additional_islands=1,
    cascade_type_=CascadeType.PowerFlow,
)
drv.run()

results = drv.results

print(results.get_table())
print("Failed branch indices:", results.get_failed_idx())
print("Number of cascade steps:", len(results.events))
```

Using the Latin Hypercube mode:

```python
import VeraGridEngine as vg
from VeraGridEngine.enumerations import CascadeType
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Reliability.blackout_driver import CascadingDriver

grid = vg.open_file("my_grid.veragrid")

drv = CascadingDriver(
    grid=grid,
    options=PowerFlowOptions(),
    cascade_type_=CascadeType.LatinHypercube,
    n_lhs_samples_=1000,
)
drv.run()

print(drv.results.get_table())
```

Running the cascade step by step:

```python
import VeraGridEngine as vg
from VeraGridEngine.enumerations import CascadeType
from VeraGridEngine.Simulations.PowerFlow.power_flow_options import PowerFlowOptions
from VeraGridEngine.Simulations.Reliability.blackout_driver import CascadingDriver

grid = vg.open_file("my_grid.veragrid")

drv = CascadingDriver(
    grid=grid,
    options=PowerFlowOptions(),
    triggering_idx=[0, 1],
    cascade_type_=CascadeType.PowerFlow,
)

drv.perform_step_run()
print(drv.results.get_table())

drv.perform_step_run()
print(drv.results.get_table())
```

The main constructor arguments are:

- `grid`: the `MultiCircuit` network model
- `options`: power flow options
- `triggering_idx`: optional list of branch indices to remove on the first step
- `max_additional_islands`: maximum additional islands tolerated before stopping
- `cascade_type_`: `CascadeType.PowerFlow` or `CascadeType.LatinHypercube`
- `n_lhs_samples_`: number of Latin Hypercube samples when using the stochastic mode

## Practical Guidance

- Start with a deterministic `CascadeType.PowerFlow` study when debugging a specific disturbance.
- Use `triggering_idx` when you already know the initiating branch outage you want to study.
- Use the Latin Hypercube mode when you want a cascade driven by stochastic loading conditions rather than a single
  operating point.
- Check the per-step power flow results inside `results.events` if you need to understand why a particular branch was
  selected for removal.
- Keep in mind that the current implementation removes branches only; this is a cascading branch outage study, not a
  full protection-and-restoration simulation.
