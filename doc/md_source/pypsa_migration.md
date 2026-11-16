# Moving a PyPSA case into VeraGrid without lying to yourself

This is the PyPSA-to-VeraGrid migration manual. It says what we import, what we
turn into a proper physical VeraGrid topology, what we preserve only as a useful
approximation, and what we refuse to invent.

That last bit matters. PyPSA has a small set of generic components that can mean
several different physical things. VeraGrid has actual devices and actual
topology. Treating a source table as if it were automatically a circuit diagram
is how you get a file that opens, an OPF that runs, and numbers that mean fuck
all. We do not do that here.

The importer reads PyPSA NetCDF (`.nc`) and HDF5 through PyPSA, builds a
VeraGrid `MultiCircuit`, and lets you save the result as `.veragrid`. It is a
conversion of model meaning, not a ritual format conversion.

## The rule: topology first, cleverness second

The topology processing is the best example of how this importer thinks.

Take `Line.num_parallel`. PyPSA-Eur uses it as a multiplier. It might be `3`,
it might be `0.67`, and it might be `0`. A lazy importer does this:

```python
number_of_lines = int(num_parallel)
```

That turns `0.67` into zero, then usually panics and makes one random full line.
Congratulations: the file loads, the electrical model is wrong, and the user
gets thousands of useless warnings.

VeraGrid does it properly:

- `3` means three actual parallel Line objects. They are named `line-1`,
  `line-2`, `line-3`, and live in a BranchGroup because they are three physical
  circuits, not one magic branch with a number taped to it.
- `0.67` means one exact electrical equivalent. Series impedance is divided by
  `0.67`, shunt susceptance and thermal capability are multiplied by `0.67`.
  That is what an aggregated fractional circuit means.
- `0` means there is no conductor. We skip it. We do not conjure copper out of
  a zero just because a GUI likes every table row to become an object.

Every mapping in this document follows the same rule. If VeraGrid has the
physical topology to represent the thing, we create it. If it has an exact
equivalent, we use it and say so. If neither is true, we log a warning rather
than smuggling a modelling assumption into a different device.

## Before you start touching things

- Install the optional `pypsa` dependency in the Python environment that runs
  VeraGrid.
- Keep the source `.nc` file. A `.veragrid` export is the converted model, not
  a replacement source format.
- Read importer messages. Information messages say what was deliberately built;
  warnings are not decorative: they are the bits where you must decide whether
  the source model means what you think it means.
- Run at least one power flow or OPF after conversion. Import success means the
  source was readable, not that a new optimisation has the same policy rules.

Programmatic import is available through the parser entry points:

```python
from VeraGridEngine.IO.others.pypsa_parser import parse_pypsa_netcdf
from VeraGridEngine.basic_structures import Logger

logger = Logger()
circuit = parse_pypsa_netcdf("case.nc", logger)

for entry in logger.entries:
    print(entry)
```

Use VeraGrid's normal save API or the GUI to write the returned circuit as
`.veragrid`.

## The mental model

PyPSA is built around generic components and a single optimisation model.
VeraGrid keeps an explicit electrical topology, physical storage topology, and
device relationships. The conversion therefore follows physical meaning rather
than source class names:

| PyPSA meaning | VeraGrid representation |
| --- | --- |
| AC/DC electrical bus | `Bus` |
| country, substation, nominal-voltage grouping | `Country`, `Substation`, `VoltageLevel` |
| AC branch | `Line` |
| integer parallel AC circuits | separate `Line` objects plus `BranchGroup` |
| DC/HVDC Link | `HvdcLine` or an HVDC star |
| producer | `Generator` |
| consumer | `Load` |
| carrier taxonomy | `Technology` plus device association |
| carrier CO2 intensity | `EmissionGas` plus generator association |
| extendable capacity | `Investment` in an `InvestmentsGroup` |
| energy state | `FluidNode` |
| conversion out of an energy state | `FluidTurbine` plus Generator |
| conversion into an energy state | `FluidPump` plus negative-P Generator |
| non-electric carrier transport | `FluidPath` |
| snapshot-indexed source fields | native VeraGrid property profiles |
| solved source dispatch/results | source evidence only; rerun a VeraGrid study |

This is especially important for storage. A PyPSA `StorageUnit` is **not**
shoved into a VeraGrid Battery because both happen to store energy. It becomes a
native fluid-energy system, so its state, inflow, losses, charge/discharge
efficiency and energy targets live in one honest balance equation.

