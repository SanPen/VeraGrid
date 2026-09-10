# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import re
from typing import cast
import xml.etree.ElementTree as ET

from VeraGridEngine.IO.fmu.importer.errors import FmuArchiveError
from VeraGridEngine.IO.fmu.importer.inspection import FmuInspectionReceipt
from VeraGridEngine.IO.fmu.importer.model_description_metadata import (
    FmiThreeCoSimulationCapabilities,
    FmiThreeModelExchangeCapabilities,
    FmiThreeVariableDimension,
    FmuModelDescription,
    FmuVariableDescription,
)
from VeraGridEngine.IO.fmu.importer.model_description_xml import (
    parse_fmi_boolean,
    parse_fmi_float,
    parse_fmi_int32,
    parse_fmi_uint32,
    parse_fmi_uint64,
    read_required_attribute,
)
from VeraGridEngine.enumerations import FmiVersion, FmuInterfaceMode, FmuVariableType


def _validate_fmi3_element_names(element: ET.Element, path: Path) -> None:
    """Reject qualified FMI elements while preserving annotation extensions.

    :param element: FMI element whose subtree will be checked.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If an FMI element uses an XML namespace.
    """

    if element.tag.startswith("{"):
        raise FmuArchiveError(f"XML namespaces are not accepted for FMI 3 elements in {path}")
    else:
        if element.tag == "Annotation":
            pass
        else:
            child_element: ET.Element
            for child_element in element:
                _validate_fmi3_element_names(child_element, path)


def _validate_attribute_subset(
    element: ET.Element,
    allowed_attribute_names: tuple[str, ...],
    fmi_element_description: str,
    path: Path,
) -> None:
    """Reject attributes outside one represented FMI metadata subset.

    :param element: FMI element whose attributes will be checked.
    :param allowed_attribute_names: Attributes represented or safely discarded.
    :param fmi_element_description: FMI element identified in validation errors.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If an unsupported attribute is present.
    """

    declared_attribute_name: str
    for declared_attribute_name in element.attrib:
        if declared_attribute_name in allowed_attribute_names:
            pass
        else:
            raise FmuArchiveError(
                f"{fmi_element_description} attribute {declared_attribute_name!r} in {path} "
                "is outside the represented FMI 3 metadata subset"
            )


def _validate_annotations(
    annotations_element: ET.Element,
    fmi_owner_description: str,
    path: Path,
) -> None:
    """Validate an FMI 3 ``Annotations`` extension block.

    :param annotations_element: FMI ``Annotations`` element.
    :param fmi_owner_description: FMI element that owns the annotations.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If the annotation container is invalid.
    """

    if len(annotations_element.attrib) == 0:
        pass
    else:
        raise FmuArchiveError(
            f"Annotations for {fmi_owner_description} in {path} cannot declare attributes"
        )
    annotation_elements: list[ET.Element] = list(annotations_element)
    if len(annotation_elements) > 0:
        pass
    else:
        raise FmuArchiveError(
            f"Annotations for {fmi_owner_description} in {path} must contain an Annotation"
        )
    annotation_element: ET.Element
    for annotation_element in annotation_elements:
        if annotation_element.tag == "Annotation":
            pass
        else:
            raise FmuArchiveError(
                f"Unexpected {annotation_element.tag!r} in Annotations for "
                f"{fmi_owner_description} in {path}"
            )
        _validate_attribute_subset(
            annotation_element,
            ("type",),
            f"Annotation for {fmi_owner_description}",
            path,
        )
        read_required_attribute(
            annotation_element,
            "type",
            f"Annotation for {fmi_owner_description}",
            path,
        )


def _validate_optional_annotations(
    parent_element: ET.Element,
    fmi_owner_description: str,
    path: Path,
) -> None:
    """Require an element to contain at most one ``Annotations`` child.

    :param parent_element: FMI element whose children will be checked.
    :param fmi_owner_description: FMI element identified in validation errors.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If another child element is present.
    """

    child_elements: list[ET.Element] = list(parent_element)
    if len(child_elements) == 0:
        pass
    else:
        if len(child_elements) == 1 and child_elements[0].tag == "Annotations":
            _validate_annotations(child_elements[0], fmi_owner_description, path)
        else:
            raise FmuArchiveError(
                f"{fmi_owner_description} in {path} contains unsupported child elements"
            )


def _validate_fmi3_boolean_attributes(
    element: ET.Element,
    fmi_attribute_owner: str,
    attribute_names: tuple[str, ...],
    path: Path,
) -> None:
    """Validate selected FMI 3 boolean attributes.

    :param element: Element containing the optional attributes.
    :param fmi_attribute_owner: FMI element or variable that owns the attributes.
    :param attribute_names: Boolean attributes defined for this element.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If a present value is not an FMI boolean.
    """

    attribute_name: str
    for attribute_name in attribute_names:
        raw_attribute_value: str | None = element.attrib.get(attribute_name, None)
        if raw_attribute_value is None:
            pass
        else:
            parse_fmi_boolean(raw_attribute_value, attribute_name, fmi_attribute_owner, path)


def _read_optional_fmi3_boolean(
    element: ET.Element,
    attribute_name: str,
    fmi_attribute_owner: str,
    path: Path,
) -> bool:
    """Read one optional FMI 3 boolean whose default is false.

    :param element: Element containing the optional attribute.
    :param attribute_name: FMI boolean attribute name.
    :param fmi_attribute_owner: FMI element that owns the attribute.
    :param path: FMU source path included in validation errors.
    :return: Parsed value, or ``False`` when the attribute is absent.
    :raises FmuArchiveError: If a present value is not an FMI boolean.
    """

    raw_attribute_value: str | None = element.attrib.get(attribute_name, None)
    if raw_attribute_value is None:
        return False
    else:
        return parse_fmi_boolean(
            raw_attribute_value,
            attribute_name,
            fmi_attribute_owner,
            path,
        )


def _read_optional_finite_float(
    element: ET.Element,
    attribute_name: str,
    fmi_attribute_owner: str,
    path: Path,
) -> float | None:
    """Return one optional finite FMI floating-point attribute.

    :param element: FMI element containing the optional attribute.
    :param attribute_name: FMI floating-point attribute.
    :param fmi_attribute_owner: FMI element that owns the attribute.
    :param path: FMU source path included in validation errors.
    :return: Parsed value, or ``None`` when the attribute is absent.
    :raises FmuArchiveError: If a present value is not finite.
    """

    raw_attribute_value: str | None = element.attrib.get(attribute_name, None)
    if raw_attribute_value is None:
        return None
    else:
        parsed_value: float = parse_fmi_float(
            raw_attribute_value,
            attribute_name,
            fmi_attribute_owner,
            path,
        )
        if math.isfinite(parsed_value):
            return parsed_value
        else:
            raise FmuArchiveError(
                f"{fmi_attribute_owner} {attribute_name} in {path} must be finite"
            )


