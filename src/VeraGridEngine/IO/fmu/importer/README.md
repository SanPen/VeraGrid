# VeraGrid FMU Import

This package owns FMU archive validation, declarative device persistence, typed
worker communication, and solver-agnostic FMI lifecycle coordination. Imported
models remain data: no import or persistence path generates, evaluates, or
dynamically imports source code.

## Ownership

- `device_config.py` owns the versioned Co-Simulation and Model Exchange device
  records. Version 4 persists `maximum_event_iterations` explicitly; only
  versions 1 through 3 synthesize the compatibility default of 32.
- `runtime_protocol.py`, `runtime_worker.py`, `runtime_worker_host.py`, and
  `runtime_session.py` own typed, bounded FMI 3 process communication.
- `runtime_coordinator.py` is the sole owner of the FMI 3 Model Exchange
  accepted/candidate transaction, optional native checkpoint, exact visible
  reconstruction, Event Mode fixpoint, and time-event request.
- `model_exchange.py` owns the device adapters, endpoint-domain detection,
  Backward Euler residual solve, per-indicator state-event localization, and
  cross-participant RMS orchestration.
- `emt_boundary.py` connects the same adapter transaction to the
  solver-independent EMT boundary protocol.
- RMS and EMT simulations own step-size selection, retry, and the integration
  policy. Attached Model Exchange devices currently require the simulation to
  select `DynamicIntegrationMethod.DaeBackEuler`; Co-Simulation never advances
  past an earlier Model Exchange event.

GUI or Qt code must not enter this layer. A second coordinator, callback table,
or generated-source model would duplicate an existing owner. The FMI ME Newton
and resource limits are persisted Engine options with stable defaults; the GUI
does not expose separate controls for them.

## FMI 3 Model Exchange transaction

1. Initialization settles Event Mode and captures the complete visible accepted
   point. When the FMU declares `canGetAndSetFMUState`, the coordinator also
   saves one native checkpoint.
2. The simulation-owned Backward Euler solver prepares one bounded candidate.
   Endpoint event-indicator domains use
   `z > 0` versus `z <= 0`, so exact zero is non-positive.
3. When an endpoint domain changes, each crossing indicator retains its own
   bracket. Every midpoint is evaluated through a shortened Backward Euler
   solve, after which the importer selects the global earliest supported event,
   restores every participant, and asks the simulation to retry.
4. Acceptance performs `completedIntegratorStep` only when the FMU requires it,
   enters Event Mode when required, settles its bounded fixpoint, and replaces
   the optional native checkpoint.
5. Rejection restores the checkpoint when available. Without checkpoints, the
   coordinator reconstructs time, states, inputs, derivatives, outputs, and
   indicators at the visible accepted point and terminates on any exact
   mismatch. It never attempts rollback after an irreversible native call.

`maximum_event_iterations` accepts exact non-Boolean integers in `[1, 1024]`
and defaults to 32. It is independent of the RMS/EMT localization iteration
bound and event-time tolerance.

A defined FMI `nextEventTime` must be finite and strictly greater than the
exact Event Mode entry time. That reference is the simulation start during
initialization and the candidate time during accepted-step settlement.

## State-event envelope and numerical bounds

Backward Euler uses the residual `x_(n+1) - x_n - h*f(t_(n+1), x_(n+1), u_n)`
and a dense forward-difference Jacobian. Convergence scales each residual with
`absolute_tolerance + relative_tolerance * max(abs(x_n), abs(x_(n+1)))`.
The persisted Engine defaults are `1e-8` for both scales, 20 Newton updates,
128 continuous states, and 100000 runtime-boundary evaluations per simulation
step. The corresponding accepted ranges are positive finite scales, 1 through
100 Newton updates, 1 through 128 states, and 1 through 10000000 evaluations.
These are deterministic Engine policy values rather than FMI-standard GUI
parameters.

The earliest-event guarantee applies only when both endpoint times are finite,
their subtraction is finite and strictly positive, every indicator has at most
one transition inside the interval, and the configured bisection bound can
meet the effective tolerance. A model capable of repeated interior transitions
requires a smaller solver step; adaptive subdivision and dense output are out
of scope.

Localization uses an effective tolerance equal to the configured positive
finite tolerance or a 16-ULP time-scale floor, whichever is larger. Exact
`frexp` preflight proves the required iteration count before the first probe.
Every midpoint is computed as the lower endpoint plus half the finite width,
which remains safe for supported same-sign extreme times. Opposite-sign finite
endpoints whose subtraction overflows are rejected before probing.

One fixed-size mutable state list is allocated per localization and reused.
For a participant with positive state cardinality, each worker probe receives a
new immutable state tuple. A valid event-only FMU with zero continuous states
passes the canonical empty tuple and remains supported. One monotonic budget is
created per initialization or simulation step and shared by every adapter,
Newton residual, Jacobian probe, localization midpoint, rejection, and retry.
Each runtime-boundary invocation consumes its unit before the native call.

## Exclusions

FMI Scheduled Execution, FMU re-instantiation or replay rollback, adaptive
subdivision, dense solver output, GUI ownership, new third-party dependencies,
global process state, and generated source representations are outside this
package contract. Hidden-state reconstruction for an FMU without native state
support is also outside the contract; only exact reconstruction of the visible
accepted point is permitted.
