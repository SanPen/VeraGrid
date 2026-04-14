# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Diagrams.graphic_location import GraphicLocation
from VeraGridEngine.Devices.Diagrams.schematic_diagram import SchematicDiagram
from VeraGridEngine.Devices.Diagrams.schematic_layout import build_default_branch_route
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.enumerations import SchematicAutoRouteStyle


def _build_obj_dict(*devices):
    obj_dict = dict()
    for device in devices:
        category = str(device.device_type.value)
        obj_dict.setdefault(category, dict())[device.idtag] = device
    return obj_dict


def test_graphic_location_serializes_polyline_and_layout_metadata():
    bus = Bus(name="B1")
    location = GraphicLocation(
        x=10,
        y=20,
        h=30,
        w=40,
        r=90,
        poly_line=[(1, 2), (3, 4)],
        layout_metadata={
            "schema_version": 1,
            "attachment": {"side": "right", "slot": "bus-right-1"},
        },
        draw_labels=False,
        api_object=bus,
    )

    data = location.get_properties_dict()

    assert data["poly_line"] == [(1, 2), (3, 4)]
    assert data["layout_metadata"] == {
        "schema_version": 1,
        "attachment": {"side": "right", "slot": "bus-right-1"},
    }
    assert data["draw_labels"] is False
    assert data["api_object"] == bus.idtag


def test_graphic_location_copy_detaches_mutable_layout_state():
    bus = Bus(name="B1")
    location = GraphicLocation(
        x=10,
        y=20,
        poly_line=[(1, 2), (3, 4)],
        layout_metadata={"attachments": {"from": {"slot": "bus-right-1"}}},
        api_object=bus,
    )

    copied = location.copy()
    copied.poly_line.append((5, 6))
    copied.layout_metadata["attachments"]["from"]["slot"] = "bus-left-1"

    assert copied is not location
    assert copied.api_object is bus
    assert location.poly_line == [(1, 2), (3, 4)]
    assert location.layout_metadata == {"attachments": {"from": {"slot": "bus-right-1"}}}


def test_schematic_diagram_roundtrip_preserves_polyline_and_layout_metadata():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="test")
    diagram.set_point(bus_from, GraphicLocation(x=5, y=10, w=80, h=20, r=0, api_object=bus_from))
    diagram.set_point(bus_to, GraphicLocation(x=105, y=10, w=80, h=20, r=0, api_object=bus_to))
    diagram.set_point(
        line,
        GraphicLocation(
            x=0,
            y=0,
            w=0,
            h=0,
            r=0,
            poly_line=[(45, 20), (45, 60), (145, 60), (145, 20)],
            layout_metadata={
                "schema_version": 1,
                "route": {"kind": "orthogonal", "locked": True},
                "center_symbol": {"anchor_segment": 1, "offset": 0.5},
            },
            draw_labels=True,
            api_object=line,
        ),
    )

    data = diagram.get_data_dict()
    parsed = SchematicDiagram()
    parsed.parse_data(data=data, obj_dict=_build_obj_dict(bus_from, bus_to, line), logger=Logger())

    parsed_line_location = parsed.query_point(line)

    assert parsed_line_location is not None
    assert parsed_line_location.poly_line == [(45, 20), (45, 60), (145, 60), (145, 20)]
    assert parsed_line_location.layout_metadata == {
        "schema_version": 1,
        "route": {"kind": "orthogonal", "locked": True},
        "center_symbol": {"anchor_segment": 1, "offset": 0.5},
    }
    assert parsed_line_location.draw_labels is True


