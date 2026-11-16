# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Storage and class registry for CGMES Dynamics profile objects."""

from typing import Dict, List, Tuple

from VeraGridEngine.IO.cim.cgmes.base import Base
from VeraGridEngine.IO.cim.cgmes.dynamics.schema_2_4_15 import get_cgmes_24_15_dynamics_schema
from VeraGridEngine.IO.cim.cgmes.dynamics.schema import (
    DY_ASSOCIATION_INVERSES,
    DY_CLASS_DICT,
    DY_CLASS_NAMES,
)
from VeraGridEngine.enumerations import CGMESVersions


class CgmesDynamicsAssets:
    """Own typed instance lists for all CGMES Dynamics vocabulary classes."""

    __slots__ = ("class_dict", "association_inverse_dict", "lists")

    def __init__(self, cgmes_version: CGMESVersions) -> None:
        """Create the Dynamics registries for the selected CGMES edition.

        :param cgmes_version: Edition controlling version-specific class additions.
        """
        self.class_dict: Dict[str, type[Base]] = dict(DY_CLASS_DICT)
        self.association_inverse_dict: Dict[Tuple[str, str], str] = dict(DY_ASSOCIATION_INVERSES)
        self.lists: Dict[str, List[Base]] = dict()
        for class_name in DY_CLASS_NAMES:
            self.lists[class_name] = list()
        if cgmes_version == CGMESVersions.v2_4_15:
            edition_specific_absences: Tuple[str, ...] = (
                'CSCDynamics',
                'CSCUserDefined',
                'CrossCompoundTurbineGovernorDynamics',
                'ExcNI',
                'ExcRQB',
                'GovSteamBB',
                'HVDCDynamics',
                'PssRQB',
                'PssSTAB2A',
                'SVCUserDefined',
                'StaticVarCompensatorDynamics',
                'VSCDynamics',
                'VSCUserDefined',
                'WindAeroOneDimIEC',
                'WindAeroTwoDimIEC',
                'WindContQLimIEC',
                'WindContQPQULimIEC',
                'WindGenType3IEC',
                'WindGenType3aIEC',
                'WindGenType3bIEC',
                'WindGenTurbineType1aIEC',
                'WindGenTurbineType1bIEC',
                'WindPitchContPowerIEC',
                'WindPlantQcontrolModeKind',
                'WindQcontrolModeKind',
                'WindRefFrameRotIEC',
                'WindTurbineType3IEC',
                'WindTurbineType4IEC',
                'WindUVRTQcontrolModeKind',
            )
            for class_name in edition_specific_absences:
                self.class_dict.pop(class_name, None)
                self.lists.pop(class_name, None)
            for inverse_key, inverse_name in tuple(self.association_inverse_dict.items()):
                if (
                        inverse_key[0] in edition_specific_absences
                        or inverse_name.split('.')[0] in edition_specific_absences
                        or (
                            inverse_key[0] == 'WindGenTurbineType2IEC'
                            and inverse_key[1] == 'WindPitchContPowerIEC'
                        )
                        or (
                            inverse_key[0] == 'WindPitchContPowerIEC'
                            and inverse_key[1] == 'WindGenTurbineType2IEC'
                        )
                ):
                    self.association_inverse_dict.pop(inverse_key, None)
                else:
                    pass
            versioned_classes, versioned_inverses = get_cgmes_24_15_dynamics_schema()
            self.class_dict.update(versioned_classes)
            self.association_inverse_dict.update(versioned_inverses)
            for class_name in versioned_classes:
                self.lists[class_name] = list()
        else:
            pass

    def get_objects(self, class_name: str) -> List[Base]:
        """Return the typed objects of one Dynamics CIM class.

        :param class_name: CGMES Dynamics class name.
        :return: Mutable list owned by this assets container.
        """
        object_list: List[Base] | None = self.lists.get(class_name, None)
        if object_list is None:
            return list()
        else:
            return object_list
