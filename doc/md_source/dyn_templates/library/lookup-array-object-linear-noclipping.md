# Lookup array object (linear noclipping)

Lookup array object (linear noclipping) interpolates from a stored lookup object without clipping the input to the table range. Use it when the out-of-range behavior should follow the shipped template directly.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `oarray_K` | Stored lookup-array object | data object |
