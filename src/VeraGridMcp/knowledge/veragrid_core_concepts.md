# VeraGrid Core Concepts

## Purpose

This document packages the main ideas from the VeraGrid user and structure documentation into AI-facing guidance.

The assistant should use these concepts when answering questions about how VeraGrid is organized and how users interact with a loaded project.

## Main Object Model

- A VeraGrid project is typically represented by a `MultiCircuit`.
- The `MultiCircuit` is the editable high-level network model used in the GUI and by many workflows.
- The `NumericalCircuit` is the compiled numerical form used by simulation engines.
- A driver represents a simulation execution.
- A results object stores the output of a simulation.

## Snapshot And Time Series

- VeraGrid distinguishes snapshot studies from time-series studies.
- Snapshot studies work on one operating point.
- Time-series studies use a time profile and can iterate over many time steps.
- Some studies can use clustering to reduce the effective number of simulated time steps.

## Runtime Interpretation Rules

- When the user says `the grid`, `the model`, or `the current project`, that usually refers to the loaded `MultiCircuit`.
- When the user asks what is selected, that refers to the devices or buses selected in the current diagram.
- When the user asks about a study, they may mean the active study in the results selector or one of the studies available in the session.

## Main Runtime Objects

- Buses are the network nodes.
- Branches connect buses and include lines, transformers, switches, reactances, HVDC links, and related branch-like equipment.
- Loads, generators, batteries, shunts, and measurements are attached to buses.
- Areas, zones, substations, voltage levels, and similar objects are organizational metadata over the network.

## GUI Structure

- The model view is where editing happens.
- The schematic editor is the main graphical construction and inspection view.
- The tabular editor is used for bulk editing of object properties.
- The time-series editor manages profiles and time-dependent data.
- The results view is used to inspect simulation outputs.
- The console and script tooling provide in-GUI automation.

## Search And Filtering

- Tabular and result views support advanced search queries.
- Query structure is based on subject, operation, and value.
- Common search subjects include value, column value, index value, and object-backed values.
- Search operators include numeric comparisons, equality, containment, and prefix or suffix matching.

## Diagnostics And Analysis

- VeraGrid includes analysis and diagnostics tooling to detect outliers and common data issues.
- Diagnostics help users identify invalid parameters, suspicious branch data, and other model-quality problems.
- When the user asks why a simulation may fail, diagnostics and model consistency checks are often relevant.

## Results Interpretation

- The schematic can be colored according to the latest available results.
- When multiple studies exist, the user can switch the active study and inspect different result sets.
- Time-dependent studies expose navigation over steps or timestamps.
- Numerical result tables mirror the graphical result view and are suitable for export or spreadsheet analysis.

## AI Guidance

- Prefer describing VeraGrid in terms of projects, studies, objects, drivers, and results.
- For engineering questions, answer in terms of the loaded model and available studies, not in terms of Python internals.
- For implementation questions, it is acceptable to refer to `MultiCircuit`, `NumericalCircuit`, drivers, and result objects explicitly.