def _validate_optional_fmi3_generation_datetime(root: ET.Element, path: Path) -> None:
    """Validate the optional FMI 3 model-generation timestamp.

    The FMI 3 schema declares ``generationDateAndTime`` as ``xs:dateTime``.
    VeraGrid accepts the bounded four-digit Gregorian producer surface needed
    for interoperable metadata while rejecting ambiguous or unsupported XML
    Schema lexical edges.

    :param root: FMI 3 ``fmiModelDescription`` element.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If the timestamp syntax, calendar, or timezone is
        outside the represented subset.
    """

    generation_date_and_time: str | None = root.attrib.get(
        "generationDateAndTime",
        None,
    )
    if generation_date_and_time is None:
        # The schema makes this provenance field optional, so absence preserves
        # the existing metadata path without manufacturing a timestamp.
        return
    else:
        date_time_pattern: str = (
            r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
            r"T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
            r"(?:\.(?P<fraction>[0-9]+))?"
            r"(?P<timezone>Z|(?P<offset_sign>[+-])"
            r"(?P<offset_hour>[0-9]{2}):(?P<offset_minute>[0-9]{2}))?"
        )
        date_time_match: re.Match[str] | None = re.fullmatch(
            date_time_pattern,
            generation_date_and_time,
        )
        validation_error_message: str = (
            "FMI 3 fmiModelDescription attribute 'generationDateAndTime' "
            f"in {path} is not a supported xs:dateTime value"
        )
        if date_time_match is None:
            raise FmuArchiveError(validation_error_message)
        else:
            # The regular expression fixes field widths; datetime then owns
            # Gregorian month, leap-year, day, and clock-range validation.
            year: int = int(date_time_match.group("year"))
            month: int = int(date_time_match.group("month"))
            day: int = int(date_time_match.group("day"))
            hour: int = int(date_time_match.group("hour"))
            minute: int = int(date_time_match.group("minute"))
            second: int = int(date_time_match.group("second"))
            try:
                datetime(year, month, day, hour, minute, second)
            except ValueError:
                raise FmuArchiveError(validation_error_message) from None
            else:
                pass

            timezone_text: str | None = date_time_match.group("timezone")
            if timezone_text is None:
                # XML Schema permits a date-time whose timezone is absent.
                pass
            else:
                if timezone_text == "Z":
                    # Uppercase Z is the FMI-recommended UTC representation.
                    pass
                else:
                    offset_hour_text: str | None = date_time_match.group("offset_hour")
                    offset_minute_text: str | None = date_time_match.group("offset_minute")
                    if offset_hour_text is None or offset_minute_text is None:
                        raise FmuArchiveError(validation_error_message)
                    else:
                        # XML Schema bounds signed zones at fourteen hours and
                        # permits no residual minutes at that outer boundary.
                        offset_hour: int = int(offset_hour_text)
                        offset_minute: int = int(offset_minute_text)
                        offset_is_valid: bool = (
                            offset_hour <= 14
                            and offset_minute <= 59
                            and (offset_hour < 14 or offset_minute == 0)
                        )
                        if offset_is_valid:
                            pass
                        else:
                            raise FmuArchiveError(validation_error_message)


def _validate_fmi3_root_structure(root: ET.Element, path: Path) -> None:
    """Validate root attributes, child order, and represented sections.

    :param root: FMI 3 ``fmiModelDescription`` element.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If the root contains unsupported or misplaced data.
    """

    _validate_attribute_subset(
        root,
        (
            "fmiVersion", "modelName", "instantiationToken", "description", "author",
            "version", "copyright", "license", "generationTool",
            "generationDateAndTime", "variableNamingConvention",
        ),
        "FMI 3 fmiModelDescription",
        path,
    )
    _validate_optional_fmi3_generation_datetime(root, path)
    variable_naming_convention: str = root.attrib.get("variableNamingConvention", "flat")
    if variable_naming_convention == "flat":
        pass
    else:
        if variable_naming_convention == "structured":
            raise FmuArchiveError(
                "FMI 3 structured variable names are outside the represented "
                "metadata subset"
            )
        else:
            raise FmuArchiveError(
                f"FMI 3 variableNamingConvention {variable_naming_convention!r} in {path} "
                "is invalid"
            )

    root_element_order: tuple[str, ...] = (
        "ModelExchange", "CoSimulation", "ScheduledExecution", "UnitDefinitions",
        "TypeDefinitions", "LogCategories", "DefaultExperiment", "ModelVariables",
        "ModelStructure", "Annotations",
    )
    unsupported_root_elements: tuple[str, ...] = (
        "ScheduledExecution", "UnitDefinitions", "TypeDefinitions", "LogCategories",
    )
    annotations_elements: list[ET.Element] = root.findall("Annotations")
    if len(annotations_elements) <= 1:
        pass
    else:
        raise FmuArchiveError(f"FMI 3 root Annotations is duplicated in {path}")
    previous_element_index: int = -1
    root_child: ET.Element
    for root_child in root:
        if root_child.tag in root_element_order:
            current_element_index: int = root_element_order.index(root_child.tag)
        else:
            raise FmuArchiveError(f"Unexpected FMI 3 root element {root_child.tag!r} in {path}")
        if current_element_index >= previous_element_index:
            previous_element_index = current_element_index
        else:
            raise FmuArchiveError(
                f"FMI 3 root element {root_child.tag!r} is out of schema order in {path}"
            )
        if root_child.tag in unsupported_root_elements:
            raise FmuArchiveError(
                f"FMI 3 {root_child.tag} is outside the represented metadata subset"
            )
        else:
            if root_child.tag == "Annotations":
                _validate_annotations(root_child, "fmiModelDescription", path)
            else:
                pass


def _validate_default_experiment(root: ET.Element, path: Path) -> None:
    """Validate optional FMI 3 default experiment values.

    :param root: FMI 3 model-description root.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If values are duplicated or invalid.
    """

    default_experiment_elements: list[ET.Element] = root.findall("DefaultExperiment")
    if len(default_experiment_elements) > 1:
        raise FmuArchiveError(f"FMI 3 DefaultExperiment is duplicated in {path}")
    else:
        if len(default_experiment_elements) == 0:
            return
        else:
            default_experiment: ET.Element = default_experiment_elements[0]
    _validate_attribute_subset(
        default_experiment,
        ("startTime", "stopTime", "tolerance", "stepSize"),
        "FMI 3 DefaultExperiment",
        path,
    )
    _validate_optional_annotations(default_experiment, "FMI 3 DefaultExperiment", path)
    start_time: float | None = _read_optional_finite_float(
        default_experiment, "startTime", "FMI 3 DefaultExperiment", path
    )
    stop_time: float | None = _read_optional_finite_float(
        default_experiment, "stopTime", "FMI 3 DefaultExperiment", path
    )
    tolerance: float | None = _read_optional_finite_float(
        default_experiment, "tolerance", "FMI 3 DefaultExperiment", path
    )
    step_size: float | None = _read_optional_finite_float(
        default_experiment, "stepSize", "FMI 3 DefaultExperiment", path
    )
    if tolerance is None or tolerance > 0.0:
        pass
    else:
        raise FmuArchiveError(f"FMI 3 DefaultExperiment tolerance in {path} must be positive")
    if step_size is None or step_size > 0.0:
        pass
    else:
        raise FmuArchiveError(f"FMI 3 DefaultExperiment stepSize in {path} must be positive")
    if start_time is None or stop_time is None or stop_time > start_time:
        pass
    else:
        raise FmuArchiveError(
            f"FMI 3 DefaultExperiment stopTime in {path} must be greater than startTime"
        )


