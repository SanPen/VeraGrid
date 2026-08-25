# XFMR

<!-- veragrid-block-introduction:start -->
**XFMR** represents passive network physics through resistance, inductance, capacitance, coupling, or switching topology. Its equations enforce voltage-current constitutive relations and therefore affect energy storage, damping, propagation, fault current, or grounding behavior.

## Typical use

- Use it to reproduce the electrical path between sources, converters, machines, and loads.
- Keep phases, terminal orientation, connection type, and SI/per-unit parameter bases consistent.
<!-- veragrid-block-introduction:end -->

This is the detailed phase-domain EMT transformer model. It represents winding connections, leakage flux, magnetizing and core-loss behavior, terminal capacitance, grounding, and optional nonlinear core saturation.

## Model structure

The from- and to-side connection matrices map external phase voltages and currents to physical winding quantities. The electrical model is referred consistently to the from side and contains:

- three leakage-current states;
- three core leg-flux states plus the selected return-flux path;
- magnetizing and iron-loss branches;
- from- and to-side terminal capacitance states; and
- neutral/grounding links required by the chosen winding connections.

This is more detailed than an ideal-ratio or conventional steady-state transformer and is intended for energization, unbalance, grounding, inrush, and fast transient studies.

## Characteristic equations

The leakage branch follows the coupled matrix relation

$$
\frac{d\boldsymbol{i}_{leak}}{dt}
=\boldsymbol{L}_{leak}^{-1}
\left(\boldsymbol{v}_{leak}-R_{sc}\boldsymbol{i}_{leak}\right).
$$

Core leg flux is obtained by integrating the core voltage,

$$
\frac{d\lambda_k}{dt}=\omega_{base}v_{core,k},
$$

and the terminal capacitances retain charge states whose derivatives are the capacitor currents. The iron-loss conductance is derived from open-circuit loss data, while leakage resistance and inductance are derived from short-circuit data.

## Core and connection options

The core can use a linear magnetizing relation or the nonlinear Frolich characteristic. Three-legged and five-legged return paths are represented differently, which matters during zero-sequence excitation and saturation. From- and to-side winding connection matrices determine phase shift and whether neutral ports exist. Grounding impedances or solid grounding must agree with those connection choices.

Do not infer the available neutral terminals from the filename or symbol alone: inspect the selected winding types. A delta winding has no external neutral, while a grounded or accessible-star winding can expose or constrain one.

## Initialization and numerical behavior

The initializer uses solved terminal voltages and power-flow currents to establish leakage current, core flux, magnetizing current, and terminal charge consistently. Energization from a de-energized state is a different study and requires the intended initial flux or switching event. Nonlinear saturation, small leakage inductance, and terminal capacitance can introduce fast time scales; use time-step convergence and inspect flux and inrush current, not only RMS power.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `vf_A` | From-side phase-A terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Input | `vf_B` | From-side phase-B terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Input | `vf_C` | From-side phase-C terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Input | `vt_A` | To-side phase-A terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Input | `vt_B` | To-side phase-B terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Input | `vt_C` | To-side phase-C terminal voltage applied to the transformer model when that port exists for the selected connection | pu |
| Output | `if_A` | Current injected by the transformer at the from-side phase-A port | pu |
| Output | `if_B` | Current injected by the transformer at the from-side phase-B port | pu |
| Output | `if_C` | Current injected by the transformer at the from-side phase-C port | pu |
| Output | `it_A` | Current injected by the transformer at the to-side phase-A port | pu |
| Output | `it_B` | Current injected by the transformer at the to-side phase-B port | pu |
| Output | `it_C` | Current injected by the transformer at the to-side phase-C port | pu |
| Variable | `i_leak_f` | Leakage-branch current state referred to the from side of the transformer | pu |
| Variable | `i_leak_t` | Leakage-branch current state referred to the to side of the transformer | pu |
| Variable | `i_mag` | Magnetizing-branch current associated with the transformer core model | pu |
| Variable | `i_core_loss` | Core-loss branch current that represents iron losses | pu |
| Variable | `q_cap_f` | Charge or equivalent state of the from-side terminal capacitance branch when enabled | pu s |
| Variable | `q_cap_t` | Charge or equivalent state of the to-side terminal capacitance branch when enabled | pu s |
| Parameter | `S_rated` | Rated apparent power used to scale the transformer model data | MVA |
| Parameter | `V_rated_f` | Rated from-side winding voltage used to scale the model data | kV |
| Parameter | `V_rated_t` | Rated to-side winding voltage used to scale the model data | kV |
| Parameter | `R_leak` | Leakage resistance parameter of the transformer equivalent circuit | pu |
| Parameter | `X_leak` | Leakage reactance parameter of the transformer equivalent circuit | pu |
| Parameter | `R_core` | Core-loss resistance parameter of the transformer equivalent circuit | pu |
| Parameter | `X_mag` | Magnetizing reactance parameter of the transformer equivalent circuit | pu |
| Parameter | `tap_ratio` | Off-nominal tap ratio applied by the transformer model | pu |
| Parameter | `connection_matrix` | Connection mapping matrix that links physical windings to external EMT ports | topology mapping |

The table lists representative phase ports. Neutral inputs and outputs are present only when the chosen from- or to-side winding connection exposes them.

## How to use it

1. Select the physical from- and to-side winding connections and grounding arrangement.
2. Map ratings, voltage bases, short-circuit data, open-circuit data, tap, core topology, and capacitance.
3. Choose linear core behavior for ordinary network transients or nonlinear behavior when saturation and inrush matter.
4. Verify phase shift, current orientation, neutral availability, and initial flux after initialization.
5. Repeat sensitive EMT results with a smaller time step, especially for energization and ferroresonance-like cases.
