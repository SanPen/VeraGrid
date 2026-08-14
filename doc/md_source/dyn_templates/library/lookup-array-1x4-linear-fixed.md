# Lookup array 1x4 (linear fixed)

Lookup array 1x4 (linear fixed) interpolates between four fixed x-y points stored as parameters. Use it when you need a compact piecewise-linear curve with four breakpoints.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Independent lookup input | model-dependent |
| Output | `yo` | Interpolated output | model-dependent |
| Parameter | `arr_x1` | First x-coordinate | same as `yi` |
| Parameter | `arr_x2` | Second x-coordinate | same as `yi` |
| Parameter | `arr_x3` | Third x-coordinate | same as `yi` |
| Parameter | `arr_x4` | Fourth x-coordinate | same as `yi` |
| Parameter | `arr_y1` | Output at `arr_x1` | same as `yo` |
| Parameter | `arr_y2` | Output at `arr_x2` | same as `yo` |
| Parameter | `arr_y3` | Output at `arr_x3` | same as `yo` |
| Parameter | `arr_y4` | Output at `arr_x4` | same as `yo` |
| Parameter | `vClip` | Clipping control | boolean, 0/1, or model-dependent |
