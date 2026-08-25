# Governor

<!-- veragrid-block-introduction:start -->
**Governor** belongs to an electromechanical machine or prime-mover model. It links electrical torque and flux with rotor speed, angle, mechanical power, or actuator dynamics, making it central to frequency, voltage, and rotor-angle stability studies.

## Typical use

- Use it when electrical transients must interact with rotating mass or machine controls.
- Initialize torque, power, flux, and speed consistently with the solved power flow.
<!-- veragrid-block-introduction:end -->

This model represents the EMT governor block used with the complete generator model.

### Purpose

It is the EMT mechanical-power controller built by `get_governor_emt()`.

### Behavior

- Receives rotor-speed and electromagnetic-torque feedback.
- Forms a speed error around the speed reference.
- Builds a torque order around a mechanical-power reference.
- Limits the commanded mechanical torque and sends it to the machine block.

### Characteristics

- Compact EMT governor model.
- Includes first-order governor dynamics and output saturation.
- Used as the mechanical control block of the composite generator.
## Block structure

```text
omega -> speed error
      -> gain K and first-order governor state
      -> torque order
      -> saturation (Pmin/Pmax)
      -> Tm
```

## Characteristic equations

$$
e_\omega = \omega_{ref} - \omega
$$

$$
T_{ord} = P_{m,ref} + y_{gov0}
$$

$$
\frac{dy_{gov0}}{dt} = \frac{K e_\omega + (T_e - P_{m,ref}) - y_{gov0}}{T_1}
$$

$$
y_{2,3} = \mathrm{sat}(T_{ord}, P_{min}, P_{max})
$$

$$
T_m = y_{2,3}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `omega` | Rotor-speed signal received from the machine block | pu |
| Input | `Te` | Electromagnetic torque signal received from the machine block | pu |
| Output | `Tm` | Mechanical torque command sent to the machine block | pu |
| Variable | `Pm_ref` | Internal mechanical-power reference | pu |
| Variable | `y_gov0` | Main governor state | pu |
| Variable | `y2_3_gov` | Saturated torque-order variable | pu |
| Parameter | `K` | Governor gain | pu/pu |
| Parameter | `Pmax` | Maximum mechanical torque or power command | pu |
| Parameter | `Pmin` | Minimum mechanical torque or power command | pu |
| Parameter | `Uc` | Reserved maximum closing-rate parameter kept in the EMT governor API | pu/s |
| Parameter | `Uo` | Reserved maximum opening-rate parameter kept in the EMT governor API | pu/s |
| Parameter | `T_aux` | Reserved auxiliary time parameter kept in the EMT governor API | s |
| Parameter | `Kp` | Reserved proportional control gain kept in the EMT governor API | model units |
| Parameter | `Ki` | Reserved integral control gain kept in the EMT governor API | model units |
| Parameter | `omega_ref` | Speed reference | pu |
| Parameter | `p0` | Initial active-power scheduling parameter | pu |
| Parameter | `P0` | Small active-power offset parameter | pu |
| Parameter | `T1` | Main governor time constant | s |
| Parameter | `T3` | Secondary governor time parameter retained by the EMT governor API | s |

## How to use it

- Treat this as the mechanical controller of the EMT `Complete generator` package.
- It is not meant to be used as a standalone network device.
