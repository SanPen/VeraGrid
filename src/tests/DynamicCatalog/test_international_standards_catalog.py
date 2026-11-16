# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Contract tests for the international-standard RMS model catalog."""

from __future__ import annotations

import keyword

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.template_catalogue import (
    InternationalStandardTemplateDescriptor,
    load_international_standard_template,
)
from VeraGrid.Gui.DynamicModelEditor.Editor.DynamicLibrary.dynamic_editor_library import (
    get_dynamic_library_international_standard_descriptors,
)
from VeraGridEngine.Templates.Rms import InternationalStandardModel
from VeraGridEngine.Templates.Rms import build_international_standard_template
def test_psse_mins_trip_relays_have_distinct_native_templates() -> None:
    """Materialize source-specific FRQTPAT and VTGTPAT relay templates.

    :return: None.
    """
    frequency: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.FRQTPAT, VarFactory(), 'FRQTPAT_test',
    )
    voltage: RmsModelTemplate = build_international_standard_template(
        InternationalStandardModel.VTGTPAT, VarFactory(), 'VTGTPAT_test',
    )

    assert frequency.name == 'FRQTPAT_test'
    assert voltage.name == 'VTGTPAT_test'
    assert frequency.block.in_vars[0].name.startswith('FHz_')
    assert voltage.block.in_vars[0].name.startswith('UPu_')
    assert any(variable.name.startswith('FL_') for variable in frequency.block.event_dict)
    assert any(variable.name.startswith('VL_') for variable in voltage.block.event_dict)


def test_international_standard_descriptor_materializes_rms_template() -> None:
    """Ensure a catalog leaf delegates to the existing standard-model builder.

    :return: None.
    """
    descriptor: InternationalStandardTemplateDescriptor = list(
        get_dynamic_library_international_standard_descriptors()
    )[0]
    template: RmsModelTemplate = load_international_standard_template(
        descriptor=descriptor,
        var_factory=VarFactory(),
    )

    assert isinstance(template, RmsModelTemplate)
    assert template.block is not None
    assert template.name == descriptor.display_label


def test_imported_model_interfaces_and_symbol_names_are_editor_safe() -> None:
    """Keep imported model ports visible and their equation source parseable.

    :return: None.
    """
    expected_interfaces: tuple[tuple[InternationalStandardModel, int, int], ...] = (
        (InternationalStandardModel.IEEEG1, 3, 3),
        (InternationalStandardModel.IEEEG2, 3, 1),
        (InternationalStandardModel.GOVSTEAMEU, 6, 1),
        (InternationalStandardModel.AC1C, 6, 3),
        (InternationalStandardModel.AC8B, 6, 3),
        (InternationalStandardModel.AC7B, 7, 3),
        (InternationalStandardModel.AC7C, 10, 6),
        (InternationalStandardModel.AC8C, 10, 5),
        (InternationalStandardModel.ST4C, 10, 5),
        (InternationalStandardModel.ST6C, 10, 5),
        (InternationalStandardModel.DC4C, 9, 3),
        (InternationalStandardModel.ST5B, 7, 6),
        (InternationalStandardModel.ST5C, 7, 6),
        (InternationalStandardModel.IVOST, 1, 1),
        (InternationalStandardModel.IVOGO, 2, 2),
        (InternationalStandardModel.DEGOV, 3, 3),
        (InternationalStandardModel.DEGOV1, 3, 3),
        (InternationalStandardModel.DEGOV1D, 3, 3),
        (InternationalStandardModel.BESSCBCURRENTSOURCENOPLANTCONTROL, 6, 2),
        (InternationalStandardModel.WPP4BCURRENTSOURCE2020, 6, 2),
        (InternationalStandardModel.MAXEX2, 1, 1),
        (InternationalStandardModel.OEL2C, 1, 1),
        (InternationalStandardModel.SCL1C, 5, 4),
        (InternationalStandardModel.SCL2C, 6, 2),
        (InternationalStandardModel.UEL2C, 6, 1),
        (InternationalStandardModel.AC6A, 6, 3),
        (InternationalStandardModel.ESAC6A, 6, 3),
        (InternationalStandardModel.AC6C, 7, 3),
        (InternationalStandardModel.AC6C2, 7, 3),
        (InternationalStandardModel.PSS2B, 3, 1),
        (InternationalStandardModel.PSS2C, 3, 1),
    )
    descriptors: list[InternationalStandardTemplateDescriptor] = list(
        get_dynamic_library_international_standard_descriptors()
    )
    model: InternationalStandardModel
    expected_input_count: int
    expected_output_count: int

    for model, expected_input_count, expected_output_count in expected_interfaces:
        descriptor: InternationalStandardTemplateDescriptor | None = None
        candidate_descriptor: InternationalStandardTemplateDescriptor
        for candidate_descriptor in descriptors:
            if candidate_descriptor.model == model:
                descriptor = candidate_descriptor
            else:
                pass

        assert descriptor is not None
        var_factory: VarFactory = VarFactory()
        template: RmsModelTemplate = load_international_standard_template(
            descriptor=descriptor,
            var_factory=var_factory,
        )
        assert len(template.block.in_vars) == expected_input_count
        assert len(template.block.out_vars) == expected_output_count

        # The properties editor emits these names directly into Python source.
        variable_names: list[str] = list(
            variable.name for variable in var_factory.get_vars_dict().values()
        )
        variable_names.extend(list(
            variable.name for variable in var_factory.get_diff_var_dict().values()
        ))
        assert len(variable_names) > 0
        assert all(variable_name.isidentifier() for variable_name in variable_names)
        assert all(not keyword.iskeyword(variable_name) for variable_name in variable_names)


def test_every_international_standard_exposes_inputs_and_outputs() -> None:
    """Prevent generated standard models from losing their public connectors.

    :return: None.
    """
    descriptors: list[InternationalStandardTemplateDescriptor] = list(
        get_dynamic_library_international_standard_descriptors()
    )
    descriptor: InternationalStandardTemplateDescriptor

    for descriptor in descriptors:
        template: RmsModelTemplate = load_international_standard_template(
            descriptor=descriptor,
            var_factory=VarFactory(),
        )

        assert template.block is not None
        assert len(template.block.in_vars) > 0, descriptor.display_label
        assert len(template.block.out_vars) > 0, descriptor.display_label
