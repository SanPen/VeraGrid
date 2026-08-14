# Limit (3 parameter inputs)

This complex Limit variant constrains `d` and `q` components using configured axis and magnitude limits, with an axis-priority input deciding which axis keeps precedence. Use it when a vector command must respect both individual-axis and overall-magnitude capability.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `d` | Direct-axis input | model-dependent |
| Input | `q` | Quadrature-axis input | model-dependent |
| Input | `PRIORITISE_AXIS` | Axis-priority selector | selector or boolean |
| Output | `yo_d` | Limited direct-axis output | same as `d` |
| Output | `yo_q` | Limited quadrature-axis output | same as `q` |
| Parameter | `D_MAX` | Maximum direct-axis value | same as `d` |
| Parameter | `Q_MAX` | Maximum quadrature-axis value | same as `q` |
| Parameter | `MAG_MAX` | Maximum vector magnitude | same as vector magnitude |
| Parameter | `D_MIN` | Minimum direct-axis value | same as `d` |
| Parameter | `Q_MIN` | Minimum quadrature-axis value | same as `q` |
