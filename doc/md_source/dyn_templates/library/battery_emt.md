# Battery EMT

<!-- veragrid-block-introduction:start -->
**Battery EMT** represents an energy resource and its interface controls. Storage and photovoltaic models combine source-side energy or power limits with converter commands, so available active power, DC voltage, and reactive-power control must remain mutually consistent.

## Typical use

- Use it to study renewable or storage response to voltage, frequency, and power-reference disturbances.
- Respect energy, current, DC-voltage, and active/reactive capability limits during initialization.
<!-- veragrid-block-introduction:end -->

Cell or pack-level EMT battery template.

## Behavior

The battery is the DC energy-storage component used by larger BESS assemblies.
It receives terminal current, evolves its stored-energy or state-of-charge
state, and returns the DC terminal voltage available to the converter. Positive
current follows the sign convention implemented by the template, so it should
be checked together with the connected DC-link block.

The model is not a complete grid-connected BESS: synchronization, AC current
control, converter equations, and the AC network interface belong to the BESS
or converter blocks that contain it.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `i_dc` | Battery current request or measured current | A |
| Output | `v_dc` | Battery terminal voltage | V |
| Parameter | `soc0` | Initial state of charge | pu |
| Parameter | `Vnom` | Nominal battery voltage | V |

## Initialization and use

- Set `soc0` inside its valid physical range before applying the model.
- Match `Vnom` and the remaining pack parameters to the converter DC base.
- Use the complete BESS template when a ready-wired battery, DC link, converter,
  PLL, and control system are required.
