# Converter

This model represents the compact converter submodel used inside the RMS grid-forming VSC package.

### Purpose

It is the reduced-order RMS converter block built by `build_vsc_rms()`. Its purpose is to capture the main active-power transfer and converter-loss behavior without exposing switching detail or a large internal controller hierarchy.

### Behavior

- Uses AC terminal voltage magnitude and angle together with a DC-side voltage input.
- Computes one effective converter current magnitude from the requested power transfer.
- Applies a polynomial loss relation to connect the AC-side and DC-side active-power channels.
- Exposes a reactive-power reference channel used by the surrounding converter package.

### Characteristics

- Compact averaged converter model.
- Positive-sequence RMS representation.
- Suitable for system-level converter studies where detailed inner control loops are not required.
- Much simpler than the EMT converter families and simpler than a controller-by-controller RMS implementation.

## How it works

The block first estimates an effective current magnitude from the commanded active and reactive operating point. It then uses a polynomial loss law to relate the power entering one side of the converter to the power leaving the other side. In that sense, the block behaves like a power-processing element with configurable conversion losses rather than a waveform-resolved electronic bridge.

## Characteristic equations

Representative equations are:

$$
i_m = \frac{\sqrt{P_t^2 + Q_{t,ref}^2}}{V_{m,t}}
$$

$$
P_f + P_t = \alpha_1 + \alpha_2 i_m + \alpha_3 i_m^2
$$

The first equation estimates converter current magnitude, and the second equation enforces the active-power balance including losses.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm_t` | AC terminal voltage magnitude seen by the converter model | pu |
| Input | `Va_t` | AC terminal voltage angle seen by the converter model | rad |
| Input | `Vdc` | DC-side voltage input used by the compact converter balance | pu |
| Output | `Pf_vsc` | Converter active power on the from side of the compact RMS model | pu |
| Output | `Pt` | Converter active power on the to side of the compact RMS model | pu |
| Output | `Qt_ref` | Reactive-power reference channel exposed by the block | pu |
| Variable | `Pf_vsc` | Algebraic active-power variable representing converter from-side power | pu |
| Variable | `Pt` | Algebraic active-power variable representing converter to-side power | pu |
| Variable | `Qt_ref` | Reactive-power reference value forwarded by the compact model | pu |
| Variable | `im` | Effective current magnitude used in the loss expression | pu |
| Parameter | `alpha1` | Constant term of the converter loss polynomial | model units |
| Parameter | `alpha2` | Linear coefficient of the converter loss polynomial | model units |
| Parameter | `alpha3` | Quadratic coefficient of the converter loss polynomial | model units |

## How to use it

- Use it as the converter core inside high-level RMS VSC studies.
- Use a more detailed EMT or controller-rich model when switching behavior, current-loop dynamics, modulation, or protection details matter.
