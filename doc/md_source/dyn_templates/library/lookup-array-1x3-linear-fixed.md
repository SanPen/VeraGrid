# Lookup array 1x3 (linear fixed)

Lookup array 1x3 (linear fixed) interpolates between three fixed x-y points stored as parameters. Use it for small tabulated relationships that should be fully visible in the block parameters.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `arr_x1` | First x-coordinate | same as `yi` |
| Parameter | `arr_x2` | Second x-coordinate | same as `yi` |
| Parameter | `arr_x3` | Third x-coordinate | same as `yi` |
| Parameter | `arr_y1` | Output at `arr_x1` | same as `yo` |
| Parameter | `arr_y2` | Output at `arr_x2` | same as `yo` |
| Parameter | `arr_y3` | Output at `arr_x3` | same as `yo` |
| Parameter | `vClip` | Clipping control | boolean, 0/1, or model-dependent |
