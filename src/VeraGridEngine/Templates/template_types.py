# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Shared structural types used by template builders and their catalogue."""
from __future__ import annotations

from enum import Enum
from typing import Any, Sequence, Type, Union

from VeraGridEngine.basic_structures import Vec
from VeraGridEngine.enumerations import (
    ConverterControlType,
    IntegratorBoundSource,
    IntegratorHoldMode,
    IntegratorResetMode,
    IntegratorSaturationMode,
    IntegratorScalingMode,
    TheveninSourceVoltageMode,
    V_I_CurveSequenceType,
    WaveformSequenceType,
    WindingType,
    X_Y_SequenceType,
    X_Y_Z_Matrix,
)

TEMPLATEPROP_TYPES = Union[
    Type[int], Type[bool], Type[float], Type[str], Type[Sequence[Vec]],
    Type[ConverterControlType], Type[WindingType], Type[V_I_CurveSequenceType],
    Type[WaveformSequenceType], Type[X_Y_SequenceType], Type[X_Y_Z_Matrix],
    Type[IntegratorScalingMode], Type[IntegratorHoldMode], Type[IntegratorResetMode],
    Type[IntegratorSaturationMode], Type[IntegratorBoundSource],
    Type[TheveninSourceVoltageMode],
]


class TemplateProp:
    """Describe one editable structural input of a template builder."""

    __slots__ = ("name", "units", "descr", "tpe", "display", "editable", "value", "allowed_values")

    def __init__(
            self, name: str, units: str, descr: str, tpe: TEMPLATEPROP_TYPES,
            value: Any = None, allowed_values: Sequence[Enum] | None = None,
    ) -> None:
        """Store one template property definition.

        :param name: Stable property identifier.
        :param units: Display units.
        :param descr: User-facing property description.
        :param tpe: Runtime value type.
        :param value: Default value.
        :param allowed_values: Optional permitted enum subset.
        :return: None.
        """
        self.name = name
        self.units = units
        self.descr = descr
        self.tpe = tpe
        self.display = True
        self.editable = True
        self.value = value
        self.allowed_values = None if allowed_values is None else tuple(allowed_values)


class TemplateDefinition:
    """Base class for one editable symbolic template builder."""

    __slots__ = ("vf", "params", "params_dict")

    def __init__(self, vf: Any, params: Sequence[TemplateProp]) -> None:
        """Store the variable factory and editable properties.

        :param vf: Factory allocating the builder's symbolic variables.
        :param params: Editable structural property definitions.
        :return: None.
        """
        self.vf = vf
        self.params = list(params)
        self.params_dict = {property_definition.name: property_definition for property_definition in params}

    def get_value(self, name: str) -> Any:
        """Return the current value of one named property.

        :param name: Stable property identifier.
        :return: Property value.
        """
        property_definition: TemplateProp | None = self.params_dict.get(name, None)
        if property_definition is None:
            raise ValueError(f"Unknown parameter: {name}")
        else:
            return property_definition.value

    def eval(self) -> Any:
        """Materialize the concrete template represented by this builder.

        :return: Concrete template object.
        """
        raise NotImplementedError("Template builders must implement eval")
