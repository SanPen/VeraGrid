# Stabilizer

This model represents the stabilizer block used with the EMT complete generator model.

### Purpose

It is the EMT damping controller that improves the oscillatory behavior of the synchronous generator by modulating the exciter auxiliary input.

### Behavior

- Receives generator speed as its input signal.
- Filters the raw signal through an input transducer.
- Removes the steady-state component through a washout stage.
- Applies gain and lead-lag compensation.
- Limits the final output before sending it to the exciter.

### Characteristics

- EMT stabilizer control block.
- Intended for damping electromechanical oscillations in the composite generator package.
- Not intended to be a standalone network device.

## How it works

The stabilizer reacts mainly to oscillatory speed deviations rather than steady-state offsets. The washout stage blocks the slow component, while the lead-lag stages shape the phase of the response so the resulting signal adds damping instead of amplifying oscillations.

## Characteristic equations

$$
\frac{dy_1}{dt} = \frac{\omega - y_1}{t_6}
$$

$$
\frac{dy_2}{dt} = \frac{y_1 - y_2}{t_5}
$$

$$
y_3 = K_s (y_1 - y_2)
$$

$$
V_{pss} = \mathrm{sat}(y_5, V_{PSS,min}, V_{PSS,max})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `omega` | Generator speed signal fed into the power-system stabilizer | pu |
| Output | `V_pss` | Stabilizing voltage signal sent to the exciter auxiliary input | pu |
| Variable | `y_stabilizer1` | Transducer output state that filters the raw speed deviation signal | pu |
| Variable | `y_stabilizer2` | Washout state that removes the steady-state component from the stabilizer input | pu |
| Variable | `y_stabilizer3` | Gain-stage output after applying the stabilizer gain to the washout channel | pu |
| Variable | `y_stabilizer4` | First lead-lag state used to shape phase compensation | pu |
| Variable | `y_stabilizer5` | Second lead-lag state used to shape phase compensation before output limiting | pu |
| Parameter | `Ks` | Main stabilizer gain applied to the filtered speed-deviation signal | pu/pu |
| Parameter | `VPssMaxPu` | Upper limiter applied to the stabilizer output | pu |
| Parameter | `VPssMinPu` | Lower limiter applied to the stabilizer output | pu |
| Parameter | `SNom` | Nominal power base used by the stabilizer block when mapped from machine data | MVA |
| Parameter | `t1` | Lead time constant of the first lead-lag block | s |
| Parameter | `t2` | Lag time constant of the first lead-lag block | s |
| Parameter | `t3` | Lead time constant of the second lead-lag block | s |
| Parameter | `t4` | Lag time constant of the second lead-lag block | s |
| Parameter | `t5` | Washout time constant | s |
| Parameter | `t6` | Input transducer time constant | s |

## How to use it

- Use it together with the EMT `Complete generator`, `Exciter`, and machine block.
- Tune it only when damping performance is relevant and a reliable generator operating point is already available.
