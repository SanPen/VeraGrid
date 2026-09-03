# DC line

**Library:** RMS DC line → Devices → DC line  
**Catalogue type:** `DC_LINE_RMS`  
**Builder:** `build_dc_line_rms_v2()` in `dc_line_rms_template_v2.py`; configurable definition: `DcLineRmsTemplateV2`.

## Purpose and interface

The series R-L model retains the DC-line current as an explicit state. A wrapper exposes the network mappings, and its `R-L DC line equations` child owns the equations and parameters.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdcf` | From-bus DC voltage; mapping `Vmf` |
| Input | 2 | `Vdct` | To-bus DC voltage; mapping `Vmt` |
| Output | 1 | `Pf` | Active power entering the line at the from terminal |
| Output | 2 | `Pt` | Active power entering the line at the to terminal |

`If_dc` is a state with a power-flow initialization mapping, **not an output port**. Positive current flows from the from bus to the to bus. Signals use the line model's per-unit bases.

## Equations and parameters

$$
\dot{I}_{f,dc}=\frac{V_{dc,f}-V_{dc,t}-r_{dc}I_{f,dc}}{l_{dc}},\qquad
P_f=V_{dc,f}I_{f,dc},\qquad P_t=-V_{dc,t}I_{f,dc}.
$$

| Parameter | Ownership | Value source |
| --- | --- | --- |
| `r_dc` | Static, `parameters` | `api_obj_mapping[dc_line_r_pu]`; assigned from static `DcLine.R_corrected` |
| `l_dc` | Dynamic, `event_dict` | Template default `0.05`, model-normalized inductance coefficient |

`r_dc` is declared as `Const(None)` and has no fallback. Set resistance on the static DC-line device; temperature correction can affect `R_corrected`. With no temperature correction changing the resistance, it equals the corresponding static resistance value. The HVDC practical example uses static `R = 0.01`.

The static DC line has no inductance counterpart. Edit `l_dc` in the dynamic parameter table, or call `set_parameter_in_model(var_name="l_dc", new_value=...)` on the model. Inductance is not a builder argument or a graphical input. Use a positive value and the normalization of the implemented equation, not unconverted henries.

## Initialization and use

The power flow initializes `If_dc`, `Pf` and `Pt` directly through `external_mapping`; their `init_eqs` are intentionally empty. Do not add equations that overwrite these values. Initial equilibrium requires `Vdcf - Vdct = r_dc If_dc` with the same resistance used by the static model.

Connect the two DC-bus voltages in from/to order and the two powers to the matching root connection variables. Apply/save the RMS model so the root exposes the child's static and power-flow mappings. An unresolved `r_dc` is a mapping/assignment error, not a reason to add an independent dynamic resistance.
