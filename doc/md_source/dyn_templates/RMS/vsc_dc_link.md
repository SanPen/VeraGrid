# DC-link capacitor

**Library:** RMS VSC → Devices → DC-link capacitor  
**Catalogue type:** `VSC_DC_LINK_RMS`  
**Builder:** `build_vsc_dc_link_rms()` in `hvdc_vsc_gfl_rms_template_v2.py`.

## Purpose and interface

This block owns the explicit DC-link voltage state and includes converter losses in the DC-link power balance. It belongs to a static **VSC** device; it is not the DC-line model or an independently assignable static capacitor.

| Direction | Position | Signal | Meaning |
| --- | --- | --- | --- |
| Input | 1 | `Vdc` | DC bus voltage for state initialization |
| Input | 2 | `Pf_vsc` | Power entering the VSC from its DC terminal |
| Input | 3 | `Pt_vsc` | Power entering the VSC from its AC terminal |
| Input | 4 | `i_d` | Electrical d-axis current used for losses |
| Input | 5 | `i_q` | Electrical q-axis current used for losses |
| Output | 1 | `Vdc_state` | Explicit capacitor-voltage state |

Signals use model per-unit quantities. Positive terminal powers enter the VSC.

## Equations

$$
i_m=\sqrt{i_d^2+i_q^2+10^{-11}},\qquad
P_{loss}=a_0+a_1i_m+a_2i_m^2,
$$

$$
\dot{V}_{dc,state}=\frac{P_{f,vsc}+P_{t,vsc}-P_{loss}}{C_{dc}V_{dc,state}}.
$$

At equilibrium, the two terminal powers sum to converter losses. During a transient, their imbalance also changes stored DC-link energy. The terminal block supplies the separate algebraic constraint `Vdc = Vdc_state`.

## Parameters

| Parameter | Ownership | Value source |
| --- | --- | --- |
| `Cdc` | Dynamic, `event_dict` | Default `0.40`, model-normalized capacitance coefficient |
| `a0` | Static, `parameters` | `api_obj_mapping[alpha1]` → static VSC `alpha1` |
| `a1` | Static, `parameters` | `api_obj_mapping[alpha2]` → static VSC `alpha2` |
| `a2` | Static, `parameters` | `api_obj_mapping[alpha3]` → static VSC `alpha3` |

The three static coefficients have no numerical template fallback. Their `Const(None)` declarations must be resolved from the associated VSC. Zero static coefficients are valid. Edit them on the static device, not in the dynamic parameter table. `Cdc` is used directly in the implemented equation; it is not an unconverted capacitance in farads.

## Initialization and wiring

Initialization sets `Vdc_state0 = Vdc0` from the DC bus. Use positive `Cdc` and a nonzero operating voltage; the equation divides by both. Terminal-power initialization comes from the power flow through the [terminal power block](vsc_terminal_power.md).

Connect `Pf_vsc/Pt_vsc` from that block and `i_d/i_q` from the electrical block. Feed `Vdc_state` to terminal-power input 2 and, in `Vm_dc` mode, to the active controller. The DC-bus voltage remains connected to input 1 and to terminal-power input 1.

If assembly reports an unresolved `a0/a1/a2`, inspect the static mapping and the saved root mappings. Do not work around the error by converting these coefficients to dynamic parameters or assigning arbitrary fallback zeros.
