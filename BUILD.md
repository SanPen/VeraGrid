# Build

This project is built from source using standard FLOSS Python tooling.

## Packages

VeraGrid is split into three Python packages:

- `VeraGridEngine`: core models, file formats, and numerical engines
- `VeraGridServer`: server package built on top of `VeraGridEngine`
- `VeraGrid`: GUI package built on top of `VeraGridEngine`

## Basic source setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

## Editable development install

Install the main packages from the source tree:

```bash
python -m pip install -e ./src/VeraGridEngine
python -m pip install -e ./src/VeraGridServer
python -m pip install -e ./src/VeraGrid
```

## Build outputs

The project produces standard Python package artifacts through `setuptools`.

- Source distributions and wheels are generated from the package directories in `src/`
- Releases are published through the project release workflow and GitHub Releases process

## Non-Python components

The repository also contains C, CMake, Makefile, shell, batch, and PowerShell assets used by optional integrations and tooling. They are maintained in-source and version controlled with the rest of the project.

## Verification

Before proposing a release or pull request, run the checks described in [TESTING.md](TESTING.md).
