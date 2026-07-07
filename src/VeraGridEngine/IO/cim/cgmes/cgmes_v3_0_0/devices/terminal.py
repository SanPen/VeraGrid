# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import TYPE_CHECKING
from VeraGridEngine.IO.base.units import UnitMultiplier, UnitSymbol
from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_terminal import ACDCTerminal
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import PhaseCode
from VeraGridEngine.IO.cim.cgmes.cgmes_property import CgmesProperty
if TYPE_CHECKING:
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.acdc_converter import ACDCConverter
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.auxiliary_equipment import AuxiliaryEquipment
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.conducting_equipment import ConductingEquipment
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.connectivity_node import ConnectivityNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.mutual_coupling import MutualCoupling
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.regulating_control import RegulatingControl
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.sv_power_flow import SvPowerFlow
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.tie_flow import TieFlow
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.topological_node import TopologicalNode
	from VeraGridEngine.IO.cim.cgmes.cgmes_v3_0_0.devices.transformer_end import TransformerEnd

class Terminal(ACDCTerminal):
	LOCAL_CGMES_PROPERTIES: tuple[CgmesProperty, ...] = (
		CgmesProperty(property_name='ConverterDCSides', class_type='ACDCConverter', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All converters' DC sides linked to this point of common coupling terminal.''', profiles=[]),
		CgmesProperty(property_name='AuxiliaryEquipment', class_type='AuxiliaryEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The auxiliary equipment connected to the terminal.''', profiles=[]),
		CgmesProperty(property_name='ConductingEquipment', class_type='ConductingEquipment', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The conducting equipment of the terminal.  Conducting equipment have  terminals that may be connected to other conducting equipment terminals via connectivity nodes or topological nodes.''', profiles=[]),
		CgmesProperty(property_name='ConnectivityNode', class_type='ConnectivityNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The connectivity node to which this terminal connects with zero impedance.''', profiles=[]),
		CgmesProperty(property_name='RegulatingControl', class_type='RegulatingControl', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The controls regulating this terminal.''', profiles=[]),
		CgmesProperty(property_name='phases', class_type=PhaseCode, multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Represents the normal network phasing condition. If the attribute is missing, three phases (ABC) shall be assumed, except for terminals of grounding classes (specializations of EarthFaultCompensator, GroundDisconnector, and Ground) which will be assumed to be N. Therefore, phase code ABCN is explicitly declared when needed, e.g. for star point grounding equipment.
The phase code on terminals connecting same ConnectivityNode or same TopologicalNode as well as for equipment between two terminals shall be consistent.''', profiles=[]),
		CgmesProperty(property_name='TransformerEnd', class_type='TransformerEnd', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''All transformer ends connected at this terminal.''', profiles=[]),
		CgmesProperty(property_name='TieFlow', class_type='TieFlow', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The control area tie flows to which this terminal associates.''', profiles=[]),
		CgmesProperty(property_name='SvPowerFlow', class_type='SvPowerFlow', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The power flow state variable associated with the terminal.''', profiles=[]),
		CgmesProperty(property_name='TopologicalNode', class_type='TopologicalNode', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''The topological node associated with the terminal.   This can be used as an alternative to the connectivity node path to topological node, thus making it unnecessary to model connectivity nodes in some cases.   Note that the if connectivity nodes are in the model, this association would probably not be used as an input specification.''', profiles=[]),
		CgmesProperty(property_name='HasSecondMutualCoupling', class_type='MutualCoupling', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Mutual couplings with the branch associated as the first branch.''', profiles=[]),
		CgmesProperty(property_name='HasFirstMutualCoupling', class_type='MutualCoupling', multiplier=UnitMultiplier.none, unit=UnitSymbol.none, description='''Mutual couplings associated with the branch as the first branch.''', profiles=[]),
	)
	__slots__ = ('ConverterDCSides', 'AuxiliaryEquipment', 'ConductingEquipment', 'ConnectivityNode', 'RegulatingControl', 'phases', 'TransformerEnd', 'TieFlow', 'SvPowerFlow', 'TopologicalNode', 'HasSecondMutualCoupling', 'HasFirstMutualCoupling')
	def __init__(self, rdfid='', tpe='Terminal'):
		ACDCTerminal.__init__(self, rdfid, tpe)

		self.ConverterDCSides: ACDCConverter | None = None
		self.AuxiliaryEquipment: AuxiliaryEquipment | None = None
		self.ConductingEquipment: ConductingEquipment | None = None
		self.ConnectivityNode: ConnectivityNode | None = None
		self.RegulatingControl: RegulatingControl | None = None
		self.phases: PhaseCode = None
		self.TransformerEnd: TransformerEnd | None = None
		self.TieFlow: TieFlow | None = None
		self.SvPowerFlow: SvPowerFlow | None = None
		self.TopologicalNode: TopologicalNode | None = None
		self.HasSecondMutualCoupling: MutualCoupling | None = None
		self.HasFirstMutualCoupling: MutualCoupling | None = None
