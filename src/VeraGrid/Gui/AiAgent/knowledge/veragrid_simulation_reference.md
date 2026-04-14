# VeraGrid Simulation Reference

## Purpose

This document packages the main study descriptions from the VeraGrid simulation documentation into concise AI-facing guidance.

Use it when the user asks what a study does, what prerequisites it has, or which study should be run next.

## Power Flow

- Power flow is the base steady-state study for voltages, injections, branch flows, and losses.
- VeraGrid supports multiple solver formulations and control options.
- Power flow is often the prerequisite for downstream studies such as short circuit, RMS, EMT, and some stability workflows.
- A power flow may use GUI options such as solver choice, tolerances, control flags, slack distribution, and initialization options.

## Three-Phase Power Flow

- VeraGrid supports three-phase unbalanced power-flow workflows.
- This is the correct study when the user explicitly asks for phase-domain or unbalanced analysis.
- Three-phase results are distinct from positive-sequence snapshot power-flow results.

## Linear Analysis

- Linear analysis provides PTDF-like approximations and sensitivity-style insights.
- It is useful for screening, fast transfer studies, and contingency-related workflows.
- VeraGrid also supports time-series linear analysis.

## Contingency Analysis

- Contingency analysis evaluates predefined contingency groups.
- It can run in snapshot or time-series mode.
- It depends on declared contingency groups and can use different contingency engines or filtering modes.

## Continuation Power Flow

- Continuation power flow is the voltage-stability workflow.
- It traces the loading path and is used to study collapse margins, nose points, and overload-driven stopping criteria.
- It is the right study when the user asks about voltage-collapse margins or voltage-stability limits.

## Short Circuit

- Short circuit uses fault definitions and typically depends on a prior power-flow state for initialization.
- VeraGrid supports multiple fault types such as single-line-to-ground, line-to-line, double-line-to-ground, and three-phase faults.
- If the user asks for fault current, short-circuit levels, or faulted-bus currents, short circuit is the relevant study.

## State Estimation

- State estimation uses measurements to reconstruct the most likely system state.
- It is the right study when the user asks about using PMU or SCADA-like measurements or reconciling noisy measurements with the network state.

## Stochastic Power Flow

- Stochastic power flow uses probabilistic sampling over uncertain inputs and usually relies on time-series data.
- It is appropriate for Monte Carlo or Latin-hypercube style analyses.

## Clustering

- Clustering reduces a long time horizon into representative time steps.
- It is primarily a preprocessing or acceleration study for time-series analyses.
- If clustering is enabled, later time-series studies may use clustered time indices rather than the full time series.

## Inputs Analysis

- Inputs analysis is a model-debugging and inspection study.
- It is used to inspect distributions and outliers in the network input data.
- When the user asks to check data quality or suspicious parameter ranges, inputs analysis is often relevant.

## Reliability

- Reliability studies require time data.
- They can be oriented toward adequacy or grid metrics depending on the chosen reliability mode.
- If the user asks about probabilistic service continuity or adequacy across time, reliability is the relevant study.

## Sigma Analysis

- Sigma analysis is a specialized voltage-stability style inspection workflow.
- It is often presented through its own dialogue and result visualization.
- If the user asks for sigma coefficients or sigma plots, this is the relevant command.

## Node Groups

- Node-groups analysis works with PTDF-related information to group buses or nodes.
- It is useful for sensitivity-based grouping or regional structure detection.
- It typically depends on linear-analysis results being available first.

## Dynamic RMS And EMT

- Dynamic RMS simulation is the dynamic phasor-domain workflow.
- Dynamic EMT simulation is the electromagnetic-transient workflow.
- Both usually require a prior initialized power-flow state.
- If the user asks for dynamic time-domain trajectories, transient responses, or controller dynamics, RMS or EMT are the relevant studies.

## Small-Signal Stability

- Small-signal stability studies analyze the linearized dynamic behavior around an operating point.
- VeraGrid supports RMS and EMT small-signal variants.
- A prior power-flow solution and relevant initialization data are typically needed.

## Practical Study Selection

- Use power flow for steady-state voltages and flows.
- Use three-phase power flow for unbalanced feeders and phase-domain studies.
- Use short circuit for fault currents and fault studies.
- Use continuation power flow or sigma analysis for voltage-stability questions.
- Use linear analysis and contingency analysis for fast transfer and outage screening.
- Use reliability, stochastic power flow, and time-series studies when time dependence matters.
- Use RMS, EMT, or small-signal studies for dynamic behavior.
