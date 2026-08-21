# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Standalone grid-following VSC models for RMS HVDC studies."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.vsc_gfl import VscGflBuild
from VeraGridEngine.Utils.Symbolic.block import Block, Var
from VeraGridEngine.enumerations import ConverterControlType, VarPowerFlowReferenceType


def _find_event_variable(block: Block, variable_name: str) -> tuple[Block, Var] | None:
    """Find an event parameter and its owning block recursively."""
    for variable in block.event_dict:
        if variable.name == variable_name:
            return block, variable
    for child in block.children:
        result = _find_event_variable(child, variable_name)
        if result is not None:
            return result
    return None


def _set_event_value(block: Block, variable_name: str, value: float, vf: VarFactory) -> None:
    """Set one existing event parameter to a numeric default."""
    result = _find_event_variable(block=block, variable_name=variable_name)
    if result is None:
        raise KeyError(f"The VSC GFL model has no event parameter named '{variable_name}'")
    owner, variable = result
    owner.event_dict[variable] = vf.add_const(value)


def build_hvdc_vsc_gfl_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC",
        control1: ConverterControlType = ConverterControlType.Vm_dc,
        control2: ConverterControlType = ConverterControlType.Qac,
        cdc: float = 0.40,
) -> RmsModelTemplate:
    """Build a complete controlled VSC with an RMS DC-link capacitor.

    The model belongs directly to a :class:`VSC` device. Its AC terminal uses
    ``Vm/Va`` and its DC terminal uses ``Vdc``. A physical coupling transformer
    must use the ordinary transformer RMS template rather than hosting converter
    controls.

    :param vfactory: Variable factory used to construct the symbolic model.
    :param name: Catalog and block display name.
    :param control1: Active-axis control mode (``Vm_dc``, ``Pdc``, or ``Pac``).
    :param control2: Reactive-axis control mode (``Qac`` or ``Vm_ac``).
    :param cdc: DC-link capacitance in p.u.
    :return: Complete reusable RMS VSC template.
    """
    template = VscGflBuild(
        vfactory=vfactory,
        name=name,
        control1=control1,
        control2=control2,
    )
    template.name = name
    template.block.name = name

    vdc = template.block.external_mapping[VarPowerFlowReferenceType.Vdc]
    dvdc_dt = vfactory.add_diff_var(f"dVdc_dt_{name}", base_var=vdc)
    cdc_parameter = vfactory.add_var(f"Cdc_{name}")

    # Pf_dc + Pt_ac - Ploss - Cdc*Vdc*dVdc/dt = 0.
    template.block.algebraic_eqs[0] -= cdc_parameter * vdc * dvdc_dt
    template.block.diff_vars.append(dvdc_dt)
    template.block.diff_init_eqs[dvdc_dt] = vfactory.add_const(0.0)
    template.block.event_dict[cdc_parameter] = vfactory.add_const(float(cdc))

    # Defaults validated by the point-to-point HVDC RMS example. The physical
    # transformer carries station resistance, so the converter interface is
    # lossless and does not duplicate that network loss.
    defaults = {
        "Kp_vdc": 0.20,
        "Ki_vdc": 1.00,
        "Kp_icl": 0.20,
        "Ki_icl": 5.00,
        "Kp_pol": 0.02,
        "Ki_pol": 0.10,
        "R": 0.0,
    }
    for variable_name, value in defaults.items():
        _set_event_value(template.block, variable_name, value, vfactory)

    return template


def get_hvdc_vdc_q_vsc_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC - Vdc/Q",
) -> RmsModelTemplate:
    """Build the DC-voltage/reactive-power controlling HVDC terminal."""
    return build_hvdc_vsc_gfl_rms(
        vfactory=vfactory,
        name=name,
        control1=ConverterControlType.Vm_dc,
        control2=ConverterControlType.Qac,
    )


def get_hvdc_pdc_q_vsc_rms(
        vfactory: VarFactory,
        name: str = "HVDC GFL VSC - Pdc/Q",
) -> RmsModelTemplate:
    """Build the DC-power/reactive-power controlling HVDC terminal."""
    return build_hvdc_vsc_gfl_rms(
        vfactory=vfactory,
        name=name,
        control1=ConverterControlType.Pdc,
        control2=ConverterControlType.Qac,
    )
