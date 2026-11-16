# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the canonical CGMES PssIEEE3B model."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.power_system_stabilizers.ieeest import (
    polynomial_measurement_filter,
)
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class PssIEEE3BParameters:
    """Canonical PssIEEE3B values used to select exact equation branches."""

    __slots__ = (
        't1', 't2', 'tw1', 'tw2', 'tw3', 'ks1', 'ks2', 'a1', 'a2', 'a3', 'a4',
        'a5', 'a6', 'a7', 'a8', 'vstmax', 'vstmin',
    )

    def __init__(
            self,
            t1: float = 0.012,
            t2: float = 0.012,
            tw1: float = 0.3,
            tw2: float = 0.3,
            tw3: float = 0.6,
            ks1: float = -0.602,
            ks2: float = 30.12,
            a1: float = 0.359,
            a2: float = 0.586,
            a3: float = 0.429,
            a4: float = 0.564,
            a5: float = 0.001,
            a6: float = 0.0,
            a7: float = 0.031,
            a8: float = 0.0,
            vstmax: float = 0.1,
            vstmin: float = -0.1,
    ) -> None:
        """Store the RDF fields and standard typical values.

        :param t1: Signal 1 transducer time in seconds.
        :param t2: Signal 2 transducer time in seconds.
        :param tw1: Signal 1 washout time in seconds.
        :param tw2: Signal 2 washout time in seconds.
        :param tw3: Common washout time in seconds.
        :param ks1: Signal 1 gain.
        :param ks2: Signal 2 gain.
        :param a1: First phase numerator first-order coefficient.
        :param a2: First phase numerator second-order coefficient.
        :param a3: First phase denominator first-order coefficient.
        :param a4: First phase denominator second-order coefficient.
        :param a5: Second phase numerator first-order coefficient.
        :param a6: Second phase numerator second-order coefficient.
        :param a7: Second phase denominator first-order coefficient.
        :param a8: Second phase denominator second-order coefficient.
        :param vstmax: Maximum stabilizer output.
        :param vstmin: Minimum stabilizer output.
        """
        self.t1: float = t1
        self.t2: float = t2
        self.tw1: float = tw1
        self.tw2: float = tw2
        self.tw3: float = tw3
        self.ks1: float = ks1
        self.ks2: float = ks2
        self.a1: float = a1
        self.a2: float = a2
        self.a3: float = a3
        self.a4: float = a4
        self.a5: float = a5
        self.a6: float = a6
        self.a7: float = a7
        self.a8: float = a8
        self.vstmax: float = vstmax
        self.vstmin: float = vstmin


