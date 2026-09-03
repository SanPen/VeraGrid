# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from typing import Callable, Tuple, Any

from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.multi_circuit import MultiCircuit


class CatalogueActionKind(Enum):
    """
    CatalogueActionKind

    This enum defines the kinds of operations supported by the catalogue selection dialog.
    """

    AddTransformerType = 1
    AddUndergroundLineType = 2
    AddWire = 3
    AddSequenceLineType = 4
    AddRmsTemplate = 5
    AddEmtTemplate = 6


class CatalogueAction:
    """
    CatalogueAction

    Lightweight action wrapper storing a kind and an explicit tuple of arguments.
    The action is executed lazily when the user accepts the dialog.
    """

    __slots__ = (
        '_kind',
        '_args',
        '_name',
        '_voltage_text',
        '_power_text',
        '_unique_key',
        '_function_ptr',
    )

    def __init__(self,
                 kind: CatalogueActionKind,
                 args: Tuple[object, ...],
                 name: str,
                 voltage_text: str,
                 power_text: str,
                 unique_key: str,
                 function_ptr: Callable[..., Any] | None = None) -> None:
        """
        Constructor.

        :param kind: Action kind.
        :param args: Explicit tuple of arguments (stored as-is).
        :param name: Display name (column 0).
        :param voltage_text: Display voltage info (column 1).
        :param power_text: Display power info (column 2).
        :param unique_key: Stable key to help avoid duplicates.
        :param function_ptr: Callable used for deferred RMS/EMT creation.
        """
        self._kind = kind
        self._args = args
        self._name = str(name)
        self._voltage_text = str(voltage_text)
        self._power_text = str(power_text)
        self._unique_key = str(unique_key)
        self._function_ptr = function_ptr

    @property
    def kind(self) -> CatalogueActionKind:
        """
        Get the action kind.

        :return: CatalogueActionKind
        """
        return self._kind

    @property
    def args(self) -> Tuple[object, ...]:
        """
        Get the action arguments.

        :return: Tuple[object, ...]
        """
        return self._args

    @property
    def name(self) -> str:
        """
        Get display name.

        :return: str
        """
        return self._name

    @property
    def voltage_text(self) -> str:
        """
        Get display voltage text.

        :return: str
        """
        return self._voltage_text

    @property
    def power_text(self) -> str:
        """
        Get display power text.

        :return: str
        """
        return self._power_text

    @property
    def unique_key(self) -> str:
        """
        Get unique key for duplication filtering.

        :return: str
        """
        return self._unique_key

    @property
    def function_ptr(self) -> Callable[..., Any] | None:
        """
        Get deferred function pointer.

        :return: Callable[..., Any] | None
        """
        return self._function_ptr

    def execute(self, circuit: MultiCircuit) -> None:
        """
        Execute the action against the provided circuit.

        :param circuit: Target circuit.
        :return: None
        """
        if self._kind == CatalogueActionKind.AddTransformerType:
            circuit.add_transformer_type(obj=self._args[0])
        elif self._kind == CatalogueActionKind.AddUndergroundLineType:
            circuit.add_underground_line(obj=self._args[0])
        elif self._kind == CatalogueActionKind.AddWire:
            circuit.add_wire(obj=self._args[0])
        elif self._kind == CatalogueActionKind.AddSequenceLineType:
            circuit.add_sequence_line(obj=self._args[0])
        elif self._kind == CatalogueActionKind.AddRmsTemplate:
            self._execute_add_rms_template(circuit=circuit)
        elif self._kind == CatalogueActionKind.AddEmtTemplate:
            self._execute_add_emt_template(circuit=circuit)
        else:
            # Unknown kind: explicit no-op.
            pass

    # ------------------------------------------------------------------------------------------------------------------
    # Concrete implementations
    # ------------------------------------------------------------------------------------------------------------------

    def _execute_add_rms_template(self, circuit: MultiCircuit) -> None:
        """
        Build and add an RMS model template.

        :param circuit: Circuit instance.
        :return: None
        """
        if self._function_ptr is None:
            obj = None
        else:
            obj = self._function_ptr(*self._args)

        if isinstance(obj, RmsModelTemplate):
            # Persist the catalogue action identity on the reusable template.
            # The display name may be edited later, while this stable code lets
            # subsequent catalogue imports recognize the original entry.
            obj.code = self._unique_key
            circuit.add_rms_model(obj)
        else:
            pass

    def _execute_add_emt_template(self, circuit: MultiCircuit) -> None:
        """
        Build and add an EMT model template.

        :param circuit: Circuit instance.
        :return: None
        """
        if self._function_ptr is None:
            obj = None
        else:
            obj = self._function_ptr(*self._args)

        if isinstance(obj, EmtModelTemplate):
            # RMS and EMT catalogue entries use the same stable-identity
            # contract so duplicate prevention is independent of display names.
            obj.code = self._unique_key
            circuit.add_emt_model(obj)
        else:
            pass
