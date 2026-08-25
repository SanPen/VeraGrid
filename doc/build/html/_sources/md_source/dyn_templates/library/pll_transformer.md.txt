# PLL transformer

<!-- veragrid-block-introduction:start -->
**PLL transformer** belongs to the synchronization layer of a power-system controller. A phase-locked loop compares a measured voltage reference with an internally generated angle, filters the phase error, and integrates the resulting frequency correction. It lets grid-following controls express currents and voltages in a rotating frame aligned with the network.

## Typical use

- Use it when a controller must track grid angle and frequency rather than establish them.
- Check loop bandwidth and damping against grid strength; an aggressive PLL can amplify disturbances or interact with converter current control.
<!-- veragrid-block-introduction:end -->

The PLL transformer is a composite RMS control block that estimates a rotating
reference frame from the terminal-voltage magnitude and angle. It exposes the
direct and quadrature voltage components together with the estimated angle and
frequency used by downstream converter controls.

## Internal composition

The packaged block contains three connected children:

- **Phase Detector**, which transforms `Vm` and `Va` into `vd` and `vq` using
  the estimated angle.
- **Loop filter**, a PI transfer-function block driven by the phase error and
  producing `omega`.
- **VCO**, which integrates the frequency deviation to obtain `theta`.

The repeated symbols visible in the child blocks are connected through shared
references; they are not independent copies.

## Characteristic equations

$$
v_d = V_m \sin(V_a - \theta)
$$

$$
v_q = V_m \cos(V_a - \theta)
$$

$$
\frac{d\theta}{dt} = 2\pi f_n(\omega - 1)
$$

The loop filter uses `Kp_pll` and `Ki_pll` to drive the phase error toward zero.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `Vm` | Measured terminal-voltage magnitude | pu |
| Input | `Va` | Measured terminal-voltage angle | rad |
| Output | `vd` | Direct-axis voltage in the estimated frame | pu |
| Output | `vq` | Quadrature-axis voltage in the estimated frame | pu |
| Output | `theta` | Estimated synchronous angle | rad |
| Output | `omega` | Estimated electrical frequency | pu |
| Parameter | `Kp_pll` | Proportional PLL gain | pu/pu |
| Parameter | `Ki_pll` | Integral PLL gain | pu/(pu s) |
| Parameter | `fn` | Nominal electrical frequency | Hz |

## How to use it

- Connect `Vm` and `Va` to the RMS terminal measurements.
- Use `theta` for dq transformations and `omega` for frequency-dependent control.
- Tune `Kp_pll` and `Ki_pll` together; excessively aggressive values can create
  oscillatory angle estimates.
- An output checkbox only controls whether a variable is exported outside this
  block. It does not change the variable's algebraic or state role.
