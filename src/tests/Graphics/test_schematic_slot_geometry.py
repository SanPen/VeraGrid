from VeraGrid.Gui.Diagrams.SchematicWidget.Branches.slot_geometry import (SchematicAttachmentSlot,
                                                                          build_explicit_slot_key,
                                                                          clamp_attachment_alignment,
                                                                          get_bar_slot_anchor,
                                                                          get_distributed_anchor,
                                                                          get_round_slot_anchor,
                                                                          infer_attachment_slot_from_route,
                                                                          parse_explicit_slot_key,
                                                                          requires_explicit_attachment_anchor,
                                                                          parse_attachment_slot)


def test_parse_attachment_slot_defaults_unknown_values():
    assert parse_attachment_slot("left") == SchematicAttachmentSlot.LEFT
    assert parse_attachment_slot("unexpected") == SchematicAttachmentSlot.DEFAULT


def test_clamp_attachment_alignment_limits_range() -> None:
    assert clamp_attachment_alignment(None) == 0.5
    assert clamp_attachment_alignment(-1.0) == 0.0
    assert clamp_attachment_alignment(0.25) == 0.25
    assert clamp_attachment_alignment(2.0) == 1.0


def test_requires_explicit_attachment_anchor_distinguishes_future_slot_ids():
    assert requires_explicit_attachment_anchor("default") is False
    assert requires_explicit_attachment_anchor("left") is True
    assert requires_explicit_attachment_anchor("top") is True
    assert requires_explicit_attachment_anchor("bus-right-1") is False


def test_explicit_slot_key_roundtrip() -> None:
    slot_key = build_explicit_slot_key(owner_kind="bus", side="bottom", order=4)

    assert slot_key == "bus-bottom-4"
    assert parse_explicit_slot_key(slot_key) == ("bus", SchematicAttachmentSlot.BOTTOM, 4)


def test_get_bar_slot_anchor_uses_bar_centerline_positions():
    assert get_bar_slot_anchor(width=180.0, terminal_y=20.0, terminal_h=10.0, slot_key="left") == (12.0, 25.0)
    assert get_bar_slot_anchor(width=180.0, terminal_y=20.0, terminal_h=10.0, slot_key="right") == (168.0, 25.0)
    assert get_bar_slot_anchor(width=180.0, terminal_y=20.0, terminal_h=10.0, slot_key="top") == (90.0, 25.0)
    assert get_bar_slot_anchor(width=180.0, terminal_y=20.0, terminal_h=10.0, slot_key="bottom") == (90.0, 25.0)
    assert get_bar_slot_anchor(width=180.0, terminal_y=20.0, terminal_h=10.0, slot_key="default") == (90.0, 25.0)


def test_get_round_slot_anchor_uses_body_edges():
    assert get_round_slot_anchor(width=50.0, height=50.0, slot_key="left") == (0.0, 25.0)
    assert get_round_slot_anchor(width=50.0, height=50.0, slot_key="right") == (50.0, 25.0)
    assert get_round_slot_anchor(width=50.0, height=50.0, slot_key="top") == (25.0, 0.0)
    assert get_round_slot_anchor(width=50.0, height=50.0, slot_key="bottom") == (25.0, 50.0)


def test_get_bar_slot_anchor_uses_manual_alignment_for_bar_feeders() -> None:
    assert get_bar_slot_anchor(width=180.0,
                               terminal_y=20.0,
                               terminal_h=10.0,
                               slot_key="bottom",
                               alignment=0.25) == (45.0, 25.0)


def test_get_bar_slot_anchor_clamps_manual_alignment_away_from_bar_ends() -> None:
    assert get_bar_slot_anchor(width=180.0,
                               terminal_y=20.0,
                               terminal_h=10.0,
                               slot_key="bottom",
                               alignment=0.0) == (12.0, 25.0)
    assert get_bar_slot_anchor(width=180.0,
                               terminal_y=20.0,
                               terminal_h=10.0,
                               slot_key="bottom",
                               alignment=1.0) == (168.0, 25.0)


def test_get_round_slot_anchor_uses_manual_alignment_for_side_feeders() -> None:
    assert get_round_slot_anchor(width=80.0,
                                 height=60.0,
                                 slot_key="right",
                                 alignment=0.75) == (80.0, 45.0)


def test_get_distributed_anchor_spreads_slots_by_order():
    assert get_distributed_anchor(side="bottom",
                                  width=180.0,
                                  height=40.0,
                                  terminal_y=20.0,
                                  terminal_h=10.0,
                                  order_index=1,
                                  slot_count=3) == (45.0, 25.0)
    assert get_distributed_anchor(side="bottom",
                                  width=180.0,
                                  height=40.0,
                                  terminal_y=20.0,
                                  terminal_h=10.0,
                                  order_index=3,
                                  slot_count=3) == (135.0, 25.0)
    assert get_distributed_anchor(side="top",
                                  width=180.0,
                                  height=40.0,
                                  terminal_y=20.0,
                                  terminal_h=10.0,
                                  order_index=2,
                                  slot_count=3) == (90.0, 25.0)


def test_infer_attachment_slot_from_route_uses_endpoint_direction():
    assert infer_attachment_slot_from_route(
        [(0.0, 0.0), (10.0, 0.0), (10.0, 20.0)],
        "from"
    ) == SchematicAttachmentSlot.RIGHT
    assert infer_attachment_slot_from_route(
        [(20.0, 20.0), (20.0, 10.0), (0.0, 10.0)],
        "to"
    ) == SchematicAttachmentSlot.RIGHT
