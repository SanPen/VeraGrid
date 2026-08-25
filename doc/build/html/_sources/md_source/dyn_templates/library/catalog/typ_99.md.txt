# Pade approximant R12 (backward increment)

This is Basic Block Catalog type `99` (`Pade approximant R12 _incbackward`). It represents a continuous-time dynamic operation, including any declared internal states.

<!-- veragrid-block-introduction:start -->
**Pade approximant R12 (backward increment)** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Continuous / Delays and Memory`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 2.
- Configurable parameters: 1.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
\frac{d x1}{dt} = x2
$$

$$
\frac{d x2}{dt} = (\frac{-(Pade approximant R12 _{incbackward\_A0} \cdot x1 + Pade approximant R12 _{incbackward\_A1} \cdot x2)}{Pade approximant R12 _{incbackward\_A2}} + \frac{yi - Pade approximant R12 _{incbackward\_offset}}{Pade approximant R12 _{incbackward\_A2}})
$$

$$
0 = (yo - (Pade approximant R12 _{incbackward\_B0} \cdot x1 + Pade approximant R12 _{incbackward\_B1} \cdot x2 + Pade approximant R12 _{incbackward\_offset}))
$$

$$
Pade approximant R12 _{incbackward\_offset}(t_0) = yo
$$

$$
x1(t_0) = 0
$$

$$
x2(t_0) = 0
$$

$$
Pade approximant R12 _{incbackward\_A0}(t_0) = 1
$$

$$
Pade approximant R12 _{incbackward\_A1}(t_0) = (0.666667(Td \cdot \Theta\left(Td - 0.0001\right) + 0.0001(1 - \Theta\left(Td - 0.0001\right))))
$$

$$
Pade approximant R12 _{incbackward\_A2}(t_0) = (0.166667(Td \cdot \Theta\left(Td - 0.0001\right) + 0.0001(1 - \Theta\left(Td - 0.0001\right))) \cdot (Td \cdot \Theta\left(Td - 0.0001\right) + 0.0001(1 - \Theta\left(Td - 0.0001\right))))
$$

$$
Pade approximant R12 _{incbackward\_B0}(t_0) = 1
$$

$$
Pade approximant R12 _{incbackward\_B1}(t_0) = (-0.333333 \cdot (Td \cdot \Theta\left(Td - 0.0001\right) + 0.0001(1 - \Theta\left(Td - 0.0001\right))))
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| State | `Pade approximant R12 _incbackward__x1` | Internal dynamic state | model-dependent |
| State | `Pade approximant R12 _incbackward__x2` | Internal dynamic state | model-dependent |
| Parameter | `Td` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
