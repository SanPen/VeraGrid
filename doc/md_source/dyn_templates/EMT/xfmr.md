# XFMR

This model represents the EMT `XFMR` transformer model.

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
