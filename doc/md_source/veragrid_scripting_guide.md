# 📑 VeraGrid scripting guide

The Scripting tab is an embedded Python environment connected to the open
VeraGrid GUI. Use it to inspect the current model, edit the live grid, run
blocking engine studies, plot results, and export data without leaving the
project.

The panel has two parts:

- the editor, where named scripts can be written and saved;
- the console, where individual commands can be executed interactively.

Saved scripts are stored in the VeraGrid user folder under `scripts`.

```python
scripts_folder = user_folder() + "/scripts"
print(scripts_folder)
```

## Console objects

The console is initialized with these objects:

| Name | Meaning |
|------|---------|
| `app` | Active VeraGrid GUI object. |
| `circuit` | The same object as `app.circuit`. |
| `vg` | Imported `VeraGridEngine` package. |
| `np` | Imported NumPy package. |
| `pd` | Imported pandas package. |
| `plt` | Imported Matplotlib pyplot package. |
| `hlp` | Function that prints the console quick reference. |
| `clc` | Function that clears the console. |
| `user_folder` | Function returning the VeraGrid user folder. |

```python
hlp()
grid = app.circuit
session = app.session
```

`app.circuit` is the live `MultiCircuit` object. Changes made through this
object modify the open grid in memory. Save the project afterwards when the
changes should persist.

## How to run studies

For scripts, use the blocking helpers exposed by `src/VeraGridEngine/api.py`.
They return the result object directly and are the preferred way to run a study
from the scripting panel.

```python
options = vg.PowerFlowOptions(vg.SolverType.NR, verbose=False)
results = vg.power_flow(app.circuit, options=options)

print(results.converged, results.error)
print(results.get_bus_df())
```

Do not use GUI launch methods as the normal scripting interface. They are
asynchronous button workflows, so the next console line can run before the
study result exists. Use them only when you intentionally want to trigger the
GUI workflow and read `app.session` later.

### API helpers

| Helper | Use |
|--------|-----|
| `vg.open_file(path)` | Open any supported grid file. |
| `vg.save_file(grid, path)` | Save a grid file. |
| `vg.open_multiverse(path)` | Open a VeraGrid multiverse file. |
| `vg.save_multiverse(mv, path)` | Save a multiverse file. |
| `vg.open_cgmes(files)` | Open CGMES XML or ZIP files. |
| `vg.save_cgmes_file(...)` | Export CGMES profiles. |
| `vg.power_flow(grid, options=None)` | Snapshot AC power flow. |
| `vg.power_flow3ph(grid, options=None)` | Snapshot three-phase power flow. |
| `vg.power_flow_ts(grid, options=None)` | Time-series AC power flow. |
| `vg.power_flow3ph_ts(grid, options=None)` | Three-phase time-series power flow. |
| `vg.linear_power_flow(grid, options=None)` | Snapshot PTDF and LODF analysis. |
| `vg.linear_power_flow_ts(grid, options=None)` | Time-series linear analysis. |
| `vg.short_circuit(grid, fault_index, ...)` | Short-circuit analysis at one bus. |
| `vg.continuation_power_flow(grid, ...)` | Voltage-stability continuation run. |
| `vg.linear_opf(grid, options=...)` | Linear optimal power flow. |
| `vg.nonlinear_opf(grid, opf_options=...)` | AC nonlinear optimal power flow. |
| `vg.simple_opf(grid, options=...)` | Greedy-dispatch OPF. |
| `vg.balanced_pf(grid, ...)` | Greedy OPF followed by power flow. |
| `vg.contingency_analysis(grid, options=None)` | Snapshot contingency analysis. |
| `vg.contingencies_ts(grid, ...)` | Time-series contingency analysis. |
| `vg.clustering(grid, n_points=100)` | Time-series representative samples. |

Some studies do not have a convenience function in `api.py`. Use their driver
directly, call `run()`, then read `driver.results`.

