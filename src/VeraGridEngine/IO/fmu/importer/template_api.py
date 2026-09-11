# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import re
from pathlib import Path

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import (
    DeviceType,
    FmiVersion,
    FmuTemplateDomain,
    FmuTemplateMode,
    FmuVariableType,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)
from VeraGridEngine.Utils.Symbolic.block import Block

from VeraGridEngine.IO.fmu.importer.bindings import (
    FmuBindingDirection,
    FmuFloat64ParameterValue,
    FmuImportConfig,
    FmuRefBinding,
    FmuVariableBinding,
    _validate_fmu_float64_parameter_values,
)
from VeraGridEngine.IO.fmu.importer.device_config import (
    build_me_record_from_device_arguments,
    build_record_from_device_arguments,
    dump_fmu_cs_device_config,
    dump_fmu_me_device_config,
)
from VeraGridEngine.IO.fmu.importer.co_simulation import (
    FmuCsDomain,
    build_emt_fmu_cs_injection_template,
    build_rms_fmu_cs_injection_template,
)
from VeraGridEngine.IO.fmu.importer.model_exchange import (
    FmuMeDomain,
    build_emt_fmu_me_injection_template,
    build_rms_fmu_me_injection_template,
)
from VeraGridEngine.IO.fmu.importer.model_description import (
    FmuInterfaceMode,
    FmuModelDescription,
    FmuVariableDescription,
    read_fmu_model_description,
)
from VeraGridEngine.IO.fmu.importer.runtime_worker_host import (
    FmiThreeWorkerHostLimits,
)


def _normalize_identifier(text: str) -> str:
    """
    Normalize one free-form FMU identifier for matching purposes.

    :param text: Original identifier.
    :return: Normalized identifier.
    """

    normalized_text: str = re.sub(r"[^A-Za-z0-9_]+", "_", str(text).strip())
    return normalized_text.strip("_").lower()


def _sanitize_symbol_name(text: str) -> str:
    """
    Convert one FMU variable name into a valid VeraGrid symbolic identifier.

    :param text: Original FMU variable name.
    :return: Valid symbolic identifier.
    """

    candidate: str = re.sub(r"[^A-Za-z0-9_]+", "_", str(text).strip())
    if len(candidate) == 0:
        candidate = "fmu_signal"
    else:
        pass

    if candidate[0].isdigit():
        return f"fmu_{candidate}"
    else:
        return candidate


def _build_var_reference_aliases() -> dict[str, VarPowerFlowReferenceType]:
    """
    Build the alias map used to auto-match FMU variable names to VeraGrid references.

    :return: Normalized alias map.
    """

    aliases: dict[str, VarPowerFlowReferenceType] = dict()
    reference: VarPowerFlowReferenceType
    for reference in VarPowerFlowReferenceType:
        if reference == VarPowerFlowReferenceType.NOTHING:
            pass
        else:
            aliases[_normalize_identifier(reference.name)] = reference
            aliases[_normalize_identifier(reference.value)] = reference
    return aliases


def _build_param_reference_aliases() -> dict[str, ParamPowerFlowReferenceType]:
    """
    Build the alias map used to auto-match FMU parameter names to VeraGrid parameter references.

    :return: Normalized alias map.
    """

    aliases: dict[str, ParamPowerFlowReferenceType] = dict()
    reference: ParamPowerFlowReferenceType
    for reference in ParamPowerFlowReferenceType:
        if reference == ParamPowerFlowReferenceType.NOTHING:
            pass
        else:
            aliases[_normalize_identifier(reference.name)] = reference
            aliases[_normalize_identifier(reference.value)] = reference
    return aliases


def _resolve_variable_reference(variable_name: str) -> VarPowerFlowReferenceType | None:
    """
    Resolve one FMU variable name into a VeraGrid runtime reference when possible.

    :param variable_name: FMU variable name.
    :return: Matching VeraGrid reference when available.
    """

    aliases = _build_var_reference_aliases()
    return aliases.get(_normalize_identifier(variable_name), None)


def _resolve_parameter_reference(variable_name: str) -> ParamPowerFlowReferenceType | None:
    """
    Resolve one FMU parameter name into a VeraGrid device-parameter reference when possible.

    :param variable_name: FMU variable name.
    :return: Matching VeraGrid parameter reference when available.
    """

    aliases = _build_param_reference_aliases()
    return aliases.get(_normalize_identifier(variable_name), None)