### The objects people usually forget

The electrical drawing is not the entire model. The importer also builds the
stuff that makes the model usable in a real VeraGrid workflow:

- **Time series are first-class.** A static source number goes to the static
  native property; a source column indexed by snapshots goes to the matching
  native profile. We do not convert a profile into a pile of unrelated device
  copies or silently take its first value.
- **Technologies are associations, not decoration.** A PyPSA carrier becomes a
  VeraGrid Technology and is associated with generators, loads, and the
  electrical conversion machines created for storage. This is what lets native
  technology reporting work after migration.
- **Fuel is not guessed from a carrier.** PyPSA's generic carrier label can
  mean fuel, technology, service, medium, or accounting category. The importer
  maps it to Technology. It does not manufacture a `Fuel` association called
  `gas`, `battery`, or `hydrogen` unless the source actually supplies separate
  fuel semantics.
- **CO2 is not a fuel either.** `carriers.co2_emissions` becomes an
  `EmissionGas` rate. A CO2 cap is a different thing and remains a global
  policy constraint to recreate explicitly.
- **Investments are records.** PyPSA extendability becomes a native Investment
  attached to the device property that actually changes. Investment groups are
  split by component type and discount rate, because mixing a 3% and 7% asset
  in one group is nonsense.
- **Contingencies are not invented.** PyPSA's core network tables do not carry
  a VeraGrid-style contingency catalogue. The importer therefore creates no
  `Contingency` or `ContingencyGroup` from a vague outage-looking field. Build
  those explicitly in VeraGrid after import when that is the study you want.
- **Source results are not a study session.** PyPSA `p`, `q`, dual, marginal
  price and solved-state tables are evidence for validation. They are not
  inserted as if VeraGrid had run the corresponding driver.

## Time axis and profiles

VeraGrid keeps the PyPSA snapshot index as the circuit profile index. A regular
`DatetimeIndex` is retained. A PyPSA multi-index is flattened to its timestamp
level and produces a warning because an investment-period index cannot be kept
as an independent native profile axis.

Every imported time series must have exactly one value per snapshot. Missing or
misaligned columns are ignored with a warning. PyPSA uses `NaN` in several
constraint/setpoint series to mean “not fixed”; the importer preserves that
meaning rather than replacing it with zero.

PyPSA snapshot objective weights are currently reported when non-uniform. They
are not yet persisted as a VeraGrid sampling/probability object, so weighted
objective comparisons require manual treatment.

## Component mapping

Read this as the contract. “Profile” means one native snapshot-aligned profile;
“review” means the importer tells you it did not silently fake an equivalent.

### Device mapping matrix

| PyPSA component | VeraGrid object(s) | Main static mapping | Main profile mapping | What is deliberately not faked |
| --- | --- | --- | --- | --- |
| `Bus` | `Bus` | `v_nom`, V limits, slack/DC state, coordinates | `v_mag_pu_set` -> `Vm0_prof` | independent investment-period axis |
| bus country/substation | `Country`, `Substation`, `VoltageLevel` | country, substation label, nominal voltage | — | source GIS semantics beyond coordinates |
| `Carrier` | `Technology` | name, nice name, colour, reference cost | — | Fuel association from a vague carrier name |
| carrier `co2_emissions` | `EmissionGas` + generator association | CO2 rate | — | global CO2 policy cap |
| `Generator` | `Generator` | `p_nom`, P/Q setpoints and bounds, costs, ramps, UC fields | P/Q setpoints, P limits, cost, status, maintenance | `e_sum_min/max` cumulative-energy constraint |
| `Load` | `Load` | P/Q setpoint, active state | P/Q setpoint | source solved demand result as a VeraGrid session |
| `LineType` | `SequenceLineType` | electrical type data | — | — |
| `Line` | `Line`, possibly `BranchGroup` | impedance/type, length, rating, active state | `s_max_pu` -> rating profile | a fake full circuit for zero `num_parallel` |
| `TransformerType` | `TransformerType` | nameplate and no-load data | — | controller policy inferred from type alone |
| `Transformer` | `Transformer2W` | impedance, tap, phase shift, rating | `s_max_pu`, `phase_shift` | undocumented tap controller logic |
| `ShuntImpedance` | `Shunt` | Siemens converted at nominal voltage | — | — |
| electrical `Link` | `HvdcLine`, possibly HVDC star | P rating, P setpoint, cost, active state | P setpoint, P limits, cost, status | Link efficiency as cable resistance; exact multi-output ratio in a fresh OPF |
| `StorageUnit` | `FluidNode` + Pump + Turbine + two Generators | energy state, power rating, efficiencies, inflow, loss | limits, efficiencies, inflow, loss, schedules, targets, spill cost | Battery shortcut that loses storage physics |
| `Store` | `FluidNode` + Pump + Turbine + two Generators | energy state, bounds, loss | energy bounds, loss, P schedule, energy target | a physical converter rating where PyPSA gives none |
| non-electric fluid-to-fluid `Link` | `FluidPath` | flow bounds, transfer loss | flow bounds, loss | electrical conversion at a carrier boundary |
| electricity -> fluid `Link` | review / future `FluidP2X` path | — | — | pretending a pipe consumes electricity |
| fluid -> electricity `Link` | review / future `FluidTurbine` path | — | — | pretending a pipe injects electricity |
| extendable component | `Investment`, `InvestmentsGroup` | nominal/optimal capacity, CAPEX, discount rate | — | modular/discrete expansion semantics |
| `GlobalConstraint` | warning / manual planning setup | — | — | policy object invented from a string |

