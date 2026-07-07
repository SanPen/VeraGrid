from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Utils.Symbolic.block import Block, Const, Var
from VeraGridEngine.enumerations import DeviceType, FmuTemplateDomain, FmuTemplateMode, VarPowerFlowRefferenceType


def _build_native_template() -> RmsModelTemplate:
    """
    Build one minimal native RMS template for assignment tests.

    :return: RMS template.
    """

    template = RmsModelTemplate(name="native-rms")
    template.tpe = DeviceType.LoadDevice
    template.block = Block(out_vars=[Var("p")])
    return template


def _build_emt_native_template() -> EmtModelTemplate:
    """
    Build one minimal native EMT template for assignment tests.

    :return: EMT template.
    """

    template = EmtModelTemplate(name="native-emt")
    template.tpe = DeviceType.LoadDevice
    template.block = Block(out_vars=[Var("i")])
    return template


def _build_emt_fmu_template() -> FmuTemplate:
    """
    Build one minimal EMT FMU template that keeps ``None`` in its external mapping.

    This reproduces the real GUI assignment path that failed when ``duplicate_block``
    tried to clone the template shell.

    :return: EMT FMU template.
    """

    current_var = Var("i_a")
    block = Block(
        algebraic_vars=[current_var],
        algebraic_eqs=[current_var - Const(0.0)],
        out_vars=[current_var],
        external_mapping={VarPowerFlowRefferenceType.i_A: None},
    )

    template = FmuTemplate(name="emt-fmu")
    template.tpe = DeviceType.LoadDevice
    template.domain = FmuTemplateDomain.EMT
    template.mode = FmuTemplateMode.CO_SIMULATION
    template.block = block
    template.serialized_config = '{"domain": "emt", "fmu_path": "demo.fmu", "version": 1}'
    return template


def _build_rms_fmu_template() -> FmuTemplate:
    """
    Build one minimal RMS FMU template for exclusivity tests.

    :return: RMS FMU template.
    """

    power_var = Var("p")
    block = Block(
        algebraic_vars=[power_var],
        algebraic_eqs=[power_var - Const(0.0)],
        out_vars=[power_var],
    )

    template = FmuTemplate(name="rms-fmu")
    template.tpe = DeviceType.LoadDevice
    template.domain = FmuTemplateDomain.RMS
    template.mode = FmuTemplateMode.CO_SIMULATION
    template.block = block
    template.serialized_config = '{"domain": "rms", "fmu_path": "demo.fmu", "version": 1}'
    return template


def _build_load() -> Load:
    """
    Build one load with RMS and EMT variable factories configured.

    :return: Load device.
    """

    load = Load(name="Load under test")
    load.set_var_factory(VarFactory(name="TestRmsFactory"))

    return load


def test_assigning_emt_fmu_template_accepts_none_external_mapping() -> None:
    """
    Assigning one EMT FMU template must clone the shell block even when some external mappings are ``None``.

    :return: None.
    """

    load = _build_load()
    template = _build_emt_fmu_template()

    load.emt_fmu_template = template

    assert load.emt_fmu_template == template
    assert load.emt_model is not template.block
    assert VarPowerFlowRefferenceType.i_A in load.emt_model.external_mapping
    assert load.emt_model.external_mapping[VarPowerFlowRefferenceType.i_A] is None


def test_rms_template_and_rms_fmu_template_are_mutually_exclusive() -> None:
    """
    RMS native templates and RMS FMU templates cannot stay assigned at the same time.

    :return: None.
    """

    load = _build_load()
    native_template = _build_native_template()
    fmu_template = _build_rms_fmu_template()

    load.rms_template = native_template
    assert load.rms_template == native_template
    assert load.rms_fmu_template is None

    load.rms_fmu_template = fmu_template
    assert load.rms_fmu_template == fmu_template
    assert load.rms_template is None


def test_emt_template_and_emt_fmu_template_are_mutually_exclusive() -> None:
    """
    EMT native templates and EMT FMU templates cannot stay assigned at the same time.

    :return: None.
    """

    load = _build_load()
    native_template = _build_emt_native_template()
    fmu_template = _build_emt_fmu_template()

    load.emt_template = native_template
    assert load.emt_template == native_template
    assert load.emt_fmu_template is None

    load.emt_fmu_template = fmu_template
    assert load.emt_fmu_template == fmu_template
    assert load.emt_template is None
