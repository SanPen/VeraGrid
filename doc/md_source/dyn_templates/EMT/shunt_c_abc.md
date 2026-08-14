# Shunt C (ABC)

This model represents a three-phase shunt capacitor for EMT studies.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A voltage across the shunt capacitor when phase A is active | pu |
| Input | `v_B` | Instantaneous phase-B voltage across the shunt capacitor when phase B is active | pu |
| Input | `v_C` | Instantaneous phase-C voltage across the shunt capacitor when phase C is active | pu |
| Output | `i_A` | Phase-A current injected by the capacitor into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the capacitor into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the capacitor into the EMT network | pu |
| Variable | `v_cap_A` | Internal capacitor-voltage state for phase A | pu |
| Variable | `v_cap_B` | Internal capacitor-voltage state for phase B | pu |
| Variable | `v_cap_C` | Internal capacitor-voltage state for phase C | pu |
| Variable | `i_A` | Algebraic phase-A capacitor current computed from the capacitor state equation | pu |
| Variable | `i_B` | Algebraic phase-B capacitor current computed from the capacitor state equation | pu |
| Variable | `i_C` | Algebraic phase-C capacitor current computed from the capacitor state equation | pu |
| Parameter | `Ql0_A` | Nominal reactive-power mapping used to size or initialize the phase-A capacitor branch | pu |
| Parameter | `Ql0_B` | Nominal reactive-power mapping used to size or initialize the phase-B capacitor branch | pu |
| Parameter | `Ql0_C` | Nominal reactive-power mapping used to size or initialize the phase-C capacitor branch | pu |
| Parameter | `C_A` | Capacitance assigned to the phase-A shunt branch | pu s |
| Parameter | `C_B` | Capacitance assigned to the phase-B shunt branch | pu s |
| Parameter | `C_C` | Capacitance assigned to the phase-C shunt branch | pu s |
| Parameter | `w_base` | Base electrical angular frequency used in the capacitor scaling | rad/s |
| Parameter | `Vnom` | Nominal line-to-neutral voltage used by the branch mapping logic | pu |