def _list_input_variables(metadata: FmuModelDescription) -> tuple[FmuVariableDescription, ...]:
    """
    Return the declared FMU input variables.

    :param metadata: Parsed FMU metadata.
    :return: Ordered input variables.
    """

    variables: list[FmuVariableDescription] = list()
    variable: FmuVariableDescription
    for variable in metadata.variables:
        if variable.causality == "input":
            variables.append(variable)
        else:
            pass
    return tuple(variables)


def _list_output_variables(metadata: FmuModelDescription) -> tuple[FmuVariableDescription, ...]:
    """
    Return the declared FMU output variables.

    :param metadata: Parsed FMU metadata.
    :return: Ordered output variables.
    """

    variables: list[FmuVariableDescription] = list()
    variable: FmuVariableDescription
    for variable in metadata.variables:
        if variable.causality == "output":
            variables.append(variable)
        else:
            pass
    return tuple(variables)


def _list_parameter_variables(metadata: FmuModelDescription) -> tuple[FmuVariableDescription, ...]:
    """
    Return the declared FMU parameter variables.

    :param metadata: Parsed FMU metadata.
    :return: Ordered parameter variables.
    """

    variables: list[FmuVariableDescription] = list()
    variable: FmuVariableDescription
    for variable in metadata.variables:
        if variable.causality == "parameter":
            variables.append(variable)
        else:
            pass
    return tuple(variables)


def _build_auto_input_bindings(metadata: FmuModelDescription) -> tuple[FmuRefBinding, ...]:
    """
    Auto-discover FMU input bindings by matching FMU variable names to VeraGrid references.

    :param metadata: Parsed FMU metadata.
    :return: Auto-discovered input bindings.
    """

    bindings: list[FmuRefBinding] = list()
    seen_references: set[VarPowerFlowReferenceType] = set()
    variable: FmuVariableDescription
    for variable in _list_input_variables(metadata):
        reference = _resolve_variable_reference(variable.name)
        if reference is None:
            pass
        else:
            if reference in seen_references:
                pass
            else:
                bindings.append(FmuRefBinding(reference=reference, fmu_variable_name=variable.name))
                seen_references.add(reference)
    return tuple(bindings)


def _build_auto_output_bindings(metadata: FmuModelDescription) -> tuple[FmuRefBinding, ...]:
    """
    Auto-discover FMU output bindings by matching FMU variable names to VeraGrid references.

    :param metadata: Parsed FMU metadata.
    :return: Auto-discovered output bindings.
    """

    bindings: list[FmuRefBinding] = list()
    seen_references: set[VarPowerFlowReferenceType] = set()
    variable: FmuVariableDescription
    for variable in _list_output_variables(metadata):
        reference = _resolve_variable_reference(variable.name)
        if reference is None:
            pass
        else:
            if reference in seen_references:
                pass
            else:
                bindings.append(FmuRefBinding(reference=reference, fmu_variable_name=variable.name))
                seen_references.add(reference)
    return tuple(bindings)


def _parse_numeric_start_value(variable: FmuVariableDescription) -> float:
    """
    Parse one FMU scalar start value into a numeric placeholder.

    :param variable: FMU variable metadata.
    :return: Numeric start value.
    """

    if variable.start is None:
        return 0.0
    else:
        text = str(variable.start).strip()
        if len(text) == 0:
            return 0.0
        else:
            lowered_text = text.lower()
            if lowered_text == "true":
                return 1.0
            else:
                if lowered_text == "false":
                    return 0.0
                else:
                    try:
                        return float(text)
                    except ValueError:
                        return 0.0


def _build_output_defaults(metadata: FmuModelDescription,
                           output_bindings: tuple[FmuRefBinding, ...]) -> dict[VarPowerFlowReferenceType, float]:
    """
    Build default output values for the bound FMU output references.

    :param metadata: Parsed FMU metadata.
    :param output_bindings: Bound FMU output bindings.
    :return: Default values indexed by VeraGrid reference.
    """

    defaults: dict[VarPowerFlowReferenceType, float] = dict()
    binding: FmuRefBinding
    for binding in output_bindings:
        defaults[binding.reference] = _parse_numeric_start_value(metadata.get_variable(binding.fmu_variable_name))
    return defaults


