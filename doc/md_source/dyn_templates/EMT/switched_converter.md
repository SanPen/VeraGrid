# Switched converter

This model represents an EMT switched converter with explicit switching behavior.

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
