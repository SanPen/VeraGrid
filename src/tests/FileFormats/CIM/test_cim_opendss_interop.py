# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import textwrap
from pathlib import Path

import numpy as np

import VeraGridEngine.api as vg
from VeraGridEngine.Devices.Branches.line import Line
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.shunt import Shunt
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.Substation.bus import Bus
from VeraGridEngine.Devices.Substation.substation import Substation
from VeraGridEngine.IO.file_open import FileOpenOptions
from VeraGridEngine.IO.file_save import FileSavingOptions
from VeraGridEngine.enumerations import FileType


def test_cim_import_accepts_opendss_style_topology_without_busbarsections(tmp_path):
    cim_path = tmp_path / "opendss_style.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>Bus 1</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000102">
                <cim:IdentifiedObject.name>Bus 2</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000202">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000102"/>
              </cim:ConnectivityNode>
              <cim:ACLineSegment rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>Line 1</cim:IdentifiedObject.name>
                <cim:Conductor.length>1</cim:Conductor.length>
                <cim:ACLineSegment.r>1</cim:ACLineSegment.r>
                <cim:ACLineSegment.x>2</cim:ACLineSegment.x>
                <cim:ACLineSegment.bch>0</cim:ACLineSegment.bch>
                <cim:ACLineSegment.gch>0</cim:ACLineSegment.gch>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:ACLineSegment>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000402">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000202"/>
                <cim:ACDCTerminal.sequenceNumber>2</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.buses) == 2
    assert {bus.name for bus in grid.buses} == {"Bus 1", "Bus 2"}
    assert len(grid.lines) == 1
    assert grid.lines[0].name == "Line 1"


def test_cim_export_uses_cim100_namespace(tmp_path):
    grid = MultiCircuit(name="CIM export test")
    substation = Substation(name="Substation 1")
    bus1 = Bus(name="Bus 1", Vnom=110, substation=substation)
    bus2 = Bus(name="Bus 2", Vnom=110, substation=substation)
    grid.add_bus(bus1)
    grid.add_bus(bus2)

    cim_path = tmp_path / "export.xml"
    vg.FileSave(
        circuit=grid,
        file_name=str(cim_path),
        options=FileSavingOptions(file_type=FileType.CIM),
    ).save()

    xml = cim_path.read_text()
    assert 'xmlns:cim="http://iec.ch/TC57/CIM100#"' in xml
    assert '<cim:IEC61970CIMVersion rdf:ID="00000000-0000-0000-0000-000000000100">' in xml
    assert '<cim:IEC61970CIMVersion.version>IEC61970CIM100</cim:IEC61970CIMVersion.version>' in xml
    assert '<cim:IEC61970CIMVersion.date>2019-04-01</cim:IEC61970CIMVersion.date>' in xml


def test_cim_import_aggregates_opendss_load_phase_power(tmp_path):
    cim_path = tmp_path / "opendss_load_phase.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>Bus 1</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:EnergyConsumer rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>Load 1</cim:IdentifiedObject.name>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:EnergyConsumer>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:EnergyConsumerPhase rdf:ID="00000000-0000-0000-0000-000000000501">
                <cim:EnergyConsumerPhase.EnergyConsumer rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:EnergyConsumerPhase.p>7</cim:EnergyConsumerPhase.p>
                <cim:EnergyConsumerPhase.q>3</cim:EnergyConsumerPhase.q>
              </cim:EnergyConsumerPhase>
              <cim:EnergyConsumerPhase rdf:ID="00000000-0000-0000-0000-000000000502">
                <cim:EnergyConsumerPhase.EnergyConsumer rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:EnergyConsumerPhase.p>5</cim:EnergyConsumerPhase.p>
                <cim:EnergyConsumerPhase.q>2</cim:EnergyConsumerPhase.q>
              </cim:EnergyConsumerPhase>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.loads) == 1
    assert grid.loads[0].P == 12
    assert grid.loads[0].Q == 5


def test_cim_import_aggregates_opendss_generator_phase_power(tmp_path):
    cim_path = tmp_path / "opendss_generator_phase.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>Bus 1</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:SynchronousMachine rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>Gen 1</cim:IdentifiedObject.name>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:SynchronousMachine>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:SynchronousMachinePhase rdf:ID="00000000-0000-0000-0000-000000000501">
                <cim:SynchronousMachinePhase.SynchronousMachine rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:SynchronousMachinePhase.p>-6</cim:SynchronousMachinePhase.p>
                <cim:SynchronousMachinePhase.q>-1</cim:SynchronousMachinePhase.q>
              </cim:SynchronousMachinePhase>
              <cim:SynchronousMachinePhase rdf:ID="00000000-0000-0000-0000-000000000502">
                <cim:SynchronousMachinePhase.SynchronousMachine rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:SynchronousMachinePhase.p>-4</cim:SynchronousMachinePhase.p>
                <cim:SynchronousMachinePhase.q>-2</cim:SynchronousMachinePhase.q>
              </cim:SynchronousMachinePhase>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.generators) == 1
    assert grid.generators[0].P == 10


