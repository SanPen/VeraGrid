# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET
import zipfile

from VeraGridEngine.IO.fmu.importer.errors import FmuArchiveError, FmuModeError


class FmuVariableType(str, Enum):
    """Enumerate the FMI 2.0 scalar variable primitive types.

    :return: None.
    """

    REAL = "Real"
    INTEGER = "Integer"
    BOOLEAN = "Boolean"
    STRING = "String"
    ENUMERATION = "Enumeration"
    UNKNOWN = "Unknown"


class FmuInterfaceMode(str, Enum):
    """Enumerate the FMI 2.0 execution modes supported by VeraGrid.

    :return: None.
    """

    CO_SIMULATION = "CoSimulation"
    MODEL_EXCHANGE = "ModelExchange"


class FmuVariableDescription:
    """Store the metadata for one FMU scalar variable.

    :param name: FMI variable name.
    :param value_reference: FMI value reference.
    :param variable_type: FMI scalar primitive type.
    :param causality: FMI causality string.
    :param variability: FMI variability string.
    :param initial: FMI initial string.
    :param start: FMI start value string.
    :param derivative_index: FMI derivative index if available.
    """

    __slots__ = (
        "name",
        "value_reference",
        "variable_type",
        "causality",
        "variability",
        "initial",
        "start",
        "derivative_index",
    )

    def __init__(
        self,
        name: str,
        value_reference: int,
        variable_type: FmuVariableType,
        causality: str | None,
        variability: str | None,
        initial: str | None,
        start: str | None,
        derivative_index: int | None,
    ) -> None:
        """Store the parsed scalar-variable metadata.

        :return: None.
        """

        self.name: str = name
        self.value_reference: int = value_reference
        self.variable_type: FmuVariableType = variable_type
        self.causality: str | None = causality
        self.variability: str | None = variability
        self.initial: str | None = initial
        self.start: str | None = start
        self.derivative_index: int | None = derivative_index


class FmuModelDescription:
    """Store the execution metadata extracted from an FMU archive.

    :param path: Absolute FMU path.
    :param fmi_version: FMI version string.
    :param model_name: Model name declared in the FMU.
    :param guid: FMI GUID.
    :param variable_naming_convention: FMI naming convention.
    :param interface_modes: Supported FMI modes.
    :param model_identifiers: Mapping from FMI mode to model identifier.
    :param platforms: Available binary platforms.
    :param variables: Ordered scalar variables.
    """

    __slots__ = (
        "path",
        "fmi_version",
        "model_name",
        "guid",
        "variable_naming_convention",
        "number_of_event_indicators",
        "interface_modes",
        "model_identifiers",
        "platforms",
        "variables",
    )

    def __init__(
        self,
        path: Path,
        fmi_version: str,
        model_name: str,
        guid: str,
        variable_naming_convention: str | None,
        number_of_event_indicators: int,
        interface_modes: tuple[FmuInterfaceMode, ...],
        model_identifiers: dict[FmuInterfaceMode, str],
        platforms: tuple[str, ...],
        variables: tuple[FmuVariableDescription, ...],
    ) -> None:
        """Store the parsed FMU execution metadata.

        :return: None.
        """

        self.path: Path = path
        self.fmi_version: str = fmi_version
        self.model_name: str = model_name
        self.guid: str = guid
        self.variable_naming_convention: str | None = variable_naming_convention
        self.number_of_event_indicators: int = number_of_event_indicators
        self.interface_modes: tuple[FmuInterfaceMode, ...] = interface_modes
        self.model_identifiers: dict[FmuInterfaceMode, str] = model_identifiers
        self.platforms: tuple[str, ...] = platforms
        self.variables: tuple[FmuVariableDescription, ...] = variables

    def get_model_identifier(self, mode: FmuInterfaceMode) -> str:
        """Return the FMI `modelIdentifier` for the requested mode.

        :param mode: Requested FMI execution mode.
        :return: The FMI model identifier.
        """

        identifier: Optional[str] = self.model_identifiers.get(mode, None)
        if identifier is None:
            raise FmuModeError(f"The FMU does not support mode {mode.value}")
        else:
            return identifier

    def get_supports_co_simulation(self) -> bool:
        """Return whether the FMU declares the Co-Simulation interface.

        :return: `True` when Co-Simulation is declared.
        """

        return FmuInterfaceMode.CO_SIMULATION in self.interface_modes

    def get_supports_model_exchange(self) -> bool:
        """Return whether the FMU declares the Model Exchange interface.

        :return: `True` when Model Exchange is declared.
        """

        return FmuInterfaceMode.MODEL_EXCHANGE in self.interface_modes

    def get_variable_names(self) -> tuple[str, ...]:
        """Return the ordered scalar-variable names.

        :return: Tuple with the FMU variable names.
        """

        variable_names: list[str] = list()
        variable: FmuVariableDescription
        for variable in self.variables:
            variable_names.append(variable.name)
        return tuple(variable_names)

    def get_variable(self, name: str) -> FmuVariableDescription:
        """Return the scalar-variable metadata for the requested name.

        :param name: Requested FMU variable name.
        :return: Matching variable metadata.
        """

        result: Optional[FmuVariableDescription] = None
        candidate: FmuVariableDescription
        for candidate in self.variables:
            if candidate.name == name:
                result = candidate
            else:
                pass

        if result is None:
            raise KeyError(name)
        else:
            return result

    def get_state_variables(self) -> tuple[FmuVariableDescription, ...]:
        """Return the FMI variables representing continuous states.

        :return: Tuple with the continuous-state variables.
        """

        state_variables: list[FmuVariableDescription] = list()
        variable: FmuVariableDescription
        for variable in self.variables:
            if variable.causality == "output" and variable.variability == "continuous":
                state_variables.append(variable)
            else:
                pass
        return tuple(state_variables)

    def get_derivative_variables(self) -> tuple[FmuVariableDescription, ...]:
        """Return the FMI variables representing continuous derivatives.

        :return: Tuple with the derivative variables.
        """

        derivative_variables: list[FmuVariableDescription] = list()
        variable: FmuVariableDescription
        for variable in self.variables:
            if variable.derivative_index is not None:
                derivative_variables.append(variable)
            else:
                pass
        return tuple(derivative_variables)

    def resolve_mode(self, preferred_mode: FmuInterfaceMode | None = None) -> FmuInterfaceMode:
        """Choose the effective FMI mode to execute.

        :param preferred_mode: Optional preferred FMI mode.
        :return: Effective FMI mode to execute.
        """

        if preferred_mode is not None:
            if preferred_mode in self.interface_modes:
                return preferred_mode
            else:
                raise FmuModeError(f"The FMU does not support preferred mode {preferred_mode.value}")
        else:
            if len(self.interface_modes) == 1:
                return self.interface_modes[0]
            else:
                if FmuInterfaceMode.CO_SIMULATION in self.interface_modes:
                    return FmuInterfaceMode.CO_SIMULATION
                else:
                    if FmuInterfaceMode.MODEL_EXCHANGE in self.interface_modes:
                        return FmuInterfaceMode.MODEL_EXCHANGE
                    else:
                        raise FmuModeError("The FMU does not declare Co-Simulation or Model Exchange")


