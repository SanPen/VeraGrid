# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Core graph model for the Sugiyama layered layout pipeline.

This module stores the graph primitives manipulated by the layout phases.
The classes are intentionally light and explicit so the pipeline can inspect
and mutate coordinates without hidden behavior.
"""

from __future__ import annotations

from typing import Any


PrimitiveId = str


class SugiyamaPrimitive:
    """Base graph primitive shared by all Sugiyama model elements.

    :param identifier: Stable primitive identifier.
    :type identifier: PrimitiveId
    :param layout_options: Layout options attached to this primitive.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional user-defined properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_identifier", "_layout_options", "_properties")

    def __init__(
            self,
            identifier: PrimitiveId,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        layout_options_data: dict[str, Any]
        properties_data: dict[str, Any]

        if layout_options is None:
            layout_options_data = dict()
        else:
            layout_options_data = dict(layout_options)

        if properties is None:
            properties_data = dict()
        else:
            properties_data = dict(properties)

        self._identifier: PrimitiveId = identifier
        self._layout_options: dict[str, Any] = layout_options_data
        self._properties: dict[str, Any] = properties_data

    @property
    def identifier(self) -> PrimitiveId:
        """Return the primitive identifier.

        :return: Primitive identifier.
        :rtype: PrimitiveId
        """
        return self._identifier

    @property
    def layout_options(self) -> dict[str, Any]:
        """Return the layout options dictionary.

        The layout engine reads the dictionary directly during the pipeline, so
        the object keeps ownership of the storage and exposes it explicitly.

        :return: Layout options storage.
        :rtype: dict[str, Any]
        """
        return self._layout_options

    @property
    def properties(self) -> dict[str, Any]:
        """Return the additional properties dictionary.

        :return: Additional properties storage.
        :rtype: dict[str, Any]
        """
        return self._properties

    def get_layout_option(self, option_id: str, default: Any = None) -> Any:
        """Return one layout option value.

        :param option_id: Layout option identifier.
        :type option_id: str
        :param default: Fallback value when the option does not exist.
        :type default: Any
        :return: Stored value or fallback.
        :rtype: Any
        """
        return self._layout_options.get(option_id, default)

    def set_layout_option(self, option_id: str, value: Any) -> None:
        """Store one layout option value.

        :param option_id: Layout option identifier.
        :type option_id: str
        :param value: Value to store.
        :type value: Any
        :return: None.
        :rtype: None
        """
        self._layout_options[option_id] = value

    def get_property(self, property_id: str, default: Any = None) -> Any:
        """Return one custom property value.

        :param property_id: Property identifier.
        :type property_id: str
        :param default: Fallback value when the property does not exist.
        :type default: Any
        :return: Stored value or fallback.
        :rtype: Any
        """
        return self._properties.get(property_id, default)

    def set_property(self, property_id: str, value: Any) -> None:
        """Store one custom property value.

        :param property_id: Property identifier.
        :type property_id: str
        :param value: Value to store.
        :type value: Any
        :return: None.
        :rtype: None
        """
        self._properties[property_id] = value


class SugiyamaLabel(SugiyamaPrimitive):
    """Text label attached to one graph primitive.

    :param identifier: Label identifier.
    :type identifier: PrimitiveId
    :param text: Label text.
    :type text: str
    :param width: Label width.
    :type width: float
    :param height: Label height.
    :type height: float
    :param x: Optional x coordinate.
    :type x: float | None
    :param y: Optional y coordinate.
    :type y: float | None
    :param layout_options: Layout options attached to the label.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional label properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_text", "_width", "_height", "_x", "_y")

    def __init__(
            self,
            identifier: PrimitiveId,
            text: str = "",
            width: float = 0.0,
            height: float = 0.0,
            x: float | None = None,
            y: float | None = None,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(identifier=identifier, layout_options=layout_options, properties=properties)
        self._text: str = text
        self._width: float = width
        self._height: float = height
        self._x: float | None = x
        self._y: float | None = y

    @property
    def text(self) -> str:
        """Return the label text.

        :return: Label text.
        :rtype: str
        """
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set the label text.

        :param value: New label text.
        :type value: str
        """
        self._text = value

    @property
    def width(self) -> float:
        """Return the label width.

        :return: Label width.
        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        """Set the label width.

        :param value: New width.
        :type value: float
        """
        self._width = value

    @property
    def height(self) -> float:
        """Return the label height.

        :return: Label height.
        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        """Set the label height.

        :param value: New height.
        :type value: float
        """
        self._height = value

    @property
    def x(self) -> float | None:
        """Return the x coordinate.

        :return: X coordinate.
        :rtype: float | None
        """
        return self._x

    @x.setter
    def x(self, value: float | None) -> None:
        """Set the x coordinate.

        :param value: New x coordinate.
        :type value: float | None
        """
        self._x = value

    @property
    def y(self) -> float | None:
        """Return the y coordinate.

        :return: Y coordinate.
        :rtype: float | None
        """
        return self._y

    @y.setter
    def y(self, value: float | None) -> None:
        """Set the y coordinate.

        :param value: New y coordinate.
        :type value: float | None
        """
        self._y = value


class SugiyamaPort(SugiyamaPrimitive):
    """Port attached to one node.

    :param identifier: Port identifier.
    :type identifier: PrimitiveId
    :param width: Port width.
    :type width: float
    :param height: Port height.
    :type height: float
    :param x: Optional x coordinate.
    :type x: float | None
    :param y: Optional y coordinate.
    :type y: float | None
    :param labels: Labels attached to the port.
    :type labels: list[SugiyamaLabel] | None
    :param layout_options: Layout options attached to the port.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional port properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_width", "_height", "_x", "_y", "_labels")

    def __init__(
            self,
            identifier: PrimitiveId,
            width: float = 0.0,
            height: float = 0.0,
            x: float | None = None,
            y: float | None = None,
            labels: list[SugiyamaLabel] | None = None,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        labels_data: list[SugiyamaLabel]

        super().__init__(identifier=identifier, layout_options=layout_options, properties=properties)
        if labels is None:
            labels_data = list()
        else:
            labels_data = list(labels)

        self._width: float = width
        self._height: float = height
        self._x: float | None = x
        self._y: float | None = y
        self._labels: list[SugiyamaLabel] = labels_data

    @property
    def width(self) -> float:
        """Return the port width.

        :return: Port width.
        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        """Set the port width.

        :param value: New width.
        :type value: float
        """
        self._width = value

    @property
    def height(self) -> float:
        """Return the port height.

        :return: Port height.
        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        """Set the port height.

        :param value: New height.
        :type value: float
        """
        self._height = value

    @property
    def x(self) -> float | None:
        """Return the x coordinate.

        :return: X coordinate.
        :rtype: float | None
        """
        return self._x

    @x.setter
    def x(self, value: float | None) -> None:
        """Set the x coordinate.

        :param value: New x coordinate.
        :type value: float | None
        """
        self._x = value

    @property
    def y(self) -> float | None:
        """Return the y coordinate.

        :return: Y coordinate.
        :rtype: float | None
        """
        return self._y

    @y.setter
    def y(self, value: float | None) -> None:
        """Set the y coordinate.

        :param value: New y coordinate.
        :type value: float | None
        """
        self._y = value

    @property
    def labels(self) -> list[SugiyamaLabel]:
        """Return the labels attached to the port.

        :return: Port labels.
        :rtype: list[SugiyamaLabel]
        """
        return self._labels

    def append_label(self, label: SugiyamaLabel) -> None:
        """Append one label to the port.

        :param label: Label to append.
        :type label: SugiyamaLabel
        :return: None.
        :rtype: None
        """
        self._labels.append(label)

    def clear_labels(self) -> None:
        """Remove all labels from the port.

        :return: None.
        :rtype: None
        """
        self._labels.clear()


class SugiyamaNode(SugiyamaPrimitive):
    """Node manipulated by the layered layout pipeline.

    :param identifier: Node identifier.
    :type identifier: PrimitiveId
    :param width: Node width.
    :type width: float
    :param height: Node height.
    :type height: float
    :param x: Optional x coordinate.
    :type x: float | None
    :param y: Optional y coordinate.
    :type y: float | None
    :param labels: Node labels.
    :type labels: list[SugiyamaLabel] | None
    :param ports: Node ports.
    :type ports: list[SugiyamaPort] | None
    :param children: Child nodes for hierarchical graphs.
    :type children: list[SugiyamaNode] | None
    :param parent: Parent identifier.
    :type parent: PrimitiveId | None
    :param layout_options: Layout options attached to the node.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional node properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_width", "_height", "_x", "_y", "_labels", "_ports", "_children", "_parent")

    def __init__(
            self,
            identifier: PrimitiveId,
            width: float = 0.0,
            height: float = 0.0,
            x: float | None = None,
            y: float | None = None,
            labels: list[SugiyamaLabel] | None = None,
            ports: list[SugiyamaPort] | None = None,
            children: list[SugiyamaNode] | None = None,
            parent: PrimitiveId | None = None,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        labels_data: list[SugiyamaLabel]
        ports_data: list[SugiyamaPort]
        children_data: list[SugiyamaNode]

        super().__init__(identifier=identifier, layout_options=layout_options, properties=properties)

        if labels is None:
            labels_data = list()
        else:
            labels_data = list(labels)

        if ports is None:
            ports_data = list()
        else:
            ports_data = list(ports)

        if children is None:
            children_data = list()
        else:
            children_data = list(children)

        self._width: float = width
        self._height: float = height
        self._x: float | None = x
        self._y: float | None = y
        self._labels: list[SugiyamaLabel] = labels_data
        self._ports: list[SugiyamaPort] = ports_data
        self._children: list[SugiyamaNode] = children_data
        self._parent: PrimitiveId | None = parent

    @property
    def width(self) -> float:
        """Return the node width.

        :return: Node width.
        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        """Set the node width.

        :param value: New width.
        :type value: float
        """
        self._width = value

    @property
    def height(self) -> float:
        """Return the node height.

        :return: Node height.
        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        """Set the node height.

        :param value: New height.
        :type value: float
        """
        self._height = value

    @property
    def x(self) -> float | None:
        """Return the x coordinate.

        :return: X coordinate.
        :rtype: float | None
        """
        return self._x

    @x.setter
    def x(self, value: float | None) -> None:
        """Set the x coordinate.

        :param value: New x coordinate.
        :type value: float | None
        """
        self._x = value

    @property
    def y(self) -> float | None:
        """Return the y coordinate.

        :return: Y coordinate.
        :rtype: float | None
        """
        return self._y

    @y.setter
    def y(self, value: float | None) -> None:
        """Set the y coordinate.

        :param value: New y coordinate.
        :type value: float | None
        """
        self._y = value

    @property
    def labels(self) -> list[SugiyamaLabel]:
        """Return the node labels.

        :return: Node labels.
        :rtype: list[SugiyamaLabel]
        """
        return self._labels

    @property
    def ports(self) -> list[SugiyamaPort]:
        """Return the node ports.

        :return: Node ports.
        :rtype: list[SugiyamaPort]
        """
        return self._ports

    @property
    def children(self) -> list[SugiyamaNode]:
        """Return the child nodes.

        :return: Child nodes.
        :rtype: list[SugiyamaNode]
        """
        return self._children

    @children.setter
    def children(self, value: list[SugiyamaNode]) -> None:
        """Replace the child node list.

        :param value: New child node list.
        :type value: list[SugiyamaNode]
        """
        self._children = value

    def append_label(self, label: SugiyamaLabel) -> None:
        """Append one label to the node.

        :param label: Label to append.
        :type label: SugiyamaLabel
        :return: None.
        :rtype: None
        """
        self._labels.append(label)

    def clear_labels(self) -> None:
        """Remove all labels from the node.

        :return: None.
        :rtype: None
        """
        self._labels.clear()

    def append_port(self, port: SugiyamaPort) -> None:
        """Append one port to the node.

        :param port: Port to append.
        :type port: SugiyamaPort
        :return: None.
        :rtype: None
        """
        self._ports.append(port)

    def clear_ports(self) -> None:
        """Remove all ports from the node.

        :return: None.
        :rtype: None
        """
        self._ports.clear()

    def append_child(self, child: SugiyamaNode) -> None:
        """Append one child to the node.

        :param child: Child node to append.
        :type child: SugiyamaNode
        :return: None.
        :rtype: None
        """
        self._children.append(child)

    def set_children(self, children: list[SugiyamaNode]) -> None:
        """Replace the child list explicitly.

        :param children: New child nodes.
        :type children: list[SugiyamaNode]
        :return: None.
        :rtype: None
        """
        self._children = list(children)

    def clear_children(self) -> None:
        """Remove all child nodes.

        :return: None.
        :rtype: None
        """
        self._children.clear()

    @property
    def parent(self) -> PrimitiveId | None:
        """Return the parent identifier.

        :return: Parent identifier.
        :rtype: PrimitiveId | None
        """
        return self._parent

    @parent.setter
    def parent(self, value: PrimitiveId | None) -> None:
        """Set the parent identifier.

        :param value: New parent identifier.
        :type value: PrimitiveId | None
        """
        self._parent = value

    def iter_descendants(self) -> list[SugiyamaNode]:
        """Return the descendants of this node in breadth-first order.

        The traversal expands children explicitly so phases that need stable
        hierarchy flattening get one deterministic order.

        :return: Descendant nodes.
        :rtype: list[SugiyamaNode]
        """
        result: list[SugiyamaNode] = list()
        queue: list[SugiyamaNode] = list(self._children)

        while len(queue) > 0:
            child: SugiyamaNode = queue.pop(0)
            result.append(child)
            if len(child.children) > 0:
                queue[0:0] = child.children
            else:
                pass

        return result


class SugiyamaEdgeSection:
    """One routed section of an edge.

    :param start_point: Section start point.
    :type start_point: tuple[float, float] | None
    :param end_point: Section end point.
    :type end_point: tuple[float, float] | None
    :param bend_points: Intermediate bend points.
    :type bend_points: list[tuple[float, float]] | None
    """

    __slots__ = ("_start_point", "_end_point", "_bend_points")

    def __init__(
            self,
            start_point: tuple[float, float] | None = None,
            end_point: tuple[float, float] | None = None,
            bend_points: list[tuple[float, float]] | None = None,
    ) -> None:
        bend_points_data: list[tuple[float, float]]

        if bend_points is None:
            bend_points_data = list()
        else:
            bend_points_data = list(bend_points)

        self._start_point: tuple[float, float] | None = start_point
        self._end_point: tuple[float, float] | None = end_point
        self._bend_points: list[tuple[float, float]] = bend_points_data

    @property
    def start_point(self) -> tuple[float, float] | None:
        """Return the section start point.

        :return: Start point.
        :rtype: tuple[float, float] | None
        """
        return self._start_point

    @start_point.setter
    def start_point(self, value: tuple[float, float] | None) -> None:
        """Set the section start point.

        :param value: New start point.
        :type value: tuple[float, float] | None
        """
        self._start_point = value

    @property
    def end_point(self) -> tuple[float, float] | None:
        """Return the section end point.

        :return: End point.
        :rtype: tuple[float, float] | None
        """
        return self._end_point

    @end_point.setter
    def end_point(self, value: tuple[float, float] | None) -> None:
        """Set the section end point.

        :param value: New end point.
        :type value: tuple[float, float] | None
        """
        self._end_point = value

    @property
    def bend_points(self) -> list[tuple[float, float]]:
        """Return the bend points.

        :return: Bend points.
        :rtype: list[tuple[float, float]]
        """
        return self._bend_points

    def append_bend_point(self, point: tuple[float, float]) -> None:
        """Append one bend point.

        :param point: Bend point to append.
        :type point: tuple[float, float]
        :return: None.
        :rtype: None
        """
        self._bend_points.append(point)

    def extend_bend_points(self, points: list[tuple[float, float]]) -> None:
        """Append several bend points.

        :param points: Bend points to append.
        :type points: list[tuple[float, float]]
        :return: None.
        :rtype: None
        """
        self._bend_points.extend(points)

    def clear_bend_points(self) -> None:
        """Remove all bend points.

        :return: None.
        :rtype: None
        """
        self._bend_points.clear()


class SugiyamaEdge(SugiyamaPrimitive):
    """Directed edge between one or more endpoints.

    :param identifier: Edge identifier.
    :type identifier: PrimitiveId
    :param sources: Source endpoint identifiers.
    :type sources: list[PrimitiveId] | None
    :param targets: Target endpoint identifiers.
    :type targets: list[PrimitiveId] | None
    :param labels: Edge labels.
    :type labels: list[SugiyamaLabel] | None
    :param sections: Routed sections.
    :type sections: list[SugiyamaEdgeSection] | None
    :param layout_options: Layout options attached to the edge.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional edge properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_sources", "_targets", "_labels", "_sections")

    def __init__(
            self,
            identifier: PrimitiveId,
            sources: list[PrimitiveId] | None = None,
            targets: list[PrimitiveId] | None = None,
            labels: list[SugiyamaLabel] | None = None,
            sections: list[SugiyamaEdgeSection] | None = None,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        sources_data: list[PrimitiveId]
        targets_data: list[PrimitiveId]
        labels_data: list[SugiyamaLabel]
        sections_data: list[SugiyamaEdgeSection]

        super().__init__(identifier=identifier, layout_options=layout_options, properties=properties)

        if sources is None:
            sources_data = list()
        else:
            sources_data = list(sources)

        if targets is None:
            targets_data = list()
        else:
            targets_data = list(targets)

        if labels is None:
            labels_data = list()
        else:
            labels_data = list(labels)

        if sections is None:
            sections_data = list()
        else:
            sections_data = list(sections)

        self._sources: list[PrimitiveId] = sources_data
        self._targets: list[PrimitiveId] = targets_data
        self._labels: list[SugiyamaLabel] = labels_data
        self._sections: list[SugiyamaEdgeSection] = sections_data

    @property
    def sources(self) -> list[PrimitiveId]:
        """Return the source endpoint identifiers.

        :return: Source endpoints.
        :rtype: list[PrimitiveId]
        """
        return self._sources

    @property
    def targets(self) -> list[PrimitiveId]:
        """Return the target endpoint identifiers.

        :return: Target endpoints.
        :rtype: list[PrimitiveId]
        """
        return self._targets

    @property
    def labels(self) -> list[SugiyamaLabel]:
        """Return the edge labels.

        :return: Edge labels.
        :rtype: list[SugiyamaLabel]
        """
        return self._labels

    @property
    def sections(self) -> list[SugiyamaEdgeSection]:
        """Return the routed edge sections.

        :return: Edge sections.
        :rtype: list[SugiyamaEdgeSection]
        """
        return self._sections

    def append_label(self, label: SugiyamaLabel) -> None:
        """Append one label to the edge.

        :param label: Label to append.
        :type label: SugiyamaLabel
        :return: None.
        :rtype: None
        """
        self._labels.append(label)

    def clear_labels(self) -> None:
        """Remove all labels from the edge.

        :return: None.
        :rtype: None
        """
        self._labels.clear()

    def append_section(self, section: SugiyamaEdgeSection) -> None:
        """Append one routed section to the edge.

        :param section: Section to append.
        :type section: SugiyamaEdgeSection
        :return: None.
        :rtype: None
        """
        self._sections.append(section)

    def clear_sections(self) -> None:
        """Remove all routed sections from the edge.

        :return: None.
        :rtype: None
        """
        self._sections.clear()


class SugiyamaGraph(SugiyamaPrimitive):
    """Root graph used by the layered pipeline.

    :param identifier: Graph identifier.
    :type identifier: PrimitiveId
    :param width: Graph width.
    :type width: float
    :param height: Graph height.
    :type height: float
    :param children: Root nodes.
    :type children: list[SugiyamaNode] | None
    :param edges: Graph edges.
    :type edges: list[SugiyamaEdge] | None
    :param labels: Graph labels.
    :type labels: list[SugiyamaLabel] | None
    :param layout_options: Layout options attached to the graph.
    :type layout_options: dict[str, Any] | None
    :param properties: Additional graph properties.
    :type properties: dict[str, Any] | None
    """

    __slots__ = ("_width", "_height", "_children", "_edges", "_labels")

    def __init__(
            self,
            identifier: PrimitiveId,
            width: float = 0.0,
            height: float = 0.0,
            children: list[SugiyamaNode] | None = None,
            edges: list[SugiyamaEdge] | None = None,
            labels: list[SugiyamaLabel] | None = None,
            layout_options: dict[str, Any] | None = None,
            properties: dict[str, Any] | None = None,
    ) -> None:
        children_data: list[SugiyamaNode]
        edges_data: list[SugiyamaEdge]
        labels_data: list[SugiyamaLabel]

        super().__init__(identifier=identifier, layout_options=layout_options, properties=properties)

        if children is None:
            children_data = list()
        else:
            children_data = list(children)

        if edges is None:
            edges_data = list()
        else:
            edges_data = list(edges)

        if labels is None:
            labels_data = list()
        else:
            labels_data = list(labels)

        self._width: float = width
        self._height: float = height
        self._children: list[SugiyamaNode] = children_data
        self._edges: list[SugiyamaEdge] = edges_data
        self._labels: list[SugiyamaLabel] = labels_data

    @property
    def width(self) -> float:
        """Return the graph width.

        :return: Graph width.
        :rtype: float
        """
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        """Set the graph width.

        :param value: New width.
        :type value: float
        """
        self._width = value

    @property
    def height(self) -> float:
        """Return the graph height.

        :return: Graph height.
        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        """Set the graph height.

        :param value: New height.
        :type value: float
        """
        self._height = value

    @property
    def children(self) -> list[SugiyamaNode]:
        """Return the root nodes.

        :return: Root nodes.
        :rtype: list[SugiyamaNode]
        """
        return self._children

    @children.setter
    def children(self, value: list[SugiyamaNode]) -> None:
        """Replace the root node list.

        :param value: New root node list.
        :type value: list[SugiyamaNode]
        """
        self._children = value

    @property
    def edges(self) -> list[SugiyamaEdge]:
        """Return the graph edges.

        :return: Graph edges.
        :rtype: list[SugiyamaEdge]
        """
        return self._edges

    def append_child(self, child: SugiyamaNode) -> None:
        """Append one root node to the graph.

        :param child: Root node to append.
        :type child: SugiyamaNode
        :return: None.
        :rtype: None
        """
        self._children.append(child)

    def clear_children(self) -> None:
        """Remove all root nodes from the graph.

        :return: None.
        :rtype: None
        """
        self._children.clear()

    def append_edge(self, edge: SugiyamaEdge) -> None:
        """Append one edge to the graph.

        :param edge: Edge to append.
        :type edge: SugiyamaEdge
        :return: None.
        :rtype: None
        """
        self._edges.append(edge)

    def clear_edges(self) -> None:
        """Remove all edges from the graph.

        :return: None.
        :rtype: None
        """
        self._edges.clear()

    def append_label(self, label: SugiyamaLabel) -> None:
        """Append one label to the graph.

        :param label: Label to append.
        :type label: SugiyamaLabel
        :return: None.
        :rtype: None
        """
        self._labels.append(label)

    def clear_labels(self) -> None:
        """Remove all labels from the graph.

        :return: None.
        :rtype: None
        """
        self._labels.clear()

    @property
    def labels(self) -> list[SugiyamaLabel]:
        """Return the graph labels.

        :return: Graph labels.
        :rtype: list[SugiyamaLabel]
        """
        return self._labels

    def all_nodes(self) -> list[SugiyamaNode]:
        """Return all nodes in breadth-first order.

        The engine often needs one flat node list to resolve identifiers and
        geometric relations. The traversal uses one explicit queue so the
        returned ordering is deterministic to inspect and debug.

        :return: Flattened node list.
        :rtype: list[SugiyamaNode]
        """
        result: list[SugiyamaNode] = list()
        queue: list[SugiyamaNode] = list(self._children)

        while len(queue) > 0:
            node: SugiyamaNode = queue.pop(0)
            result.append(node)
            if len(node.children) > 0:
                queue[0:0] = node.children
            else:
                pass

        return result

    def all_ports(self) -> list[SugiyamaPort]:
        """Return all ports in graph traversal order.

        :return: Flattened port list.
        :rtype: list[SugiyamaPort]
        """
        result: list[SugiyamaPort] = list()
        node: SugiyamaNode

        for node in self.all_nodes():
            result.extend(node.ports)

        return result

    def node_by_id(self) -> dict[PrimitiveId, SugiyamaNode]:
        """Build a node lookup by identifier.

        The lookup is rebuilt explicitly when phases request it so no hidden
        cache invalidation is needed after hierarchy or identifier updates.

        :return: Node lookup.
        :rtype: dict[PrimitiveId, SugiyamaNode]
        """
        result: dict[PrimitiveId, SugiyamaNode] = dict()
        node: SugiyamaNode

        for node in self.all_nodes():
            result[node.identifier] = node

        return result

    def port_by_id(self) -> dict[PrimitiveId, SugiyamaPort]:
        """Build a port lookup by identifier.

        :return: Port lookup.
        :rtype: dict[PrimitiveId, SugiyamaPort]
        """
        result: dict[PrimitiveId, SugiyamaPort] = dict()
        port: SugiyamaPort

        for port in self.all_ports():
            result[port.identifier] = port

        return result

    def clone_shallow(self) -> SugiyamaGraph:
        """Create a shallow graph clone.

        The clone duplicates the top-level containers so the caller can build
        alternative graph variants while reusing the already allocated
        primitives.

        :return: Shallow graph clone.
        :rtype: SugiyamaGraph
        """
        clone: SugiyamaGraph = SugiyamaGraph(
            identifier=self.identifier,
            layout_options=dict(self.layout_options),
            properties=dict(self.properties),
            width=self.width,
            height=self.height,
            children=list(self.children),
            edges=list(self.edges),
            labels=list(self.labels),
        )
        return clone
