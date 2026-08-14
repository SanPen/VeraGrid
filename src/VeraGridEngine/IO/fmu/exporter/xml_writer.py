# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from VeraGridEngine.IO.fmu.exporter.export_ir import ExportModel


def emit_model_description(export_model: ExportModel) -> str:
    root = Element(
        "fmiModelDescription",
        {
            "fmiVersion": "2.0",
            "modelName": export_model.model_name,
            "guid": export_model.guid,
            "generationTool": "veragrid_fmu_export",
            "variableNamingConvention": "flat",
            "numberOfEventIndicators": "0",
        },
    )

    SubElement(
        root,
        "CoSimulation",
        {
            "modelIdentifier": export_model.model_identifier,
            "canHandleVariableCommunicationStepSize": "true",
            "canInterpolateInputs": "false",
            "maxOutputDerivativeOrder": "0",
            "canGetAndSetFMUstate": "false",
            "canSerializeFMUstate": "false",
            "providesDirectionalDerivative": "false",
        },
    )

    SubElement(
        root,
        "DefaultExperiment",
        {
            "startTime": "0.0",
            "stepSize": format(export_model.fixed_step, ".17g"),
        },
    )

    model_variables = SubElement(root, "ModelVariables")
    exposed = sorted(export_model.exposed_variables(), key=lambda variable: variable.value_reference or -1)
    for variable in exposed:
        attrs = {
            "name": variable.name,
            "valueReference": str(variable.value_reference),
            "causality": variable.causality,
            "variability": variable.variability,
        }
        if variable.initial is not None:
            attrs["initial"] = variable.initial
        scalar = SubElement(model_variables, "ScalarVariable", attrs)
        real_attrs: dict[str, str] = {}
        if variable.start is not None:
            real_attrs["start"] = format(variable.start, ".17g")
        SubElement(scalar, "Real", real_attrs)

    structure = SubElement(root, "ModelStructure")
    outputs_element = SubElement(structure, "Outputs")
    initial_unknown_indices: list[int] = []
    for index, variable in enumerate(exposed, start=1):
        if variable.causality == "output":
            SubElement(outputs_element, "Unknown", {"index": str(index)})
        if variable.causality == "output" and variable.initial in {"calculated", "approx"}:
            initial_unknown_indices.append(index)

    if initial_unknown_indices:
        initial_unknowns = SubElement(structure, "InitialUnknowns")
        for index in initial_unknown_indices:
            SubElement(initial_unknowns, "Unknown", {"index": str(index)})

    xml_bytes = tostring(root, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    fromstring(pretty)
    return pretty


def write_model_description(export_model: ExportModel, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(emit_model_description(export_model), encoding="utf-8")
    return output_path