def _read_archive_xml(path: Path) -> tuple[bytes, tuple[str, ...]]:
    """Read the FMU XML bytes and available binary platforms.

    :param path: FMU archive path or extracted directory.
    :return: Tuple with XML bytes and supported platforms.
    """

    if path.is_dir():
        xml_path: Path = path / "modelDescription.xml"
        if xml_path.exists():
            binaries_dir: Path = path / "binaries"
            platforms_list: list[str] = list()
            if binaries_dir.exists():
                entry: Path
                for entry in binaries_dir.iterdir():
                    platforms_list.append(entry.name)
            else:
                pass
            return xml_path.read_bytes(), tuple(sorted(platforms_list))
        else:
            raise FmuArchiveError(f"Directory {path} does not contain modelDescription.xml")
    else:
        if path.exists():
            try:
                with zipfile.ZipFile(path) as archive:
                    xml_bytes: bytes = archive.read("modelDescription.xml")
                    platform_names: set[str] = set()
                    archive_name: str
                    for archive_name in archive.namelist():
                        if archive_name.startswith("binaries/"):
                            parts: list[str] = archive_name.split("/")
                            if len(parts) > 2:
                                platform_names.add(parts[1])
                            else:
                                pass
                        else:
                            pass
                    return xml_bytes, tuple(sorted(platform_names))
            except (KeyError, OSError, zipfile.BadZipFile) as exc:
                raise FmuArchiveError(f"Could not read modelDescription.xml from {path}") from exc
        else:
            raise FmuArchiveError(f"FMU file not found: {path}")


def _parse_interface_modes(root: ET.Element) -> tuple[tuple[FmuInterfaceMode, ...], dict[FmuInterfaceMode, str]]:
    """Parse the supported FMI interface modes from the XML root.

    :param root: XML root element.
    :return: Supported modes and their model identifiers.
    """

    modes: list[FmuInterfaceMode] = list()
    identifiers: dict[FmuInterfaceMode, str] = dict()

    co_simulation_node: Optional[ET.Element] = root.find("CoSimulation")
    if co_simulation_node is not None:
        modes.append(FmuInterfaceMode.CO_SIMULATION)
        identifiers[FmuInterfaceMode.CO_SIMULATION] = co_simulation_node.attrib.get("modelIdentifier", "")
    else:
        pass

    model_exchange_node: Optional[ET.Element] = root.find("ModelExchange")
    if model_exchange_node is not None:
        modes.append(FmuInterfaceMode.MODEL_EXCHANGE)
        identifiers[FmuInterfaceMode.MODEL_EXCHANGE] = model_exchange_node.attrib.get("modelIdentifier", "")
    else:
        pass

    return tuple(modes), identifiers


