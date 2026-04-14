# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from .export_ir import ExportModel, VariableCategory


def emit_model_description(export_model: ExportModel) -> str:
    model_variables = list(export_model.xml_variables())
    xml_index_by_uid = {variable.uid: index for index, variable in enumerate(model_variables, start=1)}

    root = Element(
        "fmiModelDescription",
        {
            "fmiVersion": "2.0",
            "modelName": export_model.model_name,
            "guid": export_model.guid,
            "generationTool": "veragrid_fmu_me_export",
            "variableNamingConvention": "flat",
            "numberOfEventIndicators": str(export_model.counts.get("event_indicators", 0)),
        },
    )

    SubElement(
        root,
        "ModelExchange",
        {
            "modelIdentifier": export_model.model_identifier,
            "completedIntegratorStepNotNeeded": "false" if export_model.needs_completed_integrator_step() else "true",
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
            "stepSize": format(export_model.default_step_size, ".17g"),
            "tolerance": format(export_model.relative_tolerance, ".17g"),
        },
    )

    model_variables_element = SubElement(root, "ModelVariables")
    for variable in model_variables:
        attrs = {
            "name": variable.name,
            "valueReference": str(variable.value_reference),
            "causality": variable.causality,
            "variability": variable.variability,
        }
        if variable.initial is not None:
            attrs["initial"] = variable.initial
        scalar = SubElement(model_variables_element, "ScalarVariable", attrs)
        real_attrs: dict[str, str] = {}
        if variable.start is not None:
            real_attrs["start"] = format(variable.start, ".17g")
        if variable.nominal is not None:
            real_attrs["nominal"] = format(variable.nominal, ".17g")
        if variable.category == VariableCategory.DERIVATIVE and variable.derivative_of_uid is not None:
            real_attrs["derivative"] = str(xml_index_by_uid[variable.derivative_of_uid])
        SubElement(scalar, "Real", real_attrs)

    structure = SubElement(root, "ModelStructure")

    outputs = export_model.output_variables()
    if outputs:
        outputs_element = SubElement(structure, "Outputs")
        for variable in outputs:
            SubElement(outputs_element, "Unknown", {"index": str(xml_index_by_uid[variable.uid])})

    derivatives = export_model.derivative_variables()
    if derivatives:
        derivatives_element = SubElement(structure, "Derivatives")
        for variable in derivatives:
            SubElement(derivatives_element, "Unknown", {"index": str(xml_index_by_uid[variable.uid])})

    initial_unknowns = export_model.initial_unknown_variables()
    if initial_unknowns:
        initial_unknowns_element = SubElement(structure, "InitialUnknowns")
        for variable in initial_unknowns:
            SubElement(initial_unknowns_element, "Unknown", {"index": str(xml_index_by_uid[variable.uid])})

    xml_bytes = tostring(root, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    fromstring(pretty)
    return pretty


def write_model_description(export_model: ExportModel, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(emit_model_description(export_model), encoding="utf-8")
    return output_path
