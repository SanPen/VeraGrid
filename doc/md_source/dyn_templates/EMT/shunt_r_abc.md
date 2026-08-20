# Shunt R (ABC)

<!-- veragrid-block-introduction:start -->
**Shunt R (ABC)** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

This model represents a three-phase shunt resistor for EMT studies.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_A` | Instantaneous phase-A voltage across the shunt resistor when phase A is active | pu |
| Input | `v_B` | Instantaneous phase-B voltage across the shunt resistor when phase B is active | pu |
| Input | `v_C` | Instantaneous phase-C voltage across the shunt resistor when phase C is active | pu |
| Output | `i_A` | Phase-A current injected by the resistor into the EMT network | pu |
| Output | `i_B` | Phase-B current injected by the resistor into the EMT network | pu |
| Output | `i_C` | Phase-C current injected by the resistor into the EMT network | pu |
| Variable | `i_A` | Algebraic phase-A current computed from the phase-A voltage and effective resistance | pu |
| Variable | `i_B` | Algebraic phase-B current computed from the phase-B voltage and effective resistance | pu |
| Variable | `i_C` | Algebraic phase-C current computed from the phase-C voltage and effective resistance | pu |
| Variable | `R_A` | Effective resistance used by the phase-A resistor branch | pu |
| Variable | `R_B` | Effective resistance used by the phase-B resistor branch | pu |
| Variable | `R_C` | Effective resistance used by the phase-C resistor branch | pu |
| Parameter | `Pl0_A` | Nominal phase-A active-power mapping used to size or initialize the resistor branch | pu |
| Parameter | `Pl0_B` | Nominal phase-B active-power mapping used to size or initialize the resistor branch | pu |
| Parameter | `Pl0_C` | Nominal phase-C active-power mapping used to size or initialize the resistor branch | pu |
| Parameter | `R_phase_A` | Physical or mapped resistance assigned to the phase-A shunt branch | pu |
| Parameter | `R_phase_B` | Physical or mapped resistance assigned to the phase-B shunt branch | pu |
| Parameter | `R_phase_C` | Physical or mapped resistance assigned to the phase-C shunt branch | pu |
| Parameter | `Vnom` | Nominal line-to-neutral voltage used by the branch mapping logic | pu |
