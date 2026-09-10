# VeraGrid Modeling And Topology

## Purpose

This document packages the key modeling and topology ideas from the VeraGrid documentation into retrieval-friendly guidance for the AI assistant.

## Modeling Scope

- VeraGrid models buses, loads, generators, shunts, measurements, transformers, lines, switches, HVDC links, VSCs, and many supporting templates and metadata objects.
- Modeling can be positive-sequence, three-phase, AC, DC, or mixed AC-DC depending on the device set and study.

## Branch And Line Modeling

- Lines can be defined from direct electrical parameters or from template and wire configurations.
- Overhead-line modeling can be built from wire geometry and bundled conductors.
- Underground and sequence-line templates are also supported.
- Branch templates are intended to make parameter assignment consistent and reusable.

## Transformer Modeling

- Transformer models include short-circuit and pi-model style interpretations.
- Vector groups, taps, and clock notation matter for transformer behavior.
- Transformer controls may participate in power-flow control depending on solver and configuration.

## Load And Shunt Modeling

- Load and shunt modeling can involve constant impedance, constant current, and constant power behavior.
- Three-phase and unbalanced load definitions are supported in the appropriate workflows.

## Generator And Converter Modeling

- Generators provide injections and can participate in voltage and reactive-power controls.
- HVDC and VSC devices are used for AC-DC and converter-based modeling.
- Converter controls can include AC-side, DC-side, active-power, reactive-power, and voltage-oriented modes depending on the formulation.

## Data Models

- VeraGrid has a broad catalog of editable power-system objects.
- Common user-facing objects include buses, lines, transformers, loads, generators, shunts, switches, substations, voltage levels, contingencies, investments, and measurements.
- The data-model catalog is much broader and also includes CGMES-oriented object types.

## Topology Processing

- Topology processing reduces problematic connectivity, identifies electrical islands, simulates islands independently when required, and reassembles the system results.
- The assistant should recognize that topology processing is important when the user asks about isolated islands, breaker-and-node style connectivity, or non-simulatable fragments.

## Grid Reduction

- VeraGrid includes grid-reduction methods such as Ward-style, Di-Shi, and PTDF-oriented reductions.
- Grid reduction is appropriate when the user asks for equivalencing, network simplification, or retaining external-system effects in a smaller model.

## AI Guidance

- For modeling questions, answer in terms of physical devices, controls, templates, and topology rather than code internals.
- For topology questions, emphasize islands, connectivity, branch filtering, and simulatable sub-networks.
- For questions about importing CGMES-like structures, it is correct to say that the object catalog is broader than the standard editing set used in daily GUI workflows.
