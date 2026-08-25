# EMT Floquet stability analysis

Floquet stability analysis is the small-signal stability method used when the steady state of an EMT simulation is **periodic** rather than constant. This is the normal situation for an AC network represented in the phase domain: voltages and currents in the `abc` frame are sinusoidal in steady state, so a conventional eigenvalue analysis around a constant operating point is not directly applicable.

In VeraGrid, EMT Floquet stability analysis is implemented in the `SmallSignalStabilityEmt` simulation module. The driver captures one steady-state limit cycle from the EMT solver, builds a matrix-free monodromy operator for that cycle, and computes the dominant Floquet multipliers with Arnoldi-type eigensolvers.

```{note}
Use this analysis after the EMT model has reached a periodic steady state. The result describes the stability of that periodic operating trajectory, not the response to an arbitrary large disturbance.
```

## When to use Floquet stability

Use EMT Floquet stability analysis when the system must be studied in the waveform or phase domain and the relevant operating point is periodic. Typical use cases include:

- phase-domain EMT models with sinusoidal `abc` steady-state quantities;
- converter-dominated systems where switching, controller, PLL, or filter interactions are represented in EMT form;
- unbalanced or three-phase models where the instantaneous waveforms should not be transformed into a constant synchronous-frame equilibrium;
- detection of poorly damped or unstable periodic modes around an EMT limit cycle.

Do not use it as a substitute for time-domain transient simulation after faults, switching events, or protection actions. Floquet analysis is a **local** stability analysis around a periodic orbit.

## Workflow

The VeraGrid EMT Floquet workflow is:

1. Run a power-flow calculation to initialise the network.
2. Configure the EMT simulation options, especially the integration method and time step.
3. Configure `SmallSignalStabilityEmtOptions`, including the target period and number of modes.
4. Run `SmallSignalStabilityEmtDriver`.
5. Inspect the Floquet multipliers, damping ratios, frequencies, and participation factors.

Internally, the driver performs the following steps:

1. Builds an `EmtProblemDae` from the grid and the available balanced or three-phase power-flow results.
2. Runs the `StructuralVectorizedSolver` from `t = 0` to `ss_assessment_time`.
3. Extracts the last `target_period` of the simulated trajectory.
4. Obtains a Floquet Jacobian evaluator from the EMT problem.
5. Builds a monodromy operator, either from LU-cached DAE Jacobians or from an explicit stack of per-step transition matrices if available.
6. Computes the selected Floquet multipliers.
7. Maps the multipliers to continuous-time Floquet exponents and stores engineering metrics in `SmallSignalStabilityEmtResults`.

## Settings

The Floquet-specific settings are defined in `SmallSignalStabilityEmtOptions`.

### Main settings

| Option | Default | Description |
|---|---:|---|
| `k` | `6` | Number of Floquet multipliers to compute and retain. |
| `target_period` | `0.02` | Period of the periodic orbit in seconds. For a 50 Hz grid, `T = 0.02 s`; for a 60 Hz grid, `T = 1/60 s`. |
| `target_frequency_hz` | `None` | Optional modal frequency to target. When provided in the standard Arnoldi path, VeraGrid keeps modes closest to the corresponding unit-circle multiplier. |
| `max_krylov_dim` | `30` | Nominal Krylov subspace dimension budget for each Arnoldi or restarted Block-Arnoldi cycle. |
| `ss_assessment_time` | `0.1` | EMT simulation time used before extracting the final limit cycle. This should be long enough for transients to decay. |
| `verbose` | `0` | Verbosity level. |
| `build_type` | `SmallSignalEmtBuildTypes.Arnoldi` | Solver strategy. Supported paths in the driver are `Arnoldi` and `HybridArnoldi`. |

### Restart and robustness options

These options are mainly used by the hybrid Block-Arnoldi path.

| Option | Default | Description |
|---|---:|---|
| `max_restarts` | `4` | Maximum number of explicit restart cycles. |
| `restart_tol` | `1e-6` | Relative residual tolerance for accepting Ritz pairs as converged. |
| `use_refined_ritz` | `True` | Uses refined Ritz vectors to improve restart quality. |
| `adaptive_restart` | `True` | Enables residual-stagnation detection and adaptive changes to block size or Krylov depth. |
| `stagnation_improve_ratio` | `0.90` | Residual-improvement threshold used to detect stagnation. |
| `stagnation_patience` | `2` | Number of restart cycles observed before declaring stagnation. |
| `deflation_tol` | `1e-12` | Singular-value threshold used to drop linearly dependent Arnoldi block vectors. |

### Performance options