```python
driver = vg.SigmaAnalysisDriver(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
)
driver.run()
results = driver.results
```

## GUI session results

`app.session` stores studies completed through GUI workflows. It is useful for
reading results that already exist in the GUI, but blocking `vg.*` helpers
return their result directly and do not need `app.session`.

```python
driver, results = app.session.power_flow
if results is not None:
    print(results.converged)
else:
    print("No GUI power-flow result is available")
```

| Session property | Result object |
|------------------|---------------|
| `app.session.clustering` | `ClusteringResults` |
| `app.session.power_flow` | `PowerFlowResults` |
| `app.session.power_flow_3ph` | `PowerFlowResults3Ph` |
| `app.session.power_flow_ts` | `PowerFlowTimeSeriesResults` |
| `app.session.power_flow_3ph_ts` | `PowerFlowTimeSeriesResults3Ph` |
| `app.session.state_estimation` | `StateEstimationResults` |
| `app.session.short_circuit` | `ShortCircuitResults` |
| `app.session.linear_power_flow` | `LinearAnalysisResults` |
| `app.session.linear_power_flow_ts` | `LinearAnalysisTimeSeriesResults` |
| `app.session.contingency` | `ContingencyAnalysisResults` |
| `app.session.contingency_ts` | `ContingencyAnalysisTimeSeriesResults` |
| `app.session.continuation_power_flow` | `ContinuationPowerFlowResults` |
| `app.session.net_transfer_capacity` | `AvailableTransferCapacityResults` |
| `app.session.net_transfer_capacity_ts` | `AvailableTransferCapacityTimeSeriesResults` |
| `app.session.optimal_power_flow` | `OptimalPowerFlowResults` |
| `app.session.optimal_power_flow_ts` | `OptimalPowerFlowTimeSeriesResults` |
| `app.session.optimal_net_transfer_capacity` | `OptimalNetTransferCapacityResults` |
| `app.session.optimal_net_transfer_capacity_ts` | `OptimalNetTransferCapacityTimeSeriesResults` |
| `app.session.nodal_capacity_optimization` | `NodalCapacityResults` |
| `app.session.nodal_capacity_optimization_ts` | `NodalCapacityTimeSeriesResults` |
| `app.session.reliability_analysis` | `ReliabilityResults` |
| `app.session.rms_dynamic_simulation` | `RmsResults` |
| `app.session.emt_dynamic_simulation` | `EmtResults` |
| `app.session.stochastic_power_flow` | `StochasticPowerFlowResults` |
| `app.session.sigma_analysis` | `SigmaAnalysisResults` |
| `app.session.cascade` | `CascadingResults` |
| `app.session.inputs_analysis` | `InputsAnalysisResults` |
| `app.session.investments_evaluation` | `InvestmentsEvaluationResults` |
| `app.session.catalogue_optimization` | `InvestmentsEvaluationResults` |
| `app.session.node_groups_driver` | `NodeGroupsResults` |
| `app.session.small_signal_stability_simulation` | `SmallSignalStabilityRmsResults` |

Use `results.mdl(vg.ResultTypes.X)` when you need the same table model shown
in the Results tab.

```python
table = results.mdl(vg.ResultTypes.BusVoltageModule)
df = table.to_df()
print(df)
```

## Opening and saving files

Use the API helpers when the path is known.

```python
grid = vg.open_file("case.veragrid")
vg.save_file(grid, "case_copy.veragrid")
```

To make a file from a path the active GUI circuit, open it with the engine API
and pass the loaded grid to the GUI setter. This replaces `app.circuit`, clears
old study results, updates time controls, and creates a bus-branch diagram.

```python
path = "/home/user/grids/case.veragrid"
grid = vg.open_file(path)

app.set_circuit(grid=grid, create_diagram=True)

print(app.circuit.name)
```

Use `create_diagram=False` for very large files when you only need to run
scripted studies and do not need the schematic immediately.