def _iter_block_symbol_names(block: Block) -> set[str]:
    """
    Collect the symbolic names already used by one block.

    :param block: Block to inspect.
    :return: Used symbolic names.
    """

    names: set[str] = set()
    block_item: Block
    for block_item in block.get_all_blocks():
        variable_groups = [
            block_item.algebraic_vars,
            block_item.state_vars,
            block_item.diff_vars,
            block_item.in_vars,
            block_item.out_vars,
        ]
        variables_list: list
        for variables_list in variable_groups:
            variable = None
            for variable in variables_list:
                names.add(variable.name)

        parameter_var = None
        for parameter_var in block_item.parameters.keys():
            names.add(parameter_var.name)

        event_var = None
        for event_var in block_item.event_dict.keys():
            names.add(event_var.name)
    return names


def _build_unique_symbol_name(base_name: str, used_names: set[str]) -> str:
    """
    Build one unique symbolic identifier for a new FMU port or parameter.

    :param base_name: Requested base name.
    :param used_names: Names already used by the block.
    :return: Unique symbolic name.
    """

    sanitized_name: str = _sanitize_symbol_name(base_name)
    candidate_name: str = sanitized_name
    suffix: int = 2
    while candidate_name in used_names:
        candidate_name = f"{sanitized_name}_{suffix}"
        suffix += 1
    used_names.add(candidate_name)
    return candidate_name


def _build_output_parameter_name(output_name: str) -> str:
    """
    Build the event-parameter symbol name that backs one FMU output port.

    :param output_name: Symbolic FMU output name.
    :return: Event-parameter symbolic name.
    """

    if output_name.startswith("fmu_"):
        return output_name.replace("fmu_", "fmu_param_", 1)
    else:
        return f"fmu_param_{output_name}"


def _rename_bound_output_ports(block: Block,
                               output_bindings: tuple[FmuRefBinding, ...],
                               used_names: set[str]) -> None:
    """
    Rename bound FMU output ports from internal names to their FMU variable names.

    :param block: Symbolic FMU shell block.
    :param output_bindings: Bound FMU output bindings.
    :param used_names: Names already reserved by the block.
    :return: None.
    """

    binding: FmuRefBinding
    for index, binding in enumerate(output_bindings):
        if index < len(block.out_vars):
            output_var = block.out_vars[index]
            old_output_name: str = output_var.name
            old_parameter_name: str = _build_output_parameter_name(old_output_name)
            output_var.name = _build_unique_symbol_name(binding.fmu_variable_name, used_names)

            event_parameter = None
            for event_parameter in block.event_dict.keys():
                if event_parameter.name == old_parameter_name:
                    event_parameter.name = _build_output_parameter_name(output_var.name)
                else:
                    pass

            block.external_mapping[binding.reference] = output_var
        else:
            pass


def _append_visual_input_ports(block: Block,
                               vfactory: VarFactory,
                               metadata: FmuModelDescription,
                               input_bindings: tuple[FmuRefBinding, ...],
                               used_names: set[str]) -> None:
    """
    Add visual input ports for the declared FMU inputs.

    :param block: Symbolic FMU shell block.
    :param vfactory: Variable factory used by the owning grid.
    :param metadata: Parsed FMU metadata.
    :param input_bindings: Auto-discovered runtime input bindings.
    :param used_names: Names already reserved by the block.
    :return: None.
    """

    bound_references: dict[str, VarPowerFlowReferenceType] = dict()
    binding: FmuRefBinding
    for binding in input_bindings:
        bound_references[binding.fmu_variable_name] = binding.reference

    variable: FmuVariableDescription
    for variable in _list_input_variables(metadata):
        reference = bound_references.get(variable.name, None)
        input_var = vfactory.add_var(
            name=_build_unique_symbol_name(variable.name, used_names),
            reference=reference,
        )
        block.in_vars.append(input_var)
        if reference is None:
            pass
        else:
            if reference not in block.external_mapping or block.external_mapping[reference] is None:
                block.external_mapping[reference] = input_var
            else:
                pass


