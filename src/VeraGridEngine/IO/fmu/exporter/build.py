# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile

from VeraGridEngine.IO.fmu.exporter.config import ExportConfig, TargetPlatform
from VeraGridEngine.IO.fmu.exporter.diff_to_c import render_discrete_derivative
from VeraGridEngine.IO.fmu.exporter.expr_to_c import ExprToCVisitor
from VeraGridEngine.IO.fmu.exporter.export_ir import EquationGroup, ExportModel, StorageSegment, VariableCategory
from VeraGridEngine.IO.fmu.exporter.procedural_to_c import render_procedural_c
from VeraGridEngine.IO.fmu.exporter.variable_map import CVariableResolver


def _template_root() -> Path:
    return Path(__file__).parent / "c_runtime" / "fmi2_template"


def ensure_build_layout(cfg: ExportConfig) -> tuple[Path, Path, Path]:
    if cfg.build_dir is None:
        if os.name == "nt":
            cfg.output_dir.mkdir(parents=True, exist_ok=True)
            # Building under the FMU output directory avoids Windows MSBuild warnings about
            # temporary intermediate folders and also keeps host-native artifacts together.
            root = Path(tempfile.mkdtemp(prefix="veragrid_fmu_build_", dir=str(cfg.output_dir)))
        else:
            # On Linux/macOS, especially under WSL mounted Windows paths, building on the
            # host temporary filesystem avoids make/cmake clock-skew warnings.
            root = Path(tempfile.mkdtemp(prefix="veragrid_fmu_build_"))
    else:
        root = cfg.build_dir
    root.mkdir(parents=True, exist_ok=True)
    return root / "source", root / "build", (cfg.staging_dir or root / "staging")


def _copy_template_tree(destination: Path) -> None:
    shutil.copytree(_template_root(), destination, dirs_exist_ok=True)


def _detect_tool_bin_dir() -> Path | None:
    candidates: list[str | None] = list()
    candidates.append(shutil.which("cmake"))
    candidates.append(os.environ.get("CMAKE_ROOT"))
    for candidate in candidates:
        if candidate:
            path = Path(candidate)
            if path.is_file():
                return path.parent
            else:
                if path.is_dir() and ((path / "cmake.exe").exists() or (path / "cmake").exists()):
                    return path
                else:
                    pass
        else:
            pass

    if os.name == "nt":
        known_dirs: list[Path] = list()
        known_dirs.append(Path("C:/Program Files/CMake/bin"))
        known_dirs.append(Path("C:/msys64/mingw64/bin"))
        known_dirs.append(Path("C:/msys64/ucrt64/bin"))
        directory: Path
        for directory in known_dirs:
            if (directory / "cmake.exe").exists() or (directory / "cmake").exists():
                return directory
            else:
                pass
    else:
        pass
    return None


def _toolchain_env() -> tuple[str, dict[str, str]]:
    env: dict[str, str] = os.environ.copy()

    # Optional explicit override
    cmake_override: str | None = os.environ.get("VG_CMAKE")
    if cmake_override:
        return cmake_override, env
    else:
        pass

    # Prefer the system installation already visible in PATH
    cmake_cmd: str | None = shutil.which("cmake")
    if cmake_cmd:
        return cmake_cmd, env
    else:
        pass

    # Fallback only if PATH does not provide cmake
    tool_dir: Path | None = _detect_tool_bin_dir()
    if tool_dir is not None:
        if (tool_dir / "cmake.exe").exists():
            return str(tool_dir / "cmake.exe"), env
        else:
            if (tool_dir / "cmake").exists():
                return str(tool_dir / "cmake"), env
            else:
                pass
    else:
        pass

    return "cmake", env

def _compiler_search_order() -> tuple[str, ...]:
    """
    Return the compiler executable names searched on the current host.

    :return: Ordered compiler executable names.
    """

    if os.name == "nt":
        return ("clang", "gcc", "cc")
    else:
        return ("cc", "clang", "gcc")