CGMES can be loaded from a ZIP file, a list of XML files, or a mixture of XML
and ZIP boundary files.

```python
grid = vg.open_file(["grid_EQ.xml", "grid_TP.xml", "grid_SV.xml"])
grid = vg.open_cgmes("model_cgmes.zip")
```

For CGMES export, provide the boundary set and optionally a solved power flow
so the SV profile can be written.

```python
pf_results = vg.power_flow(app.circuit)

logger = vg.save_cgmes_file(
    grid=app.circuit,
    filename="exported_cgmes.zip",
    cgmes_boundary_set_path="boundary.zip",
    cgmes_version=vg.CGMESVersions.v2_4_15,
    pf_results=pf_results,
)

logger.print()
```

For PSS/E RAW or RAWX export with a selected time step, use `FileSave`.

```python
options = vg.FileSavingOptions(
    file_type=vg.FileType.PSSE_raw,
    raw_version="35",
    t_idx=3,
)

vg.FileSave(
    circuit=app.circuit,
    file_name="network_t3.raw",
    options=options,
).save()
```

## Building and editing a grid

Create VeraGrid device objects and add them to `app.circuit`.

```python
grid = app.circuit
grid.clear()

bus1 = grid.add_bus(vg.Bus(name="Bus 1", Vnom=110.0))
bus2 = grid.add_bus(vg.Bus(name="Bus 2", Vnom=110.0))

grid.add_generator(bus=bus1, api_obj=vg.Generator(name="G1", P=100.0))
grid.add_load(bus=bus2, api_obj=vg.Load(name="L2", P=80.0, Q=30.0))

line = vg.Line(bus_from=bus1, bus_to=bus2, name="Line 1-2", r=0.01, x=0.05)
grid.add_line(line)

app.create_schematic_from_api()
app.adjust_all_node_width()
```

Common device collections include:

| Collection | Typical add method |
|------------|--------------------|
| `grid.buses` | `grid.add_bus(vg.Bus(...))` |
| `grid.lines` | `grid.add_line(vg.Line(...))` |
| `grid.transformers2w` | `grid.add_transformer2w(vg.Transformer2W(...))` |
| `grid.hvdc_lines` | `grid.add_hvdc(vg.HvdcLine(...))` |
| `grid.vsc_devices` | `grid.add_vsc(vg.VSC(...))` |
| `grid.loads` | `grid.add_load(bus=bus, api_obj=vg.Load(...))` |
| `grid.generators` | `grid.add_generator(bus=bus, api_obj=vg.Generator(...))` |
| `grid.batteries` | `grid.add_battery(bus=bus, api_obj=vg.Battery(...))` |
| `grid.shunts` | `grid.add_shunt(bus=bus, api_obj=vg.Shunt(...))` |
| `grid.static_generators` | `grid.add_static_generator(...)` |
| `grid.current_injections` | `grid.add_current_injection(...)` |
| `grid.contingency_groups` | `grid.add_contingency_group(...)` |
| `grid.contingencies` | `grid.add_contingency(...)` |
| `grid.short_circuit_events` | `grid.add_short_circuit_event(...)` |
| `grid.investments_groups` | `grid.add_investments_group(...)` |
| `grid.investments` | `grid.add_investment(...)` |
| `grid.rms_events_groups` | RMS event-group add methods. |
| `grid.emt_events_groups` | EMT event-group add methods. |

Inspect a live object with `dir(obj)` or by printing its properties directly.
The device reference files under `doc/md_source/devices` describe registered
properties for each device type.

```python
bus = app.circuit.buses[0]
print(bus.name, bus.Vnom, bus.active)
```

## Time series

Time-series studies require profiles in the grid and a valid time profile.
The GUI can import CSV or Excel profiles from the database tab. From the
console, inspect the time axis and profile count before launching a run.

```python
grid = app.circuit
print(grid.has_time_series)
print(grid.get_time_number())
print(grid.time_profile)
```

Run every time index:

