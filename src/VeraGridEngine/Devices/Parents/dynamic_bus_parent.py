# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations
from typing import Any, List, Tuple
from VeraGridEngine.Devices.Parents.physical_device import PhysicalDevice, GCProp
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import (DeviceType, BuildStatus, SubObjectType, PrpCat)
from enum import Enum


class EmtBusConnectionSide(Enum):
    """
    Enumerate the semantic side by which one EMT model is attached to one bus.

    The bus-local reconnect algorithm must know whether one device consumes the
    bus shell as a single-bus injection, a branch ``from`` terminal, or a branch
    ``to`` terminal. Using one enum keeps the registry explicit and refactorable.

    :return: None.
    """
    BUS = "bus"
    FROM = "from"
    TO = "to"


class EmtBusConnectedModelRecord:
    """
    Store one materialized EMT model endpoint connected to one bus.

    The bus EMT shell can be recreated when the required phase layout expands.
    When that happens, the bus must reconnect every already-connected EMT model
    using the correct side-specific helper. This light record stores the exact
    metadata needed for that deterministic rebinding.

    :param device: Owning device of the EMT model.
    :param model: Materialized EMT model block.
    :param side: Semantic side by which the model is attached to the bus.
    :param device_tpe: Device type used to select the proper reconnect helper.
    """
    __slots__ = (
        "_device",
        "_model",
        "_side",
        "_device_tpe",
    )

    def __init__(self,
                 device: Any,
                 model: Block,
                 side: EmtBusConnectionSide,
                 device_tpe: DeviceType) -> None:
        """
        Build one explicit bus-to-model EMT connection record.

        :param device: Owning device of the EMT model.
        :param model: Materialized EMT model block.
        :param side: Semantic side by which the model is attached to the bus.
        :param device_tpe: Device type used to select the proper reconnect helper.
        :return: None.
        """
        self._device: Any = device
        self._model: Block = model
        self._side: EmtBusConnectionSide = side
        self._device_tpe: DeviceType = device_tpe

    def get_device(self) -> Any:
        """
        Return the owner device associated to this bus endpoint.

        :return: Owning EMT device.
        """
        return self._device

    def get_model(self) -> Block:
        """
        Return the materialized EMT model block registered on the bus.

        :return: EMT model block.
        """
        return self._model

    def set_model(self, model: Block) -> None:
        """
        Replace the stored EMT model block for this bus endpoint.

        Replacing the model is required when the device assigns a fresh EMT
        template block and the bus registry must stop referencing the stale one.

        :param model: New materialized EMT model block.
        :return: None.
        """
        self._model = model

    def get_side(self) -> EmtBusConnectionSide:
        """
        Return the semantic bus side represented by this record.

        :return: Bus connection side.
        """
        return self._side

    def get_device_tpe(self) -> DeviceType:
        """
        Return the device type stored in this record.

        :return: Device type.
        """
        return self._device_tpe



