# 🚧 Reliability

The reliability study in VeraGrid estimates how often the system enters degraded states and what the operational
consequences are when devices fail and recover over time. It is a Monte Carlo study driven by the reliability
parameters of the network elements, mainly their `mttf` and `mttr`.

At a high level, the study repeatedly samples device availability trajectories over the selected time horizon, applies
those outages to the network, and accumulates reliability indicators from the resulting states.

## What The Study Evaluates

VeraGrid currently exposes two reliability modes:

- **Generation adequacy**:
  evaluates whether the available generation and storage can cover the demand profile over time.
- **Grid metrics**:
  evaluates the impact of outages on the actual network, including islanding, energy not supplied, interruption counts,
  and customer-based continuity indices.

Both modes use repeated stochastic simulations. The reported results are the evolution of the Monte Carlo estimate as
the number of simulated samples increases.

## Reliability Inputs

The quality of the results depends on the network data:

- **Generators, batteries, and branches** use their reliability parameters, especially `mttf` and `mttr`.
- **Loads** should define `n_customers` if customer-based indices such as SAIDI, SAIFI, and CAIDI are required.
- **Time series** define the study horizon. If the input time series covers one year, the indices can be interpreted as
  yearly values. Otherwise, they represent the selected study period.

For customer-based indices, VeraGrid sums the number of customers per bus from the connected loads and uses those bus
totals when an outage isolates or interrupts part of the network.

## Reported Metrics

### Adequacy-Oriented Metrics

- **LOLE**: Loss of Load Expectation.
  In this study it quantifies how much time the system is unable to fully supply demand.

### Grid Reliability Metrics

- **ENS**: Energy Not Supplied.
  Total demand not served during interruption states.
- **LOLE**: Loss of Load Expectation.
  Number of hours in which demand cannot be fully supplied.
- **LOLF**: Loss of Load Frequency.
  Number of interruption events in which demand cannot be fully supplied.
- **LOLET**:
  Total number of hours with failures, whether or not those failures end up causing unmet demand.
- **LOLFT**:
  Total number of failure events, whether or not those failures end up causing unmet demand.

### Customer Continuity Metrics

- **SAIDI**: System Average Interruption Duration Index.
  Total customer interruption hours divided by the total number of customers.
- **SAIFI**: System Average Interruption Frequency Index.
  Total customer interruptions divided by the total number of customers.
- **CAIDI**: Customer Average Interruption Duration Index.
  Total customer interruption hours divided by the total number of customer interruptions.

In VeraGrid, these customer-based indices are computed from interrupted buses using the total number of customers
connected to each bus through its loads.

## Interpretation Notes

- A high **ENS** means the interruptions are severe in energy terms.
- A high **LOLF** with a moderate **LOLE** usually means many short interruptions.
- A high **SAIDI** means the average customer spends more time interrupted.
- A high **SAIFI** means the average customer experiences more interruptions.
- A high **CAIDI** means each interruption tends to last longer once it occurs.

The indices should always be interpreted together. For example, two systems can have similar ENS but very different
customer impact if one concentrates the interruption on a few buses and the other spreads it across many customers.

<!-- BEGIN RESULTS REGISTERED PROPERTIES -->

## Registered Result Properties

### `ReliabilityResults` registered properties

The reliability result stores the evolution of reliability indices during the reliability study.

| Property | Type | Description |
|----------|------|-------------|
| `LOLE_evolution` | `Vec` | Loss of load expectation evolution. |
| `ENS_evolution` | `Vec` | Energy not supplied evolution. |
| `LOLF_evolution` | `Vec` | Loss of load frequency evolution. |
| `LOLET_evolution` | `Vec` | Loss of load expectation duration evolution. |
| `LOLFT_evolution` | `Vec` | Loss of load frequency duration evolution. |
| `SAIDI_evolution` | `Vec` | System average interruption duration index evolution. |
| `SAIFI_evolution` | `Vec` | System average interruption frequency index evolution. |
| `CAIDI_evolution` | `Vec` | Customer average interruption duration index evolution. |
<!-- END RESULTS REGISTERED PROPERTIES -->

## API

Using the driver directly:

```python
import VeraGridEngine as vg

grid = vg.open_file("my_grid.veragrid")

pf_options = vg.PowerFlowOptions()

drv = vg.ReliabilityStudyDriver(
    grid=grid,
    pf_options=pf_options,
    reliability_mode=vg.ReliabilityMode.GridMetrics,
    n_sim=1000,
)
drv.run()

results = drv.results

print("LOLE:", results.LOLE_evolution[-1])
print("ENS:", results.ENS_evolution[-1])
print("LOLF:", results.LOLF_evolution[-1])
print("LOLET:", results.LOLET_evolution[-1])
print("LOLFT:", results.LOLFT_evolution[-1])
print("SAIDI:", results.SAIDI_evolution[-1])
print("SAIFI:", results.SAIFI_evolution[-1])
print("CAIDI:", results.CAIDI_evolution[-1])
```

The main constructor arguments are:

- `grid`: the `MultiCircuit` network model
- `pf_options`: power flow options object
- `reliability_mode`: `ReliabilityMode.GenerationAdequacy` or `ReliabilityMode.GridMetrics`
- `n_sim`: number of Monte Carlo samples

Using the adequacy mode:

```python
import VeraGridEngine as vg
from matplotlib import pyplot as plt

grid = vg.open_file("my_grid.veragrid")

drv = vg.ReliabilityStudyDriver(
    grid=grid,
    pf_options=vg.PowerFlowOptions(),
    reliability_mode=vg.ReliabilityMode.GenerationAdequacy,
    n_sim=1000,
)
drv.run()

results = drv.results
print("LOLE evolution:", results.LOLE_evolution)

# Getting tabular outputs from the result object:

table = results.mdl(vg.ResultTypes.ReliabilitySAIDIResults)
print(table.get_data_frame())

table.plot()
plt.show()
```

Available result types include:

- `ResultTypes.ReliabilityLOLEResults`
- `ResultTypes.ReliabilityENSResults`
- `ResultTypes.ReliabilityLOLFResults`
- `ResultTypes.ReliabilityLOLETResults`
- `ResultTypes.ReliabilityLOLFTResults`
- `ResultTypes.ReliabilitySAIDIResults`
- `ResultTypes.ReliabilitySAIFIResults`
- `ResultTypes.ReliabilityCAIDIResults`

## Practical Guidance

- Use a larger `n_sim` when comparing alternatives or when the indices are noisy.
- Make sure `mttf`, `mttr`, and `n_customers` are populated with realistic values before trusting the results.
- If SAIDI, SAIFI, or CAIDI are important, verify that the customer allocation across loads is correct.
- If the time series does not represent a full year, interpret the metrics as applying to the simulated period, not
  automatically as annual values.
