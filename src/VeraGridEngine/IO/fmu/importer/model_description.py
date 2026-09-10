# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path
from typing import Optional
import warnings
import xml.etree.ElementTree as ET

from VeraGridEngine.IO.fmu.importer.errors import FmuArchiveError, FmuModeError
from VeraGridEngine.IO.fmu.importer.inspection import (
    FmuArchiveInspectionPolicy,
    FmuInspectionResult,
    inspect_fmu,
)
from VeraGridEngine.IO.fmu.importer.fmi3_model_description import (
    parse_fmi3_model_description,
)
from VeraGridEngine.IO.fmu.versions import parse_declared_fmi_version
from VeraGridEngine.enumerations import FmiVersion, FmuInterfaceMode, FmuVariableType
from VeraGridEngine.IO.fmu.importer.model_description_metadata import (
    FmuModelDescription,
    FmuVariableDescription,
)
from VeraGridEngine.IO.fmu.importer.model_description_xml import (
    parse_fmi_boolean as _parse_fmi_boolean,
    parse_fmi_uint32 as _parse_fmi_uint32,
    read_required_attribute as _read_required_attribute,
)


def _validate_fmi_one_co_simulation_interface(
    interface_node: ET.Element,
    path: Path,
) -> None:
    """Validate the required structure of one FMI 1 Co-Simulation interface.

    Capability values remain metadata-only and are deliberately not stored.

    :param interface_node: Stand-alone or tool interface element.
    :param path: FMU source path used in diagnostics.
    :return: None.
    :raises FmuArchiveError: If required interface children are missing.
    """

    interface_children: list[ET.Element] = list(interface_node)
    if interface_node.tag == "CoSimulation_StandAlone":
        if len(interface_children) == 1 and interface_children[0].tag == "Capabilities":
            pass
        else:
            raise FmuArchiveError(
                f"FMI 1 CoSimulation_StandAlone in {path} requires one Capabilities element"
            )
    else:
        if interface_node.tag == "CoSimulation_Tool":
            if (
                len(interface_children) == 2
                and interface_children[0].tag == "Capabilities"
                and interface_children[1].tag == "Model"
            ):
                _read_required_attribute(
                    interface_children[1],
                    "entryPoint",
                    "FMI 1 CoSimulation_Tool Model",
                    path,
                )
                _read_required_attribute(
                    interface_children[1],
                    "type",
                    "FMI 1 CoSimulation_Tool Model",
                    path,
                )
            else:
                raise FmuArchiveError(
                    f"FMI 1 CoSimulation_Tool in {path} requires Capabilities and Model elements"
                )
        else:
            raise FmuArchiveError(
                f"Unknown FMI 1 Co-Simulation interface {interface_node.tag!r} in {path}"
            )


def _parse_fmi_one_interface_modes(
    root: ET.Element,
    model_identifier: str,
    path: Path,
) -> tuple[tuple[FmuInterfaceMode, ...], dict[FmuInterfaceMode, str]]:
    """Infer the FMI 1 interface from its optional Implementation element.

    :param root: FMI 1 model-description root.
    :param model_identifier: Required root model identifier.
    :param path: FMU source path used in diagnostics.
    :return: Declared interface and its model identifier.
    :raises FmuArchiveError: If the interface declaration is ambiguous.
    """

    implementation_nodes: list[ET.Element] = root.findall("Implementation")
    if len(implementation_nodes) > 1:
        raise FmuArchiveError(f"FMI 1 Implementation element is duplicated in {path}")
    else:
        identifiers: dict[FmuInterfaceMode, str] = dict()
        if len(implementation_nodes) == 0:
            interface_mode: FmuInterfaceMode = FmuInterfaceMode.MODEL_EXCHANGE
        else:
            implementation_children: list[ET.Element] = list(implementation_nodes[0])
            if len(implementation_children) == 1:
                implementation_kind: str = implementation_children[0].tag
                if implementation_kind == "CoSimulation_StandAlone":
                    _validate_fmi_one_co_simulation_interface(
                        implementation_children[0],
                        path,
                    )
                    interface_mode = FmuInterfaceMode.CO_SIMULATION
                else:
                    if implementation_kind == "CoSimulation_Tool":
                        _validate_fmi_one_co_simulation_interface(
                            implementation_children[0],
                            path,
                        )
                        interface_mode = FmuInterfaceMode.CO_SIMULATION
                    else:
                        raise FmuArchiveError(
                            f"Unknown FMI 1 Implementation interface {implementation_kind!r} in {path}"
                        )
            else:
                raise FmuArchiveError(
                    f"FMI 1 Implementation in {path} must declare exactly one interface"
                )
        identifiers[interface_mode] = model_identifier
        return (interface_mode,), identifiers


