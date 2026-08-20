# yi1 greater than yi2 eps

<!-- veragrid-block-introduction:start -->
**yi1 greater than yi2 eps** belongs to the hybrid/event layer of a dynamic model. It selects, stores, delays, or switches signals according to conditions, so its result depends on discrete mode or accepted simulation history in addition to the instantaneous continuous variables.

## Typical use

- Use it for protection, enable/disable sequences, sampled control, reset logic, and mode transfer.
- Define initial mode and boundary behavior explicitly to avoid unintended event chattering.
<!-- veragrid-block-introduction:end -->

`yi1 greater than yi2 eps` outputs true when the first signal exceeds the second by more than `eps`.

$$
yo = (yi1 > yi2 + eps)
$$

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi1` | First signal | model-dependent |
| Input | `yi2` | Second signal | model-dependent |
| Output | `yo` | Comparison result | boolean or logical flag |
| Parameter | `eps` | Comparison margin | model-dependent |
