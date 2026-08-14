# Lookup matrix object (linear)

Lookup matrix object (linear) interpolates a two-input surface from a stored matrix object using linear interpolation. Use it when the table data is managed as a reusable object.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First lookup input | model-dependent |
| Input | `yi2` | Second lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `omatrix_K` | Stored lookup-matrix object | data object |
