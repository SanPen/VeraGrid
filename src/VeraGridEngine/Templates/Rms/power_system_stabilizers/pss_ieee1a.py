# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Executable CGMES PssIEEE1A stabilizer template."""

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import polynomial_measurement_filter
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssIEEE1AParameters:
    """Physical PSS1A filter, washout, phase, gain, and output-limit settings."""

    __slots__ = (
        'a1', 'a2', 't1', 't2', 't3', 't4', 't5', 't6', 'ks', 'upper', 'lower',
    )

    def __init__(
            self,
            a1: float = 0.061,
            a2: float = 0.0017,
            t1: float = 0.3,
            t2: float = 0.03,
            t3: float = 0.3,
            t4: float = 0.03,
            t5: float = 10.0,
            t6: float = 0.0,
            ks: float = 5.0,
            upper: float = 0.1,
            lower: float = -0.1,
    ) -> None:
        """Store PSS1A coefficients in per-unit and seconds.

        :param a1: First denominator coefficient of the torsional filter, in seconds.
        :param a2: Second denominator coefficient of the torsional filter, in seconds squared.
        :param t1: First lead time, in seconds.
        :param t2: First lag time, in seconds.
        :param t3: Second lead time, in seconds.
        :param t4: Second lag time, in seconds.
        :param t5: Washout time, in seconds.
        :param t6: Input transducer lag time, in seconds.
        :param ks: Stabilizer gain.
        :param upper: Supplementary output upper limit.
        :param lower: Supplementary output lower limit.
        """
        self.a1: float = a1
        self.a2: float = a2
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.t5: float = t5
        self.t6: float = t6
        self.ks: float = ks
        self.upper: float = upper
        self.lower: float = lower


def build_pss_i_e_e_e1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssIEEE1AParameters | None = None,
) -> RmsModelTemplate:
    """Build PssIEEE1A equations and retain its RDF scalar parameters.

    The input passes through T6 transducer, T5 washout, the second-order
    torsional filter ``1/(1+A1*s+A2*s^2)``, gain, two lead-lag stages, and
    output clipping. Zero-time transducer/phase stages and a zero washout are
    represented as exact bypass/zero-output equations.

    :param vfactory: Factory used to allocate the template symbols.
    :param name: Optional unique runtime instance name.
    :param parameters: Parsed CGMES values used to select stage topology.
    :return: Executable single-input supplementary excitation controller.
    :raises ValueError: Invalid filter coefficients, times, or output limits.
    """
    settings: PssIEEE1AParameters = PssIEEE1AParameters() if parameters is None else parameters
    template_name: str = "PssIEEE1A" if name is None else name
    if settings.lower >= settings.upper:
        raise ValueError('PssIEEE1A lower output limit must be below its upper limit')
    elif settings.t5 < 0.0:
        raise ValueError('PssIEEE1A washout time must be nonnegative')
    else:
        pass
    builder: ControlRealization = ControlRealization(vfactory, template_name)

    # Keep parameters in the block because the connected simulator can update them.
    t6: Var = builder.parameter('T6', settings.t6)
    t5: Var = builder.parameter('T5', settings.t5)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    gain: Var = builder.parameter('KS', settings.ks)
    upper: Var = builder.parameter('VSTMAX', settings.upper)
    lower: Var = builder.parameter('VSTMIN', settings.lower)
    source: Var = builder.input('SignalPu', Const(0.0))

    # T6 measures the selected host signal before the washout and torsional filter.
    transduced: Var = builder.lag('TransducerPu', source, t6, settings.t6, source)
    if settings.t5 > 0.0:
        washed_out: Expr = builder.washout('WashoutPu', transduced, t5, settings.t5, Const(1.0), transduced)
    else:
        washed_out = Const(0.0)

    # A1/A2 form the IEEE second-order denominator; zero coefficients remove states.
    filtered: Var = polynomial_measurement_filter(
        builder=builder,
        signal=washed_out,
        coefficients=(settings.a1, settings.a2, 0.0, 0.0, 0.0, 0.0),
    )
    phase1: Var = builder.lead_lag('Phase1Pu', filtered, t1, t2, settings.t1, settings.t2, Const(0.0))
    phase2: Var = builder.lead_lag('Phase2Pu', phase1, t3, t4, settings.t3, settings.t4, Const(0.0))
    output: Var = builder.algebraic(
        'VsPu',
        sym.hard_sat(gain * phase2, lower, upper),
        Const(0.0),
    )
    template: RmsModelTemplate = builder.finish((output,), 'CGMES PssIEEE1A single-input stabilizer')

    # Preserve RDF property names for audit and parameter round-tripping.
    for parameter_name in ('enabled', 'a1', 'a2', 't1', 't2', 't3', 't4', 't5', 't6', 'ks', 'vrmax', 'vrmin'):
        variable_name: str = f"PssIEEE1A.{parameter_name}_{template_name}"
        parameter_variable = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
