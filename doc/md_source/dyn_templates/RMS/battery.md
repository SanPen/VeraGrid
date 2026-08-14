# Battery

This model represents an RMS battery energy storage system with converter and DC-side state dynamics.

### Purpose

It is an ESD1-inspired RMS battery energy storage model with active/reactive power control, current limiting, and state-of-charge dynamics.

### Behavior

- Uses terminal voltage magnitude and angle as network inputs.
- Accepts active and reactive power references.
- Computes available charging and discharging power from state of charge.
- Applies current-priority logic and output current lags.
- Evolves state of charge using charge and discharge efficiencies.

Sign convention:

- `P > 0`: battery discharges into the AC grid.
- `P < 0`: battery charges from the AC grid.

### Characteristics

- Averaged RMS storage model.
- Suitable for dynamic storage studies at electromechanical timescales.
- Represents power capability and state of charge, not electrochemical cell detail.
## Characteristic equations

$$
P = V_m I_{p,out}
$$

$$
Q = V_m I_{q,out}
$$

$$
\dot{SoC} = \frac{-P_{dis}/\eta_{dis} + \eta_{ch} P_{ch}}{E_{cap} \cdot 3600}
$$

$$
P_{sum} = \mathrm{sat}(P_{ref}+P_{ext}, -P_{ch,av}, P_{dis,av})
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude at the battery point of connection | pu |
| Input | `Va` | Terminal voltage angle at the battery point of connection | rad |
| Output | `P_esd1` | Active power injected or absorbed by the battery model | pu |
| Output | `Q_esd1` | Reactive power injected or absorbed by the battery model | pu |
| Variable | `Ipout_y` | Filtered active-current output state | pu |
| Variable | `Iqout_y` | Filtered reactive-current output state | pu |
| Variable | `Soc` | State of charge | pu |
| Variable | `Pref` | Internal active-power reference after reference-channel evaluation | pu |
| Variable | `Pext` | External active-power offset channel | pu |
| Variable | `Qref` | Internal reactive-power reference | pu |
| Variable | `P_sum` | Net active-power command after limiting | pu |
| Variable | `Q_sum` | Net reactive-power command after limiting | pu |
| Variable | `P_dis_av` | Available discharge power allowed by the present state of charge | pu |
| Variable | `P_ch_av` | Available charge power allowed by the present state of charge | pu |
| Variable | `Ip_cmd` | Active-current command before current output lag | pu |
| Variable | `Iq_cmd` | Reactive-current command before current output lag | pu |
| Variable | `Ip_max` | Active-current capability limit | pu |
| Variable | `Iq_max` | Reactive-current capability limit | pu |
| Parameter | `pref0` | Base active-power reference | pu |
| Parameter | `pext0` | External active-power offset reference | pu |
| Parameter | `qref0` | Base reactive-power reference | pu |
| Parameter | `p_dis_max` | Maximum discharge power capability | pu |
| Parameter | `p_ch_max` | Maximum charge power capability | pu |
| Parameter | `qmax` | Upper reactive-power limit | pu |
| Parameter | `qmin` | Lower reactive-power limit | pu |
| Parameter | `soc_min` | Minimum allowed state of charge | pu |
| Parameter | `soc_max` | Maximum allowed state of charge | pu |
| Parameter | `soc_db` | State-of-charge deadband width used for smooth availability gating | pu |
| Parameter | `soc0` | Initial state of charge | pu |
| Parameter | `ecap_h` | Energy capacity on the system per-unit base, expressed in equivalent hours | h |
| Parameter | `eta_ch` | Charge efficiency | pu |
| Parameter | `eta_dis` | Discharge efficiency | pu |
| Parameter | `ialim` | Converter current limit | pu |
| Parameter | `pqflag` | Priority selector between active-current and reactive-current limitation | 0/1 |
| Parameter | `tip` | Active-current lag time constant | s |
| Parameter | `tiq` | Reactive-current lag time constant | s |

## How to use it

- Use it when state of charge and available charging/discharging power matter in RMS studies.
- Do not use it as a detailed battery chemistry or cell-balancing model.