| Option | Default | Description |
|---|---:|---|
| `prefer_ak_operator` | `True` | Prefer the explicit per-step state-transition stack `A_k` when the EMT backend exposes it. |
| `use_numba_kernels` | `True` | Use Numba-accelerated block propagation and orthogonalisation kernels when available. |
| `min_block_size` | `None` | Lower block-size limit for restarted Block-Arnoldi. If not set, the driver derives one from `k`. |
| `max_block_size` | `None` | Upper block-size limit for restarted Block-Arnoldi. |
| `max_krylov_dim_cap` | `None` | Upper cap for adaptive Krylov-dimension expansion. |

```{tip}
The ratio `target_period / time_step` should represent the intended number of EMT integration steps per period. For reproducibility, choose a time step that divides the period cleanly, for example `T / 200` or `T / 400`.
```

## Results

The main output is a `SmallSignalStabilityEmtResults` object. The result object reports both discrete-time Floquet quantities and continuous-time engineering quantities.

### Modes table

For `ResultTypes.Modes`, VeraGrid reports:

| Column | Meaning |
|---|---|
| `Mu Re` | Real part of the Floquet multiplier. |
| `Mu Im` | Imaginary part of the Floquet multiplier. |
| `\|Mu\|` | Multiplier magnitude. This is the direct unit-circle stability indicator. |
| `Damp Ratio` | Period-averaged damping ratio computed from the Floquet exponent. |
| `Freq [Hz]` | Modal frequency in Hz, computed from the imaginary part of the Floquet exponent. |

### Stability interpretation

Let `mu_i` be one Floquet multiplier.

| Condition | Interpretation |
|---|---|
| `abs(mu_i) < 1` for all modes | The periodic orbit is locally asymptotically stable. |
| `abs(mu_i) ≈ 1` | The mode is marginal or close to the numerical stability boundary. Inspect discretisation, spectral gaps, and physical interpretation. |
| `abs(mu_i) > 1` for any mode | The periodic orbit is locally unstable. |

The result method `report_stability()` reports the spectral radius,

```text
rho = max(abs(multipliers))
```

and classifies the case as stable if the spectral radius is below the driver tolerance used by the method.

### Participation factors

For `ResultTypes.ParticipationFactors`, VeraGrid reports a matrix indexed by state-variable names and mode labels. Each column is normalised so that the participations for one mode sum to one.

Participation factors are useful for identifying which EMT states contribute most to a critical Floquet mode. They should be interpreted as period-averaged modal indicators, not as instantaneous state sensitivities.

## Registered Result Properties

`SmallSignalStabilityEmtResults` registers the following result properties.

| Property | Type | Description |
|---|---|---|
| `multipliers` | `CxVec` | Floquet multipliers, i.e. eigenvalues of the monodromy map. |
| `right_vecs` | `CxMat` | Right eigenvectors or Ritz vectors associated with the retained multipliers. |
| `left_vecs` | `CxMat` | Left or dual eigenvectors used for participation-factor calculations. |
| `period` | `float` | Period `T` of the analysed limit cycle. |
| `eigenvalues` | `CxVec` | Continuous-time Floquet exponents, computed as `log(multipliers) / period`. |
| `damping_ratios` | `Vec` | Period-averaged damping ratios. |
| `conjugate_frequencies` | `Vec` | Modal frequencies in Hz. |
| `participation_factors` | `Mat` | Normalised state participation factors. |
| `stat_vars_array` | `StrVec` | State-variable names used as participation-factor row labels. |

## API

The following example shows the typical scripting pattern. The exact `EmtOptions` fields should follow the EMT simulation configuration used in the project; the Floquet-specific part is the `SmallSignalStabilityEmtOptions` and `SmallSignalStabilityEmtDriver` configuration.

```python
import VeraGridEngine.api as gce

from VeraGridEngine.Simulations.PowerFlow.power_flow_driver import (
    PowerFlowDriver,
    PowerFlowOptions,
)
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.small_signal_stability_emt_driver import (
    SmallSignalStabilityEmtDriver,
)
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.small_signal_stability_emt_options import (
    SmallSignalStabilityEmtOptions,
)
from VeraGridEngine.enumerations import DynamicIntegrationMethod, SmallSignalEmtBuildTypes

# 1. Load grid
# grid = gce.open_file("my_grid.veragrid")

# 2. Run power flow to initialise the EMT problem
pf_options = PowerFlowOptions(verbose=False)
pf_driver = PowerFlowDriver(grid=grid, options=pf_options)
pf_driver.run()
pf_results = pf_driver.results

# 3. Configure EMT time-domain integration
fn = float(grid.fBase)
period = 1.0 / fn
h = period / 200.0

emt_options = EmtOptions()
emt_options.time_step = h
emt_options.integration_method = DynamicIntegrationMethod.DaeTrapezoidal

# 4. Configure Floquet analysis
sss_options = SmallSignalStabilityEmtOptions(
    k=6,
    target_period=period,
    ss_assessment_time=10.0 * period,
    max_krylov_dim=30,
    build_type=SmallSignalEmtBuildTypes.Arnoldi,
    verbose=1,
)

# 5. Run EMT Floquet stability analysis
floquet_driver = SmallSignalStabilityEmtDriver(
    grid=grid,
    emt_options=emt_options,
    sss_options=sss_options,
    pf_results=pf_results,
)
floquet_driver.run()

results = floquet_driver.results

print(results.report_stability())
print(results.multipliers)
print(results.eigenvalues)
print(results.damping_ratios)
```

