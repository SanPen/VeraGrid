# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from typing import Dict
import numba as nb
import numpy as np
from VeraGridEngine.basic_structures import CxVec, Vec, IntVec, BoolVec, StrVec
from VeraGridEngine.enumerations import BusMode


@nb.njit(cache=True, inline="always")
def _control_priority(is_p: bool,
                      is_q: bool,
                      is_vm: bool,
                      is_va: bool) -> int:
    """
    Rank the control strength of a bus.
    """
    # Prefer buses that already define the electrical reference first, then
    # voltage-controlled buses, and leave plain injection-controlled buses last.
    if is_va and is_vm:
        return 6
    elif is_va:
        return 5
    elif is_vm and not is_q:
        return 4
    elif is_vm:
        return 3
    elif is_p and not is_q:
        return 2
    else:
        return 1


@nb.njit(cache=True)
def propagate_controls(chosen_idx: int,
                       other_idx: IntVec,
                       bus_types: IntVec,
                       Vbus: CxVec,
                       is_p_controlled: BoolVec,
                       is_q_controlled: BoolVec,
                       is_vm_controlled: BoolVec,
                       is_va_controlled: BoolVec) -> None:
    """
    Propagate the strongest control status of a reduced bus cluster to the surviving bus.

    The donor bus is chosen from ``chosen_idx`` and ``other_idx`` using the actual control flags,
    not only the bus type, so VSC/HVDC-added controls are preserved as well.
    :param chosen_idx: island of the island chosen by the topological reduction process to represent the reduction set
    :param other_idx: rest of buses in the set that are going to be reduced but may contain important information
    :param bus_types:
    :param Vbus:
    :param is_p_controlled:
    :param is_q_controlled:
    :param is_vm_controlled:
    :param is_va_controlled:
    :return:
    """
    # Start by assuming the surviving bus already is the best donor.
    donor_idx = chosen_idx
    donor_priority = _control_priority(
        is_p=is_p_controlled[chosen_idx],
        is_q=is_q_controlled[chosen_idx],
        is_vm=is_vm_controlled[chosen_idx],
        is_va=is_va_controlled[chosen_idx],
    )
    for idx in other_idx:
        priority = _control_priority(
            is_p=is_p_controlled[idx],
            is_q=is_q_controlled[idx],
            is_vm=is_vm_controlled[idx],
            is_va=is_va_controlled[idx],
        )

        # Replace the donor when the reduced bus carries a stronger control role.
        if priority > donor_priority:
            donor_idx = idx
            donor_priority = priority
        # For equally strong voltage-controlled buses, keep the one with the lowest
        # bus index. PSSe retains the lowest-numbered bus of a merged (switch-joined)
        # node, so when generators with conflicting setpoints land on the same node
        # its setpoint wins. This is also deterministic (independent of island ordering).
        elif priority == donor_priority and is_vm_controlled[idx] and idx < donor_idx:
            donor_idx = idx

    # Once the donor is chosen, copy its control flags and bus type as one block.
    if donor_idx != chosen_idx:
        bus_types[chosen_idx] = bus_types[donor_idx]
        is_p_controlled[chosen_idx] = is_p_controlled[donor_idx]
        is_q_controlled[chosen_idx] = is_q_controlled[donor_idx]
        is_vm_controlled[chosen_idx] = is_vm_controlled[donor_idx]
        is_va_controlled[chosen_idx] = is_va_controlled[donor_idx]

    # Copy the donor voltage state directly; do not mix magnitude from one bus
    # with angle from another.
    Vbus[chosen_idx] = Vbus[donor_idx]


