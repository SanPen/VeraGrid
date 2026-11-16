# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import keyword
import re
from functools import lru_cache
from pathlib import Path
from typing import Sequence

import numpy as np

from VeraGridEngine import X_Y_Z_Matrix
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import BasicBlockTemplateBuilder
from VeraGridEngine.Templates.template_catalogue import get_template_builder_by_module_name
from VeraGridEngine.Templates.template_types import TemplateDefinition, TemplateProp
from VeraGridEngine.Utils.Symbolic import symbolic as sym
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Comparison, Const, CmpOp, Expr, Var
from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import DeviceType, X_Y_SequenceType


class BasicBlockTemplateDescriptor:
    """
    Explicit, typed description of one shipped catalog template.
    """

    __slots__ = (
        "_template_key",
        "_blkdef_name",
        "_sample_display_name",
        "_display_label",
        "_category_path",
        "_inputs",
        "_outputs",
        "_states",
        "_params",
        "_unsupported_lines",
        "_module_name",
        "_module_filename",
        "_description",
    )

    def __init__(
        self,
        template_key: str,
        blkdef_name: str,
        sample_display_name: str,
        display_label: str,
        category_path: Sequence[str],
        inputs: Sequence[str],
        outputs: Sequence[str],
        states: Sequence[str],
        params: Sequence[str],
        unsupported_lines: Sequence[str],
        module_name: str,
        module_filename: str,
        description: str = "",
    ) -> None:
        """
        Store one immutable catalog descriptor.

        :param template_key: Stable semantic lookup key.
        :param blkdef_name: Raw source block name.
        :param sample_display_name: Clean human-facing source name.
        :param display_label: Unique label exposed in the editor.
        :param category_path: Full editor category path.
        :param inputs: Input names.
        :param outputs: Output names.
        :param states: State names.
        :param params: Runtime parameter names.
        :param unsupported_lines: Pending markers for non editor-ready templates.
        :param module_name: Standalone module stem inside the shipped catalog.
        :param module_filename: Standalone module filename inside the shipped catalog.
        :param description: Human-facing explanation of the block behavior.
        :returns: None.
        """
        self._template_key = template_key
        self._blkdef_name = blkdef_name
        self._sample_display_name = sample_display_name
        self._display_label = display_label
        self._category_path = tuple(category_path)
        self._inputs = tuple(inputs)
        self._outputs = tuple(outputs)
        self._states = tuple(states)
        self._params = tuple(params)
        self._unsupported_lines = tuple(unsupported_lines)
        self._module_name = module_name
        self._module_filename = module_filename
        self._description = description

    @property
    def template_key(self) -> str:
        """
        Return the stable semantic lookup key.

        :returns: Template lookup key.
        """
        return self._template_key

    @property
    def blkdef_name(self) -> str:
        """
        Return the raw imported block name.

        :returns: Raw block name.
        """
        return self._blkdef_name

    @property
    def sample_display_name(self) -> str:
        """
        Return the clean display name derived from the shipped module.

        :returns: Clean source name.
        """
        return self._sample_display_name

    @property
    def display_label(self) -> str:
        """
        Return the unique label exposed by the editor.

        :returns: Unique label.
        """
        return self._display_label

    @property
    def category_path(self) -> Sequence[str]:
        """
        Return the full library category path.

        :returns: Category path.
        """
        return self._category_path

    @property
    def inputs(self) -> Sequence[str]:
        """
        Return the input names.

        :returns: Input-name tuple.
        """
        return self._inputs

    @property
    def outputs(self) -> Sequence[str]:
        """
        Return the output names.

        :returns: Output-name tuple.
        """
        return self._outputs

    @property
    def states(self) -> Sequence[str]:
        """
        Return the state names.

        :returns: State-name tuple.
        """
        return self._states

    @property
    def params(self) -> Sequence[str]:
        """
        Return the runtime parameter names.

        :returns: Parameter-name tuple.
        """
        return self._params

    @property
    def unsupported_lines(self) -> Sequence[str]:
        """
        Return the pending markers for non editor-ready templates.

        :returns: Unsupported marker tuple.
        """
        return self._unsupported_lines

    @property
    def module_name(self) -> str:
        """
        Return the standalone Python module stem.

        :returns: Module stem.
        """
        return self._module_name

    @property
    def module_filename(self) -> str:
        """
        Return the standalone Python filename.

        :returns: Module filename.
        """
        return self._module_filename

    @property
    def description(self) -> str:
        """
        Return the human-facing behavior description.

        :returns: Block behavior description, or an empty string when unspecified.
        """
        return self._description

    @property
    def is_editor_ready(self) -> bool:
        """
        Return whether the template can be exposed in the editor.

        :returns: ``True`` when the template has executable content.
        """
        if len(self._unsupported_lines) == 0:
            return True
        else:
            return False

    @property
    def search_text(self) -> str:
        """
        Build the normalized search text used by the editor filter.

        :returns: Search text.
        """
        tokens: list[str] = list()
        category_name: str

        # The search index mixes the stable human-facing fields so one filter can
        # match label, source name, semantic key, or category.
        tokens.append(self._display_label)
        tokens.append(self._blkdef_name)
        tokens.append(self._sample_display_name)
        tokens.append(self._template_key)
        tokens.append(self._description)

        for category_name in self._category_path:
            tokens.append(category_name)

        return " ".join(tokens).strip()



def get_basic_block_catalog_root() -> Path:
    """
    Return the directory containing the shipped basic block catalog.

    :returns: Catalog root directory.
    """
    return Path(__file__).resolve().parent


def get_basic_block_catalog_templates_dir() -> Path:
    """
    Return the directory with the shipped standalone template modules.

    :returns: Standalone-template directory.
    """
    return get_basic_block_catalog_root() / "Functions"


def _resolve_template_builder_from_descriptor(descriptor: BasicBlockTemplateDescriptor) -> BasicBlockTemplateBuilder:
    """
    Resolve one shipped standalone template builder from the static package registry.

    :param descriptor: Catalog descriptor for the target module.
    :returns: Imported standalone template builder.
    :raises KeyError: Raised when the generated package registry does not expose the descriptor module.
    """
    template_builder: BasicBlockTemplateBuilder | None = (
        get_template_builder_by_module_name(descriptor.module_name)
    )

    # The descriptor snapshot owns the canonical module name, so the runtime can
    # resolve one explicit builder without probing the filesystem or imported module state.
    if template_builder is None:
        raise KeyError(f"Could not resolve standalone template builder for module '{descriptor.module_name}'")
    else:
        return template_builder


def _build_python_symbol_name(raw_name: str) -> str:
    """Convert one catalogue variable name into a valid Python identifier.

    Catalogue display names may contain spaces and mathematical punctuation,
    while the equation editor exposes every symbolic variable as Python source.
    This conversion deliberately affects only variable names and therefore does
    not alter the human-facing template or block labels.

    :param raw_name: Symbolic name emitted by a catalogue template builder.
    :return: Identifier-safe symbolic name.
    """
    # Replace display punctuation with separators while retaining the readable
    # portions of the source name used to identify generated internal symbols.
    safe_name: str = re.sub(r"[^0-9a-zA-Z_]", "_", raw_name)
    safe_name = re.sub(r"_+", "_", safe_name).strip("_")

    if safe_name == "":
        safe_name = "symbol"
    else:
        pass

    # Python identifiers cannot begin with a number or equal a language keyword.
    if safe_name[0].isdigit():
        safe_name = f"symbol_{safe_name}"
    else:
        pass

    if keyword.iskeyword(safe_name):
        safe_name = f"{safe_name}_symbol"
    else:
        pass

    return safe_name


