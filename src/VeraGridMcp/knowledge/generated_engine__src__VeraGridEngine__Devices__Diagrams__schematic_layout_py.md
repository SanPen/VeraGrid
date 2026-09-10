# VeraGridEngine Module: src/VeraGridEngine/Devices/Diagrams/schematic_layout.py

- Original source path: `src/VeraGridEngine/Devices/Diagrams/schematic_layout.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 4
- Top-level function count: 37
- Representative imports: __future__, copy, typing, VeraGridEngine.Devices.Diagrams.graphic_location, VeraGridEngine.enumerations

## Class: SchematicExplicitAttachmentSlot

- Bases: none
- Summary: Store one typed explicit attachment slot for runtime behavior.

### Methods

- No methods detected.

## Class: SchematicRouteRecord

- Bases: none
- Summary: Store one typed route record for runtime behavior.

### Methods

- No methods detected.

## Class: SchematicAttachmentRecord

- Bases: none
- Summary: Store one typed attachment record for runtime behavior.

### Methods

- No methods detected.

## Class: SchematicDockRecord

- Bases: none
- Summary: Store one typed dock record for runtime behavior.

### Methods

- No methods detected.

## Function: parse_schematic_branch_endpoint(endpoint)

Parse one branch endpoint value from runtime or persisted data.

## Function: parse_schematic_attachment_side(side)

Parse one attachment side value from runtime or persisted data.

## Function: parse_schematic_attachment_owner_kind(owner_kind)

Parse one attachment owner kind from runtime or persisted data.

## Function: serialize_schematic_attachment_side(side, default_side)

Serialize one attachment side to the persisted string representation.

## Function: parse_schematic_explicit_attachment_slot(slot_key)

Parse one explicit persisted slot identifier into a typed runtime object.

## Function: serialize_schematic_explicit_attachment_slot(explicit_slot)

Serialize one typed explicit slot to the persisted string representation.

## Function: parse_schematic_route_kind(kind)

Parse one route kind value from runtime or persisted data.

## Function: parse_schematic_auto_route_style(route_style)

Parse one auto-route style value from runtime or persisted data.

## Function: serialize_schematic_auto_route_style(route_style, default_route_style)

Serialize one auto-route style to the persisted string representation.

## Function: serialize_schematic_route_kind(kind, default_kind)

Serialize one route kind to the persisted string representation.

## Function: _normalize_points(points)

Normalize persisted route points to plain numeric tuples.

## Function: ensure_layout_metadata(location)

Ensure the schematic metadata envelope exists and carries a schema version.

## Function: copy_layout_metadata(location)

Return a defensive copy of the schematic metadata envelope.

## Function: get_layout_section(location, section, default)

Return a copied layout metadata section so callers do not mutate persistence by accident.

## Function: set_layout_section(location, section, value)

Replace a layout metadata section with a defensive copy.

## Function: get_branch_route_points(location)

Return branch route points, preferring structured route metadata but falling back to legacy polyline storage.

## Function: get_branch_route_record(location)

Return one typed route record from persisted metadata.

## Function: set_branch_route_record(location, route_record)

Persist one typed route record while preserving the persisted schema.

## Function: set_branch_route_points(location, points, kind, locked, route_style)

Persist route points in both the legacy polyline field and the structured layout metadata.

## Function: compress_route_points(points)

Remove redundant route points while preserving orthogonal elbows.

## Function: build_route_stub_point(point, side, stub_length)

Build the first orthogonal stub point that leaves a node from one side.

## Function: get_default_route_lane_index(start_order, end_order)

Build a deterministic lane index from endpoint slot orders.

## Function: is_axis_aligned_route_segment(start, end)

Determine whether one route segment is orthogonal.

## Function: is_orthogonal_route(points)

Determine whether a route is already orthogonal.

## Function: should_preserve_route_shape(route)

Determine whether one persisted route should drive redraw.

## Function: build_default_branch_route(start, end, start_order, end_order, route_style)

Build one deterministic coordinate-driven auto route.

## Function: get_attachment(location, endpoint)

Return attachment metadata for an endpoint such as 'from', 'to', or a shunt/injection id.

## Function: get_attachment_record(location, endpoint)

Return one typed attachment record from persisted metadata.

## Function: set_attachment_record(location, endpoint, attachment_record)

Persist one typed attachment record while preserving the persisted schema.

## Function: set_attachment(location, endpoint, attachment)

Set attachment metadata for an endpoint.

## Function: get_dock(location)

Return dock metadata for a bus-connected child such as a shunt or generator.

## Function: get_dock_record(location)

Return one typed dock record from persisted metadata.

## Function: set_dock_record(location, dock_record)

Persist one typed dock record while preserving the persisted schema.

## Function: set_dock(location, dock)

Set dock metadata for a bus-connected child.

## Function: is_canonical_attachment_slot(slot_key)

Determine whether a slot key is one of the compatibility aliases.

## Function: build_explicit_attachment_slot_key(owner_kind, side, order)

Build a stable explicit slot identifier for persisted schematic attachments.

## Function: parse_explicit_attachment_slot_key(slot_key)

Parse an explicit slot identifier.
