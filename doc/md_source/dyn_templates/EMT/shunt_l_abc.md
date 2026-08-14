# Shunt L (ABC)

This model represents a three-phase shunt inductor for EMT studies.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A voltage across the shunt inductor when phase A is active | pu |
| Input | `v_B` | Instantaneous phase-B voltage across the shunt inductor when phase B is active | pu |
| Input | `v_C` | Instantaneous phase-C voltage across the shunt inductor when phase C is active | pu |
| Output | `i_A` | Phase-A current injected by the inductor into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the inductor into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the inductor into the EMT network | pu |
| Variable | `i_L_A` | Dynamic current state of the phase-A shunt inductor | pu |
| Variable | `i_L_B` | Dynamic current state of the phase-B shunt inductor | pu |
| Variable | `i_L_C` | Dynamic current state of the phase-C shunt inductor | pu |
| Parameter | `Ql0_A` | Nominal reactive-power mapping used to size or initialize the phase-A inductor branch | pu |
| Parameter | `Ql0_B` | Nominal reactive-power mapping used to size or initialize the phase-B inductor branch | pu |
| Parameter | `Ql0_C` | Nominal reactive-power mapping used to size or initialize the phase-C inductor branch | pu |
| Parameter | `L_A` | Inductance assigned to the phase-A shunt branch | pu s |
| Parameter | `L_B` | Inductance assigned to the phase-B shunt branch | pu s |
| Parameter | `L_C` | Inductance assigned to the phase-C shunt branch | pu s |
| Parameter | `w_base` | Base electrical angular frequency used in the inductor scaling | rad/s |
| Parameter | `Vnom` | Nominal line-to-neutral voltage used by the branch mapping logic | pu |
