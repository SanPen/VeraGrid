# Limit (parameter) [param: eps/y_min]

This Limit variant applies a fixed lower boundary and an epsilon tolerance. Use it when the lower bound is fixed and the upper side is handled elsewhere by the template.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance around the limit transition | same as `yi` |
| Parameter | `y_min` | Lower limit | same as `yi` |
