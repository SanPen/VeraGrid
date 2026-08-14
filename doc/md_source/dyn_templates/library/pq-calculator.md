# PQ Calculator

PQ Calculator computes active and reactive power from real and imaginary voltage and current components. Use it when complex electrical quantities are already available in rectangular form.

$$
P = ur \cdot ir + ui \cdot ii
$$

$$
Q = ui \cdot ir - ur \cdot ii
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `ur` | Real voltage component | V or model-dependent |
| Input | `ui` | Imaginary voltage component | V or model-dependent |
| Input | `ir` | Real current component | A or model-dependent |
| Input | `ii` | Imaginary current component | A or model-dependent |
| Output | `P` | Active power | W or model-dependent |
| Output | `Q` | Reactive power | var or model-dependent |