### Hybrid Block-Arnoldi configuration

For larger EMT models, use the hybrid Block-Arnoldi path.

```python
sss_options = SmallSignalStabilityEmtOptions(
    k=12,
    target_period=period,
    ss_assessment_time=20.0 * period,
    max_krylov_dim=80,
    build_type=SmallSignalEmtBuildTypes.HybridArnoldi,
    max_restarts=6,
    restart_tol=1e-6,
    use_refined_ritz=True,
    adaptive_restart=True,
    prefer_ak_operator=True,
    use_numba_kernels=True,
    verbose=1,
)
```

### Targeting a frequency band

The standard Arnoldi path can target modes close to a specific oscillation frequency.

```python
sss_options = SmallSignalStabilityEmtOptions(
    k=6,
    target_period=period,
    target_frequency_hz=120.0,
    build_type=SmallSignalEmtBuildTypes.Arnoldi,
)
```

The driver maps the requested frequency `f_target` to the unit-circle point

```text
sigma = exp(j 2 pi f_target T)
```

and selects the multipliers closest to `sigma` and its conjugate.

## Theory

### Periodic EMT steady state

A conventional small-signal analysis assumes a constant equilibrium. In an EMT simulation expressed in the `abc` frame, the steady-state voltages and currents are generally periodic. A perturbation around the periodic trajectory is therefore governed by a linear periodic system,

$$
\dot{\delta x}(t) = A(t) \delta x(t)
$$

with

$$
A(t + T) = A(t)
$$

where $T$ is the period of the limit cycle.

### Fundamental matrix and monodromy matrix

The fundamental matrix $M(t)$ maps an initial perturbation to its value at time $t$:

$$
\dot{M}(t) = A(t) M(t), \qquad M(0) = I
$$

$$
\delta x(t) = M(t) \delta x(0)
$$

The monodromy matrix is the state-transition matrix over one complete period:

$$
C_M = M(T)
$$

The eigenvalues of $C_M$ are the Floquet multipliers:

$$
C_M r_i = \mu_i r_i
$$

These multipliers determine the local stability of the periodic orbit.

### Stability criterion

The unit circle replaces the left-half $s$ plane used in continuous-time eigenvalue analysis:

$$
\rho(C_M) = \max_i |\mu_i|
$$

The periodic orbit is locally asymptotically stable when all retained physical multipliers lie inside the unit circle. If a multiplier lies outside the unit circle, the corresponding perturbation grows from one period to the next.

### From EMT DAE to periodic state matrix

An EMT model is commonly represented as a differential-algebraic system,

$$
\dot{x} = f(x, y, t)
$$

$$
0 = g(x, y, t)
$$

After linearisation and algebraic-variable elimination, the reduced state matrix is

$$
A(t) = f_x(t) - f_y(t) g_y(t)^{-1} g_x(t)
$$

where the Jacobians are evaluated along the periodic EMT trajectory. VeraGrid avoids explicitly forming this reduced matrix for each operation whenever possible; instead, it applies the equivalent one-period transition map through the EMT linear solver infrastructure.

### Floquet exponents, damping, and frequency

Floquet multipliers are discrete-time quantities. VeraGrid maps them to continuous-time Floquet exponents with

$$
\lambda_i = \frac{1}{T} \log(\mu_i)
$$

For

$$
\lambda_i = \alpha_i + j \beta_i
$$

VeraGrid reports

$$
\zeta_i = -\frac{\alpha_i}{\sqrt{\alpha_i^2 + \beta_i^2}}
$$

and

$$
f_i = \frac{|\beta_i|}{2\pi}
$$

The complex logarithm is multi-valued, so the reported frequency corresponds to the selected logarithm branch. Interpret high-frequency or aliased modes with the EMT time step and the target period in mind.

### Participation factors

For a multiplier $mu_i$, let $r_i$ and $l_i$ be the right and left eigenvectors of the monodromy matrix. VeraGrid computes participation factors from the bi-orthonormalised left/right vectors and normalises each mode column:

$$
p_{ki} \propto |r_{ki} l_{ki}|
$$

The result is a relative contribution of state $k$ to Floquet mode $i$. Because the underlying system is periodic, these factors describe modal participation over the selected reference period rather than an instantaneous modal decomposition at every time sample.