```python
results = vg.power_flow_ts(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
)
print(results.voltage.shape)
```

Run selected indices:

```python
time_indices = np.array([0, 6, 12, 18], dtype=int)
results = vg.power_flow_ts(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
    time_indices=time_indices,
)
```

Run representative samples and expand them back to the full time axis:

```python
clusters = vg.clustering(app.circuit, n_points=200)
results = vg.power_flow_ts(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
    clustering_results=clusters,
    auto_expand=True,
)
```

Time-series result matrices normally use row `time` and column `device`.

```python
vm_t0 = np.abs(results.voltage[0, :])
loading_max = np.max(np.abs(results.loading), axis=0)
print(vm_t0)
print(loading_max)
```

## Power flow

Power flow solves the steady-state network. Options include the solver,
tolerance, maximum iterations, distributed slack, reactive power controls, tap
controls, remote-voltage controls, temperature correction, and impedance
tolerances.

```python
options = vg.PowerFlowOptions(vg.SolverType.NR, verbose=False)
results = vg.power_flow(app.circuit, options=options)

print(results.converged, results.error)
print(results.get_bus_df())
print(results.get_branch_df())
```

Important `PowerFlowResults` fields:

| Field | Meaning |
|-------|---------|
| `voltage` | Complex bus voltage. |
| `Sbus` | Complex bus power injection. |
| `Sf`, `St` | Complex branch power at from and to sides. |
| `If`, `It` | Complex branch current at from and to sides. |
| `loading` | Branch loading. |
| `losses` | Complex branch losses. |
| `Pf_hvdc`, `Pt_hvdc`, `loading_hvdc` | HVDC results. |
| `Pfp_vsc`, `Pfn_vsc`, `Vdc_vsc`, `loading_vsc` | VSC results. |
| `gen_p`, `gen_q`, `battery_p`, `battery_q`, `shunt_q` | Device outputs. |
| `converged`, `error` | Solver status. |

Plot bus voltage magnitudes:

```python
plt.figure()
plt.plot(np.abs(results.voltage))
plt.xlabel("Bus index")
plt.ylabel("Voltage [p.u.]")
plt.show()
```

## Three-phase power flow

Three-phase power flow is used for unbalanced networks. It provides neutral and
phase A, B, and C quantities for buses and branches.

```python
results = vg.power_flow3ph(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
)

print(results.get_voltage_3ph_df())
print(results.get_current_3ph_df())
```

Important fields include `voltage_A`, `voltage_B`, `voltage_C`, `Sf_A`,
`Sf_B`, `Sf_C`, `If_A`, `If_B`, `If_C`, `loading_A`, `loading_B`,
`loading_C`, `gen_q_A`, `battery_q_A`, and `shunt_q_A`, with equivalent
fields for the other phases.

Three-phase time series uses the same pattern:

```python
results = vg.power_flow3ph_ts(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
)
print(results.voltage_A.shape)
```

## Linear analysis

Linear analysis computes PTDF and LODF sensitivity factors and approximate
branch flows. It is useful for screening, transfer studies, contingency
analysis, and time-series approximations.

```python
options = vg.LinearAnalysisOptions()
results = vg.linear_power_flow(app.circuit, options=options)

print(results.PTDF)
print(results.LODF)
print(results.get_branch_df())
```

Important `LinearAnalysisResults` fields:

| Field | Meaning |
|-------|---------|
| `PTDF` | Power transfer distribution factors. |
| `LODF` | Line outage distribution factors. |
| `HvdcDF`, `HvdcODF` | HVDC distribution and outage factors. |
| `VscDF`, `VscODF` | VSC distribution and outage factors. |
| `Sf` | Linear branch flows. |
| `Sbus` | Corrected bus injections. |
| `voltage` | Linear voltage estimate. |
| `loading` | Linear branch loading. |

Time-series linear analysis:

```python
results = vg.linear_power_flow_ts(
    grid=app.circuit,
    options=vg.LinearAnalysisOptions(),
)
print(results.Sf.shape)
```