class DynamicBusDevice(PhysicalDevice):
    """
    Parent class for devices with dynamic models
    """
    __slots__ = (
        '_var_factory',
        '_rms_model',
        '_emt_model',
        '_pending_emt_devices',
        "_emt_models_connected",
        "_grid_synchronized_emt_model",
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name='rms_model',
            units='',
            tpe=SubObjectType.DaeBlockType,
            definition='RMS dynamic model',
            display=False,
            cat=[PrpCat.RMS],
        ),
        GCProp(
            prop_name='emt_model',
            units='',
            tpe=SubObjectType.DaeBlockType,
            definition='EMT dynamic model',
            display=False,
            cat=[PrpCat.EMT],
        ),
    )

    def __init__(self,
                 name: str,
                 idtag: str | None,
                 code: str,
                 device_type: DeviceType,
                 build_status: BuildStatus = BuildStatus.Commissioned):
        """

        :param name:
        :param idtag:
        :param code:
        :param device_type:
        :param build_status:
        """
        PhysicalDevice.__init__(self,
                                name=name,
                                idtag=idtag,
                                code=code,
                                device_type=device_type,
                                build_status=build_status)

        self._var_factory: VarFactory | None = None
        self._rms_model: Block = Block()
        self._emt_model: Block = Block()
        self._pending_emt_devices: List[Any] = list()
        self._emt_models_connected: List[EmtBusConnectedModelRecord] = list()
        self._grid_synchronized_emt_model: Block | None = None

    def set_var_factory(self, val: VarFactory) -> None:
        """
        Store the shared variable factory used by RMS and EMT symbolic blocks.

        :param val: Shared variable factory.
        :return: None.
        """

        if isinstance(val, VarFactory):
            self._var_factory = val
        else:
            raise ValueError(f"VarFactory cannot accept {val}")

    @property
    def rms_model(self) -> Block:
        """
        Get the RMS model
        """
        return self._rms_model

    @rms_model.setter
    def rms_model(self, val: Block) -> None:
        if isinstance(val, Block):
            self._rms_model = val
        else:
            raise ValueError(f"RMS model cannot accept {val}")

    @property
    def emt_model(self) -> Block:
        """
        Get the EMT model
        """
        return self._emt_model

    @emt_model.setter
    def emt_model(self, val: Block) -> None:
        if isinstance(val, Block):
            if val is self._emt_model:
                pass
            else:
                self._grid_synchronized_emt_model = None
            self._emt_model = val
        else:
            raise ValueError(f"EMT model cannot accept {val}")

    def mark_emt_model_grid_synchronized(self) -> None:
        """
        Mark the current EMT shell as managed by grid-topology synchronization.

        :return: None.
        """
        self._grid_synchronized_emt_model = self._emt_model

    def is_emt_model_grid_synchronized(self) -> bool:
        """
        Return whether the current EMT shell is the last grid-managed shell.

        Replacing ``emt_model`` explicitly clears the marker, allowing
        reconciliation to distinguish an external shell contract from one that
        should follow later grid-topology changes.

        :return: ``True`` when the current shell was synchronized from the grid.
        """
        return self._grid_synchronized_emt_model is self._emt_model

    def add_pending_emt_device(self, device: Any) -> None:
        """
        Store one single-bus device whose EMT model must wait for a bus shell.

        :param device: Device waiting for one EMT bus shell.
        :return: None.
        """
        if device in self._pending_emt_devices:
            pass
        else:
            self._pending_emt_devices.append(device)

    def remove_pending_emt_device(self, device: Any) -> None:
        """
        Remove one single-bus device from the pending EMT connection queue.

        :param device: Device that no longer needs deferred EMT bus connection.
        :return: None.
        """
        filtered_devices: List[Any] = list()
        pending_device: Any
        for pending_device in self._pending_emt_devices:
            if pending_device is not device:
                filtered_devices.append(pending_device)
            else:
                pass
        self._pending_emt_devices = filtered_devices

    def get_pending_emt_devices(self) -> List[Any]:
        """
        Return the devices waiting for deferred EMT bus connection.

        :return: Copy of the pending EMT device list.
        """
        return list(self._pending_emt_devices)

    def add_or_replace_emt_model_connected(self,
                                           device: Any,
                                           emt_model: Block,
                                           side: EmtBusConnectionSide,
                                           device_tpe: DeviceType) -> None:
        """
        Add or replace one connected EMT endpoint in the bus-local registry.

        The registry key is the pair ``(device, side)`` because one device can
        only expose one endpoint per bus side. When the same device assigns a new
        EMT model block, the existing record must be replaced instead of appended.

        :param device: Owning device of the EMT model.
        :param emt_model: EMT model block connected to this bus.
        :param side: Semantic side of the connection relative to this bus.
        :param device_tpe: Device type used for later reconnect dispatch.
        :return: None.
        """
        record: EmtBusConnectedModelRecord
        for record in self._emt_models_connected:
            if record.get_device() is device:
                if record.get_side() == side:
                    record.set_model(emt_model)
                    return
                else:
                    pass
            else:
                pass

        self._emt_models_connected.append(
            EmtBusConnectedModelRecord(device=device,
                                       model=emt_model,
                                       side=side,
                                       device_tpe=device_tpe)
        )

    def remove_emt_model_connected_for_device(self,
                                              device: Any,
                                              side: EmtBusConnectionSide | None = None) -> None:
        """
        Remove connected EMT registry entries associated to one device.

        Removing by device is the primary cleanup path because one device can
        replace or clear its EMT model while still representing the same logical
        bus endpoint.

        :param device: Owning device whose entries must be removed.
        :param side: Optional side filter when only one endpoint must be removed.
        :return: None.
        """
        filtered_records: List[EmtBusConnectedModelRecord] = list()
        record: EmtBusConnectedModelRecord
        for record in self._emt_models_connected:
            keep_record: bool = True

            if record.get_device() is device:
                if side is None:
                    keep_record = False
                else:
                    if record.get_side() == side:
                        keep_record = False
                    else:
                        keep_record = True
            else:
                keep_record = True

            if keep_record:
                filtered_records.append(record)
            else:
                pass

        self._emt_models_connected = filtered_records

    def remove_emt_model_connected_for_model(self, emt_model: Block) -> None:
        """
        Remove connected EMT registry entries associated to one concrete model block.

        This cleanup path is useful when one stale block instance must be removed
        explicitly regardless of which device currently owns it.

        :param emt_model: Concrete EMT model block to remove.
        :return: None.
        """
        filtered_records: List[EmtBusConnectedModelRecord] = list()
        record: EmtBusConnectedModelRecord
        for record in self._emt_models_connected:
            if record.get_model() is not emt_model:
                filtered_records.append(record)
            else:
                pass

        self._emt_models_connected = filtered_records

    def get_emt_models_connected(self) -> List[EmtBusConnectedModelRecord]:
        """
        Return the connected EMT endpoint registry for this bus.

        :return: Copy of the connected EMT endpoint list.
        """
        return list(self._emt_models_connected)

    def clear_emt_models_connected(self) -> None:
        """
        Clear the connected EMT endpoint registry for this bus.

        :return: None.
        """
        self._emt_models_connected = list()
