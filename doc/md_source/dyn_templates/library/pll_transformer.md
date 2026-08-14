# Pll transformer

Phase-locked-loop transform block used in RMS control chains.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `v_abc` | Measured phase voltages | pu |
| Output | `theta` | Estimated synchronous angle | rad |
| Output | `omega` | Estimated electrical frequency | pu |
| Parameter | `Kp` | Proportional PLL gain | model-dependent |
| Parameter | `Ki` | Integral PLL gain | model-dependent |