def test_cim_import_aggregates_opendss_shunt_phase_admittance(tmp_path):
    cim_path = tmp_path / "opendss_shunt_phase.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>Bus 1</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:LinearShuntCompensator rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>Cap 1</cim:IdentifiedObject.name>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:LinearShuntCompensator>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:LinearShuntCompensatorPhase rdf:ID="00000000-0000-0000-0000-000000000501">
                <cim:ShuntCompensatorPhase.ShuntCompensator rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:LinearShuntCompensatorPhase.bPerSection>0.4</cim:LinearShuntCompensatorPhase.bPerSection>
                <cim:LinearShuntCompensatorPhase.gPerSection>0.1</cim:LinearShuntCompensatorPhase.gPerSection>
                <cim:ShuntCompensatorPhase.sections>2</cim:ShuntCompensatorPhase.sections>
              </cim:LinearShuntCompensatorPhase>
              <cim:LinearShuntCompensatorPhase rdf:ID="00000000-0000-0000-0000-000000000502">
                <cim:ShuntCompensatorPhase.ShuntCompensator rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:LinearShuntCompensatorPhase.bPerSection>0.2</cim:LinearShuntCompensatorPhase.bPerSection>
                <cim:LinearShuntCompensatorPhase.gPerSection>0.05</cim:LinearShuntCompensatorPhase.gPerSection>
                <cim:ShuntCompensatorPhase.sections>1</cim:ShuntCompensatorPhase.sections>
              </cim:LinearShuntCompensatorPhase>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.shunts) == 1
    assert grid.shunts[0].G == 0.25
    assert grid.shunts[0].B == 1.0


def test_cim_power_flow_roundtrip_preserves_open_dss_style_solution(tmp_path):
    cim_path = tmp_path / "opendss_roundtrip.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>SourceBus</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000102">
                <cim:IdentifiedObject.name>LoadBus</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000202">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000102"/>
              </cim:ConnectivityNode>
              <cim:EquivalentNetwork rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>Source</cim:IdentifiedObject.name>
              </cim:EquivalentNetwork>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:ACLineSegment rdf:ID="00000000-0000-0000-0000-000000000302">
                <cim:IdentifiedObject.name>Line 1</cim:IdentifiedObject.name>
                <cim:Conductor.length>1</cim:Conductor.length>
                <cim:ACLineSegment.r>1</cim:ACLineSegment.r>
                <cim:ACLineSegment.x>2</cim:ACLineSegment.x>
                <cim:ACLineSegment.bch>0</cim:ACLineSegment.bch>
                <cim:ACLineSegment.gch>0</cim:ACLineSegment.gch>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:ACLineSegment>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000402">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000302"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000403">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000302"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000202"/>
                <cim:ACDCTerminal.sequenceNumber>2</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:EnergyConsumer rdf:ID="00000000-0000-0000-0000-000000000303">
                <cim:IdentifiedObject.name>Load 1</cim:IdentifiedObject.name>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
                <cim:EnergyConsumer.p>10</cim:EnergyConsumer.p>
                <cim:EnergyConsumer.q>5</cim:EnergyConsumer.q>
              </cim:EnergyConsumer>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000404">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000303"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000202"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))
    assert any(bus.is_slack for bus in grid.buses)

    first = vg.power_flow(grid)
    assert first.converged

    exported_path = tmp_path / "roundtrip_export.xml"
    vg.FileSave(
        circuit=grid,
        file_name=str(exported_path),
        options=FileSavingOptions(file_type=FileType.CIM),
    ).save()

    roundtrip_grid = vg.open_file(str(exported_path), options=FileOpenOptions(file_type=FileType.CIM))
    assert any(bus.is_slack for bus in roundtrip_grid.buses)

    second = vg.power_flow(roundtrip_grid)
    assert second.converged
    assert np.allclose(first.voltage, second.voltage, atol=1e-6)