def _parse_variable_type(variable_node: ET.Element) -> tuple[FmuVariableType, ET.Element | None]:
    """Parse the primitive FMI type for one scalar variable.

    :param variable_node: ScalarVariable XML node.
    :return: Primitive FMI type and matching child node.
    """

    child_node: ET.Element
    for child_node in variable_node:
        try:
            return FmuVariableType(child_node.tag), child_node
        except ValueError:
            pass
    return FmuVariableType.UNKNOWN, None


def _parse_variables(model_variables_node: ET.Element | None) -> tuple[FmuVariableDescription, ...]:
    """Parse the ordered scalar variables declared in the FMU.

    :param model_variables_node: XML `<ModelVariables>` node.
    :return: Ordered scalar-variable descriptions.
    """

    variables: list[FmuVariableDescription] = list()
    if model_variables_node is None:
        return tuple()
    else:
        scalar_variable_node: ET.Element
        for scalar_variable_node in model_variables_node.findall("ScalarVariable"):
            variable_type: FmuVariableType
            type_node: ET.Element | None
            variable_type, type_node = _parse_variable_type(scalar_variable_node)
            derivative_index: int | None = None
            start: str | None = None
            if type_node is not None:
                derivative_raw: Optional[str] = type_node.attrib.get("derivative", None)
                if derivative_raw is not None:
                    derivative_index = int(derivative_raw)
                else:
                    derivative_index = None
                start = type_node.attrib.get("start", None)
            else:
                pass

            variables.append(
                FmuVariableDescription(
                    name=scalar_variable_node.attrib["name"],
                    value_reference=int(scalar_variable_node.attrib.get("valueReference", "0")),
                    variable_type=variable_type,
                    causality=scalar_variable_node.attrib.get("causality", None),
                    variability=scalar_variable_node.attrib.get("variability", None),
                    initial=scalar_variable_node.attrib.get("initial", None),
                    start=start,
                    derivative_index=derivative_index,
                )
            )
        return tuple(variables)


def read_fmu_model_description(path: str | Path) -> FmuModelDescription:
    """Parse the FMU archive and build the runtime metadata object.

    :param path: FMU archive path or extracted directory.
    :return: Parsed FMU metadata.
    """

    normalized_path: Path = Path(path).expanduser().resolve()

    # First the archive is inspected to recover the XML and the binary platforms.
    xml_bytes: bytes
    platforms: tuple[str, ...]
    xml_bytes, platforms = _read_archive_xml(normalized_path)

    # Then the XML is parsed into an element tree to extract each metadata section.
    try:
        root: ET.Element = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise FmuArchiveError(f"Invalid modelDescription.xml in {normalized_path}") from exc

    interface_modes: tuple[FmuInterfaceMode, ...]
    model_identifiers: dict[FmuInterfaceMode, str]
    interface_modes, model_identifiers = _parse_interface_modes(root)
    variables: tuple[FmuVariableDescription, ...] = _parse_variables(root.find("ModelVariables"))

    # Finally the immutable metadata container is assembled for the callers.
    return FmuModelDescription(
        path=normalized_path,
        fmi_version=root.attrib.get("fmiVersion", ""),
        model_name=root.attrib.get("modelName", normalized_path.stem),
        guid=root.attrib.get("guid", ""),
        variable_naming_convention=root.attrib.get("variableNamingConvention", None),
        number_of_event_indicators=int(root.attrib.get("numberOfEventIndicators", "0")),
        interface_modes=interface_modes,
        model_identifiers=model_identifiers,
        platforms=platforms,
        variables=variables,
    )


def list_fmu_variable_names(path: str | Path) -> tuple[str, ...]:
    """Return the ordered scalar-variable names declared by the FMU.

    :param path: FMU archive path or extracted directory.
    :return: Tuple with the variable names.
    """

    metadata: FmuModelDescription = read_fmu_model_description(path)
    return metadata.get_variable_names()


def choose_fmu_mode(path: str | Path, preferred_mode: FmuInterfaceMode | None = None) -> FmuInterfaceMode:
    """Choose the FMI mode to use for the FMU runtime.

    :param path: FMU archive path or extracted directory.
    :param preferred_mode: Optional preferred FMI mode.
    :return: Effective FMI execution mode.
    """

    metadata: FmuModelDescription = read_fmu_model_description(path)
    return metadata.resolve_mode(preferred_mode)