def _detect_c_compiler() -> tuple[str | None, dict[str, str]]:
    """
    Detect one host-native C compiler usable by the direct FMU build fallback.

    The direct compiler path is a fallback behind CMake, so the search prefers
    simple host-native compilers visible in ``PATH`` and only falls back to a few
    Windows-specific known locations when running on Windows.

    :return: Compiler command and environment.
    """

    env: dict[str, str] = os.environ.copy()

    compiler_override: str | None = os.environ.get("VG_CC")
    if compiler_override:
        return compiler_override, env
    else:
        pass

    compiler_override = os.environ.get("CC")
    if compiler_override:
        return compiler_override, env
    else:
        pass

    compiler_name: str
    for compiler_name in _compiler_search_order():
        compiler_cmd: str | None = shutil.which(compiler_name)
        if compiler_cmd:
            return compiler_cmd, env
        else:
            pass

    toolchain_bin: str | None = os.environ.get("VG_TOOLCHAIN_BIN")
    if toolchain_bin:
        tool_dir: Path = Path(toolchain_bin)
        for compiler_name in _compiler_search_order():
            compiler_candidate: Path = tool_dir / compiler_name
            if compiler_candidate.exists():
                return str(compiler_candidate), env
            else:
                compiler_candidate_exe: Path = tool_dir / f"{compiler_name}.exe"
                if compiler_candidate_exe.exists():
                    return str(compiler_candidate_exe), env
                else:
                    pass
    else:
        pass

    if os.name == "nt":
        candidate_dirs: list[Path] = list()
        candidate_dirs.append(Path("C:/msys64/mingw64/bin"))
        candidate_dirs.append(Path("C:/msys64/ucrt64/bin"))
        tool_dir: Path
        for tool_dir in candidate_dirs:
            for compiler_name in _compiler_search_order():
                compiler_candidate: Path = tool_dir / f"{compiler_name}.exe"
                if compiler_candidate.exists():
                    return str(compiler_candidate), env
                else:
                    pass
    else:
        pass

    return None, env


def host_build_capable() -> bool:
    """
    Return whether the current host appears able to compile one FMU binary.

    The check is intentionally lightweight because tests use it as a skip guard.
    CMake availability is sufficient for the primary build path, while the direct
    compiler fallback covers simpler host setups.

    :return: ``True`` when the host likely has a usable FMU build toolchain.
    """

    cmake_cmd: str | None = shutil.which("cmake")
    if cmake_cmd is not None:
        return True
    else:
        tool_dir: Path | None = _detect_tool_bin_dir()
        if tool_dir is not None:
            return True
        else:
            compiler_cmd: str | None
            compiler_cmd, _ = _detect_c_compiler()
            return compiler_cmd is not None


def _direct_build_link_flags(target_platform: TargetPlatform) -> list[str]:
    """
    Return the platform-specific linker flags for the direct fallback compiler path.

    :param target_platform: Target FMU binary platform.
    :return: Linker flag list.
    """

    flags: list[str] = list()
    if target_platform == TargetPlatform.DARWIN64:
        flags.append("-dynamiclib")
    else:
        flags.append("-shared")
    return flags


def _direct_build_compile_flags(target_platform: TargetPlatform) -> list[str]:
    """
    Return the common compiler flags for the direct fallback compiler path.

    :param target_platform: Target FMU binary platform.
    :return: Compiler flag list.
    """

    flags: list[str] = list()
    flags.append("-std=c99")
    flags.append("-O2")
    if target_platform == TargetPlatform.WIN64:
        pass
    else:
        flags.append("-fPIC")
    return flags


def _direct_build_math_flags(target_platform: TargetPlatform) -> list[str]:
    """
    Return the math-library flags for the direct fallback compiler path.

    :param target_platform: Target FMU binary platform.
    :return: Linker flag list.
    """

    flags: list[str] = list()
    if target_platform == TargetPlatform.WIN64:
        pass
    else:
        flags.append("-lm")
    return flags


def _direct_c_build(cfg: ExportConfig, source_dir: Path, build_dir: Path) -> Path:
    """
    Compile the generated FMU runtime without CMake using a host-native C compiler.

    :param cfg: Export configuration.
    :param source_dir: Generated C source directory.
    :param build_dir: Binary output directory.
    :return: Built shared-library path.
    """

    compiler_cmd: str | None
    env: dict[str, str]
    compiler_cmd, env = _detect_c_compiler()
    if compiler_cmd is None:
        raise FileNotFoundError("No usable host-native C compiler was found for direct FMU runtime compilation")
    else:
        pass

    output_path = build_dir / cfg.library_name
    cmd: list[str] = list()
    cmd.append(compiler_cmd)
    cmd.extend(_direct_build_link_flags(cfg.target_platform))
    cmd.extend(_direct_build_compile_flags(cfg.target_platform))
    cmd.extend(["-I", str(source_dir / "include")])
    cmd.extend(["-I", str(source_dir / "src")])
    cmd.extend(["-o", str(output_path)])
    cmd.append(str(source_dir / "src" / "runtime_fmi2.c"))
    cmd.append(str(source_dir / "src" / "model_instance.c"))
    cmd.append(str(source_dir / "src" / "solver.c"))
    cmd.append(str(source_dir / "src" / "generated_model.c"))
    cmd.append(str(source_dir / "src" / "generated_procedural.c"))
    cmd.extend(_direct_build_math_flags(cfg.target_platform))
    subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    if not output_path.exists():
        raise FileNotFoundError(f"Direct gcc build did not produce {output_path}")
    else:
        pass
    return output_path


