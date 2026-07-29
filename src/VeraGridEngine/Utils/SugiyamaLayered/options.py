# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Option handling for the Sugiyama layered pipeline.

The layout package keeps one explicit registry of supported options so the
phases can resolve graph and element configuration deterministically.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class LayoutAlgorithm(Enum):
    """Supported layout algorithms."""

    LAYERED = "LAYERED"


class LayoutDirection(Enum):
    """Supported layout directions."""

    UNDEFINED = "UNDEFINED"
    RIGHT = "RIGHT"
    LEFT = "LEFT"
    DOWN = "DOWN"
    UP = "UP"


class EdgeRoutingMode(Enum):
    """Supported edge-routing modes."""

    ORTHOGONAL = "ORTHOGONAL"
    POLYLINE = "POLYLINE"
    SPLINES = "SPLINES"


class LayeringStrategy(Enum):
    """Supported layering strategies."""

    NETWORK_SIMPLEX = "NETWORK_SIMPLEX"
    INTERACTIVE = "INTERACTIVE"
    LONGEST_PATH = "LONGEST_PATH"
    LONGEST_PATH_SOURCE = "LONGEST_PATH_SOURCE"


class CycleBreakingStrategy(Enum):
    """Supported cycle-breaking strategies."""

    GREEDY = "GREEDY"
    NONE = "NONE"


class NodePlacementStrategy(Enum):
    """Supported node-placement strategies."""

    BRANDES_KOEPF = "BRANDES_KOEPF"
    NONE = "NONE"


class FixedAlignment(Enum):
    """Supported fixed-alignment modes for Brandes-Koepf."""

    NONE = "NONE"
    LEFT_UP = "LEFT_UP"
    RIGHT_UP = "RIGHT_UP"
    LEFT_DOWN = "LEFT_DOWN"
    RIGHT_DOWN = "RIGHT_DOWN"


class CrossingMinimizationStrategy(Enum):
    """Supported crossing-minimization strategies."""

    LAYER_SWEEP = "LAYER_SWEEP"
    NONE = "NONE"


class PortConstraint(Enum):
    """Supported port-constraint modes."""

    UNDEFINED = "UNDEFINED"
    FIXED_ORDER = "FIXED_ORDER"
    FIXED_SIDE = "FIXED_SIDE"
    FIXED_POS = "FIXED_POS"
    FIXED_RATIO = "FIXED_RATIO"


class PortSide(Enum):
    """Supported port sides."""

    UNDEFINED = "UNDEFINED"
    WEST = "WEST"
    EAST = "EAST"
    NORTH = "NORTH"
    SOUTH = "SOUTH"


class PortAlignment(Enum):
    """Supported port-alignment modes."""

    BEGIN = "BEGIN"
    CENTER = "CENTER"
    END = "END"


class ConsiderModelOrderStrategy(Enum):
    """Supported model-order preference modes."""

    NONE = "NONE"
    NODES = "NODES"
    NODES_AND_EDGES = "NODES_AND_EDGES"
    PREFER_NODES = "PREFER_NODES"


class SelfLoopDistribution(Enum):
    """Supported self-loop distribution policies."""

    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"


def _normalize_enum_token(value: str) -> str:
    """Normalize a string token so it can be matched against enum names.

    :param value: Raw string token.
    :type value: str
    :return: Normalized enum token.
    :rtype: str
    """
    normalized_value: str = value.strip().upper().replace("-", "_").replace(" ", "_")
    return normalized_value


def _enum_member_from_value(enum_tpe: type[Enum], value: Any) -> Enum | None:
    """Resolve an enum member from a raw value.

    :param enum_tpe: Enum type to resolve.
    :type enum_tpe: type[Enum]
    :param value: Raw candidate value.
    :type value: Any
    :return: Resolved enum member or ``None``.
    :rtype: Enum | None
    """
    member: Enum | None = None
    normalized_token: str

    if isinstance(value, enum_tpe):
        member = value
    else:
        if isinstance(value, str):
            normalized_token = _normalize_enum_token(value)
            member = enum_tpe.__members__.get(normalized_token, None)
        else:
            member = None

    return member


