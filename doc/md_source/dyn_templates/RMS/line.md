# Line

This model represents a positive-sequence RMS transmission line branch.

### Purpose

It is a positive-sequence AC line model that computes sending-end and receiving-end active and reactive power from terminal voltage magnitudes and angles.

### Behavior

- Uses from-side and to-side terminal voltage magnitudes and angles as inputs.
- Computes active and reactive power at both ends of the line.
- Includes series conductance, series susceptance, and shunt susceptance.
- Uses the event variable `u` to enable or disable the branch contribution.

### Characteristics

- Algebraic-only RMS branch model.
- Intended for positive-sequence branch power-flow behavior inside RMS dynamic simulations.
- Appropriate for electromechanical timescale studies.
- Does not model phase-domain wave propagation or electromagnetic line detail.

## How it works

The template evaluates the standard positive-sequence branch power expressions using the terminal voltages at both ends of the line and the branch admittance parameters. When `u = 0`, the line contribution is suppressed; when `u = 1`, the full branch equations are applied.

## Characteristic equations

$$
P_f = V_{mf}^2 g - g V_{mf} V_{mt} \cos(\theta_f - \theta_t) + b V_{mf} V_{mt} \cos\left(\theta_f - \theta_t + \frac{\pi}{2}\right)
$$

$$
Q_f = V_{mf}^2\left(-\frac{b_{sh}}{2} - b\right) - g V_{mf} V_{mt} \sin(\theta_f - \theta_t) + b V_{mf} V_{mt} \sin\left(\theta_f - \theta_t + \frac{\pi}{2}\right)
$$

Equivalent expressions are used for `P_t` and `Q_t` at the receiving end.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vmf` | From-side voltage magnitude | pu |
| Input | `Vaf` | From-side voltage angle | rad |
| Input | `Vmt` | To-side voltage magnitude | pu |
| Input | `Vat` | To-side voltage angle | rad |
| Output | `Pf` | Active power flowing from the from-side terminal into the line model | pu |
| Output | `Pt` | Active power flowing from the to-side terminal into the line model | pu |
| Output | `Qf` | Reactive power flowing from the from-side terminal into the line model | pu |
| Output | `Qt` | Reactive power flowing from the to-side terminal into the line model | pu |
| Variable | `Pf` | Algebraic from-side active-power variable | pu |
| Variable | `Pt` | Algebraic to-side active-power variable | pu |
| Variable | `Qf` | Algebraic from-side reactive-power variable | pu |
| Variable | `Qt` | Algebraic to-side reactive-power variable | pu |
| Variable | `u` | Branch enable multiplier used to switch the model contribution on or off | 0/1 |
| Parameter | `g` | Series conductance of the positive-sequence line model | pu |
| Parameter | `b` | Series susceptance of the positive-sequence line model | pu |
| Parameter | `bsh` | Total shunt susceptance term used by the line model | pu |

## How to use it

- Use this template when branch active and reactive powers are the quantities of interest in RMS simulations.
- Do not use it when EMT traveling-wave behavior, switching transients, or unbalanced phase-domain line behavior is needed.
