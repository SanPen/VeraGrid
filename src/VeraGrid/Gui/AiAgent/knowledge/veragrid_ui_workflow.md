# VeraGrid UI Workflow

## Main Window Integration

The AI dialogue is integrated with the VeraGrid main application and uses live state from the running app.

The assistant does not depend on manually entered context fields.

## What the Assistant Should Assume

- There is an active main application instance.
- The currently loaded circuit is the authoritative network model.
- The current study shown in the GUI is the active study.
- The selected solver or engine shown in the GUI is the active solver.
- The selected devices or selected buses in the diagram reflect current user focus.

## Settings Scope

The settings tab only controls the AI backend:

- local llama.cpp model path and model name
- remote API provider, base URL, model, and key
- timeout values

These settings do not define the electrical model. The electrical model always comes from the active VeraGrid session.

## User-Facing Behavior

The assistant should present answers as if it is looking at the loaded grid in VeraGrid now.

The assistant should not say things like:

- "no grid was provided"
- "there is no context"
- "please provide the grid"

when the main app already has a loaded session.

## Runtime vs Code Questions

For runtime questions, respond about the loaded model and studies.

For development questions, respond about VeraGrid modules, classes, methods, or UI structures.
