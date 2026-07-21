from __future__ import annotations

import uuid

from typing import List, Optional, Dict, Any

from PySide6 import QtCore, QtGui

from dataclasses import dataclass

from VeraGrid.Gui.Icons.icon_associations import device_type_icons
from VeraGridEngine.enumerations import DeviceType, DynamicSimulationMode
from VeraGridEngine.Devices.types import ALL_DEV_TYPES
from VeraGridEngine.Devices.Dynamic.emt_template import EmtModelTemplate
from VeraGridEngine.Devices.Dynamic.fmu_template import FmuTemplate
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Templates.BasicBlockCatalog import BasicBlockTemplateDescriptor, \
    get_editor_ready_basic_block_catalog_descriptors
from VeraGridEngine.Templates.BasicBlockCatalog.catalog import build_basic_block_catalog_branch_skeleton
from VeraGridEngine.enumerations import BlockType


def _new_uid() -> int:
    """
    Generate a fresh integer identifier.

    :return: Fresh uid.
    """
    return uuid.uuid4().int


@dataclass(frozen=True)
class LibraryLeafSpec:
    """
    One draggable leaf entry in the library tree.
    """

    label: str
    payload: object
    search_text: str = ""


class DynamicsLibraryTreeModel(QtGui.QStandardItemModel):
    __slots__ = ("_block_role", "_mime_type", "_drag_token_role", "_drag_payloads")

    def __init__(self, block_role: int, mime_type: str):
        super().__init__()
        self._block_role = block_role
        self._mime_type = mime_type
        self._drag_token_role = block_role + 1
        self._drag_payloads: Dict[str, object] = dict()

        self.setHorizontalHeaderLabels(["Models Library"])

    def register_drag_payload(self, item: QtGui.QStandardItem, payload: object) -> None:
        token: str = str(_new_uid())
        self._drag_payloads[token] = payload
        item.setData(payload, self._block_role)
        item.setData(token, self._drag_token_role)

    def get_drag_payload(self, token: str) -> object | None:
        return self._drag_payloads.get(token, None)

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
        if index.isValid():
            item: QtGui.QStandardItem | None = self.itemFromIndex(index)
            if item is not None:
                item_data: object = item.data(self._block_role)
                if is_supported_library_payload(item_data):
                    return (QtCore.Qt.ItemFlag.ItemIsEnabled
                            | QtCore.Qt.ItemFlag.ItemIsSelectable
                            | QtCore.Qt.ItemFlag.ItemIsDragEnabled)
                else:
                    return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            else:
                return QtCore.Qt.ItemFlag.ItemIsEnabled
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

    def mimeTypes(self) -> List[str]:
        return [self._mime_type]

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        return QtCore.Qt.DropAction.CopyAction

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        mime_data: QtCore.QMimeData = QtCore.QMimeData()

        index: QtCore.QModelIndex
        for index in indexes:
            if index.isValid():
                item: QtGui.QStandardItem | None = self.itemFromIndex(index)
                if item is not None:
                    item_token: object = item.data(self._drag_token_role)
                    item_data: object = item.data(self._block_role)
                    if isinstance(item_token, str) and is_supported_library_payload(item_data):
                        mime_data.setData(self._mime_type, QtCore.QByteArray(item_token.encode("utf-8")))
                        return mime_data
                    else:
                        pass
                else:
                    pass
            else:
                pass

        return mime_data


