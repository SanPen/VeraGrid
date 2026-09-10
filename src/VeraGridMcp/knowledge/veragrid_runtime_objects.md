# VeraGrid Runtime Objects

## Core Project State

The active VeraGrid session provides:

- project name
- active study
- selected solver or engine
- counts of buses, branches, loads, and generators
- selected devices and selected buses
- available studies in the session

## Network Objects

### Buses

Buses are the main electrical nodes of the network.

Useful bus properties include:

- `name`
- `idtag`
- `code`
- `type_name`
- nominal voltage such as `Vnom`

### Branches

Branches connect buses.

Common branch context includes:

- branch name
- source bus
- destination bus
- branch type

### Loads

Loads are demand devices attached to a bus.

Useful load context includes:

- load name
- connected bus name
- type and identifier fields

### Generators

Generators are production devices attached to a bus.

Useful generator context includes:

- generator name
- connected bus name
- type and identifier fields

## Selection Context

The current selection reflects the user focus in the diagram.

If there are selected devices or selected buses, they should be emphasized in answers because they often indicate what the user is asking about.

## Session Studies

The VeraGrid session can contain multiple studies or drivers.

Examples of study-oriented context:

- active study name
- available study names
- whether results are loaded
- study-specific summaries when available

## Good Runtime Summary Shape

A good summary of the current runtime model should include:

- project and active study
- scale of the network
- currently selected objects
- a few representative names
- whether loaded study results appear to exist
