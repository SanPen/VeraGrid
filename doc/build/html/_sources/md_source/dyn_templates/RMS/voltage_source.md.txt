# RMS Voltage Source

<!-- veragrid-block-introduction:start -->
**RMS Voltage Source** represents an ideal positive-sequence voltage source whose terminal voltage magnitude and angle are held at their initialized values while the required active and reactive powers remain within their configured limits. It provides the voltage-controlled network reference used by generators and external grids in RMS studies.

## Typical use

- Use it when a generator or external grid must regulate its bus voltage magnitude and angle without internal electromechanical or control dynamics.
- Set realistic active- and reactive-power limits when the source must stop behaving as an ideal voltage reference after reaching its capability boundary.
<!-- veragrid-block-introduction:end -->

This model is the native `VOLTAGE_SOURCE_RMS` block available from the Dynamic Editor library.

### Purpose

The block represents an ideal RMS voltage source with active- and reactive-power capability limits. It initializes its voltage reference from the converged power flow and changes which algebraic condition it enforces when the corresponding power reaches a limit.

### Behaviour

- Uses the bus voltage magnitude `Vm` and angle `Va` as network-facing inputs.
- Exposes the source active power `P` and reactive power `Q` as algebraic outputs.
- Initializes `Vg0` and `Ag0` from the power-flow voltage magnitude and angle.
- Holds `Vm` at `Vg0` while reactive power remains between `Qmin_G` and `Qmax_G`.
- Holds `Va` at `Ag0` while active power remains between `Pmin_G` and `Pmax_G`.
- When a power limit is exceeded, replaces the corresponding voltage constraint with the saturated power constraint.

### Characteristics

- Algebraic-only positive-sequence RMS model.
- No rotor, excitation, governor, converter, or electromagnetic state dynamics.
- Suitable as an ideal grid reference or a simplified controlled source.
- Not suitable when the source's internal transient response must be represented.

## How it works

Define the active- and reactive-power saturation functions as

$$
P_{sat} = \max\left(P_{min,G},\min\left(P,P_{max,G}\right)\right)
$$

$$
Q_{sat} = \max\left(Q_{min,G},\min\left(Q,Q_{max,G}\right)\right).
$$

Let $I_P$ equal one while $P_{min,G} \le P \le P_{max,G}$ and zero otherwise. Likewise, let $I_Q$ equal one while $Q_{min,G} \le Q \le Q_{max,G}$ and zero otherwise. The block solves

$$
I_P\left(V_a-A_{g0}\right) + \left(1-I_P\right)\left(P-P_{sat}\right) = 0
$$

$$
I_Q\left(V_m-V_{g0}\right) + \left(1-I_Q\right)\left(Q-Q_{sat}\right) = 0.
$$

Consequently, the source controls voltage angle and magnitude in its normal operating region. At a capability boundary, it instead fixes the corresponding active or reactive power to the applicable limit.

## Initialization

At RMS initialization, the converged power-flow solution supplies

$$
V_{g0} = V_m
$$

$$
A_{g0} = V_a.
$$

The native template initializes each capability bound to a wide default value of `9.999` pu or `-9.999` pu. These values should be replaced with limits appropriate for the represented device when capability limiting is relevant to the study.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Terminal voltage magnitude supplied by the connected AC bus | pu |
| Input | `Va` | Terminal voltage angle supplied by the connected AC bus | rad |
| Output | `P` | Active-power injection required by the source | pu |
| Output | `Q` | Reactive-power injection required by the source | pu |
| Variable | `Vg0` | Initialized voltage-magnitude reference | pu |
| Variable | `Ag0` | Initialized voltage-angle reference | rad |
| Variable | `Pmax_G` | Upper active-power capability limit | pu |
| Variable | `Pmin_G` | Lower active-power capability limit | pu |
| Variable | `Qmax_G` | Upper reactive-power capability limit | pu |
| Variable | `Qmin_G` | Lower reactive-power capability limit | pu |

## How to use it

- Attach the template to a compatible generator or external-grid device.
- Run a converged power flow before the RMS simulation so `Vg0` and `Ag0` receive valid initial values.
- Review the four capability limits instead of relying on the wide defaults when source saturation is part of the scenario.
- Use a detailed synchronous-machine, converter, or Thevenin source model when internal dynamics or a finite source impedance are required.
