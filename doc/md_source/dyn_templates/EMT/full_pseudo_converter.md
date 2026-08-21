# Full pseudo converter

<!-- veragrid-block-introduction:start -->
**Full pseudo converter** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

This model represents a controlled EMT converter with detailed modulation and switching-function behavior short of device-level switching.

## Model structure

The full pseudo converter is a hierarchical, averaged three-wire ABC model. It includes terminal measurements, a PLL, outer reference control, dq current control, modulation limits, an equivalent series filter, and an AC/DC power interface. It retains converter and controller dynamics without generating discrete PWM pulses.

This level of detail is useful when converter controls must interact with phase-domain network transients but switching harmonics are outside the study scope.

## Characteristic behavior

The measured ABC quantities are transformed into the PLL-aligned dq0 frame. The equivalent filter-current states follow representative equations of the form

$$
\frac{d i_d}{dt}=\frac{\omega_{base}}{L_{eq}}
\left(v_d-v_{cmd,d}-R_{eq}i_d+\omega_rL_{eq}i_q\right),
$$

$$
\frac{d i_q}{dt}=\frac{\omega_{base}}{L_{eq}}
\left(v_q-v_{cmd,q}-R_{eq}i_q-\omega_rL_{eq}i_d\right).
$$

The outer controller converts active/reactive-power or DC-voltage error into current references. The inner controller converts current error into dq voltage commands, with current, modulation, and anti-windup limits. The dq currents are transformed back to ABC current injections. `Idc` is obtained from the AC/DC power balance and configured losses.

## Averaged-model boundary

The voltage command is continuous: there is no carrier, gate pulse, or semiconductor switching transition. The model therefore captures controller bandwidth, filter dynamics, saturation, unbalance at the AC terminals, and DC-side interaction, but not PWM ripple, switching-frequency resonance, dead time, or device stress. Use the Switched converter when those effects are required.

## Initialization and numerical behavior

The solved AC power flow and DC voltage establish the initial dq currents, PLL angle, controller integrators, and modulation command. `R_eq`, `L_eq`, ratings, references, and voltage bases must describe the same interface. Confirm that the initial current and voltage command are below their limits; an initially saturated controller often indicates inconsistent data rather than a meaningful transient.

The required time step is normally governed by the filter and fastest controller state, not by a PWM carrier. A time-step convergence check is still required for fast control or weak-grid studies.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A AC terminal voltage applied to the converter interface | pu |
| Input | `v_B` | Instantaneous phase-B AC terminal voltage applied to the converter interface | pu |
| Input | `v_C` | Instantaneous phase-C AC terminal voltage applied to the converter interface | pu |
| Input | `Vdc` | DC terminal voltage seen by the converter electrical block | pu |
| Output | `i_A` | Phase-A current injected by the converter into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the converter into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the converter into the EMT network | pu |
| Output | `Idc` | DC current drawn from or supplied to the DC terminal by the converter | pu |
| Variable | `vdc` | Internal DC-link voltage state used by the electrical converter block | pu |
| Variable | `P` | Instantaneous active power measured at the AC side of the converter | pu |
| Variable | `Q` | Instantaneous reactive power measured at the AC side of the converter | pu |
| Variable | `phi_v` | Instantaneous voltage angle estimated at the converter AC terminal | rad |
| Variable | `Vpk` | Instantaneous peak AC voltage magnitude estimated at the converter AC terminal | pu |
| Variable | `theta_pll` | Internal phase angle produced by the converter PLL | rad |
| Variable | `omega_pll` | Internal electrical frequency estimated by the converter PLL | pu |
| Variable | `xi_pll` | Integral state of the PLL frequency loop | pu |
| Variable | `i_d_ref` | d-axis current reference produced by the outer control loop | pu |
| Variable | `i_q_ref` | q-axis current reference produced by the outer control loop | pu |
| Variable | `v_cmd_d` | d-axis voltage command produced by the inner current loop | pu |
| Variable | `v_cmd_q` | q-axis voltage command produced by the inner current loop | pu |
| Variable | `i_d` | d-axis converter current inside the dq0 control frame | pu |
| Variable | `i_q` | q-axis converter current inside the dq0 control frame | pu |
| Variable | `v_d` | d-axis converter terminal voltage inside the dq0 control frame | pu |
| Variable | `v_q` | q-axis converter terminal voltage inside the dq0 control frame | pu |
| Parameter | `C_dc` | DC-link capacitance used by the internal electrical block | pu s |
| Parameter | `omega_base` | Base electrical angular frequency used across the imported control blocks | rad/s |
| Parameter | `k_p_pll` | Proportional gain of the PLL controller | pu/pu |
| Parameter | `k_i_pll` | Integral gain of the PLL controller | pu/(pu s) |
| Parameter | `R_eq` | Equivalent series resistance used in the current-control decoupling equations | pu |
| Parameter | `L_eq` | Equivalent series inductance used in the current-control decoupling equations | pu |

## How to use it

1. Connect the ABC and DC ports and solve the initial operating point.
2. Map ratings, AC filter data, DC-link data, references, limits, and all controller gains.
3. Check PLL alignment, dq current signs, and the AC/DC power balance at initialization.
4. Apply small reference or voltage steps before severe faults to verify control polarity and saturation behavior.
5. Select this model for control interaction studies; select the switched model only when waveform-level switching detail justifies its smaller time step.
