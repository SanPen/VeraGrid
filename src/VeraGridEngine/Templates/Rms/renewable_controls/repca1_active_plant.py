# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native active-power path of the REPCA1/REPCTA1 plant controller."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Repca1ActivePlantSettings:
    """Store the active path's reviewed source gains, times and limits."""

    __slots__ = ('kpg', 'kig', 'tp', 'fdbd1', 'fdbd2', 'femax', 'femin',
                 'pmax', 'pmin', 'tg', 'ddn', 'dup', 'frequency_enabled')

    def __init__(self, kpg: float = 1., kig: float = 1., tp: float = .02,
                 fdbd1: float = -.001, fdbd2: float = .001,
                 femax: float = 1., femin: float = -1.,
                 pmax: float = 1.2, pmin: float = 0., tg: float = .02,
                 ddn: float = 0., dup: float = 0.,
                 frequency_enabled: bool = False) -> None:
        """Store the 35.2 J+15 through J+26 active-control fields.

        :param kpg: Active-power PI proportional gain.
        :param kig: Active-power PI integral gain.
        :param tp: Plant-power measurement filter time, seconds.
        :param fdbd1: Lower frequency-deviation deadband threshold.
        :param fdbd2: Upper frequency-deviation deadband threshold.
        :param femax: Upper active-control error limit.
        :param femin: Lower active-control error limit.
        :param pmax: Upper plant Pref limit.
        :param pmin: Lower plant Pref limit.
        :param tg: Pref output lag time, seconds.
        :param ddn: Over-frequency droop reciprocal.
        :param dup: Under-frequency droop reciprocal.
        :param frequency_enabled: Source FFLAG=1 frequency control.
        :return: None.
        """
        self.kpg: float = kpg
        self.kig: float = kig
        self.tp: float = tp
        self.fdbd1: float = fdbd1
        self.fdbd2: float = fdbd2
        self.femax: float = femax
        self.femin: float = femin
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.tg: float = tg
        self.ddn: float = ddn
        self.dup: float = dup
        self.frequency_enabled: bool = frequency_enabled


def build_repca1_active_plant_template(
        vf: VarFactory, name: str = 'REPCA1 active plant',
        settings: Repca1ActivePlantSettings | None = None,
) -> RmsModelTemplate:
    """Build filtered-power and frequency-droop PI control for plant Pref.

    The measured plant power, plant Pref, frequency and frequency reference
    are open ports. The caller must supply the correct bus/branch measurement.

    :param vf: Shared symbolic variable factory.
    :param name: Unique plant controller name.
    :param settings: Reviewed active path source fields and FFLAG.
    :return: Native plant Pref component.
    :raises ValueError: Invalid gains, limits or filter times.
    """
    selected: Repca1ActivePlantSettings = Repca1ActivePlantSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.kpg, selected.kig, selected.tp,
                                 selected.fdbd1, selected.fdbd2, selected.femax,
                                 selected.femin, selected.pmax, selected.pmin,
                                 selected.tg, selected.ddn, selected.dup)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('REPCA1 active-plant parameters must be finite')
    elif min(selected.kpg, selected.kig, selected.tp, selected.tg,
             selected.ddn, selected.dup) < 0:
        raise ValueError('REPCA1 active gains and times must be nonnegative')
    elif not selected.fdbd1 <= 0 <= selected.fdbd2:
        raise ValueError('REPCA1 frequency deadband must contain zero')
    elif not selected.femin < 0 < selected.femax or not selected.pmin < selected.pmax:
        raise ValueError('REPCA1 active-control limits are invalid')
    elif not isinstance(selected.frequency_enabled, bool):
        raise ValueError('REPCA1 FFLAG must be Boolean')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    measured_power: Var = control.input('MeasuredPlantPowerPu', Const(0.))
    plant_order: Var = control.input('PlantPowerOrderPu', measured_power)
    frequency: Var = control.input('PlantFrequencyPu', Const(1.))
    frequency_reference: Var = control.input('FrequencyReferencePu', Const(1.))
    kpg: Var = control.parameter('KPG', selected.kpg)
    kig: Var = control.parameter('KIG', selected.kig)
    tp: Var = control.parameter('TP', selected.tp)
    femax: Var = control.parameter('FEMAX', selected.femax)
    femin: Var = control.parameter('FEMIN', selected.femin)
    pmax: Var = control.parameter('PMAX', selected.pmax)
    pmin: Var = control.parameter('PMIN', selected.pmin)
    tg: Var = control.parameter('TG', selected.tg)
    filtered_power: Var = control.lag('FilteredPlantPowerPu', measured_power,
                                      tp, selected.tp, measured_power)
    frequency_correction: Expr = Const(0.)
    if selected.frequency_enabled:
        fdbd1: Var = control.parameter('FDBD1', selected.fdbd1)
        fdbd2: Var = control.parameter('FDBD2', selected.fdbd2)
        ddn: Var = control.parameter('DDN', selected.ddn)
        dup: Var = control.parameter('DUP', selected.dup)
        frequency_error: Expr = frequency_reference - frequency
        outside_deadband: Expr = (sym.min(frequency_error - fdbd1, Const(0.))
                                  + sym.max(frequency_error - fdbd2, Const(0.)))
        frequency_correction = (ddn * sym.min(outside_deadband, Const(0.))
                                + dup * sym.max(outside_deadband, Const(0.)))
    else:
        pass
    error: Expr = sym.hard_sat(plant_order - filtered_power + frequency_correction,
                               femin, femax)
    pi_memory: Var = vf.add_var('PlantPowerIntegral_' + name)
    pi_output: Var = control.algebraic(
        'PlantPowerCommandPu', sym.hard_sat(kpg * error + pi_memory, pmin, pmax),
        measured_power,
    )
    control.differential(pi_memory, kig * error, measured_power, pmin, pmax)
    pref: Var = control.lag('PlantPrefPu', pi_output, tg, selected.tg,
                             measured_power, pmin, pmax)
    return control.finish((pref,), 'REPCA1 active-power and frequency-control path')
