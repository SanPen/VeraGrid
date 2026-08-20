# El. Power

<!-- veragrid-block-introduction:start -->
**El. Power** derives a control or monitoring quantity from electrical signals. Measurement blocks may calculate RMS magnitude, active/reactive power, frequency, or filtered values; their window and sign conventions determine delay and interpretation downstream.

## Typical use

- Use it to provide physically meaningful feedback signals to protection and control blocks.
- Check scaling, sign, averaging window, and phase convention before connecting the result.
<!-- veragrid-block-introduction:end -->

El. Power converts generator-side quantities into an electrical power output using the configured base information. Use it when the model needs a direct electrical power signal from `pgt` and `cosn`.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `pgt` | Input power-related quantity | model-dependent |
| Input | `cosn` | Power-factor-related input | model-dependent |
| Output | `pelec` | Electrical power output | power |
| Parameter | `IPB` | Configured base or scaling value | model-dependent |
