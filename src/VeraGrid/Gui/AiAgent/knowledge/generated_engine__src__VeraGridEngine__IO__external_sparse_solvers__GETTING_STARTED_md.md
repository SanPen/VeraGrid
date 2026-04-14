# VeraGridEngine Doc: Getting Started

- Original source path: `src/VeraGridEngine/IO/external_sparse_solvers/GETTING_STARTED.md`
- Knowledge kind: generated VeraGridEngine documentation

## Document Content

# External Sparse Solvers - Getting Started

This guide describes the reproducible installation path for VeraGrid external
sparse solver backends on Windows.

The objective is to keep licensed or heavy native dependencies outside the
VeraGrid repository while still allowing the EMT engine to use them through the
plugin interface.

## 1. What VeraGrid ships inside the repository

The repository contains:

- the sparse backend integration code,
- plugin templates,
- helper installers,
- and validation tests.

The repository does **not** embed the external solver runtimes themselves.

## 2. External directories used by default

### Plugin templates installed into user space

```text
%USERPROFILE%\.VeraGrid\plugins\sparse_solvers
```

### External Python runtimes

```text
%USERPROFILE%\.VeraGrid\external_python_packages
```

### External native runtimes

```text
%USERPROFILE%\.VeraGrid\external_native
```

## 3. Internal fallback policy

VeraGrid keeps `SuperLU` as the default sparse backend.

If an external plugin is requested but unavailable, the EMT stack can fall back
to `SuperLU` when `allow_internal_sparse_fallback=True`.

## 4. Installing the PARDISO plugin from scratch

### Step 4.1 - Install the plugin template

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin pardiso_pypardiso
```

Expected result:

```text
%USERPROFILE%\.VeraGrid\plugins\sparse_solvers\pardiso_pypardiso
```

### Step 4.2 - Install the external Python runtime

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_runtime pardiso_pypardiso pypardiso
```

Expected result:

```text
%USERPROFILE%\.VeraGrid\external_python_packages\pardiso_pypardiso
```

### Step 4.3 - Validate the plugin

```bash
python -c "from VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_loader import load_sparse_solver_backend_provider; p = load_sparse_solver_backend_provider('pardiso_pypardiso', ''); print(p.get_name(), p.get_solver_type(), p.is_available())"
```

Expected result:

```text
pardiso_pypardiso SparseSolver.Pardiso True
```

## 5. Installing the native KLU plugin from scratch

The recommended KLU path is `klu_vcpkg_native`.

### Step 5.1 - Install the plugin template

```bash
python -m VeraGridEngine.IO.external_sparse_solvers.install_external_sparse_solver_plugin klu_vcpkg_native
```

Expected result:

```text
%USERPROFILE%\.VeraGrid\plugins\sparse_solvers\klu_vcpkg_native
```

### Step 5.2 - Install Microsoft C++ Build Tools

Use the helper scripts under:

```text
src/VeraGridEngine/IO/external_sparse_solvers/tools
```

The recommended interactive launcher is:

```text
launch_klu_toolchain_ui.cmd
```

If you need the elevated automated path, use:

```text
launch_klu_toolchain_and_runtime_admin.cmd
```

### Step 5.3 - Install SuiteSparse KLU with vcpkg

Use the helper bootstrap script:

```text
bootstrap_vcpkg_now.cmd
```

Then install the SuiteSparse components under the external vcpkg tree.

The expected native install root is:

```text
%USERPROFILE%\.VeraGrid\external_native\vcpkg\installed\x64-windows
```

### Step 5.4 - Build the native Python extension

Inside the plugin template folder:

```text
src/VeraGridEngine/IO/external_sparse_solvers/plugin_templates/klu_vcpkg_native
```

run:

```text
build_native_plugin.cmd
```

This should generate:

```text
native_build\klu_native_backend*.pyd
```

Then copy that `.pyd` into the installed plugin directory under:

```text
%USERPROFILE%\.VeraGrid\plugins\sparse_solvers\klu_vcpkg_native\native_build
```

### Step 5.5 - Validate the plugin

```bash
python -c "from VeraGridEngine.Utils.NumericalMethods.emt_sparse_solver_loader import load_sparse_solver_backend_provider; p = load_sparse_solver_backend_provider('klu_vcpkg_native', ''); print(p.get_name(), p.get_solver_type(), p.is_available())"
```

Expected result:

```text
klu_vcpkg_native SparseSolver.KLU True
```

## 6. Using an external backend from EMT

In `EmtOptions`, configure:

- `sparse_solver`
- `external_sparse_solver_plugin_name`
- `allow_internal_sparse_fallback`

Example for PARDISO:

```python
from VeraGridEngine.Simulations.EMT.emt_options import EmtOptions
from VeraGridEngine.enumerations import EmtSolverTypes, SparseSolver

options = EmtOptions(
    solver_type=EmtSolverTypes.StructuralCompiled,
    sparse_solver=SparseSolver.Pardiso,
    external_sparse_solver_plugin_name="pardiso_pypardiso",
    allow_internal_sparse_fallback=False,
)
```

Example for native KLU:

```python
options = EmtOptions(
    solver_type=EmtSolverTypes.StructuralCompiled,
    sparse_solver=SparseSolver.KLU,
    external_sparse_solver_plugin_name="klu_vcpkg_native",
    allow_internal_sparse_fallback=False,
)
```

## 7. Validation commands

### Integration tests

```bash
pytest trunk/implicit_solver_test_EMT/Test_implicit/test_emt_external_sparse_solver_integration.py -q
```

### Sparse backend benchmarks

```bash
pytest trunk/implicit_solver_test_EMT/Test_implicit/test_emt_sparse_backend_benchmark.py -q
pytest trunk/implicit_solver_test_EMT/Test_implicit/test_emt_sparse_backend_benchmark_statistics.py -q
```

### EMT benchmark suite

```bash
pytest trunk/implicit_solver_test_EMT/Test_implicit/test_dynamics_emt_benchmark_scripts.py -q
```

## 8. Troubleshooting

### PARDISO plugin says unavailable

- Check that `pypardiso` was installed into:
  - `%USERPROFILE%\.VeraGrid\external_python_packages\pardiso_pypardiso`
- Re-run the validation command in section 4.3.

### Native KLU plugin says unavailable

- Check that the SuiteSparse DLLs are present in:
  - `%USERPROFILE%\.VeraGrid\external_native\vcpkg\installed\x64-windows\bin`
- Check that the compiled `.pyd` is present in:
  - `%USERPROFILE%\.VeraGrid\plugins\sparse_solvers\klu_vcpkg_native\native_build`
- Re-run the validation command in section 5.5.

### External backend does not load and VeraGrid falls back to SuperLU

- Check plugin name spelling.
- Check `plugin.json` exists in the installed plugin directory.
- Check the plugin provider class name matches the manifest.
- Set `allow_internal_sparse_fallback=False` if you want the configuration to fail hard instead of silently falling back.