def _parse_fmi_two_interface_modes(
    root: ET.Element,
    path: Path,
) -> tuple[tuple[FmuInterfaceMode, ...], dict[FmuInterfaceMode, str]]:
    """Parse the supported FMI 2 interface modes from the XML root.

    :param root: XML root element.
    :param path: FMU source path used to identify validation failures.
    :return: Supported modes and their model identifiers.
    :raises FmuArchiveError: If an interface declaration is duplicated or incomplete.
    :raises FmuModeError: If Co-Simulation requires an external execution tool.
    """

    modes: list[FmuInterfaceMode] = list()
    identifiers: dict[FmuInterfaceMode, str] = dict()

    co_simulation_nodes: list[ET.Element] = root.findall("CoSimulation")
    if len(co_simulation_nodes) > 1:
        raise FmuArchiveError(f"FMI 2 CoSimulation interface is duplicated in {path}")
    else:
        if len(co_simulation_nodes) == 1:
            co_simulation_node: ET.Element = co_simulation_nodes[0]
            co_simulation_identifier: str = _read_required_attribute(
                co_simulation_node,
                "modelIdentifier",
                "CoSimulation",
                path,
            )
            needs_execution_tool_raw: str | None = co_simulation_node.attrib.get(
                "needsExecutionTool",
                None,
            )
            if needs_execution_tool_raw is None:
                needs_execution_tool: bool = False
            else:
                needs_execution_tool = _parse_fmi_boolean(
                    needs_execution_tool_raw,
                    "needsExecutionTool",
                    "CoSimulation",
                    path,
                )
            if needs_execution_tool:
                raise FmuModeError(
                    "FMI 2 Co-Simulation models that require an external execution tool are not supported"
                )
            else:
                modes.append(FmuInterfaceMode.CO_SIMULATION)
                identifiers[FmuInterfaceMode.CO_SIMULATION] = co_simulation_identifier
        else:
            pass

    model_exchange_nodes: list[ET.Element] = root.findall("ModelExchange")
    if len(model_exchange_nodes) > 1:
        raise FmuArchiveError(f"FMI 2 ModelExchange interface is duplicated in {path}")
    else:
        if len(model_exchange_nodes) == 1:
            model_exchange_node: ET.Element = model_exchange_nodes[0]
            model_exchange_identifier: str = _read_required_attribute(
                model_exchange_node,
                "modelIdentifier",
                "ModelExchange",
                path,
            )
            needs_execution_tool_raw = model_exchange_node.attrib.get(
                "needsExecutionTool",
                None,
            )
            if needs_execution_tool_raw is None:
                pass
            else:
                _parse_fmi_boolean(
                    needs_execution_tool_raw,
                    "needsExecutionTool",
                    "ModelExchange",
                    path,
                )
            modes.append(FmuInterfaceMode.MODEL_EXCHANGE)
            identifiers[FmuInterfaceMode.MODEL_EXCHANGE] = model_exchange_identifier
        else:
            pass

    if len(modes) > 0:
        return tuple(modes), identifiers
    else:
        raise FmuArchiveError(
            f"FMI 2 model description in {path} declares no supported interface"
        )


