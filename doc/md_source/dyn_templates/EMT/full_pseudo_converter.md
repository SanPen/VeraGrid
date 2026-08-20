# Full pseudo converter

<!-- veragrid-block-introduction:start -->
**Full pseudo converter** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

This model represents a controlled EMT converter with detailed modulation and switching-function behavior short of device-level switching.

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