def _parse_fmi3_interfaces(
    root: ET.Element,
    path: Path,
) -> tuple[
    tuple[FmuInterfaceMode, ...],
    dict[FmuInterfaceMode, str],
    FmiThreeCoSimulationCapabilities | None,
    FmiThreeModelExchangeCapabilities | None,
]:
    """Parse represented FMI 3 interface declarations.

    :param root: FMI 3 model-description root.
    :param path: FMU source path included in validation errors.
    :return: Declared interfaces, identifiers, and lifecycle capabilities.
    :raises FmuArchiveError: If an interface is duplicated, incomplete, or unsupported.
    """

    common_boolean_attributes: tuple[str, ...] = (
        "needsExecutionTool", "canBeInstantiatedOnlyOncePerProcess",
        "canGetAndSetFMUState", "canSerializeFMUState",
        "providesDirectionalDerivatives", "providesAdjointDerivatives",
        "providesPerElementDependencies",
    )
    interface_definitions: tuple[tuple[FmuInterfaceMode, str, tuple[str, ...]], ...] = (
        (FmuInterfaceMode.MODEL_EXCHANGE, "ModelExchange",
         ("needsCompletedIntegratorStep", "providesEvaluateDiscreteStates")),
        (FmuInterfaceMode.CO_SIMULATION, "CoSimulation",
         ("canHandleVariableCommunicationStepSize", "providesIntermediateUpdate",
          "mightReturnEarlyFromDoStep", "canReturnEarlyAfterIntermediateUpdate",
          "hasEventMode", "providesEvaluateDiscreteStates")),
    )
    interface_modes: list[FmuInterfaceMode] = list()
    model_identifiers: dict[FmuInterfaceMode, str] = dict()
    co_simulation_capabilities: FmiThreeCoSimulationCapabilities | None = None
    model_exchange_capabilities: FmiThreeModelExchangeCapabilities | None = None
    interface_mode: FmuInterfaceMode
    interface_element_name: str
    interface_boolean_attributes: tuple[str, ...]
    for interface_mode, interface_element_name, interface_boolean_attributes in interface_definitions:
        interface_elements: list[ET.Element] = root.findall(interface_element_name)
        if len(interface_elements) > 1:
            raise FmuArchiveError(
                f"FMI 3 {interface_element_name} interface is duplicated in {path}"
            )
        else:
            if len(interface_elements) == 1:
                interface_element: ET.Element = interface_elements[0]
                allowed_interface_attributes: tuple[str, ...] = (
                    ("modelIdentifier",)
                    + common_boolean_attributes
                    + interface_boolean_attributes
                )
                if interface_mode == FmuInterfaceMode.CO_SIMULATION:
                    allowed_interface_attributes = allowed_interface_attributes + (
                        "fixedInternalStepSize",
                        "maxOutputDerivativeOrder",
                        "recommendedIntermediateInputSmoothness",
                    )
                else:
                    pass
                _validate_attribute_subset(
                    interface_element,
                    allowed_interface_attributes,
                    f"FMI 3 {interface_element_name}",
                    path,
                )
                model_identifier: str = read_required_attribute(
                    interface_element, "modelIdentifier", interface_element_name, path
                )
                _validate_optional_annotations(
                    interface_element, f"FMI 3 {interface_element_name}", path
                )
                can_get_and_set_fmu_state: bool = _read_optional_fmi3_boolean(
                    interface_element,
                    "canGetAndSetFMUState",
                    interface_element_name,
                    path,
                )
                can_serialize_fmu_state: bool = _read_optional_fmi3_boolean(
                    interface_element,
                    "canSerializeFMUState",
                    interface_element_name,
                    path,
                )
                if can_serialize_fmu_state and not can_get_and_set_fmu_state:
                    raise FmuArchiveError(
                        f"FMI 3 {interface_element_name} canSerializeFMUState "
                        f"in {path} requires canGetAndSetFMUState=true"
                    )
                else:
                    pass
                if interface_mode == FmuInterfaceMode.CO_SIMULATION:
                    # Store every flag that changes worker construction or the
                    # supported step lifecycle. Other optional capabilities are
                    # still validated but remain outside the execution profile.
                    needs_execution_tool: bool = _read_optional_fmi3_boolean(
                        interface_element, "needsExecutionTool", interface_element_name, path
                    )
                    can_be_instantiated_only_once_per_process: bool = (
                        _read_optional_fmi3_boolean(
                            interface_element,
                            "canBeInstantiatedOnlyOncePerProcess",
                            interface_element_name,
                            path,
                        )
                    )
                    can_handle_variable_communication_step_size: bool = (
                        _read_optional_fmi3_boolean(
                            interface_element,
                            "canHandleVariableCommunicationStepSize",
                            interface_element_name,
                            path,
                        )
                    )
                    provides_intermediate_update: bool = _read_optional_fmi3_boolean(
                        interface_element,
                        "providesIntermediateUpdate",
                        interface_element_name,
                        path,
                    )
                    might_return_early_from_do_step: bool = _read_optional_fmi3_boolean(
                        interface_element,
                        "mightReturnEarlyFromDoStep",
                        interface_element_name,
                        path,
                    )
                    can_return_early_after_intermediate_update: bool = (
                        _read_optional_fmi3_boolean(
                            interface_element,
                            "canReturnEarlyAfterIntermediateUpdate",
                            interface_element_name,
                            path,
                        )
                    )
                    if (
                        can_return_early_after_intermediate_update
                        and not provides_intermediate_update
                    ):
                        raise FmuArchiveError(
                            "FMI 3 CoSimulation canReturnEarlyAfterIntermediateUpdate "
                            f"in {path} requires providesIntermediateUpdate=true"
                        )
                    else:
                        pass
                    has_event_mode: bool = _read_optional_fmi3_boolean(
                        interface_element, "hasEventMode", interface_element_name, path
                    )
                    _validate_fmi3_boolean_attributes(
                        interface_element,
                        interface_element_name,
                        (
                            "providesDirectionalDerivatives",
                            "providesAdjointDerivatives",
                            "providesPerElementDependencies",
                            "providesEvaluateDiscreteStates",
                        ),
                        path,
                    )
                    fixed_internal_step_size_text: str | None = interface_element.attrib.get(
                        "fixedInternalStepSize", None
                    )
                    if fixed_internal_step_size_text is None:
                        fixed_internal_step_size: float | None = None
                    else:
                        fixed_step_size: float = parse_fmi_float(
                            fixed_internal_step_size_text,
                            "fixedInternalStepSize",
                            interface_element_name,
                            path,
                        )
                        if math.isfinite(fixed_step_size) and fixed_step_size > 0.0:
                            fixed_internal_step_size = fixed_step_size
                        else:
                            raise FmuArchiveError(
                                f"FMI 3 CoSimulation fixedInternalStepSize in {path} "
                                "must be finite and positive"
                            )
                    maximum_output_derivative_order_text: str | None = interface_element.attrib.get(
                        "maxOutputDerivativeOrder", None
                    )
                    if maximum_output_derivative_order_text is None:
                        pass
                    else:
                        parse_fmi_uint32(
                            maximum_output_derivative_order_text,
                            "maxOutputDerivativeOrder",
                            interface_element_name,
                            path,
                        )
                    recommended_intermediate_input_smoothness_text: str | None = (
                        interface_element.attrib.get(
                        "recommendedIntermediateInputSmoothness", None
                        )
                    )
                    if recommended_intermediate_input_smoothness_text is None:
                        pass
                    else:
                        parse_fmi_int32(
                            recommended_intermediate_input_smoothness_text,
                            "recommendedIntermediateInputSmoothness",
                            interface_element_name,
                            path,
                        )
                    co_simulation_capabilities = FmiThreeCoSimulationCapabilities(
                        needs_execution_tool=needs_execution_tool,
                        can_be_instantiated_only_once_per_process=(
                            can_be_instantiated_only_once_per_process
                        ),
                        can_get_and_set_fmu_state=can_get_and_set_fmu_state,
                        can_serialize_fmu_state=can_serialize_fmu_state,
                        can_handle_variable_communication_step_size=(
                            can_handle_variable_communication_step_size
                        ),
                        provides_intermediate_update=provides_intermediate_update,
                        might_return_early_from_do_step=might_return_early_from_do_step,
                        can_return_early_after_intermediate_update=(
                            can_return_early_after_intermediate_update
                        ),
                        has_event_mode=has_event_mode,
                        fixed_internal_step_size=fixed_internal_step_size,
                    )
                else:
                    # Preserve every flag that changes Model Exchange process
                    # construction or integrator lifecycle. Remaining common
                    # capabilities stay validated without duplicating metadata.
                    model_exchange_needs_execution_tool: bool = _read_optional_fmi3_boolean(
                        interface_element, "needsExecutionTool", interface_element_name, path
                    )
                    model_exchange_single_instantiation: bool = (
                        _read_optional_fmi3_boolean(
                            interface_element,
                            "canBeInstantiatedOnlyOncePerProcess",
                            interface_element_name,
                            path,
                        )
                    )
                    needs_completed_integrator_step: bool = _read_optional_fmi3_boolean(
                        interface_element,
                        "needsCompletedIntegratorStep",
                        interface_element_name,
                        path,
                    )
                    provides_evaluate_discrete_states: bool = _read_optional_fmi3_boolean(
                        interface_element,
                        "providesEvaluateDiscreteStates",
                        interface_element_name,
                        path,
                    )
                    _validate_fmi3_boolean_attributes(
                        interface_element,
                        interface_element_name,
                        (
                            "providesDirectionalDerivatives",
                            "providesAdjointDerivatives",
                            "providesPerElementDependencies",
                        ),
                        path,
                    )
                    model_exchange_capabilities = FmiThreeModelExchangeCapabilities(
                        needs_execution_tool=model_exchange_needs_execution_tool,
                        can_be_instantiated_only_once_per_process=(
                            model_exchange_single_instantiation
                        ),
                        can_get_and_set_fmu_state=can_get_and_set_fmu_state,
                        can_serialize_fmu_state=can_serialize_fmu_state,
                        needs_completed_integrator_step=needs_completed_integrator_step,
                        provides_evaluate_discrete_states=provides_evaluate_discrete_states,
                    )
                interface_modes.append(interface_mode)
                model_identifiers[interface_mode] = model_identifier
            else:
                pass
    if len(interface_modes) > 0:
        return (
            tuple(interface_modes),
            model_identifiers,
            co_simulation_capabilities,
            model_exchange_capabilities,
        )
    else:
        raise FmuArchiveError(
            f"FMI 3 model description in {path} declares neither ModelExchange nor CoSimulation"
        )


