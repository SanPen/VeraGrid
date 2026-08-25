# Shunt R

<!-- veragrid-block-introduction:start -->
**Shunt R** represents a resistive shunt connected between one or more phase conductors and a reference point. It absorbs active power instantaneously and introduces no electrical state.

## Typical use

- Use it for resistive loads, damping branches, and the resistive part of a parallel RLC equivalent.
- Select only the conductors that physically exist and choose the star or delta connection that matches the network.
<!-- veragrid-block-introduction:end -->

The template is phase-selective: it is not restricted to ABC. Any non-empty subset of `A`, `B`, and `C` can be enabled, and a neutral conductor can be exposed when the selected star connection requires it. Consequently, valid interfaces include configurations such as A, AB, AC, BC, ABC, NA, NAB, NAC, NBC, and NABC. ABC is only the usual default.

## Electrical model

For an enabled star-connected phase $X$, the branch voltage is

$$
v_{XN}=v_X-v_N
$$

and the current absorbed by the resistor is

$$
i_{R,X}=\frac{v_{XN}}{R_X}.
$$

VeraGrid exposes current using the network-injection convention, so the external current is opposite to the absorbed branch current. A delta branch uses the same law with a line-to-line voltage, for example $i_{R,AB}=(v_A-v_B)/R_{AB}$.

Because resistance stores no energy, the model contains algebraic equations only. A voltage change therefore changes current without delay.

## Phase and neutral configurations

| Connection | Electrical reference | Neutral port | Notes |
| --- | --- | --- | --- |
| Grounded star | Ground | No external neutral is needed | Each enabled phase is connected independently to ground. |
| Neutral star | External neutral conductor | Yes | Phase and neutral currents satisfy Kirchhoff's current law. |
| Floating star | Internal star point | No | The internal neutral voltage is solved so the sum of branch currents is zero. |
| Delta | Other enabled phase conductors | No | At least two phases must be enabled; branches are created only between active phase pairs. |

Only enabled conductors, branches, equations, and external mappings are instantiated. This is why the same template can represent single-phase, two-phase, three-phase, and neutral-inclusive cases.

## Parameter sources

In star-connected load equivalents, VeraGrid can derive each phase resistance from the nominal voltage and active-power operating point:

$$
R_X=\frac{V_{nom}^2}{P_{l0,X}}.
$$

Delta equivalents use the corresponding line-to-line branch values supplied by the model data. Keep voltage bases, power bases, and connection type consistent when entering or mapping these quantities.

## Interface table

The symbol $X$ denotes any enabled phase and $XY$ an enabled delta pair.

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_X` | Instantaneous voltage of enabled phase `X` | pu |
| Input | `v_N` | Instantaneous neutral voltage for a neutral-star interface | pu |
| Output | `i_X` | Current injected into the network at enabled phase `X` | pu |
| Output | `i_N` | Neutral current injection when an external neutral is present | pu |
| Parameter | `R_X` | Star-branch resistance for phase `X` | pu |
| Parameter | `R_XY` | Delta resistance between enabled phases `X` and `Y` | pu |
| Parameter | `Pl0_X` | Initial active load power used to derive `R_X` when mapped from load data | pu |
| Parameter | `Vnom` | Nominal voltage used for parameter conversion | pu |

## Initialization and numerical limits

The resistor has no dynamic state to initialize. Its initial current follows directly from the solved terminal voltage and resistance. Resistances must remain positive and sufficiently far from zero; use a switching or fault model for an intentional short circuit. Likewise, a zero power setpoint should not be used to produce an open circuit through the conversion formula—disable the branch or supply an explicit finite parameter instead.

## How to use it

1. Enable the required phase conductors and, where applicable, the neutral.
2. Select grounded star, neutral star, floating star, or delta to match the physical connection.
3. Map either the load operating-point data or explicit branch resistances.
4. Check the current-injection sign and the initial per-phase power after initialization.
5. Combine it with Shunt L and Shunt C children when constructing a parallel RLC equivalent.
