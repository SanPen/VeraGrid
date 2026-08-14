# Lookup array 1x3 (linear variable)

Lookup array 1x3 (linear variable) interpolates between three x-y points supplied as input signals. Use it when the lookup points themselves must change during simulation.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Input | `arr_x1` | First x-coordinate input | same as `yi` |
| Input | `arr_x2` | Second x-coordinate input | same as `yi` |
| Input | `arr_x3` | Third x-coordinate input | same as `yi` |
| Input | `arr_y1` | Output value for `arr_x1` | same as `yo` |
| Input | `arr_y2` | Output value for `arr_x2` | same as `yo` |
| Input | `arr_y3` | Output value for `arr_x3` | same as `yo` |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `vClip` | Clipping control | boolean, 0/1, or model-dependent |
