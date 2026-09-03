# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import tempfile
import os

from VeraGridEngine.IO.fmu.exporter.build import (
    _detect_c_compiler,
    _direct_build_compile_flags,
    _direct_build_link_flags,
    _direct_build_math_flags,
    _toolchain_env,
)

from VeraGridEngine.IO.fmu.exporter_me.config import ExportConfig, TargetPlatform
from VeraGridEngine.IO.fmu.exporter_me.expr_to_c import ExprToCVisitor
from VeraGridEngine.IO.fmu.exporter_me.export_ir import EquationGroup, ExportModel, StorageSegment, VariableCategory
from VeraGridEngine.IO.fmu.exporter_me.procedural_to_c import render_procedural_c
from VeraGridEngine.IO.fmu.exporter_me.variable_map import CVariableResolver


def _base_template_root() -> Path:
    return Path(__file__).parent.parent / "exporter" / "c_runtime" / "fmi2_template"


def ensure_build_layout(cfg: ExportConfig) -> tuple[Path, Path, Path]:
    if cfg.build_dir is None:
        if os.name == "nt":
            cfg.output_dir.mkdir(parents=True, exist_ok=True)
            # Building under the FMU output directory avoids Windows MSBuild warnings about
            # temporary intermediate folders and also keeps host-native artifacts together.
            root = Path(tempfile.mkdtemp(prefix="veragrid_fmu_me_build_", dir=str(cfg.output_dir)))
        else:
            # On Linux/macOS, especially under WSL mounted Windows paths, building on the
            # host temporary filesystem avoids make/cmake clock-skew warnings.
            root = Path(tempfile.mkdtemp(prefix="veragrid_fmu_me_build_"))
    else:
        root = cfg.build_dir
    root.mkdir(parents=True, exist_ok=True)
    return root / "source", root / "build", (cfg.staging_dir or root / "staging")


def _copy_template_tree(destination: Path) -> None:
    shutil.copytree(_base_template_root(), destination, dirs_exist_ok=True)


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


