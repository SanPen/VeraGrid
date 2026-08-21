# Switched converter

<!-- veragrid-block-introduction:start -->
**Switched converter** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

This model represents an EMT switched converter with explicit switching behavior.

## Model structure

The template is a hierarchical three-wire ABC converter. It combines:

- an AC electrical plant and series filter;
- an angle and frequency estimator (PLL);
- outer active/reactive or DC-voltage control;
- inner dq current control and modulation limiting;
- a PWM carrier and two-level bridge representation; and
- an AC/DC power balance that produces the DC-side current.

The external interface is deliberately small, while the child blocks retain the electrical, measurement, and controller states needed to inspect the response.

## Startup and procedural handover

The model starts with an averaged bridge so that the initialized operating point is not immediately disturbed by an arbitrary carrier state. At `t_enable_sw`, the `startup_handover` procedural event changes `switching_enabled_mode` from 0 to 1. The effective switching frequency is

$$
\omega_{sw,eff}=m_{sw}\omega_{sw},
$$

where $m_{sw}$ is the mode flag. Before handover, the converter voltage follows the continuous modulation reference. Afterwards, the phase bridge voltages follow the discrete PWM gate states. The mode is retained after the event; it is not an ordinary continuously solved parameter.

## Electrical and control behavior

Terminal voltages and currents are transformed to the PLL-aligned dq0 frame. The outer loop produces current references, the inner loop produces limited voltage commands, and the phase modulator compares the normalized references with the carrier. The series filter retains its current dynamics, while measured $P$ and $Q$ close the control loops. DC current follows the converter power balance, including the configured loss term.

The explicit bridge introduces switching harmonics and discontinuous voltage steps that an averaged converter cannot reproduce. It does not represent semiconductor junction physics, dead time, device temperature, or detailed commutation losses.

## Initialization and time-step selection

Initialization uses the solved AC voltage, active and reactive power, DC voltage, and controller references to establish compatible currents, integrator states, and modulation commands. Check that the initialized converter is inside its current and modulation limits before enabling switching.

The EMT step must resolve the carrier and filter dynamics. As a practical check, use many integration steps per switching period and repeat the study with a smaller step; important RMS values and waveform features should not materially change. Ensure `t_enable_sw` lies on or is represented accurately by the simulation time grid.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A AC terminal voltage applied to the converter plant | pu |
| Input | `v_B` | Instantaneous phase-B AC terminal voltage applied to the converter plant | pu |
| Input | `v_C` | Instantaneous phase-C AC terminal voltage applied to the converter plant | pu |
| Input | `Vdc` | DC terminal voltage applied to the switched converter bridge | pu |
| Output | `i_A` | Phase-A current injected by the converter into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the converter into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the converter into the EMT network | pu |
| Output | `Idc` | DC current drawn from or supplied to the DC terminal by the converter | pu |
| Variable | `switching_enabled_mode` | Internal mode flag that is `0` before handover and `1` after explicit switching is enabled | 0/1 |
| Variable | `P` | Instantaneous active power measured at the converter AC interface | pu |
| Variable | `Q` | Instantaneous reactive power measured at the converter AC interface | pu |
| Variable | `theta_pll` | Internal PLL phase angle used by the converter controls | rad |
| Variable | `omega_pll` | Internal PLL frequency estimate used by the converter controls | pu |
| Variable | `m_a` | Modulation or gate-equivalent command for converter phase A | pu |
| Variable | `m_b` | Modulation or gate-equivalent command for converter phase B | pu |
| Variable | `m_c` | Modulation or gate-equivalent command for converter phase C | pu |
| Parameter | `t_enable_sw` | Simulation time at which the model changes from averaged startup mode to switched mode | s |
| Parameter | `omega_sw_eff` | Effective switching angular frequency used after applying the startup handover logic | rad/s |
| Parameter | `omega_sw` | Nominal switching angular frequency of the PWM carrier | rad/s |
| Parameter | `carrier_phase` | Initial phase offset of the PWM carrier | rad |

## How to use it

1. Connect the ABC and DC terminals and initialize the network operating point.
2. Map the converter ratings, filter data, controller gains, limits, references, and switching frequency.
3. Choose `t_enable_sw` late enough for a clean initialized start but before the event window being studied.
4. Inspect current and modulation saturation as well as $P$, $Q$, `Vdc`, and `Idc`.
5. Validate the time step by convergence and use an averaged converter when switching ripple is not part of the study objective.