## Contingencies

Contingencies are modelled with contingency groups and contingency objects. The
analysis can use linear factors or full power flow, depending on the options.

```python
grid = app.circuit
line = grid.lines[0]

group = vg.ContingencyGroup(name="Line 1 outage")
grid.add_contingency_group(group)

contingency = vg.Contingency(
    device=line,
    group=group,
    prop=vg.ContingencyOperationTypes.Active,
    value=0,
)
grid.add_contingency(contingency)

options = vg.ContingencyAnalysisOptions(
    contingency_method=vg.ContingencyMethod.PowerFlow,
    contingency_groups=grid.get_contingency_groups(),
    pf_options=vg.PowerFlowOptions(vg.SolverType.NR),
)
results = vg.contingency_analysis(grid, options=options)
print(results.get_bus_df())
```

Time-series contingencies:

```python
results = vg.contingencies_ts(
    circuit=app.circuit,
    use_clustering=True,
    n_points=200,
    contingency_method=vg.ContingencyMethod.Linear,
)
print(results.loading.shape)
```

## Short circuit

Use the helper for a bus-index fault. If no power-flow result is supplied, the
helper runs one first.

```python
pf_results = vg.power_flow(app.circuit)
results = vg.short_circuit(
    grid=app.circuit,
    fault_index=0,
    fault_type=vg.FaultType.LG,
    pf_results=pf_results,
)

print(results.SCpower)
print(results.voltage)
```

For custom short-circuit events, add the event and use the driver directly.

```python
event = vg.ShortCircuitEvent(
    device=app.circuit.buses[0],
    fault_type=vg.FaultType.LLG,
    method=vg.MethodShortCircuit.sequences,
    phases=vg.PhasesShortCircuit.a,
)
app.circuit.add_short_circuit_event(event)

driver = vg.ShortCircuitDriver(
    grid=app.circuit,
    options=vg.ShortCircuitOptions(),
    pf_options=vg.PowerFlowOptions(),
    pf_results=pf_results,
)
driver.run()
results = driver.results
```

## Optimal power flow

Linear OPF is the usual planning-screening workflow.

```python
options = vg.OptimalPowerFlowOptions(
    solver=vg.SolverType.LINEAR_OPF,
    mip_solver=vg.MIPSolvers.HIGHS,
)
results = vg.linear_opf(app.circuit, options=options)

print(results.generator_power)
print(results.load_shedding)
print(results.bus_shadow_prices)
```

AC nonlinear OPF:

```python
options = vg.OptimalPowerFlowOptions()
results = vg.nonlinear_opf(
    grid=app.circuit,
    opf_options=options,
    plot_error=False,
)
```

Greedy dispatch followed by a balanced power flow:

```python
results = vg.balanced_pf(app.circuit)
print(results.get_bus_df())
```

Time-series OPF is a direct driver workflow.

```python
options = vg.OptimalPowerFlowOptions(
    solver=vg.SolverType.LINEAR_OPF,
    mip_solver=vg.MIPSolvers.HIGHS,
)
driver = vg.OptimalPowerFlowTimeSeriesDriver(
    grid=app.circuit,
    options=options,
    time_indices=app.circuit.get_all_time_indices(),
)
driver.run()
results = driver.results
```

## Transfer capacity

Available transfer capacity needs source buses, receiving buses, monitored
branches, and branch senses. The `bus_idx_from` and `bus_idx_to` arrays define
the transfer direction. The monitored branch arrays define what is reported.

```python
bus_idx_from = np.array([0], dtype=int)
bus_idx_to = np.array([1], dtype=int)
idx_br = np.array([0], dtype=int)
sense_br = np.array([1.0], dtype=float)

options = vg.AvailableTransferCapacityOptions(
    bus_idx_from=bus_idx_from,
    bus_idx_to=bus_idx_to,
    idx_br=idx_br,
    sense_br=sense_br,
    dT=100.0,
    threshold=0.02,
    mode=vg.AvailableTransferMode.Generation,
)

driver = vg.AvailableTransferCapacityDriver(
    grid=app.circuit,
    options=options,
)
driver.run()
results = driver.results
```