### Field-level tables

### Buses, geography and hierarchy

| PyPSA field | VeraGrid target | Notes |
| --- | --- | --- |
| `name` | `Bus.name` | source identity retained |
| `v_nom` | `Bus.Vnom` | nominal kV |
| `v_mag_pu_min`, `v_mag_pu_max` | `Bus.Vmin`, `Bus.Vmax` | per-unit bounds |
| `v_mag_pu_set`, `v_mag_pu_set[t]` | `Vm0`, `Vm0_prof` | voltage target/initial guess |
| `control == Slack` | `is_slack` | source slack bus |
| `carrier == DC` | `is_dc` | DC-network flag |
| `x`, `y`, CRS | map position, longitude, latitude | transformed through source CRS |
| `country`, `substation` | Country/Substation/VoltageLevel links | hierarchy objects reused by name |

`Bus` maps to `Bus`.

- `v_nom`, `v_mag_pu_min`, `v_mag_pu_max`, `v_mag_pu_set`, `control`, and
  `carrier == "DC"` map to nominal voltage, voltage limits/setpoint, slack
  state, and DC flag.
- `buses_t.v_mag_pu_set` maps to `Vm0_prof`.
- bus `x`/`y` are transformed using the source CRS for map position; longitude
  and latitude are retained where available.
- `country`, `substation`, and nominal voltage create/reuse `Country`,
  `Substation`, and `VoltageLevel` objects.

Review source coordinate-reference-system metadata before trusting a map view.

### Carriers, technologies and emissions

| PyPSA field/table | VeraGrid field/object | Notes |
| --- | --- | --- |
| `carriers.index` | `Technology.name` | created once and reused |
| `carriers.nice_name` | `Technology.name2` | when non-empty |
| `carriers.color` | `Technology.color` | source colour retained |
| `carriers.marginal_cost` | `Technology.reference_cost` | reference metadata, not a device cost override |
| `carriers.co2_emissions` | `EmissionGas("CO2")` association value | rate on generating machines |

Each non-empty PyPSA carrier becomes a VeraGrid `Technology` when first used.

- carrier name -> Technology name;
- `nice_name` -> Technology alternate name;
- carrier `color` -> Technology colour;
- carrier `marginal_cost` -> Technology reference cost.

Generators, loads, and both electrical conversion generators created for fluid
storage receive the Technology association. FluidNode, FluidPath, Pump and
Turbine do not own a technology-association container; assigning the association
to the electrical machines keeps reporting and optimisation associations in the
native place.

Carrier `co2_emissions` creates/reuses an `EmissionGas` named `CO2` and is
associated with generating machines. This imports an emissions **rate**, not a
system-wide emission cap.

### Generators

| PyPSA field | VeraGrid field/profile | Conversion |
| --- | --- | --- |
| `p_nom` | `Snom` | MW/MVA source nameplate convention retained |
| `p_nom * p_min_pu`, `p_nom * p_max_pu` | `Pmin`, `Pmax` | MW dispatch interval |
| `p_set`, `q_set` | `P`, `Q`, `P_prof`, `Q_prof` | finite P schedule disables dispatch at that snapshot |
| `p_min_pu[t]`, `p_max_pu[t]` | `Pmin_prof`, `Pmax_prof` | multiplied by `p_nom` |
| `marginal_cost[t]` | `Cost`, `Cost_prof` | operating cost |
| `status[t]`, `maintenance[t]` | `active_prof` | maintenance forces inactive |
| ramp/start-up/min-time fields | Generator UC/ramp fields | active when the corresponding VeraGrid OPF mode is used |
| `p_nom_extendable`, costs, discount rate | Investment/InvestmentsGroup | planning record |

