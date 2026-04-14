# VeraGrid Development And Debugging

## Purpose

This document packages the main development and debugging guidance from the VeraGrid documentation into a concise AI-facing reference.

## Development Workflow

- VeraGrid has a normal source-based contribution workflow with Git.
- Development includes repository setup, contribution practices, and automated testing.
- The project uses pytest-based testing workflows.

## Model Debugging

- Inputs analysis is the first-line debugging study for suspicious model data.
- Diagnostics and analysis views in the GUI help identify outliers and inconsistent parameters.
- Many simulation problems are caused by model prerequisites not being satisfied rather than by numerical bugs alone.

## Typical Debugging Heuristics

- If a power flow fails, check slack definition, generator support, controls, and suspicious branch data.
- If a time-series study fails, check that the grid actually has time data and compatible profiles.
- If a short-circuit or dynamic study fails, check that the necessary prerequisite study has already been run.
- If a contingency or investment study fails, check that the required contingency or investment groups exist.
- If nodal hosting capacity fails, check that buses are selected when the study expects selected target nodes.

## Results And Validation

- A missing results object usually means the study did not complete successfully or prerequisites were missing.
- The assistant should not invent results or claim a study succeeded if VeraGrid does not expose a result set.
- If VeraGrid reports a study as unavailable or not loaded, the assistant should state that plainly.

## Engineering And Implementation Boundary

- For users asking engineering questions, prioritize the loaded model and study prerequisites.
- For users asking implementation questions, it is appropriate to mention drivers, results, session state, and GUI actions.
- If the user asks for developer guidance, it is reasonable to mention pytest, repository contribution workflow, and source-level extension points.
