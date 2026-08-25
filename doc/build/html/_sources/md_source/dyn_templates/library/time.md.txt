# time

<!-- veragrid-block-introduction:start -->
**time** generates or evaluates a deterministic time waveform. Waveform blocks provide repeatable references and disturbances for controller tests, EMT source profiles, and event-sequence validation.

## Typical use

- Use it to apply controlled steps, ramps, periodic signals, clocks, or test trajectories.
- Choose amplitude, offset, phase, start time, and frequency consistently with simulation units.
<!-- veragrid-block-introduction:end -->

`time` outputs the current simulation time. Use it when downstream logic needs direct access to elapsed model time.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Output | `yo` | Current simulation time | s |