Time-series ATC:

```python
driver = vg.AvailableTransferCapacityTimeSeriesDriver(
    grid=app.circuit,
    options=options,
    time_indices=app.circuit.get_all_time_indices(),
)
driver.run()
results = driver.results
```

Optimal net transfer capacity uses OPF internally.

```python
ntc_options = vg.OptimalNetTransferCapacityOptions(
    sending_bus_idx=bus_idx_from,
    receiving_bus_idx=bus_idx_to,
    transfer_method=vg.AvailableTransferMode.InstalledPower,
    opf_options=vg.OptimalPowerFlowOptions(),
    lin_options=vg.LinearAnalysisOptions(),
)

driver = vg.OptimalNetTransferCapacityDriver(
    grid=app.circuit,
    options=ntc_options,
)
driver.run()
results = driver.results
```

## Continuation power flow

Continuation power flow traces the voltage-stability curve from a solved base
case toward a target loading direction.

```python
pf_results = vg.power_flow(app.circuit)
results = vg.continuation_power_flow(
    grid=app.circuit,
    pf_results=pf_results,
    factor=2.0,
    stop_at=vg.CpfStopAt.Full,
)

print(results.lambdas)
print(results.voltages)
```

Pass a vector as `factor` when the loading direction must be bus-specific.

## Sigma analysis

Sigma analysis estimates proximity to voltage collapse. It has no helper in
`api.py`, so use the driver directly.

```python
driver = vg.SigmaAnalysisDriver(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
    t_idx=None,
    classical_sigma=False,
)
driver.run()
results = driver.results

print(results.sigma_re)
print(results.sigma_im)
```

## Stochastic power flow

Stochastic power flow samples load and generation uncertainty using Monte Carlo
or Latin Hypercube sampling.

```python
driver = vg.StochasticPowerFlowDriver(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
    mc_tol=1e-3,
    batch_size=100,
    sampling_points=10000,
    simulation_type=vg.StochasticPowerFlowType.LatinHypercube,
)
driver.run()
results = driver.results

print(results.voltage)
print(results.loading)
```

## Clustering

Clustering selects representative time steps from the time-series profiles and
stores the sample probabilities.

```python
results = vg.clustering(app.circuit, n_points=200)

print(results.time_indices)
print(results.sampled_probabilities)
```

Use the result as an input to time-series helpers:

```python
pf_ts = vg.power_flow_ts(
    grid=app.circuit,
    clustering_results=results,
    auto_expand=True,
)
```

## State estimation

State estimation uses measurement devices attached to the grid, such as active
and reactive power measurements, voltage measurements, and current
measurements.

```python
options = vg.StateEstimationOptions()
driver = vg.StateEstimationDriver(app.circuit, options)
driver.run()
results = driver.results

print(results.voltage)
print(results.Sbus)
```

Add measurement devices through the model before running the driver. The
measurement device docs describe `PfMeasurement`, `QfMeasurement`,
`VmMeasurement`, `IfMeasurement`, and the other supported measurement classes.

## Inputs analysis and model debugging

Inputs analysis builds the model summary tables used by the debugging tools.

```python
driver = vg.InputsAnalysisDriver(grid=app.circuit)
results = driver.results

table = results.mdl(vg.ResultTypes.LoadPower)
print(table.to_df())
```

Use diagnostics from the GUI when you need the full interactive repair flow.
Use scripting when you need reproducible inspections:

```python
for bus in app.circuit.buses:
    print(bus.name, bus.Vnom, bus.active)
```

## Nodal hosting capacity

Nodal hosting capacity optimizes how much generation or load can be connected
at selected buses.

