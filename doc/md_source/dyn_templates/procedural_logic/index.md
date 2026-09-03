# Runtime procedural logic

Procedural logic runs at accepted simulation boundaries, outside the continuous DAE residual evaluation. It reads the accepted state, runtime parameters and simulation time, and may update retained modes or explicitly mutable targets before the next solve.

The order shown in the editor is the execution order inside each owning block. If one entry reads a mode written by another entry, place the writer first unless a one-step delay is intentional.

## Retained modes

A retained mode is a runtime parameter with an initialization expression. Its value survives between accepted steps. Most procedural entries write one or more modes; DAE equations can read them like any other symbolic parameter.

## Available types

```{toctree}
:maxdepth: 1

fixed_sample
sampled_value
hard_saturation
time_delay
moving_average
gradient_limiter
conditional_diagnostic
delayed_switch_event
flipflop
analog_flipflop
pickup_dropoff
reset_on_rising_edge
delayed_threshold_latch
startup_handover
valve_state
three_phase_carrier_pwm
three_phase_carrier_sampled_modulation
```

Use **Validate runtime logic** before applying. Validation checks names, references, expressions, missing modes, duplicate writers and order-dependent reads.