def build_pss_i_e_e_e3_b_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: PssIEEE3BParameters | None = None,
) -> RmsModelTemplate:
    """Build PssIEEE3B's dual-input, dual-quadratic phase-compensation graph.

    :param vfactory: Factory allocating equation and parameter symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical CGMES values, including exact zero-time branches.
    :return: Standalone template with two open selected-measurement inputs.
    :raises ValueError: Invalid times, limits, or improper quadratic filters.
    """
    settings: PssIEEE3BParameters = PssIEEE3BParameters() if parameters is None else parameters
    numeric_values: tuple[float, ...] = (
        settings.t1, settings.t2, settings.tw1, settings.tw2, settings.tw3,
        settings.ks1, settings.ks2, settings.a1, settings.a2, settings.a3,
        settings.a4, settings.a5, settings.a6, settings.a7, settings.a8,
        settings.vstmax, settings.vstmin,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('CGMES PssIEEE3B parameters must be finite')
    elif min(settings.t1, settings.t2, settings.tw1, settings.tw2, settings.tw3) < 0.0:
        raise ValueError('CGMES PssIEEE3B time constants must be nonnegative')
    elif settings.vstmin >= settings.vstmax:
        raise ValueError('CGMES PssIEEE3B output limits are invalid')
    else:
        pass

    template_name: str = 'PssIEEE3B' if name is None else name
    builder: ControlRealization = ControlRealization(vfactory, template_name)
    signal1: Var = builder.input('Signal1Pu', Const(0.0))
    signal2: Var = builder.input('Signal2Pu', Const(0.0))
    transducer1: Var = builder.parameter('T1', settings.t1)
    transducer2: Var = builder.parameter('T2', settings.t2)
    transducer_signal1: Var = builder.lag(
        'Transducer1Pu', signal1, transducer1, settings.t1, signal1,
    )
    transducer_signal2: Var = builder.lag(
        'Transducer2Pu', signal2, transducer2, settings.t2, signal2,
    )

    # The channel gains precede their washouts, preserving nonzero DC bias when
    # a source record selects a zero washout time.
    gain1: Var = builder.parameter('KS1', settings.ks1)
    gain2: Var = builder.parameter('KS2', settings.ks2)
    gained_signal1: Var = builder.algebraic(
        'GainedSignal1Pu', gain1 * transducer_signal1, gain1 * signal1,
    )
    gained_signal2: Var = builder.algebraic(
        'GainedSignal2Pu', gain2 * transducer_signal2, gain2 * signal2,
    )
    washout1_time: Var = builder.parameter('TW1', settings.tw1)
    washout2_time: Var = builder.parameter('TW2', settings.tw2)
    if settings.tw1 > 0.0:
        washed_signal1: Var = builder.washout(
            'Washout1Pu', gained_signal1, washout1_time, settings.tw1,
            Const(1.0), gained_signal1,
        )
    else:
        washed_signal1 = builder.algebraic('Washout1Pu', gained_signal1, gained_signal1)
    if settings.tw2 > 0.0:
        washed_signal2: Var = builder.washout(
            'Washout2Pu', gained_signal2, washout2_time, settings.tw2,
            Const(1.0), gained_signal2,
        )
    else:
        washed_signal2 = builder.algebraic('Washout2Pu', gained_signal2, gained_signal2)

    combined: Var = builder.algebraic(
        'CombinedPu', washed_signal1 + washed_signal2, washed_signal1 + washed_signal2,
    )
    washout3_time: Var = builder.parameter('TW3', settings.tw3)
    if settings.tw3 > 0.0:
        common_signal: Var = builder.washout(
            'CommonWashoutPu', combined, washout3_time, settings.tw3,
            Const(1.0), combined,
        )
    else:
        common_signal = builder.algebraic('CommonWashoutPu', combined, combined)

    # Each source quadratic is represented directly as a rational polynomial;
    # no pole factoring changes repeated or complex roots.
    first_phase: Var = polynomial_measurement_filter(
        builder,
        common_signal,
        (settings.a3, settings.a4, 0.0, 0.0, settings.a1, settings.a2),
        'Phase1',
    )
    second_phase: Var = polynomial_measurement_filter(
        builder,
        first_phase,
        (settings.a7, settings.a8, 0.0, 0.0, settings.a5, settings.a6),
        'Phase2',
    )
    upper: Var = builder.parameter('VSTMAX', settings.vstmax)
    lower: Var = builder.parameter('VSTMIN', settings.vstmin)
    output_expression: Expr = sym.hard_sat(second_phase, lower, upper)
    output: Var = builder.algebraic('VsPu', output_expression, output_expression)
    runtime_template: RmsModelTemplate = builder.finish(
        (output,),
        'Dual-input CGMES PSS with two quadratic phase-compensation stages',
    )

    template: RmsModelTemplate = RmsModelTemplate(name=template_name)
    template.block.children.append(runtime_template.block)
    template.block.name = template_name
    template.comment = 'CGMES PssIEEE3B equations with two selected measurements and exact zero-time bypasses.'
    for parameter_name in (
            'enabled', 't1', 't2', 'tw1', 'tw2', 'tw3', 'ks1', 'ks2',
            'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'vstmax', 'vstmin',
    ):
        variable_name: str = f'PssIEEE3B.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None,
            name=variable_name,
        )
    return template
