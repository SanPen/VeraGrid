# Bergeron line (ABC)

This model represents a three-phase Bergeron transmission line for EMT studies.

### Purpose

It is the EMT transmission-line template used when finite wave travel time must be represented without moving to a full frequency-dependent line model.

### Behavior

- Uses three-phase terminal voltages at both ends of the line.
- Computes terminal current injections at both ends.
- Stores delayed history terms that represent wave travel from one end of the line to the other.
- Uses characteristic-impedance relations together with one propagation delay.

### Characteristics

- EMT traveling-wave line model.
- Phase-domain ABC representation.
- More detailed than an algebraic or lumped branch model, but simpler than a full JMarti-type frequency-dependent line.

## How it works

The Bergeron method represents each phase through a characteristic impedance and one propagation delay. At each time step, the current injected at one terminal depends on the present terminal voltage and on delayed current history arriving from the opposite end. This captures finite travel time and reflections in a computationally efficient way.

## Characteristic equations

Representative Bergeron relations are:

$$
i_f(t) = \frac{v_f(t)}{Z_c} + I_{h,t}(t-\tau)
$$

$$
i_t(t) = \frac{v_t(t)}{Z_c} + I_{h,f}(t-\tau)
$$

where the history terms carry the delayed traveling-wave information from the opposite terminal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_f_A` | From-side phase-A terminal voltage used by the Bergeron line equations when phase A is active | pu |
| Input | `v_f_B` | From-side phase-B terminal voltage used by the Bergeron line equations when phase B is active | pu |
| Input | `v_f_C` | From-side phase-C terminal voltage used by the Bergeron line equations when phase C is active | pu |
| Input | `v_t_A` | To-side phase-A terminal voltage used by the Bergeron line equations when phase A is active | pu |
| Input | `v_t_B` | To-side phase-B terminal voltage used by the Bergeron line equations when phase B is active | pu |
| Input | `v_t_C` | To-side phase-C terminal voltage used by the Bergeron line equations when phase C is active | pu |
| Output | `if_A` | Current injected by the line at the from-side phase-A port | pu |
| Output | `if_B` | Current injected by the line at the from-side phase-B port | pu |
| Output | `if_C` | Current injected by the line at the from-side phase-C port | pu |
| Output | `it_A` | Current injected by the line at the to-side phase-A port | pu |
| Output | `it_B` | Current injected by the line at the to-side phase-B port | pu |
| Output | `it_C` | Current injected by the line at the to-side phase-C port | pu |
| Variable | `Ih_f_A` | Bergeron history current seen from the from-side phase-A port after one travel delay | pu |
| Variable | `Ih_f_B` | Bergeron history current seen from the from-side phase-B port after one travel delay | pu |
| Variable | `Ih_f_C` | Bergeron history current seen from the from-side phase-C port after one travel delay | pu |
| Variable | `Ih_t_A` | Bergeron history current seen from the to-side phase-A port after one travel delay | pu |
| Variable | `Ih_t_B` | Bergeron history current seen from the to-side phase-B port after one travel delay | pu |
| Variable | `Ih_t_C` | Bergeron history current seen from the to-side phase-C port after one travel delay | pu |
| Variable | `history_buffer_f` | Runtime delay buffer that stores from-side wave-history samples between EMT steps | sample history |
| Variable | `history_buffer_t` | Runtime delay buffer that stores to-side wave-history samples between EMT steps | sample history |
| Parameter | `R_reduced` | Reduced series-resistance matrix used in the Bergeron line companion form | pu |
| Parameter | `L_reduced` | Reduced series-inductance matrix used in the Bergeron line companion form | pu |
| Parameter | `Zc_reduced` | Reduced characteristic-impedance matrix used to relate terminal voltages and traveling-wave currents | pu |
| Parameter | `tau_delay` | Wave travel time used by the history update logic | s |

## How to use it

- Use it when propagation delay and wave reflection matter in EMT line studies.
- Prefer simpler EMT line blocks when the line is short enough that travel-time effects are negligible for the study objective.
