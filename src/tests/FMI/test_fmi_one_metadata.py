# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Tests for the metadata-only FMI 1 model-description parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from VeraGridEngine.IO.fmu.importer.bindings import FmuImportConfig
from VeraGridEngine.IO.fmu.importer.errors import FmuArchiveError, FmuModeError
from VeraGridEngine.IO.fmu.importer.model_description import (
    FmuInterfaceMode,
    FmuModelDescription,
    read_fmu_model_description,
)
from VeraGridEngine.enumerations import FmiVersion


def _write_fmi_one_document(
    directory: Path,
    root_attributes: str,
    implementation_xml: str = "",
    variables_xml: str = "",
) -> Path:
    """Write one extracted FMI 1 metadata fixture.

    :param directory: Directory representing the extracted FMU.
    :param root_attributes: Root attributes other than ``fmiVersion``.
    :param implementation_xml: Optional FMI 1 Implementation element.
    :param variables_xml: Ordered scalar-variable declarations.
    :return: Extracted FMU directory containing modelDescription.xml.
    """

    directory.mkdir()
    xml_text: str = (
        f'<fmiModelDescription fmiVersion="1.0" {root_attributes}>'
        f"<ModelVariables>{variables_xml}</ModelVariables>"
        f"{implementation_xml}"
        "</fmiModelDescription>"
    )
    (directory / "modelDescription.xml").write_text(xml_text, encoding="utf-8")
    return directory


def test_fmi_one_model_exchange_metadata_is_preserved(tmp_path: Path) -> None:
    """Verify FMI 1 without Implementation is Model Exchange metadata.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :return: None.
    """

    source: Path = _write_fmi_one_document(
        tmp_path / "model-exchange",
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfContinuousStates="1" '
            'numberOfEventIndicators="2"'
        ),
        variables_xml=(
            '<ScalarVariable name="input" valueReference="1" causality="input">'
            '<Real start="1.0"/></ScalarVariable>'
            '<ScalarVariable name="output" valueReference="2" causality="output">'
            '<Real/><DirectDependency><Name>input</Name></DirectDependency>'
            "</ScalarVariable>"
            '<ScalarVariable name="internal" valueReference="3"><Integer/></ScalarVariable>'
        ),
    )
    metadata: FmuModelDescription = read_fmu_model_description(source)

    assert metadata.fmi_version_family == FmiVersion.FMI_1_0
    assert metadata.interface_modes == (FmuInterfaceMode.MODEL_EXCHANGE,)
    assert metadata.get_model_identifier(FmuInterfaceMode.MODEL_EXCHANGE) == "legacy_model"
    assert metadata.number_of_event_indicators == 2
    assert metadata.get_variable_names() == ("input", "output", "internal")
    assert metadata.variables[2].causality == "internal"
    assert metadata.variables[2].variability == "continuous"

    config: FmuImportConfig = FmuImportConfig(fmu_path=source)
    with pytest.raises(FmuModeError, match="execution is not supported"):
        config.resolve_execution_mode(metadata)


@pytest.mark.parametrize(
    "implementation_xml",
    (
        (
            "<Implementation><CoSimulation_StandAlone><Capabilities/>"
            "</CoSimulation_StandAlone></Implementation>"
        ),
        (
            "<Implementation><CoSimulation_Tool><Capabilities/>"
            '<Model entryPoint="tool" type="application"/>'
            "</CoSimulation_Tool></Implementation>"
        ),
    ),
)
def test_fmi_one_co_simulation_forms_are_metadata_only(
    tmp_path: Path,
    implementation_xml: str,
) -> None:
    """Verify both FMI 1 Co-Simulation forms are identified as metadata.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :param implementation_xml: Valid FMI 1 Co-Simulation declaration.
    :return: None.
    """

    source: Path = _write_fmi_one_document(
        tmp_path / "co-simulation",
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfContinuousStates="0" '
            'numberOfEventIndicators="0"'
        ),
        implementation_xml=implementation_xml,
    )
    metadata: FmuModelDescription = read_fmu_model_description(source)

    assert metadata.interface_modes == (FmuInterfaceMode.CO_SIMULATION,)
    assert metadata.get_model_identifier(FmuInterfaceMode.CO_SIMULATION) == "legacy_model"