def _parse_fmi3_array_dimensions(
    variable_element: ET.Element,
    variable_name: str,
    path: Path,
) -> tuple[FmiThreeVariableDimension, ...]:
    """Parse ordered constant or referenced dimensions and annotations.

    :param variable_element: FMI 3 variable element containing child metadata.
    :param variable_name: Required variable name used in diagnostics.
    :param path: FMU source path included in validation errors.
    :return: Ordered typed dimensions, or an empty tuple for a scalar.
    :raises FmuArchiveError: If child order, attributes, or sizes are invalid.
    """

    child_elements: list[ET.Element] = list(variable_element)
    variable_text: str | None = variable_element.text
    if variable_text is None or len(variable_text.strip()) == 0:
        pass
    else:
        raise FmuArchiveError(
            f"FMI 3 variable {variable_name!r} in {path} contains text outside "
            "its child elements"
        )
    child_element_with_tail: ET.Element
    for child_element_with_tail in child_elements:
        child_tail: str | None = child_element_with_tail.tail
        if child_tail is None or len(child_tail.strip()) == 0:
            pass
        else:
            raise FmuArchiveError(
                f"FMI 3 variable {variable_name!r} in {path} contains text outside "
                "its child elements"
            )
    first_dimension_index: int = 0
    if len(child_elements) > 0 and child_elements[0].tag == "Annotations":
        _validate_annotations(
            child_elements[0],
            f"FMI 3 variable {variable_name!r}",
            path,
        )
        first_dimension_index = 1
    else:
        pass
    dimension_count: int = len(child_elements) - first_dimension_index
    dimensions: list[FmiThreeVariableDimension | None] = [None] * dimension_count
    dimension_index: int
    for dimension_index in range(dimension_count):
        child_element: ET.Element = child_elements[
            first_dimension_index + dimension_index
        ]
        if child_element.tag == "Dimension":
            dimension_owner: str = (
                f"FMI 3 variable {variable_name!r} Dimension {dimension_index + 1}"
            )
            _validate_attribute_subset(
                child_element,
                ("start", "valueReference"),
                dimension_owner,
                path,
            )
            if len(child_element) == 0:
                pass
            else:
                raise FmuArchiveError(
                    f"{dimension_owner} in {path} must not contain child elements"
                )
            dimension_text: str | None = child_element.text
            if dimension_text is None or len(dimension_text.strip()) == 0:
                pass
            else:
                raise FmuArchiveError(
                    f"{dimension_owner} in {path} must not contain text"
                )
            start_text: str | None = child_element.attrib.get("start", None)
            value_reference_text: str | None = child_element.attrib.get(
                "valueReference",
                None,
            )
            if start_text is not None and value_reference_text is None:
                start_size: int = parse_fmi_uint64(
                    start_text,
                    "start",
                    dimension_owner,
                    path,
                )
                if start_size > 0:
                    dimensions[dimension_index] = FmiThreeVariableDimension(
                        constant_size=start_size,
                        value_reference=None,
                    )
                else:
                    raise FmuArchiveError(
                        f"{dimension_owner} in {path} must be positive"
                    )
            else:
                if start_text is None and value_reference_text is not None:
                    dimension_value_reference: int = parse_fmi_uint32(
                        raw_attribute_value=value_reference_text,
                        attribute_name="valueReference",
                        fmi_attribute_owner=dimension_owner,
                        path=path,
                    )
                    dimensions[dimension_index] = FmiThreeVariableDimension(
                        constant_size=None,
                        value_reference=dimension_value_reference,
                    )
                else:
                    raise FmuArchiveError(
                        f"{dimension_owner} in {path} must declare exactly one of "
                        "start or valueReference"
                    )
        else:
            raise FmuArchiveError(
                f"FMI 3 variable {variable_name!r} in {path} contains "
                "unsupported or out-of-order child elements"
            )
    return cast(tuple[FmiThreeVariableDimension, ...], tuple(dimensions))


