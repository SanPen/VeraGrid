# Inverse Clarke transform

<!-- veragrid-block-introduction:start -->
**Inverse Clarke transform** is a coordinate-transformation block. In three-phase analysis, Clarke and Park transforms separate stationary or rotating components so sinusoidal phase quantities can be controlled as nearly constant d-q signals. The selected scaling determines whether amplitude or instantaneous power is preserved.

## Typical use

- Use it to connect phase-domain electrical quantities with d-q or sequence-domain control laws.
- Keep angle orientation, axis alignment, phase order, and power/amplitude convention consistent.
<!-- veragrid-block-introduction:end -->

### Purpose

This block reconstructs three-phase quantities from classical non-power-invariant `alpha-beta-0` components.

### Behavior

- Receives orthogonal stationary-frame quantities.
- Produces phase-domain outputs.
- Inverts the classical Clarke transform.

### Characteristics

- Appropriate when the surrounding formulation uses the classical Clarke scaling.

## Characteristic equations

$$
\begin{bmatrix}
x_A \\
x_B \\
x_C
\end{bmatrix}
=
\begin{bmatrix}
1 & 0 & 1 \\
-\frac{1}{2} & \frac{\sqrt{3}}{2} & 1 \\
-\frac{1}{2} & -\frac{\sqrt{3}}{2} & 1
\end{bmatrix}
\begin{bmatrix}
x_\alpha \\
x_\beta \\
x_0
\end{bmatrix}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `x_alpha` | Alpha-axis stationary component | model-dependent |
| Input | `x_beta` | Beta-axis stationary component | model-dependent |
| Input | `x_0` | Zero-sequence stationary component | model-dependent |
| Output | `x_A` | Phase-A reconstructed quantity | model-dependent |
| Output | `x_B` | Phase-B reconstructed quantity | model-dependent |
| Output | `x_C` | Phase-C reconstructed quantity | model-dependent |

## How to use it

- Use this block only with signals that follow the classical Clarke scaling convention.
