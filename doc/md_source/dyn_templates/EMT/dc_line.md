# DC line

This model represents a DC line with distributed electrical parameters for EMT studies.

### Purpose

It is the EMT DC branch used to transfer current and power between two DC nodes while preserving electrical dynamics such as current ramping through line inductance.

### Behavior

- Uses from-side and to-side DC terminal voltages as inputs.
- Computes the line current flowing between the two terminals.
- Injects equal and opposite currents into the DC nodes.
- May also expose one power-command channel in variants where the line is embedded inside a higher-level controlled DC transfer setup.

### Characteristics

- EMT DC branch model.
- Suitable for converter-to-converter DC interconnections.
- Can represent both resistive loss and current-dynamic effects.

## How it works

The line current evolves according to the voltage difference across the branch and the series electrical parameters. Resistance dissipates power while inductance prevents instantaneous current changes. The current computed inside the branch is then exported as current injections at the two DC terminals.

## Characteristic equations

$$
L_{dc}\frac{di_{line}}{dt} = v_{f,dc} - v_{t,dc} - R_{dc} i_{line}
$$

$$
i_{f,dc} = -i_{line}, \qquad i_{t,dc} = i_{line}
$$

$$
p_{line} = (v_{f,dc} - v_{t,dc}) i_{line}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_f_dc` | From-side DC terminal voltage applied to the line model | pu |
| Input | `v_t_dc` | To-side DC terminal voltage applied to the line model | pu |
| Input | `p_cmd` | Power-transfer command used by the power-input DC line variant selected by the catalogue | pu |
| Output | `i_f_dc` | Current injected by the line into the from-side DC node | pu |
| Output | `i_t_dc` | Current injected by the line into the to-side DC node | pu |
| Variable | `i_line` | Internal branch current carried by the DC line between the two terminals | pu |
| Variable | `p_line` | Instantaneous power transferred through the DC line model | pu |
| Parameter | `R_dc` | Series resistance of the DC line branch | pu |
| Parameter | `L_dc` | Series inductance of the DC line branch when dynamic current evolution is enabled | pu |

## How to use it

- Use it for EMT studies of DC links, DC feeders, or converter-to-converter DC interconnections.
- Use a simpler algebraic connection only when DC current dynamics are not important.
