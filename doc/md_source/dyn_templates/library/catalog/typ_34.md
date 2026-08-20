# abs(in) less than C (pulse)

This is Basic Block Catalog type `34` (`abs(in) less than C _ip`). It generates or evaluates a time-dependent waveform.

<!-- veragrid-block-introduction:start -->
**abs(in) less than C (pulse)** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

## Behaviour

- Library location: `Native / Waveforms and Time / Signal Generators`.
- Inputs: 1.
- Outputs: 1.
- Declared states: 0.
- Configurable parameters: 3.
- The imported definition is fully supported by the Dynamic Editor catalogue.

## Characteristic equations

$$
0 = (yo - proc_{picdro\_0})
$$

$$
yo(t_0) = (proc_{selfix\_1} \cdot 1 + (1 - proc_{selfix\_1}) \cdot 0)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal consumed by the block | model-dependent |
| Output | `yo` | Output signal produced by the block | model-dependent |
| Parameter | `C` | Configurable model parameter | model-dependent |
| Parameter | `Tpick` | Configurable model parameter | model-dependent |
| Parameter | `Tdrop` | Configurable model parameter | model-dependent |

## Editing notes

Use General options for numeric parameter values and the DAE tab for symbolic variables and equations. Changing an Output flag only controls whether a variable is exported; it does not remove the variable from the model.
