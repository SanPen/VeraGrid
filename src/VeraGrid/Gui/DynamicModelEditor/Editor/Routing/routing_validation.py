# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.001--.0-

from __future__ import annotations

from VeraGridEngine.enumerations import RoutingValidationMessageLevel

class RoutingValidationMessage:
    """
    Store one validation message.

    :return: None.
    """

    __slots__ = ("_level", "_code", "_message", "_node_id", "_segment_id")

    def __init__(
            self,
            level: RoutingValidationMessageLevel,
            code: str,
            message: str,
            node_id: int | None,
            segment_id: int | None,
    ) -> None:
        """
        Build one validation message.

        :param level: Validation severity level.
        :param code: Stable machine-readable validation code.
        :param message: Human-readable validation message.
        :param node_id: Related node identifier or ``None``.
        :param segment_id: Related segment identifier or ``None``.
        :return: None.
        """
        self._level: RoutingValidationMessageLevel = level
        self._code: str = str(code)
        self._message: str = str(message)
        self._node_id: int | None = node_id
        self._segment_id: int | None = segment_id

    def get_level(self) -> RoutingValidationMessageLevel:
        """
        :return: Validation severity level.
        """
        return self._level

    def get_code(self) -> str:
        """
        Return the machine-readable validation code.

        :return: Validation code.
        """
        return self._code

    def get_message(self) -> str:
        """
        :return: Human-readable validation message.
        """
        return self._message

    def get_node_id(self) -> int | None:
        """
        Return the related node identifier.

        :return: Related node identifier or ``None``.
        """
        return self._node_id

    def get_segment_id(self) -> int | None:
        """
        Return the related segment identifier.

        :return: Related segment identifier or ``None``.
        """
        return self._segment_id


class RoutingValidationReport:
    """
    Store the full validation result of one routing graph.

    :return: None.
    """

    __slots__ = ("_errors", "_warnings")

    def __init__(self) -> None:
        """
        Build one empty validation report.

        :return: None.
        """
        self._errors: list[RoutingValidationMessage] = list()
        self._warnings: list[RoutingValidationMessage] = list()

    def add_message(self, message: RoutingValidationMessage) -> None:
        """
        Add one validation message to the report.

        :param message: Validation message to add.
        :return: None.
        """
        if message.get_level() == RoutingValidationMessageLevel.ERROR:
            self._errors.append(message)
        else:
            self._warnings.append(message)

    def is_valid(self) -> bool:
        """
        Return whether the validated object is valid.

        :return: ``True`` when the report contains no errors.
        """
        if len(self._errors) == 0:
            return True
        else:
            return False

    def get_errors(self) -> list[RoutingValidationMessage]:
        """
        :return: Validation errors.
        """
        return list(self._errors)

    def get_warnings(self) -> list[RoutingValidationMessage]:
        """
        :return: Validation warnings.
        """
        return list(self._warnings)
