# Lookup array object (spline)

Lookup array object (spline) interpolates from a stored one-dimensional lookup object using spline interpolation. Use it when you want a smoother curve than piecewise linear interpolation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