def coerce_enum_value(enum_tpe: type[Enum], value: Any, default: Enum) -> Enum:
    """Coerce one raw value to an enum member with fallback.

    :param enum_tpe: Enum type to resolve.
    :type enum_tpe: type[Enum]
    :param value: Raw candidate value.
    :type value: Any
    :param default: Fallback enum member.
    :type default: Enum
    :return: Resolved enum member.
    :rtype: Enum
    """
    member: Enum | None = _enum_member_from_value(enum_tpe, value)
    resolved_member: Enum = default

    if member is not None:
        resolved_member = member
    else:
        resolved_member = default

    return resolved_member


class OptionDefinition:
    """One supported layout option definition.

    :param identifier: Unique option identifier.
    :type identifier: str
    :param default: Default option value.
    :type default: Any
    :param value_type: Accepted Python type or tuple of types.
    :type value_type: type | tuple[type, ...]
    :param applies_to: Primitive kinds where the option is meaningful.
    :type applies_to: tuple[str, ...]
    :param enum_tpe: Optional enum type used to normalize the option value.
    :type enum_tpe: type[Enum] | None
    """

    __slots__ = ("_identifier", "_default", "_value_type", "_applies_to", "_enum_tpe")

    def __init__(
            self,
            identifier: str,
            default: Any,
            value_type: type | tuple[type, ...],
            applies_to: tuple[str, ...],
            enum_tpe: type[Enum] | None = None,
    ) -> None:
        self._identifier: str = identifier
        self._default: Any = default
        self._value_type: type | tuple[type, ...] = value_type
        self._applies_to: tuple[str, ...] = applies_to
        self._enum_tpe: type[Enum] | None = enum_tpe

    @property
    def identifier(self) -> str:
        """Return the option identifier.

        :return: Option identifier.
        :rtype: str
        """
        return self._identifier

    @property
    def default(self) -> Any:
        """Return the default option value.

        :return: Default option value.
        :rtype: Any
        """
        return self._default

    @property
    def value_type(self) -> type | tuple[type, ...]:
        """Return the accepted Python type.

        :return: Accepted type or tuple of types.
        :rtype: type | tuple[type, ...]
        """
        return self._value_type

    @property
    def applies_to(self) -> tuple[str, ...]:
        """Return the supported primitive kinds.

        :return: Supported primitive kinds.
        :rtype: tuple[str, ...]
        """
        return self._applies_to

    @property
    def enum_tpe(self) -> type[Enum] | None:
        """Return the enum type used for normalization.

        :return: Enum type or ``None``.
        :rtype: type[Enum] | None
        """
        return self._enum_tpe

    def normalize_value(self, value: Any) -> Any:
        """Normalize one raw option value.

        :param value: Raw value to normalize.
        :type value: Any
        :return: Normalized value.
        :rtype: Any
        """
        normalized_value: Any = value
        member: Enum | None

        if self._enum_tpe is not None:
            normalized_value = coerce_enum_value(self._enum_tpe, value, self._default)
        else:
            normalized_value = value

        return normalized_value


