# Ideal converter

<!-- veragrid-block-introduction:start -->
**Ideal converter** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

This model represents an averaged EMT converter with abc current injection and DC power balance.

### Purpose

It is an averaged EMT converter with abc current injection and DC power balance.

### Behavior

- Uses three-phase AC bus voltages and DC bus voltage as inputs.
- Synthesizes phase currents from active and reactive power commands.
- Computes DC current from the active-power balance.
- Does not represent switching, PLL dynamics, filter dynamics, detailed inner current loops, or transformer detail.

### Characteristics

- Simple and computationally light EMT converter.
- Better suited to control-oriented EMT studies than hardware-detail studies.
- Good starting point when switching detail is unnecessary.
## Characteristic equations

Representative equations are:

$$
P_{dc,cmd} = P_{ref} + 2(v_{dc} - V_{dc,ref})\,\mathrm{regulate}_{vdc}
$$

$$
Q_{cmd} = Q_{ref}\,\mathrm{regulate}_q
$$

$$
i_{d,cmd} = \frac{2}{3}\frac{Q_{cmd,pu}}{V_{pk}}
$$

$$
i_{q,cmd} = \frac{2}{3}\frac{P_{ac,cmd,pu}}{V_{pk}}
$$

$$
i_A = i_{d,cmd}\cos\theta + i_{q,cmd}\sin\theta
$$

$$
v_{dc} i_{dc} + P_{dc,cmd,pu} = 0
$$

$$
P = v_A i_A + v_B i_B + v_C i_C
$$

$$
Q = \frac{1}{\sqrt{3}}\left((v_A-v_B)i_C + (v_B-v_C)i_A + (v_C-v_A)i_B\right)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A AC terminal voltage | pu |
| Input | `v_B` | Instantaneous phase-B AC terminal voltage | pu |
| Input | `v_C` | Instantaneous phase-C AC terminal voltage | pu |
| Input | `v_dc` | DC bus voltage applied to the converter model | pu |
| Output | `i_A` | Injected phase-A current sent to the AC network | pu |
| Output | `i_B` | Injected phase-B current sent to the AC network | pu |
| Output | `i_C` | Injected phase-C current sent to the AC network | pu |
| Output | `i_dc` | DC current implied by the converter active-power balance | pu |
| Variable | `theta` | Internal synchronous angle used to synthesize abc current references | rad |
| Variable | `P_ref` | Active-power reference used by the averaged converter logic | system-base power |
| Variable | `Q_ref` | Reactive-power reference used by the averaged converter logic | system-base power |
| Variable | `Vdc_ref` | DC-voltage reference used when DC-voltage regulation is active | pu |
| Variable | `i_A` | Algebraic phase-A output current variable | pu |
| Variable | `i_B` | Algebraic phase-B output current variable | pu |
| Variable | `i_C` | Algebraic phase-C output current variable | pu |
| Variable | `i_dc` | Algebraic DC current variable | pu |
| Variable | `P` | Measured instantaneous active power at the AC interface | pu or system-base power |
| Variable | `Q` | Measured instantaneous reactive power at the AC interface | pu or system-base power |
| Parameter | `P_loss` | Converter loss term added on top of transferred active power | system-base power |
| Parameter | `P0` | Scheduled base active-power seed used by the control-reference resolver | system-base power |
| Parameter | `omega_base` | Base angular frequency used to evolve the internal synchronous angle | rad/s |
| Parameter | `sbase` | System base power used to normalize power commands | MVA or system-base power |
| Parameter | `control1` | First control mode selector | code |
| Parameter | `control2` | Second control mode selector | code |
| Parameter | `control1_val` | Target value associated with the first control mode | mode-dependent |
| Parameter | `control2_val` | Target value associated with the second control mode | mode-dependent |
| Parameter | `phi_v` | Initial AC voltage angle reference coming from the PF/EMT bridge | rad |
| Parameter | `Vpk` | Initial AC peak voltage magnitude used for current synthesis and initialization | pu |
| Parameter | `Vdc_nom` | Nominal DC voltage used by the control-reference resolver | pu |

## How to use it

- Use it for simple EMT converter studies where only averaged current injection is required.
- Do not use it when switching harmonics or detailed converter hardware effects matter.