def _detect_gcc() -> tuple[str | None, dict[str, str]]:
    """
    Backward-compatible alias for legacy tests that still import `_detect_gcc`.

    :return: Compiler command and environment.
    """

    return _detect_c_compiler()


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _json_compatible(value):
    if isinstance(value, dict):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


def _sorted_variables(export_model: ExportModel, category: VariableCategory) -> list:
    return sorted(
        [variable for variable in export_model.variables if variable.category == category],
        key=lambda variable: variable.storage_index,
    )


def _storage_expr(segment: StorageSegment, index: int) -> str:
    if segment == StorageSegment.STATES:
        return f"instance->states[{index}]"
    if segment == StorageSegment.ALGEBRAICS:
        return f"instance->algebraics[{index}]"
    if segment == StorageSegment.INPUTS:
        return f"instance->inputs[{index}]"
    if segment == StorageSegment.CONST_PARAMS:
        return f"instance->const_params[{index}]"
    if segment == StorageSegment.RUNTIME_PARAMS:
        return f"instance->runtime_params[{index}]"
    raise ValueError(f"Unsupported storage segment: {segment}")


def render_generated_metadata_h(export_model: ExportModel, cfg: ExportConfig) -> str:
    logic_count = len(export_model.logic_entries)
    lines = [
        "#ifndef GENERATED_METADATA_H",
        "#define GENERATED_METADATA_H",
        "",
        f"#define VG_MODEL_NAME \"{export_model.model_name}\"",
        f"#define VG_MODEL_IDENTIFIER \"{export_model.model_identifier}\"",
        f"#define VG_MODEL_GUID \"{export_model.guid}\"",
        f"#define VG_NUM_STATES {export_model.counts.get('states', 0)}",
        f"#define VG_NUM_ALGEBRAICS {export_model.counts.get('algebraics', 0)}",
        f"#define VG_NUM_CONTINUOUS_VARS {export_model.counts.get('states', 0) + export_model.counts.get('algebraics', 0)}",
        f"#define VG_NUM_INPUTS {export_model.counts.get('inputs', 0)}",
        f"#define VG_NUM_CONST_PARAMS {export_model.counts.get('const_params', 0)}",
        f"#define VG_NUM_RUNTIME_PARAMS {export_model.counts.get('runtime_params', 0)}",
        f"#define VG_NUM_RESIDUALS {export_model.counts.get('states', 0) + export_model.counts.get('algebraics', 0)}",
        f"#define VG_FIXED_STEP {cfg.fixed_step:.17g}",
        f"#define VG_NEWTON_TOLERANCE {cfg.newton_tolerance:.17g}",
        f"#define VG_MAX_NEWTON_ITERATIONS {cfg.max_newton_iterations}",
        f"#define VG_LOGIC_ENTRY_COUNT {logic_count}",
        f"#define VG_LOGIC_REAL_SLOTS {logic_count * 5}",
        f"#define VG_LOGIC_INT_SLOTS {logic_count * 3}",
        "",
        "#endif",
        "",
    ]
    return "\n".join(lines)


def render_generated_model_h() -> str:
    return "\n".join(
        [
            "#ifndef GENERATED_MODEL_H",
            "#define GENERATED_MODEL_H",
            "",
            '#include "model_instance.h"',
            "",
            "double vg_heaviside(double x);",
            "double vg_safe_log(double x);",
            "double vg_safe_sqrt(double x);",
            "",
            "void generated_set_start_values(ModelInstance* instance);",
            "void generated_eval_init(ModelInstance* instance);",
            "void generated_eval_discrete_init(ModelInstance* instance);",
            "void generated_eval_residual(ModelInstance* instance, double* out);",
            "void generated_eval_outputs(ModelInstance* instance);",
            "double generated_procedural_next_event(ModelInstance* instance, double t_prev, double t_target);",
            "void generated_procedural_update(ModelInstance* instance, double t);",
            "int generated_get_real(ModelInstance* instance, fmi2ValueReference vr, double* value);",
            "int generated_set_real(ModelInstance* instance, fmi2ValueReference vr, double value);",
            "",
            "#endif",
            "",
        ]
    )


