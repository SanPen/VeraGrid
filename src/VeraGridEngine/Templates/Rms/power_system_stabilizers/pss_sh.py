# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES Siemens H-infinity PssSH model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssSHParameters:
    """Canonical PssSH fields with their documented typical values."""

    __slots__ = ('k', 'k0', 'k1', 'k2', 'k3', 'k4', 'td', 't1', 't2', 't3', 't4', 'vsmax', 'vsmin')

    def __init__(
            self,
            k: float = 1.0,
            k0: float = 0.012,
            k1: float = 0.488,
            k2: float = 0.064,
            k3: float = 0.224,
            k4: float = 0.1,
            td: float = 10.0,
            t1: float = 0.076,
            t2: float = 0.086,
            t3: float = 1.068,
            t4: float = 1.913,
            vsmax: float = 0.1,
            vsmin: float = -0.1,
    ) -> None:
        """Store the CGMES parameters used by the PssSH realization.

        :param k: Main output gain.
        :param k0: Washout input gain.
        :param k1: First state output gain.
        :param k2: Second state output gain.
        :param k3: Third state output gain.
        :param k4: Fourth state output gain.
        :param td: Input-filter time constant in seconds.
        :param t1: First integrator time constant in seconds.
        :param t2: Second integrator time constant in seconds.
        :param t3: Third integrator time constant in seconds.
        :param t4: Fourth integrator time constant in seconds.
        :param vsmax: Upper stabilizer output limit.
        :param vsmin: Lower stabilizer output limit.
        """
        self.k: float = k
        self.k0: float = k0
        self.k1: float = k1
        self.k2: float = k2
        self.k3: float = k3
        self.k4: float = k4
        self.td: float = td
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.vsmax: float = vsmax
        self.vsmin: float = vsmin


def build_pss_s_h_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssSHParameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1325 four-integrator H-infinity stabilizer graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Imported canonical CGMES values.
    :return: Equation template with one electrical-power input and Vs output.
    :raises ValueError: Nonfinite parameters, nonpositive integrator times, or invalid limits.
    """
    settings: PssSHParameters = PssSHParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.k, settings.k0, settings.k1, settings.k2, settings.k3, settings.k4,
        settings.td, settings.t1, settings.t2, settings.t3, settings.t4,
        settings.vsmax, settings.vsmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES PssSH parameters must be finite')
    elif settings.td < 0.0 or min(settings.t1, settings.t2, settings.t3, settings.t4) <= 0.0:
        raise ValueError('CGMES PssSH requires td >= 0 and positive integrator times')
    elif settings.vsmin >= settings.vsmax:
        raise ValueError('CGMES PssSH output limits are invalid')
    else:
        pass

    template_name: str = 'PssSH' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    electrical_power: Var = model.input('PePu', Const(0.0))
    filter_time: Var = model.parameter('PssSH.td', settings.td)
    filtered_power: Var = model.lag(
        'InputFilterPu', electrical_power, filter_time, settings.td, electrical_power,
    )
    washout: Var = model.algebraic(
        'WashoutPu', electrical_power - filtered_power, Const(0.0),
    )

    # The feedback sum enters the first integrator; predeclared states close this loop.
    state1: Var = vfactory.add_var(f'Integrator1Pu_{template_name}')
    state2: Var = vfactory.add_var(f'Integrator2Pu_{template_name}')
    state3: Var = vfactory.add_var(f'Integrator3Pu_{template_name}')
    state4: Var = vfactory.add_var(f'Integrator4Pu_{template_name}')
    state_feedback: Expr = state1 + state2 + state3 + state4
    model.differential(
        state1,
        (washout - state_feedback) / model.parameter('PssSH.t1', settings.t1),
        Const(0.0),
    )
    model.differential(
        state2,
        state1 / model.parameter('PssSH.t2', settings.t2),
        Const(0.0),
    )
    model.differential(
        state3,
        state2 / model.parameter('PssSH.t3', settings.t3),
        Const(0.0),
    )
    model.differential(
        state4,
        state3 / model.parameter('PssSH.t4', settings.t4),
        Const(0.0),
    )

    output_sum: Expr = (
        model.parameter('PssSH.k0', settings.k0) * washout
        + model.parameter('PssSH.k1', settings.k1) * state1
        + model.parameter('PssSH.k2', settings.k2) * state2
        + model.parameter('PssSH.k3', settings.k3) * state3
        + model.parameter('PssSH.k4', settings.k4) * state4
    )
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(
            model.parameter('PssSH.k', settings.k) * output_sum,
            model.parameter('PssSH.vsmin', settings.vsmin),
            model.parameter('PssSH.vsmax', settings.vsmax),
        ),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssSH Siemens H-infinity stabilizer')
    template.comment = 'CGMES PssSH EA1325 four-integrator state-space graph with input washout and Vs limits.'
    enabled: Var = vfactory.add_var(f'PssSH.enabled_{template_name}')
    template.block.event_dict[enabled] = vfactory.add_const(value=None)
    return template