def _build_catalogue_local_symbol_name(
        variable: Var,
        descriptor: BasicBlockTemplateDescriptor,
        template_name: str,
        role_name: str,
        role_index: int,
) -> str:
    """Build one concise local name from generated catalogue metadata.

    Generated modules prefix internal variables with the complete block name
    and append the complete runtime instance name. Removing both repetitions
    retains the meaningful local token while keeping the result compact.

    :param variable: Materialized symbolic variable being named.
    :param descriptor: Stable descriptor of the source catalogue block.
    :param template_name: Runtime block name appended by the generated builder.
    :param role_name: Fallback symbolic role such as ``state`` or ``mode``.
    :param role_index: Zero-based position inside that symbolic role.
    :return: Python-safe local name without the per-template namespace.
    """
    runtime_free_name: str = variable.name
    runtime_suffix: str = f"_{template_name}"
    if runtime_free_name.endswith(runtime_suffix):
        runtime_free_name = runtime_free_name[:-len(runtime_suffix)]
    else:
        pass

    # Differential symbols add ``d_`` before the same generated block prefix.
    # Preserve that mathematical role while normalizing the shared payload.
    is_derivative: bool = runtime_free_name.startswith("d_")
    if is_derivative:
        generated_name: str = runtime_free_name[2:]
    else:
        generated_name = runtime_free_name

    # The standalone generators use either one or two separators between the
    # imported block name and the actual local symbol. Remove only that exact
    # descriptor-owned prefix; mathematical underscores inside local names are
    # therefore preserved.
    double_separator_prefix: str = f"{descriptor.blkdef_name}__"
    single_separator_prefix: str = f"{descriptor.blkdef_name}_"
    if generated_name.startswith(double_separator_prefix):
        local_name: str = generated_name[len(double_separator_prefix):]
    elif generated_name.startswith(single_separator_prefix):
        local_name = generated_name[len(single_separator_prefix):]
    else:
        local_name = generated_name

    if is_derivative:
        local_name = f"d_{local_name}"
    else:
        pass

    safe_local_name: str = _build_python_symbol_name(raw_name=local_name)
    # The local token and catalogue namespace form the persisted identifier;
    # constrain their combined size so generated helper names remain editable.
    maximum_local_name_length: int = 44 - len(
        f"bb_{descriptor.module_name.removeprefix('typ_').split('__', 1)[0]}"
    ) - 1
    if len(safe_local_name) > maximum_local_name_length:
        safe_local_name = f"{role_name[0]}{role_index + 1}"
    else:
        pass
    return safe_local_name


def _register_catalogue_role_symbol_names(
        variables: Sequence[Var],
        descriptor: BasicBlockTemplateDescriptor,
        template_name: str,
        namespace: str,
        role_name: str,
        preferred_names_by_identity: dict[int, str],
) -> None:
    """Register concise preferred names for one ordered variable role.

    The first role that owns a variable is authoritative. This matters for
    output variables that are also present in the algebraic collection and for
    differential variables that retain a reference to their base state.

    :param variables: Ordered variables belonging to the same symbolic role.
    :param descriptor: Stable descriptor of the source catalogue block.
    :param template_name: Runtime name used during materialization.
    :param namespace: Short stable namespace derived from the catalogue type.
    :param role_name: Fallback role used when an imported local name is long.
    :param preferred_names_by_identity: Destination lookup by stable identity.
    :return: None.
    """
    role_index: int
    variable: Var
    for role_index, variable in enumerate(variables):
        variable_identity: int = variable.non_mutable_uid
        if variable_identity not in preferred_names_by_identity:
            local_name: str = _build_catalogue_local_symbol_name(
                variable=variable,
                descriptor=descriptor,
                template_name=template_name,
                role_name=role_name,
                role_index=role_index,
            )
            preferred_names_by_identity[variable_identity] = f"{local_name}_{namespace}"
        else:
            pass


def _build_catalogue_preferred_symbol_names(
        descriptor: BasicBlockTemplateDescriptor,
        root_block: Block,
        template_name: str,
) -> dict[int, str]:
    """Build concise role-aware names for one materialized catalogue tree.

    :param descriptor: Stable descriptor of the source catalogue block.
    :param root_block: Root of the freshly materialized block tree.
    :param template_name: Runtime name used by the generated builder.
    :return: Preferred Python-safe names keyed by non-mutable variable identity.
    """
    preferred_names_by_identity: dict[int, str] = dict()
    namespace: str = f"bb_{descriptor.module_name.removeprefix('typ_').split('__', 1)[0]}"
    owner: Block

    # Public ports and states receive priority because these are the names that
    # users see most often in equations and on the block interface.
    for owner in root_block.get_all_blocks():
        if owner is root_block:
            input_index: int
            for input_index, variable in enumerate(owner.in_vars):
                if input_index < len(descriptor.inputs):
                    preferred_names_by_identity[variable.non_mutable_uid] = (
                        f"{descriptor.inputs[input_index]}_{namespace}"
                    )
                else:
                    pass

            output_index: int
            for output_index, variable in enumerate(owner.out_vars):
                if output_index < len(descriptor.outputs):
                    preferred_names_by_identity[variable.non_mutable_uid] = (
                        f"{descriptor.outputs[output_index]}_{namespace}"
                    )
                else:
                    pass
        else:
            pass

        _register_catalogue_role_symbol_names(
            variables=owner.in_vars,
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="input",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=owner.out_vars,
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="output",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=owner.state_vars,
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="state",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=owner.diff_vars,
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="derivative",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=tuple(owner.event_dict.keys()),
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="parameter",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=tuple(owner.mode_dict.keys()),
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="mode",
            preferred_names_by_identity=preferred_names_by_identity,
        )
        _register_catalogue_role_symbol_names(
            variables=owner.algebraic_vars,
            descriptor=descriptor,
            template_name=template_name,
            namespace=namespace,
            role_name="auxiliary",
            preferred_names_by_identity=preferred_names_by_identity,
        )
    return preferred_names_by_identity