def _parse_fmi3_variable_semantics(
    variable_element: ET.Element,
    variable_name: str,
    variable_type: FmuVariableType,
    dimensions: tuple[FmiThreeVariableDimension, ...],
    path: Path,
) -> tuple[str, str, str | None, str | None]:
    """Resolve causality, variability, initial condition, and start values.

    :param variable_element: Supported primitive variable element.
    :param variable_name: Required variable name.
    :param variable_type: Parsed FMI 3 primitive type.
    :param dimensions: Ordered constant or referenced array dimensions.
    :param path: FMU source path included in validation errors.
    :return: Effective causality, variability, initial condition, and start text.
    :raises FmuArchiveError: If the semantic combination is invalid.
    """

    causality: str = variable_element.attrib.get("causality", "local")
    declared_variability: str | None = variable_element.attrib.get("variability", None)
    if declared_variability is None:
        if causality in ("parameter", "calculatedParameter", "structuralParameter"):
            variability: str = "fixed"
        else:
            variability = "continuous"
    else:
        variability = declared_variability
    declared_initial: str | None = variable_element.attrib.get("initial", None)
    if declared_initial is None:
        if variability == "constant":
            if causality == "output" or causality == "local":
                initial: str | None = "exact"
            else:
                initial = None
        else:
            if variability == "fixed" or variability == "tunable":
                if causality == "structuralParameter" or causality == "parameter":
                    initial = "exact"
                else:
                    if causality == "calculatedParameter" or causality == "local":
                        initial = "calculated"
                    else:
                        initial = None
            else:
                if variability == "discrete" or variability == "continuous":
                    if causality == "input":
                        initial = "exact"
                    else:
                        if causality == "output" or causality == "local":
                            initial = "calculated"
                        else:
                            initial = None
                else:
                    initial = None
    else:
        initial = declared_initial
    legal_semantic_combinations: tuple[tuple[str, str, str | None], ...] = (
        ("structuralParameter", "fixed", "exact"),
        ("structuralParameter", "tunable", "exact"),
        ("parameter", "fixed", "exact"), ("parameter", "tunable", "exact"),
        ("calculatedParameter", "fixed", "calculated"),
        ("calculatedParameter", "fixed", "approx"),
        ("calculatedParameter", "tunable", "calculated"),
        ("calculatedParameter", "tunable", "approx"),
        ("input", "discrete", "exact"), ("input", "continuous", "exact"),
        ("output", "constant", "exact"), ("output", "discrete", "calculated"),
        ("output", "discrete", "exact"), ("output", "discrete", "approx"),
        ("output", "continuous", "calculated"), ("output", "continuous", "exact"),
        ("output", "continuous", "approx"), ("local", "constant", "exact"),
        ("local", "fixed", "calculated"), ("local", "fixed", "approx"),
        ("local", "tunable", "calculated"), ("local", "tunable", "approx"),
        ("local", "discrete", "calculated"), ("local", "discrete", "exact"),
        ("local", "discrete", "approx"), ("local", "continuous", "calculated"),
        ("local", "continuous", "exact"), ("local", "continuous", "approx"),
        ("independent", "continuous", None),
    )
    if (causality, variability, initial) in legal_semantic_combinations:
        pass
    else:
        raise FmuArchiveError(
            f"FMI 3 variable {variable_name!r} in {path} has invalid causality, "
            "variability, and initial semantics"
        )
    start_value: str | None = variable_element.attrib.get("start", None)
    requires_start: bool = initial in ("exact", "approx") or causality == "input"
    if requires_start:
        if start_value is None:
            raise FmuArchiveError(
                f"FMI 3 variable {variable_name!r} in {path} requires a start value"
            )
        else:
            pass
    else:
        if start_value is None:
            pass
        else:
            raise FmuArchiveError(
                f"FMI 3 variable {variable_name!r} in {path} cannot declare a start value"
            )
    if start_value is None:
        pass
    else:
        start_values: list[str] = start_value.split()
        start_value_text: str
        for start_value_text in start_values:
            if variable_type in (
                FmuVariableType.FLOAT32,
                FmuVariableType.FLOAT64,
            ):
                parse_fmi_float(
                    start_value_text,
                    "start",
                    f"FMI 3 variable {variable_name!r}",
                    path,
                )
            else:
                if variable_type == FmuVariableType.UINT64:
                    parse_fmi_uint64(
                        start_value_text,
                        "start",
                        f"FMI 3 variable {variable_name!r}",
                        path,
                    )
                else:
                    raise FmuArchiveError(
                        f"Unsupported FMI 3 start type for variable "
                        f"{variable_name!r} in {path}"
                    )
        if len(dimensions) == 0:
            if len(start_values) == 1:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 scalar variable {variable_name!r} in {path} must "
                    "declare one start value"
                )
        else:
            pass
    return causality, variability, initial, start_value