@pytest.mark.parametrize(
    "root_attributes",
    (
        (
            'modelIdentifier="legacy_model" guid="legacy-guid" '
            'numberOfContinuousStates="0" numberOfEventIndicators="0"'
        ),
        (
            'modelName="LegacyModel" guid="legacy-guid" '
            'numberOfContinuousStates="0" numberOfEventIndicators="0"'
        ),
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'numberOfContinuousStates="0" numberOfEventIndicators="0"'
        ),
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfEventIndicators="0"'
        ),
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfContinuousStates="0"'
        ),
    ),
)
def test_fmi_one_required_root_attributes_fail_closed(
    tmp_path: Path,
    root_attributes: str,
) -> None:
    """Verify every required FMI 1 root field is present.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :param root_attributes: Root declaration missing one required field.
    :return: None.
    """

    source: Path = _write_fmi_one_document(
        tmp_path / "required-root",
        root_attributes,
    )

    with pytest.raises(FmuArchiveError, match="missing required|missing required attribute"):
        read_fmu_model_description(source)


@pytest.mark.parametrize(
    ("attribute_name", "attribute_value"),
    (
        ("numberOfContinuousStates", "-1"),
        ("numberOfContinuousStates", "4294967296"),
        ("numberOfEventIndicators", "1.0"),
    ),
)
def test_fmi_one_counts_require_unsigned_32_bit_integers(
    tmp_path: Path,
    attribute_name: str,
    attribute_value: str,
) -> None:
    """Verify required FMI 1 counts use the XSD unsigned integer domain.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :param attribute_name: Count attribute under test.
    :param attribute_value: Invalid count value.
    :return: None.
    """

    continuous_states: str = "0"
    event_indicators: str = "0"
    if attribute_name == "numberOfContinuousStates":
        continuous_states = attribute_value
    else:
        event_indicators = attribute_value
    source: Path = _write_fmi_one_document(
        tmp_path / "count",
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            f'guid="legacy-guid" numberOfContinuousStates="{continuous_states}" '
            f'numberOfEventIndicators="{event_indicators}"'
        ),
    )

    with pytest.raises(FmuArchiveError, match="unsigned 32-bit"):
        read_fmu_model_description(source)


@pytest.mark.parametrize(
    "implementation_xml",
    (
        "<Implementation/>",
        "<Implementation><Unknown/></Implementation>",
        "<Implementation><CoSimulation_StandAlone/></Implementation>",
        (
            "<Implementation><CoSimulation_Tool><Capabilities/>"
            "</CoSimulation_Tool></Implementation>"
        ),
        (
            "<Implementation><CoSimulation_Tool><Capabilities/><Model/>"
            "</CoSimulation_Tool></Implementation>"
        ),
        (
            "<Implementation><CoSimulation_StandAlone/><CoSimulation_Tool/>"
            "</Implementation>"
        ),
        (
            "<Implementation><CoSimulation_StandAlone/></Implementation>"
            "<Implementation><CoSimulation_Tool/></Implementation>"
        ),
    ),
)
def test_fmi_one_implementation_must_identify_one_interface(
    tmp_path: Path,
    implementation_xml: str,
) -> None:
    """Verify malformed FMI 1 Implementation metadata is never ambiguous.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :param implementation_xml: Missing, unknown, or duplicated interface form.
    :return: None.
    """

    source: Path = _write_fmi_one_document(
        tmp_path / "implementation",
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfContinuousStates="0" '
            'numberOfEventIndicators="0"'
        ),
        implementation_xml=implementation_xml,
    )

    with pytest.raises(FmuArchiveError, match="Implementation|interface|CoSimulation"):
        read_fmu_model_description(source)


def test_fmi_one_rejects_fmi_two_derivative_metadata(tmp_path: Path) -> None:
    """Verify FMI 2 derivative metadata cannot leak into an FMI 1 variable.

    :param tmp_path: Isolated fixture directory provided by pytest.
    :return: None.
    """

    source: Path = _write_fmi_one_document(
        tmp_path / "derivative",
        (
            'modelName="LegacyModel" modelIdentifier="legacy_model" '
            'guid="legacy-guid" numberOfContinuousStates="1" '
            'numberOfEventIndicators="0"'
        ),
        variables_xml=(
            '<ScalarVariable name="state" valueReference="1">'
            '<Real derivative="1"/></ScalarVariable>'
        ),
    )

    with pytest.raises(FmuArchiveError, match="outside FMI 2"):
        read_fmu_model_description(source)
