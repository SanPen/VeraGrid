# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Any

from . import compat
from .expr_to_c import ExprToCVisitor
from .export_ir import ExportEventIndicator, ExportLogicEntry, ExportModel
from .variable_map import CVariableResolver

_dict_to_expr = compat._dict_to_expr


def _expr_like_from_dict(data: dict[str, Any]) -> Any:
    kind = str(data.get("kind", "Expr"))
    if kind == "Expr":
        return _dict_to_expr(data["expr"])
    if kind == "Comparison":
        rhs_raw = data["rhs"]
        rhs: Any
        if bool(data.get("rhs_is_expr", False)):
            rhs = _dict_to_expr(rhs_raw)
        else:
            rhs = rhs_raw
        return compat.Comparison(lhs=_dict_to_expr(data["lhs"]), op=compat.CmpOp(str(data["op"])), rhs=rhs)
    raise ValueError(f"Unsupported procedural expression kind: {kind!r}")


def _render_indicator_expr(visitor: ExprToCVisitor, value: Any) -> str:
    if not isinstance(value, dict) or "kind" not in value:
        raise ValueError(f"Unsupported procedural indicator value: {value!r}")
    kind = str(value.get("kind", "Expr"))
    if kind == "Expr":
        expr = _expr_like_from_dict(value)
        return f"({visitor.render(expr)} - 0.5)"
    comparison = _expr_like_from_dict(value)
    left = visitor.visit(comparison.lhs)
    rhs_expr = comparison.rhs if isinstance(comparison.rhs, compat.Expr) else compat.Const(float(comparison.rhs))
    right = visitor.visit(rhs_expr)
    left_code = left.code
    right_code = right.code
    if comparison.op in {compat.CmpOp.GE, compat.CmpOp.GT, compat.CmpOp.EQ}:
        return f"({left_code} - {right_code})"
    if comparison.op in {compat.CmpOp.LE, compat.CmpOp.LT}:
        return f"({right_code} - {left_code})"
    raise ValueError(f"Unsupported comparison operator {comparison.op!r}")


def _render_numeric(visitor: ExprToCVisitor, value: Any) -> str:
    if isinstance(value, dict) and "kind" in value:
        kind = str(value.get("kind", "Expr"))
        if kind == "Comparison":
            indicator = _render_indicator_expr(visitor, value)
            return f"(({indicator}) > 0.0 ? 1.0 : 0.0)"
        return visitor.render(_expr_like_from_dict(value))
    if isinstance(value, (int, float, bool)):
        return visitor.render(float(value))
    if isinstance(value, str):
        return visitor.render(compat.Var(value))
    if isinstance(value, compat.Expr):
        return visitor.render(value)
    raise ValueError(f"Unsupported procedural numeric value: {value!r}")


def _render_bool_runtime(visitor: ExprToCVisitor, value: Any) -> str:
    if isinstance(value, dict) and str(value.get("kind", "Expr")) == "Comparison":
        return f"({_render_indicator_expr(visitor, value)} > 0.0)"
    return f"(({_render_numeric(visitor, value)}) > 0.5)"


def _render_bool_event(visitor: ExprToCVisitor, value: Any) -> str:
    if isinstance(value, dict) and str(value.get("kind", "Expr")) == "Comparison":
        return f"({_render_indicator_expr(visitor, value)} >= 0.0)"
    return f"(({_render_numeric(visitor, value)}) > 0.5)"


def _target_expr(resolver: CVariableResolver, name: str) -> str:
    variable = resolver.by_name.get(name)
    if variable is None:
        raise KeyError(f"Unknown procedural target variable {name!r}")
    return resolver.resolve_target(variable.uid)


def _render_apply_initial(lines: list[str], entry: ExportLogicEntry, visitor: ExprToCVisitor, resolver: CVariableResolver) -> None:
    base_r = entry.index * 4
    base_i = entry.index * 2
    data = entry.data
    if entry.logic_type == "fixed_sample":
        target = _target_expr(resolver, str(data["output_var_name"]))
        condition = _render_bool_runtime(visitor, data["condition_expr"])
        lines.extend(
            [
                f"    /* {entry.name or entry.logic_type} */",
                f"    if (!instance->logic_ints[{base_i}]) {{",
                f"        {target} = {condition} ? 1.0 : 0.0;",
                f"        instance->logic_ints[{base_i}] = 1;",
                "    }",
            ]
        )
    elif entry.logic_type == "sampled_value":
        target = _target_expr(resolver, str(data["output_var_name"]))
        source = _render_numeric(visitor, data["source_expr"])
        lines.extend([f"    /* {entry.name or entry.logic_type} */", f"    {target} = {source};"])
    elif entry.logic_type == "flipflop":
        target = _target_expr(resolver, str(data["output_var_name"]))
        set_expr = _render_bool_runtime(visitor, data["set_expr"])
        reset_expr = _render_bool_runtime(visitor, data["reset_expr"])
        lines.extend(
            [
                f"    /* {entry.name or entry.logic_type} */",
                f"    if (!instance->logic_ints[{base_i}]) {{",
                f"        instance->logic_reals[{base_r}] = {set_expr} ? 1.0 : 0.0;",
                f"        instance->logic_ints[{base_i}] = 1;",
                "    }",
                f"    {target} = instance->logic_reals[{base_r}];",
                f"    instance->logic_ints[{base_i + 1}] = {set_expr};",
                f"    instance->logic_ints[{base_i + 2}] = {reset_expr};",
            ]
        )