def append_fmu_parameter_entries(
    block: Block,
    vfactory: VarFactory,
    metadata: FmuModelDescription,
    used_names: set[str] | None = None,
    parameter_values: tuple[FmuFloat64ParameterValue, ...] = tuple(),
) -> tuple[FmuVariableBinding, ...]:
    """
    Add executable scalar parameter entries and return their identity mappings.

    :param block: Symbolic FMU shell block.
    :param vfactory: Variable factory used by the owning grid.
    :param metadata: Parsed FMU metadata.
    :param used_names: Optional names already reserved by the block.
    :param parameter_values: Optional values overriding metadata starts.
    :return: Ordered Block-symbol to FMU-parameter identity mappings.
    """

    # Validate the whole override request against authoritative metadata before
    # adding variables to the block or allocating symbols in the factory.
    reserved_names: list[str] = [""] * len(metadata.variables)
    reserved_name_count: int = 0
    variable: FmuVariableDescription
    for variable in metadata.variables:
        if variable.causality in ("input", "structuralParameter"):
            reserved_names[reserved_name_count] = variable.name
            reserved_name_count += 1
        else:
            pass
    _validate_fmu_float64_parameter_values(
        parameter_values=parameter_values,
        metadata=metadata,
        reserved_variable_names=tuple(reserved_names[:reserved_name_count]),
    )

    override_values: dict[str, float] = dict()
    parameter_value: FmuFloat64ParameterValue
    for parameter_value in parameter_values:
        override_values[parameter_value.variable_name] = parameter_value.value

    eligible_variables: list[FmuVariableDescription | None] = [None] * len(
        metadata.variables
    )
    eligible_count: int = 0
    for variable in metadata.variables:
        if metadata.fmi_version_family == FmiVersion.FMI_2_0:
            variable_is_eligible: bool = (
                variable.causality == "parameter"
                and variable.variable_type == FmuVariableType.REAL
                and variable.variability in (None, "fixed", "tunable")
                and variable.initial in (None, "exact")
            )
        else:
            if metadata.fmi_version_family == FmiVersion.FMI_3_0:
                variable_is_eligible = (
                    variable.causality == "parameter"
                    and variable.variable_type == FmuVariableType.FLOAT64
                    and variable.variability in ("fixed", "tunable")
                    and variable.initial == "exact"
                    and len(variable.dimensions) == 0
                )
            else:
                variable_is_eligible = False
        if variable_is_eligible:
            eligible_variables[eligible_count] = variable
            eligible_count += 1
        else:
            pass

    # Resolve and validate every numeric source before the factory or Block is
    # changed, so a later malformed metadata start cannot leave partial state.
    resolved_parameter_values: list[FmuFloat64ParameterValue | None] = [
        None
    ] * eligible_count
    parameter_index: int
    for parameter_index in range(eligible_count):
        eligible_variable: FmuVariableDescription | None = eligible_variables[
            parameter_index
        ]
        if eligible_variable is None:
            raise RuntimeError("FMU parameter eligibility plan is incomplete")
        else:
            pass
        parameter_start: float | None = override_values.get(
            eligible_variable.name,
            None,
        )
        if parameter_start is None:
            parameter_start = _parse_numeric_start_value(eligible_variable)
        else:
            pass
        resolved_parameter_values[parameter_index] = FmuFloat64ParameterValue(
            variable_name=eligible_variable.name,
            value=parameter_start,
        )

    if used_names is None:
        active_used_names: set[str] = _iter_block_symbol_names(block)
    else:
        active_used_names = used_names
    parameter_bindings: list[FmuVariableBinding | None] = [None] * eligible_count
    for parameter_index in range(eligible_count):
        eligible_variable: FmuVariableDescription | None = eligible_variables[
            parameter_index
        ]
        if eligible_variable is None:
            raise RuntimeError("FMU parameter eligibility plan is incomplete")
        else:
            pass
        block_parameter_name: str = _build_unique_symbol_name(
            eligible_variable.name,
            active_used_names,
        )
        parameter_var: Var = vfactory.add_var(name=block_parameter_name)
        validated_parameter_value: FmuFloat64ParameterValue | None = (
            resolved_parameter_values[parameter_index]
        )
        if validated_parameter_value is not None:
            pass
        else:
            raise RuntimeError("FMU parameter value plan is incomplete")
        block.parameters[parameter_var] = vfactory.add_const(
            validated_parameter_value.value
        )
        parameter_bindings[parameter_index] = FmuVariableBinding(
            signal_name=parameter_var.name,
            variable_name=eligible_variable.name,
            direction=FmuBindingDirection.PARAMETER,
        )

        parameter_reference = _resolve_parameter_reference(eligible_variable.name)
        if parameter_reference is None:
            pass
        else:
            block.api_obj_mapping[parameter_reference] = parameter_var
    resolved_bindings: list[FmuVariableBinding] = list()
    parameter_binding: FmuVariableBinding | None
    for parameter_binding in parameter_bindings:
        if parameter_binding is not None:
            resolved_bindings.append(parameter_binding)
        else:
            raise RuntimeError("FMU parameter binding plan is incomplete")
    return tuple(resolved_bindings)


