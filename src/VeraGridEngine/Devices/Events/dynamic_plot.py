# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0

from typing import Union, Tuple
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice, DeviceType, GCProp
from VeraGridEngine.enumerations import PrpCat, PlotSimulationType


class DynamicPlot(EditableDevice):
    """
    Persistent dynamic plot definition owned by the project assets.

    This asset stores only the plot configuration that the user wants to keep in
    the ``.veragrid`` project file. Runtime simulation results, NumPy arrays, and
    any GUI-only plotting state remain outside this object.

    A dynamic plot belongs to exactly one simulation family in the first
    implementation so RMS and EMT curve definitions are not mixed in the same
    persistent group.
    """
    __slots__ = (
        '_simulation_type',
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='simulation_type',
            units='',
            tpe=PlotSimulationType,
            definition='Simulation family for this persistent dynamic plot definition.',
            cat=[PrpCat.RMS, PrpCat.EMT],
        ),
    )

    def __init__(self,
                  idtag: Union[str, None] = None,
                  name: str = "EmtEventsGroup",
                  simulation_type: PlotSimulationType = PlotSimulationType.RMS,
                  comment: str = ""):
        """
        Build one persistent dynamic plot asset.

        :param idtag: Unique identifier.
        :param name: Plot-group name shown in the GUI.
        :param simulation_type: Simulation family identifier.
        :param comment: Optional user comment.
        :return: None.
        """

        EditableDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code='',
                                device_type=DeviceType.DynamicPlotGroupDevice,
                                comment=comment)
        self._simulation_type = simulation_type


    @property
    def simulation_type(self) -> PlotSimulationType:
        """
        Get the simulation family assigned to this plot.

        :return: Simulation family identifier.
        """
        return self._simulation_type

    @simulation_type.setter
    def simulation_type(self, val: PlotSimulationType) -> None:
        """
        Set the simulation family assigned to this plot.

        :param val: Simulation family identifier.
        :return: None.
        """
        if isinstance(val, PlotSimulationType):
            self._simulation_type = val
        else:
            raise ValueError("Unsupported plot simulation type")
