# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Colib SM1 synchronous-machine EMT template."""

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Emt.synchronous_machines.generator_emt_type_template import get_generator_emt_type_template


def get_sm1_emt_template(vf: VarFactory, name: str = 'SM1') -> EmtModelTemplate:
    """Build the Colib SM1 physical synchronous-machine realization.

    Colib SM1 is an ABC winding model with stator, field, and damper flux
    linkages. VeraGrid's existing nine-winding EMT machine is the native
    superset: its additional damper windings retain the same physical flux
    formulation while allowing the Colib winding set to be parameterised.

    :param vf: Variable factory used to allocate symbolic variables.
    :param name: Unique template instance name.
    :return: Native EMT physical synchronous-machine template.
    """
    template: EmtModelTemplate = get_generator_emt_type_template(vf=vf, name=name)
    template.comment = 'Colib SM1 ABC winding synchronous-machine realization'
    return template
