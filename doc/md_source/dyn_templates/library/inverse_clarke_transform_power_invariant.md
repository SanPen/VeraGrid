# Inverse Clarke transform (power invariant)

### Purpose

This block reconstructs three-phase quantities from power-invariant `alpha-beta-0` components.

### Behavior

- Receives orthogonal stationary-frame components.
- Produces three-phase outputs.
- Inverts the power-invariant Clarke transform.

### Characteristics

- Must be paired with the power-invariant forward Clarke transform when exact scaling consistency is required.

## Characteristic equations

$$
\begin{bmatrix}
x_A \\
x_B \\
x_C
\end{bmatrix}
=
\sqrt{\frac{2}{3}}
\begin{bmatrix}
1 & 0 & \frac{1}{\sqrt{2}} \\
-\frac{1}{2} & \frac{\sqrt{3}}{2} & \frac{1}{\sqrt{2}} \\
-\frac{1}{2} & -\frac{\sqrt{3}}{2} & \frac{1}{\sqrt{2}}
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
| Input | `x_alpha` | Power-invariant alpha-axis component | model-dependent |
| Input | `x_beta` | Power-invariant beta-axis component | model-dependent |
| Input | `x_0` | Power-invariant zero-sequence component | model-dependent |
| Output | `x_A` | Phase-A reconstructed quantity | model-dependent |
| Output | `x_B` | Phase-B reconstructed quantity | model-dependent |
| Output | `x_C` | Phase-C reconstructed quantity | model-dependent |

## How to use it

- Use this block only with signals that were generated using the power-invariant Clarke transform convention.
