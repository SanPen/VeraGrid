# Shunt L

<!-- veragrid-block-introduction:start -->
**Shunt L** represents an inductive shunt connected between one or more phase conductors and a reference point. Unlike a static reactive-power load, it retains the electromagnetic current state of every enabled branch.

## Typical use

- Use it for shunt reactors, magnetizing equivalents, and the inductive part of a parallel RLC load.
- Select the actual conductors and connection instead of assuming a balanced ABC device.
<!-- veragrid-block-introduction:end -->

The template accepts any non-empty subset of phases `A`, `B`, and `C`. Depending on the selected star connection, it can also expose a neutral conductor. It therefore covers A, AB, AC, BC, ABC and their applicable neutral-inclusive forms, including NA, NAB, NAC, NBC, and NABC.

## Electrical model

For an enabled star branch $X$, the absorbed branch current obeys

$$
L_X\frac{d i_{L,X}}{dt}=v_X-v_N.
$$

The corresponding stored magnetic energy is

$$
W_{L,X}=\frac{1}{2}L_X i_{L,X}^2.
$$

External port currents use VeraGrid's network-injection convention and are therefore opposite to absorbed load current. Delta branches use line-to-line voltages, such as $v_A-v_B$, and one current state per active phase pair.

## Phase and neutral configurations

| Connection | Electrical reference | Neutral port | Notes |
| --- | --- | --- | --- |
| Grounded star | Ground | No external neutral is needed | Each enabled phase has an independent inductor to ground. |
| Neutral star | External neutral conductor | Yes | The neutral carries the sum of the enabled phase branch currents. |
| Floating star | Internal star point | No | The star-point voltage is solved while enforcing zero current sum. |
| Delta | Other enabled phase conductors | No | At least two phases are required; a state is created for each active pair. |

Only selected conductors appear at the external interface. ABC is a common configuration, not a limitation of the template.

## Parameter sources

For a star-connected load equivalent, each phase inductance can be obtained from its nominal reactive-power demand:

$$
L_X=\frac{V_{nom}^2}{Q_{l0,X}\,\omega_{base}}.
$$

Delta equivalents use explicit line-to-line branch inductances. Verify whether the source data represents total three-phase power or per-phase power before mapping it.

## Interface table

The symbol $X$ denotes an enabled phase and $XY$ an enabled delta pair.

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_X` | Instantaneous voltage of enabled phase `X` | pu |
| Input | `v_N` | Instantaneous neutral voltage for a neutral-star interface | pu |
| Output | `i_X` | Current injected into the network at enabled phase `X` | pu |
| Output | `i_N` | Neutral current injection when an external neutral is present | pu |
| State | `i_L_X` | Current state of star branch `X` | pu |
| State | `i_L_XY` | Current state of delta branch `XY` | pu |
| Parameter | `L_X` | Star-branch inductance for phase `X` | pu·s |
| Parameter | `L_XY` | Delta inductance between enabled phases `X` and `Y` | pu·s |
| Parameter | `Ql0_X` | Initial inductive reactive power used to derive `L_X` | pu |
| Parameter | `Vnom` | Nominal voltage used for parameter conversion | pu |
| Parameter | `omega_base` | Base electrical angular frequency | rad/s |

## Initialization and numerical limits

Branch currents are initialized from the steady operating point. The initial currents, phase voltages, connection, and reactive-power sign must describe the same physical state; otherwise an artificial transient appears at the first time step. Inductance must be positive. Very small inductances create a fast electrical time scale and may require a smaller EMT step, while a zero reactive-power mapping must not be allowed to create an infinite or undefined parameter.

## How to use it

1. Enable the required phases and neutral conductor.
2. Choose the physical star or delta connection.
3. Map the initial reactive load or supply explicit inductances.
4. Verify the initialized branch currents and reactive-power sign.
5. Reduce the EMT time step if the chosen inductance produces dynamics faster than the existing step can resolve.
