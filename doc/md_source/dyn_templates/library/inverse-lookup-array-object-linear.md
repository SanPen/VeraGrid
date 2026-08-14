# Inverse Lookup array object (linear)

Inverse Lookup array object (linear) maps an input back through a stored one-dimensional lookup object using linear interpolation. Use it when you need the inverse of a tabulated nonlinear relation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input value to invert through the table | model-dependent |
| Output | `yo` | Interpolated inverse lookup result | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