class LibraryTreeFilterProxyModel(QtCore.QSortFilterProxyModel):
    __slots__ = ("_search_role",)

    def __init__(self, search_role: int, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        self._search_role = search_role
        self.setRecursiveFilteringEnabled(True)
        self.setAutoAcceptChildRows(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(search_role)
        self.setFilterKeyColumn(0)

    def mimeData(self, indexes: List[QtCore.QModelIndex]) -> QtCore.QMimeData:
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            source_indexes: List[QtCore.QModelIndex] = [self.mapToSource(index) for index in indexes if index.isValid()]
            return source_model.mimeData(source_indexes)
        else:
            return super().mimeData(indexes)

    def supportedDragActions(self) -> QtCore.Qt.DropAction:
        source_model: QtCore.QAbstractItemModel | None = self.sourceModel()
        if isinstance(source_model, DynamicsLibraryTreeModel):
            return source_model.supportedDragActions()
        else:
            return super().supportedDragActions()


class DynamicEditorLibrary:
    def __init__(self,
                 api_object: ALL_DEV_TYPES,
                 mode: DynamicSimulationMode = DynamicSimulationMode.RMS,
                 templates_list: Optional[List[RmsModelTemplate | EmtModelTemplate | FmuTemplate]] = None):

        self.api_object = api_object
        self.mode = mode
        self.templates_list = templates_list
        self.block_role: int = int(QtCore.Qt.ItemDataRole.UserRole) + 300
        self.mime_type: str = "application/x-veragrid-dynamics-block"
        self.LIBRARY_SEARCH_TEXT_ROLE: int = int(QtCore.Qt.ItemDataRole.UserRole) + 502

        # Library categories:

        # emt common
        self.common_emt_device_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Generic", BlockType.GENERIC),
            LibraryLeafSpec("Voltage source EMT", BlockType.VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Current source EMT", BlockType.CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled voltage source EMT", BlockType.CONTROLLED_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled current source EMT", BlockType.CONTROLLED_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("DC voltage source EMT", BlockType.DC_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("DC current source EMT", BlockType.DC_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled DC voltage source EMT", BlockType.CONTROLLED_DC_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled DC current source EMT", BlockType.CONTROLLED_DC_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Balanced 3-phase voltage source EMT", BlockType.BALANCED_3PH_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Balanced 3-phase current source EMT", BlockType.BALANCED_3PH_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Controlled balanced 3-phase voltage source EMT",
                            BlockType.CONTROLLED_BALANCED_3PH_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Controlled balanced 3-phase current source EMT",
                            BlockType.CONTROLLED_BALANCED_3PH_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Arbitrary waveform voltage source EMT", BlockType.ARBITRARY_WAVEFORM_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Arbitrary waveform current source EMT", BlockType.ARBITRARY_WAVEFORM_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Step voltage source EMT", BlockType.STEP_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Step current source EMT", BlockType.STEP_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Ramp voltage source EMT", BlockType.RAMP_VOLTAGE_SOURCE_EMT),
            LibraryLeafSpec("Ramp current source EMT", BlockType.RAMP_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Double exponential current source EMT", BlockType.DOUBLE_EXPONENTIAL_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Heidler current source EMT", BlockType.HEIDLER_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("CIGRE surge current source EMT", BlockType.CIGRE_SURGE_CURRENT_SOURCE_EMT),
            LibraryLeafSpec("Switch EMT", BlockType.SWITCH_EMT),
            LibraryLeafSpec("Ground EMT", BlockType.GROUND_EMT),
            LibraryLeafSpec("Grounding Link EMT", BlockType.GROUNDING_LINK_EMT),
            LibraryLeafSpec("Nonlinear Resistor EMT", BlockType.NONLINEAR_RESISTOR_EMT),
            LibraryLeafSpec("RLC Combo", BlockType.RLC_COMBO_EMT),
            LibraryLeafSpec("R load", BlockType.R_LOAD_EMT),
            LibraryLeafSpec("L load", BlockType.L_LOAD_EMT),
            LibraryLeafSpec("C load", BlockType.C_LOAD_EMT),
            LibraryLeafSpec("DC load", BlockType.DC_LOAD_EMT),
        ])

        # emt fault
        self.common_emt_fault_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Fault EMT", BlockType.FAULT_EMT),
        ])

        # common rms
        self.common_rms_device_blocks: List[LibraryLeafSpec] = list([
            LibraryLeafSpec("Pll transformer", BlockType.PLL_TRANSFORM_RMS),
            LibraryLeafSpec("Pi current controller", BlockType.PI_CURRENT_CONTROLLER),
            LibraryLeafSpec("Pi power controller", BlockType.PI_POWER_CONTROLLER)])

        # devices rms
        self.device_rms_related_blocks = {
            DeviceType.GeneratorDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Generator basic", BlockType.GENRAW),
                LibraryLeafSpec("Generator QEC", BlockType.GENQEC),
                LibraryLeafSpec("Governor", BlockType.GOV_RMS),
                LibraryLeafSpec("Stabilizer", BlockType.STAB_RMS),
                LibraryLeafSpec("Exciter", BlockType.EXCITER_RMS),

            ],
            DeviceType.VscDevice: [
                LibraryLeafSpec("Gfl converter", BlockType.GFL_CONVERTER_RMS),
            ],
            DeviceType.LineDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Line", BlockType.LINE_RMS),
            ],

            DeviceType.LoadDevice: [
                LibraryLeafSpec("Generic", BlockType.GENERIC),
                LibraryLeafSpec("Load", BlockType.LOAD_RMS),
                # LibraryLeafSpec("Load", BlockType.DC_PV_SOURCE_RMS),
            ],
        }
        # devices emt
        self.device_emt_related_blocks = {
            DeviceType.GeneratorDevice: [
                LibraryLeafSpec("Generator", BlockType.EMT_GENERATOR),
                LibraryLeafSpec("Thevenin eq. generator", BlockType.EMT_THEVENIN),
                LibraryLeafSpec("Governor", BlockType.GOV_EMT),
                LibraryLeafSpec("Stabilizer", BlockType.STAB_EMT),
                LibraryLeafSpec("Exciter", BlockType.EXCITER_EMT),
                LibraryLeafSpec("PV power plant", BlockType.PV_POWER_PLANT_EMT),
                LibraryLeafSpec("PV ", BlockType.PV_EMT),
            ],
            DeviceType.BatteryDevice: [
                LibraryLeafSpec("BESS ", BlockType.BESS_EMT),
                LibraryLeafSpec("Battery ", BlockType.BATTERY_EMT),
            ],
            DeviceType.LineDevice: [
                LibraryLeafSpec("Emt pi line", BlockType.EMT_PI_LINE),
                LibraryLeafSpec("Emt Bergeron line", BlockType.EMT_BERGERON_LINE),
                LibraryLeafSpec("Emt JMarti line", BlockType.EMT_JMARTI_LINE),
            ],
            DeviceType.DCLineDevice: [
                LibraryLeafSpec("Emt DC line", BlockType.EMT_DC_LINE),
            ],
            DeviceType.LoadDevice: [  # the other types of loads already appear in common emt device blocks
                LibraryLeafSpec("Exponential load", BlockType.EXP_LOAD_EMT),
                LibraryLeafSpec("ZIP load", BlockType.ZIP_LOAD_EMT),
                LibraryLeafSpec("Induction motor", BlockType.INDUCTION_MOTOR_EMT)
            ],
            DeviceType.Transformer2WDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.Transformer3WDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.TransformerTypeDevice: [
                LibraryLeafSpec("Transformer", BlockType.TRAFO_EMT),
                LibraryLeafSpec("XFMR Transformer", BlockType.XFMR_TRANSFORMER),
            ],
            DeviceType.VscDevice: [
                LibraryLeafSpec("Complete pseudo-EMT VSC", BlockType.COMPLETE_PSEUDO_VSC_EMT),
                # LibraryLeafSpec("pseudo-EMT VSC", BlockType.PSEUDO_VSC_EMT),
                # LibraryLeafSpec("PLL VSC", BlockType.PLL_EMT),
                # LibraryLeafSpec("Outer loop VSC", BlockType.OUTER_LOOP_EMT),
                # LibraryLeafSpec("Inner loop VSC", BlockType.INNER_LOOP_EMT),
                # LibraryLeafSpec("Reduced transformer VSC", BlockType.REDUCED_TRANSFORMER_EMT),
            ],

        }

        # Build tree structure
        self.tree_structure: Dict[str, Any] = dict()
        if mode == DynamicSimulationMode.RMS:
            self.tree_structure["Basic"] = build_basic_library_branch()
            self.tree_structure["Basic_devices"] = list(self.common_rms_device_blocks)
            self.tree_structure["Devices"] = self.device_rms_related_blocks.get(
                self.api_object.device_type if self.api_object is not None else DeviceType.NoDevice, dict())

        elif mode == DynamicSimulationMode.EMT:
            self.tree_structure["Basic"] = build_basic_library_branch()
            specific_emt_blocks: List[LibraryLeafSpec] = list(
                self.device_emt_related_blocks.get(
                    self.api_object.device_type if self.api_object is not None else DeviceType.NoDevice, list()))
            self.tree_structure["Devices"] = list(self.common_emt_device_blocks + specific_emt_blocks)
            self.tree_structure["Faults"] = list(self.common_emt_fault_blocks)

        else:
            pass

        self.tree_structure["Tools"] = [
            LibraryLeafSpec("Signal Pair", BlockType.FROM_GOTO)]

        if self.templates_list:
            self.tree_structure["Templates"] = {
                "Available": [LibraryLeafSpec(template.name, template, template.name) for template in
                              self.templates_list]
            }
        else:
            pass

        # build and add library model
        self.library_model = self.build_library_tree_model()

    def build_library_tree_model(self) -> DynamicsLibraryTreeModel:
        """
        Build the source tree-view model for dynamic library.

        :param block_role:
        :type block_role:
        :param mime_type:
        :type mime_type:
        :return:
        :rtype:
        """

        model: DynamicsLibraryTreeModel = DynamicsLibraryTreeModel(self.block_role, self.mime_type)
        model.setHorizontalHeaderLabels(["Dynamic library"])
        root_item: QtGui.QStandardItem = model.invisibleRootItem()

        category: str
        branch_data: Any
        for category, branch_data in self.tree_structure.items():
            self._append_library_branch(model, root_item, category, branch_data)

        return model

    def _append_library_branch(self,
                               model: DynamicsLibraryTreeModel,
                               parent_item: QtGui.QStandardItem,
                               branch_label: str,
                               branch_data: Any,
                               path_tokens: tuple[str, ...] = tuple()) -> None:
        """
        Append one recursive library branch into the tree model.
        """

        branch_item: QtGui.QStandardItem = QtGui.QStandardItem(branch_label)
        branch_item.setEditable(False)
        branch_item.setData(" ".join((*path_tokens, branch_label)).strip(), self.LIBRARY_SEARCH_TEXT_ROLE)
        parent_item.appendRow(branch_item)

        if len(path_tokens) == 0:
            category_icon_path: str | None = device_type_icons.get(branch_label, None)
            if category_icon_path is not None:
                branch_item.setIcon(QtGui.QIcon(category_icon_path))
            else:
                pass
        else:
            pass

        if isinstance(branch_data, dict):
            child_label: str
            child_data: Any
            for child_label, child_data in branch_data.items():
                self._append_library_branch(model, branch_item, child_label, child_data, (*path_tokens, branch_label))
        else:
            if isinstance(branch_data, list):
                leaf: LibraryLeafSpec
                for leaf in sorted(branch_data, key=_library_leaf_label_sort_key):
                    item: QtGui.QStandardItem = QtGui.QStandardItem(leaf.label)
                    item.setEditable(False)
                    item.setData(leaf.search_text if leaf.search_text else leaf.label, self.LIBRARY_SEARCH_TEXT_ROLE)
                    set_library_item_icon(item, leaf.payload)
                    model.register_drag_payload(item, leaf.payload)
                    branch_item.appendRow(item)
            else:
                raise TypeError(f"Unsupported library branch data type {type(branch_data)!r}")


