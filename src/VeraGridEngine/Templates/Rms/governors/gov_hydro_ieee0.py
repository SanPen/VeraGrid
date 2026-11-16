# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES GovHydroIEEE0 simplified hydro governor."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class GovHydroIEEE0Parameters:
    """CGMES GovHydroIEEE0 scalar parameters."""

    __slots__ = ('mwbase', 'k', 't1', 't2', 't3', 't4', 'pmax', 'pmin')

    def __init__(
            self,
            mwbase: float = 100.0,
            k: float = 25.0,
            t1: float = 0.25,
            t2: float = 0.0,
            t3: float = 0.1,
            t4: float = 1.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
    ) -> None:
        """Store equation coefficients in their CIM units.

        :param mwbase: Turbine power base in MW.
        :param k: Inverse-droop governor gain.
        :param t1: Speed governor lag time in seconds.
        :param t2: Speed governor lead time in seconds.
        :param t3: Gate actuator lag time in seconds.
        :param t4: Water starting time in seconds.
        :param pmax: Maximum gate position in per unit.
        :param pmin: Minimum gate position in per unit.
        """
        self.mwbase: float = mwbase
        self.k: float = k
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.pmax: float = pmax
        self.pmin: float = pmin


def build_gov_hydro_i_e_e_e0_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: GovHydroIEEE0Parameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE G2 transfer path with exact zero-time reductions.

    :param vfactory: Factory owning this template's symbolic variables.
    :param name: Optional runtime name.
    :param parameters: Parsed RDF settings selecting stage topologies.
    :return: CGMES parameter template with speed, reference, and Pm ports.
    :raises ValueError: Invalid limits or a noncausal zero-time stage combination.
    """
    settings: GovHydroIEEE0Parameters = (
        GovHydroIEEE0Parameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.mwbase, settings.k, settings.t1, settings.t2, settings.t3,
        settings.t4, settings.pmax, settings.pmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('GovHydroIEEE0 parameters must be finite')
    elif settings.mwbase <= 0.0 or min(settings.t1, settings.t2, settings.t3, settings.t4) < 0.0:
        raise ValueError('GovHydroIEEE0 requires positive MWBASE and nonnegative times')
    elif settings.pmin >= settings.pmax:
        raise ValueError('GovHydroIEEE0 requires PMIN below PMAX')
    elif settings.t1 == 0.0 and settings.t3 == 0.0 and settings.t2 > 0.0:
        raise ValueError('GovHydroIEEE0 zero T1 and T3 with positive T2 is noncausal')
    else:
        pass

    template_name: str = 'GovHydroIEEE0' if name is None else name
    control: ControlRealization = ControlRealization(vfactory, template_name)
    gain: Var = control.parameter('GovHydroIEEE0.k', settings.k)
    t1: Var = control.parameter('GovHydroIEEE0.t1', settings.t1)
    t2: Var = control.parameter('GovHydroIEEE0.t2', settings.t2)
    t3: Var = control.parameter('GovHydroIEEE0.t3', settings.t3)
    t4: Var = control.parameter('GovHydroIEEE0.t4', settings.t4)
    pmax: Var = control.parameter('GovHydroIEEE0.pmax', settings.pmax)
    pmin: Var = control.parameter('GovHydroIEEE0.pmin', settings.pmin)
    control.parameter('GovHydroIEEE0.mwbase', settings.mwbase)
    speed: Var = control.input('OmegaPu', Const(1.0))
    speed_reference: Var = control.input('OmegaRefPu', Const(1.0))
    power_reference: Var = control.input('PRefPu', Const(0.5))

    # The IEEE diagram filters absolute-speed error before lead compensation.
    speed_error: Expr = speed - speed_reference
    filtered_speed_error: Var = control.lag(
        'SpeedGovernorLag', speed_error, t1, settings.t1, Const(0.0),
    )
    if settings.t3 > 0.0:
        compensated_speed: Var = control.lead_lag(
            'SpeedGovernorCompensator', filtered_speed_error, t2, t3,
            settings.t2, settings.t3, Const(0.0),
        )
    elif settings.t2 == 0.0:
        compensated_speed = control.algebraic(
            'SpeedGovernorCompensator', filtered_speed_error, Const(0.0),
        )
    elif settings.t1 > 0.0:
        filtered_speed_rate: Expr = (speed_error - filtered_speed_error) / t1
        compensated_speed = control.algebraic(
            'SpeedGovernorCompensator',
            filtered_speed_error + t2 * filtered_speed_rate,
            Const(0.0),
        )
    else:
        raise ValueError('GovHydroIEEE0 lead stage lacks a causal lag state')

    # Gate limits precede the water-column transfer in the IEC diagram.
    gate_command: Var = control.algebraic(
        'GateCommandPu',
        sym.hard_sat(power_reference - gain * compensated_speed, pmin, pmax),
        Const(min(max(0.5, settings.pmin), settings.pmax)),
    )
    if settings.t4 > 0.0:
        mechanical_power: Var = control.lead_lag(
            'PmPu', gate_command, -t4, Const(0.5) * t4,
            -settings.t4, 0.5 * settings.t4, Const(min(max(0.5, settings.pmin), settings.pmax)),
        )
    else:
        mechanical_power = control.algebraic(
            'PmPu', gate_command, Const(min(max(0.5, settings.pmin), settings.pmax)),
        )

    runtime: RmsModelTemplate = control.finish(
        (mechanical_power,), 'CGMES GovHydroIEEE0 IEEE G2 governor and water column',
    )
    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime.block)
    template.block.name = template_name
    template.comment = 'CGMES GovHydroIEEE0 equations with exact zero-time stages.'

    # Keep the canonical RDF parameter names available beside equation events.
    for parameter_name in ('enabled', 'mwbase', 'k', 't1', 't2', 't3', 't4', 'pmax', 'pmin'):
        parameter_variable: Var = vfactory.add_var(
            f'GovHydroIEEE0.{parameter_name}_{template_name}'
        )
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=parameter_variable.name,
        )
    return template