def _storage_expr(segment: StorageSegment, index: int) -> str:
    if segment == StorageSegment.STATES:
        return f"instance->states[{index}]"
    if segment == StorageSegment.DERIVATIVES:
        return f"instance->derivatives[{index}]"
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
    lines = [
        "#ifndef GENERATED_METADATA_H",
        "#define GENERATED_METADATA_H",
        "",
        f'#define VG_MODEL_NAME "{export_model.model_name}"',
        f'#define VG_MODEL_IDENTIFIER "{export_model.model_identifier}"',
        f'#define VG_MODEL_GUID "{export_model.guid}"',
        f"#define VG_NUM_STATES {export_model.counts.get('states', 0)}",
        f"#define VG_NUM_DERIVATIVES {export_model.counts.get('derivatives', 0)}",
        f"#define VG_NUM_ALGEBRAICS {export_model.counts.get('algebraics', 0)}",
        f"#define VG_NUM_INPUTS {export_model.counts.get('inputs', 0)}",
        f"#define VG_NUM_CONST_PARAMS {export_model.counts.get('const_params', 0)}",
        f"#define VG_NUM_RUNTIME_PARAMS {export_model.counts.get('runtime_params', 0)}",
        f"#define VG_NUM_EVENT_INDICATORS {export_model.counts.get('event_indicators', 0)}",
        f"#define VG_LOGIC_ENTRY_COUNT {len(export_model.logic_entries)}",
        f"#define VG_LOGIC_REAL_SLOTS {len(export_model.logic_entries) * 4}",
        f"#define VG_LOGIC_INT_SLOTS {len(export_model.logic_entries) * 3}",
        f"#define VG_RELATIVE_TOLERANCE {cfg.relative_tolerance:.17g}",
        f"#define VG_DEFAULT_STEP_SIZE {cfg.fixed_step:.17g}",
        f"#define VG_NEWTON_TOLERANCE {cfg.newton_tolerance:.17g}",
        f"#define VG_MAX_NEWTON_ITERATIONS {cfg.max_newton_iterations}",
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
            "void generated_eval_initial_derivatives(ModelInstance* instance);",
            "void generated_eval_algebraic_residual(ModelInstance* instance, double* out);",
            "void generated_get_derivatives(ModelInstance* instance, double* out);",
            "void generated_get_event_indicators(ModelInstance* instance, double* out);",
            "void generated_procedural_apply_initial(ModelInstance* instance);",
            "fmi2Boolean generated_procedural_completed_integrator_step(ModelInstance* instance);",
            "void generated_procedural_get_event_indicators(ModelInstance* instance, double* out);",
            "fmi2Boolean generated_procedural_new_discrete_states(ModelInstance* instance);",
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
        if variable.category == VariableCategory.DERIVATIVE:
            continue
        if variable.start is None:
            continue
        lines.append(f"    {_storage_expr(variable.storage_segment, variable.storage_index)} = {variable.start:.17g};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_runtime_init_lines(export_model: ExportModel, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.RUNTIME_INIT or equation.target_uid is None:
            continue
        lines.append(f"    {resolver.resolve_target(equation.target_uid)} = {visitor.render(equation.expression)};")
    return lines


def _render_init_lines(export_model: ExportModel, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.INIT or equation.target_uid is None:
            continue
        variable = export_model.variable_by_uid(equation.target_uid)
        if variable.category == VariableCategory.RUNTIME_PARAM:
            continue
        lines.append(f"    {resolver.resolve_target(equation.target_uid)} = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_diff_init_lines(export_model: ExportModel, visitor: ExprToCVisitor, resolver: CVariableResolver) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.DIFF_INIT or equation.target_uid is None:
            continue
        variable = export_model.variable_by_uid(equation.target_uid)
        if variable.category != VariableCategory.DERIVATIVE:
            continue
        lines.append(f"    {resolver.resolve_target(equation.target_uid)} = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
    return lines


def _render_algebraic_residual_lines(export_model: ExportModel, visitor: ExprToCVisitor) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.ALGEBRAIC:
            continue
        lines.append(f"    out[{equation.index}] = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
        lines.append("    (void)out;")
    return lines


def _render_derivative_lines(export_model: ExportModel, visitor: ExprToCVisitor) -> list[str]:
    lines: list[str] = []
    for equation in export_model.equations:
        if equation.group != EquationGroup.DERIVATIVE:
            continue
        lines.append(f"    out[{equation.index}] = {visitor.render(equation.expression)};")
    if not lines:
        lines.append("    (void)instance;")
        lines.append("    (void)out;")
    return lines


def _render_event_indicator_lines(export_model: ExportModel) -> list[str]:
    if export_model.counts.get("event_indicators", 0) == 0:
        return ["    (void)instance;", "    (void)out;"]
    return ["    generated_procedural_get_event_indicators(instance, out);"]


def _render_get_real(export_model: ExportModel) -> list[str]:
    lines = ["    switch (vr) {"]
    for variable in export_model.variables:
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
    for variable in export_model.variables:
        target = _storage_expr(variable.storage_segment, variable.storage_index)
        if variable.category in {VariableCategory.INPUT, VariableCategory.RUNTIME_PARAM}:
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


def render_generated_model_c(export_model: ExportModel) -> str:
    resolver = CVariableResolver(export_model)
    visitor = ExprToCVisitor(resolver)
    algebraic_count = export_model.counts.get("algebraics", 0)
    derivative_count = export_model.counts.get("derivatives", 0)
    event_indicator_count = export_model.counts.get("event_indicators", 0)
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
        "    int pass_index;",
        "    for (pass_index = 0; pass_index < 8; ++pass_index) {",
        *[f"    {line}" for line in _render_init_lines(export_model, visitor, resolver)],
        "    }",
        "}",
        "",
        "void generated_eval_initial_derivatives(ModelInstance* instance) {",
        "    int pass_index;",
        "    for (pass_index = 0; pass_index < 4; ++pass_index) {",
        *[f"    {line}" for line in _render_diff_init_lines(export_model, visitor, resolver)],
        "    }",
        "}",
        "",
        "void generated_eval_algebraic_residual(ModelInstance* instance, double* out) {",
        f"    memset(out, 0, sizeof(double) * {algebraic_count});" if algebraic_count > 0 else "    (void)out;",
        *_render_algebraic_residual_lines(export_model, visitor),
        "}",
        "",
        "void generated_get_derivatives(ModelInstance* instance, double* out) {",
        f"    memset(out, 0, sizeof(double) * {derivative_count});" if derivative_count > 0 else "    (void)out;",
        *_render_derivative_lines(export_model, visitor),
        "}",
        "",
        "void generated_get_event_indicators(ModelInstance* instance, double* out) {",
        f"    memset(out, 0, sizeof(double) * {event_indicator_count});" if event_indicator_count > 0 else "    (void)out;",
        *_render_event_indicator_lines(export_model),
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


def render_model_instance_h() -> str:
    return "\n".join(
        [
            "#ifndef MODEL_INSTANCE_H",
            "#define MODEL_INSTANCE_H",
            "",
            '#include "../include/fmi2Functions.h"',
            '#include "generated_metadata.h"',
            "",
            "enum {",
            "    VG_STATE_INSTANTIATED = 1,",
            "    VG_STATE_INITIALIZATION_MODE = 2,",
            "    VG_STATE_EVENT_MODE = 4,",
            "    VG_STATE_CONTINUOUS_TIME_MODE = 8,",
            "    VG_STATE_TERMINATED = 16,",
            "    VG_STATE_ERROR = 32",
            "};",
            "",
            "typedef struct ModelInstance {",
            "    fmi2CallbackFunctions callbacks;",
            "    fmi2String instance_name;",
            "    char* instance_name_owned;",
            "    fmi2Boolean logging_on;",
            "    fmi2Boolean initialized;",
            "    fmi2Boolean terminated;",
            "    fmi2Boolean stop_time_defined;",
            "    fmi2Boolean dirty;",
            "    int state;",
            "    double time;",
            "    double start_time;",
            "    double stop_time;",
            "    double relative_tolerance;",
            "    double last_successful_time;",
            "    double* states;",
            "    double* derivatives;",
            "    double* algebraics;",
            "    double* inputs;",
            "    double* const_params;",
            "    double* runtime_params;",
            "    double* nominals;",
            "    double* event_indicators;",
            "    double* logic_reals;",
            "    int* logic_ints;",
            "} ModelInstance;",
            "",
            "ModelInstance* model_instance_create(fmi2String instance_name, const fmi2CallbackFunctions* callbacks, fmi2Boolean logging_on);",
            "void model_instance_free(ModelInstance* instance);",
            "int model_instance_setup_experiment(ModelInstance* instance, fmi2Boolean tolerance_defined, fmi2Real tolerance, fmi2Real start_time, fmi2Boolean stop_time_defined, fmi2Real stop_time);",
            "int model_instance_initialize(ModelInstance* instance);",
            "int model_instance_reset(ModelInstance* instance);",
            "int model_instance_sync(ModelInstance* instance);",
            "int model_instance_set_time(ModelInstance* instance, fmi2Real time);",
            "int model_instance_set_continuous_states(ModelInstance* instance, const fmi2Real x[], size_t nx);",
            "int model_instance_get_continuous_states(ModelInstance* instance, fmi2Real x[], size_t nx);",
            "int model_instance_get_derivatives(ModelInstance* instance, fmi2Real dx[], size_t nx);",
            "int model_instance_get_event_indicators(ModelInstance* instance, fmi2Real z[], size_t ni);",
            "int model_instance_completed_integrator_step(ModelInstance* instance, fmi2Boolean* enter_event_mode, fmi2Boolean* terminate_simulation);",
            "int model_instance_enter_event_mode(ModelInstance* instance);",
            "int model_instance_new_discrete_states(ModelInstance* instance, fmi2EventInfo* event_info);",
            "int model_instance_enter_continuous_time_mode(ModelInstance* instance);",
            "int solver_solve_algebraics(ModelInstance* instance);",
            "int model_instance_copy_string(ModelInstance* instance, const char* source, char** dest);",
            "",
            "#endif",
            "",
        ]
    )


def render_model_instance_c() -> str:
    return "\n".join(
        [
            '#include "model_instance.h"',
            "",
            '#include "generated_model.h"',
            '#include "runtime_support.h"',
            "",
            "static void* vg_calloc(const fmi2CallbackFunctions* callbacks, size_t count, size_t size) {",
            "    if (callbacks != NULL && callbacks->allocateMemory != NULL) {",
            "        return callbacks->allocateMemory(count, size);",
            "    }",
            "    return calloc(count, size);",
            "}",
            "",
            "static void vg_free(const fmi2CallbackFunctions* callbacks, void* ptr) {",
            "    if (ptr == NULL) {",
            "        return;",
            "    }",
            "    if (callbacks != NULL && callbacks->freeMemory != NULL) {",
            "        callbacks->freeMemory(ptr);",
            "        return;",
            "    }",
            "    free(ptr);",
            "}",
            "",
            "static double* allocate_vector(const fmi2CallbackFunctions* callbacks, size_t count) {",
            "    if (count == 0u) {",
            "        return NULL;",
            "    }",
            "    return (double*)vg_calloc(callbacks, count, sizeof(double));",
            "}",
            "",
            "static void zero_vector(double* data, size_t count) {",
            "    if (data != NULL && count > 0u) {",
            "        memset(data, 0, sizeof(double) * count);",
            "    }",
            "}",
            "",
            "int model_instance_copy_string(ModelInstance* instance, const char* source, char** dest) {",
            "    size_t length;",
            "    char* text;",
            "    if (dest == NULL) {",
            "        return 1;",
            "    }",
            "    *dest = NULL;",
            "    if (source == NULL) {",
            "        return 0;",
            "    }",
            "    length = strlen(source);",
            "    text = (char*)vg_calloc(instance != NULL ? &instance->callbacks : NULL, length + 1u, sizeof(char));",
            "    if (text == NULL) {",
            "        return 1;",
            "    }",
            "    memcpy(text, source, length + 1u);",
            "    *dest = text;",
            "    return 0;",
            "}",
            "",
            "ModelInstance* model_instance_create(fmi2String instance_name, const fmi2CallbackFunctions* callbacks, fmi2Boolean logging_on) {",
            "    size_t i;",
            "    ModelInstance* instance = (ModelInstance*)vg_calloc(callbacks, 1u, sizeof(ModelInstance));",
            "    if (instance == NULL) {",
            "        return NULL;",
            "    }",
            "    if (callbacks != NULL) {",
            "        instance->callbacks = *callbacks;",
            "    }",
            "    if (model_instance_copy_string(instance, instance_name, &instance->instance_name_owned) != 0) {",
            "        vg_free(&instance->callbacks, instance);",
            "        return NULL;",
            "    }",
            "    instance->instance_name = instance->instance_name_owned;",
            "    instance->logging_on = logging_on;",
            "    instance->state = VG_STATE_INSTANTIATED;",
            "    instance->dirty = fmi2True;",
            "    instance->relative_tolerance = VG_RELATIVE_TOLERANCE;",
            "    instance->states = allocate_vector(&instance->callbacks, VG_NUM_STATES);",
            "    instance->derivatives = allocate_vector(&instance->callbacks, VG_NUM_DERIVATIVES);",
            "    instance->algebraics = allocate_vector(&instance->callbacks, VG_NUM_ALGEBRAICS);",
            "    instance->inputs = allocate_vector(&instance->callbacks, VG_NUM_INPUTS);",
            "    instance->const_params = allocate_vector(&instance->callbacks, VG_NUM_CONST_PARAMS);",
            "    instance->runtime_params = allocate_vector(&instance->callbacks, VG_NUM_RUNTIME_PARAMS);",
            "    instance->nominals = allocate_vector(&instance->callbacks, VG_NUM_STATES);",
            "    instance->event_indicators = allocate_vector(&instance->callbacks, VG_NUM_EVENT_INDICATORS);",
            "    instance->logic_reals = allocate_vector(&instance->callbacks, VG_LOGIC_REAL_SLOTS);",
            "    instance->logic_ints = (int*)vg_calloc(&instance->callbacks, VG_LOGIC_INT_SLOTS, sizeof(int));",
            "    for (i = 0u; i < (size_t)VG_NUM_STATES; ++i) {",
            "        instance->nominals[i] = 1.0;",
            "    }",
            "    generated_set_start_values(instance);",
            "    return instance;",
            "}",
            "",
            "void model_instance_free(ModelInstance* instance) {",
            "    if (instance == NULL) {",
            "        return;",
            "    }",
            "    vg_free(&instance->callbacks, instance->instance_name_owned);",
            "    vg_free(&instance->callbacks, instance->states);",
            "    vg_free(&instance->callbacks, instance->derivatives);",
            "    vg_free(&instance->callbacks, instance->algebraics);",
            "    vg_free(&instance->callbacks, instance->inputs);",
            "    vg_free(&instance->callbacks, instance->const_params);",
            "    vg_free(&instance->callbacks, instance->runtime_params);",
            "    vg_free(&instance->callbacks, instance->nominals);",
            "    vg_free(&instance->callbacks, instance->event_indicators);",
            "    vg_free(&instance->callbacks, instance->logic_reals);",
            "    vg_free(&instance->callbacks, instance->logic_ints);",
            "    vg_free(&instance->callbacks, instance);",
            "}",
            "",
            "int model_instance_setup_experiment(ModelInstance* instance, fmi2Boolean tolerance_defined, fmi2Real tolerance, fmi2Real start_time, fmi2Boolean stop_time_defined, fmi2Real stop_time) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    instance->time = start_time;",
            "    instance->start_time = start_time;",
            "    instance->stop_time_defined = stop_time_defined;",
            "    instance->stop_time = stop_time;",
            "    instance->relative_tolerance = tolerance_defined ? tolerance : VG_RELATIVE_TOLERANCE;",
            "    instance->last_successful_time = start_time;",
            "    instance->dirty = fmi2True;",
            "    return 0;",
            "}",
            "",
            "int model_instance_sync(ModelInstance* instance) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    if (solver_solve_algebraics(instance) != 0) {",
            "        return 2;",
            "    }",
            "    generated_get_derivatives(instance, instance->derivatives);",
            "    generated_get_event_indicators(instance, instance->event_indicators);",
            "    instance->dirty = fmi2False;",
            "    instance->last_successful_time = instance->time;",
            "    return 0;",
            "}",
            "",
            "int model_instance_initialize(ModelInstance* instance) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    generated_eval_init(instance);",
            "    generated_eval_initial_derivatives(instance);",
            "    generated_procedural_apply_initial(instance);",
            "    instance->initialized = fmi2True;",
            "    instance->terminated = fmi2False;",
            "    instance->dirty = fmi2True;",
            "    if (model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    instance->state = VG_STATE_EVENT_MODE;",
            "    return 0;",
            "}",
            "",
            "int model_instance_reset(ModelInstance* instance) {",
            "    size_t i;",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    zero_vector(instance->states, VG_NUM_STATES);",
            "    zero_vector(instance->derivatives, VG_NUM_DERIVATIVES);",
            "    zero_vector(instance->algebraics, VG_NUM_ALGEBRAICS);",
            "    zero_vector(instance->inputs, VG_NUM_INPUTS);",
            "    zero_vector(instance->const_params, VG_NUM_CONST_PARAMS);",
            "    zero_vector(instance->runtime_params, VG_NUM_RUNTIME_PARAMS);",
            "    zero_vector(instance->event_indicators, VG_NUM_EVENT_INDICATORS);",
            "    zero_vector(instance->logic_reals, VG_LOGIC_REAL_SLOTS);",
            "    if (instance->logic_ints != NULL && VG_LOGIC_INT_SLOTS > 0) memset(instance->logic_ints, 0, sizeof(int) * VG_LOGIC_INT_SLOTS);",
            "    for (i = 0u; i < (size_t)VG_NUM_STATES; ++i) {",
            "        instance->nominals[i] = 1.0;",
            "    }",
            "    generated_set_start_values(instance);",
            "    instance->time = instance->start_time;",
            "    instance->last_successful_time = instance->start_time;",
            "    instance->initialized = fmi2False;",
            "    instance->terminated = fmi2False;",
            "    instance->dirty = fmi2True;",
            "    instance->state = VG_STATE_INSTANTIATED;",
            "    return 0;",
            "}",
            "",
            "int model_instance_set_time(ModelInstance* instance, fmi2Real time) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    instance->time = time;",
            "    instance->dirty = fmi2True;",
            "    return 0;",
            "}",
            "",
            "int model_instance_set_continuous_states(ModelInstance* instance, const fmi2Real x[], size_t nx) {",
            "    if (instance == NULL || ((nx > 0u) && x == NULL) || nx != (size_t)VG_NUM_STATES) {",
            "        return 1;",
            "    }",
            "    if (nx > 0u) {",
            "        memcpy(instance->states, x, sizeof(fmi2Real) * nx);",
            "    }",
            "    instance->dirty = fmi2True;",
            "    return 0;",
            "}",
            "",
            "int model_instance_get_continuous_states(ModelInstance* instance, fmi2Real x[], size_t nx) {",
            "    if (instance == NULL || ((nx > 0u) && x == NULL) || nx != (size_t)VG_NUM_STATES) {",
            "        return 1;",
            "    }",
            "    if (nx > 0u) {",
            "        memcpy(x, instance->states, sizeof(fmi2Real) * nx);",
            "    }",
            "    return 0;",
            "}",
            "",
            "int model_instance_get_derivatives(ModelInstance* instance, fmi2Real dx[], size_t nx) {",
            "    if (instance == NULL || ((nx > 0u) && dx == NULL) || nx != (size_t)VG_NUM_DERIVATIVES) {",
            "        return 1;",
            "    }",
            "    if (instance->dirty && model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    if (nx > 0u) {",
            "        memcpy(dx, instance->derivatives, sizeof(fmi2Real) * nx);",
            "    }",
            "    return 0;",
            "}",
            "",
            "int model_instance_get_event_indicators(ModelInstance* instance, fmi2Real z[], size_t ni) {",
            "    if (instance == NULL || ((ni > 0u) && z == NULL) || ni != (size_t)VG_NUM_EVENT_INDICATORS) {",
            "        return 1;",
            "    }",
            "    if (instance->dirty && model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    if (ni > 0u) {",
            "        memcpy(z, instance->event_indicators, sizeof(fmi2Real) * ni);",
            "    }",
            "    return 0;",
            "}",
            "",
            "int model_instance_completed_integrator_step(ModelInstance* instance, fmi2Boolean* enter_event_mode, fmi2Boolean* terminate_simulation) {",
            "    fmi2Boolean changed;",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    changed = generated_procedural_completed_integrator_step(instance);",
            "    if (changed) {",
            "        instance->dirty = fmi2True;",
            "    }",
            "    if (enter_event_mode != NULL) {",
            "        *enter_event_mode = changed;",
            "    }",
            "    if (terminate_simulation != NULL) {",
            "        *terminate_simulation = fmi2False;",
            "    }",
            "    return 0;",
            "}",
            "",
            "int model_instance_enter_event_mode(ModelInstance* instance) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    instance->state = VG_STATE_EVENT_MODE;",
            "    return 0;",
            "}",
            "",
            "int model_instance_new_discrete_states(ModelInstance* instance, fmi2EventInfo* event_info) {",
            "    if (instance == NULL || event_info == NULL) {",
            "        return 1;",
            "    }",
            "    if (instance->dirty && model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    if (generated_procedural_new_discrete_states(instance)) {",
            "        instance->dirty = fmi2True;",
            "    }",
            "    if (instance->dirty && model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    event_info->newDiscreteStatesNeeded = fmi2False;",
            "    event_info->terminateSimulation = fmi2False;",
            "    event_info->nominalsOfContinuousStatesChanged = fmi2False;",
            "    event_info->valuesOfContinuousStatesChanged = fmi2False;",
            "    event_info->nextEventTimeDefined = fmi2False;",
            "    event_info->nextEventTime = 0.0;",
            "    return 0;",
            "}",
            "",
            "int model_instance_enter_continuous_time_mode(ModelInstance* instance) {",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    if (instance->dirty && model_instance_sync(instance) != 0) {",
            "        return 2;",
            "    }",
            "    instance->state = VG_STATE_CONTINUOUS_TIME_MODE;",
            "    return 0;",
            "}",
            "",
        ]
    )


def render_solver_c() -> str:
    return "\n".join(
        [
            '#include "model_instance.h"',
            "",
            '#include "generated_model.h"',
            '#include "runtime_support.h"',
            "",
            "static double* algebraic_ptr(ModelInstance* instance, size_t index) {",
            "    if (index < (size_t)VG_NUM_ALGEBRAICS) {",
            "        return &instance->algebraics[index];",
            "    }",
            "    return NULL;",
            "}",
            "",
            "static double residual_norm(const double* residual, size_t count) {",
            "    size_t i;",
            "    double max_abs = 0.0;",
            "    for (i = 0u; i < count; ++i) {",
            "        double value = fabs(residual[i]);",
            "        if (value > max_abs) {",
            "            max_abs = value;",
            "        }",
            "    }",
            "    return max_abs;",
            "}",
            "",
            "static int solve_dense_system(size_t n, double* matrix, double* rhs) {",
            "    size_t i;",
            "    size_t j;",
            "    size_t k;",
            "    for (i = 0u; i < n; ++i) {",
            "        size_t pivot = i;",
            "        double pivot_abs = fabs(matrix[i * n + i]);",
            "        for (j = i + 1u; j < n; ++j) {",
            "            double candidate = fabs(matrix[j * n + i]);",
            "            if (candidate > pivot_abs) {",
            "                pivot = j;",
            "                pivot_abs = candidate;",
            "            }",
            "        }",
            "        if (pivot_abs < 1e-14) {",
            "            return 1;",
            "        }",
            "        if (pivot != i) {",
            "            for (k = i; k < n; ++k) {",
            "                double tmp = matrix[i * n + k];",
            "                matrix[i * n + k] = matrix[pivot * n + k];",
            "                matrix[pivot * n + k] = tmp;",
            "            }",
            "            {",
            "                double tmp_rhs = rhs[i];",
            "                rhs[i] = rhs[pivot];",
            "                rhs[pivot] = tmp_rhs;",
            "            }",
            "        }",
            "        for (j = i + 1u; j < n; ++j) {",
            "            double factor = matrix[j * n + i] / matrix[i * n + i];",
            "            matrix[j * n + i] = 0.0;",
            "            for (k = i + 1u; k < n; ++k) {",
            "                matrix[j * n + k] -= factor * matrix[i * n + k];",
            "            }",
            "            rhs[j] -= factor * rhs[i];",
            "        }",
            "    }",
            "    for (i = n; i-- > 0u;) {",
            "        double sum = rhs[i];",
            "        for (j = i + 1u; j < n; ++j) {",
            "            sum -= matrix[i * n + j] * rhs[j];",
            "        }",
            "        rhs[i] = sum / matrix[i * n + i];",
            "    }",
            "    return 0;",
            "}",
            "",
            "int solver_solve_algebraics(ModelInstance* instance) {",
            "    size_t n = (size_t)VG_NUM_ALGEBRAICS;",
            "    size_t i;",
            "    size_t j;",
            "    double* jacobian;",
            "    double* residual0;",
            "    double* residual1;",
            "    double* delta;",
            "",
            "    if (instance == NULL) {",
            "        return 1;",
            "    }",
            "    if (n == 0u) {",
            "        return 0;",
            "    }",
            "",
            "    jacobian = (double*)calloc(n * n, sizeof(double));",
            "    residual0 = (double*)calloc(n, sizeof(double));",
            "    residual1 = (double*)calloc(n, sizeof(double));",
            "    delta = (double*)calloc(n, sizeof(double));",
            "    if (jacobian == NULL || residual0 == NULL || residual1 == NULL || delta == NULL) {",
            "        free(jacobian);",
            "        free(residual0);",
            "        free(residual1);",
            "        free(delta);",
            "        return 1;",
            "    }",
            "",
            "    for (i = 0u; i < (size_t)VG_MAX_NEWTON_ITERATIONS; ++i) {",
            "        generated_eval_algebraic_residual(instance, residual0);",
            "        if (residual_norm(residual0, n) <= VG_NEWTON_TOLERANCE) {",
            "            break;",
            "        }",
            "        for (j = 0u; j < n; ++j) {",
            "            double* x = algebraic_ptr(instance, j);",
            "            double original = *x;",
            "            double epsilon = 1e-7 * (fabs(original) + 1.0);",
            "            size_t row;",
            "            *x = original + epsilon;",
            "            generated_eval_algebraic_residual(instance, residual1);",
            "            *x = original;",
            "            for (row = 0u; row < n; ++row) {",
            "                jacobian[row * n + j] = (residual1[row] - residual0[row]) / epsilon;",
            "            }",
            "            delta[j] = -residual0[j];",
            "        }",
            "        if (solve_dense_system(n, jacobian, delta) != 0) {",
            "            free(jacobian);",
            "            free(residual0);",
            "            free(residual1);",
            "            free(delta);",
            "            return 2;",
            "        }",
            "        for (j = 0u; j < n; ++j) {",
            "            double* x = algebraic_ptr(instance, j);",
            "            *x += delta[j];",
            "        }",
            "    }",
            "",
            "    free(jacobian);",
            "    free(residual0);",
            "    free(residual1);",
            "    free(delta);",
            "    return 0;",
            "}",
            "",
        ]
    )


def render_runtime_fmi2_c() -> str:
    return "\n".join(
        [
            '#include "runtime_fmi2.h"',
            "",
            '#include "generated_metadata.h"',
            '#include "generated_model.h"',
            '#include "runtime_support.h"',
            "",
            "static void vg_log(ModelInstance* instance, fmi2Status status, const char* category, const char* message) {",
            "    if (instance == NULL || instance->callbacks.logger == NULL) {",
            "        return;",
            "    }",
            "    instance->callbacks.logger(instance->callbacks.componentEnvironment, instance->instance_name, status, category, message);",
            "}",
            "",
            "static int vg_allowed_state(ModelInstance* instance, int mask) {",
            "    return instance != NULL && (instance->state & mask) != 0;",
            "}",
            "",
            "static fmi2Status vg_state_error(ModelInstance* instance, const char* function_name) {",
            "    vg_log(instance, fmi2Error, \"error\", function_name);",
            "    if (instance != NULL) {",
            "        instance->state = VG_STATE_ERROR;",
            "    }",
            "    return fmi2Error;",
            "}",
            "",
            "fmi2Status status_from_result(int result) {",
            "    return result == 0 ? fmi2OK : fmi2Error;",
            "}",
            "",
            "const char* fmi2GetTypesPlatform(void) {",
            "    return fmi2TypesPlatform;",
            "}",
            "",
            "const char* fmi2GetVersion(void) {",
            "    return fmi2Version;",
            "}",
            "",
            "fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    (void)nCategories;",
            "    (void)categories;",
            "    if (instance == NULL) {",
            "        return fmi2Error;",
            "    }",
            "    instance->logging_on = loggingOn;",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Component fmi2Instantiate(",
            "    fmi2String instanceName,",
            "    fmi2Type fmuType,",
            "    fmi2String fmuGUID,",
            "    fmi2String fmuResourceLocation,",
            "    const fmi2CallbackFunctions* functions,",
            "    fmi2Boolean visible,",
            "    fmi2Boolean loggingOn",
            ") {",
            "    (void)fmuResourceLocation;",
            "    (void)visible;",
            "    if (instanceName == NULL || functions == NULL) {",
            "        return NULL;",
            "    }",
            "    if (fmuType != fmi2ModelExchange) {",
            "        return NULL;",
            "    }",
            "    if (fmuGUID == NULL) {",
            "        return NULL;",
            "    }",
            "    if (VG_MODEL_GUID[0] != '\\0') {",
            "        size_t index = 0u;",
            "        while (VG_MODEL_GUID[index] != '\\0' || fmuGUID[index] != '\\0') {",
            "            if (VG_MODEL_GUID[index] != fmuGUID[index]) {",
            "                return NULL;",
            "            }",
            "            index += 1u;",
            "        }",
            "    }",
            "    return (fmi2Component)model_instance_create(instanceName, functions, loggingOn);",
            "}",
            "",
            "void fmi2FreeInstance(fmi2Component c) {",
            "    model_instance_free((ModelInstance*)c);",
            "}",
            "",
            "fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_INSTANTIATED)) {",
            "        return vg_state_error(instance, \"fmi2SetupExperiment illegal state\");",
            "    }",
            "    if (stopTimeDefined && stopTime <= startTime) {",
            "        return vg_state_error(instance, \"fmi2SetupExperiment invalid stop time\");",
            "    }",
            "    return status_from_result(model_instance_setup_experiment(instance, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime));",
            "}",
            "",
            "fmi2Status fmi2EnterInitializationMode(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_INSTANTIATED)) {",
            "        return vg_state_error(instance, \"fmi2EnterInitializationMode illegal state\");",
            "    }",
            "    instance->state = VG_STATE_INITIALIZATION_MODE;",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Status fmi2ExitInitializationMode(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_INITIALIZATION_MODE)) {",
            "        return vg_state_error(instance, \"fmi2ExitInitializationMode illegal state\");",
            "    }",
            "    return status_from_result(model_instance_initialize(instance));",
            "}",
            "",
            "fmi2Status fmi2Terminate(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_EVENT_MODE | VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_ERROR)) {",
            "        return vg_state_error(instance, \"fmi2Terminate illegal state\");",
            "    }",
            "    instance->terminated = fmi2True;",
            "    instance->state = VG_STATE_TERMINATED;",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Status fmi2Reset(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_INSTANTIATED | VG_STATE_INITIALIZATION_MODE | VG_STATE_EVENT_MODE | VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_TERMINATED | VG_STATE_ERROR)) {",
            "        return vg_state_error(instance, \"fmi2Reset illegal state\");",
            "    }",
            "    return status_from_result(model_instance_reset(instance));",
            "}",
            "",
            "fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {",
            "    size_t i;",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (instance == NULL || ((nvr > 0u) && (vr == NULL || value == NULL))) {",
            "        return fmi2Error;",
            "    }",
            "    if (instance->initialized && instance->dirty && model_instance_sync(instance) != 0) {",
            "        return vg_state_error(instance, \"fmi2GetReal sync failed\");",
            "    }",
            "    for (i = 0u; i < nvr; ++i) {",
            "        if (generated_get_real(instance, vr[i], &value[i]) != 0) {",
            "            return fmi2Error;",
            "        }",
            "    }",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {",
            "    size_t i;",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_INSTANTIATED | VG_STATE_INITIALIZATION_MODE | VG_STATE_EVENT_MODE | VG_STATE_CONTINUOUS_TIME_MODE)) {",
            "        return vg_state_error(instance, \"fmi2SetReal illegal state\");",
            "    }",
            "    if ((nvr > 0u) && (vr == NULL || value == NULL)) {",
            "        return fmi2Error;",
            "    }",
            "    for (i = 0u; i < nvr; ++i) {",
            "        if (generated_set_real(instance, vr[i], value[i]) != 0) {",
            "            return fmi2Error;",
            "        }",
            "    }",
            "    instance->dirty = fmi2True;",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {",
            "    (void)c; if (FMUstate != NULL) *FMUstate = NULL; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate FMUstate) {",
            "    (void)c; (void)FMUstate; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {",
            "    (void)c; if (FMUstate != NULL) *FMUstate = NULL; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate FMUstate, size_t* size) {",
            "    (void)c; (void)FMUstate; if (size != NULL) *size = 0u; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate FMUstate, fmi2Byte serializedState[], size_t size) {",
            "    (void)c; (void)FMUstate; (void)serializedState; (void)size; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {",
            "    (void)c; (void)serializedState; (void)size; if (FMUstate != NULL) *FMUstate = NULL; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetDirectionalDerivative(fmi2Component c, const fmi2ValueReference vUnknown_ref[], size_t nUnknown, const fmi2ValueReference vKnown_ref[], size_t nKnown, const fmi2Real dvKnown[], fmi2Real dvUnknown[]) {",
            "    (void)c; (void)vUnknown_ref; (void)nUnknown; (void)vKnown_ref; (void)nKnown; (void)dvKnown; (void)dvUnknown; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2EnterEventMode(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_EVENT_MODE | VG_STATE_CONTINUOUS_TIME_MODE)) {",
            "        return vg_state_error(instance, \"fmi2EnterEventMode illegal state\");",
            "    }",
            "    return status_from_result(model_instance_enter_event_mode(instance));",
            "}",
            "",
            "fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2NewDiscreteStates illegal state\");",
            "    }",
            "    return status_from_result(model_instance_new_discrete_states(instance, eventInfo));",
            "}",
            "",
            "fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2EnterContinuousTimeMode illegal state\");",
            "    }",
            "    return status_from_result(model_instance_enter_continuous_time_mode(instance));",
            "}",
            "",
            "fmi2Status fmi2CompletedIntegratorStep(fmi2Component c, fmi2Boolean noSetFMUStatePriorToCurrentPoint, fmi2Boolean* enterEventMode, fmi2Boolean* terminateSimulation) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    (void)noSetFMUStatePriorToCurrentPoint;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE)) {",
            "        return vg_state_error(instance, \"fmi2CompletedIntegratorStep illegal state\");",
            "    }",
            "    return status_from_result(model_instance_completed_integrator_step(instance, enterEventMode, terminateSimulation));",
            "}",
            "",
            "fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2SetTime illegal state\");",
            "    }",
            "    return status_from_result(model_instance_set_time(instance, time));",
            "}",
            "",
            "fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2SetContinuousStates illegal state\");",
            "    }",
            "    return status_from_result(model_instance_set_continuous_states(instance, x, nx));",
            "}",
            "",
            "fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2GetDerivatives illegal state\");",
            "    }",
            "    return status_from_result(model_instance_get_derivatives(instance, derivatives, nx));",
            "}",
            "",
            "fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2GetEventIndicators illegal state\");",
            "    }",
            "    return status_from_result(model_instance_get_event_indicators(instance, eventIndicators, ni));",
            "}",
            "",
            "fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real states[], size_t nx) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (!vg_allowed_state(instance, VG_STATE_CONTINUOUS_TIME_MODE | VG_STATE_EVENT_MODE)) {",
            "        return vg_state_error(instance, \"fmi2GetContinuousStates illegal state\");",
            "    }",
            "    return status_from_result(model_instance_get_continuous_states(instance, states, nx));",
            "}",
            "",
            "fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (instance == NULL || ((nx > 0u) && x_nominal == NULL) || nx != (size_t)VG_NUM_STATES) {",
            "        return fmi2Error;",
            "    }",
            "    if (nx > 0u) {",
            "        memcpy(x_nominal, instance->nominals, sizeof(fmi2Real) * nx);",
            "    }",
            "    return fmi2OK;",
            "}",
            "",
            "fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)order; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) {",
            "    (void)c; (void)vr; (void)nvr; (void)order; (void)value; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2CancelStep(fmi2Component c) {",
            "    (void)c; return fmi2Error;",
            "}",
            "",
            "fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {",
            "    (void)c; (void)s; if (value != NULL) *value = fmi2OK; return fmi2Discard;",
            "}",
            "",
            "fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {",
            "    ModelInstance* instance = (ModelInstance*)c;",
            "    if (value == NULL || instance == NULL) {",
            "        return fmi2Error;",
            "    }",
            "    if (s == fmi2LastSuccessfulTime) {",
            "        *value = instance->last_successful_time;",
            "        return fmi2OK;",
            "    }",
            "    *value = 0.0;",
            "    return fmi2Discard;",
            "}",
            "",
            "fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {",
            "    (void)c; (void)s; if (value != NULL) *value = 0; return fmi2Discard;",
            "}",
            "",
            "fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {",
            "    (void)c; (void)s; if (value != NULL) *value = fmi2False; return fmi2Discard;",
            "}",
            "",
            "fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String* value) {",
            "    (void)c; (void)s; if (value != NULL) *value = \"\"; return fmi2Discard;",
            "}",
            "",
        ]
    )


def emit_c_sources(export_model: ExportModel, cfg: ExportConfig, source_root: Path) -> None:
    _copy_template_tree(source_root)
    resolver = CVariableResolver(export_model)

    metadata_h_path = source_root / "src" / "generated_metadata.h"
    model_h_path = source_root / "src" / "generated_model.h"
    model_c_path = source_root / "src" / "generated_model.c"
    procedural_c_path = source_root / "src" / "generated_procedural.c"
    model_instance_h_path = source_root / "src" / "model_instance.h"
    model_instance_c_path = source_root / "src" / "model_instance.c"
    solver_c_path = source_root / "src" / "solver.c"
    runtime_fmi2_c_path = source_root / "src" / "runtime_fmi2.c"

    _write_text(metadata_h_path, render_generated_metadata_h(export_model, cfg))
    _write_text(model_h_path, render_generated_model_h())
    _write_text(model_c_path, render_generated_model_c(export_model))
    _write_text(procedural_c_path, render_procedural_c(export_model, resolver))
    _write_text(model_instance_h_path, render_model_instance_h())
    _write_text(model_instance_c_path, render_model_instance_c())
    _write_text(solver_c_path, render_solver_c())
    _write_text(runtime_fmi2_c_path, render_runtime_fmi2_c())

    print(f"[emit_c_sources] generated_model.c: {model_c_path.stat().st_size} bytes", flush=True)
    print(f"[emit_c_sources] generated_procedural.c: {procedural_c_path.stat().st_size} bytes", flush=True)

def write_debug_resources(export_model: ExportModel, cfg: ExportConfig, resources_dir: Path) -> None:
    if cfg.include_export_model_resource:
        _write_text(resources_dir / "export_model.json", json.dumps(_json_compatible(export_model.to_dict()), indent=2, sort_keys=True))
    if cfg.include_snapshot_resource:
        _write_text(resources_dir / "snapshot.json", json.dumps(_json_compatible(export_model.source_snapshot), indent=2, sort_keys=True))


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

    # Resolve every compiler operand before changing the child working
    # directory so direct builds remain independent from the caller location.
    resolved_source_dir: Path = source_dir.resolve()
    resolved_build_dir: Path = build_dir.resolve()
    output_path: Path = resolved_build_dir / cfg.library_name
    compiler_path: Path = Path(compiler_cmd)
    compiler_working_directory: Path | None
    if compiler_path.is_absolute():
        # MSYS2 compiler helpers load sibling runtime DLLs from the compiler
        # directory. A scoped child cwd provides that lookup without PATH edits.
        compiler_working_directory = compiler_path.parent
    else:
        compiler_working_directory = None
    cmd: list[str] = list()
    cmd.append(compiler_cmd)
    cmd.extend(_direct_build_link_flags(cfg.target_platform))
    cmd.extend(_direct_build_compile_flags(cfg.target_platform))
    cmd.extend(["-I", str(resolved_source_dir / "include")])
    cmd.extend(["-I", str(resolved_source_dir / "src")])
    cmd.extend(["-o", str(output_path)])
    cmd.append(str(resolved_source_dir / "src" / "runtime_fmi2.c"))
    cmd.append(str(resolved_source_dir / "src" / "model_instance.c"))
    cmd.append(str(resolved_source_dir / "src" / "solver.c"))
    cmd.append(str(resolved_source_dir / "src" / "generated_model.c"))
    cmd.append(str(resolved_source_dir / "src" / "generated_procedural.c"))
    cmd.extend(_direct_build_math_flags(cfg.target_platform))

    print("Direct C compiler build starting...", flush=True)
    print(" ".join(cmd), flush=True)
    subprocess.run(
        cmd,
        check=True,
        text=True,
        env=env,
        cwd=compiler_working_directory,
    )
    print("Direct C compiler build finished.", flush=True)

    if not output_path.exists():
        raise FileNotFoundError(f"Direct gcc build did not produce {output_path}")
    else:
        pass
    return output_path


def build_shared_library(cfg: ExportConfig, source_dir: Path, build_dir: Path) -> Path:
    """
    Build the platform-specific shared library for one exported FMI 2.0 ME runtime.

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
    else:
        pass
    try:

        print("CMake configure starting...", flush=True)
        print(" ".join(configure_cmd), flush=True)
        subprocess.run(configure_cmd, check=True, text=True, env=env)

        print("CMake build starting...", flush=True)
        subprocess.run(
            [cmake_cmd, "--build", str(build_dir), "--config", "Release"],
            check=True,
            text=True,
            env=env,
        )
        print("CMake build finished.", flush=True)

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
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"CMake build failed: {exc}", flush=True)
        print("Falling back to direct C compiler build...", flush=True)

    return _direct_c_build(cfg, source_dir, build_dir)
