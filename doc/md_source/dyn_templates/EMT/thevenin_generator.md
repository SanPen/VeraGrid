# Thevenin generator

This model represents a Thevenin-equivalent generator source for EMT studies.

### Purpose

It is a three-phase Thevenin-equivalent EMT generator with RL current dynamics and an internally reconstructed balanced emf.

### Behavior

- Uses three-phase terminal voltages as inputs.
- Evolves three phase-current states and one electrical-angle state.
- Reconstructs the internal balanced emf from power-flow-derived initialization quantities.
- Injects abc currents into the EMT network according to a source-behind-impedance structure.

### Characteristics

- Compact EMT source model.
- Useful when a full synchronous machine and controls are not required.
- Supports higher-level shared-reference wiring without changing the local source equations.
## Characteristic equations

$$
\frac{di_A}{dt} = \omega_{base}\frac{e_A - R_s i_A - v_A}{X_s}
$$

$$
\frac{di_B}{dt} = \omega_{base}\frac{e_B - R_s i_B - v_B}{X_s}
$$

$$
\frac{di_C}{dt} = \omega_{base}\frac{e_C - R_s i_C - v_C}{X_s}
$$

$$
\frac{d\theta}{dt} = \omega_{base} f_{scale}
$$

$$
e_A = E_{scale} E_{pk} \sin(\theta + \theta_{dev})
$$

Equivalent `±2π/3` phase shifts are used for `e_B` and `e_C`.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A terminal voltage | pu |
| Input | `v_B` | Instantaneous phase-B terminal voltage | pu |
| Input | `v_C` | Instantaneous phase-C terminal voltage | pu |
| Output | `i_A` | Phase-A current injected into the EMT network | pu |
| Output | `i_B` | Phase-B current injected into the EMT network | pu |
| Output | `i_C` | Phase-C current injected into the EMT network | pu |
| Variable | `i_A` | Phase-A current state variable | pu |
| Variable | `i_B` | Phase-B current state variable | pu |
| Variable | `i_C` | Phase-C current state variable | pu |
| Variable | `theta` | Internal electrical angle of the balanced source | rad |
| Variable | `e_A` | Internal phase-A emf | pu |
| Variable | `e_B` | Internal phase-B emf | pu |
| Variable | `e_C` | Internal phase-C emf | pu |
| Variable | `Pe` | Instantaneous electrical active power measured at the source terminals | pu |
| Variable | `Qe` | Instantaneous electrical reactive power measured at the source terminals | pu |
| Parameter | `omega_base` | Base electrical angular frequency | rad/s |
| Parameter | `R_s` | Source resistance | pu |
| Parameter | `X_s` | Source reactance | pu |
| Parameter | `phi_v` | Power-flow-derived terminal voltage angle used for initialization | rad |
| Parameter | `phi` | Power-flow-derived current-to-voltage phase relation used for initialization | rad |
| Parameter | `Vpk` | Power-flow-derived peak phase-voltage magnitude used for initialization | pu |
| Parameter | `Ipk` | Power-flow-derived peak phase-current magnitude used for initialization | pu |
| Parameter | `theta_deviation_param` | Runtime angle-deviation offset applied to the internal emf | rad |
| Parameter | `f_scale` | Runtime frequency scaling applied to the angle state equation | pu |
| Parameter | `E_scale` | Runtime emf-magnitude scaling factor | pu |
| Parameter | `share_enable` | Higher-level flag used by orchestration logic for shared-reference behavior | 0/1 |
| Parameter | `P_share_ref` | Higher-level active-power sharing reference | pu |
| Parameter | `Q_share_ref` | Higher-level reactive-power sharing reference | pu |

## How to use it

- Use this template when you want a compact EMT source behind impedance.
- Use the EMT `Complete generator` instead when you need explicit machine, exciter, governor, and stabilizer dynamics.