def test_schematic_diagram_roundtrip_preserves_manual_polyline_route_and_nexus_dock_metadata() -> None:
    bus = Bus(name="B1")
    load = Load(name="LD1")
    load.bus = bus
    line = Line(name="L1", bus_from=bus, bus_to=bus)

    diagram = SchematicDiagram(name="polyline-roundtrip")
    diagram.set_point(bus, GraphicLocation(x=5, y=10, w=80, h=20, r=0, api_object=bus))
    diagram.set_branch_route_points(api_object=line,
                                    points=[(15.0, 20.0), (40.0, 55.0), (75.0, 30.0)],
                                    kind="manual-polyline",
                                    locked=False)
    diagram.set_point(
        load,
        GraphicLocation(
            x=30,
            y=120,
            layout_metadata={
                "schema_version": 1,
                "dock": {
                    "side": "bottom",
                    "order": 3,
                    "offset": 15.0,
                    "nexus_route_kind": "manual-polyline",
                    "nexus_route_points": [(55.0, 145.0), (80.0, 185.0), (110.0, 165.0)],
                    "nexus_parent_alignment": 0.35,
                    "nexus_child_alignment": 0.7,
                },
            },
            api_object=load,
        ),
    )

    parsed = SchematicDiagram()
    parsed.parse_data(data=diagram.get_data_dict(),
                      obj_dict=_build_obj_dict(bus, line, load),
                      logger=Logger())

    parsed_line_location = parsed.query_point(line)
    parsed_load_location = parsed.query_point(load)

    assert parsed_line_location is not None
    assert parsed_line_location.layout_metadata["route"] == {
        "points": [(15.0, 20.0), (40.0, 55.0), (75.0, 30.0)],
        "kind": "manual-polyline",
        "locked": False,
    }
    assert parsed_load_location is not None
    assert parsed_load_location.layout_metadata["dock"] == {
        "side": "bottom",
        "order": 3,
        "offset": 15.0,
        "nexus_route_kind": "manual-polyline",
        "nexus_route_points": [(55.0, 145.0), (80.0, 185.0), (110.0, 165.0)],
        "nexus_parent_alignment": 0.35,
        "nexus_child_alignment": 0.7,
    }


def test_schematic_diagram_roundtrip_preserves_branch_auto_route_style() -> None:
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="style-roundtrip")
    diagram.set_point(bus_from, GraphicLocation(x=5, y=10, w=80, h=20, r=0, api_object=bus_from))
    diagram.set_point(bus_to, GraphicLocation(x=105, y=10, w=80, h=20, r=0, api_object=bus_to))
    diagram.set_branch_auto_route_style(api_object=line, route_style=SchematicAutoRouteStyle.STRAIGHT)

    parsed = SchematicDiagram()
    parsed.parse_data(data=diagram.get_data_dict(),
                      obj_dict=_build_obj_dict(bus_from, bus_to, line),
                      logger=Logger())

    assert parsed.get_branch_auto_route_style(api_object=line) == SchematicAutoRouteStyle.STRAIGHT


def test_schematic_diagram_legacy_parse_defaults_layout_metadata_and_polyline():
    bus = Bus(name="B1")
    legacy_data = {
        "type": "bus-branch",
        "idtag": "diagram1",
        "name": "legacy",
        "use_flow_based_width": False,
        "min_branch_width": 1,
        "max_branch_width": 5,
        "min_bus_width": 1,
        "max_bus_width": 20,
        "arrow_size": 1,
        "use_api_colors": False,
        "palette": "VeraGrid",
        "default_bus_voltage": 10,
        "data": {
            str(bus.device_type.value): {
                bus.idtag: {
                    "x": 1,
                    "y": 2,
                    "w": 3,
                    "h": 4,
                    "r": 5,
                    "draw_labels": True,
                    "api_object": bus.idtag,
                }
            }
        },
    }

    parsed = SchematicDiagram()
    parsed.parse_data(data=legacy_data, obj_dict=_build_obj_dict(bus), logger=Logger())

    bus_location = parsed.query_point(bus)

    assert bus_location is not None
    assert bus_location.poly_line == []
    assert bus_location.layout_metadata == {}
    assert bus_location.x == 1
    assert bus_location.y == 2
    assert bus_location.r == 5


def test_schematic_diagram_compatibility_route_reader_uses_legacy_polyline():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_point(
        line,
        GraphicLocation(
            poly_line=[(10, 20), (10, 30), (40, 30)],
            layout_metadata={},
            api_object=line,
        ),
    )

    assert diagram.get_branch_route_points(line) == [(10.0, 20.0), (10.0, 30.0), (40.0, 30.0)]


def test_schematic_diagram_compatibility_route_writer_keeps_polyline_and_metadata_in_sync():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")

    diagram.set_branch_route_points(
        api_object=line,
        points=[(15, 25), (15, 60), (80, 60)],
        kind="orthogonal",
        locked=True,
    )

    location = diagram.query_point(line)

    assert location is not None
    assert location.poly_line == [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)]
    assert location.layout_metadata["route"] == {
        "points": [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)],
        "kind": "orthogonal",
        "locked": True,
    }
    assert diagram.get_branch_route_points(line) == [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)]