def _resolve_fmi3_initial_dimension_sizes(
    variable: FmuVariableDescription,
    variables_by_reference: dict[int, FmuVariableDescription],
    path: Path,
) -> tuple[int, ...]:
    """Resolve one variable's initial dimensions from declarative metadata.

    :param variable: Variable owning the ordered dimensions.
    :param variables_by_reference: Bounded lookup for referenced variables.
    :param path: FMU source path included in validation errors.
    :return: Positive initial UInt64 sizes in dimension order.
    :raises FmuArchiveError: If a referenced dimension source is invalid.
    """

    dimension_sizes: list[int] = [0] * len(variable.dimensions)
    dimension_index: int
    for dimension_index in range(len(variable.dimensions)):
        dimension: FmiThreeVariableDimension = variable.dimensions[dimension_index]
        if dimension.constant_size is not None:
            dimension_sizes[dimension_index] = dimension.constant_size
        else:
            value_reference: int | None = dimension.value_reference
            if value_reference is not None:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable {variable.name!r} in {path} has an invalid "
                    "dimension owner"
                )
            source_variable: FmuVariableDescription | None = (
                variables_by_reference.get(value_reference, None)
            )
            if source_variable is not None:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable {variable.name!r} in {path} has a Dimension "
                    f"referencing missing valueReference {value_reference}"
                )
            if source_variable.variable_type == FmuVariableType.UINT64:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable {variable.name!r} in {path} has a Dimension "
                    "whose valueReference is not UInt64"
                )
            if len(source_variable.dimensions) == 0:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable {variable.name!r} in {path} has a Dimension "
                    "whose UInt64 source is not scalar"
                )
            source_is_legal: bool = (
                source_variable.variability == "constant"
                or source_variable.causality == "structuralParameter"
            )
            if source_is_legal:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable {variable.name!r} in {path} has a Dimension "
                    "whose UInt64 source is neither constant nor a structural "
                    "parameter"
                )
            if source_variable.start is not None:
                initial_size: int = parse_fmi_uint64(
                    source_variable.start,
                    "start",
                    f"FMI 3 dimension source {source_variable.name!r}",
                    path,
                )
            else:
                raise FmuArchiveError(
                    f"FMI 3 dimension source {source_variable.name!r} in {path} "
                    "requires a start value"
                )
            if initial_size > 0:
                dimension_sizes[dimension_index] = initial_size
            else:
                raise FmuArchiveError(
                    f"FMI 3 dimension source {source_variable.name!r} in {path} "
                    "must have a positive initial size"
                )
    return tuple(dimension_sizes)


def _validate_fmi3_dimension_references_and_start_cardinalities(
    variables: tuple[FmuVariableDescription, ...],
    path: Path,
) -> None:
    """Validate dimension references and default array cardinalities.

    :param variables: Complete parsed FMI 3 variable collection.
    :param path: FMU source path included in validation errors.
    :return: None.
    :raises FmuArchiveError: If dimension semantics or start counts are invalid.
    """

    variables_by_reference: dict[int, FmuVariableDescription] = dict()
    variable: FmuVariableDescription
    for variable in variables:
        variables_by_reference[variable.value_reference] = variable
    for variable in variables:
        if variable.causality == "structuralParameter":
            if len(variable.dimensions) == 0:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 structural parameter {variable.name!r} in {path} "
                    "must be scalar"
                )
        else:
            pass
        initial_dimension_sizes: tuple[int, ...] = (
            _resolve_fmi3_initial_dimension_sizes(
                variable=variable,
                variables_by_reference=variables_by_reference,
                path=path,
            )
        )
        if variable.start is not None and len(initial_dimension_sizes) > 0:
            start_value_count: int = len(variable.start.split())
            if start_value_count == 1:
                pass
            else:
                expected_value_count: int = 1
                dimension_size: int
                for dimension_size in initial_dimension_sizes:
                    if expected_value_count <= start_value_count:
                        expected_value_count *= dimension_size
                    else:
                        pass
                if start_value_count == expected_value_count:
                    pass
                else:
                    raise FmuArchiveError(
                        f"FMI 3 array variable {variable.name!r} in {path} start "
                        "cardinality does not match its initial dimensions"
                    )
        else:
            pass


