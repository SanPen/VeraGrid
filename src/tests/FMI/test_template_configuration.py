from __future__ import annotations

from pathlib import Path

from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.enumerations import (
    DeviceType,
    FmuTemplateDomain,
    FmuTemplateMode,
    ParamPowerFlowReferenceType,
    VarPowerFlowReferenceType,
)
from VeraGridEngine.IO.fmu.importer.device_config import load_fmu_cs_device_config
from VeraGridEngine.IO.fmu.importer.template_api import configure_fmu_template


def _artifact_path() -> Path:
    """
    Return the path to the FMU artifact used by the template-configuration tests.

    :return: FMU artifact path.
    """

    return Path(__file__).resolve().parents[1] / "data" / "fmi" / "artifacts" / "FrequencyLoadPilot.fmu"


def test_configure_fmu_template_builds_visual_ports_and_auto_bindings() -> None:
    """
    Configuring one FMU template must expose the FMU interface as editor ports and serialized runtime bindings.

    :return: None.
    """

    template = FmuTemplate(name="")
    var_factory = VarFactory(name="RmsFmuTemplateFactory")

    configured_template = configure_fmu_template(
        template=template,
        var_factory=var_factory,
        fmu_path=_artifact_path(),
        device_tpe=DeviceType.LoadDevice,
        domain=FmuTemplateDomain.RMS,
        mode=FmuTemplateMode.CO_SIMULATION,
        template_name="",
    )

    input_names = [var.name for var in configured_template.block.in_vars]
    output_names = [var.name for var in configured_template.block.out_vars]
    parameter_names = [var.name for var in configured_template.block.parameters.keys()]

    assert "Va_" in input_names
    assert "Vm_" in input_names
    assert "P" in output_names
    assert "Q" in output_names
    assert "y_frequency_measure" in output_names
    assert "Pl0" in parameter_names
    assert "Ql0" in parameter_names
    assert configured_template.block.api_obj_mapping[ParamPowerFlowReferenceType.Pl0].name == "Pl0"
    assert configured_template.block.api_obj_mapping[ParamPowerFlowReferenceType.Ql0].name == "Ql0"

    serialized_record = load_fmu_cs_device_config(configured_template.serialized_config)
    assert serialized_record is not None
    assert {binding.reference for binding in serialized_record.input_bindings} == {
        VarPowerFlowReferenceType.Va,
        VarPowerFlowReferenceType.Vm,
    }
    assert {binding.reference for binding in serialized_record.output_bindings} == {
        VarPowerFlowReferenceType.P,
        VarPowerFlowReferenceType.Q,
    }
