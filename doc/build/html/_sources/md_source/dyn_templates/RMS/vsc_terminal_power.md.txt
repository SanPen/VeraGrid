# VSC terminal power equations

**Library:** RMS → Basic_devices → VSC terminal power equations  
**Catalogue type:** `VSC_TERMINAL_POWER_RMS`  
**Builder:** `build_vsc_terminal_power_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

This algebraic interface couples the converter's internal powers and capacitor voltage to the network terminals. It is a component of a VSC model, not a complete converter on its own.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdc` | DC bus voltage, pu |
| Input | 2 | `Vdc_state` | Capacitor-voltage state, pu |
| Input | 3 | `P` | Internal converter active power, pu |
| Input | 4 | `Q` | Internal converter reactive power, pu |
| Output | 1 | `Pf_vsc` | DC-terminal active power entering the VSC |
| Output | 2 | `Pt_vsc` | AC-terminal active power entering the VSC |
| Output | 3 | `Qt_vsc` | AC-terminal reactive power entering the VSC |

The output order is **Pf, Pt, Qt**. Do not reorder these ports by the order of variables in the equation editor.

## Equations

$$
0=V_{dc}-V_{dc,state},\qquad
0=P_{t,vsc}+P,\qquad
0=Q_{t,vsc}+Q.
$$

There is no isolated equation `Pf_vsc = ...` in this block. `Pf_vsc` is determined jointly by the DC-network equations, the voltage constraint and the capacitor dynamics. Do not remove the voltage constraint because it does not explicitly contain `Pf_vsc`, and do not replace it with a steady-state loss balance: that would change the transient model.

The block has no differential states and no control-mode selector. `Qf = 0.0` is stored in `event_dict` for the DC-side reactive-power mapping; it is not an output port or a selectable reactive-power control.

## Initialization and mappings

The block exposes `Vdc`, `Pf`, `Pt`, `Qt` and `Qf` through `external_mapping`. The power flow initializes the terminal powers; this block has no duplicate `init_eqs` for them. Applying/saving a manually assembled model allows the connected electrical block to derive `P0 = -Pt_vsc0` and `Q0 = -Qt_vsc0`.

Connect `P/Q` from the electrical model and `Vdc_state` from the capacitor. Connect `Pf_vsc/Pt_vsc` both to the root's corresponding network outputs and to the capacitor balance inputs. Connect `Qt_vsc` to the root AC-reactive-power output. The DC-bus voltage goes to input 1, not input 2.
