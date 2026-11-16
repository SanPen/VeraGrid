# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES simplified steam turbine governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovSteamSGOParameters:
    """Values for the scalar fields declared by CGMES GovSteamSGO."""

    __slots__ = ('mwbase', 't1', 't2', 't3', 't4', 't5', 't6', 'k1', 'k2', 'k3', 'pmax', 'pmin')

    def __init__(
            self,
            mwbase: float = 100.0,
            t1: float = 0.1,
            t2: float = 0.0,
            t3: float = 0.1,
            t4: float = 0.1,
            t5: float = 1.0,
            t6: float = 0.1,
            k1: float = 0.2,
            k2: float = 0.3,
            k3: float = 0.3,
            pmax: float = 1.0,
            pmin: float = 0.0,
    ) -> None:
        """Store the CGMES scalar values.

        :param mwbase: Governor power base in MW.
        :param t1: Speed controller lag time in seconds.
        :param t2: Speed controller lead time in seconds.
        :param t3: Governor lag time in seconds.
        :param t4: Steam chest delay in seconds.
        :param t5: Reheater delay in seconds.
        :param t6: Intermediate and low pressure turbine delay in seconds.
        :param k1: Speed droop gain.
        :param k2: Reheater power fraction.
        :param k3: Intermediate and low pressure power fraction.
        :param pmax: Upper mechanical power limit in per unit.
        :param pmin: Lower mechanical power limit in per unit.
        """
        self.mwbase: float = mwbase
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t5: float = t5
        self.t6: float = t6
        self.k1: float = k1
        self.k2: float = k2
        self.k3: float = k3
        self.pmax: float = pmax
        self.pmin: float = pmin


def build_gov_steam_s_g_o_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovSteamSGOParameters | None = None,
) -> RmsModelTemplate:
    """Build the CGMES SGO governor, steam chest, reheater, and turbine equations.

    :param vfactory: Factory that owns all symbolic variables.
    :param name: Optional unique model instance name.
    :param parameters: Canonical GovSteamSGO scalar values.
    :return: Equation-backed governor with speed and power-reference ports.
    :raises ValueError: Invalid time constants, droop, limits, or power fractions.
    """
    settings: GovSteamSGOParameters = (
        GovSteamSGOParameters() if parameters is None else parameters
    )
    values: tuple[float, ...] = (
        settings.mwbase, settings.t1, settings.t2, settings.t3, settings.t4,
        settings.t5, settings.t6, settings.k1, settings.k2, settings.k3,
        settings.pmax, settings.pmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES GovSteamSGO parameters must be finite')
    elif settings.mwbase <= 0.0 or settings.k1 <= 0.0:
        raise ValueError('CGMES GovSteamSGO requires positive mwbase and droop gain')
    elif min(settings.t1, settings.t2, settings.t3, settings.t4, settings.t5, settings.t6) < 0.0:
        raise ValueError('CGMES GovSteamSGO times must be nonnegative')
    elif settings.pmin > settings.pmax:
        raise ValueError('CGMES GovSteamSGO requires pmin <= pmax')
    elif not 0.0 <= settings.k2 <= 1.0 or not 0.0 <= settings.k3 <= 1.0:
        raise ValueError('CGMES GovSteamSGO power fractions must lie in [0, 1]')
    else:
        pass

    template_name: str = 'GovSteamSGO' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    mwbase: Var = control.parameter('mwbase', settings.mwbase)
    t1: Var = control.parameter('t1', settings.t1)
    t2: Var = control.parameter('t2', settings.t2)
    t3: Var = control.parameter('t3', settings.t3)
    t4: Var = control.parameter('t4', settings.t4)
    t5: Var = control.parameter('t5', settings.t5)
    t6: Var = control.parameter('t6', settings.t6)
    k1: Var = control.parameter('k1', settings.k1)
    k2: Var = control.parameter('k2', settings.k2)
    k3: Var = control.parameter('k3', settings.k3)
    pmax: Var = control.parameter('pmax', settings.pmax)
    pmin: Var = control.parameter('pmin', settings.pmin)

    speed: Var = control.input('gov.omegaPu', Const(1.0))
    reference: Var = control.input('gov.PRefPu', Const(0.0))
    operating_power: Expr = Const(0.0)
    speed_error: Expr = (Const(1.0) - speed) / k1
    controller_output: Var = control.lead_lag(
        'GovSteamSGOControllerPu', speed_error, t2, t1,
        settings.t2, settings.t1, Const(0.0),
    )
    reference_sum: Var = control.algebraic(
        'GovSteamSGOReferenceSumPu', reference + controller_output, reference,
    )
    governor_demand: Expr = sym.hard_sat(reference_sum, pmin, pmax)
    valve_power: Var = control.lag(
        'GovSteamSGOValvePu', governor_demand, t3, settings.t3,
        operating_power, pmin, pmax,
    )
    chest_power: Var = control.lag(
        'GovSteamSGOSteamChestPu', valve_power, t4, settings.t4,
        operating_power,
    )
    reheater_power: Var = control.lag(
        'GovSteamSGOReheaterPu', chest_power, t5, settings.t5,
        operating_power,
    )
    low_pressure_power: Var = control.lag(
        'GovSteamSGOLowPressurePu', reheater_power, t6, settings.t6,
        operating_power,
    )
    mechanical_power: Expr = (
        (Const(1.0) - k2) * chest_power
        + (Const(1.0) - k3) * reheater_power
        + low_pressure_power
    )
    mechanical_power_pu: Var = control.algebraic(
        'gov.PmPu', mechanical_power, operating_power,
    )
    mechanical_power_mw: Var = control.algebraic(
        'gov.PmMW', mwbase * mechanical_power_pu, mwbase * operating_power,
    )
    parameter_names: tuple[str, ...] = (
        'enabled', 'mwbase', 't1', 't2', 't3', 't4', 't5', 't6',
        'k1', 'k2', 'k3', 'pmax', 'pmin',
    )
    for parameter_name in parameter_names:
        parameter_variable: Var = vfactory.add_var(
            f'GovSteamSGO.{parameter_name}_{template_name}'
        )
        control.block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    runtime_template: RmsModelTemplate = control.finish(
        (mechanical_power_pu, mechanical_power_mw),
        'CGMES GovSteamSGO speed controller, steam chest, reheater, and turbine response',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.tpe = runtime_template.tpe
    template.block = runtime_template.block
    template.comment = 'CGMES GovSteamSGO equations from its local EA block diagram.'
    return template