def _parse_variable_type(
    variable_node: ET.Element,
    variable_name: str,
    fmi_version_family: FmiVersion,
    path: Path,
) -> tuple[FmuVariableType, ET.Element]:
    """Parse the primitive FMI type for one scalar variable.

    :param variable_node: ScalarVariable XML node.
    :param variable_name: Required variable name used in diagnostics.
    :param fmi_version_family: FMI family that defines trailing child elements.
    :param path: FMU source path used to identify validation failures.
    :return: Primitive FMI type and matching child node.
    :raises FmuArchiveError: If the variable has no unique known primitive type.
    """

    variable_type: FmuVariableType = FmuVariableType.UNKNOWN
    type_node: ET.Element | None = None
    trailing_element_seen: bool = False
    if fmi_version_family == FmiVersion.FMI_1_0:
        trailing_element_name: str = "DirectDependency"
    else:
        if fmi_version_family == FmiVersion.FMI_2_0:
            trailing_element_name = "Annotations"
        else:
            raise FmuArchiveError(
                f"FMI {fmi_version_family.value} scalar-variable parsing is not supported"
            )

    child_node: ET.Element
    for child_node in variable_node:
        if child_node.tag == trailing_element_name:
            if type_node is None:
                raise FmuArchiveError(
                    f"ScalarVariable {variable_name!r} in {path} declares "
                    f"{trailing_element_name} before its primitive type"
                )
            else:
                if trailing_element_seen:
                    raise FmuArchiveError(
                        f"ScalarVariable {variable_name!r} in {path} duplicates "
                        f"{trailing_element_name}"
                    )
                else:
                    trailing_element_seen = True
        else:
            if trailing_element_seen:
                raise FmuArchiveError(
                    f"ScalarVariable {variable_name!r} in {path} declares a child "
                    f"after {trailing_element_name}"
                )
            else:
                pass
            try:
                candidate_type: FmuVariableType = FmuVariableType(child_node.tag)
            except ValueError as exc:
                raise FmuArchiveError(
                    f"ScalarVariable {variable_name!r} in {path} has unknown type {child_node.tag!r}"
                ) from exc
            if candidate_type == FmuVariableType.UNKNOWN:
                raise FmuArchiveError(
                    f"ScalarVariable {variable_name!r} in {path} has unknown type {child_node.tag!r}"
                )
            else:
                if type_node is None:
                    variable_type = candidate_type
                    type_node = child_node
                else:
                    raise FmuArchiveError(
                        f"ScalarVariable {variable_name!r} in {path} declares multiple primitive types"
                    )

    if type_node is None:
        raise FmuArchiveError(
            f"ScalarVariable {variable_name!r} in {path} does not declare a primitive type"
        )
    else:
        return variable_type, type_node


