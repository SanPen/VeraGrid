# pi

### Purpose

This reusable library template inserts one EMT pi-line block.

### Behavior

- Uses from-side and to-side terminal voltages.
- Produces branch-port currents.
- Represents line dynamics through one pi-equivalent formulation.

### Characteristics

- Runtime template exposed through the dynamic editor `Templates` branch.
- EMT branch model.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `vf_*` | From-side active terminal voltages for the active conductors | pu |
| Input | `vt_*` | To-side active terminal voltages for the active conductors | pu |
| Output | `if_*` | From-side branch-port currents for the active conductors | pu |
| Output | `it_*` | To-side branch-port currents for the active conductors | pu |
| Variable | `i_ser_*` | Series-current states for active conductors | pu |
| Parameter | `R*` | Resistance matrix entries | pu |
| Parameter | `Linv_*` | Inverse-inductance matrix entries | 1/(pu·s) |
| Parameter | `C*` | Shunt-capacitance matrix entries | pu·s |

## How to use it

- Use this template when one reusable EMT pi-line template is needed directly from the library.
