# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcNI bidirectional bridge template."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.exni import (
    BridgeExcitationSupply,
    build_exni_template,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


class ExcNIParameters:
    """Canonical ExcNI fields with source-backed reference defaults."""

    __slots__ = (
        'bus_fed_selector', 'tr', 'ka', 'ta', 'vrmax', 'vrmin', 'kf',
        'tf2', 'tf1', 'r',
    )

    def __init__(
            self,
            bus_fed_selector: bool = False,
            tr: float = 0.02,
            ka: float = 20.0,
            ta: float = 0.05,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
            kf: float = 0.05,
            tf2: float = 0.1,
            tf1: float = 1.0,
            r: float = 0.0,
    ) -> None:
        """Store all ten numeric/Boolean fields defined by the RDF class.

        :param bus_fed_selector: True selects independent bus supply.
        :param tr: Voltage sensing lag time in seconds.
        :param ka: Amplifier gain.
        :param ta: Amplifier lag time in seconds.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        :param kf: Regulator-output washout feedback gain.
        :param tf2: Final feedback filter lag time in seconds.
        :param tf1: First feedback washout time in seconds.
        :param r: Bridge reverse-current resistance.
        """
        self.bus_fed_selector: bool = bus_fed_selector
        self.tr: float = tr
        self.ka: float = ka
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.kf: float = kf
        self.tf2: float = tf2
        self.tf1: float = tf1
        self.r: float = r


def build_exc_n_i_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcNIParameters | None = None,
) -> RmsModelTemplate:
    """Build the reviewed bidirectional bridge graph or retain unsupported R.

    :param vfactory: Factory allocating symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed canonical fields or reference defaults.
    :return: Equation-backed graph for ``r=0``, otherwise an RDF record graph.
    :raises ValueError: Invalid fields or nonfinite parameter values.
    """
    settings: ExcNIParameters = ExcNIParameters() if parameters is None else parameters
    template_name: str = 'ExcNI' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tr, settings.ka, settings.ta, settings.vrmax, settings.vrmin,
        settings.kf, settings.tf2, settings.tf1, settings.r,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcNI fields must be finite')
    elif not isinstance(settings.bus_fed_selector, bool):
        raise ValueError('ExcNI busFedSelector must be Boolean')
    else:
        pass

    if settings.r != 0.0:
        template: RmsModelTemplate = RmsModelTemplate(name=template_name)
        template.block = Block(name=template_name)
        template.comment = (
            'CGMES ExcNI source record retained; nonzero R reverse-current behavior is unsupported'
        )
        retained_fields: tuple[tuple[str, float | bool], ...] = (
            ('busFedSelector', settings.bus_fed_selector),
            ('tr', settings.tr), ('ka', settings.ka), ('ta', settings.ta),
            ('vrmax', settings.vrmax), ('vrmin', settings.vrmin),
            ('kf', settings.kf), ('tf2', settings.tf2), ('tf1', settings.tf1),
            ('r', settings.r),
        )
        for parameter_name, parameter_value in retained_fields:
            parameter_var: Var = vfactory.add_var(
                f'ExcNI.{parameter_name}_{template_name}',
            )
            template.block.event_dict[parameter_var] = vfactory.add_const(
                value=parameter_value,
                name=parameter_var.name,
            )
        return template
    else:
        pass

    supply: BridgeExcitationSupply = (
        BridgeExcitationSupply.INDEPENDENT
        if settings.bus_fed_selector
        else BridgeExcitationSupply.TERMINAL
    )
    template: RmsModelTemplate = build_exni_template(
        vf=vfactory,
        name=template_name,
        tr=settings.tr,
        ka=settings.ka,
        ta=settings.ta,
        vrmax=settings.vrmax,
        vrmin=settings.vrmin,
        kf=settings.kf,
        tf1=settings.tf1,
        tf2=settings.tf2,
        supply=supply,
    )
    template.comment = 'CGMES ExcNI bidirectional controlled bridge, reviewed for R=0'
    parameter_fields: tuple[tuple[str, float | bool], ...] = (
        ('busFedSelector', settings.bus_fed_selector),
        ('tr', settings.tr), ('ka', settings.ka), ('ta', settings.ta),
        ('vrmax', settings.vrmax), ('vrmin', settings.vrmin),
        ('kf', settings.kf), ('tf2', settings.tf2), ('tf1', settings.tf1),
        ('r', settings.r),
    )
    for parameter_name, parameter_value in parameter_fields:
        parameter_var: Var = vfactory.add_var(
            f'ExcNI.{parameter_name}_{template_name}',
        )
        template.block.event_dict[parameter_var] = vfactory.add_const(
            value=parameter_value,
            name=parameter_var.name,
        )
    return template