def test_schematic_diagram_should_preserve_branch_route_shape_uses_kind_and_lock_state() -> None:
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_branch_route_points(api_object=line,
                                    points=[(15, 25), (15, 60), (80, 60)],
                                    kind="orthogonal",
                                    locked=False)
    assert diagram.should_preserve_branch_route_shape(line) is False

    diagram.set_branch_route_points(api_object=line,
                                    points=[(15, 25), (15, 60), (80, 60)],
                                    kind="manual-polyline",
                                    locked=False)
    assert diagram.should_preserve_branch_route_shape(line) is True

    diagram.set_branch_route_points(api_object=line,
                                    points=[(15, 25), (15, 60), (80, 60)],
                                    kind="orthogonal",
                                    locked=True)
    assert diagram.should_preserve_branch_route_shape(line) is True


def test_schematic_diagram_attachment_accessors_are_defensive_and_persisted():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_attachment(line, "from", {"side": "right", "slot": "bus-right-1", "order": 1})

    attachment = diagram.get_attachment(line, "from")
    attachment["side"] = "left"

    location = diagram.query_point(line)

    assert location is not None
    assert location.layout_metadata["attachments"]["from"] == {
        "side": "right",
        "slot": "bus-right-1",
        "order": 1,
    }
    assert diagram.get_attachment(line, "from") == {
        "side": "right",
        "slot": "bus-right-1",
        "order": 1,
    }


def test_schematic_diagram_update_graphic_location_preserves_route_metadata():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_branch_route_points(
        api_object=line,
        points=[(15, 25), (15, 60), (80, 60)],
        kind="orthogonal",
        locked=True,
    )
    diagram.set_attachment(line, "from", {"side": "right", "slot": "bus-right-1"})

    location = diagram.update_graphic_location(api_object=line,
                                               x=100,
                                               y=200,
                                               w=50,
                                               h=60,
                                               r=90,
                                               draw_labels=False)

    assert location.x == 100
    assert location.y == 200
    assert location.w == 50
    assert location.h == 60
    assert location.r == 90
    assert location.draw_labels is False
    assert location.poly_line == [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)]
    assert location.layout_metadata["route"] == {
        "points": [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)],
        "kind": "orthogonal",
        "locked": True,
    }
    assert location.layout_metadata["attachments"]["from"] == {
        "side": "right",
        "slot": "bus-right-1",
    }


def test_schematic_diagram_copy_layout_state_preserves_route_and_attachments():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    source_line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    target_line = Line(name="L2", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.update_graphic_location(api_object=source_line,
                                    x=100,
                                    y=200,
                                    w=50,
                                    h=60,
                                    r=90,
                                    draw_labels=False)
    diagram.set_branch_route_points(
        api_object=source_line,
        points=[(15, 25), (15, 60), (80, 60)],
        kind="orthogonal",
        locked=True,
    )
    diagram.set_attachment(source_line, "from", {"side": "right", "slot": "bus-right-1"})

    copied_location = diagram.copy_layout_state(source_api_object=source_line,
                                                target_api_object=target_line)

    assert copied_location is not None
    assert copied_location.api_object is target_line
    assert copied_location.x == 0.0
    assert copied_location.y == 0.0
    assert copied_location.w == 0.0
    assert copied_location.h == 0.0
    assert copied_location.r == 0.0
    assert copied_location.draw_labels is False
    assert copied_location.poly_line == [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)]
    assert copied_location.layout_metadata["attachments"]["from"] == {
        "side": "right",
        "slot": "bus-right-1",
    }
    assert copied_location.layout_metadata["route"] == {
        "points": [(15.0, 25.0), (15.0, 60.0), (80.0, 60.0)],
        "kind": "orthogonal",
        "locked": True,
    }

    source_location = diagram.query_point(source_line)
    copied_location.layout_metadata["attachments"]["from"]["slot"] = "bus-left-1"

    assert source_location is not None
    assert source_location.layout_metadata["attachments"]["from"]["slot"] == "bus-right-1"


