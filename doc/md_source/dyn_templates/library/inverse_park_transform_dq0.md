# Inverse Park transform (dq0)

### Purpose

This block reconstructs three-phase quantities from rotating-frame `dq0` components.

### Behavior

- Receives `d`, `q`, `0`, and one electrical angle.
- Produces three-phase outputs.
- Preserves zero-sequence contribution in the reconstructed phase signals.

### Characteristics

- Useful in models where zero-sequence voltage or current is explicitly retained.

## Characteristic equations

$$
\begin{bmatrix}
x_A \\
x_B \\
x_C
\end{bmatrix}
=
\begin{bmatrix}
\cos\theta & -\sin\theta & 1 \\
\cos\left(\theta - \frac{2\pi}{3}\right) & -\sin\left(\theta - \frac{2\pi}{3}\right) & 1 \\
\cos\left(\theta + \frac{2\pi}{3}\right) & -\sin\left(\theta + \frac{2\pi}{3}\right) & 1
\end{bmatrix}
\begin{bmatrix}
x_d \\
x_q \\
x_0
\end{bmatrix}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `x_d` | d-axis rotating-frame component | model-dependent |
| Input | `x_q` | q-axis rotating-frame component | model-dependent |
| Input | `x_0` | Zero-sequence rotating-frame component | model-dependent |
| Input | `theta` | Electrical angle of the rotating frame | rad |
| Output | `x_A` | Phase-A reconstructed quantity | model-dependent |
| Output | `x_B` | Phase-B reconstructed quantity | model-dependent |
| Output | `x_C` | Phase-C reconstructed quantity | model-dependent |

## How to use it

- Use this block when zero-sequence must be preserved while converting `dq0` signals back into the phase domain.
