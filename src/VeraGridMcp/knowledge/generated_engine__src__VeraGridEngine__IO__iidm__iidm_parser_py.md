# VeraGridEngine Module: src/VeraGridEngine/IO/iidm/iidm_parser.py

- Original source path: `src/VeraGridEngine/IO/iidm/iidm_parser.py`
- Knowledge kind: generated VeraGridEngine code summary

## Module Summary

No docstring provided.

## Module Surface

- Class count: 0
- Top-level function count: 2
- Representative imports: typing, bz2, xml.etree.ElementTree, VeraGridEngine.IO.iidm.devices.rtesubstation, VeraGridEngine.IO.iidm.devices.voltage_level, VeraGridEngine.IO.iidm.devices.rte_area, VeraGridEngine.IO.iidm.devices.rte_bus, VeraGridEngine.IO.iidm.devices.generator, VeraGridEngine.IO.iidm.devices.load, VeraGridEngine.IO.iidm.devices.line, VeraGridEngine.IO.iidm.devices.two_winding_transformer, VeraGridEngine.IO.iidm.devices.rte_dangling_line, VeraGridEngine.IO.iidm.devices.shunt, VeraGridEngine.IO.iidm.devices.switch, VeraGridEngine.IO.iidm.devices.rte_busbar_section, VeraGridEngine.IO.iidm.devices.static_var_compensator

## Function: strip_ns(tag)

:param tag:

## Function: parse_xiidm_file(file_path)

Parse Xiidm to IidmCircuit
