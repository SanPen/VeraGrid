# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Tuple, List
from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_object import RawObject
from VeraGridEngine.basic_structures import Logger
import numpy as np
from VeraGridEngine.IO.raw.psse_property import PsseProperty, coerce_psse_float


class RawTransformer(RawObject):
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name='I', rawx_key='ibus', class_type=int, description='Bus I number', min_value=0,
                     max_value=999999, max_chars=6),
        PsseProperty(property_name='J', rawx_key='jbus', class_type=int, description='Bus J number', min_value=0,
                     max_value=999999, max_chars=6),
        PsseProperty(property_name='K', rawx_key='kbus', class_type=int, description='Bus K number', min_value=0,
                     max_value=999999, max_chars=6),
        PsseProperty(property_name='CKT', rawx_key='ckt', class_type=str, description='Circuit identifier',
                     max_chars=2),
        PsseProperty(property_name='CW', rawx_key='cw', class_type=int, description='Winding input mode', min_value=1,
                     max_value=3, max_chars=1),
        PsseProperty(property_name='CZ', rawx_key='cz', class_type=int, description='Series Impedance input mode',
                     min_value=1, max_value=3, max_chars=1),
        PsseProperty(property_name='CM', rawx_key='cm', class_type=int, description='Magnetizing impedance input mode',
                     min_value=1, max_value=2, max_chars=1),
        PsseProperty(property_name='MAG1', rawx_key='mag1', class_type=float, description='Magnetizing admittance 1'),
        PsseProperty(property_name='MAG2', rawx_key='mag2', class_type=float, description='Magnetizing admittance 2'),
        PsseProperty(property_name='NMETR', rawx_key='nmet', class_type=int, description='Non-metered end code',
                     min_value=1, max_value=3, max_chars=1),
        PsseProperty(property_name='NAME', rawx_key='name', class_type=str, description='Name', max_chars=12),
        PsseProperty(property_name='STAT', rawx_key='stat', class_type=int,
                     description='Status of the several windings', min_value=0, max_value=4, max_chars=1),
        PsseProperty(property_name='VECGRP', rawx_key='vecgrp', class_type=str,
                     description='Vector group (has zero effect, information only)', max_chars=12),
        PsseProperty(property_name='ZCOD', rawx_key='zcod', class_type=int, description='Impedance code', min_value=0,
                     max_value=1),
        PsseProperty(property_name='R1_2', rawx_key='r1_2', class_type=float,
                     description='1->2 resistance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='X1_2', rawx_key='x1_2', class_type=float,
                     description='1->2 reactance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='R2_3', rawx_key='r2_3', class_type=float,
                     description='2->3 resistance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='X2_3', rawx_key='x2_3', class_type=float,
                     description='2->3 reactance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='R3_1', rawx_key='r3_1', class_type=float,
                     description='3->1 resistance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='X3_1', rawx_key='x3_1', class_type=float,
                     description='3->1 reactance or other stuff', unit=Unit.get_pu(), format_rule='.5E'),
        PsseProperty(property_name='SBASE1_2', rawx_key='sbase1_2', class_type=float, description='1->2 base power',
                     unit=Unit.get_mvar(), format_rule='.2f'),
        PsseProperty(property_name='SBASE2_3', rawx_key='sbase2_3', class_type=float, description='2->3 base power',
                     unit=Unit.get_mvar(), format_rule='.2f'),
        PsseProperty(property_name='SBASE3_1', rawx_key='sbase3_1', class_type=float, description='3->1 base power',
                     unit=Unit.get_mvar(), format_rule='.2f'),
        PsseProperty(property_name='VMSTAR', rawx_key='vmstar', class_type=float,
                     description='The voltage magnitude at the center star point', unit=Unit.get_pu(),
                     format_rule='.5f'),
        PsseProperty(property_name='ANSTAR', rawx_key='anstar', class_type=float,
                     description='The bus voltage phase angle at the center star point.', unit=Unit.get_deg(),
                     format_rule='.4f'),
        PsseProperty(property_name='WINDV1', rawx_key='windv1', class_type=float,
                     description='Winding 1 off-nominal turns ratio or other stuff', format_rule='.5f'),
        PsseProperty(property_name='NOMV1', rawx_key='nomv1', class_type=float,
                     description='Winding 1 voltage base in kV or other stuff', unit=Unit.get_kv(), format_rule='.3f'),
        PsseProperty(property_name='ANG1', rawx_key='ang1', class_type=float,
                     description='Winding 1 phase shift angle in degrees.', unit=Unit.get_deg(), format_rule='.3f'),
        PsseProperty(property_name='COD1', rawx_key='cod1', class_type=int, description='Winding 1 control mode.',
                     min_value=-5, max_value=5),
        PsseProperty(property_name='CONT1', rawx_key='cont1', class_type=int,
                     description='Control bus for the winding 1.', min_value=0, max_value=999999),
        PsseProperty(property_name='NODE1', rawx_key='node1', class_type=int, description='A node number of bus CONT1.',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='RMA1', rawx_key='rma1', class_type=float,
                     description='Winding 1 upper limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='RMI1', rawx_key='rmi1', class_type=float,
                     description='Winding 1 lower limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='VMA1', rawx_key='vma1', class_type=float,
                     description='Winding 1 upper voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='VMI1', rawx_key='vmi1', class_type=float,
                     description='Winding 1 lower voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='NTP1', rawx_key='ntp1', class_type=int,
                     description='Winding 1 number of tap positions available', min_value=2, max_value=9999),
        PsseProperty(property_name='TAB1', rawx_key='tab1', class_type=int,
                     description='Winding 1  number  of  a  transformer  impedance  correction  table', min_value=0,
                     max_value=999999),
        PsseProperty(property_name='CR1', rawx_key='cr1', class_type=float,
                     description='Winding 1 load drop compensation resistance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CX1', rawx_key='cx1', class_type=float,
                     description='Winding 1 load drop compensation reactance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CNXA1', rawx_key='cnxa1', class_type=float, description='', min_value=0,
                     max_value=999999, format_rule='.3f'),
        PsseProperty(property_name='RATA1', rawx_key='rata1', class_type=float,
                     description='Winding 1 rating set A', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATB1', rawx_key='ratb1', class_type=float,
                     description='Winding 1 rating set B', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATC1', rawx_key='ratc1', class_type=float,
                     description='Winding 1 rating set C', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(1), rawx_key='wdg1rate{}'.format(1), class_type=float,
                     description='Winding rating {}'.format(1), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(2), rawx_key='wdg1rate{}'.format(2), class_type=float,
                     description='Winding rating {}'.format(2), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(3), rawx_key='wdg1rate{}'.format(3), class_type=float,
                     description='Winding rating {}'.format(3), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(4), rawx_key='wdg1rate{}'.format(4), class_type=float,
                     description='Winding rating {}'.format(4), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(5), rawx_key='wdg1rate{}'.format(5), class_type=float,
                     description='Winding rating {}'.format(5), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(6), rawx_key='wdg1rate{}'.format(6), class_type=float,
                     description='Winding rating {}'.format(6), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(7), rawx_key='wdg1rate{}'.format(7), class_type=float,
                     description='Winding rating {}'.format(7), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(8), rawx_key='wdg1rate{}'.format(8), class_type=float,
                     description='Winding rating {}'.format(8), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(9), rawx_key='wdg1rate{}'.format(9), class_type=float,
                     description='Winding rating {}'.format(9), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(10), rawx_key='wdg1rate{}'.format(10), class_type=float,
                     description='Winding rating {}'.format(10), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(11), rawx_key='wdg1rate{}'.format(11), class_type=float,
                     description='Winding rating {}'.format(11), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE1_{}'.format(12), rawx_key='wdg1rate{}'.format(12), class_type=float,
                     description='Winding rating {}'.format(12), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='WINDV2', rawx_key='windv2', class_type=float,
                     description='Winding 2 off-nominal turns ratio or other stuff', format_rule='.5f'),
        PsseProperty(property_name='NOMV2', rawx_key='nomv2', class_type=float,
                     description='Winding 2 voltage base in kV or other stuff', unit=Unit.get_kv(), format_rule='.3f'),
        PsseProperty(property_name='ANG2', rawx_key='ang2', class_type=float,
                     description='Winding 2 phase shift angle in degrees.', unit=Unit.get_deg(), format_rule='.3f'),
        PsseProperty(property_name='COD2', rawx_key='cod2', class_type=int, description='Winding 2 control mode.',
                     min_value=-5, max_value=5),
        PsseProperty(property_name='CONT2', rawx_key='cont2', class_type=int,
                     description='Control bus for the winding 2.', min_value=0, max_value=999999),
        PsseProperty(property_name='NODE2', rawx_key='node2', class_type=int, description='A node number of bus CONT1.',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='RMA2', rawx_key='rma2', class_type=float,
                     description='Winding 2 upper limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='RMI2', rawx_key='rmi2', class_type=float,
                     description='Winding 2 lower limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='VMA2', rawx_key='vma2', class_type=float,
                     description='Winding 2 upper voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='VMI2', rawx_key='vmi2', class_type=float,
                     description='Winding 2 lower voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='NTP2', rawx_key='ntp2', class_type=int,
                     description='Winding 2 number of tap positions available', min_value=2, max_value=9999),
        PsseProperty(property_name='TAB2', rawx_key='tab2', class_type=int,
                     description='Winding 2 number  of  a  transformer  impedance  correction  table', min_value=0,
                     max_value=999999),
        PsseProperty(property_name='CR2', rawx_key='cr2', class_type=float,
                     description='Winding 2 load drop compensation resistance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CX2', rawx_key='cx2', class_type=float,
                     description='Winding 1 load drop compensation reactance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CNXA2', rawx_key='cnxa2', class_type=float, description='', min_value=0,
                     max_value=999999, format_rule='.3f'),
        PsseProperty(property_name='RATA2', rawx_key='rata2', class_type=float,
                     description='Winding 2 rating set A', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATB2', rawx_key='ratb2', class_type=float,
                     description='Winding 2 rating set B', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATC2', rawx_key='ratc2', class_type=float,
                     description='Winding 2 rating set C', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(1), rawx_key='wdg2rate{}'.format(1), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(2), rawx_key='wdg2rate{}'.format(2), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(3), rawx_key='wdg2rate{}'.format(3), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(4), rawx_key='wdg2rate{}'.format(4), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(5), rawx_key='wdg2rate{}'.format(5), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(6), rawx_key='wdg2rate{}'.format(6), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(7), rawx_key='wdg2rate{}'.format(7), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(8), rawx_key='wdg2rate{}'.format(8), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(9), rawx_key='wdg2rate{}'.format(9), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(10), rawx_key='wdg2rate{}'.format(10), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(11), rawx_key='wdg2rate{}'.format(11), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE2_{}'.format(12), rawx_key='wdg2rate{}'.format(12), class_type=float,
                     description='Winding rating', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='WINDV3', rawx_key='windv3', class_type=float,
                     description='Winding 3 off-nominal turns ratio or other stuff', format_rule='.5f'),
        PsseProperty(property_name='NOMV3', rawx_key='nomv3', class_type=float,
                     description='Winding 3 voltage base in kV or other stuff', unit=Unit.get_kv(), format_rule='.3f'),
        PsseProperty(property_name='ANG3', rawx_key='ang3', class_type=float,
                     description='Winding 3 phase shift angle in degrees.', unit=Unit.get_deg(), format_rule='.3f'),
        PsseProperty(property_name='COD3', rawx_key='cod3', class_type=int, description='Winding 3 control mode.',
                     min_value=-5, max_value=5),
        PsseProperty(property_name='CONT3', rawx_key='cont3', class_type=int,
                     description='Control bus for the winding 3', min_value=0, max_value=999999),
        PsseProperty(property_name='NODE3', rawx_key='node3', class_type=int, description='A node number of bus CONT3.',
                     min_value=0, max_value=999999),
        PsseProperty(property_name='RMA3', rawx_key='rma3', class_type=float,
                     description='Winding 3 upper limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='RMI3', rawx_key='rmi3', class_type=float,
                     description='Winding 3 lower limit depending of COD1 and CW', format_rule='.5f'),
        PsseProperty(property_name='VMA3', rawx_key='vma3', class_type=float,
                     description='Winding 3 upper voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='VMI3', rawx_key='vmi3', class_type=float,
                     description='Winding 3 lower voltage limit depending of COD1.', format_rule='.5f'),
        PsseProperty(property_name='NTP3', rawx_key='ntp3', class_type=int,
                     description='Winding 3 number of tap positions available', min_value=2, max_value=9999),
        PsseProperty(property_name='TAB3', rawx_key='tab3', class_type=int,
                     description='Winding 1 number of a transformer impedance correction table', min_value=0,
                     max_value=999999),
        PsseProperty(property_name='CR3', rawx_key='cr3', class_type=float,
                     description='Winding 3 load drop compensation resistance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CX3', rawx_key='cx3', class_type=float,
                     description='Winding 3 load drop compensation reactance', unit=Unit.get_pu(), format_rule='.5f'),
        PsseProperty(property_name='CNXA3', rawx_key='cnxa3', class_type=float, description='', min_value=0,
                     max_value=999999, format_rule='.3f'),
        PsseProperty(property_name='RATA3', rawx_key='rata3', class_type=float,
                     description='Winding 3 rating set A', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATB3', rawx_key='ratb3', class_type=float,
                     description='Winding 3 rating set B', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATC3', rawx_key='ratc3', class_type=float,
                     description='Winding 3 rating set C', unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(1), rawx_key='wdg3rate{}'.format(1), class_type=float,
                     description='Winding 3 rating {}'.format(1), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(2), rawx_key='wdg3rate{}'.format(2), class_type=float,
                     description='Winding 3 rating {}'.format(2), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(3), rawx_key='wdg3rate{}'.format(3), class_type=float,
                     description='Winding 3 rating {}'.format(3), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(4), rawx_key='wdg3rate{}'.format(4), class_type=float,
                     description='Winding 3 rating {}'.format(4), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(5), rawx_key='wdg3rate{}'.format(5), class_type=float,
                     description='Winding 3 rating {}'.format(5), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(6), rawx_key='wdg3rate{}'.format(6), class_type=float,
                     description='Winding 3 rating {}'.format(6), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(7), rawx_key='wdg3rate{}'.format(7), class_type=float,
                     description='Winding 3 rating {}'.format(7), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(8), rawx_key='wdg3rate{}'.format(8), class_type=float,
                     description='Winding 3 rating {}'.format(8), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(9), rawx_key='wdg3rate{}'.format(9), class_type=float,
                     description='Winding 3 rating {}'.format(9), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(10), rawx_key='wdg3rate{}'.format(10), class_type=float,
                     description='Winding 3 rating {}'.format(10), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(11), rawx_key='wdg3rate{}'.format(11), class_type=float,
                     description='Winding 3 rating {}'.format(11), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='RATE3_{}'.format(12), rawx_key='wdg3rate{}'.format(12), class_type=float,
                     description='Winding 3 rating {}'.format(12), unit=Unit.get_mva(), format_rule='.2f'),
        PsseProperty(property_name='O{}'.format(0 + 1), rawx_key='o{}'.format(0 + 1), class_type=int,
                     description='Owner number {}'.format(0 + 1), min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(0 + 1), rawx_key='f{}'.format(0 + 1), class_type=float,
                     description='Ownership fraction {}'.format(0 + 1), min_value=0.0, max_value=1.0,
                     format_rule='.4f'),
        PsseProperty(property_name='O{}'.format(1 + 1), rawx_key='o{}'.format(1 + 1), class_type=int,
                     description='Owner number {}'.format(1 + 1), min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(1 + 1), rawx_key='f{}'.format(1 + 1), class_type=float,
                     description='Ownership fraction {}'.format(1 + 1), min_value=0.0, max_value=1.0,
                     format_rule='.4f'),
        PsseProperty(property_name='O{}'.format(2 + 1), rawx_key='o{}'.format(2 + 1), class_type=int,
                     description='Owner number {}'.format(2 + 1), min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(2 + 1), rawx_key='f{}'.format(2 + 1), class_type=float,
                     description='Ownership fraction {}'.format(2 + 1), min_value=0.0, max_value=1.0,
                     format_rule='.4f'),
        PsseProperty(property_name='O{}'.format(3 + 1), rawx_key='o{}'.format(3 + 1), class_type=int,
                     description='Owner number {}'.format(3 + 1), min_value=1, max_value=9999, max_chars=4),
        PsseProperty(property_name='F{}'.format(3 + 1), rawx_key='f{}'.format(3 + 1), class_type=float,
                     description='Ownership fraction {}'.format(3 + 1), min_value=0.0, max_value=1.0,
                     format_rule='.4f'),
    )

    def __init__(self):
        RawObject.__init__(self, "Transformer")

        self.windings = 0

        self.I = 0
        self.J = 0
        self.K = 0
        self.CKT = 0
        self.CW = 1
        self.CZ = 1
        self.CM = 1
        self.MAG1 = 0
        self.MAG2 = 0
        self.NMETR = 2
        self.NAME = ""
        self.STAT = 1
        self.VECGRP = ""
        self.ZCOD = 0

        self.R1_2 = 0.0
        self.X1_2 = 0.0
        self.R2_3 = 0.0
        self.X2_3 = 0.0
        self.R3_1 = 0.0
        self.X3_1 = 0.0

        self.SBASE1_2 = 100.0
        self.SBASE2_3 = 100.0
        self.SBASE3_1 = 100.0

        self.VMSTAR = 1.0
        self.ANSTAR = 0.0

        self.WINDV1 = 1.0
        self.NOMV1 = 0
        self.ANG1 = 0

        self.COD1 = 0
        self.CONT1 = 0
        self.NODE1 = 0
        self.RMA1 = 1.5
        self.RMI1 = 0.51
        self.VMA1 = 1.1
        self.VMI1 = 0.9
        self.NTP1 = 33
        self.TAB1 = 0  # number of the impedance correction table
        self.CR1 = 0
        self.CX1 = 0
        self.CNXA1 = 0

        self.WINDV2 = 0
        self.NOMV2 = 0

        # in case of 3 W
        self.ANG2 = 0

        self.COD2 = 0
        self.CONT2 = 0
        self.NODE2 = 0
        self.RMA2 = 1.1
        self.RMI2 = 0.9
        self.VMA2 = 1.1
        self.VMI2 = 0.9
        self.NTP2 = 33
        self.TAB2 = 0  # number of the impedance correction table
        self.CR2 = 0
        self.CX2 = 0
        self.CNXA2 = 0

        self.WINDV3 = 0
        self.NOMV3 = 0
        self.ANG3 = 0

        self.COD3 = 0
        self.CONT3 = 0
        self.NODE3 = 0
        self.RMA3 = 1.1
        self.RMI3 = 0.9
        self.VMA3 = 1.1
        self.VMI3 = 0.9
        self.NTP3 = 0
        self.TAB3 = 0  # number of the impedance correction table
        self.CR3 = 0
        self.CX3 = 0
        self.CNXA3 = 0

        self.RATE1_1 = 0
        self.RATE1_2 = 0
        self.RATE1_3 = 0
        self.RATE1_4 = 0
        self.RATE1_5 = 0
        self.RATE1_6 = 0
        self.RATE1_7 = 0
        self.RATE1_8 = 0
        self.RATE1_9 = 0
        self.RATE1_10 = 0
        self.RATE1_11 = 0
        self.RATE1_12 = 0

        self.RATE2_1 = 0
        self.RATE2_2 = 0
        self.RATE2_3 = 0
        self.RATE2_4 = 0
        self.RATE2_5 = 0
        self.RATE2_6 = 0
        self.RATE2_7 = 0
        self.RATE2_8 = 0
        self.RATE2_9 = 0
        self.RATE2_10 = 0
        self.RATE2_11 = 0
        self.RATE2_12 = 0

        self.RATE3_1 = 0
        self.RATE3_2 = 0
        self.RATE3_3 = 0
        self.RATE3_4 = 0
        self.RATE3_5 = 0
        self.RATE3_6 = 0
        self.RATE3_7 = 0
        self.RATE3_8 = 0
        self.RATE3_9 = 0
        self.RATE3_10 = 0
        self.RATE3_11 = 0
        self.RATE3_12 = 0

        self.O1 = 1
        self.F1 = 1.0
        self.O2 = 0
        self.F2 = 1.0
        self.O3 = 0
        self.F3 = 1.0
        self.O4 = 0
        self.F4 = 1.0

        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------

        # --------------------------------------------------------------------------------------------------------------

    def parse(self, data: List[List[float | int | str]], version: int, logger: Logger):
        raise NotImplementedError(f"{self.__class__.__name__}.parse must be implemented in a version-specific subclass")

    def get_raw_line(self, version):
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_raw_line must be implemented in a version-specific subclass"
        )

    def get_id(self):

        if self.windings == 2:
            return "{0}_{1}_{2}".format(self.I, self.J, self.CKT)
        elif self.windings == 3:
            return "{0}_{1}_{2}_{3}".format(self.I, self.J, self.K, self.CKT)
        else:
            raise Exception("unsupported number of windings")

    @property
    def RATA1(self):
        return self.RATE1_1

    @RATA1.setter
    def RATA1(self, value: float | int | str | None) -> None:
        self.RATE1_1 = coerce_psse_float(value=value, current_value=self.RATE1_1)

    @property
    def RATB1(self):
        return self.RATE1_2

    @RATB1.setter
    def RATB1(self, value: float | int | str | None) -> None:
        self.RATE1_2 = coerce_psse_float(value=value, current_value=self.RATE1_2)

    @property
    def RATC1(self):
        return self.RATE1_3

    @RATC1.setter
    def RATC1(self, value: float | int | str | None) -> None:
        self.RATE1_3 = coerce_psse_float(value=value, current_value=self.RATE1_3)

    @property
    def RATA2(self):
        return self.RATE2_1

    @RATA2.setter
    def RATA2(self, value: float | int | str | None) -> None:
        self.RATE2_1 = coerce_psse_float(value=value, current_value=self.RATE2_1)

    @property
    def RATB2(self):
        return self.RATE2_2

    @RATB2.setter
    def RATB2(self, value: float | int | str | None) -> None:
        self.RATE2_2 = coerce_psse_float(value=value, current_value=self.RATE2_2)

    @property
    def RATC2(self):
        return self.RATE2_3

    @RATC2.setter
    def RATC2(self, value: float | int | str | None) -> None:
        self.RATE2_3 = coerce_psse_float(value=value, current_value=self.RATE2_3)

    @property
    def RATA3(self):
        return self.RATE3_1

    @RATA3.setter
    def RATA3(self, value: float | int | str | None) -> None:
        self.RATE3_1 = coerce_psse_float(value=value, current_value=self.RATE3_1)

    @property
    def RATB3(self):
        return self.RATE3_2

    @RATB3.setter
    def RATB3(self, value: float | int | str | None) -> None:
        self.RATE3_2 = coerce_psse_float(value=value, current_value=self.RATE3_2)

    @property
    def RATC3(self):
        return self.RATE3_3

    @RATC3.setter
    def RATC3(self, value: float | int | str | None) -> None:
        self.RATE3_3 = coerce_psse_float(value=value, current_value=self.RATE3_3)

    def set_winding_record(self,
                           winding_index: int,
                           windv: float,
                           nomv: float,
                           ang: float,
                           cod: int,
                           cont: int,
                           node: int,
                           rma: float,
                           rmi: float,
                           vma: float,
                           vmi: float,
                           ntp: int,
                           tab: int,
                           cr: float,
                           cx: float,
                           cnxa: float) -> None:
        if winding_index == 1:
            self.WINDV1 = windv
            self.NOMV1 = nomv
            self.ANG1 = ang
            self.COD1 = cod
            self.CONT1 = cont
            self.NODE1 = node
            self.RMA1 = rma
            self.RMI1 = rmi
            self.VMA1 = vma
            self.VMI1 = vmi
            self.NTP1 = ntp
            self.TAB1 = tab
            self.CR1 = cr
            self.CX1 = cx
            self.CNXA1 = cnxa
        elif winding_index == 2:
            self.WINDV2 = windv
            self.NOMV2 = nomv
            self.ANG2 = ang
            self.COD2 = cod
            self.CONT2 = cont
            self.NODE2 = node
            self.RMA2 = rma
            self.RMI2 = rmi
            self.VMA2 = vma
            self.VMI2 = vmi
            self.NTP2 = ntp
            self.TAB2 = tab
            self.CR2 = cr
            self.CX2 = cx
            self.CNXA2 = cnxa
        else:
            self.WINDV3 = windv
            self.NOMV3 = nomv
            self.ANG3 = ang
            self.COD3 = cod
            self.CONT3 = cont
            self.NODE3 = node
            self.RMA3 = rma
            self.RMI3 = rmi
            self.VMA3 = vma
            self.VMI3 = vmi
            self.NTP3 = ntp
            self.TAB3 = tab
            self.CR3 = cr
            self.CX3 = cx
            self.CNXA3 = cnxa

    def set_numbered_winding_rating(self, winding_index: int, rate_index: int, value: float) -> None:
        if winding_index == 1:
            if rate_index == 1:
                self.RATE1_1 = value
            elif rate_index == 2:
                self.RATE1_2 = value
            elif rate_index == 3:
                self.RATE1_3 = value
            elif rate_index == 4:
                self.RATE1_4 = value
            elif rate_index == 5:
                self.RATE1_5 = value
            elif rate_index == 6:
                self.RATE1_6 = value
            elif rate_index == 7:
                self.RATE1_7 = value
            elif rate_index == 8:
                self.RATE1_8 = value
            elif rate_index == 9:
                self.RATE1_9 = value
            elif rate_index == 10:
                self.RATE1_10 = value
            elif rate_index == 11:
                self.RATE1_11 = value
            else:
                self.RATE1_12 = value
        elif winding_index == 2:
            if rate_index == 1:
                self.RATE2_1 = value
            elif rate_index == 2:
                self.RATE2_2 = value
            elif rate_index == 3:
                self.RATE2_3 = value
            elif rate_index == 4:
                self.RATE2_4 = value
            elif rate_index == 5:
                self.RATE2_5 = value
            elif rate_index == 6:
                self.RATE2_6 = value
            elif rate_index == 7:
                self.RATE2_7 = value
            elif rate_index == 8:
                self.RATE2_8 = value
            elif rate_index == 9:
                self.RATE2_9 = value
            elif rate_index == 10:
                self.RATE2_10 = value
            elif rate_index == 11:
                self.RATE2_11 = value
            else:
                self.RATE2_12 = value
        else:
            if rate_index == 1:
                self.RATE3_1 = value
            elif rate_index == 2:
                self.RATE3_2 = value
            elif rate_index == 3:
                self.RATE3_3 = value
            elif rate_index == 4:
                self.RATE3_4 = value
            elif rate_index == 5:
                self.RATE3_5 = value
            elif rate_index == 6:
                self.RATE3_6 = value
            elif rate_index == 7:
                self.RATE3_7 = value
            elif rate_index == 8:
                self.RATE3_8 = value
            elif rate_index == 9:
                self.RATE3_9 = value
            elif rate_index == 10:
                self.RATE3_10 = value
            elif rate_index == 11:
                self.RATE3_11 = value
            else:
                self.RATE3_12 = value

    def get_winding_rating_triplet(self, winding_index: int, version: int) -> tuple[float, float, float]:
        if version <= 33:
            if winding_index == 1:
                return self.RATA1, self.RATB1, self.RATC1
            elif winding_index == 2:
                return self.RATA2, self.RATB2, self.RATC2
            return self.RATA3, self.RATB3, self.RATC3

        if winding_index == 1:
            return self.RATE1_1, self.RATE1_2, self.RATE1_3
        elif winding_index == 2:
            return self.RATE2_1, self.RATE2_2, self.RATE2_3
        return self.RATE3_1, self.RATE3_2, self.RATE3_3

    def set_winding_rating_triplet(self,
                                   winding_index: int,
                                   version: int,
                                   rate_1: float,
                                   rate_2: float,
                                   rate_3: float) -> None:
        if version <= 33:
            if winding_index == 1:
                self.RATA1 = rate_1
                self.RATB1 = rate_2
                self.RATC1 = rate_3
            elif winding_index == 2:
                self.RATA2 = rate_1
                self.RATB2 = rate_2
                self.RATC2 = rate_3
            else:
                self.RATA3 = rate_1
                self.RATB3 = rate_2
                self.RATC3 = rate_3
        else:
            self.set_numbered_winding_rating(winding_index, 1, rate_1)
            self.set_numbered_winding_rating(winding_index, 2, rate_2)
            self.set_numbered_winding_rating(winding_index, 3, rate_3)

    def get_2w_pu_impedances(self,
                             Sbase: float,
                             v_bus_i: float,
                             v_bus_j: float) -> Tuple[float, float, float, float, float, float]:
        """
        Get the 2-winding impedances if this is a 2-winding transformer
        :param Sbase: system base power in MVA
        :param v_bus_i: Nominal voltage of the bus I in kV
        :param v_bus_j: Nominal voltage of the bus J in kV
        :return: r, x, g, b, tap_module, tap_angle
        """

        assert self.windings == 2

        # yeah, self.NOMV1 and self.NOMV2 may be zero....
        NOMV1 = self.NOMV1 if self.NOMV1 > 0 else v_bus_i
        NOMV2 = self.NOMV2 if self.NOMV2 > 0 else v_bus_j
        if NOMV1 <= 0.0:
            NOMV1 = 1.0
        if NOMV2 <= 0.0:
            NOMV2 = NOMV1

        winding_base_power = self.SBASE1_2 if self.SBASE1_2 > 0.0 else Sbase
        if winding_base_power <= 0.0:
            winding_base_power = 100.0

        bus_i_base_voltage = v_bus_i if v_bus_i > 0.0 else NOMV1
        bus_j_base_voltage = v_bus_j if v_bus_j > 0.0 else NOMV2

        system_base_power = Sbase if Sbase > 0.0 else 100.0

        z_base_winding = (NOMV1 * NOMV1) / winding_base_power
        z_base_sys = (bus_i_base_voltage * bus_i_base_voltage) / system_base_power

        'The winding data I/O code defines the units in which the turns ratios '
        'WINDV1, WINDV2 and WINDV3 are specified (the units of RMAn and RMIn are '
        'also governed by CW when CODn is 1 or 2):\n'
        '• 1 for off-nominal turns ratio in pu of winding bus base voltage\n'
        '• 2 for winding voltage in kV\n'
        '• 3 for off-nominal turns ratio in pu of nominal winding voltage, NOMV1, NOMV2 and NOMV3.'
        if self.CW == 1:
            """
            WINDV1 is the Winding 1 off-nominal turns ratio in pu of Winding1 bus base voltage
            """
            ti = self.WINDV1
            tj = self.WINDV2
            tap_module = ti / tj if tj != 0 else 1.0

        elif self.CW == 2:
            """
            WINDV1 is the actual Winding 1 voltage in kV; WINDV1 is equal to the base voltage of bus I by default.
            """
            ti = self.WINDV1 / bus_i_base_voltage
            tj = self.WINDV2 / bus_j_base_voltage
            tap_module = ti / tj

        elif self.CW == 3:
            """
            WINDV1 is the Winding 1 off-nominal turns ratio in pu of nominal Winding 1 voltage,
            """
            # ti = self.WINDV1 / NOMV1
            # tj = self.WINDV2 / NOMV2

            ti = self.WINDV1 * NOMV1 / bus_i_base_voltage
            tj = self.WINDV2 * NOMV2 / bus_j_base_voltage

            tap_module = ti / tj
        else:
            raise Exception("Invalid value of CW")

        # --------------------------------------------------------------------------------------------------------------

        if self.CZ == 1:
            """
            1 for resistance and reactance in pu on system MVA base and winding voltage base
            translating: impedances in the system base, do noting
            """
            r = self.R1_2
            x = self.X1_2

        elif self.CZ == 2:
            """
            2 for resistance and reactance in pu on a specified MVA base and winding voltage base
            translating: impedances in the machine base with S=SBASE1_2 and V=NOMV1 
            """
            # base change from winding base to system base
            r_ohm = self.R1_2 * z_base_winding
            x_ohm = self.X1_2 * z_base_winding
            r = r_ohm / z_base_sys
            x = x_ohm / z_base_sys

        elif self.CZ == 3:
            """
            3 for transformer load loss in watts and impedance magnitude in pu on a 
            specified MVA base and winding voltage base
            
            R1-2 is the load loss in watts, and X1-2 is the impedance magnitude in  pu  
            on  Winding  1  to  2  MVA  base (SBASE1-2) and  winding  voltage  base
            """
            # Series impedance
            Pcu = self.R1_2 / 1000.0  # Pcu comes in W from PSSe, we want it in kW
            Vsc = self.X1_2 * 100.0  # Vsc comes in p.u. from Psse, we want it in %
            GR_hv1 = 0.5
            Sn = winding_base_power
            HV = max(NOMV1, NOMV2)
            LV = min(NOMV1, NOMV2)
            VH_bus = max(bus_i_base_voltage, bus_j_base_voltage)
            VL_bus = min(bus_i_base_voltage, bus_j_base_voltage)

            zsc = Vsc / 100.0
            rsc = (Pcu / 1000.0) / Sn
            if rsc < zsc:
                xsc = np.sqrt(zsc ** 2 - rsc ** 2)
            else:
                xsc = 0.0

            # series impedance in p.u. of the machine
            zs = rsc + 1j * xsc

            # convert impedances from machine per unit to ohms
            z_base_hv = (HV * HV) / Sn
            z_base_lv = (LV * LV) / Sn

            z_series_hv = zs * GR_hv1 * z_base_hv  # Ohm
            z_series_lv = zs * (1.0 - GR_hv1) * z_base_lv  # Ohm

            # convert impedances from ohms to system per unit
            z_base_hv_sys = (VH_bus * VH_bus) / system_base_power
            z_base_lv_sys = (VL_bus * VL_bus) / system_base_power

            z_series = z_series_hv / z_base_hv_sys + z_series_lv / z_base_lv_sys

            r = z_series.real
            x = z_series.imag
        else:
            raise Exception("Invalid value of CZ")

        # --------------------------------------------------------------------------------------------------------------

        if self.CM == 1:
            """
            1 for complex  admittance  in pu  on  system  MVA  base  and Winding 1 bus voltage base
            """
            g = self.MAG1
            b = self.MAG2

        elif self.CM == 2:
            """
            2 for no load loss in watts and exciting current in pu on Winding 1 to two 
            MVA base (SBASE1-2) and nominal Winding 1 voltage, NOMV1
            """
            Pfe = self.MAG1 / 1000.0  # Iron losses, AKA magnetic losses (kW) Mag1 comes in W, convert it to kW
            I0 = self.MAG2 * 100  # No-load current (%), comes in p.u. from PSSe
            Sn = winding_base_power  # Base power MVA

            # Shunt impedance (leakage)
            if Pfe > 0.0 and I0 > 0.0:

                rm = system_base_power / (Pfe / 1000.0)
                I0 = I0 * Sn / system_base_power
                zm = 1.0 / (I0 / 100.0)

                if zm < rm:  # only with this is possible to perform xm, otherwise we get div0 or sqrt(neg)
                    inside_sqrt = (-zm ** 2 * rm ** 2) / (zm ** 2 - rm ** 2)
                    xm = np.sqrt(inside_sqrt)
                else:
                    xm = 0.0
            else:
                rm = 0.0
                xm = 0.0

            # convert shunt impedance to shunt admittance
            g = 1.0 / rm if rm > 0.0 else 0.0
            b = -1.0 / xm if xm > 0.0 else 0.0
        else:
            raise Exception("Invalid value of CM")

        # NOTE: ANG1 seems to be related to the vector group and not the tap angle...
        tap_angle = np.deg2rad(self.ANG1)  # ANG2 is ignored for 2W transformers

        return r, x, g, b, tap_module, tap_angle
