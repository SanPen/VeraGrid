# Three-phase carrier PWM

<!-- veragrid-block-introduction:start -->
**Three-phase carrier PWM** represents a power-electronic conversion or modulation function. Converter models translate control references into AC/DC electrical quantities, while averaged and switched variants retain different levels of switching detail and therefore require different simulation time steps.

## Typical use

- Use averaged models for control and system studies, and switched models when waveform detail matters.
- Coordinate reference frames, modulation limits, DC-side energy, and current-control bandwidth.
<!-- veragrid-block-introduction:end -->

## Purpose

Generates three retained gate signals by comparing phase modulation references with a triangular switching carrier.

## Configuration

- **Modulation A/B/C**: DAE modulation references.
- **Gate mode A/B/C**: retained gate outputs.
- **Switching frequency**: runtime angular frequency in radians per second.
- **Carrier phase**: runtime phase offset.

## Runtime behavior

The logic clips modulation references to the carrier range, schedules within-half-cycle switching instants and requests exact event boundaries. A near-zero switching frequency freezes the carrier on a very long interval. All three gate modes are written by this single entry.

## Library block

The standalone block exposes three modulation inputs and three gate outputs. `switching_frequency` defaults to `2π·1000` radians per second and `carrier_phase` defaults to `0.0`.
