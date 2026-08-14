# Exciter

This model represents the EMT excitation control block used with the complete generator model.

### Purpose

It is the EMT excitation controller built by `get_exciter_emt()`.

### Behavior

- Receives machine exciter-feedback quantity, three-phase terminal voltages, and stabilizer signal.
- Builds a voltage-magnitude measurement from the three phase voltages.
- Filters the measurement and forms a regulated voltage error.
- Applies lead-lag AVR action, limit logic, and field-stage dynamics.
- Produces the field-voltage signal sent to the machine block.

### Characteristics

- EMT excitation control block.
- Includes voltage filtering, AVR dynamics, limiter logic, and nonlinear field feedback.
## Block structure

```text
abc voltage measurement
  -> voltage magnitude Vm
  -> voltage filter
  -> reference / PSS error
  -> lead-lag AVR
  -> limiter and field feedback
  -> field stage
  -> Vf
```

## Characteristic equations

$$
V_m = \sqrt{\frac{v_A^2 + v_B^2 + v_C^2}{3}}
$$

$$
e_{exc} = U_{s,ref} + V_{pss} - y_1 - y_2
$$

$$
y_{LL} = y_3 + \frac{t_C}{t_B}(e_{exc} - y_3)
$$

$$
\frac{dy_1}{dt} = \frac{V_m - y_1}{t_R}
$$

$$
\frac{dy_2}{dt} = \frac{K_f V_f - y_2}{t_F}
$$

$$
\frac{dy_3}{dt} = \frac{e_{exc} - y_3}{t_B}
$$

$$
\frac{dy_4}{dt} = \frac{K_a y_{LL} - y_4}{t_A}
$$

$$
\frac{dV_f}{dt} = \frac{V_{field,ref} - V_{field,fb}}{t_E}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `IRPu` | Exciter-feedback quantity received from the machine block | pu |
| Input | `v_A` | Phase-A terminal voltage used by the exciter voltage-magnitude measurement | pu |
| Input | `v_B` | Phase-B terminal voltage used by the exciter voltage-magnitude measurement | pu |
| Input | `v_C` | Phase-C terminal voltage used by the exciter voltage-magnitude measurement | pu |
| Input | `V_pss` | Stabilizer signal received from the stabilizer block | pu |
| Output | `Vf` | Field-voltage signal sent to the machine block | pu |
| Variable | `Vm` | Measured voltage magnitude used by the AVR | pu |
| Variable | `Efe` | Internal exciter-field variable after limiter action | pu |
| Variable | `UsRefPu` | Voltage reference used by the AVR loop | pu |
| Variable | `y_exciter1` | Voltage-measurement filter state | pu |
| Variable | `y_exciter2` | Rate-feedback state/output variable | pu |
| Variable | `y_exciter3` | Lead-lag internal state | pu |
| Variable | `y_exciter4` | AVR internal state | pu |
| Variable | `VeMaxPu` | Dynamic ceiling variable used by one limiter stage | pu |
| Variable | `u_aux` | Auxiliary nonlinear field-feedback variable | pu |
| Parameter | `Ka` | AVR gain | pu/pu |
| Parameter | `Kf` | Rate-feedback gain | pu/pu |
| Parameter | `tA` | AVR stage time constant | s |
| Parameter | `tB` | Lead-lag lag time constant | s |
| Parameter | `tC` | Lead-lag lead time constant | s |
| Parameter | `tE` | Field-stage time constant | s |
| Parameter | `tF` | Rate-feedback time constant | s |
| Parameter | `tR` | Voltage measurement filter time constant | s |
| Parameter | `Kd` | Demagnetizing/field-feedback factor | pu |
| Parameter | `Ke` | Field-feedback coefficient | pu |
| Parameter | `Kfd` | Field conversion factor | pu |
| Parameter | `AEz` | Saturation-law shaping coefficient | pu |
| Parameter | `BEz` | Saturation-law exponential coefficient | 1/pu |
| Parameter | `AEx` | Exponential field-feedback coefficient | pu |
| Parameter | `BEx` | Exponential field-feedback exponent coefficient | 1/pu |
| Parameter | `Se_threshold` | Threshold at which the nonlinear field saturation becomes active | pu |
| Parameter | `VaMaxPu` | Upper AVR output limit | pu |
| Parameter | `VaMinPu` | Lower AVR output limit | pu |
| Parameter | `VfeMaxPu` | Upper field-output related limit | pu |
| Parameter | `EfeMaxPu` | Upper internal exciter-field limit | pu |
| Parameter | `EfeMinPu` | Lower internal exciter-field limit | pu |

## How to use it

- Treat this as the field-voltage control block of the EMT `Complete generator` package.
- It is not a standalone source or sink for the network.