class BusData:
    """
    BusData
    """

    def __init__(self, nbus: int):
        """
        Bus data arrays
        :param nbus: number of buses
        """
        self.nbus: int = nbus
        self.idtag: StrVec = np.empty(nbus, dtype=object)
        self.names: StrVec = np.empty(nbus, dtype=object)
        self.active: IntVec = np.ones(nbus, dtype=int)
        self.Vbus: CxVec = np.ones(nbus, dtype=complex)
        self.Vmin: Vec = np.ones(nbus, dtype=float)
        self.Vmax: Vec = np.ones(nbus, dtype=float)
        self.Vnom: Vec = np.ones(nbus, dtype=float)
        self.cost_v: Vec = np.ones(nbus, dtype=float)
        self.angle_min: Vec = np.full(nbus, fill_value=-3.14, dtype=float)
        self.angle_max: Vec = np.full(nbus, fill_value=3.14, dtype=float)
        self.bus_types: IntVec = np.empty(nbus, dtype=int)
        self.is_p_controlled = np.zeros(nbus, dtype=bool)
        self.is_q_controlled = np.zeros(nbus, dtype=bool)
        self.is_vm_controlled = np.zeros(nbus, dtype=bool)
        self.is_va_controlled = np.zeros(nbus, dtype=bool)
        self.installed_power: Vec = np.zeros(nbus, dtype=float)
        self.srap_available_power: Vec = np.zeros(nbus, dtype=float)
        self.is_dc: BoolVec = np.empty(nbus, dtype=bool)
        self.is_grounded: BoolVec = np.empty(nbus, dtype=bool)
        self.areas: IntVec = np.empty(nbus, dtype=int)
        self.substations: IntVec = np.empty(nbus, dtype=int)

        # This is the total value used to compute the q_share in generators, batteries and shunts
        self.q_shared_total = np.zeros(nbus, dtype=float)

        # This is the fixed amount of Q that is Subtrated from Qbus to compute
        # the Q of each generator, battery and shunt controlling
        self.q_fixed = np.zeros(nbus, dtype=float)
        self.ii_fixed = np.zeros(nbus, dtype=float)  # same concept, but imag current from loads
        self.b_fixed = np.zeros(nbus, dtype=float)  # same concept, but susceptance from shunts

        self.original_idx: IntVec = np.zeros(nbus, dtype=int)

    def slice(self, elm_idx: IntVec) -> "BusData":
        """
        Slice this data structure
        :param elm_idx: array of bus indices
        :return: instance of BusData
        """

        data = BusData(nbus=len(elm_idx))

        data.names = self.names[elm_idx]
        data.idtag = self.idtag[elm_idx]
        data.active = self.active[elm_idx]

        data.Vbus = self.Vbus[elm_idx]
        data.Vmin = self.Vmin[elm_idx]
        data.Vmax = self.Vmax[elm_idx]
        data.Vnom = self.Vnom[elm_idx]
        data.cost_v = self.cost_v[elm_idx]
        data.angle_min = self.angle_min[elm_idx]
        data.angle_max = self.angle_max[elm_idx]

        data.bus_types = self.bus_types[elm_idx]
        data.is_p_controlled = self.is_p_controlled[elm_idx]
        data.is_q_controlled = self.is_q_controlled[elm_idx]
        data.is_vm_controlled = self.is_vm_controlled[elm_idx]
        data.is_va_controlled = self.is_va_controlled[elm_idx]
        data.installed_power = self.installed_power[elm_idx]
        data.srap_available_power = self.srap_available_power[elm_idx]
        data.is_dc = self.is_dc[elm_idx]
        data.is_grounded = self.is_grounded[elm_idx]
        data.areas = self.areas[elm_idx]
        data.substations = self.substations[elm_idx]

        data.q_shared_total = self.q_shared_total[elm_idx]
        data.q_fixed = self.q_fixed[elm_idx]
        data.ii_fixed = self.ii_fixed[elm_idx]
        data.b_fixed = self.b_fixed[elm_idx]

        data.original_idx = elm_idx

        return data

    def size(self) -> int:
        """
        Get size of the structure
        :return:
        """

        return self.nbus

    def copy(self) -> "BusData":
        """
        Deep copy of this structure
        :return: instance of BusData
        """

        data = BusData(nbus=self.nbus)

        data.names = self.names.copy()
        data.idtag = self.idtag.copy()
        data.active = self.active.copy()

        data.Vbus = self.Vbus.copy()
        data.Vmin = self.Vmin.copy()
        data.Vmax = self.Vmax.copy()
        data.Vnom = self.Vnom.copy()
        data.cost_v = self.cost_v.copy()
        data.angle_min = self.angle_min.copy()
        data.angle_max = self.angle_max.copy()

        data.bus_types = self.bus_types.copy()
        data.is_p_controlled = self.is_p_controlled.copy()
        data.is_q_controlled = self.is_q_controlled.copy()
        data.is_vm_controlled = self.is_vm_controlled.copy()
        data.is_va_controlled = self.is_va_controlled.copy()
        data.installed_power = self.installed_power.copy()
        data.srap_available_power = self.srap_available_power.copy()
        data.is_dc = self.is_dc.copy()
        data.is_grounded = self.is_grounded.copy()
        data.areas = self.areas.copy()
        data.substations = self.substations.copy()

        data.q_shared_total = self.q_shared_total.copy()
        data.q_fixed = self.q_fixed.copy()
        data.ii_fixed = self.ii_fixed.copy()
        data.b_fixed = self.b_fixed.copy()

        data.original_idx = self.original_idx.copy()

        return data

    def get_original_to_island_bus_dict(self) -> Dict[int, int]:
        """
        Dictionary that relates the original bus index to the island bus index
        :return: dict[original idx] -> island index
        """
        return {
            int(val): idx for idx, val in enumerate(self.original_idx)
        }

    def get_idtag_dict(self) -> Dict[str, int]:
        """
        Get dictionary of bus idtagd related to the island bus index
        :return:
        """
        return {idtag_val: i for i, idtag_val in enumerate(self.idtag)}

    def propagate_controls(self, chosen_idx: int, other_idx: IntVec) -> None:
        """
        Propagate the strongest control status of the reduced buses into ``chosen_idx``.
        """
        propagate_controls(
            chosen_idx=chosen_idx,
            other_idx=other_idx,
            bus_types=self.bus_types,
            Vbus=self.Vbus,
            is_p_controlled=self.is_p_controlled,
            is_q_controlled=self.is_q_controlled,
            is_vm_controlled=self.is_vm_controlled,
            is_va_controlled=self.is_va_controlled,
        )

    def set_bus_mode(self, idx: int, val: BusMode):
        """
        Set bus mode
        :param idx: int
        :param val: BusMode
        """
        self.bus_types[idx] = val.value
        is_dc = self.is_dc[idx]
        is_grounded = self.is_grounded[idx]

        # For each bus the logic and priority is:
        #   1) grounded (AC or DC): Vm/Va fixed (to 0), P/Q free
        #   2) DC non-grounded
        #   3) AC non-grounded
        if val == BusMode.PQ_tpe:
            if is_grounded:
                # grounded bus (AC or DC): acts as ground reference
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            elif is_dc:
                # DC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = False
                self.is_va_controlled[idx] = True
            else:
                # AC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = True
                self.is_vm_controlled[idx] = False
                self.is_va_controlled[idx] = False

        elif val == BusMode.PV_tpe:
            if is_grounded:
                # grounded bus (AC or DC): acts as ground reference
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            elif is_dc:
                # DC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            else:
                # AC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = False

        elif val == BusMode.Slack_tpe:
            if is_grounded:
                # grounded bus (AC or DC): acts as ground reference
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            elif is_dc:
                # DC, not grounded
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            else:
                # AC, not grounded
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True

        elif val == BusMode.PQV_tpe:
            if is_grounded:
                # grounded bus (AC or DC): acts as ground reference
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            elif is_dc:
                # DC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            else:
                # AC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = True
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = False

        elif val == BusMode.P_tpe:
            if is_grounded:
                # grounded bus (AC or DC): acts as ground reference
                self.is_p_controlled[idx] = False
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = True
                self.is_va_controlled[idx] = True
            elif is_dc:
                # DC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = False
                self.is_va_controlled[idx] = True
            else:
                # AC, not grounded
                self.is_p_controlled[idx] = True
                self.is_q_controlled[idx] = False
                self.is_vm_controlled[idx] = False
                self.is_va_controlled[idx] = False

        else:
            raise ValueError("Unexpected bus mode")

    def __len__(self) -> int:
        return self.nbus

    def get_3ph_names(self):
        """
        Get the 3-phase names
        :return:
        """
        # names3: StrVec = np.empty(self.nbus * 3, dtype=object)
        # for i in range(self.nbus):
        #     names3[3 * i + 0] = self.names[i] + "_A"
        #     names3[3 * i + 1] = self.names[i] + "_B"
        #     names3[3 * i + 2] = self.names[i] + "_C"

        names3: StrVec = np.empty(self.nbus, dtype=object)
        for i in range(self.nbus):
            names3[i] = self.names[i]

        return names3