def _append_unbound_output_ports(block: Block,
                                 vfactory: VarFactory,
                                 metadata: FmuModelDescription,
                                 output_bindings: tuple[FmuRefBinding, ...],
                                 used_names: set[str]) -> None:
    """
    Add visual output ports for FMU outputs that are not auto-bound to VeraGrid references.

    :param block: Symbolic FMU shell block.
    :param vfactory: Variable factory used by the owning grid.
    :param metadata: Parsed FMU metadata.
    :param output_bindings: Auto-discovered runtime output bindings.
    :param used_names: Names already reserved by the block.
    :return: None.
    """

    bound_output_names: set[str] = set()
    binding: FmuRefBinding
    for binding in output_bindings:
        bound_output_names.add(binding.fmu_variable_name)

    variable: FmuVariableDescription
    for variable in _list_output_variables(metadata):
        if variable.name in bound_output_names:
            pass
        else:
            output_name = _build_unique_symbol_name(variable.name, used_names)
            output_var = vfactory.add_var(name=output_name)
            parameter_var = vfactory.add_var(name=_build_output_parameter_name(output_name))
            block.algebraic_vars.append(output_var)
            block.algebraic_eqs.append(output_var - parameter_var)
            block.out_vars.append(output_var)
            block.event_dict[parameter_var] = vfactory.add_const(_parse_numeric_start_value(variable))


def _refresh_block_var_mapping(block: Block) -> None:
    """
    Refresh the block variable-name mapping after post-processing the FMU shell.

    :param block: Symbolic FMU shell block.
    :return: None.
    """

    block.var_mapping = {var.name: var for var in block.algebraic_vars + block.state_vars + block.diff_vars}


def _decorate_template_block(block: Block,
                             vfactory: VarFactory,
                             metadata: FmuModelDescription,
                             input_bindings: tuple[FmuRefBinding, ...],
                             output_bindings: tuple[FmuRefBinding, ...]) -> tuple[FmuVariableBinding, ...]:
    """
    Enrich the generated FMU shell block with visual ports and editable parameters.

    :param block: Symbolic FMU shell block.
    :param vfactory: Variable factory used by the owning grid.
    :param metadata: Parsed FMU metadata.
    :param input_bindings: Auto-discovered runtime input bindings.
    :param output_bindings: Auto-discovered runtime output bindings.
    :return: Ordered executable parameter identity mappings.
    """

    used_names = _iter_block_symbol_names(block)
    _rename_bound_output_ports(block, output_bindings, used_names)
    _append_visual_input_ports(block, vfactory, metadata, input_bindings, used_names)
    parameter_bindings: tuple[FmuVariableBinding, ...] = (
        append_fmu_parameter_entries(
            block=block,
            vfactory=vfactory,
            metadata=metadata,
            used_names=used_names,
        )
    )
    _append_unbound_output_ports(block, vfactory, metadata, output_bindings, used_names)
    _refresh_block_var_mapping(block)
    return parameter_bindings


def _build_mode_summary_line(metadata: FmuModelDescription) -> str:
    """
    Build one human-readable line describing the supported FMI modes.

    :param metadata: Parsed FMU metadata.
    :return: Supported modes summary.
    """

    supported_modes: list[str] = list()
    if metadata.get_supports_co_simulation():
        supported_modes.append(FmuTemplateMode.CO_SIMULATION.value)
    else:
        pass
    if metadata.get_supports_model_exchange():
        supported_modes.append(FmuTemplateMode.MODEL_EXCHANGE.value)
    else:
        pass

    if len(supported_modes) > 0:
        return ", ".join(supported_modes)
    else:
        return "none"


def _build_variable_list_text(variables: tuple[FmuVariableDescription, ...]) -> str:
    """
    Build one compact text line from a list of FMU variable descriptors.

    :param variables: Variable descriptors.
    :return: Joined variable names.
    """

    names: list[str] = list()
    variable: FmuVariableDescription
    for variable in variables:
        names.append(variable.name)
    if len(names) > 0:
        return ", ".join(names)
    else:
        return "none"