def _parse_fmi3_variables(
    model_variables: ET.Element,
    path: Path,
) -> tuple[FmuVariableDescription, ...]:
    """Parse represented floating-point and UInt64 FMI 3 variables.

    :param model_variables: Required FMI 3 ``ModelVariables`` element.
    :param path: FMU source path included in validation errors.
    :return: Ordered supported primitive-variable metadata.
    :raises FmuArchiveError: If variable metadata is unsupported or ambiguous.
    """

    variable_elements: list[ET.Element] = list(model_variables)
    if len(variable_elements) > 0:
        variables: list[FmuVariableDescription | None] = [None] * len(variable_elements)
    else:
        raise FmuArchiveError(f"FMI 3 ModelVariables in {path} must not be empty")
    supported_variable_types: tuple[FmuVariableType, ...] = (
        FmuVariableType.FLOAT32,
        FmuVariableType.FLOAT64,
        FmuVariableType.UINT64,
    )
    allowed_variable_attributes: tuple[str, ...] = (
        "name", "valueReference", "description", "causality", "variability",
        "initial", "start", "derivative",
    )
    variable_names: set[str] = set()
    value_references: set[int] = set()
    independent_variable_count: int = 0
    variable_index: int
    for variable_index in range(len(variable_elements)):
        variable_element: ET.Element = variable_elements[variable_index]
        try:
            variable_type: FmuVariableType = FmuVariableType(variable_element.tag)
        except ValueError as exc:
            raise FmuArchiveError(
                f"Unknown FMI 3 variable type {variable_element.tag!r} in {path}"
            ) from exc
        if variable_type == FmuVariableType.UNKNOWN:
            raise FmuArchiveError(f"Unknown FMI 3 variable type {variable_element.tag!r} in {path}")
        else:
            if variable_type in supported_variable_types:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 variable type {variable_element.tag!r} is outside "
                    "the represented Float32, Float64, and UInt64 subset"
                )
        variable_name: str = read_required_attribute(
            variable_element, "name", variable_element.tag, path
        )
        _validate_attribute_subset(
            variable_element,
            allowed_variable_attributes,
            f"FMI 3 variable {variable_name!r}",
            path,
        )
        dimensions: tuple[FmiThreeVariableDimension, ...] = (
            _parse_fmi3_array_dimensions(
                variable_element,
                variable_name,
                path,
            )
        )
        if variable_name in variable_names:
            raise FmuArchiveError(f"FMI 3 variable name {variable_name!r} is duplicated in {path}")
        else:
            variable_names.add(variable_name)
        value_reference: int = parse_fmi_uint32(
            read_required_attribute(
                variable_element,
                "valueReference",
                f"FMI 3 variable {variable_name!r}",
                path,
            ),
            "valueReference",
            f"FMI 3 variable {variable_name!r}",
            path,
        )
        if value_reference in value_references:
            raise FmuArchiveError(
                f"FMI 3 valueReference {value_reference} is ambiguous in {path}"
            )
        else:
            value_references.add(value_reference)
        causality: str
        variability: str
        initial: str | None
        start_value: str | None
        causality, variability, initial, start_value = _parse_fmi3_variable_semantics(
            variable_element,
            variable_name,
            variable_type,
            dimensions,
            path,
        )
        if causality == "independent":
            independent_variable_count += 1
        else:
            pass
        state_value_reference_text: str | None = variable_element.attrib.get("derivative", None)
        if state_value_reference_text is None:
            state_value_reference: int | None = None
        else:
            state_value_reference = parse_fmi_uint32(
                state_value_reference_text,
                "derivative",
                f"FMI 3 variable {variable_name!r}",
                path,
            )
        if variable_type == FmuVariableType.UINT64:
            if state_value_reference is None and causality != "independent":
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 UInt64 variable {variable_name!r} in {path} cannot "
                    "be independent or declare a derivative"
                )
        else:
            pass
        variables[variable_index] = FmuVariableDescription(
            name=variable_name,
            value_reference=value_reference,
            variable_type=variable_type,
            causality=causality,
            variability=variability,
            initial=initial,
            start=start_value,
            derivative_index=None,
            state_value_reference=state_value_reference,
            dimensions=dimensions,
        )
    if independent_variable_count == 1:
        pass
    else:
        raise FmuArchiveError(
            f"FMI 3 ModelVariables in {path} must declare exactly one independent variable"
        )
    parsed_variables: tuple[FmuVariableDescription, ...] = cast(
        tuple[FmuVariableDescription, ...],
        tuple(variables),
    )
    _validate_fmi3_dimension_references_and_start_cardinalities(
        variables=parsed_variables,
        path=path,
    )
    variables_by_value_reference: dict[int, FmuVariableDescription] = dict()
    parsed_variable: FmuVariableDescription
    for parsed_variable in parsed_variables:
        variables_by_value_reference[parsed_variable.value_reference] = parsed_variable
    referenced_state_value_references: set[int] = set()
    for parsed_variable in parsed_variables:
        state_value_reference = parsed_variable.state_value_reference
        if state_value_reference is None:
            pass
        else:
            state_variable: FmuVariableDescription | None = variables_by_value_reference.get(
                state_value_reference, None
            )
            if state_variable is None:
                raise FmuArchiveError(
                    f"FMI 3 derivative variable {parsed_variable.name!r} references missing "
                    f"state valueReference {state_value_reference}"
                )
            else:
                if state_variable.variable_type == parsed_variable.variable_type:
                    pass
                else:
                    raise FmuArchiveError(
                        f"FMI 3 derivative variable {parsed_variable.name!r} and its state "
                        "must use the same floating-point type"
                    )
            if parsed_variable.variability == "continuous" and state_variable.variability == "continuous":
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 derivative variable {parsed_variable.name!r} and its state "
                    "must be continuous"
                )
            if (
                parsed_variable.causality in ("local", "output")
                and state_variable.causality in ("local", "output")
            ):
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 derivative variable {parsed_variable.name!r} and its state "
                    "must have local or output causality"
                )
            if state_variable.state_value_reference is None:
                pass
            else:
                raise FmuArchiveError(
                    f"FMI 3 derivative variable {parsed_variable.name!r} references another derivative"
                )
            if state_value_reference in referenced_state_value_references:
                raise FmuArchiveError(
                    f"FMI 3 state valueReference {state_value_reference} has multiple derivatives"
                )
            else:
                referenced_state_value_references.add(state_value_reference)
    return parsed_variables


def _parse_fmi3_model_structure(
    model_structure: ET.Element,
    variables: tuple[FmuVariableDescription, ...],
    path: Path,
) -> int:
    """Validate the represented FMI 3 model structure.

    :param model_structure: Required FMI 3 ``ModelStructure`` element.
    :param variables: Parsed variables addressed by value reference.
    :param path: FMU source path included in validation errors.
    :return: Number of serialized event-indicator values.
    :raises FmuArchiveError: If references, order, or semantic sets are invalid.
    """

    variables_by_reference: dict[int, FmuVariableDescription] = dict()
    expected_output_references: set[int] = set()
    expected_derivative_references: set[int] = set()
    expected_initial_unknown_references: set[int] = set()
    variable: FmuVariableDescription
    for variable in variables:
        variables_by_reference[variable.value_reference] = variable
        if variable.causality == "output":
            expected_output_references.add(variable.value_reference)
        else:
            pass
        if variable.state_value_reference is None:
            pass
        else:
            expected_derivative_references.add(variable.value_reference)
        if (
            (variable.causality == "output" and variable.initial in ("approx", "calculated"))
            or variable.causality == "calculatedParameter"
        ):
            expected_initial_unknown_references.add(variable.value_reference)
        else:
            pass
    derivative_variable: FmuVariableDescription
    for derivative_variable in variables:
        state_reference: int | None = derivative_variable.state_value_reference
        if state_reference is None:
            pass
        else:
            state_variable: FmuVariableDescription = variables_by_reference[state_reference]
            if state_variable.initial in ("approx", "calculated"):
                expected_initial_unknown_references.add(state_variable.value_reference)
            else:
                pass
            if derivative_variable.initial in ("approx", "calculated"):
                expected_initial_unknown_references.add(derivative_variable.value_reference)
            else:
                pass

    structure_order: tuple[str, ...] = (
        "Output", "ContinuousStateDerivative", "ClockedState", "InitialUnknown",
        "EventIndicator",
    )
    output_references: set[int] = set()
    derivative_references: set[int] = set()
    initial_unknown_references: set[int] = set()
    event_indicator_references: set[int] = set()
    previous_structure_index: int = -1
    structure_element: ET.Element
    for structure_element in model_structure:
        if structure_element.tag in structure_order:
            structure_index: int = structure_order.index(structure_element.tag)
        else:
            raise FmuArchiveError(
                f"Unexpected FMI 3 ModelStructure element {structure_element.tag!r} in {path}"
            )
        if structure_index >= previous_structure_index:
            previous_structure_index = structure_index
        else:
            raise FmuArchiveError(
                f"FMI 3 ModelStructure element {structure_element.tag!r} is out of schema order"
            )
        if "dependencies" in structure_element.attrib or "dependenciesKind" in structure_element.attrib:
            raise FmuArchiveError(
                "FMI 3 ModelStructure dependencies are outside the represented "
                "metadata subset"
            )
        else:
            pass
        _validate_attribute_subset(
            structure_element,
            ("valueReference",),
            f"FMI 3 ModelStructure {structure_element.tag}",
            path,
        )
        _validate_optional_annotations(
            structure_element, f"FMI 3 ModelStructure {structure_element.tag}", path
        )
        value_reference: int = parse_fmi_uint32(
            read_required_attribute(
                structure_element, "valueReference", structure_element.tag, path
            ),
            "valueReference",
            structure_element.tag,
            path,
        )
        referenced_variable: FmuVariableDescription | None = variables_by_reference.get(
            value_reference, None
        )
        if referenced_variable is None:
            raise FmuArchiveError(
                f"FMI 3 {structure_element.tag} in {path} references unknown "
                f"valueReference {value_reference}"
            )
        else:
            pass
        if structure_element.tag == "Output":
            if referenced_variable.causality == "output":
                target_references: set[int] = output_references
            else:
                raise FmuArchiveError(
                    f"FMI 3 Output in {path} must reference a variable with output causality"
                )
        else:
            if structure_element.tag == "ContinuousStateDerivative":
                if referenced_variable.state_value_reference is not None:
                    target_references = derivative_references
                else:
                    raise FmuArchiveError(
                        "FMI 3 ContinuousStateDerivative must reference a variable with a "
                        "derivative attribute"
                    )
            else:
                if structure_element.tag == "ClockedState":
                    raise FmuArchiveError(
                        "FMI 3 ClockedState is outside the represented metadata subset"
                    )
                else:
                    if structure_element.tag == "InitialUnknown":
                        target_references = initial_unknown_references
                    else:
                        target_references = event_indicator_references
        if value_reference in target_references:
            raise FmuArchiveError(
                f"FMI 3 {structure_element.tag} duplicates valueReference {value_reference}"
            )
        else:
            target_references.add(value_reference)
    if output_references == expected_output_references:
        pass
    else:
        raise FmuArchiveError(
            "FMI 3 ModelStructure outputs do not match variables with output causality"
        )
    if derivative_references == expected_derivative_references:
        pass
    else:
        raise FmuArchiveError(
            "FMI 3 ModelStructure continuous-state derivatives do not match variable metadata"
        )
    if initial_unknown_references == expected_initial_unknown_references:
        pass
    else:
        raise FmuArchiveError(
            "FMI 3 ModelStructure initial unknowns do not match variable metadata"
        )
    # FMI 3 exposes this cardinality through size_t. Bound parser arithmetic to
    # the maximum 64-bit size_t of the supported native platform families.
    maximum_represented_event_indicator_count: int = 18446744073709551615
    number_of_event_indicators: int = 0
    event_indicator_reference: int
    for event_indicator_reference in event_indicator_references:
        event_indicator_variable: FmuVariableDescription = variables_by_reference[
            event_indicator_reference
        ]
        serialized_value_count: int = 1
        initial_dimension_sizes: tuple[int, ...] = (
            _resolve_fmi3_initial_dimension_sizes(
                variable=event_indicator_variable,
                variables_by_reference=variables_by_reference,
                path=path,
            )
        )
        dimension_size: int
        for dimension_size in initial_dimension_sizes:
            if (
                serialized_value_count
                <= maximum_represented_event_indicator_count // dimension_size
            ):
                serialized_value_count *= dimension_size
            else:
                raise FmuArchiveError(
                    "FMI 3 event-indicator cardinality exceeds the represented "
                    "unsigned 64-bit size_t limit"
                )
        if (
            number_of_event_indicators
            <= maximum_represented_event_indicator_count - serialized_value_count
        ):
            number_of_event_indicators += serialized_value_count
        else:
            raise FmuArchiveError(
                "FMI 3 event-indicator cardinality exceeds the represented "
                "unsigned 64-bit size_t limit"
            )
    return number_of_event_indicators


