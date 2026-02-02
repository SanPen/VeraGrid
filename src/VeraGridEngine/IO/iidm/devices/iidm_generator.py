# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from VeraGridEngine.IO.iidm.devices.iidm_object import IidmObject, Unit


class IidmGeneratorShortCircuit(IidmObject):
    def __init__(self, generatorId: str, voltageFactor: float, k: float):
        super().__init__("GeneratorShortCircuit")
        self.generatorId = generatorId
        self.voltageFactor = voltageFactor
        self.k = k

        self.register_property("generatorId",
                               str,
                               description="Associated generator ID")
        self.register_property("voltageFactor",
                               float,
                               description="Voltage factor")
        self.register_property("k",
                               float,
                               description="Short circuit ratio k")


class IidmGenerator(IidmObject):
    def __init__(self, id_, bus, targetP, targetQ, targetV):
        super().__init__("Generator")
        self.id = id_
        self.bus = bus
        self.targetP = targetP
        self.targetQ = targetQ
        self.targetV = targetV

        self.register_property("id",
                               str,
                               description="Generator ID")

        self.register_property("bus",
                               str,
                               description="Connected bus")

        self.register_property("targetP",
                               float,
                               Unit.get_kw(),
                               description="Active power set-point")

        self.register_property("targetQ",
                               float,
                               Unit.get_mvar(),
                               description="Reactive power set-point")

        self.register_property("targetV",
                               float,
                               Unit.get_kv(),
                               description="Voltage set-point")
