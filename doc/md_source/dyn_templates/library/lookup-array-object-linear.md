# Lookup array object (linear)

Lookup array object (linear) interpolates from a stored one-dimensional lookup object using linear interpolation. Use it when the table is managed as a reusable object rather than inline points.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