def test_schematic_diagram_sync_branch_route_points_preserves_kind_and_locked():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_branch_route_points(
        api_object=line,
        points=[(10, 20), (10, 60), (80, 60)],
        kind="manual-polyline",
        locked=True,
    )

    diagram.sync_branch_route_points(api_object=line,
                                     points=[(15, 25), (15, 70), (90, 70)])

    location = diagram.query_point(line)

    assert location is not None
    assert location.poly_line == [(15.0, 25.0), (15.0, 70.0), (90.0, 70.0)]
    assert location.layout_metadata["route"] == {
        "points": [(15.0, 25.0), (15.0, 70.0), (90.0, 70.0)],
        "kind": "manual-polyline",
        "locked": True,
    }


def test_schematic_diagram_sync_branch_attachments_normalizes_explicit_slot_metadata_from_order():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_attachment(line, "from", {"side": "right", "slot": "bus-right-1", "order": 2})
    diagram.set_attachment(line, "to", {"side": "left", "slot": "bus-left-1"})

    attachments = diagram.sync_branch_attachments(api_object=line)

    assert attachments["from"] == {
        "anchor_auto": True,
        "auto_slot": True,
        "side": "right",
        "slot": "bus-right-2",
        "order": 2,
        "owner_device_id": bus_from.idtag,
        "owner_device_type": bus_from.device_type.value,
        "terminal_key": "bus-right-2",
    }
    assert attachments["to"] == {
        "anchor_auto": True,
        "auto_slot": True,
        "side": "left",
        "slot": "left",
        "owner_device_id": bus_to.idtag,
        "owner_device_type": bus_to.device_type.value,
        "terminal_key": "left",
    }


def test_schematic_diagram_sync_branch_attachments_updates_owner_when_endpoint_changes():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    bus_new = Bus(name="B3")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.sync_branch_attachments(api_object=line)

    line.bus_to = bus_new
    diagram.sync_branch_attachments(api_object=line)

    assert diagram.get_attachment(line, "from")["owner_device_id"] == bus_from.idtag
    assert diagram.get_attachment(line, "to")["owner_device_id"] == bus_new.idtag
    assert diagram.get_attachment(line, "to")["owner_device_type"] == bus_new.device_type.value


def test_schematic_diagram_sync_branch_attachments_sets_default_slot_identity():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    attachments = diagram.sync_branch_attachments(api_object=line)

    assert attachments["from"]["side"] == "bottom"
    assert attachments["from"]["slot"] == "bottom"
    assert attachments["from"]["terminal_key"] == "bottom"
    assert attachments["to"]["side"] == "bottom"
    assert attachments["to"]["slot"] == "bottom"
    assert attachments["to"]["terminal_key"] == "bottom"


def test_schematic_diagram_sync_branch_attachments_copies_branch_position_into_order():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    line.bus_from_pos = 3
    line.bus_to_pos = 5

    diagram = SchematicDiagram(name="compat")
    attachments = diagram.sync_branch_attachments(api_object=line)

    assert attachments["from"]["order"] == 3
    assert attachments["to"]["order"] == 5
    assert attachments["from"]["slot"] == "bus-bottom-3"
    assert attachments["from"]["terminal_key"] == "bus-bottom-3"
    assert attachments["to"]["slot"] == "bus-bottom-5"
    assert attachments["to"]["terminal_key"] == "bus-bottom-5"


def test_schematic_diagram_sync_attachment_preserves_custom_noncanonical_slot_keys():
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    line.bus_from_pos = 4

    diagram = SchematicDiagram(name="compat")
    diagram.set_attachment(
        line,
        "from",
        {
            "side": "bottom",
            "slot": "manual-slot-a",
            "terminal_key": "manual-slot-a",
            "order": 4,
            "auto_slot": False,
        },
    )

    attachment = diagram.sync_attachment(api_object=line, endpoint="from", owner_device=bus_from)

    assert attachment["side"] == "bottom"
    assert attachment["slot"] == "bottom"
    assert attachment["terminal_key"] == "bottom"
    assert attachment["order"] == 4


def test_schematic_diagram_dock_accessors_are_defensive_and_persisted():
    bus = Bus(name="B1")
    load = Load(name="LD1")
    load.bus = bus

    diagram = SchematicDiagram(name="compat")
    diagram.set_dock(load, {"side": "bottom", "order": 2, "offset": 14.0})

    dock = diagram.get_dock(load)
    dock["side"] = "top"

    location = diagram.query_point(load)

    assert location is not None
    assert location.layout_metadata["dock"] == {
        "side": "bottom",
        "order": 2,
        "offset": 14.0,
    }
    assert diagram.get_dock(load) == {
        "side": "bottom",
        "order": 2,
        "offset": 14.0,
    }


