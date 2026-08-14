# GFM VSC

This model represents a positive-sequence RMS grid-forming voltage-source converter.

### Purpose

It provides a compact grid-forming converter representation for RMS studies. The model focuses on terminal power exchange and converter losses rather than detailed modulation or inner current-control dynamics.

### Behavior

- Uses AC terminal voltage magnitude and angle together with a DC-side voltage input.
- Represents the converter as a compact power-processing device between its AC-side and DC-side channels.
- Computes one effective current magnitude from the active and reactive operating point.
- Uses a polynomial loss law to relate the active power on both sides of the converter.
- Exposes one reactive-power reference channel used by the surrounding VSC formulation.

### Characteristics

- Very compact averaged converter representation.
- Positive-sequence RMS model.
- Suitable for high-level grid-forming converter behavior studies.
- Simpler than the EMT converter family and simpler than a detailed RMS control hierarchy.

## How it works

The model does not reconstruct phase voltages, switching states, or modulation signals. Instead, it estimates the operating current magnitude from the power point and uses that current to evaluate conversion losses. This makes the block useful when the network-level impact of the converter matters more than the internal control implementation.

## Characteristic equations

$$
i_m = \frac{\sqrt{P_t^2 + Q_{t,ref}^2}}{V_{m,t}}
$$

$$
P_f + P_t = \alpha_1 + \alpha_2 i_m + \alpha_3 i_m^2
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm_t` | AC terminal voltage magnitude seen by the converter model | pu |
| Input | `Va_t` | AC terminal voltage angle seen by the converter model | rad |
| Input | `Vdc` | DC-side voltage input | pu |
| Output | `Pf_vsc` | Active power at the converter from side | pu |
| Output | `Pt` | Active power at the converter to side | pu |
| Output | `Qt_ref` | Reactive-power reference channel exported by the model | pu |
| Variable | `Pf_vsc` | Algebraic from-side active-power variable | pu |
| Variable | `Pt` | Algebraic to-side active-power variable | pu |
| Variable | `Qt_ref` | Runtime reactive-power reference used by the compact model | pu |
| Variable | `im` | Effective current magnitude used by the loss model | pu |
| Parameter | `alpha1` | Constant term of the converter loss polynomial | model units |
| Parameter | `alpha2` | Linear coefficient of the converter loss polynomial | model units |
| Parameter | `alpha3` | Quadratic coefficient of the converter loss polynomial | model units |

## How to use it

- Use it when one compact RMS grid-forming converter is enough for the study objective.
- Move to EMT or to a richer RMS controller structure when detailed current control, modulation, or waveform phenomena are important.
