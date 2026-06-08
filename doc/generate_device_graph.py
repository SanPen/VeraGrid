from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Set

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from doc.generate_device_docs import DEVICE_DOCS
else:
    from doc.generate_device_docs import DEVICE_DOCS


ROOT = Path(__file__).resolve().parent
SRC_DEVICES = ROOT.parent / "src" / "VeraGridEngine" / "Devices"
STATIC_DIR = ROOT / "_static"
MD_SOURCE = ROOT / "md_source"
HTML_FILE = STATIC_DIR / "device_relationships.html"
JSON_FILE = STATIC_DIR / "device_relationships.json"


@dataclass
class PropertyRef:
    name: str
    target_device_type: str


@dataclass
class ClassInfo:
    name: str
    module_name: str
    file_path: Path
    bases: List[str] = field(default_factory=list)
    property_refs: List[PropertyRef] = field(default_factory=list)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


EXPOSED_INFO = {
    doc.class_name: {
        "category": doc.category,
        "doc_url": f"../md_source/modelling.html#{slugify(doc.class_name)}",
    }
    for doc in DEVICE_DOCS
}


def attr_path(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = attr_path(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def literal_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def iter_gcprop_calls(node: ast.AST) -> Iterable[ast.Call]:
    if isinstance(node, ast.Call):
        fn = attr_path(node.func)
        if fn and fn.endswith("GCProp"):
            yield node
    elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        for item in node.elts:
            yield from iter_gcprop_calls(item)


def parse_property_refs(class_def: ast.ClassDef) -> List[PropertyRef]:
    refs: List[PropertyRef] = []
    for stmt in class_def.body:
        value = None
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "LOCAL_PROPERTY_DECLARATIONS":
                    value = stmt.value
                    break
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name) and stmt.target.id == "LOCAL_PROPERTY_DECLARATIONS":
                value = stmt.value
        if value is None:
            continue

        for call in iter_gcprop_calls(value):
            prop_name = None
            tpe_name = None
            for kw in call.keywords:
                if kw.arg in {"prop_name", "key"}:
                    prop_name = literal_str(kw.value)
                elif kw.arg == "tpe":
                    tpe_path = attr_path(kw.value)
                    if tpe_path and tpe_path.startswith("DeviceType."):
                        tpe_name = tpe_path.split(".", 1)[1]
            if prop_name and tpe_name:
                refs.append(PropertyRef(name=prop_name, target_device_type=tpe_name))
    return refs


def parse_classes() -> Dict[str, ClassInfo]:
    classes: Dict[str, ClassInfo] = {}
    for file_path in SRC_DEVICES.rglob("*.py"):
        if file_path.name == "__init__.py":
            continue
        module_name = ".".join(file_path.relative_to(ROOT.parent).with_suffix("").parts)
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [attr_path(base) or "<unknown>" for base in node.bases]
            classes[node.name] = ClassInfo(
                name=node.name,
                module_name=module_name,
                file_path=file_path.relative_to(ROOT.parent),
                bases=[base.split(".")[-1] for base in bases],
                property_refs=parse_property_refs(node),
            )
    return classes


def build_device_type_map(exposed_names: Iterable[str]) -> Dict[str, str]:
    mapping = {
        "AreaDevice": "Area",
        "BatteryDevice": "Battery",
        "BranchGroupDevice": "BranchGroup",
        "BusBarDevice": "BusBar",
        "BusDevice": "Bus",
        "CommunityDevice": "Community",
        "ContingencyDevice": "Contingency",
        "ContingencyGroupDevice": "ContingencyGroup",
        "CountryDevice": "Country",
        "CurrentInjectionDevice": "CurrentInjection",
        "DCLineDevice": "DcLine",
        "EmissionGasDevice": "EmissionGas",
        "EmtEventDevice": "EmtEvent",
        "EmtEventsGroupDevice": "EmtEventsGroup",
        "EmtModelTemplateDevice": "EmtModelTemplate",
        "ExternalGridDevice": "ExternalGrid",
        "FacilityDevice": "Facility",
        "FluidNodeDevice": "FluidNode",
        "FluidP2XDevice": "FluidP2x",
        "FluidPathDevice": "FluidPath",
        "FluidPumpDevice": "FluidPump",
        "FluidTurbineDevice": "FluidTurbine",
        "FmuTemplateDevice": "FmuTemplate",
        "FuelDevice": "Fuel",
        "GeneratorDevice": "Generator",
        "HVDCLineDevice": "HvdcLine",
        "IfMeasurementDevice": "IfMeasurement",
        "InvestmentDevice": "Investment",
        "InvestmentsGroupDevice": "InvestmentsGroup",
        "ItMeasurementDevice": "ItMeasurement",
        "LineDevice": "Line",
        "LoadDevice": "Load",
        "ModellingAuthority": "ModellingAuthority",
        "MunicipalityDevice": "Municipality",
        "OverheadLineTypeDevice": "OverheadLineType",
        "Owner": "Owner",
        "PfMeasurementDevice": "PfMeasurement",
        "PgMeasurementDevice": "PgMeasurement",
        "PiMeasurementDevice": "PiMeasurement",
        "PtMeasurementDevice": "PtMeasurement",
        "QfMeasurementDevice": "QfMeasurement",
        "QgMeasurementDevice": "QgMeasurement",
        "QiMeasurementDevice": "QiMeasurement",
        "QtMeasurementDevice": "QtMeasurement",
        "RegionDevice": "Region",
        "RemedialActionDevice": "RemedialAction",
        "RemedialActionGroupDevice": "RemedialActionGroup",
        "RmsEventDevice": "RmsEvent",
        "RmsEventsGroupDevice": "RmsEventsGroup",
        "RmsModelTemplateDevice": "RmsModelTemplate",
        "SequenceLineDevice": "SequenceLineType",
        "SeriesReactanceDevice": "SeriesReactance",
        "ShortCircuitEvent": "ShortCircuitEvent",
        "ShuntDevice": "Shunt",
        "StaticGeneratorDevice": "StaticGenerator",
        "SubstationDevice": "Substation",
        "SwitchDevice": "Switch",
        "Technology": "Technology",
        "Transformer2WDevice": "Transformer2W",
        "Transformer3WDevice": "Transformer3W",
        "TransformerNwDevice": "TransformerNW",
        "TransformerTypeDevice": "TransformerType",
        "UnderGroundLineDevice": "UndergroundLineType",
        "UpfcDevice": "UPFC",
        "VaMeasurementDevice": "VaMeasurement",
        "VmMeasurementDevice": "VmMeasurement",
        "VoltageLevelDevice": "VoltageLevel",
        "VscDevice": "VSC",
        "WindingDevice": "Winding",
        "WireDevice": "Wire",
        "ZoneDevice": "Zone",
    }

    # Add conservative automatic aliases for any future devices that follow the common pattern.
    for name in exposed_names:
        mapping.setdefault(f"{name}Device", name)
        mapping.setdefault(name, name)
    return mapping


def collect_relevant_classes(classes: Dict[str, ClassInfo]) -> Set[str]:
    relevant: Set[str] = set(EXPOSED_INFO.keys())
    queue = list(EXPOSED_INFO.keys())
    while queue:
        current = queue.pop()
        info = classes.get(current)
        if info is None:
            continue
        for base in info.bases:
            if base in classes and base not in relevant:
                relevant.add(base)
                queue.append(base)
    return relevant


def collect_inherited_property_refs(
    classes: Dict[str, ClassInfo],
    class_name: str,
    memo: Dict[str, List[PropertyRef]] | None = None,
) -> List[PropertyRef]:
    if memo is None:
        memo = {}

    cached = memo.get(class_name)
    if cached is not None:
        return cached

    info = classes.get(class_name)
    if info is None:
        memo[class_name] = []
        return []

    refs: List[PropertyRef] = list(info.property_refs)
    for base in info.bases:
        refs.extend(collect_inherited_property_refs(classes, base, memo))

    memo[class_name] = refs
    return refs


def render_html(graph: Dict[str, object]) -> str:
    payload = json.dumps(graph, separators=(",", ":"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Device Relationship Graph</title>
  <style>
    :root {{
      --bg: #f3efe6;
      --panel: rgba(255, 252, 245, 0.96);
      --ink: #1f2933;
      --muted: #5f6c76;
      --border: #d7ccbc;
      --accent: #0f766e;
      --accent-2: #b45309;
      --edge: rgba(82, 95, 111, 0.28);
      --reference: rgba(180, 83, 9, 0.38);
    }}
    html, body {{
      height: 100%;
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 28%),
        radial-gradient(circle at bottom right, rgba(180, 83, 9, 0.10), transparent 32%),
        var(--bg);
      color: var(--ink);
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    }}
    .app {{
      display: grid;
      grid-template-columns: 320px 1fr 320px;
      height: 100%;
      gap: 12px;
      padding: 12px;
      box-sizing: border-box;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(31, 41, 51, 0.08);
      backdrop-filter: blur(8px);
      overflow: hidden;
    }}
    .panel-inner {{
      padding: 16px 18px;
      height: 100%;
      box-sizing: border-box;
      overflow: auto;
    }}
    h1, h2 {{
      margin: 0 0 10px 0;
      font-weight: 700;
      line-height: 1.1;
    }}
    h1 {{
      font-size: 1.25rem;
    }}
    h2 {{
      font-size: 0.95rem;
      margin-top: 18px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    p, li, label, input, button, a {{
      font-size: 0.9rem;
      line-height: 1.45;
    }}
    a {{
      color: var(--accent);
    }}
    input[type="search"] {{
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      box-sizing: border-box;
      background: rgba(255, 255, 255, 0.84);
    }}
    .checklist {{
      display: grid;
      gap: 8px;
      margin-top: 10px;
    }}
    .checklist label {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
    }}
    .stat {{
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--border);
    }}
    .stat strong {{
      display: block;
      font-size: 1.15rem;
      margin-bottom: 3px;
    }}
    .graph-wrap {{
      position: relative;
      min-height: 0;
    }}
    canvas {{
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }}
    canvas.dragging {{
      cursor: grabbing;
    }}
    .legend {{
      position: absolute;
      left: 18px;
      bottom: 18px;
      display: grid;
      gap: 8px;
      padding: 12px 14px;
      background: rgba(255, 252, 245, 0.88);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    .legend-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
    }}
    .swatch {{
      width: 18px;
      height: 3px;
      border-radius: 999px;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 3px 10px;
      background: rgba(255,255,255,0.85);
      border: 1px solid var(--border);
      margin: 3px 6px 0 0;
      color: var(--muted);
    }}
    .muted {{
      color: var(--muted);
    }}
    .empty {{
      color: var(--muted);
      font-style: italic;
    }}
    button {{
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(255,255,255,0.8);
      padding: 8px 10px;
      cursor: pointer;
    }}
    .toolbar {{
      display: flex;
      gap: 8px;
      margin-top: 12px;
      flex-wrap: wrap;
    }}
    @media (max-width: 1200px) {{
      .app {{
        grid-template-columns: 280px 1fr;
        grid-template-rows: minmax(360px, 1fr) 300px;
      }}
      .details {{
        grid-column: 1 / -1;
      }}
    }}
    @media (max-width: 860px) {{
      .app {{
        grid-template-columns: 1fr;
        grid-template-rows: auto minmax(420px, 1fr) auto;
      }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <section class="panel">
      <div class="panel-inner">
        <h1>Device Relationship Graph</h1>
        <p class="muted">Explore typed property references among the final device classes exposed by <code>MultiCircuit</code>.</p>
        <h2>Search</h2>
        <input id="search" type="search" placeholder="Find a class or device type">
        <div class="toolbar">
          <button id="resetView" type="button">Reset view</button>
          <button id="focusSearch" type="button">Focus search</button>
        </div>
        <h2>Node kinds</h2>
        <div class="checklist" id="kindFilters"></div>
        <h2>Edge kinds</h2>
        <div class="checklist" id="edgeFilters"></div>
        <h2>Categories</h2>
        <div class="checklist" id="categoryFilters"></div>
        <div class="stats">
          <div class="stat"><strong id="visibleNodes">0</strong><span>visible nodes</span></div>
          <div class="stat"><strong id="visibleEdges">0</strong><span>visible edges</span></div>
          <div class="stat"><strong id="totalNodes">0</strong><span>total nodes</span></div>
          <div class="stat"><strong id="totalEdges">0</strong><span>total edges</span></div>
        </div>
      </div>
    </section>
    <section class="panel graph-wrap">
      <canvas id="graph"></canvas>
      <div class="legend">
        <div class="legend-row"><span class="swatch" style="background: var(--reference)"></span><span>Typed property reference</span></div>
      </div>
    </section>
    <aside class="panel details">
      <div class="panel-inner" id="details"></div>
    </aside>
  </div>
  <script>
    const graph = {payload};
    const canvas = document.getElementById("graph");
    const ctx = canvas.getContext("2d");
    const details = document.getElementById("details");
    const search = document.getElementById("search");
    const kindFilters = document.getElementById("kindFilters");
    const edgeFilters = document.getElementById("edgeFilters");
    const categoryFilters = document.getElementById("categoryFilters");
    const focusSearchButton = document.getElementById("focusSearch");
    const resetViewButton = document.getElementById("resetView");
    const totalNodesEl = document.getElementById("totalNodes");
    const totalEdgesEl = document.getElementById("totalEdges");
    const visibleNodesEl = document.getElementById("visibleNodes");
    const visibleEdgesEl = document.getElementById("visibleEdges");

    const state = {{
      width: 0,
      height: 0,
      panX: 0,
      panY: 0,
      zoom: 1,
      draggingNode: null,
      hoveringNode: null,
      selectedNode: null,
      lastPointer: null,
      isPanning: false,
      searchTerm: "",
      categorySelection: new Set(graph.meta.categories),
      kindSelection: new Set(graph.meta.nodeKinds),
      edgeSelection: new Set(graph.meta.edgeKinds),
    }};

    const nodes = graph.nodes.map((node, idx) => {{
      const angle = (idx / Math.max(graph.nodes.length, 1)) * Math.PI * 2;
      return {{
        ...node,
        x: Math.cos(angle) * (260 + (idx % 7) * 18),
        y: Math.sin(angle) * (260 + (idx % 11) * 14),
        vx: 0,
        vy: 0,
        radius: 22,
        visible: true,
        match: false,
      }};
    }});
    const nodeById = new Map(nodes.map((node) => [node.id, node]));
    const edges = graph.edges.map((edge) => ({{
      ...edge,
      sourceNode: nodeById.get(edge.source),
      targetNode: nodeById.get(edge.target),
      visible: true,
    }}));

    totalNodesEl.textContent = String(nodes.length);
    totalEdgesEl.textContent = String(edges.length);

    function nodeColor(node) {{
      const palette = graph.meta.categoryPalette[node.category] || "#3b82f6";
      return palette;
    }}

    function edgeColor(edge) {{
      return getComputedStyle(document.documentElement).getPropertyValue("--reference").trim();
    }}

    function buildChecklist(container, values, selectedSet) {{
      container.innerHTML = "";
      values.forEach((value) => {{
        const id = container.id + "-" + value.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
        const label = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = id;
        checkbox.checked = selectedSet.has(value);
        checkbox.addEventListener("change", () => {{
          if (checkbox.checked) selectedSet.add(value);
          else selectedSet.delete(value);
          applyFilters();
        }});
        const text = document.createElement("span");
        text.textContent = value;
        label.appendChild(checkbox);
        label.appendChild(text);
        container.appendChild(label);
      }});
    }}

    function resize() {{
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      state.width = rect.width;
      state.height = rect.height;
      if (state.panX === 0 && state.panY === 0) {{
        state.panX = state.width / 2;
        state.panY = state.height / 2;
      }}
    }}

    function worldToScreen(x, y) {{
      return {{
        x: x * state.zoom + state.panX,
        y: y * state.zoom + state.panY,
      }};
    }}

    function screenToWorld(x, y) {{
      return {{
        x: (x - state.panX) / state.zoom,
        y: (y - state.panY) / state.zoom,
      }};
    }}

    function findNodeAt(x, y) {{
      const world = screenToWorld(x, y);
      for (let i = nodes.length - 1; i >= 0; i -= 1) {{
        const node = nodes[i];
        if (!node.visible) continue;
        const dx = world.x - node.x;
        const dy = world.y - node.y;
        const radius = node.radius + 4 / state.zoom;
        if ((dx * dx) + (dy * dy) <= radius * radius) return node;
      }}
      return null;
    }}

    function normalize(text) {{
      return String(text || "").toLowerCase();
    }}

    function applyFilters() {{
      state.searchTerm = normalize(search.value.trim());
      nodes.forEach((node) => {{
        const categoryOk = state.categorySelection.has(node.category);
        const kindOk = state.kindSelection.has(node.kind);
        const text = normalize(node.label + " " + node.category + " " + node.module_name);
        node.match = !state.searchTerm || text.includes(state.searchTerm);
        node.visible = categoryOk && kindOk;
      }});

      edges.forEach((edge) => {{
        edge.visible = state.edgeSelection.has(edge.kind) &&
          edge.sourceNode.visible &&
          edge.targetNode.visible;
      }});

      if (state.selectedNode && !state.selectedNode.visible) {{
        state.selectedNode = null;
      }}
      if (state.hoveringNode && !state.hoveringNode.visible) {{
        state.hoveringNode = null;
      }}
      updateStats();
      updateDetails();
    }}

    function updateStats() {{
      visibleNodesEl.textContent = String(nodes.filter((node) => node.visible).length);
      visibleEdgesEl.textContent = String(edges.filter((edge) => edge.visible).length);
    }}

    function updateDetails() {{
      const node = state.selectedNode;
      if (!node) {{
        details.innerHTML = `
          <h1>Details</h1>
          <p class="muted">Click a node to inspect its typed references, module path, and documentation link.</p>
          <h2>What is shown</h2>
          <p>Nodes come from <code>MultiCircuit.template_objects_dict</code>. Edges come only from typed <code>GCProp(..., tpe=DeviceType.*)</code> relationships that resolve to another exposed final device class, including typed properties inherited from parent classes.</p>
        `;
        return;
      }}

      const outgoing = edges.filter((edge) => edge.visible && edge.source === node.id);
      const incoming = edges.filter((edge) => edge.visible && edge.target === node.id);
      const outgoingList = outgoing.length
        ? outgoing.map((edge) => {{
            const target = nodeById.get(edge.target);
            const label = `${{edge.properties.join(", ")}} -> ${{target.label}}`;
            return `<li>${{label}}</li>`;
          }}).join("")
        : `<li class="empty">No outgoing edges in the current filter set.</li>`;
      const incomingList = incoming.length
        ? incoming.map((edge) => {{
            const source = nodeById.get(edge.source);
            const label = `${{source.label}} references it through ${{edge.properties.join(", ")}}`;
            return `<li>${{label}}</li>`;
          }}).join("")
        : `<li class="empty">No incoming edges in the current filter set.</li>`;
      const pills = node.bases.length
        ? node.bases.map((base) => `<span class="pill">${{base}}</span>`).join("")
        : `<span class="empty">No direct base classes recorded.</span>`;
      const docLink = node.doc_url
        ? `<p><a href="${{node.doc_url}}" target="_top" rel="noopener">Open modelling chapter section</a></p>`
        : "";

      details.innerHTML = `
        <h1>${{node.label}}</h1>
        <p class="muted">${{node.category}} · ${{node.kind}} · <code>${{node.module_name}}</code></p>
        ${{docLink}}
        <h2>Base classes</h2>
        <div>${{pills}}</div>
        <h2>Outgoing</h2>
        <ul>${{outgoingList}}</ul>
        <h2>Incoming</h2>
        <ul>${{incomingList}}</ul>
      `;
    }}

    function centerOnNode(node) {{
      state.panX = state.width / 2 - node.x * state.zoom;
      state.panY = state.height / 2 - node.y * state.zoom;
    }}

    function focusSearchResult() {{
      const match = nodes.find((node) => node.visible && node.match);
      if (!match) return;
      state.selectedNode = match;
      centerOnNode(match);
      updateDetails();
    }}

    function resetView() {{
      state.zoom = 1;
      state.panX = state.width / 2;
      state.panY = state.height / 2;
    }}

    function physicsStep() {{
      const visibleNodes = nodes.filter((node) => node.visible);
      const visibleEdges = edges.filter((edge) => edge.visible);

      for (let i = 0; i < visibleNodes.length; i += 1) {{
        const a = visibleNodes[i];
        for (let j = i + 1; j < visibleNodes.length; j += 1) {{
          const b = visibleNodes[j];
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const distSq = Math.max(100, dx * dx + dy * dy);
          const force = 1500 / distSq;
          const nx = dx / Math.sqrt(distSq);
          const ny = dy / Math.sqrt(distSq);
          a.vx -= nx * force;
          a.vy -= ny * force;
          b.vx += nx * force;
          b.vy += ny * force;
        }}
      }}

      visibleEdges.forEach((edge) => {{
        const a = edge.sourceNode;
        const b = edge.targetNode;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy));
        const target = 170;
        const force = (dist - target) * 0.0022;
        const nx = dx / dist;
        const ny = dy / dist;
        a.vx += nx * force;
        a.vy += ny * force;
        b.vx -= nx * force;
        b.vy -= ny * force;
      }});

      visibleNodes.forEach((node) => {{
        if (state.draggingNode === node) return;
        const pull = 0.0012;
        node.vx += -node.x * pull;
        node.vy += -node.y * pull;
        node.vx *= 0.92;
        node.vy *= 0.92;
        node.x += node.vx;
        node.y += node.vy;
      }});
    }}

    function draw() {{
      ctx.clearRect(0, 0, state.width, state.height);
      ctx.lineCap = "round";

      edges.forEach((edge) => {{
        if (!edge.visible) return;
        const from = worldToScreen(edge.sourceNode.x, edge.sourceNode.y);
        const to = worldToScreen(edge.targetNode.x, edge.targetNode.y);
        ctx.strokeStyle = edgeColor(edge);
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.stroke();
      }});

      nodes.forEach((node) => {{
        if (!node.visible) return;
        const pos = worldToScreen(node.x, node.y);
        const radius = node.radius * state.zoom;
        ctx.beginPath();
        ctx.fillStyle = nodeColor(node);
        ctx.arc(pos.x, pos.y, Math.max(4, radius), 0, Math.PI * 2);
        ctx.fill();

        if (node === state.selectedNode || node === state.hoveringNode || node.match) {{
          ctx.strokeStyle = node === state.selectedNode ? "#111827" : "rgba(17, 24, 39, 0.55)";
          ctx.lineWidth = node === state.selectedNode ? 3 : 2;
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, Math.max(7, radius + 4), 0, Math.PI * 2);
          ctx.stroke();
        }}

        if (state.zoom > 0.52 || node === state.selectedNode || node.match) {{
          ctx.font = `${{Math.max(11, 12 * state.zoom)}}px IBM Plex Sans, Segoe UI, sans-serif`;
          ctx.fillStyle = "#1f2933";
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          ctx.fillText(node.label, pos.x, pos.y + Math.max(8, radius + 6));
        }}
      }});
    }}

    function tick() {{
      physicsStep();
      draw();
      requestAnimationFrame(tick);
    }}

    function pointerPosition(event) {{
      const rect = canvas.getBoundingClientRect();
      return {{
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      }};
    }}

    canvas.addEventListener("pointerdown", (event) => {{
      const pos = pointerPosition(event);
      const node = findNodeAt(pos.x, pos.y);
      state.lastPointer = pos;
      if (node) {{
        state.draggingNode = node;
        state.selectedNode = node;
        node.vx = 0;
        node.vy = 0;
        canvas.classList.add("dragging");
        updateDetails();
      }} else {{
        state.isPanning = true;
        canvas.classList.add("dragging");
      }}
      canvas.setPointerCapture(event.pointerId);
    }});

    canvas.addEventListener("pointermove", (event) => {{
      const pos = pointerPosition(event);
      if (state.draggingNode) {{
        const world = screenToWorld(pos.x, pos.y);
        state.draggingNode.x = world.x;
        state.draggingNode.y = world.y;
      }} else if (state.isPanning && state.lastPointer) {{
        state.panX += pos.x - state.lastPointer.x;
        state.panY += pos.y - state.lastPointer.y;
      }} else {{
        state.hoveringNode = findNodeAt(pos.x, pos.y);
      }}
      state.lastPointer = pos;
    }});

    canvas.addEventListener("pointerup", (event) => {{
      canvas.releasePointerCapture(event.pointerId);
      state.draggingNode = null;
      state.isPanning = false;
      state.lastPointer = null;
      canvas.classList.remove("dragging");
    }});

    canvas.addEventListener("wheel", (event) => {{
      event.preventDefault();
      const pos = pointerPosition(event);
      const worldBefore = screenToWorld(pos.x, pos.y);
      const factor = event.deltaY < 0 ? 1.08 : 0.92;
      state.zoom = Math.min(2.8, Math.max(0.28, state.zoom * factor));
      const worldAfter = screenToWorld(pos.x, pos.y);
      state.panX += (worldAfter.x - worldBefore.x) * state.zoom;
      state.panY += (worldAfter.y - worldBefore.y) * state.zoom;
    }}, {{ passive: false }});

    search.addEventListener("input", applyFilters);
    focusSearchButton.addEventListener("click", focusSearchResult);
    resetViewButton.addEventListener("click", resetView);
    window.addEventListener("resize", resize);

    buildChecklist(kindFilters, graph.meta.nodeKinds, state.kindSelection);
    buildChecklist(edgeFilters, graph.meta.edgeKinds, state.edgeSelection);
    buildChecklist(categoryFilters, graph.meta.categories, state.categorySelection);
    resize();
    applyFilters();
    updateDetails();
    tick();
  </script>
</body>
</html>
"""


def build_graph() -> Dict[str, object]:
    classes = parse_classes()
    device_type_to_class = build_device_type_map(EXPOSED_INFO.keys())
    relevant = set(EXPOSED_INFO.keys())

    nodes: Dict[str, Dict[str, object]] = {}
    for class_name in sorted(relevant):
        info = classes[class_name]
        exposed = EXPOSED_INFO.get(class_name)
        nodes[class_name] = {
            "id": class_name,
            "label": class_name,
            "kind": "exposed",
            "category": exposed["category"],
            "module_name": info.module_name,
            "file_path": str(info.file_path),
            "bases": info.bases,
            "doc_url": exposed["doc_url"],
        }

    ref_edge_map: Dict[tuple[str, str], Set[str]] = {}
    inherited_refs_memo: Dict[str, List[PropertyRef]] = {}

    for class_name in sorted(relevant):
        for ref in collect_inherited_property_refs(classes, class_name, inherited_refs_memo):
            target_class = device_type_to_class.get(ref.target_device_type)
            if not target_class or target_class not in relevant:
                continue
            target_id = target_class
            ref_edge_map.setdefault((class_name, target_id), set()).add(ref.name)

    reference_edges = [{
        "source": source,
        "target": target,
        "kind": "references",
        "properties": sorted(properties),
    } for (source, target), properties in sorted(ref_edge_map.items())]

    categories = sorted({
        node["category"] for node in nodes.values()
    })
    category_palette = {
        "Associations": "#8b5cf6",
        "Branches": "#0f766e",
        "Catalogue": "#2563eb",
        "Contingencies": "#dc2626",
        "Dynamic": "#7c3aed",
        "Fluid": "#0891b2",
        "Groups": "#475569",
        "Injections": "#15803d",
        "Investments": "#b91c1c",
        "Measurements": "#c2410c",
        "Regions": "#7c2d12",
        "Substation": "#1d4ed8",
        "Templates": "#be185d",
    }

    return {
        "nodes": list(nodes.values()),
        "edges": reference_edges,
        "meta": {
            "categories": categories,
            "nodeKinds": ["exposed"],
            "edgeKinds": ["references"],
            "categoryPalette": category_palette,
        },
    }


def generate_device_graph() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    graph = build_graph()
    JSON_FILE.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    HTML_FILE.write_text(render_html(graph), encoding="utf-8")


if __name__ == "__main__":
    generate_device_graph()