def build_default_option_registry() -> dict[str, OptionDefinition]:
    """Build the default option registry.

    :return: Default option definitions indexed by identifier.
    :rtype: dict[str, OptionDefinition]
    """
    registry: dict[str, OptionDefinition] = dict()

    registry["org.vera.sugiyama.algorithm"] = OptionDefinition(
        identifier="org.vera.sugiyama.algorithm",
        default=LayoutAlgorithm.LAYERED,
        value_type=(LayoutAlgorithm, str),
        applies_to=("graph",),
        enum_tpe=LayoutAlgorithm,
    )
    registry["org.vera.sugiyama.direction"] = OptionDefinition(
        identifier="org.vera.sugiyama.direction",
        default=LayoutDirection.UNDEFINED,
        value_type=(LayoutDirection, str),
        applies_to=("graph", "node"),
        enum_tpe=LayoutDirection,
    )
    registry["org.vera.sugiyama.edgeRouting"] = OptionDefinition(
        identifier="org.vera.sugiyama.edgeRouting",
        default=EdgeRoutingMode.ORTHOGONAL,
        value_type=(EdgeRoutingMode, str),
        applies_to=("graph",),
        enum_tpe=EdgeRoutingMode,
    )
    registry["org.vera.sugiyama.spacing.nodeNode"] = OptionDefinition(
        identifier="org.vera.sugiyama.spacing.nodeNode",
        default=20.0,
        value_type=(int, float),
        applies_to=("graph", "node"),
    )
    registry["org.vera.sugiyama.spacing.componentComponent"] = OptionDefinition(
        identifier="org.vera.sugiyama.spacing.componentComponent",
        default=40.0,
        value_type=(int, float),
        applies_to=("graph",),
    )
    registry["org.vera.sugiyama.layered.spacing.nodeNodeBetweenLayers"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.spacing.nodeNodeBetweenLayers",
        default=20.0,
        value_type=(int, float),
        applies_to=("graph",),
    )
    registry["org.vera.sugiyama.layered.layering.strategy"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.layering.strategy",
        default=LayeringStrategy.NETWORK_SIMPLEX,
        value_type=(LayeringStrategy, str),
        applies_to=("graph",),
        enum_tpe=LayeringStrategy,
    )
    registry["org.vera.sugiyama.layered.cycleBreaking.strategy"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.cycleBreaking.strategy",
        default=CycleBreakingStrategy.GREEDY,
        value_type=(CycleBreakingStrategy, str),
        applies_to=("graph",),
        enum_tpe=CycleBreakingStrategy,
    )
    registry["org.vera.sugiyama.layered.nodePlacement.strategy"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.nodePlacement.strategy",
        default=NodePlacementStrategy.BRANDES_KOEPF,
        value_type=(NodePlacementStrategy, str),
        applies_to=("graph",),
        enum_tpe=NodePlacementStrategy,
    )
    registry["org.vera.sugiyama.layered.nodePlacement.bk.fixedAlignment"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.nodePlacement.bk.fixedAlignment",
        default=FixedAlignment.NONE,
        value_type=(FixedAlignment, str),
        applies_to=("graph",),
        enum_tpe=FixedAlignment,
    )
    registry["org.vera.sugiyama.layered.crossingMinimization.strategy"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.crossingMinimization.strategy",
        default=CrossingMinimizationStrategy.LAYER_SWEEP,
        value_type=(CrossingMinimizationStrategy, str),
        applies_to=("graph",),
        enum_tpe=CrossingMinimizationStrategy,
    )
    registry["org.vera.sugiyama.portConstraints"] = OptionDefinition(
        identifier="org.vera.sugiyama.portConstraints",
        default=PortConstraint.UNDEFINED,
        value_type=(PortConstraint, str),
        applies_to=("node",),
        enum_tpe=PortConstraint,
    )
    registry["org.vera.sugiyama.port.side"] = OptionDefinition(
        identifier="org.vera.sugiyama.port.side",
        default=PortSide.UNDEFINED,
        value_type=(PortSide, str),
        applies_to=("port",),
        enum_tpe=PortSide,
    )
    registry["org.vera.sugiyama.portAlignment.default"] = OptionDefinition(
        identifier="org.vera.sugiyama.portAlignment.default",
        default=PortAlignment.CENTER,
        value_type=(PortAlignment, str),
        applies_to=("graph", "node"),
        enum_tpe=PortAlignment,
    )
    registry["org.vera.sugiyama.portAlignment.west"] = OptionDefinition(
        identifier="org.vera.sugiyama.portAlignment.west",
        default=PortAlignment.CENTER,
        value_type=(PortAlignment, str),
        applies_to=("graph", "node"),
        enum_tpe=PortAlignment,
    )
    registry["org.vera.sugiyama.portAlignment.east"] = OptionDefinition(
        identifier="org.vera.sugiyama.portAlignment.east",
        default=PortAlignment.CENTER,
        value_type=(PortAlignment, str),
        applies_to=("graph", "node"),
        enum_tpe=PortAlignment,
    )
    registry["org.vera.sugiyama.portAlignment.north"] = OptionDefinition(
        identifier="org.vera.sugiyama.portAlignment.north",
        default=PortAlignment.CENTER,
        value_type=(PortAlignment, str),
        applies_to=("graph", "node"),
        enum_tpe=PortAlignment,
    )
    registry["org.vera.sugiyama.portAlignment.south"] = OptionDefinition(
        identifier="org.vera.sugiyama.portAlignment.south",
        default=PortAlignment.CENTER,
        value_type=(PortAlignment, str),
        applies_to=("graph", "node"),
        enum_tpe=PortAlignment,
    )
    registry["org.vera.sugiyama.layered.considerModelOrder.strategy"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.considerModelOrder.strategy",
        default=ConsiderModelOrderStrategy.NONE,
        value_type=(ConsiderModelOrderStrategy, str),
        applies_to=("graph",),
        enum_tpe=ConsiderModelOrderStrategy,
    )
    registry["org.vera.sugiyama.layered.edgeRouting.selfLoopDistribution"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.edgeRouting.selfLoopDistribution",
        default=SelfLoopDistribution.NORTH,
        value_type=(SelfLoopDistribution, str),
        applies_to=("graph",),
        enum_tpe=SelfLoopDistribution,
    )
    registry["org.vera.sugiyama.layered.feedbackEdges"] = OptionDefinition(
        identifier="org.vera.sugiyama.layered.feedbackEdges",
        default=False,
        value_type=(bool, str),
        applies_to=("graph",),
    )

    return registry