```python
capacity_nodes_idx = np.array([0, 1], dtype=int)

options = vg.NodalCapacityOptions(
    opf_options=vg.OptimalPowerFlowOptions(),
    capacity_nodes_idx=capacity_nodes_idx,
    nodal_capacity_sign=1.0,
    method=vg.NodalCapacityMethod.LinearOptimization,
)

driver = vg.NodalCapacityDriver(
    grid=app.circuit,
    options=options,
)
driver.run()
results = driver.results
```

Time-series nodal capacity:

```python
driver = vg.NodalCapacityTimeSeriesDriver(
    grid=app.circuit,
    options=options,
    time_indices=app.circuit.get_all_time_indices(),
)
driver.run()
results = driver.results
```

## Reliability and cascading

Reliability studies sample outage states and generation adequacy with a power
flow model.

```python
driver = vg.ReliabilityStudyDriver(
    grid=app.circuit,
    pf_options=vg.PowerFlowOptions(),
    reliability_mode=vg.ReliabilityMode.GenerationAdequacy,
    time_indices=app.circuit.get_all_time_indices(),
    n_sim=10000,
)
driver.run()
results = driver.results
```

Cascading analysis removes branches according to the selected cascade criteria.

```python
driver = vg.CascadingDriver(
    grid=app.circuit,
    options=vg.PowerFlowOptions(),
    triggering_idx=None,
)
driver.run()
results = driver.results
```

## Investments and catalogue optimization

Investment studies evaluate candidate devices grouped under investment groups.
Create the candidate investments in the grid first, then select the investment
evaluation driver and options matching the optimization method documented in
`investment_optimization.md` and `catalogue_element_optimization.md`.

```python
group = vg.InvestmentsGroup(name="Candidate reinforcements")
app.circuit.add_investments_group(group)

investment = vg.Investment(
    name="Build line 1-2",
    group=group,
    CAPEX=100000.0,
)
app.circuit.add_investment(investment)
```

The result object reports the evaluated combinations, objective values, costs,
losses, overload scores, voltage scores, and reliability terms according to
the selected objective function.

## RMS dynamics

RMS dynamic simulation starts from a solved balanced power flow and uses RMS
model templates plus RMS events.

```python
pf_results = vg.power_flow(app.circuit)

driver = vg.RmsSimulationDriver(
    grid=app.circuit,
    options=vg.RmsOptions(),
    pf_results=pf_results,
)
driver.run()
results = driver.results

print(results.time)
```

Use the dynamic model library docs for the available RMS blocks, generator
models, converter controls, loads, HVDC components, and event definitions.

## EMT dynamics

EMT simulation can start from three-phase or balanced power-flow results. Use
three-phase results for unbalanced phase-domain cases.

```python
pf3 = vg.power_flow3ph(app.circuit)

driver = vg.EmtSimulationDriver(
    grid=app.circuit,
    options=vg.EmtOptions(),
    pf_results_3ph=pf3,
)
driver.run()
results = driver.results

print(results.time)
```

The EMT docs cover the EMT model templates, solver settings, faults, lines,
transformers, converters, controls, and event groups.

## Small-signal stability

RMS small-signal stability linearizes the RMS dynamic model around the
operating point.

```python
pf_results = vg.power_flow(app.circuit)

driver = vg.SmallSignalStabilityRmsDriver(
    grid=app.circuit,
    rms_options=vg.RmsOptions(),
    sss_options=vg.RmsSmallSignalStabilityOptions(),
    pf_results=pf_results,
)
driver.run()
results = driver.results
```

EMT small-signal stability uses the EMT limit-cycle and Floquet workflow.

```python
pf3 = vg.power_flow3ph(app.circuit)

driver = vg.SmallSignalStabilityEmtDriver(
    grid=app.circuit,
    emt_options=vg.EmtOptions(),
    sss_options=vg.SmallSignalStabilityEmtOptions(),
    pf_results=pf3,
)
driver.run()
results = driver.results
```

