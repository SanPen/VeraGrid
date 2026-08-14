# Park transform (dq)

### Purpose

This block converts three-phase quantities into a rotating `dq` frame using one electrical angle.

### Behavior

- Receives phase quantities and one angle.
- Produces `d` and `q` components.
- Removes the oscillation associated with the rotating reference when the angle tracks the signal.

### Characteristics

- Used in synchronous-frame current, voltage, and power control.
- Omits the zero-sequence output.

## Characteristic equations

$$
\begin{bmatrix}
x_d \\
x_q
\end{bmatrix}
=
\begin{bmatrix}
\frac{2}{3}\cos\theta & \frac{2}{3}\cos\left(\theta - \frac{2\pi}{3}\right) & \frac{2}{3}\cos\left(\theta + \frac{2\pi}{3}\right) \\
-\frac{2}{3}\sin\theta & -\frac{2}{3}\sin\left(\theta - \frac{2\pi}{3}\right) & -\frac{2}{3}\sin\left(\theta + \frac{2\pi}{3}\right)
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

## How to use it

- Use this block when zero-sequence is not needed and a rotating two-axis representation is sufficient.
