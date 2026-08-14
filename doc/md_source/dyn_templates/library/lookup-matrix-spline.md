# Lookup matrix (spline)

Lookup matrix (spline) interpolates a two-input surface using spline interpolation. Use it when you want a smoother mapped surface than linear interpolation provides.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First lookup input | model-dependent |
| Input | `yi2` | Second lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `matrix_K` | Stored lookup matrix | data object |