def _render_start_assignments(export_model: ExportModel) -> list[str]:
    lines: list[str] = []
    for variable in export_model.variables:
        if variable.category == VariableCategory.DIFF:
            continue
        if variable.start is None:
            continue
        lines.append(f"    {_storage_expr(variable.storage_segment, variable.storage_index)} = {variable.start:.17g};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_runtime_init(export_model: ExportModel, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.RUNTIME_INIT or equation.target_uid is None:
            continue
        lines.append(f"    {resolver.resolve_target(equation.target_uid)} = {visitor.render(equation.expression)};")
    return lines


def _render_init_assignments(export_model: ExportModel, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines = _render_runtime_init(export_model, visitor, resolver)
    for equation in export_model.equations:
        if equation.group != EquationGroup.INIT or equation.target_uid is None:
            continue
        lines.append(f"    {resolver.resolve_target(equation.target_uid)} = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_diff_init_assignments(export_model: ExportModel, visitor: ExprToCVisitor) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.DIFF_INIT or equation.target_uid is None:
            continue
        diff_variable = export_model.variable_by_uid(equation.target_uid)
        base_uid = diff_variable.diff_base_uid
        if base_uid is None:
            continue
        base_variable = export_model.variable_by_uid(base_uid)
        if base_variable.history_index is None:
            continue
        lines.append(f"    instance->d_history[{base_variable.history_index}] = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_residual_lines(export_model: ExportModel, cfg: ExportConfig, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines: list[str] = []
    state_count = export_model.counts.get("states", 0)
    for equation in export_model.equations:
        if equation.group == EquationGroup.STATE and equation.target_uid is not None:
            variable = export_model.variable_by_uid(equation.target_uid)
            if variable.history_index is None:
                raise ValueError(f"State variable {variable.name!r} is missing history index")
            derivative = render_discrete_derivative(
                method=cfg.integration_method,
                state_expr=_storage_expr(StorageSegment.STATES, variable.storage_index),
                history_expr=f"instance->history[{variable.history_index}]",
                d_history_expr=f"instance->d_history[{variable.history_index}]",
                history2_expr=f"instance->history2[{variable.history_index}]",
                step_expr="instance->current_step_size",
            )
            lines.append(f"    out[{equation.index}] = ({derivative}) - ({visitor.render(equation.expression)});")
        elif equation.group == EquationGroup.ALGEBRAIC:
            lines.append(f"    out[{state_count + equation.index}] = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)out;")
    return lines


def _render_get_real(export_model: ExportModel) -> list[str]:
    lines = ["    switch (vr) {"]
    for variable in sorted(export_model.exposed_variables(), key=lambda item: item.value_reference or -1):
        lines.extend(
            [
                f"        case {variable.value_reference}u:",
                f"            *value = {_storage_expr(variable.storage_segment, variable.storage_index)};",
                "            return 0;",
            ]
        )
    lines.extend(["        default:", "            return 1;", "    }"])
    return lines


def _render_set_real(export_model: ExportModel) -> list[str]:
    lines = ["    switch (vr) {"]
    for variable in sorted(export_model.exposed_variables(), key=lambda item: item.value_reference or -1):
        target = _storage_expr(variable.storage_segment, variable.storage_index)
        if variable.causality == "input" or variable.category == VariableCategory.RUNTIME_PARAM:
            lines.extend(
                [
                    f"        case {variable.value_reference}u:",
                    f"            {target} = value;",
                    "            return 0;",
                ]
            )
        elif variable.category == VariableCategory.CONST_PARAM:
            lines.extend(
                [
                    f"        case {variable.value_reference}u:",
                    "            if (instance->initialized) return 1;",
                    f"            {target} = value;",
                    "            return 0;",
                ]
            )
    lines.extend(["        default:", "            return 1;", "    }"])
    return lines


def render_generated_model_c(export_model: ExportModel, cfg: ExportConfig) -> str:
    resolver = CVariableResolver(export_model, cfg)
    visitor = ExprToCVisitor(resolver)
    residual_count = export_model.counts.get("states", 0) + export_model.counts.get("algebraics", 0)
    lines = [
        '#include "generated_model.h"',
        '#include "generated_metadata.h"',
        '#include "runtime_support.h"',
        "",
        "double vg_heaviside(double x) { return x > 0.0 ? 1.0 : 0.0; }",
        "double vg_safe_log(double x) { return log(x > 1e-300 ? x : 1e-300); }",
        "double vg_safe_sqrt(double x) { return sqrt(x >= 0.0 ? x : 0.0); }",
        "",
        "void generated_set_start_values(ModelInstance* instance) {",
        *_render_start_assignments(export_model),
        "}",
        "",
        "void generated_eval_init(ModelInstance* instance) {",
        *_render_init_assignments(export_model, visitor, resolver),
        "}",
        "",
        "void generated_eval_discrete_init(ModelInstance* instance) {",
        *_render_diff_init_assignments(export_model, visitor),
        "}",
        "",
        "void generated_eval_residual(ModelInstance* instance, double* out) {",
        f"    memset(out, 0, sizeof(double) * {residual_count});",
        *_render_residual_lines(export_model, cfg, visitor, resolver),
        "}",
        "",
        "void generated_eval_outputs(ModelInstance* instance) {",
        "    (void)instance;",
        "}",
        "",
        "int generated_get_real(ModelInstance* instance, fmi2ValueReference vr, double* value) {",
        *_render_get_real(export_model),
        "}",
        "",
        "int generated_set_real(ModelInstance* instance, fmi2ValueReference vr, double value) {",
        *_render_set_real(export_model),
        "}",
        "",
    ]
    return "\n".join(lines)


def emit_c_sources(export_model: ExportModel, cfg: ExportConfig, source_root: Path) -> None:
    _copy_template_tree(source_root)
    resolver = CVariableResolver(export_model, cfg)
    _write_text(source_root / "src" / "generated_metadata.h", render_generated_metadata_h(export_model, cfg))
    _write_text(source_root / "src" / "generated_model.h", render_generated_model_h())
    _write_text(source_root / "src" / "generated_model.c", render_generated_model_c(export_model, cfg))
    _write_text(source_root / "src" / "generated_procedural.c", render_procedural_c(export_model, resolver))


def write_debug_resources(export_model: ExportModel, cfg: ExportConfig, resources_dir: Path) -> None:
    if cfg.include_export_model_resource:
        _write_text(resources_dir / "export_model.json", json.dumps(_json_compatible(export_model.to_dict()), indent=2, sort_keys=True))
    if cfg.include_snapshot_resource:
        _write_text(resources_dir / "snapshot.json", json.dumps(_json_compatible(export_model.source_snapshot), indent=2, sort_keys=True))


def build_shared_library(cfg: ExportConfig, source_dir: Path, build_dir: Path) -> Path:
    """
    Build the platform-specific shared library for one exported FMU.

    :param cfg: Export configuration.
    :param source_dir: Generated C source directory.
    :param build_dir: Binary output directory.
    :return: Built shared-library path.
    """

    build_dir.mkdir(parents=True, exist_ok=True)
    cmake_cmd: str
    env: dict[str, str]
    cmake_cmd, env = _toolchain_env()
    configure_cmd: list[str] = [
        cmake_cmd,
        "-S",
        str(source_dir),
        "-B",
        str(build_dir),
        f"-DVG_MODEL_IDENTIFIER={cfg.model_identifier}",
    ]
    if cfg.target_platform == TargetPlatform.WIN64:
        cmake_generator = os.environ.get("VG_CMAKE_GENERATOR")
        if cmake_generator:
            configure_cmd.extend(["-G", cmake_generator])
        else:
            pass
    try:
        subprocess.run(
            configure_cmd,
            check=True,
            text=True,
            env=env,
        )
        subprocess.run(
            [cmake_cmd, "--build", str(build_dir), "--config", "Release"],
            check=True,
            text=True,
            env=env,
        )
        release_candidate = build_dir / "Release" / cfg.library_name
        if release_candidate.exists():
            return release_candidate
        direct_candidate = build_dir / cfg.library_name
        if direct_candidate.exists():
            return direct_candidate
        matches = list(build_dir.rglob(cfg.library_name))
        if matches:
            return matches[0]
        else:
            pass
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return _direct_c_build(cfg, source_dir, build_dir)
