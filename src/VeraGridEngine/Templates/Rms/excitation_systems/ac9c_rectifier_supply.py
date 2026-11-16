# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C potential-source rectifier characteristic and voltage ceiling."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac9cRectifierSupplySettings:
    """Store one AC9C source-channel loading coefficient and limit."""

    __slots__ = ('kc', 'vbmax', 'source0', 've0')

    def __init__(self, kc: float = 0.0, vbmax: float = 5.0,
                 source0: float = 1.0, ve0: float = 1.0) -> None:
        """Set channel values and its solved operating point.

        :param kc: Source-channel rectifier loading coefficient.
        :param vbmax: Maximum available voltage from this source channel.
        :param source0: Initial potential-source voltage magnitude.
        :param ve0: Initial exciter field-voltage state.
        """
        self.kc: float = kc
        self.vbmax: float = vbmax
        self.source0: float = source0
        self.ve0: float = ve0


def _ac9c_fex_value(value: float) -> float:
    """Evaluate the PSS/E five-region AC9C rectifier characteristic.

    :param value: Normalized source loading ``IN``.
    :return: Rectifier factor ``FEX(IN)``.
    """
    if value <= 0.0:
        return 1.0
    elif value <= 0.433:
        return 1.0 - 0.577 * value
    elif value <= 0.75:
        return math.sqrt(0.75 - value * value)
    elif value <= 1.0:
        return 1.732 * (1.0 - value)
    else:
        return 0.0


def build_ac9c_rectifier_supply_template(
        vf: VarFactory,
        name: str = 'AC9C rectifier source channel',
        settings: Ac9cRectifierSupplySettings | None = None,
) -> RmsModelTemplate:
    """Build one PSS/E AC9C loaded source channel with its voltage ceiling.

    PSS/E 35.2 Model Library §6.14 defines ``IN=KC*VFE/VE`` and
    ``VB=min(VBMAX, VFE*FEX(IN))`` for each of its two source channels.

    :param vf: Factory owning the block symbols.
    :param name: Unique component label.
    :param settings: Loading coefficient, cap and initialization values.
    :return: Native single-channel rectifier supply block.
    :raises ValueError: Settings are nonfinite or outside their physical domain.
    """
    selected: Ac9cRectifierSupplySettings = (
        Ac9cRectifierSupplySettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.kc, selected.vbmax, selected.source0, selected.ve0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC9C rectifier supply settings must be finite')
    elif selected.kc < 0.0 or selected.vbmax <= 0.0 or selected.source0 < 0.0:
        raise ValueError('AC9C rectifier supply coefficient, source and cap are invalid')
    elif selected.ve0 <= 0.0:
        raise ValueError('AC9C rectifier supply initialization requires positive VE')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    loading: Var = control.parameter('KC', selected.kc)
    maximum: Var = control.parameter('VBMAX', selected.vbmax)
    source_voltage: Var = control.input('SourceVoltagePu', Const(selected.source0))
    exciter_voltage: Var = control.input('ExciterVoltagePu', Const(selected.ve0))
    normalized_loading: Expr = sym.safe_divide(
        loading * source_voltage, exciter_voltage, Const(1.0),
    )
    supply_expression: Expr = sym.min(
        maximum, source_voltage * _esst3a_fex(normalized_loading),
    )
    loading0: float = selected.kc * selected.source0 / selected.ve0
    output0: float = min(
        selected.vbmax, selected.source0 * _ac9c_fex_value(loading0),
    )
    supply: Var = control.algebraic('AvailableVoltagePu', supply_expression, Const(output0))
    return control.finish((supply,), 'AC9C loaded potential-source rectifier channel')