`Generator` maps to `Generator`.

- `p_nom * p_min_pu` and `p_nom * p_max_pu` -> MW dispatch limits;
- `p_set`, `q_set`, `p_min_pu`, `p_max_pu`, and `marginal_cost` time series ->
  corresponding VeraGrid profiles;
- finite `p_set[t]` fixes dispatch at that snapshot; `NaN` leaves it available
  to OPF;
- `status` -> availability profile; `maintenance` disables availability;
- `marginal_cost_quadratic`, start/shutdown cost, min-up/down, and ramp fields
  map to Generator operating fields;
- extendable `p_nom` imports a native Investment record.

PyPSA `e_sum_min/e_sum_max` cumulative-energy constraints are not yet native
constraints. `committable` is not treated as a mere “dispatchable” flag; the
normal VeraGrid unit-commitment formulation must be selected to use commitment
fields.

### Loads

| PyPSA field | VeraGrid field/profile |
| --- | --- |
| `p_set`, `q_set` | `P`, `Q`, `P_prof`, `Q_prof` |
| `carrier` | Technology association |
| `active` / construction state | `active` |

`Load` maps to `Load`.

- static and time-series `p_set`/`q_set` map directly;
- `carrier` maps to Technology;
- active state is retained.

### Lines and line types

| PyPSA field | VeraGrid field/object | Notes |
| --- | --- | --- |
| `LineType` electrical data | `SequenceLineType` | reusable line template |
| `type`, `length` | Line template application | or explicit R/X/B route |
| `r`, `x`, `b`, `g` | `Line` electrical design data | when no type is supplied |
| `s_nom * s_max_pu` | `rate` | operating limit |
| `s_max_pu[t]` | `rate_prof` | snapshot operating limit |
| `num_parallel` | Lines and BranchGroup | integer copies or fractional equivalent |

PyPSA `LineType` maps to `SequenceLineType`. A `Line` maps to native `Line`,
using its type where present or its explicit impedance/shunt data otherwise.
`s_max_pu` maps to the operating thermal rating and profile.

`num_parallel` is handled physically:

- integer `N > 1`: VeraGrid creates `N` separate, identical Lines, named
  `name-1`, `name-2`, ..., in a shared `BranchGroup`;
- fractional positive values: VeraGrid creates one exact electrical equivalent
  (`R`/`X` divided by multiplier, shunt `B` multiplied by multiplier, rating
  scaled accordingly);
- zero: the source row is skipped as a no-conductor placeholder, rather than
  becoming a fabricated conducting line.

Line capacity expansion imports an Investment record. PyPSA topology/subnetwork
metadata is not a separate native object.

### Transformers

| PyPSA field | VeraGrid target | Conversion |
| --- | --- | --- |
| transformer type data | `TransformerType` | nameplate/impedance information |
| `r`, `x`, `g`, `b` | `Transformer2W` | explicit electrical data |
| `tap_ratio` | `tap_module` | per unit |
| `phase_shift`, `phase_shift[t]` | `tap_phase`, `tap_phase_prof` | degrees -> radians |
| `s_nom * s_max_pu`, `s_max_pu[t]` | `rate`, `rate_prof` | MVA operating limit |

`TransformerType` maps to `TransformerType`; two-winding `Transformer` maps to
`Transformer2W`.

- impedance, shunt, rating and parallel circuits map;
- `s_max_pu[t]` maps to `rate_prof`;
- static and time-series `phase_shift` are converted from degrees to radians
  and map to controllable phase taps;
- capacity expansion imports Investment data.

PyPSA transformer phase shifting is supported. Review unusual tap-position or
control policies after import if their behaviour depends on a PyPSA-specific
controller rather than an explicit phase-shift value.

### Shunt impedances

| PyPSA field | VeraGrid target | Conversion |
| --- | --- | --- |
| `g`, `b` in Siemens | `Shunt.G`, `Shunt.B` | converted at bus nominal voltage |

`ShuntImpedance` maps to `Shunt`. PyPSA Siemens are converted at bus nominal
voltage into VeraGrid MW/MVAr conductance and susceptance quantities.

