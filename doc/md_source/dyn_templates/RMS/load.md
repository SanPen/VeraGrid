# Load

This model represents a positive-sequence RMS constant-power load.

### Purpose

It is the simplest RMS load template in the dynamic library. Its job is to consume fixed active and reactive power from the network without adding internal dynamics, voltage sensitivity, or frequency sensitivity.

### Behavior

- Uses bus voltage magnitude and angle as network-facing inputs.
- Exposes active and reactive power demand as outputs consumed by the surrounding RMS network equations.
- Keeps the active and reactive demand equal to internal setpoint values in the present implementation.
- Uses the terminal-voltage inputs for coupling with the rest of the network and for a consistent template interface, even though those inputs do not presently modulate the demanded power.

### Characteristics

- Algebraic-only RMS load model.
- Positive-sequence representation.
- Appropriate for constant-PQ load behavior in electromechanical simulations.
- Not intended for motor starting, recovery dynamics, voltage-dependent demand, or frequency-dependent demand.

## How it works

The block stores one active-power demand and one reactive-power demand. At every RMS time step, those values are exported directly to the network as the load power injection channels. No internal state evolves with time, so the model reacts instantaneously.

## Characteristic equations

$$
P_l = P_{l0}
$$

$$
Q_l = Q_{l0}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the load bus | pu |
| Input | `Va` | Terminal voltage angle at the load bus | rad |
| Output | `Pl` | Active power consumed by the load | pu |
| Output | `Ql` | Reactive power consumed by the load | pu |
| Variable | `Pl0` | Internal active-power setpoint copied directly into the active-power output equation | pu |
| Variable | `Ql0` | Internal reactive-power setpoint copied directly into the reactive-power output equation | pu |
| Variable | `Pl` | Algebraic active-power variable exported to the network model | pu |
| Variable | `Ql` | Algebraic reactive-power variable exported to the network model | pu |
| Parameter | none | This template does not use a separate fixed parameter block beyond its internal runtime variables | - |

## How to use it

- Use this template when you need one simple constant-PQ demand in RMS studies.
- Use a richer load model instead when the load must vary with voltage, frequency, motor slip, tap action, or recovery logic.
