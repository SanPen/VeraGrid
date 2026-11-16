# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES PssSB4 model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssSB4Parameters:
    """CGMES PssSB4 parameters read from the canonical RDF properties."""

    __slots__ = ('tt', 'kx', 'tx2', 'ta', 'tx1', 'tb', 'tc', 'td', 'te', 'vsmax', 'vsmin')

    def __init__(
            self,
            tt: float = 0.0,
            kx: float = 0.0,
            tx2: float = 0.0,
            ta: float = 0.0,
            tx1: float = 0.0,
            tb: float = 0.0,
            tc: float = 0.0,
            td: float = 0.0,
            te: float = 0.0,
            vsmax: float = 0.1,
            vsmin: float = -0.1,
    ) -> None:
        """Store RDF fields without substituting values absent from an import.

        :param tt: Active-power measurement lag in seconds.
        :param kx: Washout numerator gain.
        :param tx2: Washout denominator time in seconds.
        :param ta: First phase-compensation numerator time in seconds.
        :param tx1: First phase-compensation denominator time in seconds.
        :param tb: Second phase-compensation numerator time in seconds.
        :param tc: Second phase-compensation denominator time in seconds.
        :param td: First output-lag time in seconds.
        :param te: Second output-lag time in seconds.
        :param vsmax: Stabilizer upper output limit.
        :param vsmin: Stabilizer lower output limit.
        """
        self.tt: float = tt
        self.kx: float = kx
        self.tx2: float = tx2
        self.ta: float = ta
        self.tx1: float = tx1
        self.tb: float = tb
        self.tc: float = tc
        self.td: float = td
        self.te: float = te
        self.vsmax: float = vsmax
        self.vsmin: float = vsmin


def build_pss_s_b4_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssSB4Parameters | None = None,
) -> RmsModelTemplate:
    """Build PssSB4's filtered-power washout and compensation chain.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Imported canonical CGMES parameter values.
    :return: Controller template with active-power and power-reference ports.
    :raises ValueError: Nonfinite values, invalid limits, or a singular washout.
    """
    settings: PssSB4Parameters = PssSB4Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.tt, settings.kx, settings.tx2, settings.ta, settings.tx1,
        settings.tb, settings.tc, settings.td, settings.te, settings.vsmax, settings.vsmin,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES PssSB4 parameters must be finite')
    elif min(settings.tt, settings.tx2, settings.ta, settings.tx1, settings.tb,
             settings.tc, settings.td, settings.te) < 0.0:
        raise ValueError('CGMES PssSB4 time constants must be nonnegative')
    elif settings.vsmin >= settings.vsmax:
        raise ValueError('CGMES PssSB4 output limits are invalid')
    elif settings.tx2 == 0.0 and settings.kx != 0.0:
        raise ValueError('CGMES PssSB4 washout is singular when tx2 is zero and kx is nonzero')
    else:
        pass

    template_name: str = 'PssSB4' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    active_power: Var = model.input('PePu', Const(0.0))
    power_reference: Var = model.input('PRefPu', Const(0.0))
    power_lag_time: Var = model.parameter('PssSB4.tt', settings.tt)
    measured_power: Var = model.lag(
        'MeasuredPowerPu', active_power, power_lag_time, settings.tt, active_power,
    )
    washout_input: Var = model.algebraic(
        'WashoutInputPu', measured_power - power_reference, Const(0.0),
    )
    if settings.tx2 > 0.0:
        # A state realizes the finite washout pole without differentiating Pe.
        washout_time: Var = model.parameter('PssSB4.tx2', settings.tx2)
        washout_state: Var = model.lag(
            'WashoutStatePu', washout_input, washout_time, settings.tx2, Const(0.0),
        )
        washout_gain: Var = model.parameter('PssSB4.kx', settings.kx)
        compensated_signal: Var = model.algebraic(
            'WashoutOutputPu', washout_gain / washout_time * (washout_input - washout_state), Const(0.0),
        )
    else:
        # A zero washout time has the exact diagram limit only when its numerator gain is zero.
        washout_time = model.parameter('PssSB4.tx2', settings.tx2)
        washout_gain = model.parameter('PssSB4.kx', settings.kx)
        compensated_signal = model.algebraic('WashoutOutputPu', washout_gain * washout_input, Const(0.0))

    first_phase: Var = model.lead_lag(
        'FirstPhasePu', compensated_signal,
        model.parameter('PssSB4.ta', settings.ta),
        model.parameter('PssSB4.tx1', settings.tx1),
        settings.ta, settings.tx1, Const(0.0),
    )
    second_phase: Var = model.lead_lag(
        'SecondPhasePu', first_phase,
        model.parameter('PssSB4.tb', settings.tb),
        model.parameter('PssSB4.tc', settings.tc),
        settings.tb, settings.tc, Const(0.0),
    )
    first_output_lag: Var = model.lag(
        'FirstOutputLagPu', second_phase,
        model.parameter('PssSB4.td', settings.td), settings.td, Const(0.0),
    )
    second_output_lag: Var = model.lag(
        'SecondOutputLagPu', first_output_lag,
        model.parameter('PssSB4.te', settings.te), settings.te, Const(0.0),
    )
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(
            second_output_lag,
            model.parameter('PssSB4.vsmin', settings.vsmin),
            model.parameter('PssSB4.vsmax', settings.vsmax),
        ),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssSB4 power stabilizer')
    template.comment = 'CGMES PssSB4 EA1323 filtered-power washout, two phase stages, and output lags.'
    enabled: Var = vfactory.add_var(f'PssSB4.enabled_{template_name}')
    template.block.event_dict[enabled] = vfactory.add_const(value=None)
    return template
