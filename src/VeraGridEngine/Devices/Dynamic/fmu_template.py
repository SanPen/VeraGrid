from __future__ import annotations

import copy
from typing import Tuple

from VeraGridEngine.Devices.Parents.pointer_device_parent import PointerDeviceParent
from VeraGridEngine.Devices.Parents.editable_device import GCProp
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.enumerations import DeviceType, FmuTemplateDomain, FmuTemplateMode, SubObjectType


class FmuTemplate(PointerDeviceParent):
    """
    Reusable FMU template stored in the VeraGrid catalogue.

    The template keeps a symbolic wrapper block plus the serialized FMU runtime
    configuration that can later be copied into a concrete device.
    """

    __slots__ = (
        "_block",
        "_domain",
        "_mode",
        "_fmu_relative_path",
        "_serialized_config",
    )

    LOCAL_PROPERTY_DECLARATIONS: Tuple[GCProp, ...] = (
        GCProp(
            prop_name="block",
            units="",
            tpe=SubObjectType.DaeBlockType,
            definition="Symbolic wrapper block used by the FMU template",
            editable=False,
            display=False,
        ),
        GCProp(
            prop_name="tpe",
            units="",
            tpe=DeviceType,
            definition="Device type supported by this FMU template",
            editable=True,
            display=True,
        ),
        GCProp(
            prop_name="domain",
            units="",
            tpe=FmuTemplateDomain,
            definition="Simulation domain where the FMU template can be used",
            editable=True,
            display=True,
        ),
        GCProp(
            prop_name="mode",
            units="",
            tpe=FmuTemplateMode,
            definition="FMI 2.0 execution mode stored by the template",
            editable=True,
            display=True,
        ),
        GCProp(
            prop_name="fmu_relative_path",
            units="",
            tpe=str,
            definition="Path to the FMU archive relative to the VeraGrid project file",
            editable=True,
            display=True,
        ),
        GCProp(
            prop_name="serialized_config",
            units="",
            tpe=str,
            definition="Serialized FMU runtime configuration payload",
            editable=False,
            display=False,
        ),
    )

    def __init__(self, idtag: str = "", name: str = "") -> None:
        """
        Build an empty reusable FMU template.

        :param idtag: Template identifier.
        :param name: Template name.
        """

        super().__init__(
            name=name,
            idtag=idtag,
            code="",
            device=None,
            comment="",
            device_type=DeviceType.FmuTemplateDevice,
        )
        self.tpe: DeviceType = DeviceType.NoDevice
        self._domain: FmuTemplateDomain = FmuTemplateDomain.RMS
        self._mode: FmuTemplateMode = FmuTemplateMode.CO_SIMULATION
        self._fmu_relative_path: str = ""
        self._serialized_config: str = ""
        self._block: Block = Block()

    def __deepcopy__(self, memo: dict[int, object]) -> "FmuTemplate":
        """
        Deep-copy the reusable FMU template while preserving its symbolic shell.

        :param memo: Standard deepcopy memo table.
        :return: Copied FMU template.
        """

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        result._idtag = self._idtag
        result._name = self._name
        result._code = self._code
        result._rdfid = self._rdfid
        result.device_type = self.device_type
        result.comment = self.comment
        result.action = self.action
        result.selected_to_merge = self.selected_to_merge
        result.diff_changes = copy.deepcopy(self.diff_changes, memo)
        result._EditableDevice__auto_update_enabled = self._EditableDevice__auto_update_enabled

        result._device_idtag = self._device_idtag
        result._device_name = self._device_name
        result._device = self._device
        result._tpe = self._tpe

        result._domain = self._domain
        result._mode = self._mode
        result._fmu_relative_path = self._fmu_relative_path
        result._serialized_config = self._serialized_config
        result._block = copy.deepcopy(self._block, memo)

        return result

    @property
    def block(self) -> Block:
        """
        Return the symbolic wrapper block stored by the template.

        :return: Wrapper block.
        """

        return self._block

    @block.setter
    def block(self, obj: Block) -> None:
        """
        Store the symbolic wrapper block used by the template.

        :param obj: Wrapper block.
        :return: None.
        """

        self._block = obj

    @property
    def domain(self) -> FmuTemplateDomain:
        """
        Return the simulation domain supported by the template.

        :return: Template domain.
        """

        return self._domain

    @domain.setter
    def domain(self, value: FmuTemplateDomain) -> None:
        """
        Set the simulation domain supported by the template.

        :param value: Template domain.
        :return: None.
        """

        self._domain = value

    @property
    def mode(self) -> FmuTemplateMode:
        """
        Return the FMI execution mode stored by the template.

        :return: Template execution mode.
        """

        return self._mode

    @mode.setter
    def mode(self, value: FmuTemplateMode) -> None:
        """
        Set the FMI execution mode stored by the template.

        :param value: Template execution mode.
        :return: None.
        """

        self._mode = value

    @property
    def fmu_relative_path(self) -> str:
        """
        Return the FMU archive path relative to the VeraGrid project.

        :return: Relative FMU path.
        """

        return self._fmu_relative_path

    @fmu_relative_path.setter
    def fmu_relative_path(self, value: str) -> None:
        """
        Set the FMU archive path relative to the VeraGrid project.

        :param value: Relative FMU path.
        :return: None.
        """

        self._fmu_relative_path = str(value)

    @property
    def serialized_config(self) -> str:
        """
        Return the serialized FMU runtime configuration payload.

        :return: Serialized configuration string.
        """

        return self._serialized_config

    @serialized_config.setter
    def serialized_config(self, value: str) -> None:
        """
        Set the serialized FMU runtime configuration payload.

        :param value: Serialized configuration string.
        :return: None.
        """

        self._serialized_config = str(value)
