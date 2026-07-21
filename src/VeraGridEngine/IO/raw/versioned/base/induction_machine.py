# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
import VeraGridEngine.Devices as dev
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_int


class RawInductionMachine(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=0,
                     max_value=999997),
        PsseProperty(property_name='ID', rawx_key='imid', class_type=str, description='One or  two character ID',
                     max_chars=2),
        PsseProperty(property_name='STAT', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='SCODE', rawx_key='scode', class_type=int,
                     description='Machine standard code: \n1:NEMA\n2:IEC', min_value=1, max_value=2),
        PsseProperty(property_name='DCODE', rawx_key='dcode', class_type=int,
                     description='Machine design code.\n•  0 - for Custom design with equivalent circuit reactances specified\n•  1 - for NEMA Design A\n•  2 - for NEMA Design B / IEC Design N\n•  3 - for NEMA Design C / IEC Design H\n•  4 - for NEMA Design D\n•  5 - for NEMA Design E',
                     min_value=0, max_value=5),
        PsseProperty(property_name='AREA', rawx_key='area', class_type=int, description='Area number'),
        PsseProperty(property_name='ZONE', rawx_key='zone', class_type=int, description='Zone number'),
        PsseProperty(property_name='OWNER', rawx_key='owner', class_type=int, description='Owner number'),
        PsseProperty(property_name='TCODE', rawx_key='tcode', class_type=int,
                     description='Type of mechanical load torque variation:\n•  1 - Simple power law\n•  2 - WECC model',
                     min_value=1, max_value=2),
        PsseProperty(property_name='BCODE', rawx_key='bcode', class_type=int,
                     description='Machine base power code:\n•  1 - Mechanical power (MW) output of the machine\n•  2 - Apparent electrical power (MVA) drawn by the machine',
                     min_value=1, max_value=2),
        PsseProperty(property_name='MBASE', rawx_key='mbase', class_type=float,
                     description='Nominal power (see the manual for more funkyness).', unit=Unit.get_mva()),
        PsseProperty(property_name='RATEKV', rawx_key='ratekv', class_type=float, description='Rated voltage',
                     unit=Unit.get_kv()),
        PsseProperty(property_name='PCODE', rawx_key='pcode', class_type=int, description='Scheduled power code',
                     min_value=1, max_value=2),
        PsseProperty(property_name='PSET', rawx_key='pset', class_type=float, unit=Unit.get_mw(),
                     description='Scheduled  active  power (see the manual).'),
        PsseProperty(property_name='H', rawx_key='hconst', class_type=float,
                     description='Machine inertia, in per unit on MBASE base.', unit=Unit.get_pu()),
        PsseProperty(property_name='A', rawx_key='aconst', class_type=float,
                     description='A parameter to model the torque of the mechanical load with speed. (see manual)'),
        PsseProperty(property_name='B', rawx_key='bconst', class_type=float,
                     description='B parameter to model the torque of the mechanical load with speed. (see manual)'),
        PsseProperty(property_name='D', rawx_key='dconst', class_type=float,
                     description='D parameter to model the torque of the mechanical load with speed. (see manual)'),
        PsseProperty(property_name='E', rawx_key='econst', class_type=float,
                     description='E parameter to model the torque of the mechanical load with speed. (see manual)'),
        PsseProperty(property_name='RA', rawx_key='ra', class_type=float, description='Armature resistance',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='XA', rawx_key='xa', class_type=float, description='Armature leakage reactance.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='XM', rawx_key='xm', class_type=float,
                     description='Unsaturated magnetizing reactance.', unit=Unit.get_pu()),
        PsseProperty(property_name='R1', rawx_key='r1', class_type=float,
                     description='Resistance of the first rotor winding.', unit=Unit.get_pu()),
        PsseProperty(property_name='X1', rawx_key='x1', class_type=float,
                     description='Reactance of the first rotor winding.', unit=Unit.get_pu()),
        PsseProperty(property_name='R2', rawx_key='r2', class_type=float,
                     description='Resistance of the second rotor winding.', unit=Unit.get_pu()),
        PsseProperty(property_name='X2', rawx_key='x2', class_type=float,
                     description='Reactance of the second rotor winding.', unit=Unit.get_pu()),
        PsseProperty(property_name='X3', rawx_key='x3', class_type=float, description='Third rotor reactance.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='E1', rawx_key='e1', class_type=float,
                     description='First terminal voltage point from the open circuit saturation  curve.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='SE1', rawx_key='se1', class_type=float,
                     description='Saturation factor at terminal voltage E1, S(E1).'),
        PsseProperty(property_name='E2', rawx_key='e2', class_type=float,
                     description='Second terminal voltage point from the open circuit saturation curve.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='SE2', rawx_key='se2', class_type=float,
                     description='Saturation factor at terminal voltage E2, S(E2)'),
        PsseProperty(property_name='IA1', rawx_key='ia1', class_type=float,
                     description='Stator currents in PU specifying saturation of the stator leakage reactance, XA.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='IA2', rawx_key='ia2', class_type=float,
                     description='Stator currents in PU specifying saturation of the stator leakage reactance, XA.',
                     unit=Unit.get_pu()),
        PsseProperty(property_name='XAMULT', rawx_key='xamult', class_type=float,
                     description='Multiplier for the saturated value. Allowed value 0 to 1.0.', unit=Unit.get_pu()),
    )

    def __init__(self):
        RawObject.__init__(self, "Induction machine")

        self.I = 0
        self.ID = "1"
        self.STAT = 1
        self.SCODE = 1
        self.DCODE = 2
        self.AREA = 0
        self.ZONE = 0
        self.OWNER = 0
        self.TCODE = 1
        self.BCODE = 1
        self.MBASE = 100
        self.RATEKV = 0
        self.PCODE = 1
        self.PSET = 0

        self.H = 1.0
        self.A = 1.0
        self.B = 1.0
        self.D = 1.0
        self.E = 1.0

        self.RA = 0
        self.XA = 0
        self.XM = 2.5

        self.R1 = 999.0
        self.X1 = 999.0
        self.R2 = 999.0
        self.X2 = 999.0
        self.X3 = 0.0

        self.E1 = 1.0
        self.SE1 = 0
        self.E2 = 1.2
        self.SE2 = 0
        self.IA1 = 0
        self.IA2 = 0
        self.XAMULT = 1.0

    def parse(self, data, version, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self):
        """
        Get the element PSSE ID
        :return:
        """
        return "{0}_{1}".format(self.I, self.ID)

    def get_object(self, logger: list):
        """
        Return Newton Load object
        Returns:
            Newton Load object
        """

        elm = dev.Generator(name=str(self.I) + '_' + str(self.ID),
                            P=self.PSET,
                            vset=self.RATEKV,
                            Snom=self.MBASE,
                            active=bool(self.STAT))

        return elm

    @property
    def STATUS(self):
        return self.STAT

    @STATUS.setter
    def STATUS(self, value: int | str | None) -> None:
        self.STAT = coerce_psse_int(value=value, current_value=self.STAT)