def test_cim_import_accepts_opendss_style_switch_topology(tmp_path):
    cim_path = tmp_path / "opendss_switch.xml"
    cim_path.write_text(
        textwrap.dedent(
            """\
            <?xml version="1.0" encoding="UTF-8"?>
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                     xmlns:cim="http://iec.ch/TC57/CIM100#">
              <cim:BaseVoltage rdf:ID="00000000-0000-0000-0000-0000000000b1">
                <cim:BaseVoltage.nominalVoltage>110</cim:BaseVoltage.nominalVoltage>
              </cim:BaseVoltage>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000101">
                <cim:IdentifiedObject.name>Bus 1</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:TopologicalNode rdf:ID="00000000-0000-0000-0000-000000000102">
                <cim:IdentifiedObject.name>Bus 2</cim:IdentifiedObject.name>
                <cim:TopologicalNode.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:TopologicalNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000201">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000101"/>
              </cim:ConnectivityNode>
              <cim:ConnectivityNode rdf:ID="00000000-0000-0000-0000-000000000202">
                <cim:ConnectivityNode.TopologicalNode rdf:resource="#00000000-0000-0000-0000-000000000102"/>
              </cim:ConnectivityNode>
              <cim:Switch rdf:ID="00000000-0000-0000-0000-000000000301">
                <cim:IdentifiedObject.name>SW 1</cim:IdentifiedObject.name>
                <cim:ConductingEquipment.BaseVoltage rdf:resource="#00000000-0000-0000-0000-0000000000b1"/>
              </cim:Switch>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000401">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000201"/>
                <cim:ACDCTerminal.sequenceNumber>1</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
              <cim:Terminal rdf:ID="00000000-0000-0000-0000-000000000402">
                <cim:Terminal.ConductingEquipment rdf:resource="#00000000-0000-0000-0000-000000000301"/>
                <cim:Terminal.ConnectivityNode rdf:resource="#00000000-0000-0000-0000-000000000202"/>
                <cim:ACDCTerminal.sequenceNumber>2</cim:ACDCTerminal.sequenceNumber>
              </cim:Terminal>
            </rdf:RDF>
            """
        ).strip()
    )

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.switch_devices) == 1
    assert grid.switch_devices[0].name == "SW 1"


def test_cim_roundtrip_preserves_exported_shunt_and_pf_solution(tmp_path):
    grid = MultiCircuit(name="CIM shunt roundtrip")
    substation = Substation(name="Substation 1")
    bus1 = Bus(name="Bus 1", Vnom=110, substation=substation, is_slack=True)
    bus2 = Bus(name="Bus 2", Vnom=110, substation=substation)
    grid.add_bus(bus1)
    grid.add_bus(bus2)
    grid.add_line(Line(bus_from=bus1, bus_to=bus2, name="Line 1", r=0.01, x=0.05, b=0, rate=100))
    grid.add_load(bus2, Load(name="Load 1", P=10, Q=5))
    grid.add_shunt(bus2, Shunt(name="Cap 1", G=0.1, B=0.2))

    first = vg.power_flow(grid)
    assert first.converged

    cim_path = tmp_path / "shunt_roundtrip.xml"
    vg.FileSave(
        circuit=grid,
        file_name=str(cim_path),
        options=FileSavingOptions(file_type=FileType.CIM),
    ).save()

    roundtrip_grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(roundtrip_grid.shunts) == 1
    assert roundtrip_grid.shunts[0].G == 0.1
    assert roundtrip_grid.shunts[0].B == 0.2

    second = vg.power_flow(roundtrip_grid)
    assert second.converged
    assert np.allclose(first.voltage, second.voltage, atol=1e-6)


def test_cim_roundtrip_preserves_open_dss_ieee13_cdpsm_solution(tmp_path):
    cim_path = Path(__file__).resolve().parents[4] / "benchmarks" / "roundtrips" / "cim" / "opendss" / "ieee13cdpsm.xml"

    grid = vg.open_file(str(cim_path), options=FileOpenOptions(file_type=FileType.CIM))

    assert len(grid.buses) == 22
    assert len(grid.lines) == 11
    assert len(grid.transformers2w) == 1
    assert len(grid.loads) == 16
    assert len(grid.shunts) == 2
    assert any(bus.is_slack for bus in grid.buses)

    first = vg.power_flow(grid)
    assert first.converged

    exported_path = tmp_path / "ieee13cdpsm_roundtrip.xml"
    vg.FileSave(
        circuit=grid,
        file_name=str(exported_path),
        options=FileSavingOptions(file_type=FileType.CIM),
    ).save()

    roundtrip_grid = vg.open_file(str(exported_path), options=FileOpenOptions(file_type=FileType.CIM))

    second = vg.power_flow(roundtrip_grid)
    assert second.converged
    assert np.allclose(first.voltage, second.voltage, atol=1e-6)
