# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES PssELIN2 model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssELIN2Parameters:
    """Canonical PssELIN2 fields used by its piecewise control law."""

    __slots__ = ('ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ks1', 'ks2', 'ppss', 'apss', 'psslim')

    def __init__(
            self,
            ts1: float = 0.0,
            ts2: float = 0.0,
            ts3: float = 0.0,
            ts4: float = 0.0,
            ts5: float = 0.0,
            ts6: float = 0.0,
            ks1: float = 0.0,
            ks2: float = 0.0,
            ppss: float = 0.0,
            apss: float = 0.0,
            psslim: float = 0.0,
    ) -> None:
        """Store PssELIN2's canonical DY values.

        :param ts1: First input low-pass time constant in seconds.
        :param ts2: Parallel Ks2 path lag time in seconds.
        :param ts3: Second input low-pass time constant in seconds.
        :param ts4: First washout time constant in seconds.
        :param ts5: Second washout time constant in seconds.
        :param ts6: Third washout time constant in seconds.
        :param ks1: B(s) path gain.
        :param ks2: V(s) path gain.
        :param ppss: Piecewise stabilizer operating-point selector in [0, 4].
        :param apss: Piecewise stabilizer gain.
        :param psslim: Symmetric output limit magnitude.
        """
        self.ts1: float = ts1
        self.ts2: float = ts2
        self.ts3: float = ts3
        self.ts4: float = ts4
        self.ts5: float = ts5
        self.ts6: float = ts6
        self.ks1: float = ks1
        self.ks2: float = ks2
        self.ppss: float = ppss
        self.apss: float = apss
        self.psslim: float = psslim


def build_pss_e_l_i_n2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssELIN2Parameters | None = None,
) -> RmsModelTemplate:
    """Build the EA1317 cascaded-filter and piecewise PssELIN2 graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime instance name.
    :param parameters: Parsed canonical CGMES PssELIN2 values.
    :return: Equation-backed stabilizer with electrical-power input and Vs output.
    :raises ValueError: Nonfinite/negative times, invalid pPSS range, or limit.
    """
    settings: PssELIN2Parameters = PssELIN2Parameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        settings.ts1, settings.ts2, settings.ts3, settings.ts4,
        settings.ts5, settings.ts6, settings.ks1, settings.ks2,
        settings.ppss, settings.apss, settings.psslim,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('CGMES PssELIN2 parameters must be finite')
    elif min(settings.ts1, settings.ts2, settings.ts3, settings.ts4,
             settings.ts5, settings.ts6, settings.psslim) < 0.0:
        raise ValueError('CGMES PssELIN2 times and psslim must be nonnegative')
    elif settings.ppss < 0.0 or settings.ppss > 4.0:
        raise ValueError('CGMES PssELIN2 ppss must lie in [0, 4]')
    else:
        pass

    template_name: str = 'PssELIN2' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    electrical_power: Var = model.input('PePu', Const(0.0))
    first_low_pass: Var = model.lag(
        'PowerLowPass1Pu', electrical_power,
        model.parameter('PssELIN2.ts1', settings.ts1), settings.ts1, electrical_power,
    )
    second_low_pass: Var = model.lag(
        'PowerLowPass2Pu', first_low_pass,
        model.parameter('PssELIN2.ts3', settings.ts3), settings.ts3, first_low_pass,
    )
    first_washout: Var = model.washout(
        'Washout1Pu', second_low_pass,
        model.parameter('PssELIN2.ts4', settings.ts4), settings.ts4,
        Const(1.0), second_low_pass,
    ) if settings.ts4 > 0.0 else model.algebraic('Washout1Pu', Const(0.0), Const(0.0))
    second_washout: Var = model.washout(
        'Washout2Pu', first_washout,
        model.parameter('PssELIN2.ts5', settings.ts5), settings.ts5,
        Const(1.0), Const(0.0),
    ) if settings.ts5 > 0.0 else model.algebraic('Washout2Pu', Const(0.0), Const(0.0))
    third_washout: Var = model.washout(
        'Washout3Pu', second_washout,
        model.parameter('PssELIN2.ts6', settings.ts6), settings.ts6,
        Const(1.0), Const(0.0),
    ) if settings.ts6 > 0.0 else model.algebraic('Washout3Pu', Const(0.0), Const(0.0))

    b_path: Var = model.algebraic(
        'BPathPu', model.parameter('PssELIN2.ks1', settings.ks1) * third_washout, Const(0.0),
    )
    v_path_lag: Var = model.lag(
        'VPathLagPu', third_washout,
        model.parameter('PssELIN2.ts2', settings.ts2), settings.ts2, Const(0.0),
    )
    v_path: Var = model.algebraic(
        'VPathPu', model.parameter('PssELIN2.ks2', settings.ks2) * v_path_lag, Const(0.0),
    )
    ppss_parameter: Var = model.parameter('PssELIN2.ppss', settings.ppss)
    apss_parameter: Var = model.parameter('PssELIN2.apss', settings.apss)
    if settings.ppss <= 2.0:
        control_output: Expr = apss_parameter * (
            b_path * (Const(1.0) - ppss_parameter)
            + v_path * (Const(1.0) - sym.abs(ppss_parameter - Const(1.0)))
        )
    else:
        control_output = -apss_parameter * (
            b_path * (Const(3.0) - ppss_parameter)
            + v_path * (Const(1.0) - sym.abs(ppss_parameter - Const(3.0)))
        )

    output_limit: Var = model.parameter('PssELIN2.psslim', settings.psslim)
    output: Var = model.algebraic(
        'VsPu',
        sym.hard_sat(control_output, -output_limit, output_limit),
        Const(0.0),
    )
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssELIN2 electrical-power stabilizer')
    template.comment = 'CGMES PssELIN2 EA1317 cascaded filters, parallel paths, piecewise F(s), and Vs limiter.'
    enabled: Var = vfactory.add_var(f'PssELIN2.enabled_{template_name}')
    template.block.event_dict[enabled] = vfactory.add_const(value=None)
    return template