def parse_fmi3_model_description(
    root: ET.Element,
    path: Path,
    raw_fmi_version: str,
    platforms: tuple[str, ...],
    inspection_receipt: FmuInspectionReceipt,
) -> FmuModelDescription:
    """Build validated metadata for the represented FMI 3 primitive subset.

    :param root: Parsed ``fmiModelDescription`` root.
    :param path: Resolved FMU source path.
    :param raw_fmi_version: Exact source version declaration.
    :param platforms: Binary platform directories found during inspection.
    :param inspection_receipt: Content-bound inspection evidence.
    :return: Validated FMI 3 model-description metadata without runtime approval.
    :raises FmuArchiveError: If required metadata is incomplete or unsupported.
    """

    # Validate vocabulary and schema order before reading semantic fields.
    _validate_fmi3_element_names(root, path)
    _validate_fmi3_root_structure(root, path)
    _validate_default_experiment(root, path)
    model_name: str = read_required_attribute(
        root, "modelName", "fmiModelDescription", path
    )
    instantiation_token: str = read_required_attribute(
        root, "instantiationToken", "fmiModelDescription", path
    )
    interface_modes: tuple[FmuInterfaceMode, ...]
    model_identifiers: dict[FmuInterfaceMode, str]
    co_simulation_capabilities: FmiThreeCoSimulationCapabilities | None
    model_exchange_capabilities: FmiThreeModelExchangeCapabilities | None
    (
        interface_modes,
        model_identifiers,
        co_simulation_capabilities,
        model_exchange_capabilities,
    ) = _parse_fmi3_interfaces(root, path)

    # Build the floating-point variables directly into the shared metadata container.
    model_variables_elements: list[ET.Element] = root.findall("ModelVariables")
    if len(model_variables_elements) == 1:
        _validate_attribute_subset(
            model_variables_elements[0],
            tuple(),
            "FMI 3 ModelVariables",
            path,
        )
        variables: tuple[FmuVariableDescription, ...] = _parse_fmi3_variables(
            model_variables_elements[0], path
        )
    else:
        if len(model_variables_elements) == 0:
            raise FmuArchiveError(f"FMI 3 model description in {path} is missing ModelVariables")
        else:
            raise FmuArchiveError(f"FMI 3 ModelVariables is duplicated in {path}")

    # Validate structural references before exposing the metadata object.
    model_structure_elements: list[ET.Element] = root.findall("ModelStructure")
    if len(model_structure_elements) == 1:
        _validate_attribute_subset(
            model_structure_elements[0],
            tuple(),
            "FMI 3 ModelStructure",
            path,
        )
        number_of_event_indicators: int = _parse_fmi3_model_structure(
            model_structure_elements[0], variables, path
        )
    else:
        if len(model_structure_elements) == 0:
            raise FmuArchiveError(f"FMI 3 model description in {path} is missing ModelStructure")
        else:
            raise FmuArchiveError(f"FMI 3 ModelStructure is duplicated in {path}")
    return FmuModelDescription(
        path=path,
        fmi_version=raw_fmi_version,
        fmi_version_family=FmiVersion.FMI_3_0,
        inspection_receipt=inspection_receipt,
        model_name=model_name,
        guid=None,
        instantiation_token=instantiation_token,
        variable_naming_convention=root.attrib.get("variableNamingConvention", None),
        number_of_event_indicators=number_of_event_indicators,
        interface_modes=interface_modes,
        model_identifiers=model_identifiers,
        platforms=platforms,
        variables=variables,
        fmi_three_co_simulation_capabilities=co_simulation_capabilities,
        fmi_three_model_exchange_capabilities=model_exchange_capabilities,
    )
