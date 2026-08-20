# Phase locked loop

<!-- veragrid-block-introduction:start -->
**Phase locked loop** belongs to the synchronization layer of a power-system controller. A phase-locked loop compares a measured voltage reference with an internally generated angle, filters the phase error, and integrates the resulting frequency correction. It lets grid-following controls express currents and voltages in a rotating frame aligned with the network.

## Typical use

- Use it when a controller must track grid angle and frequency rather than establish them.
- Check loop bandwidth and damping against grid strength; an aggressive PLL can amplify disturbances or interact with converter current control.
<!-- veragrid-block-introduction:end -->

### Purpose

A phase locked loop (PLL) estimates the angle and frequency of an electrical signal so that other control blocks can align themselves to the network reference frame.

### Behavior

- Measures voltage in one stationary representation.
- Produces estimated angle and estimated frequency.
- Typically contains a phase detector, a PI loop filter, and one oscillator/integrator stage.

### Characteristics

- Used heavily in grid-following converter controls.
- Can be implemented with RMS phasor inputs or EMT dq/abc measurements, depending on the library block.

## Block structure

```text
measured voltage
  -> phase detector
  -> PI loop filter
  -> angle integrator / oscillator
  -> theta, omega
```

## Characteristic equations

$$
e_{pll} = v_d \quad \text{or} \quad e_{pll} = v_q
$$

$$
\omega_{est} = K_p e_{pll} + K_i \int e_{pll} \, dt
$$

$$
\frac{d\theta_{est}}{dt} = \omega_{base}(\omega_{est} - 1)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Voltage magnitude input in RMS-style PLL variants | pu |
| Input | `Va` | Voltage angle input in RMS-style PLL variants | rad |
| Input | `omega` | Frequency/speed estimate input used by some PLL realizations | pu |
| Output | `theta` | Estimated electrical angle | rad |
| Output | `omega` | Estimated electrical frequency or speed | pu |
| Output | `vd` | d-axis voltage after the phase detector or transform stage | pu |
| Output | `vq` | q-axis voltage after the phase detector or transform stage | pu |
| Variable | `phase detector` | Internal block that compares measured voltage to the present angle estimate | submodel |
| Variable | `loop filter` | Internal PI stage that converts phase error into frequency correction | submodel |
| Variable | `VCO` | Internal oscillator or angle integrator stage | submodel |
| Parameter | `Kp_pll` | Proportional PLL gain | pu/pu |
| Parameter | `Ki_pll` | Integral PLL gain | pu/(pu·s) |
| Parameter | `fn` | Nominal frequency used by the angle integrator | Hz |

## How to use it

- Use a PLL when a controller must follow the grid angle or frequency.
- Avoid it in true grid-forming controls that generate their own angle reference instead of locking to the network.