def _parse_variables(
    model_variables_node: ET.Element | None,
    fmi_version_family: FmiVersion,
    path: Path,
) -> tuple[FmuVariableDescription, ...]:
    """Parse the ordered scalar variables declared in the FMU.

    :param model_variables_node: XML `<ModelVariables>` node.
    :param fmi_version_family: FMI family that defines variable semantics.
    :param path: FMU source path used to identify validation failures.
    :return: Ordered scalar-variable descriptions.
    :raises FmuArchiveError: If variable identity, type or derivative metadata is invalid.
    """

    variables: list[FmuVariableDescription] = list()
    variable_names: set[str] = set()
    if model_variables_node is None:
        return tuple()
    else:
        # ModelVariables may contain only unqualified FMI ScalarVariable
        # elements. Checking every child prevents namespace-qualified entries
        # from disappearing through the exact-name lookup below.
        model_variable_child: ET.Element
        for model_variable_child in model_variables_node:
            if model_variable_child.tag == "ScalarVariable":
                pass
            else:
                if model_variable_child.tag.startswith("{"):
                    raise FmuArchiveError(
                        f"XML namespaces are not accepted for FMI "
                        f"{fmi_version_family.value} variables in {path}"
                    )
                else:
                    raise FmuArchiveError(
                        f"Unexpected ModelVariables element {model_variable_child.tag!r} in {path}"
                    )

        scalar_variable_node: ET.Element
        for scalar_variable_node in model_variables_node.findall("ScalarVariable"):
            variable_name: str = _read_required_attribute(
                scalar_variable_node,
                "name",
                "ScalarVariable",
                path,
            )
            if variable_name in variable_names:
                raise FmuArchiveError(
                    f"ScalarVariable name {variable_name!r} is duplicated in {path}"
                )
            else:
                variable_names.add(variable_name)

            value_reference_raw: str = _read_required_attribute(
                scalar_variable_node,
                "valueReference",
                f"ScalarVariable {variable_name!r}",
                path,
            )
            value_reference: int = _parse_fmi_uint32(
                value_reference_raw,
                "valueReference",
                f"ScalarVariable {variable_name!r}",
                path,
            )
            variable_type: FmuVariableType
            type_node: ET.Element
            variable_type, type_node = _parse_variable_type(
                scalar_variable_node,
                variable_name,
                fmi_version_family,
                path,
            )
            derivative_index: int | None = None
            derivative_raw: Optional[str] = type_node.attrib.get("derivative", None)
            if derivative_raw is not None:
                if fmi_version_family == FmiVersion.FMI_2_0:
                    if variable_type == FmuVariableType.REAL:
                        derivative_index = _parse_fmi_uint32(
                            derivative_raw,
                            "derivative",
                            f"ScalarVariable {variable_name!r}",
                            path,
                        )
                    else:
                        raise FmuArchiveError(
                            f"ScalarVariable {variable_name!r} in {path} declares "
                            "derivative on a non-Real type"
                        )
                else:
                    raise FmuArchiveError(
                        f"ScalarVariable {variable_name!r} in {path} declares "
                        "derivative outside FMI 2"
                    )
            else:
                pass
            start: str | None = type_node.attrib.get("start", None)

            if fmi_version_family == FmiVersion.FMI_1_0:
                causality: str | None = scalar_variable_node.attrib.get(
                    "causality",
                    "internal",
                )
                variability: str | None = scalar_variable_node.attrib.get(
                    "variability",
                    "continuous",
                )
            else:
                causality = scalar_variable_node.attrib.get("causality", None)
                variability = scalar_variable_node.attrib.get("variability", None)

            variables.append(
                FmuVariableDescription(
                    name=variable_name,
                    value_reference=value_reference,
                    variable_type=variable_type,
                    causality=causality,
                    variability=variability,
                    initial=scalar_variable_node.attrib.get("initial", None),
                    start=start,
                    derivative_index=derivative_index,
                )
            )
        variable_count: int = len(variables)
        variable: FmuVariableDescription
        for variable in variables:
            if variable.derivative_index is None:
                pass
            else:
                if 1 <= variable.derivative_index <= variable_count:
                    state_variable: FmuVariableDescription = variables[
                        variable.derivative_index - 1
                    ]
                    if state_variable.variable_type == FmuVariableType.REAL:
                        pass
                    else:
                        raise FmuArchiveError(
                            f"ScalarVariable {variable.name!r} derivative index in {path} "
                            "does not reference a Real variable"
                        )
                else:
                    raise FmuArchiveError(
                        f"ScalarVariable {variable.name!r} derivative index in {path} "
                        "is outside the 1-based variable range"
                    )
        return tuple(variables)


def _parse_supported_fmi_version(
    root: ET.Element,
    path: Path,
) -> tuple[str, FmiVersion]:
    """Validate the declared version before version-specific XML parsing.

    FMI 1 and FMI 2 use the established scalar-variable parser. FMI 3 is
    dispatched to its dedicated model-description parser.

    :param root: Parsed ``fmiModelDescription`` XML root.
    :param path: FMU path used to identify validation failures.
    :return: Exact declared version and its canonical FMI family.
    :raises FmuArchiveError: If the declaration is missing, invalid, or unsupported.
    """

    # Preserve the source declaration exactly because it is provenance, while
    # the enum family provides the identity used for dispatch.
    raw_fmi_version: str | None = root.attrib.get("fmiVersion", None)
    if raw_fmi_version is not None:
        try:
            fmi_version_family: FmiVersion = parse_declared_fmi_version(raw_fmi_version)
        except (TypeError, ValueError) as exc:
            raise FmuArchiveError(
                f"Invalid FMI version declaration in {path}: {raw_fmi_version!r}"
            ) from exc
    else:
        raise FmuArchiveError(f"modelDescription.xml in {path} is missing fmiVersion")

    if (
        fmi_version_family == FmiVersion.FMI_1_0
        or fmi_version_family == FmiVersion.FMI_2_0
        or fmi_version_family == FmiVersion.FMI_3_0
    ):
        pass
    else:
        raise FmuArchiveError(
            f"FMI {raw_fmi_version} model-description parsing is not supported"
        )

    return raw_fmi_version, fmi_version_family


