# Lookup matrix object (spline)

Lookup matrix object (spline) interpolates a two-input surface from a stored matrix object using spline interpolation. Use it when you need a smoother reusable 2D table.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First lookup input | model-dependent |
| Input | `yi2` | Second lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `omatrix_K` | Stored lookup-matrix object | data object |
