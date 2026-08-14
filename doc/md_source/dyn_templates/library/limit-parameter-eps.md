# Limit (parameter) eps

This Limit variant uses a stored limit definition together with an epsilon tolerance. Use it when the bound data is packaged as one parameter object or value set.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Signal to limit | model-dependent |
| Output | `yo` | Limited output | same as `yi` |
| Parameter | `eps` | Small tolerance around the limit transition | same as `yi` |
| Parameter | `y_lim` | Stored limit definition | same as `yi` |
