# Park transform (dq0)

### Purpose

This block converts three-phase quantities into a rotating `dq0` frame using one electrical angle.

### Behavior

- Receives phase quantities and one angle.
- Produces `d`, `q`, and `0` components.
- Keeps explicit zero-sequence information while rotating the balanced part into the synchronous frame.

### Characteristics

- Useful when zero-sequence information matters.

## Characteristic equations

$$
\begin{bmatrix}
x_d \\
x_q \\
x_0
\end{bmatrix}
=
\begin{bmatrix}
\frac{2}{3}\cos\theta & \frac{2}{3}\cos\left(\theta - \frac{2\pi}{3}\right) & \frac{2}{3}\cos\left(\theta + \frac{2\pi}{3}\right) \\
-\frac{2}{3}\sin\theta & -\frac{2}{3}\sin\left(\theta - \frac{2\pi}{3}\right) & -\frac{2}{3}\sin\left(\theta + \frac{2\pi}{3}\right) \\
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
| Input | `theta` | Electrical angle of the rotating frame | rad |
| Output | `x_d` | d-axis rotating-frame component | model-dependent |
| Output | `x_q` | q-axis rotating-frame component | model-dependent |
| Output | `x_0` | Zero-sequence rotating-frame component | model-dependent |

## How to use it

- Use this block when the model must preserve zero-sequence information in the rotating frame.