def test_schematic_diagram_sync_injection_dock_copies_bus_position_and_owner() -> None:
    bus = Bus(name="B1")
    load = Load(name="LD1")
    load.bus = bus
    load.bus_pos = 4

    diagram = SchematicDiagram(name="compat")
    dock = diagram.sync_injection_dock(api_object=load, owner_device=bus)

    assert dock == {
        "owner_device_id": bus.idtag,
        "owner_device_type": bus.device_type.value,
        "side": "bottom",
        "offset": 0.0,
        "order": 4,
    }


def test_schematic_diagram_sync_injection_dock_preserves_custom_fields() -> None:
    bus = Bus(name="B1")
    load = Load(name="LD1")
    load.bus = bus
    load.bus_pos = 4

    diagram = SchematicDiagram(name="compat")
    diagram.set_dock(load, {"side": "top", "offset": 22.0, "order": 7})

    dock = diagram.sync_injection_dock(api_object=load, owner_device=bus)

    assert dock["side"] == "top"
    assert dock["offset"] == 22.0
    assert dock["order"] == 7
    assert dock["owner_device_id"] == bus.idtag


def test_schematic_diagram_upgrade_legacy_branch_layout_synthesizes_coordinate_route() -> None:
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    line.bus_from_pos = 2
    line.bus_to_pos = 4

    diagram = SchematicDiagram(name="compat")
    metadata = diagram.upgrade_legacy_branch_layout(api_object=line, start=(10.0, 20.0), end=(110.0, 80.0))

    assert diagram.get_branch_route_points(line) == [(10.0, 20.0), (110.0, 80.0)]
    assert metadata["route"] == {
        "points": [(10.0, 20.0), (110.0, 80.0)],
        "kind": "auto-polyline",
        "locked": False,
    }
    assert diagram.get_attachment(line, "from")["slot"] == "bus-bottom-2"
    assert diagram.get_attachment(line, "to")["slot"] == "bus-bottom-4"


def test_schematic_diagram_upgrade_legacy_branch_layout_preserves_legacy_polyline() -> None:
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)

    diagram = SchematicDiagram(name="compat")
    diagram.set_point(
        line,
        GraphicLocation(
            poly_line=[(10.0, 20.0), (10.0, 60.0), (90.0, 60.0)],
            layout_metadata=dict(),
            api_object=line,
        ),
    )

    metadata = diagram.upgrade_legacy_branch_layout(api_object=line, start=(10.0, 20.0), end=(90.0, 60.0))

    assert diagram.get_branch_route_points(line) == [(10.0, 20.0), (10.0, 60.0), (90.0, 60.0)]
    assert metadata["route"] == {
        "points": [(10.0, 20.0), (10.0, 60.0), (90.0, 60.0)],
        "kind": "manual-polyline",
        "locked": False,
    }


def test_build_default_branch_route_uses_coordinate_midline_and_optional_lane_offset() -> None:
    route = build_default_branch_route(start=(20.0, 10.0),
                                       end=(120.0, 10.0),
                                       start_order=1,
                                       end_order=3,
                                       route_style=SchematicAutoRouteStyle.RETICULAR)

    assert route == [
        (20.0, 10.0),
        (20.0, 24.0),
        (120.0, 24.0),
        (120.0, 10.0),
    ]


def test_schematic_diagram_upgrade_legacy_branch_layout_preserves_legacy_straight_polyline() -> None:
    bus_from = Bus(name="B1")
    bus_to = Bus(name="B2")
    line = Line(name="L1", bus_from=bus_from, bus_to=bus_to)
    line.bus_from_pos = 1
    line.bus_to_pos = 2

    diagram = SchematicDiagram(name="compat")
    diagram.set_point(
        line,
        GraphicLocation(
            poly_line=[(10.0, 20.0), (90.0, 60.0)],
            layout_metadata=dict(),
            api_object=line,
        ),
    )

    metadata = diagram.upgrade_legacy_branch_layout(api_object=line, start=(10.0, 20.0), end=(90.0, 60.0))

    assert diagram.get_branch_route_points(line) == [
        (10.0, 20.0),
        (90.0, 60.0),
    ]
    assert metadata["route"]["kind"] == "manual-polyline"
