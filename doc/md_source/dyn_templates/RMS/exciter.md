# Exciter

This model represents the RMS excitation control block used with the complete generator model.

### Purpose

It is the RMS excitation control block built by `get_exciter_rms()`.

### Behavior

- Receives machine exciter-feedback quantity, measured terminal voltage, and stabilizer signal.
- Filters the measured voltage.
- Forms a regulated voltage error signal.
- Applies lead-lag AVR action, limits, nonlinear field feedback, and field-stage dynamics.
- Produces the field-voltage signal sent to the machine block.

### Characteristics

- Explicit-state RMS exciter model.
- Includes AVR dynamics, rate feedback, limiters, and nonlinear field feedback.
- Acts as the voltage-control channel of the composite generator.
## Block structure

```text
Vm measurement
  -> voltage filter
  -> error with reference and PSS input
  -> lead-lag AVR path
  -> limiter / saturation
  -> exciter field stage
  -> Vf
```

## Characteristic equations

$$
e_1 = (-y_1 + U_{s,ref}) + V_{pss}
$$

$$
e_2 = e_1 - y_2
$$

$$
\frac{dy_1}{dt} = \frac{V_m - y_1}{t_R}
$$

$$
\frac{dx_2}{dt} = \frac{V_f - x_2}{t_F}
$$

$$
\frac{dx_3}{dt} = \frac{e_2 - x_3}{t_B}
$$

$$
\frac{dy_4}{dt} = \frac{K_a y_3 - y_6}{t_A}
$$

$$
\frac{dV_e}{dt} = \frac{E_{fe} - (I_{RPu}K_d + u_{aux})}{t_E}
$$

$$
V_f = f_{out} V_e
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `IRPu` | Feedback quantity received from the machine block | pu |
| Input | `Vm` | Terminal voltage magnitude measured at the generator bus | pu |
| Input | `Vpss` | Stabilizer signal received from the stabilizer block | pu |
| Output | `Vf` | Field-voltage signal sent to the machine block | pu |
| Variable | `Efe` | Internal exciter field-voltage-related variable | pu |
| Variable | `UsRefPu` | Voltage reference used by the AVR | pu |
| Variable | `VeMaxPu` | Dynamic ceiling variable for one internal limiter stage | pu |
| Variable | `u_aux` | Auxiliary nonlinear field-feedback variable | pu |
| Variable | `AEz` | Saturation shaping variable/parameter channel retained in the block | pu |
| Variable | `BEz` | Saturation shaping variable/parameter channel retained in the block | pu |
| Variable | `EfeMaxPu` | Upper field-voltage limit variable | pu |
| Variable | `EfeMinPu` | Lower field-voltage limit variable | pu |
| Variable | `TolLi` | Limiter tolerance variable | pu |
| Variable | `VaMaxPu` | Upper AVR output limit | pu |
| Variable | `VaMinPu` | Lower AVR output limit | pu |
| Variable | `VeMinPu` | Lower exciter-stage limit | pu |
| Variable | `VfeMaxPu` | Upper field-current/field-output limit variable | pu |
| Variable | `AEx` | Exponential saturation coefficient | pu |
| Variable | `BEx` | Exponential saturation exponent coefficient | 1/pu |
| Variable | `Se_threshold` | Threshold at which the exponential saturation becomes active | pu |
| Variable | `ToLLi` | Additional limiter-tolerance variable retained by the template | pu |
| Variable | `VeMinPu_submodel` | Submodel lower limit for the field stage | pu |
| Variable | `VfeMaxPu_submodel` | Submodel upper limit for the field stage | pu |
| Variable | `y_exciter1` | Voltage-filter state | pu |
| Variable | `x_exciter2` | Rate-feedback state | pu |
| Variable | `y_exciter2` | Rate-feedback output variable | pu |
| Variable | `x_exciter3` | Lead-lag state | pu |
| Variable | `y_exciter3` | Lead-lag output variable | pu |
| Variable | `y_exciter4` | AVR-stage state | pu |
| Variable | `y_exciter4_sat` | Saturated AVR output variable | pu |
| Variable | `y_subexciter1` | Field-stage state variable | pu |
| Variable | `f_input` | Input variable of the nonlinear exciter-output shaping function | pu |
| Variable | `f_output` | Output of the nonlinear exciter-output shaping function | pu |
| Parameter | `Ka` | AVR gain | pu/pu |
| Parameter | `Kf` | Rate-feedback gain | pu/pu |
| Parameter | `tA` | AVR stage time constant | s |
| Parameter | `tB` | Lead-lag lag time constant | s |
| Parameter | `tC` | Lead-lag lead time constant | s |
| Parameter | `tE` | Exciter field-stage time constant | s |
| Parameter | `tF` | Rate-feedback time constant | s |
| Parameter | `tR` | Voltage measurement filter time constant | s |
| Parameter | `Kc` | Rectifier/loading factor used in the output shaping relation | pu |
| Parameter | `Kd` | Demagnetizing factor used in field feedback | pu |
| Parameter | `Ke` | Field resistance or field-feedback coefficient | pu |
| Parameter | `Kfd` | Field conversion factor | pu |

## How to use it

- Treat this as the voltage-control block of the RMS `Complete generator` package.
- It is not intended to inject directly into the network by itself.
