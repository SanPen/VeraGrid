# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from typing import Dict, Protocol, Sequence

from VeraGridEngine.enumerations import VarPowerFlowReferenceType


class ConnectionIntentVariable(Protocol):
    """Expose the immutable variable identity required by intent parsing."""

    __slots__ = ()

    @property
    def non_mutable_uid(self) -> int:
        """Return the stable symbolic variable identifier.

        :return: Stable variable identifier.
        """
        ...


class ConnectionIntentBlock(Protocol):
    """Expose the bounded block structure required by intent parsing."""

    __slots__ = ()

    @property
    def uid(self) -> int:
        """Return the block identifier.

        :return: Stable block identifier.
        """
        ...

    @property
    def in_vars(self) -> Sequence[ConnectionIntentVariable]:
        """Return the block input variables.

        :return: Ordered input variables.
        """
        ...

    @property
    def out_vars(self) -> Sequence[ConnectionIntentVariable]:
        """Return the block output variables.

        :return: Ordered output variables.
        """
        ...

    def get_all_blocks(self) -> Sequence["ConnectionIntentBlock"]:
        """Return this block and its bounded descendants.

        :return: Ordered block traversal.
        """
        ...


class DynamicConnectionIntentOrigin(Enum):
    """
    Describe who established a dynamic root-interface connection.
    """

    USER = "USER"
    TEMPLATE_DERIVED = "TEMPLATE_DERIVED"


class DynamicConnectionIntentDirection(Enum):
    """
    Describe the direction of a dynamic root-interface connection.
    """

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class DynamicConnectionIntent:
    """
    Store the current desired state of one dynamic root-interface connection.

    The object records one effective connection state rather than an edit
    history. An active intent may remain temporarily unavailable when a phase
    disappears from the current topology and can be materialized again when
    that phase returns.
    """

    __slots__ = (
        "_origin",
        "_root_reference",
        "_direction",
        "_internal_block_uid",
        "_internal_variable_uid",
        "_suppressed",
    )

    def __init__(self,
                 origin: DynamicConnectionIntentOrigin,
                 root_reference: VarPowerFlowReferenceType,
                 direction: DynamicConnectionIntentDirection,
                 internal_block_uid: int,
                 internal_variable_uid: int,
                 suppressed: bool = False) -> None:
        """
        Initialize one connection intent.

        :param origin: Component that established the connection.
        :param root_reference: Semantic root-interface reference.
        :param direction: Connection direction at both endpoints.
        :param internal_block_uid: Stable UID of the connected internal block.
        :param internal_variable_uid: Non-mutable UID of the connected internal variable.
        :param suppressed: Whether an automatic connection is intentionally disabled.
        """
        self._origin: DynamicConnectionIntentOrigin = origin
        self._root_reference: VarPowerFlowReferenceType = root_reference
        self._direction: DynamicConnectionIntentDirection = direction
        self._internal_block_uid: int = internal_block_uid
        self._internal_variable_uid: int = internal_variable_uid
        self._suppressed: bool = suppressed

    def get_origin(self) -> DynamicConnectionIntentOrigin:
        """
        Return who established the connection.

        :return: Intent origin.
        """
        return self._origin

    def get_root_reference(self) -> VarPowerFlowReferenceType:
        """
        Return the semantic root-interface reference.

        :return: Root-interface reference.
        """
        return self._root_reference

    def set_root_reference(self, root_reference: VarPowerFlowReferenceType) -> None:
        """
        Replace a legacy root reference with its canonical reference.

        :param root_reference: Canonical root-interface reference.
        :return: None.
        """
        self._root_reference = root_reference

    def get_direction(self) -> DynamicConnectionIntentDirection:
        """
        Return the connection direction.

        :return: Connection direction.
        """
        return self._direction

    def get_internal_block_uid(self) -> int:
        """
        Return the connected internal block UID.

        :return: Internal block UID.
        """
        return self._internal_block_uid

    def get_internal_variable_uid(self) -> int:
        """
        Return the connected internal variable non-mutable UID.

        :return: Internal variable UID.
        """
        return self._internal_variable_uid

    def is_suppressed(self) -> bool:
        """
        Return whether the connection is intentionally disabled.

        :return: ``True`` when the intent must not be materialized.
        """
        return self._suppressed

    def set_suppressed(self, suppressed: bool) -> None:
        """
        Set whether the connection is intentionally disabled.

        :param suppressed: New suppression state.
        :return: None.
        """
        self._suppressed = suppressed

    def has_same_identity(self, other: "DynamicConnectionIntent") -> bool:
        """
        Compare the semantic identity used to replace an existing intent.

        :param other: Intent to compare.
        :return: ``True`` when both objects describe the same connection and origin.
        """
        if self._origin != other.get_origin():
            return False
        elif self._root_reference != other.get_root_reference():
            return False
        elif self._direction != other.get_direction():
            return False
        elif self._internal_block_uid != other.get_internal_block_uid():
            return False
        elif self._internal_variable_uid != other.get_internal_variable_uid():
            return False
        else:
            return True

    def copy(self) -> "DynamicConnectionIntent":
        """
        Create a detached copy with the same semantic state.

        :return: Copied connection intent.
        """
        return DynamicConnectionIntent(
            origin=self._origin,
            root_reference=self._root_reference,
            direction=self._direction,
            internal_block_uid=self._internal_block_uid,
            internal_variable_uid=self._internal_variable_uid,
            suppressed=self._suppressed,
        )