def _rename_new_catalogue_variables(
    variables_by_identity: dict[int, Var],
    previous_identities: set[int],
    reserved_names: set[str],
    renamed_identities: set[int],
    procedural_name_mapping: dict[Expr | str, Expr],
    preferred_names_by_identity: dict[int, str],
    descriptor: BasicBlockTemplateDescriptor,
    template_name: str,
    namespace: str,
) -> None:
    """Give newly materialized catalogue variables unique Python-safe names.

    :param variables_by_identity: Factory variables keyed by stable identity.
    :param previous_identities: Identities that existed before materialization.
    :param reserved_names: Names already owned by the surrounding model.
    :param renamed_identities: New identities already handled through another
        factory collection.
    :param procedural_name_mapping: Old names mapped to their renamed symbolic variables.
    :param preferred_names_by_identity: Role-aware names for variables exposed by the block.
    :param descriptor: Stable descriptor of the source catalogue block.
    :param template_name: Runtime name used during materialization.
    :param namespace: Stable short namespace used for unclassified helper variables.
    :return: None.
    """
    variable_identity: int
    variable: Var

    for variable_identity, variable in variables_by_identity.items():
        if (
            variable_identity not in previous_identities
            and variable_identity not in renamed_identities
        ):
            original_name: str = variable.name
            preferred_name: str | None = preferred_names_by_identity.get(variable.non_mutable_uid, None)
            if preferred_name is not None:
                base_name: str = _build_python_symbol_name(raw_name=preferred_name)
            else:
                # A generated helper that is referenced only from an expression
                # retains its local token even though it is not part of one of
                # the explicit block collections.
                local_name: str = _build_catalogue_local_symbol_name(
                    variable=variable,
                    descriptor=descriptor,
                    template_name=template_name,
                    role_name="symbol",
                    role_index=len(renamed_identities),
                )
                base_name = f"{local_name}_{namespace}"
            candidate_name: str = base_name
            suffix: int = 2

            # Normalization can merge punctuation variants. Allocate a stable
            # suffix so the editor namespace never loses one of those symbols.
            while candidate_name in reserved_names:
                candidate_name = f"{base_name}_{suffix}"
                suffix += 1

            variable.set_name(candidate_name)
            reserved_names.add(candidate_name)
            renamed_identities.add(variable_identity)
            if original_name != candidate_name:
                procedural_name_mapping[original_name] = variable
            else:
                pass
        else:
            pass


def _remap_catalogue_procedural_logic(
    root_block: Block,
    procedural_name_mapping: dict[Expr | str, Expr],
) -> None:
    """Synchronize name-backed procedural references after symbol normalization.

    Procedural entries retain some targets as strings for persisted legacy
    compatibility. Their typed ``remap`` operation updates those strings while
    preserving symbolic expression identities and the concrete logic type.

    :param root_block: Complete materialized catalogue block tree.
    :param procedural_name_mapping: Old symbol names mapped to renamed variables.
    :return: None.
    """
    if len(procedural_name_mapping) > 0:
        owner: Block
        for owner in root_block.get_all_blocks():
            if len(owner.procedural_logic) > 0:
                owner.procedural_logic = list(
                    entry.remap(procedural_name_mapping)
                    for entry in owner.procedural_logic
                )
            else:
                pass
    else:
        pass


def _normalize_materialized_catalogue_symbol_names(
    descriptor: BasicBlockTemplateDescriptor,
    var_factory: VarFactory,
    root_block: Block,
    template_name: str,
    previous_var_identities: set[int],
    previous_diff_var_identities: set[int],
) -> None:
    """Normalize only the variables created by one catalogue materialization.

    The factory can already contain symbols belonging to the surrounding model.
    Those names remain untouched; they only reserve their namespace so newly
    created catalogue variables cannot collide with them.

    :param descriptor: Stable descriptor of the source catalogue block.
    :param var_factory: Factory containing old and newly created variables.
    :param root_block: Complete materialized catalogue block tree.
    :param template_name: Runtime name used by the generated builder.
    :param previous_var_identities: Regular-variable identities present before
        loading.
    :param previous_diff_var_identities: Differential-variable identities present
        before loading.
    :return: None.
    """
    regular_variables: dict[int, Var] = var_factory.get_vars_dict()
    differential_variables: dict[int, Var] = var_factory.get_diff_var_dict()
    reserved_names: set[str] = set()
    renamed_identities: set[int] = set()
    procedural_name_mapping: dict[Expr | str, Expr] = dict()
    preferred_names_by_identity: dict[int, str] = _build_catalogue_preferred_symbol_names(
        descriptor=descriptor,
        root_block=root_block,
        template_name=template_name,
    )
    namespace: str = f"bb_{_build_python_symbol_name(descriptor.template_key)}"
    variable: Var

    # Existing symbols define the namespace that the new template must respect.
    for variable in regular_variables.values():
        if variable.non_mutable_uid in previous_var_identities:
            reserved_names.add(variable.name)
        else:
            pass

    for variable in differential_variables.values():
        if variable.non_mutable_uid in previous_diff_var_identities:
            reserved_names.add(variable.name)
        else:
            pass

    _rename_new_catalogue_variables(
        variables_by_identity=regular_variables,
        previous_identities=previous_var_identities,
        reserved_names=reserved_names,
        renamed_identities=renamed_identities,
        procedural_name_mapping=procedural_name_mapping,
        preferred_names_by_identity=preferred_names_by_identity,
        descriptor=descriptor,
        template_name=template_name,
        namespace=namespace,
    )
    _rename_new_catalogue_variables(
        variables_by_identity=differential_variables,
        previous_identities=previous_diff_var_identities,
        reserved_names=reserved_names,
        renamed_identities=renamed_identities,
        procedural_name_mapping=procedural_name_mapping,
        preferred_names_by_identity=preferred_names_by_identity,
        descriptor=descriptor,
        template_name=template_name,
        namespace=namespace,
    )
    _remap_catalogue_procedural_logic(
        root_block=root_block,
        procedural_name_mapping=procedural_name_mapping,
    )


