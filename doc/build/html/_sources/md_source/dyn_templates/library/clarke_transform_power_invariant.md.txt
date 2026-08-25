# Clarke transform (power invariant)

<!-- veragrid-block-introduction:start -->
**Clarke transform (power invariant)** is a coordinate-transformation block. In three-phase analysis, Clarke and Park transforms separate stationary or rotating components so sinusoidal phase quantities can be controlled as nearly constant d-q signals. The selected scaling determines whether amplitude or instantaneous power is preserved.

## Typical use

- Use it to connect phase-domain electrical quantities with d-q or sequence-domain control laws.
- Keep angle orientation, axis alignment, phase order, and power/amplitude convention consistent.
<!-- veragrid-block-introduction:end -->

### Purpose

This block converts three-phase `abc` quantities into stationary `alpha-beta-0` quantities while preserving power invariance.

### Behavior

- Receives phase-domain quantities.
- Produces orthogonal stationary-frame components.
- Preserves power under the chosen normalization.

### Characteristics

- Suitable for control and analysis schemes that require power-invariant scaling.

## Characteristic equations

$$
\begin{bmatrix}
x_\alpha \\
x_\beta \\
x_0
\end{bmatrix}
=
\sqrt{\frac{2}{3}}
\begin{bmatrix}
1 & -\frac{1}{2} & -\frac{1}{2} \\
0 & \frac{\sqrt{3}}{2} & -\frac{\sqrt{3}}{2} \\
\frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}} & \frac{1}{\sqrt{2}}
\end{bmatrix}
\begin{bmatrix}
x_A \\
x_B \\
x_C
\end{bmatrix}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `x_A` | Phase-A input quantity | model-dependent |
| Input | `x_B` | Phase-B input quantity | model-dependent |
| Input | `x_C` | Phase-C input quantity | model-dependent |
| Output | `x_alpha` | Power-invariant alpha-axis component | model-dependent |
| Output | `x_beta` | Power-invariant beta-axis component | model-dependent |
| Output | `x_0` | Power-invariant zero-sequence component | model-dependent |

## How to use it

- Use this variant when orthogonal components must preserve power normalization.
