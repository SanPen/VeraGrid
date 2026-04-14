# VeraGrid Studies And Results

## Study Context

The current VeraGrid project may expose multiple studies or drivers inside the session.

The assistant should care about:

- active study
- list of available studies
- whether a driver exists for a requested study
- whether results are loaded

## Power Flow

For power-flow context, useful summary fields include:

- convergence state
- minimum voltage
- maximum voltage
- maximum branch loading
- elapsed time or iterations when available

## Time Series

For time-series power-flow context, useful summary fields include:

- number of time steps
- minimum voltage across the series
- maximum voltage across the series
- maximum branch loading across the series

## Result Communication Rules

- Distinguish clearly between model structure and simulation results.
- If only counts and object data are available, say that the answer is based on the loaded model structure.
- If result data is available, summarize the result data explicitly.
- If the active study is a design-view style context without results, say that there are no simulation results for that view.
