# VeraGrid IO, UI, And Setup

## Purpose

This document packages the main installation, file-operations, plugin, and user-interface guidance from the VeraGrid documentation.

## Installation

- VeraGrid can be installed as a Python package and also distributed in standalone-oriented forms.
- The GUI is launched from the `veragrid` entry point when properly installed.
- The engine can also be installed on its own for programmatic workflows.

## File Operations

- VeraGrid can load native project files and multiple industry formats.
- It supports import and export workflows for grid files and result files.
- CGMES-related workflows may involve multiple XML files or ZIP bundles.
- Result export can produce structured files such as zipped CSV bundles.

## Client And Server

- VeraGrid also supports client-server style remote execution workflows.
- In those workflows, the local GUI can issue remote instructions and later receive results.
- The AI assistant should treat remote execution as part of the supported simulation flow when the server mode is active.

## User Interface

- The schematic editor is the primary visual construction and inspection tool.
- The tabular editor is the primary bulk-editing tool.
- The time-series editor manages profile data and time events.
- The results and tabular-results views are the main output inspection surfaces.
- The console exposes in-GUI scripting and automation.
- Many GUI controls are explained through tooltips rather than only through long manuals.

## Profiles Importer

- Profile import accepts spreadsheet or CSV-like data and maps columns to objects.
- Assignment can be automatic by name, random, universal, or selection-based depending on the workflow.
- This importer is central when the user asks how to attach demand, generation, or other profiles to the network.

## Templates And Editors

- Template editors exist for wires, overhead lines, sequence lines, underground lines, and transformers.
- The overhead-line editor exposes impedance and admittance matrices and related conductor modeling details.

## Plugins

- VeraGrid supports plugins.
- Plugins extend behavior and can be installed through the supported plugin workflow.
- If the user asks whether VeraGrid can be extended, plugins are one of the standard answers.

## AI Guidance

- When the user asks where something is in the GUI, answer in terms of schematic view, tabular view, results view, settings, or importer workflows.
- When the user asks how to get data in or out, answer in terms of file loading, saving, export, profile import, and remote execution.
- When the user asks about automation inside the GUI, mention the console and scripting facilities.
