# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Set, Tuple

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.IO.dynamic_model_import_types import (
    DynamicModelImportBundle,
    DynamicModelImportEntry,
    DynamicModelImportSource,
    DynamicModelPersistenceKind,
    DynamicModelPersistenceSpec,
    _emit_dynamic_model_import_progress,
)
from VeraGridEngine.IO.dynamic_model_import_utils import (
    sanitize_dynamic_model_file_stem,
)
from VeraGridEngine.IO.modelica.modelica_parser import (
    ExternalFunc,
    LogicExpr,
    ModelicaXMLParser,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import (
    BinOp,
    Const,
    Expr,
    Func,
    Func2,
    UnOp,
    Var,
)
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import DeviceType


def _collect_vars_from_modelica_expr(
        expression: Expr | LogicExpr | ExternalFunc,
        vars_found: Dict[int, Var],
) -> None:
    """
    Collect every symbolic variable referenced by one Modelica-derived expression.

    :param expression: Modelica-derived symbolic expression.
    :param vars_found: UID-indexed variable collector.
    :return: None.
    """
    if isinstance(expression, Var):
        vars_found[expression.uid] = expression
        return

    if isinstance(expression, BinOp):
        _collect_vars_from_modelica_expr(expression.left, vars_found)
        _collect_vars_from_modelica_expr(expression.right, vars_found)
        return

    if isinstance(expression, UnOp):
        _collect_vars_from_modelica_expr(expression.operand, vars_found)
        return

    if isinstance(expression, Func):
        _collect_vars_from_modelica_expr(expression.arg, vars_found)
        return

    if isinstance(expression, Func2):
        _collect_vars_from_modelica_expr(expression.arg1, vars_found)
        _collect_vars_from_modelica_expr(expression.arg2, vars_found)
        return

    if isinstance(expression, (ExternalFunc, LogicExpr)):
        for arg_expression in expression.args:
            _collect_vars_from_modelica_expr(arg_expression, vars_found)


def _split_modelica_residual_equation(
        equation: Expr,
) -> Tuple[Var | None, Expr | None]:
    """
    Split one residual-form Modelica equation into ``lhs`` and ``rhs``.

    The experimental Modelica parser stores equations as ``lhs - rhs = 0``
    symbolic residuals. Importing them into VeraGrid requires recovering the
    target variable on the left-hand side and the explicit right-hand side.

    :param equation: Residual-form equation.
    :return: Pair ``(lhs_var, rhs_expr)`` or ``(None, None)`` when the pattern is unsupported.
    """
    if not isinstance(equation, BinOp):
        return None, None

    if equation.op != "-":
        return None, None

    if not isinstance(equation.left, Var):
        return None, None

    return equation.left, equation.right


def _append_unique_var(target_list: List[Var], candidate_var: Var) -> None:
    """
    Append one variable only when its UID is not already present.

    :param target_list: Output variable list.
    :param candidate_var: Candidate variable.
    :return: None.
    """
    existing_var: Var
    for existing_var in target_list:
        if existing_var.uid == candidate_var.uid:
            return
        else:
            pass

    target_list.append(candidate_var)


def _build_modelica_parameter_list(
        collected_vars: Dict[int, Var],
        state_vars: List[Var],
        algebraic_vars: List[Var],
        diff_vars: List[Var],
) -> List[Var]:
    """
    Build the parameter-variable list from one parsed Modelica symbol set.

    :param collected_vars: UID-indexed variable collector.
    :param state_vars: State variables already classified.
    :param algebraic_vars: Algebraic variables already classified.
    :param diff_vars: Differential variables already classified.
    :return: Parameter-variable list.
    """
    state_uids: Set[int] = set()
    algebraic_uids: Set[int] = set()
    diff_uids: Set[int] = set()
    parameter_vars: List[Var] = list()
    candidate_var: Var

    for candidate_var in state_vars:
        state_uids.add(candidate_var.uid)

    for candidate_var in algebraic_vars:
        algebraic_uids.add(candidate_var.uid)

    for candidate_var in diff_vars:
        diff_uids.add(candidate_var.uid)

    for candidate_var in collected_vars.values():
        if candidate_var.name == "time":
            pass
        else:
            if candidate_var.uid in state_uids:
                pass
            else:
                if candidate_var.uid in algebraic_uids:
                    pass
                else:
                    if candidate_var.uid in diff_uids:
                        pass
                    else:
                        parameter_vars.append(candidate_var)

    return parameter_vars


def _build_modelica_parameter_mapping(
        parser: ModelicaXMLParser,
        parameter_vars: List[Var],
) -> Dict[Var, Const]:
    """
    Build one editable runtime-parameter mapping for one imported Modelica template.

    :param parser: Parsed Modelica source.
    :param parameter_vars: Classified parameter variables.
    :return: Parameter-to-constant mapping.
    """
    parameter_mapping: Dict[Var, Const] = dict()
    parameter_var: Var

    for parameter_var in parameter_vars:
        initial_value: float | None = parser.initial_guesses.get(parameter_var.uid, None)

        if initial_value is None:
            parameter_mapping[parameter_var] = Const(None)
        else:
            parameter_mapping[parameter_var] = Const(float(initial_value))

    return parameter_mapping


def _build_modelica_initialization_maps(
        parser: ModelicaXMLParser,
        state_vars: List[Var],
        algebraic_vars: List[Var],
        diff_vars: List[Var],
) -> Tuple[Dict[Var, Expr], Dict[Var, Expr]]:
    """
    Build ``init_eqs`` and ``diff_init_eqs`` from parsed Modelica initial equations.

    :param parser: Parsed Modelica source.
    :param state_vars: Classified state variables.
    :param algebraic_vars: Classified algebraic variables.
    :param diff_vars: Classified differential variables.
    :return: Pair ``(init_eqs, diff_init_eqs)``.
    """
    init_eqs: Dict[Var, Expr] = dict()
    diff_init_eqs: Dict[Var, Expr] = dict()
    state_uids: Set[int] = set()
    algebraic_uids: Set[int] = set()
    diff_uids: Set[int] = set()
    equation: Expr

    for state_var in state_vars:
        state_uids.add(state_var.uid)

    for algebraic_var in algebraic_vars:
        algebraic_uids.add(algebraic_var.uid)

    for diff_var in diff_vars:
        diff_uids.add(diff_var.uid)

    for equation in parser.initial_equations:
        lhs_var: Var | None
        rhs_expr: Expr | None
        lhs_var, rhs_expr = _split_modelica_residual_equation(equation)

        if lhs_var is None or rhs_expr is None:
            pass
        else:
            if lhs_var.uid in diff_uids:
                diff_init_eqs[lhs_var] = rhs_expr
            else:
                if lhs_var.uid in state_uids or lhs_var.uid in algebraic_uids:
                    init_eqs[lhs_var] = rhs_expr
                else:
                    pass

    state_var: Var
    for state_var in state_vars:
        if state_var in init_eqs:
            pass
        else:
            guessed_value: float | None = parser.initial_guesses.get(state_var.uid, None)
            if guessed_value is None:
                pass
            else:
                init_eqs[state_var] = Const(float(guessed_value))

    algebraic_var: Var
    for algebraic_var in algebraic_vars:
        if algebraic_var in init_eqs:
            pass
        else:
            guessed_value = parser.initial_guesses.get(algebraic_var.uid, None)
            if guessed_value is None:
                pass
            else:
                init_eqs[algebraic_var] = Const(float(guessed_value))

    diff_var: Var
    for diff_var in diff_vars:
        if diff_var in diff_init_eqs:
            pass
        else:
            guessed_value = parser.initial_guesses.get(diff_var.uid, None)
            if guessed_value is None:
                pass
            else:
                diff_init_eqs[diff_var] = Const(float(guessed_value))

    return init_eqs, diff_init_eqs


def _build_modelica_equation_partition(
        parser: ModelicaXMLParser,
) -> Tuple[List[Var], List[Var], List[Var], List[Expr], List[Expr], Dict[Var, Const], Dict[Var, Expr], Dict[Var, Expr], List[str]]:
    """
    Partition one parsed Modelica source into VeraGrid EMT template structures.

    :param parser: Parsed Modelica source.
    :return: State vars, diff vars, algebraic vars, state equations, algebraic equations,
        parameter mapping, init_eqs, diff_init_eqs, and warning messages.
    """
    collected_vars: Dict[int, Var] = dict()
    state_vars: List[Var] = list()
    diff_vars: List[Var] = list()
    algebraic_vars: List[Var] = list()
    state_eqs: List[Expr] = list()
    algebraic_eqs: List[Expr] = list()
    warnings_text: List[str] = list()
    equation: Expr

    for equation in parser.equations:
        _collect_vars_from_modelica_expr(equation, collected_vars)

    for equation in parser.initial_equations:
        _collect_vars_from_modelica_expr(equation, collected_vars)

    for condition_expr, statement_list in parser.when_equations.items():
        _collect_vars_from_modelica_expr(condition_expr, collected_vars)
        for equation in statement_list:
            _collect_vars_from_modelica_expr(equation, collected_vars)

    for candidate_var in collected_vars.values():
        if candidate_var.name.startswith("d_") and candidate_var.base_var is not None:
            _append_unique_var(diff_vars, candidate_var)
            _append_unique_var(state_vars, candidate_var.base_var)
        else:
            pass

    for equation in parser.equations:
        lhs_var: Var | None
        rhs_expr: Expr | None
        lhs_var, rhs_expr = _split_modelica_residual_equation(equation)

        if lhs_var is None or rhs_expr is None:
            warnings_text.append(f"Unsupported Modelica equation shape skipped: {equation}")
        else:
            if lhs_var.name.startswith("d_") and lhs_var.base_var is not None:
                state_eqs.append(rhs_expr)
            else:
                _append_unique_var(algebraic_vars, lhs_var)
                algebraic_eqs.append(equation)

    if len(parser.when_equations) > 0:
        warnings_text.append("Modelica when-equations are not imported yet and were ignored.")
    else:
        pass

    parameter_vars: List[Var] = _build_modelica_parameter_list(
        collected_vars=collected_vars,
        state_vars=state_vars,
        algebraic_vars=algebraic_vars,
        diff_vars=diff_vars,
    )
    parameter_mapping: Dict[Var, Const] = _build_modelica_parameter_mapping(parser, parameter_vars)
    init_eqs: Dict[Var, Expr]
    diff_init_eqs: Dict[Var, Expr]
    init_eqs, diff_init_eqs = _build_modelica_initialization_maps(
        parser=parser,
        state_vars=state_vars,
        algebraic_vars=algebraic_vars,
        diff_vars=diff_vars,
    )

    return (
        state_vars,
        diff_vars,
        algebraic_vars,
        state_eqs,
        algebraic_eqs,
        parameter_mapping,
        init_eqs,
        diff_init_eqs,
        warnings_text,
    )


def _build_modelica_emt_template(xml_path: str) -> Tuple[EmtModelTemplate | None, List[str]]:
    """
    Build one generic EMT template from one flattened Modelica XML source.

    :param xml_path: Source XML file path.
    :return: Pair ``(template_or_none, warnings_text)``.
    """
    parser: ModelicaXMLParser = ModelicaXMLParser(xml_source=xml_path, is_file=True)
    model_name: str = Path(xml_path).stem
    parser.parse_and_build(block_name=model_name)

    state_vars: List[Var]
    diff_vars: List[Var]
    algebraic_vars: List[Var]
    state_eqs: List[Expr]
    algebraic_eqs: List[Expr]
    parameter_mapping: Dict[Var, Const]
    init_eqs: Dict[Var, Expr]
    diff_init_eqs: Dict[Var, Expr]
    warnings_text: List[str]
    (
        state_vars,
        diff_vars,
        algebraic_vars,
        state_eqs,
        algebraic_eqs,
        parameter_mapping,
        init_eqs,
        diff_init_eqs,
        warnings_text,
    ) = _build_modelica_equation_partition(parser)

    if len(state_eqs) == 0 and len(algebraic_eqs) == 0:
        warnings_text.append("No supported continuous equations were extracted from the Modelica XML file.")
        return None, warnings_text
    else:
        pass

    template: EmtModelTemplate = EmtModelTemplate(name=model_name)
    template.tpe = DeviceType.NoDevice
    template.block = Block(
        name=model_name,
        state_vars=state_vars,
        state_eqs=state_eqs,
        diff_vars=diff_vars,
        algebraic_vars=algebraic_vars,
        algebraic_eqs=algebraic_eqs,
        event_dict=parameter_mapping,
        init_eqs=init_eqs,
        diff_init_eqs=diff_init_eqs,
    )
    return template, warnings_text


def _build_modelica_persistence_spec(xml_path: str, template_name: str) -> DynamicModelPersistenceSpec:
    """
    Build the persistence descriptor for one imported Modelica template.

    :param xml_path: Source XML path.
    :param template_name: Template name.
    :return: Persistence descriptor.
    """
    return DynamicModelPersistenceSpec(
        kind=DynamicModelPersistenceKind.ModelicaXml,
        source_path=xml_path,
        template_name=template_name,
        module_stem=sanitize_dynamic_model_file_stem(text=template_name),
    )


def build_modelica_dynamic_model_import_bundle(xml_path: str) -> Tuple[DynamicModelImportBundle, Logger]:
    """
    Parse one flattened Modelica XML file into one import bundle.

    :param xml_path: Source Modelica XML path.
    :return: Pair ``(bundle, logger)``.
    """
    logger: Logger = Logger()
    template: EmtModelTemplate | None
    warnings_text: List[str]
    template, warnings_text = _build_modelica_emt_template(xml_path)
    notes_lines: List[str] = list()
    notes_text: str
    entry: DynamicModelImportEntry

    if template is None:
        logger.add_error(msg="Modelica import failed", value=xml_path)
        notes_lines.append("Template could not be materialized.")
    else:
        pass

    for warning_text in warnings_text:
        notes_lines.append(warning_text)
        logger.add_warning(msg="Modelica import warning", value=warning_text)

    notes_text = "\n".join(notes_lines)
    entry = DynamicModelImportEntry(
        unique_key=f"modelica|{Path(xml_path).stem}",
        display_name=Path(xml_path).stem,
        source_tpe=DynamicModelImportSource.ModelicaXml,
        source_block=None if template is None else template.block,
        notes_text=notes_text,
        persistence_spec=None if template is None else _build_modelica_persistence_spec(xml_path, template.name),
    )
    bundle = DynamicModelImportBundle(
        source_tpe=DynamicModelImportSource.ModelicaXml,
        source_path=xml_path,
        entries=list([entry]),
    )
    return bundle, logger


def build_modelica_dynamic_model_import_bundle_with_progress(
        xml_path: str,
        progress_callback: Callable[[int, str], None] | None = None,
) -> Tuple[DynamicModelImportBundle, Logger]:
    """
    Parse one flattened Modelica XML file into one import bundle with visible progress.

    :param xml_path: Source Modelica XML path.
    :param progress_callback: Optional UI progress callback.
    :return: Pair ``(bundle, logger)``.
    """
    bundle: DynamicModelImportBundle
    logger: Logger

    _emit_dynamic_model_import_progress(progress_callback, 0, "Scanning Modelica XML import request...")
    _emit_dynamic_model_import_progress(progress_callback, 20, "Parsing flattened Modelica XML...")
    bundle, logger = build_modelica_dynamic_model_import_bundle(xml_path)
    _emit_dynamic_model_import_progress(progress_callback, 85, "Building Modelica import catalogue...")
    _emit_dynamic_model_import_progress(progress_callback, 100, "Modelica dynamic model catalogue ready")
    return bundle, logger
