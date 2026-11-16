# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Preserve Cartesian DGS meter components instead of falling back to magnitude."""
from __future__ import annotations

import cmath

import pytest

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.IO.dgs.dgs_objects import StaImea, StaVmea
from VeraGridEngine.IO.dgs.dgs_rms_measurement_binding import (
    _build_current_alias_expressions, _build_voltage_alias_expressions,
)
from VeraGridEngine.Templates.Rms.buses.bus_rms_template import initialize_bus_rms
from VeraGridEngine.Templates.Rms.line.line_rms_template import get_line_rms_template
from VeraGridEngine.Utils.Symbolic.symbolic import Expr
from VeraGridEngine.enumerations import VarPowerFlowReferenceType


@pytest.mark.parametrize('angle', (0.0, 0.4, -0.7))
def test_voltage_cartesian_aliases_keep_both_components(angle: float) -> None:
    """Use the measured phasor for real/imaginary and alpha/beta aliases.

    :param angle: Measured voltage angle in radians.
    :return: None.
    """
    factory: VarFactory = VarFactory()
    bus: Bus = Bus(name='Measured', Vnom=110.0)
    initialize_bus_rms(bus, factory)
    aliases: dict[str, Expr] = _build_voltage_alias_expressions(
        StaVmea(), list(('xr_pos', 'xi_pos', 'alpha', 'beta')), bus)
    values: dict[int, float] = dict((
        (bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm].uid, 1.1),
        (bus.rms_model.external_mapping[VarPowerFlowReferenceType.Va].uid, angle)))
    voltage: complex = 1.1 * cmath.exp(1j * angle)
    assert aliases['xr_pos'].eval_uid(values) == pytest.approx(voltage.real)
    assert aliases['alpha'].eval_uid(values) == pytest.approx(voltage.real)
    assert aliases['xi_pos'].eval_uid(values) == pytest.approx(voltage.imag)
    assert aliases['beta'].eval_uid(values) == pytest.approx(voltage.imag)


@pytest.mark.parametrize('terminal', (0, 1))
def test_current_cartesian_aliases_keep_components_and_terminal(terminal: int) -> None:
    """Resolve Cartesian current using P/Q at the selected branch terminal.

    :param terminal: Source cubicle terminal ordinal.
    :return: None.
    """
    factory: VarFactory = VarFactory()
    bus: Bus = Bus(name='Measured', Vnom=110.0)
    initialize_bus_rms(bus, factory)
    line: Line = Line(bus_from=bus, bus_to=bus)
    line.rms_model = get_line_rms_template(factory).block
    meter: StaImea = StaImea()
    meter.i_mode = 0
    aliases: dict[str, Expr] = _build_current_alias_expressions(
        meter, list(('xr_pos', 'xi_pos')), bus, line, terminal, 100.0)
    values: dict[int, float] = dict((
        (bus.rms_model.external_mapping[VarPowerFlowReferenceType.Vm].uid, 1.0),
        (bus.rms_model.external_mapping[VarPowerFlowReferenceType.Va].uid, 0.0),
        (line.rms_model.external_mapping[VarPowerFlowReferenceType.Pf].uid, 0.3),
        (line.rms_model.external_mapping[VarPowerFlowReferenceType.Qf].uid, 0.4),
        (line.rms_model.external_mapping[VarPowerFlowReferenceType.Pt].uid, -0.2),
        (line.rms_model.external_mapping[VarPowerFlowReferenceType.Qt].uid, -0.1)))
    expected: complex = complex(0.3, -0.4) if terminal == 0 else complex(-0.2, 0.1)
    assert aliases['xr_pos'].eval_uid(values) == pytest.approx(expected.real)
    assert aliases['xi_pos'].eval_uid(values) == pytest.approx(expected.imag)
