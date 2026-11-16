# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES IEEE DEC2A transient excitation booster."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import aflipflop, bool_and
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class DiscExcContIEEEDEC2AParameters:
    """Canonical IEEE DEC2A filter and output-limit settings."""

    __slots__ = ('vk', 'td1', 'td2', 'vdmin', 'vdmax')

    def __init__(
            self,
            vk: float = 0.0,
            td1: float = 0.0,
            td2: float = 0.0,
            vdmin: float = -0.1,
            vdmax: float = 0.1,
    ) -> None:
        """Store the canonical DEC2A parameters.

        :param vk: Remote-triggered excitation-boost step amplitude.
        :param td1: Optional first-order trigger conditioning time in seconds.
        :param td2: High-pass washout time in seconds.
        :param vdmin: Boost signal lower limit.
        :param vdmax: Boost signal upper limit.
        """
        self.vk: float = vk
        self.td1: float = td1
        self.td2: float = td2
        self.vdmin: float = vdmin
        self.vdmax: float = vdmax


def build_disc_exc_cont_i_e_e_e_d_e_c2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: DiscExcContIEEEDEC2AParameters | None = None,
) -> RmsModelTemplate:
    """Build the IEEE DEC2A trigger, lead filter and transient boost equations.

    :param vfactory: Factory that owns all graph symbols.
    :param name: Optional unique runtime model name.
    :param parameters: Canonical CGMES DEC2A values.
    :return: Standalone DEC2A graph with remote-trigger, voltage and PSS ports.
    :raises ValueError: Nonfinite settings, negative times or reversed limits.
    """
    settings: DiscExcContIEEEDEC2AParameters = (
        DiscExcContIEEEDEC2AParameters() if parameters is None else parameters
    )
    numeric_values: tuple[float, ...] = (
        settings.vk, settings.td1, settings.td2, settings.vdmin, settings.vdmax,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('DEC2A parameters must be finite')
    elif min(settings.td1, settings.td2) < 0.0:
        raise ValueError('DEC2A filter times must be nonnegative')
    elif settings.vdmin >= settings.vdmax:
        raise ValueError('DEC2A lower output limit must be below its upper limit')
    else:
        pass

    template_name: str = 'DiscExcContIEEEDEC2A' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    vk: Var = model.parameter('DiscExcContIEEEDEC2A.vk', settings.vk)
    td1: Var = model.parameter('DiscExcContIEEEDEC2A.td1', settings.td1)
    td2: Var = model.parameter('DiscExcContIEEEDEC2A.td2', settings.td2)
    vdmin: Var = model.parameter('DiscExcContIEEEDEC2A.vdmin', settings.vdmin)
    vdmax: Var = model.parameter('DiscExcContIEEEDEC2A.vdmax', settings.vdmax)
    trigger: Var = model.input('TriggerPu', Const(0.0))
    terminal_voltage: Var = model.input('VtPu', Const(1.0))
    # This operating-point seed is not a DEC2A threshold; the IEEE setting remains host-owned.
    voltage_threshold: Var = model.input('VfreezePu', Const(1.0))
    stabilizer: Var = model.input('VstPu', Const(0.0))
    trigger_step: Var = model.algebraic(
        'TriggerStepPu', vk * sym.heaviside(trigger - Const(0.5)), Const(0.0),
    )
    conditioned_step: Var = model.lag(
        'ConditionedStepPu', trigger_step, td1, settings.td1, Const(0.0),
    )
    if settings.td2 > 0.0:
        decaying_boost: Var = model.washout(
            'BoostPu', conditioned_step, td2, settings.td2, Const(1.0), Const(0.0),
        )
    else:
        decaying_boost = model.algebraic('BoostPu', Const(0.0), Const(0.0))
    frozen_boost: Var = vfactory.add_var(f'FrozenBoostPu_{template_name}')
    model.block.event_dict[frozen_boost] = vfactory.add_const(value=0.0)
    model.block.procedural_logic.append(
        aflipflop(
            x=decaying_boost,
            boolset=terminal_voltage > voltage_threshold,
            boolreset=bool_and(
                terminal_voltage < voltage_threshold,
                decaying_boost < frozen_boost,
            ),
            output=frozen_boost,
            name=f'DEC2A.BumplessBoostFreeze_{template_name}',
        )
    )
    limited_boost: Var = model.algebraic(
        'LimitedBoostPu', sym.hard_sat(frozen_boost, vdmin, vdmax), Const(0.0),
    )
    output: Var = model.algebraic('VsPu', stabilizer + limited_boost, Const(0.0))
    template: RmsModelTemplate = model.finish((output,), 'CGMES IEEE DEC2A transient boost')
    enabled_variable_name: str = f'DiscExcContIEEEDEC2A.enabled_{template_name}'
    enabled_variable: Var = vfactory.add_var(enabled_variable_name)
    template.block.event_dict[enabled_variable] = vfactory.add_const(
        value=None, name=enabled_variable_name,
    )
    template.comment = (
        'IEEE 421.5 DEC2A trigger step, TD1 lag, TD2 high-pass pulse, VD limits, '
        'digital bumpless washout freeze, and additive PSS signal. VfreezePu is an '
        'explicit host input because the CGMES RDF does not define its threshold. '
        'The remote trigger remains a host input and must be resolved from its '
        'RemoteInputSignal association during graph composition.'
    )
    return template
