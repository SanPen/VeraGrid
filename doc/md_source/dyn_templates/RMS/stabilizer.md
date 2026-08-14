# Stabilizer

This model represents the RMS stabilizer block used with the complete generator model.

### Purpose

It is the RMS damping controller built by `get_stabilizer_rms()`.

### Behavior

- Receives machine speed as its input signal.
- Applies a transducer stage, washout stage, shaping/notch behavior, and two lead-lag compensation stages.
- Limits the final output.
- Produces the stabilizing signal sent to the exciter block.

### Characteristics

- Explicit-state RMS stabilizer model.
- Designed to improve damping of electromechanical oscillations.
- Works as an auxiliary control channel for the exciter.
## Block structure

```text
omega
  -> transducer
  -> washout
  -> notch / shaping stage
  -> lead-lag 1
  -> lead-lag 2
  -> output limiter
  -> Vpss
```

## Characteristic equations

$$
\frac{dy}{dt} = \frac{\omega - y}{t_6}
$$

$$
\frac{dx_{wash}}{dt} = \frac{y - x_{wash}}{t_5}
$$

$$
y_2 = K_s (y - x_{wash})
$$

$$
y_4 = \frac{t_1}{t_2} y_3 + \left(1 - \frac{t_1}{t_2}\right)x_4
$$

$$
y_5 = \frac{t_3}{t_4} y_4 + \left(1 - \frac{t_3}{t_4}\right)x_5
$$

$$
V_{pss} = \mathrm{sat}(y_5, V_{PSS,min}, V_{PSS,max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `omega_` | Generator speed signal received from the machine block | pu |
| Output | `V_pss` | Stabilizing signal sent to the exciter block | pu |
| Variable | `y_stabilizer1` | Transducer-state variable | pu |
| Variable | `x_stabilizer2` | Washout-state variable | pu |
| Variable | `y_stabilizer2` | Washout-output-related algebraic variable | pu |
| Variable | `y_stabilizer3` | Intermediate shaping-stage variable | pu |
| Variable | `dy_stabilizer3` | Internal derivative/shaping variable used by the notch-like stage | pu/s |
| Variable | `x_stabilizer4` | First lead-lag internal state | pu |
| Variable | `y_stabilizer4` | First lead-lag output variable | pu |
| Variable | `x_stabilizer5` | Second lead-lag internal state | pu |
| Variable | `y_stabilizer5` | Second lead-lag output variable before limiting | pu |
| Parameter | `Ks` | Stabilizer gain | pu/pu |
| Parameter | `VPssMaxPu` | Upper output limit of the stabilizer | pu |
| Parameter | `VPssMinPu` | Lower output limit of the stabilizer | pu |
| Parameter | `SNom` | Nominal apparent-power scaling parameter retained by the template | pu |
| Parameter | `A1` | Shaping/notch coefficient 1 | pu |
| Parameter | `A2` | Shaping/notch coefficient 2 | pu |
| Parameter | `t1` | Lead time constant of the first compensator | s |
| Parameter | `t2` | Lag time constant of the first compensator | s |
| Parameter | `t3` | Lead time constant of the second compensator | s |
| Parameter | `t4` | Lag time constant of the second compensator | s |
| Parameter | `t5` | Washout time constant | s |
| Parameter | `t6` | Transducer time constant | s |

## How to use it

- Treat this as the damping controller of the RMS `Complete generator` package.
- It is useful only together with the machine and exciter blocks.