def summarize_fmu_template_metadata(metadata: FmuModelDescription) -> str:
    """
    Build the metadata text shown by the FMU template editor.

    :param metadata: Parsed FMU metadata.
    :return: Human-readable metadata summary.
    """

    input_bindings = _build_auto_input_bindings(metadata)
    output_bindings = _build_auto_output_bindings(metadata)

    auto_input_names: list[str] = list()
    binding: FmuRefBinding
    for binding in input_bindings:
        auto_input_names.append(f"{binding.fmu_variable_name}->{binding.reference.value}")

    auto_output_names: list[str] = list()
    for binding in output_bindings:
        auto_output_names.append(f"{binding.fmu_variable_name}->{binding.reference.value}")

    platforms_text = ", ".join(metadata.platforms) if len(metadata.platforms) > 0 else "none"
    auto_inputs_text = ", ".join(auto_input_names) if len(auto_input_names) > 0 else "none"
    auto_outputs_text = ", ".join(auto_output_names) if len(auto_output_names) > 0 else "none"

    return (
        f"Model: {metadata.model_name}\n"
        f"FMI version: {metadata.fmi_version}\n"
        f"Supported modes: {_build_mode_summary_line(metadata)}\n"
        f"Platforms: {platforms_text}\n"
        f"Inputs: {_build_variable_list_text(_list_input_variables(metadata))}\n"
        f"Outputs: {_build_variable_list_text(_list_output_variables(metadata))}\n"
        f"Parameters: {_build_variable_list_text(_list_parameter_variables(metadata))}\n"
        f"Auto input bindings: {auto_inputs_text}\n"
        f"Auto output bindings: {auto_outputs_text}"
    )


def _to_interface_mode(mode: FmuTemplateMode) -> FmuInterfaceMode:
    """
    Convert one template mode into the importer runtime enum.

    :param mode: Template mode.
    :return: Importer interface mode.
    """

    if mode == FmuTemplateMode.CO_SIMULATION:
        return FmuInterfaceMode.CO_SIMULATION
    else:
        if mode == FmuTemplateMode.MODEL_EXCHANGE:
            return FmuInterfaceMode.MODEL_EXCHANGE
        else:
            raise ValueError(f"Unsupported FMU template mode {mode}")


