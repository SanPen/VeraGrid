# Clarke transform

### Purpose

This block converts three-phase `abc` quantities into stationary `alpha-beta-0` quantities using the classical non-power-invariant scaling.

### Behavior

- Receives phase quantities in `abc` form.
- Produces stationary-frame orthogonal components.
- Is commonly used ahead of Park transforms and stationary-frame analysis blocks.

### Characteristics

- Simpler scaling than the power-invariant version.
- Widely used in classical three-phase control derivations.

## Characteristic equations

$$
\begin{bmatrix}
x_\alpha \\
x_\beta \\
x_0
\end{bmatrix}
=
\begin{bmatrix}
\frac{2}{3} & -\frac{1}{3} & -\frac{1}{3} \\
0 & \frac{1}{\sqrt{3}} & -\frac{1}{\sqrt{3}} \\
\frac{1}{3} & \frac{1}{3} & \frac{1}{3}
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
| Output | `x_alpha` | Alpha-axis stationary component | model-dependent |
| Output | `x_beta` | Beta-axis stationary component | model-dependent |
| Output | `x_0` | Zero-sequence stationary component | model-dependent |

## How to use it

- Use this variant when the surrounding formulation assumes classical Clarke scaling rather than power invariance.