def build_basic_library_branch() -> Dict[str, Any]:
    """
    Build the nested Basic branch used by both RMS and EMT editors.
    """
    # build native branch
    native_branch: Dict[str, Any] = {
        "Arithmetic": [
            LibraryLeafSpec("Const", BlockType.CONST),
            LibraryLeafSpec("Gain", BlockType.GAIN),
            LibraryLeafSpec("Sum", BlockType.SUM),
            LibraryLeafSpec("Substr", BlockType.SUBSTR),
            LibraryLeafSpec("Product", BlockType.PRODUCT),
            LibraryLeafSpec("Divide", BlockType.DIVIDE),
            LibraryLeafSpec("Abs", BlockType.ABS),
        ],
    }

    # build catalogue branch
    branch: Dict[str, Any] = build_basic_block_catalog_branch_skeleton()

    descriptor: BasicBlockTemplateDescriptor
    for descriptor in get_editor_ready_basic_block_catalog_descriptors():
        category_path: tuple[str, ...] = descriptor.category_path[1:] if descriptor.category_path and \
                                                                         descriptor.category_path[
                                                                             0] == "Native" else descriptor.category_path
        if len(category_path) == 0:
            category_path = ("Miscellaneous", "Other")
        else:
            pass

        insert_library_leaf(
            branch=branch,
            category_path=category_path,
            leaf=LibraryLeafSpec(
                label=descriptor.display_label,
                payload=descriptor,
                search_text=descriptor.search_text,
            ),
        )

    if len(branch["Miscellaneous"]["Other"]) == 0:
        del branch["Miscellaneous"]
    else:
        pass
    native_branch.update(branch)

    return {
        "Native": native_branch,
    }