### Electrical Links and HVDC: do not call every Link a cable

PyPSA `Link` is generic process plumbing. It is not automatically an HVDC cable,
a VSC, a pipe, an electrolyser, or a turbine. We classify it by carrier and by
what exists at each endpoint before creating anything.

**DC/HVDC electrical Links** (`carrier` empty, `dc`, or `hvdc`) map to
`HvdcLine`:

| PyPSA Link field | VeraGrid target | Notes |
| --- | --- | --- |
| `bus0`, `bus1` | `HvdcLine.bus_from`, `bus_to` | electrical endpoints |
| `p_nom`, `p_min_pu`, `p_max_pu` | `rate` | symmetric envelope uses largest absolute bound |
| `p_set`, `p_set[t]` | `Pset`, `Pset_prof` | schedule |
| `p_min_pu[t]`, `p_max_pu[t]` | `rate_prof` | snapshot rating |
| `marginal_cost[t]` | `Cost`, `Cost_prof` | operating cost |
| `status[t]` | `active_prof` | availability |
| expansion fields | Investment | capacity planning record |

- `p_nom`, `p_min_pu`, `p_max_pu` -> symmetric native rating envelope;
- `p_set`, marginal cost, status, and limit profiles map;
- extendable capacity imports Investment data.

PyPSA Link efficiency is deliberately **not** converted to cable resistance.
It is a process/terminal efficiency, not an ohmic cable parameter. Turning one
into the other would be numerology, not modelling.

Multi-terminal electrical Links become an HVDC star: an artificial DC hub plus
one input and one output branch per output bus. Output ratings and schedules
are efficiency-scaled. This preserves a usable electrical topology, but a fresh
VeraGrid OPF cannot enforce PyPSA's exact one-variable fixed output ratios.

### StorageUnit and Store: the energy state gets a real topology

Both PyPSA `StorageUnit` and `Store` map to a virtual-fluid topology. The
canonical basis is:

```text
1 MWh stored energy = 1 hm3 virtual fluid = 1,000,000 m3
```

The units are virtual. Nobody is claiming that a battery is a lake. We use the
fluid subsystem because it already has the exact ingredients an energy state
needs: a level, inflow, loss, a charging machine, a discharging machine, and
proper time-series bounds.

For every imported storage element, VeraGrid creates:

1. a `FluidNode` for the energy state;
2. a positive-P Generator and `FluidTurbine` for discharge;
3. a negative-P Generator and `FluidPump` for charge.

Mapping details:

| PyPSA field | VeraGrid target |
| --- | --- |
| `p_nom * max_hours` / `e_nom` | FluidNode nominal level |
| `state_of_charge_initial` / `e_initial` | FluidNode initial level |
| `p_min_pu`, `p_max_pu` | pump/turbine power and flow limits |
| `efficiency_store`, `efficiency_dispatch` | pump/turbine efficiency |
| `inflow[t]` | FluidNode inflow profile |
| `standing_loss[t]` | FluidNode `loss_factor_prof` |
| `state_of_charge_set[t]`, `e_set[t]` | equal FluidNode min/max SoC bounds |
| Store `e_min_pu[t]`, `e_max_pu[t]` | FluidNode SoC profiles |
| StorageUnit `spill_cost[t]` | FluidNode spillage-cost profile |
| `p_dispatch_set[t]`, `p_store_set[t]` | separate discharge/charge schedules |

The storage recurrence is therefore:

```text
level[t] = (1 - loss_factor[t]) ** elapsed_hours * level[t-1]
           + inflow + pump_flow - turbine_flow - spillage
```

`loss_factor = 0` means no standing loss; `0.05` means 5% of stored level is
lost per hour. It maps directly from PyPSA `standing_loss`.

PyPSA `Store` has energy capacity but no converter nameplate. When no schedule
reveals a useful power envelope, the importer uses a broad virtual conversion
rating. Review and set a physical converter rating before relying on a new OPF.

### Non-electric Links and FluidPath: a pipe is a pipe

A Link between two **non-electric** buses which each resolve uniquely to an
imported virtual FluidNode maps to `FluidPath`.

| PyPSA Link field | FluidPath field/profile | Conversion |
| --- | --- | --- |
| `bus0`, `bus1` | `source`, `target` | resolved virtual FluidNodes |
| `p_nom * p_min_pu`, `p_nom * p_max_pu` | `min_flow`, `max_flow` | MW -> virtual m3/s |
| `p_min_pu[t]`, `p_max_pu[t]` | `min_flow_prof`, `max_flow_prof` | MW -> virtual m3/s |
| `efficiency`, `efficiency[t]` | `loss_factor`, `loss_factor_prof` | `1 - efficiency` |

