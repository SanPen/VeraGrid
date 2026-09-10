# VeraGrid Optimization And Planning

## Purpose

This document packages the main optimization and planning workflows described in the VeraGrid documentation.

Use it when the user asks about dispatch, transfer capacity, hosting capacity, or investment studies.

## Optimal Power Flow

- Optimal power flow computes an operating point subject to constraints and an explicit objective.
- VeraGrid supports linear and non-linear OPF workflows.
- OPF may include ramping, grouping, commitment-like options, contingencies, and hydro-related formulations depending on the configuration.
- Snapshot OPF and time-series OPF are both available.

## OPF Interpretation

- OPF is the relevant study when the user asks to optimize generator dispatch, minimize operating cost, enforce branch limits, or respect generator bounds.
- ACOPF or non-linear OPF is relevant when the user explicitly asks for AC-consistent optimization.
- Linear OPF is appropriate when the user asks for faster screening or planning-style optimization.

## Net Transfer Capacity

- Net transfer capacity workflows study feasible transfer between source and sink areas under operational constraints.
- VeraGrid supports both regular transfer-capacity studies and optimization-oriented NTC variants.
- These studies depend on compatible area definitions, inter-area branches, and transfer settings.

## Available Transfer Capacity

- ATC is the right workflow when the user asks how much extra transfer can be accommodated between areas.
- Time-series ATC is used when transfer capability must be assessed across many time steps.

## Optimal Net Transfer Capacity

- OPF NTC combines transfer-capacity concepts with an optimization formulation.
- It is useful when the user asks for an optimal transfer under constraints rather than only a screening-style ATC result.

## Nodal Hosting Capacity

- Nodal hosting capacity estimates how much extra injection can be accommodated at selected nodes.
- VeraGrid supports linear, non-linear, and CPF-based hosting-capacity methods depending on settings.
- Selected buses in the GUI are typically the target nodes for this study.

## Investment Evaluation

- Investment evaluation compares network investment alternatives or groups of alternatives.
- It can use several objective types, including power-flow, time-series power-flow, adequacy-related, and simplified dispatch-style formulations.
- This workflow depends on declared investment groups and a configured evaluation method.

## Planning Guidance

- Use OPF for operational optimization of a known system state.
- Use NTC or ATC for transfer-capacity studies between areas.
- Use nodal hosting capacity for additional injection or hosting questions at specific buses.
- Use investment evaluation for expansion planning or alternative-comparison questions.

## AI Guidance

- If the user asks for optimization without specifying a time horizon, snapshot OPF is the default interpretation.
- If the user mentions yearly operation, profiles, or evolving dispatch, time-series OPF, ATC time series, or reliability may be more relevant.
- If the user asks about where to add capacity, hosting-capacity or investment-evaluation studies are usually the correct direction.
