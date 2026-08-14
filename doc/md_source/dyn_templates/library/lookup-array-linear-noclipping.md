# Lookup array (linear noclipping)

Lookup array (linear noclipping) interpolates from a one-dimensional table without clipping the input to the stored range. Use it when extrapolation or out-of-range handling should follow the template behavior instead of saturating.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `array_K` | Stored lookup array | data object |