- `p_nom`, `p_min_pu`, `p_max_pu` -> path flow limits;
- dynamic `p_min_pu`/`p_max_pu` -> flow-limit profiles;
- `efficiency` -> `loss_factor = 1 - efficiency` (per transfer, not per hour);
- `efficiency[t]` -> FluidPath loss-factor profile.

The imported path follows PyPSA's oriented terminal equation, not an invented
physical pipe law. For its signed path flow `f`, the source terminal carries
`f` and the target terminal carries `(1-loss_factor)*f`. This is one affine
constraint even when `f` becomes negative; therefore the importer adds no
direction binary and keeps the PyPSA LP behaviour. It also means a reversed
flow uses the same orientation-defined efficiency, exactly as PyPSA Link does.

If the intended asset is a physically symmetric bidirectional pipe, that is a
different model: the receiving end changes with the sign of the flow. That
requires a direction disjunction (binary variables) or a deliberately relaxed
loss model. Do not silently call that PyPSA-compatible behaviour.

An electricity-to-fluid Link is **not** a FluidPath: it needs a `FluidP2X` to
consume electrical power. A fluid-to-electric Link needs a `FluidTurbine` to
inject electrical power. A path alone cannot make power disappear from an AC
bus or appear at one. Those boundary conversions are reported for review rather
than dressed up as carrier-only transport.

## Investments

| PyPSA field | VeraGrid target | Notes |
| --- | --- | --- |
| `*_extendable` | Investment existence | only when extension is enabled |
| `*_nom`, `*_nom_opt` | Investment value | target device property depends on component |
| `capital_cost` | Investment `CAPEX` | scaled for parallel circuits when required |
| `discount_rate` | InvestmentsGroup discount rate | p.u. -> percent |
| component type + discount rate | InvestmentsGroup key | avoids mixing economics |

Extendable Generator, StorageUnit, Store, Line, Link and Transformer capacity
creates VeraGrid Investment records. PyPSA discount rates are converted from
per-unit to percent and investment groups are separated by component type and
discount rate, so assets with different economic assumptions are not merged.

Discrete `p_nom_mod`, piecewise investment costs, build-year/lifetime planning,
and full multi-investment-period optimisation remain planning-model work rather
than one-to-one operational imports.

## Global constraints and results

PyPSA global constraints are logged but not imported as native policy objects.
This includes CO2 caps, primary-energy constraints and technology-expansion
limits. Emission rates are retained, but a system-wide cap must currently be
recreated in a VeraGrid planning workflow.

PyPSA solved dispatch, branch flows, dual values and other result tables are
not treated as a native VeraGrid result session. Import the network and rerun
the desired VeraGrid study; use source result tables separately for comparison.

## Migration checklist

1. Open/import the `.nc` and inspect every warning.
2. Check bus count, AC-line count, HVDC count, generators, FluidNodes, Pumps,
   Turbines and FluidPaths against the source component tables.
3. Review every source Link: electrical HVDC, carrier transport, and
   electricity-to-fluid conversions have different native representations.
4. Set physical Store converter ratings where PyPSA supplied no power limit.
5. Recreate global policy constraints and snapshot weighting if they matter.
6. Run a power flow first, then a time-series OPF.
7. Compare bus injections, line loading, storage state trajectories, and total
   generation cost over matching snapshots.
8. Save the reviewed circuit as `.veragrid`; retain the source `.nc` and the
   import log as provenance.

## Conversion limitations

- Exact fixed output ratios for multi-terminal electrical Links are not imposed
  in a fresh VeraGrid OPF;
- lectricity-to-fluid and fluid-to-electric PyPSA Links need explicit P2X or
  Turbine conversion support/review;
- Cyclic end-of-horizon storage state has no automatic native terminal
  constraint yet;
- Global constraints, cumulative generator energy budgets, snapshot objective
  weighting, and full multi-period planning semantics require manual/native
  planning setup;
- A lossy imported FluidPath remains an LP because it preserves PyPSA's
  orientation-defined affine Link equation. A future symmetric physical pipe
  model would require direction logic when its loss is non-zero.

These are not hidden. The importer reports them where it can. Do not “fix” a
warning by deleting source data or setting everything to one; decide what the
physical model is first, then make the native topology say that.
