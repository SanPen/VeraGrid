# Deadband stepped (bypass)

Deadband stepped (bypass) suppresses small variations and then resumes with stepped behavior once the input leaves the dead zone. Use it when threshold crossings should create a clearer discrete response.

## Interface table

| Category | Name | Meaning | Units |
| --- | --- | --- | --- |
| Input | `yi` | Input signal | model-dependent |
| Output | `yo` | Stepped deadband output | same as `yi` |
| Parameter | `db` | Deadband width | same as `yi` |
