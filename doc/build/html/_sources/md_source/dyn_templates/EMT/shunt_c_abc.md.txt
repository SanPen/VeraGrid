# Shunt C

<!-- veragrid-block-introduction:start -->
**Shunt C** represents a capacitive shunt connected between one or more phase conductors and a reference point. It retains capacitor-voltage or charge dynamics and supplies capacitive reactive current according to the instantaneous terminal voltage.

## Typical use

- Use it for capacitor banks, filters, cable or equipment shunt capacitance, and the capacitive part of a parallel RLC equivalent.
- Configure the actual active conductors and connection; ABC is only one possible interface.
<!-- veragrid-block-introduction:end -->

The template accepts any non-empty subset of phases `A`, `B`, and `C` and can expose a neutral for the appropriate star connection. It therefore supports single-, two-, and three-phase arrangements such as A, AB, AC, BC, ABC and applicable neutral-inclusive variants such as NA, NAB, NAC, NBC, and NABC.

## Electrical model

For an enabled star branch $X$,

$$
v_{C,X}=v_X-v_N,
$$

$$
i_{C,X}=C_X\frac{d v_{C,X}}{dt}.
$$

The stored electric energy is

$$
W_{C,X}=\frac{1}{2}C_Xv_{C,X}^2.
$$

The external current follows VeraGrid's network-injection sign convention. Delta branches use the line-to-line voltage of each enabled pair.

## Phase and neutral configurations

| Connection | Electrical reference | Neutral port | Notes |
| --- | --- | --- | --- |
| Grounded star | Ground | No external neutral is needed | One independent capacitor is created for every enabled phase. |
| Neutral star | External neutral conductor | Yes | Neutral current balances the enabled phase currents. |
| Floating star | Internal star point | No | The internal neutral voltage is solved from current balance. |
| Delta | Other enabled phase conductors | No | At least two phases are required; capacitors are placed between active pairs. |

Only enabled conductors, variables, equations, and mappings are created.

## Parameter sources

For a star-connected equivalent, each phase capacitance can be obtained from nominal capacitive reactive power:

$$
C_X=\frac{Q_{l0,X}}{V_{nom}^2\,\omega_{base}}.
$$

Delta equivalents use explicit line-to-line branch capacitances. Check the reactive-power sign convention and whether the source quantity is per-phase or total before mapping it.

## Interface table

The symbol $X$ denotes an enabled phase and $XY$ an enabled delta pair.

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_X` | Instantaneous voltage of enabled phase `X` | pu |
| Input | `v_N` | Instantaneous neutral voltage for a neutral-star interface | pu |
| Output | `i_X` | Current injected into the network at enabled phase `X` | pu |
| Output | `i_N` | Neutral current injection when an external neutral is present | pu |
| Variable | `v_C_X` | Capacitor voltage of star branch `X` | pu |
| Variable | `v_C_XY` | Capacitor voltage of delta branch `XY` | pu |
| Parameter | `C_X` | Star-branch capacitance for phase `X` | pu·s |
| Parameter | `C_XY` | Delta capacitance between enabled phases `X` and `Y` | pu·s |
| Parameter | `Ql0_X` | Initial capacitive reactive power used to derive `C_X` | pu |
| Parameter | `Vnom` | Nominal voltage used for parameter conversion | pu |
| Parameter | `omega_base` | Base electrical angular frequency | rad/s |

## Initialization and numerical limits

The initial capacitor voltage must agree with the initialized terminal voltages and connection. Inconsistent values cause an artificial charging transient. Capacitance must be positive. Very small capacitance can introduce fast transients, while very large capacitance can dominate the network energy and slow the response. A zero reactive-power mapping needs explicit handling rather than relying on a singular parameter conversion.

## How to use it

1. Enable the physical phase and neutral conductors.
2. Select the correct grounded-star, neutral-star, floating-star, or delta connection.
3. Map the initial capacitive reactive power or supply explicit branch capacitances.
4. Check the initial capacitor voltages and reactive-power sign.
5. Select an EMT time step that resolves the fastest network resonance involving this capacitance.
