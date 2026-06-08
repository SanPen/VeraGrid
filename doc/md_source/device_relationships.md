#🌟 Device Relationship Graph

This page shows an interactive graph of the device classes exposed by `MultiCircuit`.
It combines:

- only the final device classes exposed by `MultiCircuit`
- only typed references declared through `LOCAL_PROPERTY_DECLARATIONS`
- inherited typed references declared by parent classes are included
- only relationships that resolve to another exposed final device class

Use the controls on the left to filter by node kind, edge kind, and device category. Click a node to inspect its incoming and outgoing relationships.

The graph is generated from the source tree during the documentation build:

- Graph view: [standalone HTML](../_static/device_relationships.html)
- Raw data: [JSON](../_static/device_relationships.json)

<iframe
    src="../_static/device_relationships.html"
    title="Interactive device relationship graph"
    style="width: 100%; height: 920px; border: 1px solid #d7ccbc; border-radius: 12px; background: #f3efe6;"
></iframe>