def read_fmu_model_description(
    path: str | Path,
    inspection_policy: FmuArchiveInspectionPolicy | None = None,
) -> FmuModelDescription:
    """Parse an FMU archive into validated model-description metadata.

    :param path: FMU archive path or extracted directory.
    :param inspection_policy: Optional finite archive-inspection limits.
    :return: Parsed FMU metadata.
    """

    # Inspect the source without extraction or native-code loading before XML
    # parsing. The receipt records exactly which source bytes were observed.
    inspection_result: FmuInspectionResult = inspect_fmu(path, policy=inspection_policy)
    normalized_path: Path = inspection_result.receipt.path
    xml_bytes: bytes = inspection_result.model_description_xml
    platforms: tuple[str, ...] = inspection_result.receipt.platforms

    # FMI model descriptions do not require DTD processing. Reject DTD and
    # entity declarations before parsing so untrusted XML cannot request entity
    # expansion; removing NUL bytes also covers UTF-16/32 ASCII declarations.
    comparable_xml: bytes = xml_bytes.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in comparable_xml or b"<!ENTITY" in comparable_xml:
        raise FmuArchiveError(
            f"DTD and entity declarations are not accepted in {normalized_path}"
        )
    else:
        pass

    # Then the XML is parsed into an element tree to extract each metadata section.
    try:
        root: ET.Element = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise FmuArchiveError(f"Invalid modelDescription.xml in {normalized_path}") from exc

    # Version dispatch precedes every FMI-family-specific structural lookup so
    # FMI 1 or FMI 3 can never be partially interpreted as FMI 2.
    raw_fmi_version: str
    fmi_version_family: FmiVersion
    raw_fmi_version, fmi_version_family = _parse_supported_fmi_version(
        root,
        normalized_path,
    )

    if root.tag.startswith("{"):
        raise FmuArchiveError(
            f"XML namespaces are not accepted for FMI {raw_fmi_version} "
            f"model descriptions in {normalized_path}"
        )
    else:
        if root.tag == "fmiModelDescription":
            pass
        else:
            raise FmuArchiveError(
                f"Invalid modelDescription.xml root element in {normalized_path}: {root.tag!r}"
            )

    if fmi_version_family == FmiVersion.FMI_3_0:
        return parse_fmi3_model_description(
            root=root,
            path=normalized_path,
            raw_fmi_version=raw_fmi_version,
            platforms=platforms,
            inspection_receipt=inspection_result.receipt,
        )
    else:
        pass

    # FMI 1 and FMI 2 schema elements are unqualified. Reject qualified children
    # before exact-name parsing so an alternate namespace cannot be ignored
    # beside an otherwise valid interface declaration.
    root_child: ET.Element
    for root_child in root:
        if root_child.tag.startswith("{"):
            raise FmuArchiveError(
                f"XML namespaces are not accepted for FMI {raw_fmi_version} "
                f"elements in {normalized_path}"
            )
        else:
            pass

    model_name: str = _read_required_attribute(
        root,
        "modelName",
        "fmiModelDescription",
        normalized_path,
    )
    guid: str = _read_required_attribute(
        root,
        "guid",
        "fmiModelDescription",
        normalized_path,
    )
    number_of_event_indicators_raw: str | None = root.attrib.get(
        "numberOfEventIndicators",
        None,
    )
    if number_of_event_indicators_raw is None:
        if fmi_version_family == FmiVersion.FMI_1_0:
            raise FmuArchiveError(
                f"fmiModelDescription in {normalized_path} is missing required "
                "attribute numberOfEventIndicators"
            )
        else:
            number_of_event_indicators: int = 0
    else:
        number_of_event_indicators = _parse_fmi_uint32(
            number_of_event_indicators_raw,
            "numberOfEventIndicators",
            "fmiModelDescription",
            normalized_path,
        )

    interface_modes: tuple[FmuInterfaceMode, ...]
    model_identifiers: dict[FmuInterfaceMode, str]
    if fmi_version_family == FmiVersion.FMI_1_0:
        model_identifier: str = _read_required_attribute(
            root,
            "modelIdentifier",
            "fmiModelDescription",
            normalized_path,
        )
        number_of_continuous_states_raw: str = _read_required_attribute(
            root,
            "numberOfContinuousStates",
            "fmiModelDescription",
            normalized_path,
        )
        _parse_fmi_uint32(
            number_of_continuous_states_raw,
            "numberOfContinuousStates",
            "fmiModelDescription",
            normalized_path,
        )
        interface_modes, model_identifiers = _parse_fmi_one_interface_modes(
            root,
            model_identifier,
            normalized_path,
        )
    else:
        interface_modes, model_identifiers = _parse_fmi_two_interface_modes(
            root,
            normalized_path,
        )
    variables: tuple[FmuVariableDescription, ...] = _parse_variables(
        root.find("ModelVariables"),
        fmi_version_family,
        normalized_path,
    )

    # Finally the metadata container is assembled for the callers.
    return FmuModelDescription(
        path=normalized_path,
        fmi_version=raw_fmi_version,
        fmi_version_family=fmi_version_family,
        inspection_receipt=inspection_result.receipt,
        model_name=model_name,
        guid=guid,
        variable_naming_convention=root.attrib.get("variableNamingConvention", None),
        number_of_event_indicators=number_of_event_indicators,
        interface_modes=interface_modes,
        model_identifiers=model_identifiers,
        platforms=platforms,
        variables=variables,
    )


