# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC9C compensated-voltage transducer stage."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Var


def build_ac9c_voltage_transducer_template(
        vf: VarFactory,
        name: str = 'AC9C voltage transducer',
        tr: float = 0.01,
        ecomp0: float = 1.0,
) -> RmsModelTemplate:
    """Build the source's first-order filter from ECOMP to sensed voltage.

    :param vf: Symbol factory owning this transducer.
    :param name: Unique component label.
    :param tr: Voltage-measurement time constant in seconds.
    :param ecomp0: Solved initial compensated terminal voltage.
    :return: Transducer component with output ``SensedVoltagePu``.
    :raises ValueError: Time or initial voltage is nonfinite or invalid.
    """
    if not math.isfinite(tr) or not math.isfinite(ecomp0) or tr < 0.0:
        raise ValueError('AC9C transducer settings must be finite with TR nonnegative')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    time: Var = control.parameter('TR', tr)
    compensated_voltage: Var = control.input('EcompPu', Const(ecomp0))
    sensed_voltage: Var = control.lag(
        'SensedVoltagePu', compensated_voltage, time, tr, Const(ecomp0),
    )
    return control.finish((sensed_voltage,), 'AC9C compensated-voltage transducer')
