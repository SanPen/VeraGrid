# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from VeraGridEngine.Utils.SugiyamaLayered.model import (SugiyamaEdge, SugiyamaEdgeSection, SugiyamaGraph,
                                                        SugiyamaLabel, SugiyamaNode, SugiyamaPort)


def _parse_label(data: dict[str, Any]) -> SugiyamaLabel:
    return SugiyamaLabel(
        identifier=str(data.get("id", "")),
        text=str(data.get("text", "")),
        width=float(data.get("width", 0.0) or 0.0),
        height=float(data.get("height", 0.0) or 0.0),
        x=float(data["x"]) if data.get("x") is not None else None,
        y=float(data["y"]) if data.get("y") is not None else None,
        layout_options=dict(data.get("layoutOptions", {})),
        properties={
            key: value
            for key, value in data.items()
            if key not in {"id", "text", "width", "height", "x", "y", "layoutOptions"}
        },
    )


def _parse_port(data: dict[str, Any]) -> SugiyamaPort:
    return SugiyamaPort(
        identifier=str(data.get("id", "")),
        width=float(data.get("width", 0.0) or 0.0),
        height=float(data.get("height", 0.0) or 0.0),
        x=float(data["x"]) if data.get("x") is not None else None,
        y=float(data["y"]) if data.get("y") is not None else None,
        labels=[_parse_label(label) for label in data.get("labels", [])],
        layout_options=dict(data.get("layoutOptions", {})),
        properties={
            key: value
            for key, value in data.items()
            if key not in {"id", "width", "height", "x", "y", "labels", "layoutOptions"}
        },
    )


def _parse_node(data: dict[str, Any], parent: str | None = None) -> SugiyamaNode:
    node = SugiyamaNode(
        identifier=str(data.get("id", "")),
        width=float(data.get("width", 0.0) or 0.0),
        height=float(data.get("height", 0.0) or 0.0),
        x=float(data["x"]) if data.get("x") is not None else None,
        y=float(data["y"]) if data.get("y") is not None else None,
        labels=[_parse_label(label) for label in data.get("labels", [])],
        ports=[_parse_port(port) for port in data.get("ports", [])],
        layout_options=dict(data.get("layoutOptions", {})),
        parent=parent,
        properties={
            key: value
            for key, value in data.items()
            if key not in {
                "id", "width", "height", "x", "y", "labels", "ports", "children", "layoutOptions"
            }
        },
    )
    node.set_children([_parse_node(child, parent=node.identifier) for child in data.get("children", [])])
    return node


def _parse_edge(data: dict[str, Any]) -> SugiyamaEdge:
    sections: list[SugiyamaEdgeSection] = []
    for section in data.get("sections", []):
        sections.append(
            SugiyamaEdgeSection(
                start_point=(
                    float(section["startPoint"]["x"]),
                    float(section["startPoint"]["y"]),
                ) if section.get("startPoint") else None,
                end_point=(
                    float(section["endPoint"]["x"]),
                    float(section["endPoint"]["y"]),
                ) if section.get("endPoint") else None,
                bend_points=[
                    (float(point["x"]), float(point["y"]))
                    for point in section.get("bendPoints", [])
                ],
            )
        )
    return SugiyamaEdge(
        identifier=str(data.get("id", "")),
        sources=[str(value) for value in data.get("sources", [])],
        targets=[str(value) for value in data.get("targets", [])],
        labels=[_parse_label(label) for label in data.get("labels", [])],
        sections=sections,
        layout_options=dict(data.get("layoutOptions", {})),
        properties={
            key: value
            for key, value in data.items()
            if key not in {"id", "sources", "targets", "labels", "sections", "layoutOptions"}
        },
    )


def graph_from_sugiyama_json(data: dict[str, Any]) -> SugiyamaGraph:
    return SugiyamaGraph(
        identifier=str(data.get("id", "root")),
        width=float(data.get("width", 0.0) or 0.0),
        height=float(data.get("height", 0.0) or 0.0),
        children=[_parse_node(child, parent=str(data.get("id", "root"))) for child in data.get("children", [])],
        edges=[_parse_edge(edge) for edge in data.get("edges", [])],
        labels=[_parse_label(label) for label in data.get("labels", [])],
        layout_options=dict(data.get("layoutOptions", {})),
        properties={
            key: value
            for key, value in data.items()
            if key not in {"id", "width", "height", "children", "edges", "labels", "layoutOptions"}
        },
    )


def _label_to_json(label: SugiyamaLabel) -> dict[str, Any]:
    payload = {
        "id": label.identifier,
        "text": label.text,
        "width": label.width,
        "height": label.height,
        "layoutOptions": dict(label.layout_options),
    }
    if label.x is not None:
        payload["x"] = label.x
    if label.y is not None:
        payload["y"] = label.y
    payload.update(label.properties)
    return payload


def _port_to_json(port: SugiyamaPort) -> dict[str, Any]:
    payload = {
        "id": port.identifier,
        "width": port.width,
        "height": port.height,
        "labels": [_label_to_json(label) for label in port.labels],
        "layoutOptions": dict(port.layout_options),
    }
    if port.x is not None:
        payload["x"] = port.x
    if port.y is not None:
        payload["y"] = port.y
    payload.update(port.properties)
    return payload


def _node_to_json(node: SugiyamaNode) -> dict[str, Any]:
    payload = {
        "id": node.identifier,
        "width": node.width,
        "height": node.height,
        "labels": [_label_to_json(label) for label in node.labels],
        "ports": [_port_to_json(port) for port in node.ports],
        "children": [_node_to_json(child) for child in node.children],
        "layoutOptions": dict(node.layout_options),
    }
    if node.x is not None:
        payload["x"] = node.x
    if node.y is not None:
        payload["y"] = node.y
    payload.update(node.properties)
    return payload


def _edge_to_json(edge: SugiyamaEdge) -> dict[str, Any]:
    payload = {
        "id": edge.identifier,
        "sources": list(edge.sources),
        "targets": list(edge.targets),
        "labels": [_label_to_json(label) for label in edge.labels],
        "sections": [],
        "layoutOptions": dict(edge.layout_options),
    }
    for section in edge.sections:
        section_payload: dict[str, Any] = {
            "bendPoints": [{"x": x, "y": y} for x, y in section.bend_points],
        }
        if section.start_point is not None:
            section_payload["startPoint"] = {"x": section.start_point[0], "y": section.start_point[1]}
        if section.end_point is not None:
            section_payload["endPoint"] = {"x": section.end_point[0], "y": section.end_point[1]}
        payload["sections"].append(section_payload)
    payload.update(edge.properties)
    return payload


def graph_to_sugiyama_json(graph: SugiyamaGraph) -> dict[str, Any]:
    payload = {
        "id": graph.identifier,
        "width": graph.width,
        "height": graph.height,
        "children": [_node_to_json(node) for node in graph.children],
        "edges": [_edge_to_json(edge) for edge in graph.edges],
        "labels": [_label_to_json(label) for label in graph.labels],
        "layoutOptions": dict(graph.layout_options),
    }
    payload.update(graph.properties)
    return payload