def list_fmu_variable_names(
    path: str | Path,
    inspection_policy: FmuArchiveInspectionPolicy | None = None,
) -> tuple[str, ...]:
    """Return the ordered scalar-variable names declared by the FMU.

    :param path: FMU archive path or extracted directory.
    :param inspection_policy: Optional finite archive-inspection limits.
    :return: Tuple with the variable names.
    """

    metadata: FmuModelDescription = read_fmu_model_description(
        path,
        inspection_policy=inspection_policy,
    )
    return metadata.get_variable_names()


def select_declared_fmu_interface(
    path: str | Path,
    preferred_interface: FmuInterfaceMode | None = None,
    inspection_policy: FmuArchiveInspectionPolicy | None = None,
) -> FmuInterfaceMode:
    """Select one interface declared in an FMU model description.

    This metadata helper does not approve runtime execution. Runtime consumers
    must use ``FmuImportConfig.resolve_execution_mode``.

    :param path: FMU archive path or extracted directory.
    :param preferred_interface: Preferred FMI interface, when specified.
    :param inspection_policy: Optional finite archive-inspection limits.
    :return: Interface selected from the model description.
    :raises FmuModeError: If the preferred interface is absent or no represented
        interface is declared.
    """

    metadata: FmuModelDescription = read_fmu_model_description(
        path,
        inspection_policy=inspection_policy,
    )
    return metadata.select_declared_interface(preferred_interface)


def choose_fmu_mode(
    path: str | Path,
    preferred_mode: FmuInterfaceMode | None = None,
    inspection_policy: FmuArchiveInspectionPolicy | None = None,
) -> FmuInterfaceMode:
    """Call the former metadata-selection API with a deprecation warning.

    The historical name did not distinguish declared metadata from runtime
    approval. New code must use ``select_declared_fmu_interface`` for metadata
    or ``FmuImportConfig.resolve_execution_mode`` for execution.

    :param path: FMU archive path or extracted directory.
    :param preferred_mode: Preferred declared FMI interface, when specified.
    :param inspection_policy: Optional finite archive-inspection limits.
    :return: Interface selected from the model description.
    :raises FmuModeError: If the preferred interface is absent or no represented
        interface is declared.
    """

    warnings.warn(
        "choose_fmu_mode() is deprecated; use select_declared_fmu_interface()",
        DeprecationWarning,
        stacklevel=2,
    )
    return select_declared_fmu_interface(
        path=path,
        preferred_interface=preferred_mode,
        inspection_policy=inspection_policy,
    )
