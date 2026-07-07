# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple

from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.psse_property import PsseProperty


class RawSwitchedShunt(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus number', min_value=1,
                     max_value=999997, max_chars=6),
        PsseProperty(property_name='ID', rawx_key='shntid', class_type=str, description='Load 2-character ID',
                     max_chars=2),
        PsseProperty(property_name='MODSW', rawx_key='modsw', class_type=int, description='Control mode', min_value=0,
                     max_value=6),
        PsseProperty(property_name='ADJM', rawx_key='adjm', class_type=int, description='Adjustment method',
                     min_value=0, max_value=1),
        PsseProperty(property_name='STAT', rawx_key='stat', class_type=int, description='Status', min_value=0,
                     max_value=1),
        PsseProperty(property_name='VSWHI', rawx_key='vswhi', class_type=float,
                     description='Controlled voltage upper limit', unit=Unit.get_pu()),
        PsseProperty(property_name='VSWLO', rawx_key='vswlo', class_type=float,
                     description='Controlled voltage upper limit', unit=Unit.get_pu()),
        PsseProperty(property_name='SWREG', rawx_key='swreg', class_type=int, description='Controlled voltage bus',
                     min_value=0, max_value=999997),
        PsseProperty(property_name='SWREM', rawx_key='swrem', class_type=int,
                     description='Controlled bus or plant bus for pre-35 switched shunt formats',
                     min_value=0, max_value=999997),
        PsseProperty(property_name='NREG', rawx_key='nreg', class_type=int,
                     description="Node number of bus IREG when IREG's bus is a substation", min_value=0,
                     max_value=999997),
        PsseProperty(property_name='RMPCT', rawx_key='rmpct', class_type=float,
                     description='Percent of the total Mvar required to hold the voltage at the control bus',
                     min_value=0, max_value=100.0, unit=Unit.get_percent()),
        PsseProperty(property_name='RMIDNT', rawx_key='rmidnt', class_type=str,
                     description='Controlled branch for VSC like operation'),
        PsseProperty(property_name='BINIT', rawx_key='binit', class_type=float,
                     description='Initial switched shunt admittance', unit=Unit.get_pu()),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str,
                     description='Switched shunt name', max_chars=12),
        PsseProperty(property_name='S{}'.format(0 + 1), rawx_key='s{}'.format(0 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(1 + 1), rawx_key='s{}'.format(1 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(2 + 1), rawx_key='s{}'.format(2 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(3 + 1), rawx_key='s{}'.format(3 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(4 + 1), rawx_key='s{}'.format(4 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(5 + 1), rawx_key='s{}'.format(5 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(6 + 1), rawx_key='s{}'.format(6 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='S{}'.format(7 + 1), rawx_key='s{}'.format(7 + 1), class_type=int,
                     description='Initial switched shunt status of one for in-service and zero for out-of-service for block i',
                     min_value=0, max_value=1),
        PsseProperty(property_name='N{}'.format(0 + 1), rawx_key='n{}'.format(0 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(1 + 1), rawx_key='n{}'.format(1 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(2 + 1), rawx_key='n{}'.format(2 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(3 + 1), rawx_key='n{}'.format(3 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(4 + 1), rawx_key='n{}'.format(4 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(5 + 1), rawx_key='n{}'.format(5 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(6 + 1), rawx_key='n{}'.format(6 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='N{}'.format(7 + 1), rawx_key='n{}'.format(7 + 1), class_type=int,
                     description='Number of steps for block i', min_value=0, max_value=99999),
        PsseProperty(property_name='B{}'.format(0 + 1), rawx_key='b{}'.format(0 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(1 + 1), rawx_key='b{}'.format(1 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(2 + 1), rawx_key='b{}'.format(2 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(3 + 1), rawx_key='b{}'.format(3 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(4 + 1), rawx_key='b{}'.format(4 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(5 + 1), rawx_key='b{}'.format(5 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(6 + 1), rawx_key='b{}'.format(6 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
        PsseProperty(property_name='B{}'.format(7 + 1), rawx_key='b{}'.format(7 + 1), class_type=float,
                     description='Admittance increment for each of Ni steps in block i;', unit=Unit.get_mvar()),
    )

    def __init__(self):
        RawObject.__init__(self, "Switched shunt")

        self.I = 0
        self.ID = ''
        '''
        MODSW:
        0 - locked
        1 - discrete adjustment, local voltage control
        2 - continuous adjustment, local voltage control
        3 - discrete adjustment, local generator reactive power control (WTF?)
        4 - discrete adjustment, branch voltage control (see RMIDNT)
        5 - discrete adjustment, local admittance control (WTF?)
        6 - discrete adjustment, reactive power control for FACTS (see RMIDNT)
        '''
        self.MODSW = 0
        self.ADJM = 0
        self.STAT = 0
        self.VSWHI = 1
        self.VSWLO = 1
        self.SWREM = 0
        self.SWREG = 0
        self.NREG = 0
        self.RMPCT = 1
        self.RMIDNT = ''
        self.BINIT = 0
        self.NAME = ''

        self.S1 = 0
        self.S2 = 0
        self.S3 = 0
        self.S4 = 0
        self.S5 = 0
        self.S6 = 0
        self.S7 = 0
        self.S8 = 0

        self.N1 = 0
        self.N2 = 0
        self.N3 = 0
        self.N4 = 0
        self.N5 = 0
        self.N6 = 0
        self.N7 = 0
        self.N8 = 0

        self.B1 = 0.0
        self.B2 = 0.0
        self.B3 = 0.0
        self.B4 = 0.0
        self.B5 = 0.0
        self.B6 = 0.0
        self.B7 = 0.0
        self.B8 = 0.0

    def set_block_status(self, index: int, value: int) -> None:
        if index == 1:
            self.S1 = value
        elif index == 2:
            self.S2 = value
        elif index == 3:
            self.S3 = value
        elif index == 4:
            self.S4 = value
        elif index == 5:
            self.S5 = value
        elif index == 6:
            self.S6 = value
        elif index == 7:
            self.S7 = value
        else:
            self.S8 = value

    def get_block_status(self, index: int) -> int:
        if index == 1:
            return self.S1
        elif index == 2:
            return self.S2
        elif index == 3:
            return self.S3
        elif index == 4:
            return self.S4
        elif index == 5:
            return self.S5
        elif index == 6:
            return self.S6
        elif index == 7:
            return self.S7
        return self.S8

    def set_block_steps(self, index: int, value: int) -> None:
        if index == 1:
            self.N1 = value
        elif index == 2:
            self.N2 = value
        elif index == 3:
            self.N3 = value
        elif index == 4:
            self.N4 = value
        elif index == 5:
            self.N5 = value
        elif index == 6:
            self.N6 = value
        elif index == 7:
            self.N7 = value
        else:
            self.N8 = value

    def get_block_steps(self, index: int) -> int:
        if index == 1:
            return self.N1
        elif index == 2:
            return self.N2
        elif index == 3:
            return self.N3
        elif index == 4:
            return self.N4
        elif index == 5:
            return self.N5
        elif index == 6:
            return self.N6
        elif index == 7:
            return self.N7
        return self.N8

    def set_block_admittance(self, index: int, value: float) -> None:
        if index == 1:
            self.B1 = value
        elif index == 2:
            self.B2 = value
        elif index == 3:
            self.B3 = value
        elif index == 4:
            self.B4 = value
        elif index == 5:
            self.B5 = value
        elif index == 6:
            self.B6 = value
        elif index == 7:
            self.B7 = value
        else:
            self.B8 = value

    def get_block_admittance(self, index: int) -> float:
        if index == 1:
            return self.B1
        elif index == 2:
            return self.B2
        elif index == 3:
            return self.B3
        elif index == 4:
            return self.B4
        elif index == 5:
            return self.B5
        elif index == 6:
            return self.B6
        elif index == 7:
            return self.B7
        return self.B8

    def set_block(self, index: int, status: int, steps: int, admittance: float) -> None:
        self.set_block_status(index, status)
        self.set_block_steps(index, steps)
        self.set_block_admittance(index, admittance)

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