def load_basic_block_catalog_template(
    descriptor: BasicBlockTemplateDescriptor,
    var_factory: VarFactory,
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Materialize one shipped catalog-derived template on demand.

    :param descriptor: Template descriptor.
    :param var_factory: Variable factory for the new instance.
    :param name: Optional explicit instance name.
    :returns: Materialized EMT template.
    """
    # Snapshot the surrounding model so normalization is strictly limited to
    # the variables allocated by this catalogue builder call.
    previous_var_identities: set[int] = set(var_factory.get_vars_dict().keys())
    previous_diff_var_identities: set[int] = set(var_factory.get_diff_var_dict().keys())
    template_builder: BasicBlockTemplateBuilder = _resolve_template_builder_from_descriptor(descriptor)
    template: EmtModelTemplate = template_builder(var_factory, name)
    _normalize_materialized_catalogue_symbol_names(
        descriptor=descriptor,
        var_factory=var_factory,
        root_block=template.block,
        template_name=template.name,
        previous_var_identities=previous_var_identities,
        previous_diff_var_identities=previous_diff_var_identities,
    )
    return template

def _build_lookup_comparison(lhs: Expr, op: CmpOp, rhs: Expr) -> Expr:
    """
    Build one boolean-like expression used to activate a lookup segment.

    :param lhs: Left-hand side expression.
    :param op: Comparison operator.
    :param rhs: Right-hand side expression.
    :return: Symbolic 0/1 expression.
    """
    comparison: Comparison = Comparison(lhs=lhs, op=op, rhs=rhs)
    return comparison.to_expression()


def _build_interval_selector(value_expr: Expr, lower_var: Var, upper_var: Var | None) -> Expr:
    """
    Build the activation selector for one lookup interval.

    :param value_expr: Evaluated lookup coordinate.
    :param lower_var: Lower interval bound.
    :param upper_var: Optional exclusive upper interval bound.
    :return: Symbolic 0/1 selector.
    """
    lower_expr: Expr = _build_lookup_comparison(value_expr, CmpOp.GE, lower_var)

    if upper_var is None:
        return lower_expr
    else:
        upper_expr: Expr = _build_lookup_comparison(value_expr, CmpOp.LT, upper_var)
        return lower_expr * upper_expr


def _validate_lookup_points(x_points: Sequence[float], y_points: Sequence[float]) -> None:
    """
    Validate one one-dimensional lookup table before building its symbolic block.

    :param x_points: Monotonic abscissa values.
    :param y_points: Ordinated values.
    :return: None.
    :raises ValueError: If the lookup table is not valid.
    """
    point_count: int = len(x_points)
    point_index: int

    if point_count != len(y_points):
        raise ValueError("Lookup table x/y vectors must have the same size")
    else:
        pass

    if point_count < 2:
        raise ValueError("Lookup table requires at least two points")
    else:
        pass

    for point_index in range(point_count - 1):
        if float(x_points[point_index + 1]) > float(x_points[point_index]):
            pass
        else:
            raise ValueError("Lookup table x values must be strictly increasing")


def _normalize_inverse_lookup_points(x_points: Sequence[float], y_points: Sequence[float]) -> tuple[list[float], list[float]]:
    """
    Normalize one inverse lookup table so the driven axis is strictly increasing.

    :param x_points: Original x values.
    :param y_points: Original y values to be inverted.
    :return: Normalized `(x_points, y_points)` where `y_points` are increasing.
    :raises ValueError: If the inverse lookup is not strictly monotonic.
    """
    point_count: int = len(x_points)
    point_index: int
    is_increasing: bool = True
    is_decreasing: bool = True

    if point_count != len(y_points):
        raise ValueError("Inverse lookup x/y vectors must have the same size")
    else:
        pass

    if point_count < 2:
        raise ValueError("Inverse lookup requires at least two points")
    else:
        pass

    for point_index in range(point_count - 1):
        if float(y_points[point_index + 1]) > float(y_points[point_index]):
            is_decreasing = False
        else:
            if float(y_points[point_index + 1]) < float(y_points[point_index]):
                is_increasing = False
            else:
                raise ValueError("Inverse lookup requires strictly monotonic y values")

    if is_increasing:
        return list(float(item) for item in x_points), list(float(item) for item in y_points)
    else:
        if is_decreasing:
            return list(float(item) for item in reversed(x_points)), list(float(item) for item in reversed(y_points))
        else:
            raise ValueError("Inverse lookup requires y values to be strictly monotonic")


def _validate_lookup_matrix(x_points: Sequence[float], y_points: Sequence[float], z_matrix: Sequence[Sequence[float]]) -> None:
    """
    Validate one two-dimensional lookup table before building its symbolic block.

    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :return: None.
    :raises ValueError: If the lookup matrix is not valid.
    """
    x_count: int = len(x_points)
    y_count: int = len(y_points)
    point_index: int
    row_index: int

    # Bilinear and bicubic interpolation both require at least one interval on
    # each axis. Checking this explicitly produces an actionable error instead
    # of a later indexing or linear-algebra failure.
    if x_count >= 2 and y_count >= 2:
        pass
    else:
        raise ValueError("Lookup matrix requires at least two points on each axis")

    # Repeated or descending coordinates make interval selection ambiguous and
    # can introduce divisions by zero in the interpolation equations.
    for point_index in range(x_count - 1):
        if float(x_points[point_index + 1]) > float(x_points[point_index]):
            pass
        else:
            raise ValueError("Lookup matrix x-axis values must be strictly increasing")
    for point_index in range(y_count - 1):
        if float(y_points[point_index + 1]) > float(y_points[point_index]):
            pass
        else:
            raise ValueError("Lookup matrix y-axis values must be strictly increasing")

    if len(z_matrix) == y_count:
        pass
    else:
        raise ValueError("Lookup matrix row count must match the y-axis size")

    for row_index in range(len(z_matrix)):
        if len(z_matrix[row_index]) == x_count:
            pass
        else:
            raise ValueError("Lookup matrix column count must match the x-axis size")


def _build_linear_combination(sample_values: Sequence[Expr], weights: Sequence[float]) -> Expr:
    """
    Build one linear combination of symbolic sample values.

    :param sample_values: Symbolic sample values.
    :param weights: Numeric weights.
    :return: Linear-combination expression.
    """
    result_expr: Expr = Const(0.0)
    sample_index: int

    for sample_index in range(len(sample_values)):
        result_expr = result_expr + sample_values[sample_index] * Const(float(weights[sample_index]))

    return result_expr


def _solve_natural_cubic_second_derivatives(axis_points: Sequence[float], sample_values: np.ndarray) -> np.ndarray:
    """
    Solve the natural cubic spline second derivatives for one numeric surface.

    :param axis_points: Strictly increasing axis values.
    :param sample_values: Numeric sample values on that axis.
    :return: Numeric second-derivative vector.
    """
    point_count: int = len(axis_points)
    second_derivatives: np.ndarray = np.zeros(point_count, dtype=float)
    equation_count: int = point_count - 2
    h_values: np.ndarray = np.diff(np.asarray(axis_points, dtype=float))
    row_index: int

    if point_count <= 2:
        return second_derivatives
    else:
        pass

    matrix_a: np.ndarray = np.zeros((equation_count, equation_count), dtype=float)
    rhs_vector: np.ndarray = np.zeros(equation_count, dtype=float)

    for row_index in range(equation_count):
        if row_index > 0:
            matrix_a[row_index, row_index - 1] = h_values[row_index]
        else:
            pass

        matrix_a[row_index, row_index] = 2.0 * (h_values[row_index] + h_values[row_index + 1])

        if row_index < equation_count - 1:
            matrix_a[row_index, row_index + 1] = h_values[row_index + 1]
        else:
            pass

        rhs_vector[row_index] = 6.0 * (
            (sample_values[row_index + 2] - sample_values[row_index + 1]) / h_values[row_index + 1]
            - (sample_values[row_index + 1] - sample_values[row_index]) / h_values[row_index]
        )

    second_derivatives[1:point_count - 1] = np.linalg.solve(matrix_a, rhs_vector)
    return second_derivatives


@lru_cache(maxsize=32)
def _compute_natural_cubic_segment_weights(axis_points_key: tuple[float, ...]) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], ...]:
    """
    Return linear weights for every natural-cubic spline segment coefficient.

    :param axis_points_key: Hashable axis-point tuple.
    :return: Per-segment coefficient weights `(a, b, c, d)`.
    """
    axis_points: tuple[float, ...] = axis_points_key
    point_count: int = len(axis_points)
    segment_count: int = point_count - 1
    weights_by_segment: list[list[np.ndarray]] = list()
    segment_index: int
    basis_index: int

    for segment_index in range(segment_count):
        weights_by_segment.append(
            list([
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
                np.zeros(point_count, dtype=float),
            ])
        )

    for basis_index in range(point_count):
        basis_values: np.ndarray = np.zeros(point_count, dtype=float)
        basis_values[basis_index] = 1.0
        second_derivatives: np.ndarray = _solve_natural_cubic_second_derivatives(axis_points, basis_values)

        for segment_index in range(segment_count):
            h_value: float = float(axis_points[segment_index + 1] - axis_points[segment_index])
            a_value: float = float(basis_values[segment_index])
            b_value: float = float(
                (basis_values[segment_index + 1] - basis_values[segment_index]) / h_value
                - h_value * (2.0 * second_derivatives[segment_index] + second_derivatives[segment_index + 1]) / 6.0
            )
            c_value: float = float(second_derivatives[segment_index] / 2.0)
            d_value: float = float((second_derivatives[segment_index + 1] - second_derivatives[segment_index]) / (6.0 * h_value))
            weights_by_segment[segment_index][0][basis_index] = a_value
            weights_by_segment[segment_index][1][basis_index] = b_value
            weights_by_segment[segment_index][2][basis_index] = c_value
            weights_by_segment[segment_index][3][basis_index] = d_value

    output_segments: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = list()
    for segment_index in range(segment_count):
        output_segments.append(
            (
                weights_by_segment[segment_index][0],
                weights_by_segment[segment_index][1],
                weights_by_segment[segment_index][2],
                weights_by_segment[segment_index][3],
            )
        )

    return tuple(output_segments)


def _build_cubic_spline_piecewise_expression(
    coord_expr: Expr,
    axis_points: Sequence[float],
    axis_vars: Sequence[Var],
    sample_values: Sequence[Expr],
) -> Expr:
    """
    Build the clipped natural cubic spline expression for one axis.

    :param coord_expr: Lookup coordinate.
    :param axis_points: Strictly increasing numeric axis values.
    :param axis_vars: Strictly increasing symbolic axis variables.
    :param sample_values: Symbolic sample values aligned with the axis.
    :return: Piecewise cubic spline expression.
    """
    point_count: int = len(axis_vars)
    segment_count: int = point_count - 1
    # Clamp the lower exterior region to the first table value. Keeping this
    # region explicit avoids extending the first cubic segment beyond the data.
    result_expr: Expr = sample_values[0] * _build_lookup_comparison(coord_expr, CmpOp.LT, axis_vars[0])
    segment_index: int
    segment_weights: tuple[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], ...] = (
        _compute_natural_cubic_segment_weights(tuple(float(value) for value in axis_points))
    )
    a_weights: np.ndarray
    b_weights: np.ndarray
    c_weights: np.ndarray
    d_weights: np.ndarray

    for segment_index in range(segment_count):
        a_weights, b_weights, c_weights, d_weights = segment_weights[segment_index]
        dx_expr: Expr = coord_expr - axis_vars[segment_index]
        segment_expr: Expr = _build_linear_combination(sample_values, a_weights)
        segment_expr = segment_expr + _build_linear_combination(sample_values, b_weights) * dx_expr
        segment_expr = segment_expr + _build_linear_combination(sample_values, c_weights) * dx_expr * dx_expr
        segment_expr = segment_expr + _build_linear_combination(sample_values, d_weights) * dx_expr * dx_expr * dx_expr

        # Every cubic segment is active only inside its two breakpoints. The
        # former open-ended final segment extrapolated above the table even
        # though this helper's contract specifies clipping.
        selector_expr: Expr = _build_interval_selector(
            coord_expr,
            axis_vars[segment_index],
            axis_vars[segment_index + 1],
        )
        result_expr = result_expr + segment_expr * selector_expr

    # Clamp the upper exterior region symmetrically to the final sample.
    result_expr = result_expr + sample_values[point_count - 1] * _build_lookup_comparison(
        coord_expr,
        CmpOp.GE,
        axis_vars[point_count - 1],
    )
    return result_expr


def _build_segment_expression(
    yi_var: Var,
    x_left_var: Var,
    x_right_var: Var,
    y_left_var: Var,
    y_right_var: Var,
) -> Expr:
    """
    Build one affine interpolation expression between two lookup points.

    :param yi_var: Lookup input variable.
    :param x_left_var: Segment left x value.
    :param x_right_var: Segment right x value.
    :param y_left_var: Segment left y value.
    :param y_right_var: Segment right y value.
    :return: Interpolation expression valid on that segment.
    """
    slope_expr: Expr = (y_right_var - y_left_var) / (x_right_var - x_left_var)
    intercept_expr: Expr = y_left_var - slope_expr * x_left_var
    return slope_expr * yi_var + intercept_expr


def _build_clipped_lookup_expression(yi_var: Var, x_vars: Sequence[Var], y_vars: Sequence[Var]) -> Expr:
    """
    Build the clipped lookup expression for one strictly increasing table.

    :param yi_var: Lookup input variable.
    :param x_vars: Symbolic x-point parameters.
    :param y_vars: Symbolic y-point parameters.
    :return: Piecewise clipped interpolation expression.
    """
    point_count: int = len(x_vars)
    segment_index: int
    result_expr: Expr = y_vars[0] * _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[0])

    for segment_index in range(point_count - 1):
        segment_expr: Expr = _build_segment_expression(
            yi_var=yi_var,
            x_left_var=x_vars[segment_index],
            x_right_var=x_vars[segment_index + 1],
            y_left_var=y_vars[segment_index],
            y_right_var=y_vars[segment_index + 1],
        )

        lower_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.GE, x_vars[segment_index])
        upper_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[segment_index + 1])
        result_expr = result_expr + segment_expr * lower_expr * upper_expr

    result_expr = result_expr + y_vars[point_count - 1] * _build_lookup_comparison(
        yi_var,
        CmpOp.GE,
        x_vars[point_count - 1],
    )
    return result_expr


def _build_unclipped_lookup_expression(yi_var: Var, x_vars: Sequence[Var], y_vars: Sequence[Var]) -> Expr:
    """
    Build the non-clipped lookup expression with linear extrapolation.

    :param yi_var: Lookup input variable.
    :param x_vars: Symbolic x-point parameters.
    :param y_vars: Symbolic y-point parameters.
    :return: Piecewise interpolation plus linear extrapolation expression.
    """
    point_count: int = len(x_vars)
    first_segment_expr: Expr = _build_segment_expression(
        yi_var=yi_var,
        x_left_var=x_vars[0],
        x_right_var=x_vars[1],
        y_left_var=y_vars[0],
        y_right_var=y_vars[1],
    )

    if point_count == 2:
        return first_segment_expr
    else:
        pass

    last_segment_expr: Expr = _build_segment_expression(
        yi_var=yi_var,
        x_left_var=x_vars[point_count - 2],
        x_right_var=x_vars[point_count - 1],
        y_left_var=y_vars[point_count - 2],
        y_right_var=y_vars[point_count - 1],
    )
    segment_index: int
    result_expr: Expr = first_segment_expr * _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[1])

    for segment_index in range(1, point_count - 2):
        segment_expr: Expr = _build_segment_expression(
            yi_var=yi_var,
            x_left_var=x_vars[segment_index],
            x_right_var=x_vars[segment_index + 1],
            y_left_var=y_vars[segment_index],
            y_right_var=y_vars[segment_index + 1],
        )
        lower_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.GE, x_vars[segment_index])
        upper_expr: Expr = _build_lookup_comparison(yi_var, CmpOp.LT, x_vars[segment_index + 1])
        result_expr = result_expr + segment_expr * lower_expr * upper_expr

    result_expr = result_expr + last_segment_expr * _build_lookup_comparison(
        yi_var,
        CmpOp.GE,
        x_vars[point_count - 2],
    )
    return result_expr


def _build_bilinear_cell_expression(
    x_expr: Expr,
    y_expr: Expr,
    x_left_var: Var,
    x_right_var: Var,
    y_lower_var: Var,
    y_upper_var: Var,
    z00_var: Var,
    z10_var: Var,
    z01_var: Var,
    z11_var: Var,
) -> Expr:
    """
    Build one bilinear interpolation expression on a single rectangular cell.

    :param x_expr: Clipped x lookup coordinate.
    :param y_expr: Clipped y lookup coordinate.
    :param x_left_var: Left x bound.
    :param x_right_var: Right x bound.
    :param y_lower_var: Lower y bound.
    :param y_upper_var: Upper y bound.
    :param z00_var: Cell value at `(x_left, y_lower)`.
    :param z10_var: Cell value at `(x_right, y_lower)`.
    :param z01_var: Cell value at `(x_left, y_upper)`.
    :param z11_var: Cell value at `(x_right, y_upper)`.
    :return: Bilinear interpolation expression.
    """
    one_const: Const = Const(1.0)
    tx_expr: Expr = (x_expr - x_left_var) / (x_right_var - x_left_var)
    ty_expr: Expr = (y_expr - y_lower_var) / (y_upper_var - y_lower_var)
    return (
        z00_var * (one_const - tx_expr) * (one_const - ty_expr)
        + z10_var * tx_expr * (one_const - ty_expr)
        + z01_var * (one_const - tx_expr) * ty_expr
        + z11_var * tx_expr * ty_expr
    )


def _build_clipped_lookup_matrix_expression(
    x_input_var: Var,
    y_input_var: Var,
    x_vars: Sequence[Var],
    y_vars: Sequence[Var],
    z_vars: Sequence[Sequence[Var]],
) -> Expr:
    """
    Build the clipped bilinear interpolation expression for one lookup matrix.

    :param x_input_var: X-axis input variable.
    :param y_input_var: Y-axis input variable.
    :param x_vars: Symbolic x-axis parameters.
    :param y_vars: Symbolic y-axis parameters.
    :param z_vars: Symbolic matrix values indexed as `[y][x]`.
    :return: Bilinear interpolation expression.
    """
    x_index: int
    y_index: int
    x_clamped_expr: Expr = sym.hard_sat(x_input_var, x_vars[0], x_vars[len(x_vars) - 1])
    y_clamped_expr: Expr = sym.hard_sat(y_input_var, y_vars[0], y_vars[len(y_vars) - 1])
    result_expr: Expr = Const(0.0)

    for y_index in range(len(y_vars) - 1):
        for x_index in range(len(x_vars) - 1):
            cell_expr: Expr = _build_bilinear_cell_expression(
                x_expr=x_clamped_expr,
                y_expr=y_clamped_expr,
                x_left_var=x_vars[x_index],
                x_right_var=x_vars[x_index + 1],
                y_lower_var=y_vars[y_index],
                y_upper_var=y_vars[y_index + 1],
                z00_var=z_vars[y_index][x_index],
                z10_var=z_vars[y_index][x_index + 1],
                z01_var=z_vars[y_index + 1][x_index],
                z11_var=z_vars[y_index + 1][x_index + 1],
            )

            if x_index == len(x_vars) - 2:
                upper_x_var: Var | None = None
            else:
                upper_x_var = x_vars[x_index + 1]

            if y_index == len(y_vars) - 2:
                upper_y_var: Var | None = None
            else:
                upper_y_var = y_vars[y_index + 1]

            selector_expr: Expr = _build_interval_selector(x_clamped_expr, x_vars[x_index], upper_x_var)
            selector_expr = selector_expr * _build_interval_selector(y_clamped_expr, y_vars[y_index], upper_y_var)
            result_expr = result_expr + cell_expr * selector_expr

    return result_expr


class LookupArrayLinearRuntimeTemplate(TemplateDefinition):
    __slots__ = ()

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="points", units="", descr="Strictly increasing x breakpoints.", tpe=X_Y_SequenceType, value=((0.0, 0.0), (0.02, 1), (0.04, 0.0))),
                TemplateProp(name="clip", units="", descr="If True, clip outside the table; otherwise extrapolate linearly.", tpe=bool, value=True),
                TemplateProp(name="name", units="", descr="Optional explicit runtime template name.", tpe=str, value="lookup_array_linear_runtime"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        points: Sequence[Vec] = self.get_value("points")
        clip: bool = self.get_value("clip")
        name: str = self.get_value("name")

        x_points = list()
        y_points = list()
        for point in points:
            x_points.append(point[0])
            y_points.append(point[1])

        return build_lookup_array_linear_runtime_template(
            vf=self.vf,
            x_points=x_points,
            y_points=y_points,
            clip=clip,
            name=name,
        )



def build_lookup_array_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    clip: bool,
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime one-dimensional linear lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x values.
    :param y_points: Matching y values.
    :param clip: If True, clip outside the table; otherwise extrapolate linearly.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int = len(x_points)
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    parameter_var: Var
    lookup_expr: Expr
    clipped_lookup_expr: Expr
    extrapolated_lookup_expr: Expr
    clip_mode_var: Var
    template: EmtModelTemplate = EmtModelTemplate()

    # Reject malformed tables before allocating equations that contain invalid
    # intervals or divisions by zero.
    _validate_lookup_points(x_points=x_points, y_points=y_points)

    if name is None:
        if clip:
            template_name = f"lookup_array_linear_{point_count}pt"
        else:
            template_name = f"lookup_array_linear_noclipping_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    # Retain the boundary rule as an ordinary mode parameter so reopening
    # General Options can recover it after a save/load round trip.
    clipped_lookup_expr = _build_clipped_lookup_expression(yi_var=yi_var, x_vars=x_vars, y_vars=y_vars)
    extrapolated_lookup_expr = _build_unclipped_lookup_expression(yi_var=yi_var, x_vars=x_vars, y_vars=y_vars)
    clip_mode_var = vf.add_var("lookup_clip_" + template_name)
    lookup_expr = (
        clip_mode_var * clipped_lookup_expr
        + (Const(1.0) - clip_mode_var) * extrapolated_lookup_expr
    )

    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        mode_dict=dict(((clip_mode_var, vf.add_const(1.0 if clip else 0.0, name="clip")),)),
        name=template_name,
    )
    return template

class LookupArrayLinearVariableRuntimeTemplate(TemplateDefinition):
    """Build a linear lookup whose tabulated coordinates are signal inputs."""

    __slots__ = ()

    def __init__(self, vf: VarFactory) -> None:
        """Create the configurable dynamic-table builder.

        :param vf: Variable factory used to allocate the symbolic interface.
        :return: None.
        """
        TemplateDefinition.__init__(
            self,
            vf,
            params=list((
                TemplateProp(
                    name="point_count",
                    units="",
                    descr="Number of signal-driven (x, y) points in the table.",
                    tpe=int,
                    value=3,
                ),
                TemplateProp(
                    name="clip",
                    units="",
                    descr="Clip outside the table instead of extrapolating linearly.",
                    tpe=bool,
                    value=True,
                ),
                TemplateProp(
                    name="name",
                    units="",
                    descr="Optional explicit runtime template name.",
                    tpe=str,
                    value="lookup_array_linear_variable_runtime",
                ),
            )),
        )

    def eval(self) -> EmtModelTemplate:
        """Materialize the dynamic lookup using the selected structure.

        :return: EMT template whose breakpoints and samples are input ports.
        """
        point_count: int = self.get_value("point_count")
        clip: bool = self.get_value("clip")
        name: str = self.get_value("name")
        return build_lookup_array_linear_variable_runtime_template(
            vf=self.vf,
            point_count=point_count,
            clip=clip,
            name=name,
        )


def build_lookup_array_linear_variable_runtime_template(
    vf: VarFactory,
    point_count: int,
    clip: bool,
    name: str | None = None,
) -> EmtModelTemplate:
    """Build a linear lookup whose complete table is supplied by signals.

    The first port is the lookup coordinate, followed by every x breakpoint
    and then every y sample. A stable positional naming scheme allows General
    Options to increase or decrease the point count while retaining surviving
    diagram connections.

    :param vf: Variable factory used to allocate symbolic objects.
    :param point_count: Number of dynamic table points; at least two are required.
    :param clip: Whether values outside the table are clipped or extrapolated.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template with signal-driven table coordinates.
    :raises ValueError: If fewer than two points are requested.
    """
    template_name: str
    if point_count >= 2:
        pass
    else:
        raise ValueError("Dynamic lookup table requires at least two points")

    if name is None:
        template_name = "lookup_array_linear_variable_" + str(point_count) + "pt"
    else:
        template_name = name

    # Allocate the lookup coordinate and stable table-input groups separately
    # so their port order matches the imported variable-table blocks.
    lookup_input: Var = vf.add_var("yi_" + template_name)
    output_variable: Var = vf.add_var("yo_" + template_name)
    x_variables: list[Var] = list()
    y_variables: list[Var] = list()
    point_index: int
    for point_index in range(point_count):
        x_variables.append(vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name))
    for point_index in range(point_count):
        y_variables.append(vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name))

    # Store the boundary choice in the symbolic model so General Options can
    # reconstruct it after persistence without relying on Python-only state.
    clipped_lookup_expression: Expr = _build_clipped_lookup_expression(
        yi_var=lookup_input,
        x_vars=x_variables,
        y_vars=y_variables,
    )
    extrapolated_lookup_expression: Expr = _build_unclipped_lookup_expression(
        yi_var=lookup_input,
        x_vars=x_variables,
        y_vars=y_variables,
    )
    clip_mode_variable: Var = vf.add_var("lookup_clip_" + template_name)
    lookup_expression: Expr = (
        clip_mode_variable * clipped_lookup_expression
        + (Const(1.0) - clip_mode_variable) * extrapolated_lookup_expression
    )

    input_variables: list[Var] = list((lookup_input,))
    input_variables.extend(x_variables)
    input_variables.extend(y_variables)
    template: EmtModelTemplate = EmtModelTemplate(name=template_name)
    template.tpe = DeviceType.NoDevice
    template.block = Block(
        algebraic_vars=list((output_variable,)),
        algebraic_eqs=list((output_variable - lookup_expression,)),
        in_vars=input_variables,
        out_vars=list((output_variable,)),
        mode_dict=dict(((clip_mode_variable, vf.add_const(1.0 if clip else 0.0, name="clip")),)),
        name=template_name,
    )
    return template


# ---
class InverseLookupArrayLinearRuntimeTemplate(TemplateDefinition):
    __slots__ = ()

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(
                    name="points",
                    units="",
                    descr="Points with strictly monotonic y values so the table can be inverted.",
                    tpe=X_Y_SequenceType,
                    value=((0.0, 0.0), (0.02, 0.5), (0.04, 1.0)),
                ),
                TemplateProp(name="name", units="", descr="Name of the runtime template.", tpe=str, value="inverse_lookup_array_linear_runtime"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        points: Sequence[Vec] = self.get_value("points")
        name: str | None = self.get_value("name")

        x_points = list()
        y_points = list()
        for point in points:
            x_points.append(point[0])
            y_points.append(point[1])

        return build_inverse_lookup_array_linear_runtime_template(
            self.vf, x_points, y_points, name
        )


def build_inverse_lookup_array_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime inverse linear lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Original x values.
    :param y_points: Original y values to invert.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Var] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    # Validate the x table as well as the driven y axis normalized below. This
    # keeps the inverse relation deterministic in both directions.
    _validate_lookup_points(x_points=x_points, y_points=y_points)
    normalized_x_points: list[float]
    normalized_y_points: list[float]

    normalized_x_points, normalized_y_points = _normalize_inverse_lookup_points(x_points=x_points, y_points=y_points)
    point_count = len(normalized_x_points)

    if name is None:
        template_name = f"inverse_lookup_array_linear_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(normalized_x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(normalized_y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    lookup_expr = _build_clipped_lookup_expression(yi_var=yi_var, x_vars=y_vars, y_vars=x_vars)
    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


class LookupMatrixLinearRuntimeTemplate(TemplateDefinition):
    __slots__ = ()

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[

                TemplateProp(name="x_y_z_values", units="", descr="Flat matrix values in row-major order (y then x).", tpe=X_Y_Z_Matrix, value=((0.0, 0.1), (0.02, 1), ((0.04, 0.0),(0.1, 0.2)))),
                TemplateProp(name="name", units="", descr="Optional explicit runtime template name.", tpe=str, value="lookup_matrix_linear_runtime"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        x_y_z_values = self.get_value("x_y_z_values")
        name: str = self.get_value("name")

        x_points = x_y_z_values[0]
        y_points = x_y_z_values[1]

        z_matrix = x_y_z_values[2]

        return build_lookup_matrix_linear_runtime_template(
            vf=self.vf,
            x_points=x_points,
            y_points=y_points,
            z_matrix=z_matrix,
            name=name,
        )


def build_lookup_matrix_linear_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    z_matrix: Sequence[Sequence[float]],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime bilinear lookup matrix template from explicit axes and values.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    x_count: int = len(x_points)
    y_count: int = len(y_points)
    x_index: int
    y_index: int
    x_input_var: Var
    y_input_var: Var
    output_var: Var
    x_axis_vars: list[Var] = list()
    y_axis_vars: list[Var] = list()
    z_value_vars: list[list[Var]] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_matrix(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    if name is None:
        template_name = f"lookup_matrix_linear_{x_count}x{y_count}"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    x_input_var = vf.add_var("yi1_" + template_name)
    y_input_var = vf.add_var("yi2_" + template_name)
    output_var = vf.add_var("yo_" + template_name)

    for x_index in range(x_count):
        parameter_var = vf.add_var("arr_x" + str(x_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[x_index]), name="arr_x" + str(x_index + 1))
        x_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        parameter_var = vf.add_var("arr_y" + str(y_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[y_index]), name="arr_y" + str(y_index + 1))
        y_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        row_vars: list[Var] = list()
        for x_index in range(x_count):
            parameter_var = vf.add_var("arr_z" + str(y_index + 1) + "_" + str(x_index + 1) + "_" + template_name)
            template.block.event_dict[parameter_var] = vf.add_const(
                float(z_matrix[y_index][x_index]),
                name="arr_z" + str(y_index + 1) + "_" + str(x_index + 1),
            )
            row_vars.append(parameter_var)
        z_value_vars.append(row_vars)

    lookup_expr = _build_clipped_lookup_matrix_expression(
        x_input_var=x_input_var,
        y_input_var=y_input_var,
        x_vars=x_axis_vars,
        y_vars=y_axis_vars,
        z_vars=z_value_vars,
    )

    template.block = Block(
        algebraic_vars=list([output_var]),
        algebraic_eqs=list([output_var - lookup_expr]),
        in_vars=list([x_input_var, y_input_var]),
        out_vars=list([output_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


class LookupArraySplineRuntimeTemplate(TemplateDefinition):
    __slots__ = ()

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="points", units="", descr="Strictly increasing x breakpoints.", tpe=X_Y_SequenceType,
                             value=((0.0, 0.0), (0.02, 1), (0.04, 0.0))),
                TemplateProp(name="name", units="", descr="Optional explicit runtime template name.", tpe=str, value="lookup_array_spline_runtime"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        points: Sequence[Vec] = self.get_value("points")
        name: str | None = self.get_value("name")

        x_points = list()
        y_points = list()
        for point in points:
            x_points.append(point[0])
            y_points.append(point[1])

        return build_lookup_array_spline_runtime_template(
            vf=self.vf,
            x_points=x_points,
            y_points=y_points,
            name=name,
        )

def build_lookup_array_spline_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime one-dimensional spline lookup template from explicit points.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x values.
    :param y_points: Matching y values.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    point_count: int = len(x_points)
    point_index: int
    yi_var: Var
    yo_var: Var
    x_vars: list[Var] = list()
    y_vars: list[Expr] = list()
    parameter_var: Var
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    # Spline coefficient construction assumes a valid ordered point table.
    _validate_lookup_points(x_points=x_points, y_points=y_points)

    if name is None:
        template_name = f"lookup_array_spline_{point_count}pt"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    yi_var = vf.add_var("yi_" + template_name)
    yo_var = vf.add_var("yo_" + template_name)

    for point_index in range(point_count):
        parameter_var = vf.add_var("arr_x" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[point_index]), name="arr_x" + str(point_index + 1))
        x_vars.append(parameter_var)

        parameter_var = vf.add_var("arr_y" + str(point_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[point_index]), name="arr_y" + str(point_index + 1))
        y_vars.append(parameter_var)

    lookup_expr = _build_cubic_spline_piecewise_expression(
        coord_expr=yi_var,
        axis_points=x_points,
        axis_vars=x_vars,
        sample_values=y_vars,
    )

    template.block = Block(
        algebraic_vars=list([yo_var]),
        algebraic_eqs=list([yo_var - lookup_expr]),
        in_vars=list([yi_var]),
        out_vars=list([yo_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template


class LookupMatrixSplineRuntimeTemplate(TemplateDefinition):
    __slots__ = ()

    def __init__(self, vf):
        super().__init__(
            vf,
            params=[
                TemplateProp(name="x_y_z_values", units="", descr="Flat matrix values in row-major order (y then x).", tpe=X_Y_Z_Matrix, value=((0.0, 0.1), (0.02, 1), ((0.04, 0.0), (0.1, 0.2)))),
                TemplateProp(name="name", units="", descr="Optional explicit runtime template name.", tpe=str, value="lookup_matrix_spline_runtime"),
            ]
        )

    def eval(self) -> EmtModelTemplate:
        x_y_z_values = self.get_value("x_y_z_values")
        name: str = self.get_value("name")

        x_points = x_y_z_values[0]
        y_points = x_y_z_values[1]
        z_matrix = x_y_z_values[2]

        return build_lookup_matrix_spline_runtime_template(
            vf=self.vf,
            x_points=x_points,
            y_points=y_points,
            z_matrix=z_matrix,
            name=name,
        )


def build_lookup_matrix_spline_runtime_template(
    vf: VarFactory,
    x_points: Sequence[float],
    y_points: Sequence[float],
    z_matrix: Sequence[Sequence[float]],
    name: str | None = None,
) -> EmtModelTemplate:
    """
    Build one runtime two-dimensional spline lookup template from explicit axes and values.

    :param vf: Variable factory used to allocate symbolic objects.
    :param x_points: Strictly increasing x-axis values.
    :param y_points: Strictly increasing y-axis values.
    :param z_matrix: Matrix values indexed as `[y][x]`.
    :param name: Optional explicit runtime template name.
    :return: Materialized EMT template.
    """
    template_name: str
    x_count: int = len(x_points)
    y_count: int = len(y_points)
    x_index: int
    y_index: int
    x_input_var: Var
    y_input_var: Var
    output_var: Var
    x_axis_vars: list[Var] = list()
    y_axis_vars: list[Var] = list()
    z_value_vars: list[list[Expr]] = list()
    parameter_var: Var
    row_spline_exprs: list[Expr] = list()
    lookup_expr: Expr
    template: EmtModelTemplate = EmtModelTemplate()

    _validate_lookup_matrix(x_points=x_points, y_points=y_points, z_matrix=z_matrix)

    if name is None:
        template_name = f"lookup_matrix_spline_{x_count}x{y_count}"
    else:
        template_name = name

    template.tpe = DeviceType.NoDevice
    template.name = template_name

    x_input_var = vf.add_var("yi1_" + template_name)
    y_input_var = vf.add_var("yi2_" + template_name)
    output_var = vf.add_var("yo_" + template_name)

    for x_index in range(x_count):
        parameter_var = vf.add_var("arr_x" + str(x_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(x_points[x_index]), name="arr_x" + str(x_index + 1))
        x_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        parameter_var = vf.add_var("arr_y" + str(y_index + 1) + "_" + template_name)
        template.block.event_dict[parameter_var] = vf.add_const(float(y_points[y_index]), name="arr_y" + str(y_index + 1))
        y_axis_vars.append(parameter_var)

    for y_index in range(y_count):
        row_vars: list[Expr] = list()
        for x_index in range(x_count):
            parameter_var = vf.add_var("arr_z" + str(y_index + 1) + "_" + str(x_index + 1) + "_" + template_name)
            template.block.event_dict[parameter_var] = vf.add_const(
                float(z_matrix[y_index][x_index]),
                name="arr_z" + str(y_index + 1) + "_" + str(x_index + 1),
            )
            row_vars.append(parameter_var)
        z_value_vars.append(row_vars)

    for y_index in range(y_count):
        row_spline_exprs.append(
            _build_cubic_spline_piecewise_expression(
                coord_expr=x_input_var,
                axis_points=x_points,
                axis_vars=x_axis_vars,
                sample_values=z_value_vars[y_index],
            )
        )

    lookup_expr = _build_cubic_spline_piecewise_expression(
        coord_expr=y_input_var,
        axis_points=y_points,
        axis_vars=y_axis_vars,
        sample_values=row_spline_exprs,
    )

    template.block = Block(
        algebraic_vars=list([output_var]),
        algebraic_eqs=list([output_var - lookup_expr]),
        in_vars=list([x_input_var, y_input_var]),
        out_vars=list([output_var]),
        event_dict=template.block.event_dict,
        name=template_name,
    )
    return template