def _render_completed_step(lines: list[str], entry: ExportLogicEntry, visitor: ExprToCVisitor, resolver: CVariableResolver) -> None:
    data = entry.data
    if entry.logic_type != "sampled_value":
        return
    target = _target_expr(resolver, str(data["output_var_name"]))
    source = _render_numeric(visitor, data["source_expr"])
    lines.extend(
        [
            f"    /* {entry.name or entry.logic_type} */",
            "    {",
            f"      double old_value = {target};",
            f"      double new_value = {source};",
            f"      {target} = new_value;",
            "      if (vg_logic_changed(old_value, new_value)) changed = fmi2True;",
            "    }",
        ]
    )


def _render_new_discrete_states(lines: list[str], entry: ExportLogicEntry, visitor: ExprToCVisitor, resolver: CVariableResolver) -> None:
    base_r = entry.index * 4
    data = entry.data
    if entry.logic_type != "flipflop":
        return
    target = _target_expr(resolver, str(data["output_var_name"]))
    set_expr = _render_bool_event(visitor, data["set_expr"])
    reset_expr = _render_bool_event(visitor, data["reset_expr"])
    lines.extend(
        [
            f"    /* {entry.name or entry.logic_type} */",
            "    {",
            f"      double old_state = instance->logic_reals[{base_r}];",
            f"      double old_target = {target};",
            f"      int set_on = {set_expr};",
            f"      int reset_on = {reset_expr};",
            f"      double new_state = instance->logic_reals[{base_r}];",
            "      if (set_on && !reset_on) new_state = 1.0;",
            "      else if (!set_on && reset_on) new_state = 0.0;",
            f"      instance->logic_reals[{base_r}] = new_state;",
            f"      {target} = new_state;",
            f"      if (vg_logic_changed(old_state, new_state) || vg_logic_changed(old_target, {target})) changed = fmi2True;",
            "    }",
        ]
    )


def _render_indicator(lines: list[str], indicator: ExportEventIndicator, visitor: ExprToCVisitor) -> None:
    lines.append(f"    out[{indicator.index}] = {_render_indicator_expr(visitor, indicator.expr_data)};")


def render_procedural_c(export_model: ExportModel, resolver: CVariableResolver) -> str:
    visitor = ExprToCVisitor(resolver)
    lines: list[str] = [
        '#include "generated_model.h"',
        '#include "generated_metadata.h"',
        '#include "runtime_support.h"',
        "",
        "static int vg_logic_changed(double previous, double current) {",
        "    return fabs(previous - current) > 1e-12;",
        "}",
        "",
        "void generated_procedural_apply_initial(ModelInstance* instance) {",
    ]
    for entry in export_model.logic_entries:
        _render_apply_initial(lines, entry, visitor, resolver)
    if not export_model.logic_entries:
        lines.append("    (void)instance;")
    lines.extend(["}", "", "fmi2Boolean generated_procedural_completed_integrator_step(ModelInstance* instance) {", "    fmi2Boolean changed = fmi2False;"])
    for entry in export_model.logic_entries:
        _render_completed_step(lines, entry, visitor, resolver)
    lines.extend(["    (void)instance;" if not export_model.logic_entries else "", "    return changed;", "}", "", "void generated_procedural_get_event_indicators(ModelInstance* instance, double* out) {"])
    if export_model.event_indicators:
        for indicator in export_model.event_indicators:
            _render_indicator(lines, indicator, visitor)
    else:
        lines.extend(["    (void)instance;", "    (void)out;"])
    lines.extend(["}", "", "fmi2Boolean generated_procedural_new_discrete_states(ModelInstance* instance) {", "    fmi2Boolean changed = fmi2False;"])
    for entry in export_model.logic_entries:
        _render_new_discrete_states(lines, entry, visitor, resolver)
    lines.extend(["    (void)instance;" if not export_model.logic_entries else "", "    return changed;", "}", ""])
    return "\n".join(line for line in lines if line != "")
