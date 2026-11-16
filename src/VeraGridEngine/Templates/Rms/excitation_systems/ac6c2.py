# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Two-stage brushless excitation with selectable terminal-dependent forcing limits."""
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.excitation_systems.ac6c import Ac6cParameters, build_ac6c_template


def build_ac6c2_template(vf: VarFactory, name: str | None = None,
                         parameters: Ac6cParameters | None = None) -> RmsModelTemplate:
    """Build the brushless controller with an explicit forcing-limit dependency.

    The two bounded-regulator gates, feedback and rotating field have the same
    physical equations as the base family. The supplied parameter object chooses
    whether VRMIN/VRMAX follow terminal magnitude or remain fixed; this affects
    capability during voltage excursions, not the available excitation supply.

    :param vf: Shared symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Physical coefficients and forcing-limit choice.
    :return: Native two-stage brushless controller.
    """
    return build_ac6c_template(vf,'AC6C2' if name is None else name,parameters)
