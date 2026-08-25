# Three-phase carrier sampled modulation

<!-- veragrid-block-introduction:start -->
**Three-phase carrier sampled modulation** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

## Purpose

Samples three modulation references at carrier half-period boundaries and retains the sampled values for use by switching logic.

## Configuration

- **Modulation A/B/C**: source DAE variables.
- **Sample mode A/B/C**: retained sampled outputs.
- **Switching frequency**: runtime angular frequency in radians per second.
- **Carrier phase**: runtime phase offset.

## Runtime behavior

Samples are updated only at carrier boundaries and remain constant between them. The logic requests those boundaries from the solver. Place it before a PWM entry that consumes the sampled modes during the same accepted update.