def dynamic_connection_intent_to_dict(intent: DynamicConnectionIntent) -> Dict[str, str | int | bool]:
    """
    Convert one typed intent at the persistence boundary.

    :param intent: Runtime connection intent.
    :return: Named JSON-compatible intent fields.
    """
    return dict({
        "origin": intent.get_origin().value,
        "root_ref": intent.get_root_reference().value,
        "direction": intent.get_direction().value,
        "internal_block_uid": intent.get_internal_block_uid(),
        "internal_variable_uid": intent.get_internal_variable_uid(),
        "suppressed": intent.is_suppressed(),
    })


def _parse_origin(value: object) -> DynamicConnectionIntentOrigin | None:
    """
    Parse one persisted origin without exposing strings to runtime code.

    :param value: Persisted candidate value.
    :return: Parsed origin or ``None`` when invalid.
    """
    if isinstance(value, str):
        try:
            result: DynamicConnectionIntentOrigin | None = DynamicConnectionIntentOrigin(value)
        except ValueError:
            result = None
    else:
        result = None
    return result


def _parse_direction(data: Dict[str, object]) -> DynamicConnectionIntentDirection | None:
    """
    Parse the current direction field or its legacy equivalents.

    :param data: Persisted intent fields.
    :return: Parsed direction or ``None`` when invalid.
    """
    direction_value: object = data.get("direction", None)

    # The internal legacy direction is authoritative because old branch files
    # could persist an incorrect graphical root direction.
    if direction_value is None:
        direction_value = data.get("internal_port_direction", data.get("root_direction", None))
    else:
        pass

    if isinstance(direction_value, str):
        try:
            result: DynamicConnectionIntentDirection | None = DynamicConnectionIntentDirection(
                direction_value.upper()
            )
        except ValueError:
            result = None
    else:
        result = None
    return result


def _parse_root_reference(value: object) -> VarPowerFlowReferenceType | None:
    """
    Parse one persisted root reference.

    :param value: Persisted reference value.
    :return: Parsed reference or ``None`` when invalid.
    """
    if isinstance(value, str):
        try:
            result: VarPowerFlowReferenceType | None = VarPowerFlowReferenceType(value)
        except ValueError:
            result = None
    else:
        result = None
    return result


def _find_internal_block(root_block: ConnectionIntentBlock,
                         internal_block_uid: int) -> ConnectionIntentBlock | None:
    """
    Locate the internal block referenced by one intent.

    :param root_block: Root block that owns the intent collection.
    :param internal_block_uid: Persisted child block UID.
    :return: Matching block or ``None`` when absent.
    """
    candidate_block: ConnectionIntentBlock

    for candidate_block in root_block.get_all_blocks():
        if candidate_block.uid == internal_block_uid:
            return candidate_block
        else:
            pass

    return None


def _resolve_internal_variable_uid(data: Dict[str, object],
                                   internal_block: ConnectionIntentBlock,
                                   direction: DynamicConnectionIntentDirection) -> int | None:
    """
    Resolve the stable variable UID, including the legacy positional format.

    :param data: Persisted intent fields.
    :param internal_block: Connected internal block.
    :param direction: Connection direction.
    :return: Non-mutable variable UID or ``None`` when the reference is invalid.
    """
    variable_uid_value: object = data.get("internal_variable_uid", None)
    port_index_value: object
    variables: Sequence[ConnectionIntentVariable]
    candidate_var: ConnectionIntentVariable

    if direction == DynamicConnectionIntentDirection.INPUT:
        variables = internal_block.in_vars
    else:
        variables = internal_block.out_vars

    if isinstance(variable_uid_value, int) and not isinstance(variable_uid_value, bool):
        for candidate_var in variables:
            if candidate_var.non_mutable_uid == variable_uid_value:
                return variable_uid_value
            else:
                pass
        return None
    else:
        pass

    port_index_value = data.get("internal_port_index", None)
    if isinstance(port_index_value, int) and not isinstance(port_index_value, bool):
        if 0 <= port_index_value < len(variables):
            return variables[port_index_value].non_mutable_uid
        else:
            return None
    else:
        return None


def dynamic_connection_intent_from_dict(data: Dict[str, object],
                                        root_block: ConnectionIntentBlock) -> DynamicConnectionIntent | None:
    """
    Build one typed intent from current or legacy persisted fields.

    :param data: Persisted intent fields.
    :param root_block: Root block used to validate internal identities.
    :return: Parsed intent or ``None`` when any required field is invalid.
    """
    origin: DynamicConnectionIntentOrigin | None = _parse_origin(data.get("origin", None))
    direction: DynamicConnectionIntentDirection | None = _parse_direction(data=data)
    root_reference: VarPowerFlowReferenceType | None = _parse_root_reference(data.get("root_ref", None))
    internal_block_uid_value: object = data.get("internal_block_uid", None)
    suppressed_value: object = data.get("suppressed", False)
    internal_block: ConnectionIntentBlock | None
    internal_variable_uid: int | None

    if origin is None or direction is None or root_reference is None:
        return None
    elif not isinstance(internal_block_uid_value, int) or isinstance(internal_block_uid_value, bool):
        return None
    elif not isinstance(suppressed_value, bool):
        return None
    else:
        pass

    internal_block = _find_internal_block(root_block=root_block,
                                          internal_block_uid=internal_block_uid_value)
    if internal_block is None:
        return None
    else:
        internal_variable_uid = _resolve_internal_variable_uid(data=data,
                                                               internal_block=internal_block,
                                                               direction=direction)

    if internal_variable_uid is None:
        return None
    else:
        return DynamicConnectionIntent(
            origin=origin,
            root_reference=root_reference,
            direction=direction,
            internal_block_uid=internal_block_uid_value,
            internal_variable_uid=internal_variable_uid,
            suppressed=suppressed_value,
        )