## Implementation notes

### Matrix-free monodromy operators

VeraGrid represents the monodromy map as a `scipy.sparse.linalg.LinearOperator`. This is important because the full monodromy matrix is generally dense and expensive to store for large EMT systems.

The implementation includes three operator paths:

| Operator | Purpose |
|---|---|
| `EmtFloquetOperator` | Standard vector-by-vector monodromy action with LU factorisation caching. |
| `BlockEmtFloquetOperator` | Block matrix-by-matrix monodromy action for Block-Arnoldi and Randomized Numerical Linear Algebra workflows. |
| `AkStackBlockEmtFloquetOperator` | Explicit product of per-step state-transition matrices `A_k` when the EMT backend exposes the transition stack. |

For the LU-cached paths, VeraGrid assembles or evaluates the augmented DAE Jacobian along the captured trajectory and stores sparse LU factorisations. Applying the operator to a perturbation then becomes a sequence of sparse triangular solves over one period.

### Standard Arnoldi path

The standard `Arnoldi` build type uses:

- a dense fallback when the number of states is small;
- ARPACK through `scipy.sparse.linalg.eigs` when the system is larger;
- sorting by multiplier magnitude when no target frequency is selected;
- optional selection of multipliers closest to a requested target-frequency point on the unit circle.

### Hybrid Block-Arnoldi path

The `HybridArnoldi` build type is intended for larger EMT cases. It uses:

- block operator applications;
- Block Modified Gram-Schmidt orthogonalisation;
- rank-revealing SVD deflation;
- refined Ritz vectors when requested;
- restarts seeded from previously selected Ritz or refined vectors;
- adaptive block-size or Krylov-depth changes when residual stagnation is detected.

### Numba kernels

When available, VeraGrid can use Numba kernels for two performance-sensitive operations:

- block Modified Gram-Schmidt with optional re-orthogonalisation;
- block propagation through an explicit `A_k` transition stack.

The code falls back to NumPy/SciPy paths when Numba is not available.

## Practical notes

### Choose the period carefully

For a fundamental-frequency periodic orbit,

$$
T = 1 / f_base
$$

For a 50 Hz system, $T = 0.02 s$. For a 60 Hz system, $T = 0.016666... s$.

If the EMT model includes a different dominant periodicity, such as a controller or switching pattern that requires several fundamental cycles to repeat, set `target_period` to the full repeat period of the trajectory being analysed.

### Check that the captured trajectory is periodic

The final period extracted by the driver should represent a settled limit cycle. If the waveform has not settled, the resulting multipliers describe the linearisation of a non-periodic segment and should not be interpreted as Floquet stability indicators.

Increase `ss_assessment_time` when:

- the EMT transient has not decayed;
- the system has slow controls;
- the final period depends noticeably on the simulation start time;
- the largest multipliers change significantly when the assessment time is increased.

### Interpret near-unit multipliers with tolerance

Multipliers very close to the unit circle can be physical, numerical, or both. Before concluding that a system is marginally stable, check:

- EMT time-step sensitivity;
- period selection;
- Arnoldi residuals;
- spectral gap isolation;
- whether the mode is a physical symmetry or a modelling artefact.

`SmallSignalStabilityEmtResults.validate_spectral_gaps(h_step)` can be used to inspect whether the computed multipliers are sufficiently isolated relative to the integration-step scale.

### Floquet analysis versus ERA Matrix Pencil

VeraGrid also includes an ERA/Matrix Pencil EMT modal-extraction workflow. The two tools answer related but different questions:

| Tool | Input | Main output | Interpretation |
|---|---|---|---|
| EMT Floquet stability | Periodic EMT trajectory and EMT Jacobian information | Floquet multipliers of the one-period transition map | Model-based local stability of a periodic orbit. |
| ERA Matrix Pencil EMT | Ringdown time-series data | Identified continuous-time poles and residues | Signal-based modal identification from simulated observations. |

Use Floquet analysis when the objective is stability of the EMT periodic orbit. Use ERA/Matrix Pencil when the objective is modal extraction from measured or simulated ringdown signals.

## References

1. G. Floquet, “Sur les équations différentielles linéaires à coefficients périodiques,” 1883.
2. V. A. Yakubovich and V. M. Starzhinskii, *Linear Differential Equations with Periodic Coefficients*, 1975.
3. H. Sandberg and M. Molinas, “Floquet theory for stability analysis of periodic power system models,” *IEEE Transactions on Power Systems*, 2013.
4. Y. Saad, *Numerical Methods for Large Eigenvalue Problems*, 2nd edition, SIAM, 2011.
5. F. Milano, *Power System Modelling and Scripting*, Springer, 2010.
6. N. Watson and J. Arrillaga, *Power Systems Electromagnetic Transients Simulation*, 2nd edition, IET, 2019.
