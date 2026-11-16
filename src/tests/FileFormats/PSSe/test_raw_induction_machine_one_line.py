# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.IO.raw.raw_parser_writer import read_raw

RAW = """0,100.00,33,0,0,60.00     / two-bus case
induction machine on one line
 
1,'B1',110.0,3,1,1,1,1.0,0.0
2,'B2',110.0,1,1,1,1,1.0,0.0
0 / END OF BUS DATA, BEGIN LOAD DATA
2,'1 ',1,1,1,10.0,2.0,0,0,0,0,1,1
0 / END OF LOAD DATA, BEGIN FIXED SHUNT DATA
0 / END OF FIXED SHUNT DATA, BEGIN GENERATOR DATA
1,'1 ',0,0,999,-999,1.0,0,100,0,1,0,0,1,1,100,999,-999,1,1.0
0 / END OF GENERATOR DATA, BEGIN BRANCH DATA
1,2,'1 ',0.01,0.1,0.0,0,0,0,0,0,0,0,1,1,0,1,1.0
0 / END OF BRANCH DATA, BEGIN TRANSFORMER DATA
0 / END OF TRANSFORMER DATA, BEGIN AREA DATA
0 / END OF AREA DATA, BEGIN TWO-TERMINAL DC DATA
0 / END OF TWO-TERMINAL DC DATA, BEGIN VOLTAGE SOURCE CONVERTER DATA
0 / END OF VOLTAGE SOURCE CONVERTER DATA, BEGIN IMPEDANCE CORRECTION DATA
0 / END OF IMPEDANCE CORRECTION DATA, BEGIN MULTI-TERMINAL DC DATA
0 / END OF MULTI-TERMINAL DC DATA, BEGIN MULTI-SECTION LINE DATA
0 / END OF MULTI-SECTION LINE DATA, BEGIN ZONE DATA
0 / END OF ZONE DATA, BEGIN INTER-AREA TRANSFER DATA
0 / END OF INTER-AREA TRANSFER DATA, BEGIN OWNER DATA
0 / END OF OWNER DATA, BEGIN FACTS DEVICE DATA
0 / END OF FACTS DEVICE DATA, BEGIN SWITCHED SHUNT DATA
0 / END OF SWITCHED SHUNT DATA, BEGIN GNE DATA
0 / END OF GNE DATA, BEGIN INDUCTION MACHINE DATA
2,'1 ',1,1,2,1,1,1,1,1,5.0,0,1,2.0,1,1,1,1,1,0,0.1,2.5,999,999,999,999,0,1,0,1.2,0,0,0,1.5
0 / END OF INDUCTION MACHINE DATA
Q
"""


def test_one_line_induction_machine_record(tmp_path):
    """PSS/E v30+ writes an induction machine as one line of 34 fields."""
    path = tmp_path / "one_line_induction_machine.raw"
    path.write_text(RAW)
    psse_model = read_raw(str(path), logger=Logger())
    assert len(psse_model.induction_machines) == 1
    machine = psse_model.induction_machines[0]
    assert machine.I == 2
    assert machine.XM == 2.5
    assert machine.XAMULT == 1.5
