# PQ Calculator

<!-- veragrid-block-introduction:start -->
**PQ Calculator** derives a control or monitoring quantity from electrical signals. Measurement blocks may calculate RMS magnitude, active/reactive power, frequency, or filtered values; their window and sign conventions determine delay and interpretation downstream.

## Typical use

- Use it to provide physically meaningful feedback signals to protection and control blocks.
- Check scaling, sign, averaging window, and phase convention before connecting the result.
<!-- veragrid-block-introduction:end -->

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