def _library_leaf_label_sort_key(leaf: "LibraryLeafSpec") -> str:
    """
    Return the case-insensitive sort key for one library leaf.

    :param leaf: Library leaf specification.
    :return: Lower-case label.
    """
    return leaf.label.lower()


def is_supported_library_payload(item_data: object) -> bool:
    """
    Check whether a tree item payload can be dragged into the editor scene.

    :param item_data: Candidate payload object.
    :return: ``True`` when the payload can be materialized in the editor.
    """
    if isinstance(item_data, BlockType):
        return True
    elif isinstance(item_data, BasicBlockTemplateDescriptor):
        return True
    elif isinstance(item_data, (RmsModelTemplate, EmtModelTemplate, FmuTemplate)):
        return True
    else:
        return False


def insert_library_leaf(branch: Dict[str, Any], category_path: tuple[str, ...], leaf: LibraryLeafSpec) -> None:
    """
    Insert one library leaf into a nested dictionary branch.
    """

    head: str = category_path[0]
    if len(category_path) == 1:
        leaves: Any = branch.setdefault(head, list())
        if isinstance(leaves, list):
            leaves.append(leaf)
        else:
            raise TypeError(f"Category '{head}' is already used as a branch node")
    else:
        child_branch: Any = branch.setdefault(head, dict())
        if isinstance(child_branch, dict):
            insert_library_leaf(child_branch, category_path[1:], leaf)
        else:
            raise TypeError(f"Category '{head}' is already used as a leaf collection")


def set_library_item_icon(item: QtGui.QStandardItem, payload: object) -> None:
    """
    Apply the best matching icon for one draggable library leaf.
    """

    if isinstance(payload, FmuTemplate):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.FmuTemplateDevice.value]))
    elif isinstance(payload, RmsModelTemplate):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.RmsModelTemplateDevice.value]))
    elif isinstance(payload, (EmtModelTemplate, BasicBlockTemplateDescriptor)):
        item.setIcon(QtGui.QIcon(device_type_icons[DeviceType.EmtModelTemplateDevice.value]))
    else:
        pass
