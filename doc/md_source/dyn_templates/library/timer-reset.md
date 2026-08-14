# Timer (reset)

Timer (reset) produces a timer output that restarts when the reset input is active. Use it for elapsed-time logic that must be cleared by an external reset signal.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `rst` | Reset signal | boolean, 0/1, or model-dependent |
| Output | `yo` | Timer output | s or model-dependent |