class SugiyamaOptionResolver:
    """Resolve and validate layered layout options.

    :param registry: Optional custom option registry.
    :type registry: dict[str, OptionDefinition] | None
    """

    __slots__ = ("_registry",)

    def __init__(self, registry: dict[str, OptionDefinition] | None = None) -> None:
        if registry is None:
            self._registry: dict[str, OptionDefinition] = build_default_option_registry()
        else:
            self._registry = dict(registry)

    def validate(self, option_id: str, value: Any) -> bool:
        """Validate one option value against the registry.

        :param option_id: Option identifier to validate.
        :type option_id: str
        :param value: Candidate value.
        :type value: Any
        :return: ``True`` when the value is acceptable.
        :rtype: bool
        """
        definition: OptionDefinition | None = self._registry.get(option_id, None)

        if definition is None:
            return True
        else:
            if definition.enum_tpe is not None:
                if _enum_member_from_value(definition.enum_tpe, value) is not None:
                    return True
                else:
                    return False
            else:
                if isinstance(value, definition.value_type):
                    return True
                else:
                    if isinstance(value, str) and definition.value_type == (int, float):
                        try:
                            float(value)
                        except ValueError:
                            return False
                        else:
                            return True
                    else:
                        return False

    def resolve_for_element(
            self,
            graph_options: dict[str, Any],
            element_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve options for one graph element.

        The algorithm starts from registry defaults, then applies graph-level
        overrides, and finally element-specific overrides. The precedence must
        be explicit because all phases inspect the resolved values repeatedly.

        :param graph_options: Graph-level option overrides.
        :type graph_options: dict[str, Any]
        :param element_options: Element-specific option overrides.
        :type element_options: dict[str, Any] | None
        :return: Resolved option dictionary.
        :rtype: dict[str, Any]
        """
        resolved: dict[str, Any] = dict()
        option_id: str
        definition: OptionDefinition

        for option_id, definition in self._registry.items():
            resolved[option_id] = definition.default

        resolved.update(graph_options)
        if element_options is None:
            pass
        else:
            resolved.update(element_options)

        for option_id, definition in self._registry.items():
            resolved[option_id] = definition.normalize_value(resolved[option_id])

        return resolved
