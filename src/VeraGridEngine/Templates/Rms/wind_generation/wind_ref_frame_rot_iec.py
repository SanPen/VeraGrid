# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""IEC reference-frame rotation for wind converter current commands."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


def build_wind_ref_frame_rot_i_e_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        tpll: float = 0.01,
        upll1: float = 0.0,
        upll2: float = 0.0,
        initial_voltage_real: float = 1.0,
        initial_voltage_imaginary: float = 0.0,
        initial_active_current: float = 0.0,
        initial_reactive_current: float = 0.0,
) -> RmsModelTemplate:
    """Build IEC 61400-27-1 Figure 25 reference-frame rotation equations.

    :param vfactory: Factory allocating model symbols.
    :param name: Optional unique runtime model name.
    :param tpll: Voltage-angle low-pass time constant in seconds.
    :param upll1: Voltage threshold selecting the filtered angle in pu.
    :param upll2: Voltage threshold freezing the angle-filter state in pu.
    :param initial_voltage_real: Load-flow real voltage component in pu.
    :param initial_voltage_imaginary: Load-flow imaginary voltage component in pu.
    :param initial_active_current: Load-flow active current in the controls frame.
    :param initial_reactive_current: Load-flow reactive current in the controls frame.
    :return: Equation-backed angle filter and current-coordinate rotation.
    :raises ValueError: Invalid time, voltage thresholds, or initial phasor.
    """
    values: tuple[float, ...] = (
        tpll, upll1, upll2, initial_voltage_real, initial_voltage_imaginary,
        initial_active_current, initial_reactive_current,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES WindRefFrameRotIEC values must be finite')
    elif min(tpll, upll1, upll2) < 0.0:
        raise ValueError('CGMES WindRefFrameRotIEC times and thresholds must be nonnegative')
    elif upll2 > upll1:
        raise ValueError('CGMES WindRefFrameRotIEC upll2 must not exceed upll1')
    else:
        pass

    template_name: str = 'WindRefFrameRotIEC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    pll_time: Var = model.parameter('WindRefFrameRotIEC.tpll', tpll)
    filtered_angle_threshold: Var = model.parameter('WindRefFrameRotIEC.upll1', upll1)
    freeze_angle_threshold: Var = model.parameter('WindRefFrameRotIEC.upll2', upll2)
    initial_voltage_magnitude: float = math.hypot(
        initial_voltage_real, initial_voltage_imaginary,
    )
    initial_voltage_angle: float = math.atan2(
        initial_voltage_imaginary, initial_voltage_real,
    )
    initial_current_real: float = (
        initial_active_current * math.cos(initial_voltage_angle)
        - initial_reactive_current * math.sin(initial_voltage_angle)
    )
    initial_current_imaginary: float = (
        initial_active_current * math.sin(initial_voltage_angle)
        + initial_reactive_current * math.cos(initial_voltage_angle)
    )
    bus_voltage_magnitude: Var = vfactory.add_var(
        name=f'Vm_{template_name}', reference=VarPowerFlowReferenceType.Vm,
    )
    bus_voltage_angle: Var = vfactory.add_var(
        name=f'Va_{template_name}', reference=VarPowerFlowReferenceType.Va,
    )
    model.block.external_mapping[VarPowerFlowReferenceType.Vm] = bus_voltage_magnitude
    model.block.external_mapping[VarPowerFlowReferenceType.Va] = bus_voltage_angle
    voltage_real: Expr = bus_voltage_magnitude * sym.cos(bus_voltage_angle)
    voltage_imaginary: Expr = bus_voltage_magnitude * sym.sin(bus_voltage_angle)
    current_real_control: Var = model.input('IpCtrlPu', Const(0.0))
    current_imaginary_control: Var = model.input('IqCtrlPu', Const(0.0))
    voltage_magnitude: Expr = sym.sqrt(
        voltage_real ** 2 + voltage_imaginary ** 2,
    )
    raw_voltage_angle: Expr = sym.atan2(voltage_imaginary, voltage_real)

    # The standard freezes PLL memory only below uPLL2, while uPLL1 independently selects the filtered output.
    angle_filter_state: Var = vfactory.add_var(
        name=f'VoltageAngleFilterState_{template_name}',
    )
    angle_filter_derivative: Expr = (
        (raw_voltage_angle - angle_filter_state) / pll_time
        if tpll > 0.0
        else Const(0.0)
    )
    if tpll > 0.0:
        freeze_flag: Expr = sym.heaviside(
            freeze_angle_threshold - voltage_magnitude,
        )
        model.differential(
            angle_filter_state,
            angle_filter_derivative * (Const(1.0) - freeze_flag),
            Const(initial_voltage_angle),
        )
        filtered_voltage_angle: Expr = angle_filter_state
    else:
        model.block.algebraic_vars.append(angle_filter_state)
        model.block.algebraic_eqs.append(angle_filter_state - raw_voltage_angle)
        model.block.init_eqs[angle_filter_state] = Const(initial_voltage_angle)
        filtered_voltage_angle = angle_filter_state

    filter_select: Expr = sym.heaviside(
        filtered_angle_threshold - voltage_magnitude,
    )
    selected_voltage_angle: Expr = (
        (Const(1.0) - filter_select) * raw_voltage_angle
        + filter_select * filtered_voltage_angle
    )
    # Cartesian rotation is algebraically the IEC polar conversion and stays defined at zero current.
    current_real_grid_expression: Expr = (
        current_real_control * sym.cos(selected_voltage_angle)
        - current_imaginary_control * sym.sin(selected_voltage_angle)
    )
    current_imaginary_grid_expression: Expr = (
        current_real_control * sym.sin(selected_voltage_angle)
        + current_imaginary_control * sym.cos(selected_voltage_angle)
    )
    current_real_grid: Var = model.algebraic(
        'IrePu', current_real_grid_expression, Const(initial_current_real),
    )
    current_imaginary_grid: Var = model.algebraic(
        'IimPu', current_imaginary_grid_expression, Const(initial_current_imaginary),
    )
    voltage_angle: Var = model.algebraic(
        'VoltageAngleRad', selected_voltage_angle, Const(initial_voltage_angle),
    )
    return model.finish(
        (current_real_grid, current_imaginary_grid, voltage_angle),
        'IEC 61400-27-1 Figure 25 PLL angle filtering/freezing and current-frame rotation.',
    )
