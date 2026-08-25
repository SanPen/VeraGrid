# Inverse Park transform (dq)

<!-- veragrid-block-introduction:start -->
**Inverse Park transform (dq)** is a coordinate-transformation block. In three-phase analysis, Clarke and Park transforms separate stationary or rotating components so sinusoidal phase quantities can be controlled as nearly constant d-q signals. The selected scaling determines whether amplitude or instantaneous power is preserved.

## Typical use

- Use it to connect phase-domain electrical quantities with d-q or sequence-domain control laws.
- Keep angle orientation, axis alignment, phase order, and power/amplitude convention consistent.
<!-- veragrid-block-introduction:end -->

### Purpose

This block reconstructs three-phase quantities from rotating-frame `dq` components.

### Behavior

- Receives `d`, `q`, and one electrical angle.
- Produces three-phase outputs.
- Is used to convert synchronous-frame controller outputs back into phase-domain commands.

### Characteristics

- Appropriate when zero-sequence is not part of the signal model.

## Characteristic equations

$$
\begin{bmatrix}
x_A \\
x_B \\
x_C
\end{bmatrix}
=
\begin{bmatrix}
\cos\theta & -\sin\theta \\
\cos\left(\theta - \frac{2\pi}{3}\right) & -\sin\left(\theta - \frac{2\pi}{3}\right) \\
\cos\left(\theta + \frac{2\pi}{3}\right) & -\sin\left(\theta + \frac{2\pi}{3}\right)
\end{bmatrix}
\begin{bmatrix}
x_d \\
x_q
\end{bmatrix}
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `x_d` | d-axis rotating-frame component | model-dependent |
| Input | `x_q` | q-axis rotating-frame component | model-dependent |
| Input | `theta` | Electrical angle of the rotating frame | rad |
| Output | `x_A` | Phase-A reconstructed quantity | model-dependent |
| Output | `x_B` | Phase-B reconstructed quantity | model-dependent |
| Output | `x_C` | Phase-C reconstructed quantity | model-dependent |

## How to use it

- Use this block to turn `dq` controller outputs into three-phase commands when zero-sequence is not used.
