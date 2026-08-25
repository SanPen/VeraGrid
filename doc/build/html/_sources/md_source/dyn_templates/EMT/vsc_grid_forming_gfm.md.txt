# VSC Grid-Forming (GFM)

<!-- veragrid-block-introduction:start -->
**VSC Grid-Forming (GFM)** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

This model represents a grid-forming voltage-source converter in EMT form.

### Purpose

It is the EMT grid-forming converter template used when the converter must establish its own voltage angle and magnitude instead of locking to an external grid reference.

### Behavior

- Uses three-phase terminal voltages and one DC-side voltage input.
- Maintains an internal electrical angle and frequency.
- Synthesizes an internal balanced three-phase emf behind a series output branch.
- Measures active and reactive power at the AC interface.
- Adjusts frequency and voltage magnitude through droop control.
- Produces AC current injections and one implied DC current channel.

### Characteristics

- EMT grid-forming converter model.
- Source-behind-impedance representation.
- Suitable for islanded systems, weak-grid studies, and converter-dominated systems where the converter sets the local voltage reference.

## How it works

The converter behaves like a controlled internal three-phase source behind an output impedance. Its internal angle evolves from a frequency state, and that frequency is adjusted from active-power error through droop control. The internal emf magnitude is adjusted from reactive-power error through voltage droop. The branch impedance then determines the current exchanged with the network.

## Characteristic equations

$$
\frac{d\theta}{dt} = \omega_{base}\,\omega
$$

$$
\tau_\omega \frac{d\omega}{dt} = (\omega_{ref} - \omega) - K_{dp}(P_e - P_{ref})
$$

$$
\tau_v \frac{dE_{pk}}{dt} = (V_{ref} - E_{pk}) - K_{dq}(Q_e - Q_{ref})
$$

$$
\mathbf{i}_{abc} = \frac{\mathbf{e}_{abc} - \mathbf{v}_{abc}}{R_s + sL_s}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A AC terminal voltage applied to the converter output branch | pu |
| Input | `v_B` | Instantaneous phase-B AC terminal voltage applied to the converter output branch | pu |
| Input | `v_C` | Instantaneous phase-C AC terminal voltage applied to the converter output branch | pu |
| Input | `v_dc` | DC terminal voltage used to compute DC power balance | pu |
| Output | `i_A` | Phase-A current injected by the grid-forming converter into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the grid-forming converter into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the grid-forming converter into the EMT network | pu |
| Output | `i_dc` | DC current implied by the converter active-power balance | pu |
| Variable | `theta` | Internal electrical angle of the converter voltage source | rad |
| Variable | `omega` | Internal per-unit electrical frequency after P-f droop control | pu |
| Variable | `Epk` | Peak magnitude of the internal balanced three-phase emf | pu |
| Variable | `e_A` | Internal phase-A emf behind the series RL branch | pu |
| Variable | `e_B` | Internal phase-B emf behind the series RL branch | pu |
| Variable | `e_C` | Internal phase-C emf behind the series RL branch | pu |
| Variable | `Pe` | Instantaneous active power measured at the AC interface for frequency droop control | pu |
| Variable | `Qe` | Instantaneous reactive power measured at the AC interface for voltage droop control | pu |
| Parameter | `omega_base` | Base electrical angular frequency used by the state equations | rad/s |
| Parameter | `R_s` | Series resistance of the converter output branch | pu |
| Parameter | `X_s` | Series reactance of the converter output branch | pu |
| Parameter | `Kdp` | Active-power-to-frequency droop gain | pu frequency/pu power |
| Parameter | `Kdq` | Reactive-power-to-voltage droop gain | pu voltage/pu reactive power |
| Parameter | `tau_omega` | Time constant of the internal frequency-control state | s |
| Parameter | `tau_v` | Time constant of the internal voltage-magnitude-control state | s |
| Parameter | `omega_ref` | Frequency reference used by the grid-forming droop controller | pu |
| Parameter | `P_ref` | Active-power reference used by the frequency droop controller | pu |
| Parameter | `Q_ref` | Reactive-power reference used by the voltage droop controller | pu |
| Parameter | `V_ref` | Voltage-magnitude reference used by the voltage droop controller | pu |
| Parameter | `Qf` | Initialization reactive-power quantity used by the EMT/PF bridge for this converter | pu |
| Parameter | `Vpk_ref` | Initialization peak-voltage magnitude used to seed the internal emf state | pu |
| Parameter | `phi_v_ref` | Initialization terminal-voltage angle used to seed the internal emf state | rad |
| Parameter | `Ipk_ref` | Initialization peak-current magnitude used to align the EMT state with the solved operating point | pu |
| Parameter | `phi_ref` | Initialization current-to-voltage phase relation used to align the EMT state with the solved operating point | rad |

## How to use it

- Use it when the converter must form the grid voltage rather than track it.
- Do not replace a grid-following converter with this model unless the control philosophy of the study is truly grid-forming.