## Topology, compilation, and arrays

For numerical inspection, compile the current circuit at a snapshot or time
index.

```python
nc = vg.compile_numerical_circuit_at(circuit=app.circuit, t_idx=None)

print(nc.bus_data.names)
print(nc.passive_branch_data.names)
print(nc.Ybus)
```

Topology processing separates islands, applies connectivity, and builds the
arrays consumed by the solvers. Use the topology and data-model docs when you
need to inspect compiled buses, branches, injections, HVDC, VSC, or sparse
matrix structures.

## Result export

Many result objects expose data-frame helpers.

```python
pf = vg.power_flow(app.circuit)

pf.get_bus_df().to_csv("bus_results.csv")
pf.get_branch_df().to_excel("branch_results.xlsx")
```

When a result table is available through `mdl`, convert it through the table
model:

```python
table = pf.mdl(vg.ResultTypes.BusVoltageModule)
df = table.to_df()
df.to_csv("voltage_table.csv")
```

Matplotlib is already available as `plt`.

```python
plt.figure()
plt.plot(np.abs(pf.voltage), marker="o")
plt.xlabel("Bus")
plt.ylabel("Voltage [p.u.]")
plt.grid(True)
plt.show()
```

## Practical patterns

Always keep the result returned by the blocking helper:

```python
pf = vg.power_flow(app.circuit)
if pf is not None:
    print(pf.get_bus_df())
else:
    print("No result returned")
```

Save model edits explicitly:

```python
app.circuit.buses[0].name = "Main bus"
vg.save_file(app.circuit, "edited_case.veragrid")
```

Refresh the schematic after programmatic model edits:

```python
app.create_schematic_from_api()
app.adjust_all_node_width()
```

Run the same calculation for many files:

```python
paths = ["case1.veragrid", "case2.veragrid", "case3.veragrid"]
rows = list()

for path in paths:
    grid = vg.open_file(path)
    pf = vg.power_flow(grid)
    rows.append([path, bool(pf.converged), float(np.max(np.abs(pf.loading)))])

df = pd.DataFrame(rows, columns=["file", "converged", "max_loading"])
print(df)
```

## Source documentation map

Use these files for the full theory and GUI background behind each scripting
workflow:

| Topic | Detailed docs |
|-------|---------------|
| Installation and UI | `installation.md`, `user_interface.md` |
| Grid structure and topology | `structure.md`, `topology.md`, `data_models.md` |
| Model editing | `modelling.md`, `device_relationships.md`, `devices/*.md` |
| File import and export | `file_operations.md` |
| Diagnostics | `model_debugging.md`, `grid_analysis.md` |
| Power flow | `power_flow.md` |
| Linear factors | `linear_analysis.md` |
| Optimal power flow | `optimal_power_flow.md` |
| Contingencies | `contingency_analysis.md` |
| Short circuit | `short_circuit.md` |
| Stochastic studies | `stochastic_power_flow.md` |
| Continuation and sigma | `continuation_power_flow.md`, `sigma_analysis.md` |
| Transfer capacity | `net_transfer_capacity.md` |
| Clustering and reduction | `clustering.md`, `grid_reduction.md` |
| Procedural grids | `procedural_grid.md` |
| Nodal hosting capacity | `nodal_hosting_capacity.md` |
| Reliability and cascading | `reliability.md`, `cascading.md` |
| Investments | `investment_optimization.md`, `catalogue_element_optimization.md` |
| Dynamic simulations | `dynamic_simulations.md`, `rms_simulations.md`, `emt_simulations.md` |
| Practical dynamic sessions | `RMS_practical_session.md`, `EMT_practical_session.md` |
| Small-signal stability | `small_signal_stability_rms.md`, `small_signal_stability_emt.md` |
| Dynamic model library | `dynamic_model_library_index.md`, `dyn_templates/**/*.md` |
| DAE block authoring | `dae_block_authoring.md` |
| Plugins | `plugins.md` |