def configure_fmu_template(
    template: FmuTemplate,
    var_factory: VarFactory,
    fmu_path: str | Path,
    device_tpe: DeviceType,
    domain: FmuTemplateDomain,
    mode: FmuTemplateMode,
    template_name: str | None = None,
    worker_limits: FmiThreeWorkerHostLimits | None = None,
) -> FmuTemplate:
    """
    Populate one reusable ``FmuTemplate`` from an FMU archive.

    The function builds the symbolic shell block, exposes the FMU interface as visual
    ports and parameters, and stores the serialized runtime configuration required by
    the RMS or EMT import adapters.

    :param template: Template instance to mutate.
    :param var_factory: RMS variable factory owned by the current grid.
    :param fmu_path: FMU archive selected by the user.
    :param device_tpe: Target VeraGrid device type.
    :param domain: Simulation domain where the template will be used.
    :param mode: FMI interface mode required by the template.
    :param template_name: Optional explicit template name.
    :param worker_limits: Explicit FMI 3 worker supervision policy. FMI 2
        callers may leave it unset.
    :return: Configured template instance.
    """

    normalized_path: Path = Path(fmu_path).expanduser().resolve()
    metadata: FmuModelDescription = read_fmu_model_description(normalized_path)
    template_config: FmuImportConfig = FmuImportConfig(
        fmu_path=normalized_path,
        preferred_mode=_to_interface_mode(mode),
    )
    # Reject unsupported FMI versions before creating or storing a template.
    template_config.resolve_execution_mode(metadata)
    input_bindings: tuple[FmuRefBinding, ...] = _build_auto_input_bindings(
        metadata
    )
    output_bindings: tuple[FmuRefBinding, ...] = _build_auto_output_bindings(
        metadata
    )
    output_defaults: dict[VarPowerFlowReferenceType, float] = (
        _build_output_defaults(metadata, output_bindings)
    )

    resolved_name: str
    if template_name is None:
        resolved_name = metadata.model_name
    else:
        resolved_name = str(template_name).strip()
        if len(resolved_name) == 0:
            resolved_name = metadata.model_name
        else:
            pass

    shell_template: RmsModelTemplate | EmtModelTemplate
    serialized_config: str
    parameter_bindings: tuple[FmuVariableBinding, ...]
    if domain == FmuTemplateDomain.RMS:
        if mode == FmuTemplateMode.CO_SIMULATION:
            shell_template = build_rms_fmu_cs_injection_template(
                vfactory=var_factory,
                config=template_config,
                input_bindings=input_bindings,
                output_bindings=output_bindings,
                name=resolved_name,
                device_tpe=device_tpe,
                output_defaults=output_defaults,
                worker_limits=worker_limits,
            )
            parameter_bindings = _decorate_template_block(shell_template.block, var_factory, metadata, input_bindings, output_bindings)
            serialized_config = dump_fmu_cs_device_config(
                build_record_from_device_arguments(
                    domain=FmuCsDomain.RMS,
                    config=template_config,
                    input_bindings=input_bindings,
                    output_bindings=output_bindings,
                    output_defaults=output_defaults,
                    block=shell_template.block,
                    worker_limits=worker_limits,
                    parameter_bindings=parameter_bindings,
                )
            )
        else:
            if mode == FmuTemplateMode.MODEL_EXCHANGE:
                shell_template = build_rms_fmu_me_injection_template(
                    vfactory=var_factory,
                    config=template_config,
                    input_bindings=input_bindings,
                    output_bindings=output_bindings,
                    name=resolved_name,
                    device_tpe=device_tpe,
                    output_defaults=output_defaults,
                    worker_limits=worker_limits,
                )
                parameter_bindings = _decorate_template_block(shell_template.block, var_factory, metadata, input_bindings, output_bindings)
                serialized_config = dump_fmu_me_device_config(
                    build_me_record_from_device_arguments(
                        domain=FmuMeDomain.RMS,
                        config=template_config,
                        input_bindings=input_bindings,
                        output_bindings=output_bindings,
                        output_defaults=output_defaults,
                        block=shell_template.block,
                        worker_limits=worker_limits,
                        parameter_bindings=parameter_bindings,
                    )
                )
            else:
                raise ValueError(f"Unsupported FMU template mode {mode}")
    else:
        if domain == FmuTemplateDomain.EMT:
            if mode == FmuTemplateMode.CO_SIMULATION:
                shell_template = build_emt_fmu_cs_injection_template(
                    vfactory=var_factory,
                    config=template_config,
                    input_bindings=input_bindings,
                    output_bindings=output_bindings,
                    name=resolved_name,
                    device_tpe=device_tpe,
                    output_defaults=output_defaults,
                    worker_limits=worker_limits,
                )
                parameter_bindings = _decorate_template_block(shell_template.block, var_factory, metadata, input_bindings, output_bindings)
                serialized_config = dump_fmu_cs_device_config(
                    build_record_from_device_arguments(
                        domain=FmuCsDomain.EMT,
                        config=template_config,
                        input_bindings=input_bindings,
                        output_bindings=output_bindings,
                        output_defaults=output_defaults,
                        block=shell_template.block,
                        worker_limits=worker_limits,
                        parameter_bindings=parameter_bindings,
                    )
                )
            else:
                if mode == FmuTemplateMode.MODEL_EXCHANGE:
                    shell_template = build_emt_fmu_me_injection_template(
                        vfactory=var_factory,
                        config=template_config,
                        input_bindings=input_bindings,
                        output_bindings=output_bindings,
                        name=resolved_name,
                        device_tpe=device_tpe,
                        output_defaults=output_defaults,
                        worker_limits=worker_limits,
                    )
                    parameter_bindings = _decorate_template_block(shell_template.block, var_factory, metadata, input_bindings, output_bindings)
                    serialized_config = dump_fmu_me_device_config(
                        build_me_record_from_device_arguments(
                            domain=FmuMeDomain.EMT,
                            config=template_config,
                            input_bindings=input_bindings,
                            output_bindings=output_bindings,
                            output_defaults=output_defaults,
                            block=shell_template.block,
                            worker_limits=worker_limits,
                            parameter_bindings=parameter_bindings,
                        )
                    )
                else:
                    raise ValueError(f"Unsupported FMU template mode {mode}")
        else:
            raise ValueError(f"Unsupported FMU template domain {domain}")

    template.name = resolved_name
    template.tpe = device_tpe
    template.domain = domain
    template.mode = mode
    template.fmu_relative_path = str(normalized_path)
    template.serialized_config = serialized_config
    template.block = shell_template.block
    return template
