# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from PySide6.QtCore import Qt, QPoint, QModelIndex, QItemSelectionModel
from PySide6 import QtWidgets

from VeraGrid.Gui.Main.SubClasses.Settings.configuration import ConfigurationMain
from VeraGrid.Gui.scenario_tree_model import ScenarioTreeModel
from VeraGrid.Gui import gui_functions as gf
from VeraGrid.Gui.messages import yes_no_question, warning_msg
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
from VeraGridEngine.Devices.multiverse import MultiVerse, ScenarioNode


class ScenariosMain(ConfigurationMain):
    """
    Scenarios Main
    """

    def __init__(self, parent=None):
        """
        Initialize the Scenarios Main window.

        :param parent: Parent widget
        """

        # create main window
        ConfigurationMain.__init__(self, parent)



        self.ui.multiverseTreeView.setModel(self.scenario_tree_model)

        # Disable editing on double-click, only allow editing via the rename menu option
        self.ui.multiverseTreeView.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        # Set context menu policy to CustomContextMenu
        self.ui.multiverseTreeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Connect context menu signal
        self.ui.multiverseTreeView.customContextMenuRequested.connect(self.show_scenario_tree_context_menu)

        # Show the initially active scenario (root) in the label
        self.ui.activeScenarioLabel.setText(f"Current: {self.multiverse.current_model.name}")

    # ------------------------------------------------------------------
    # Property override: rebuilds MultiVerse and resets the scenario tree
    # whenever a new grid is loaded, replacing the old root entirely.
    # ------------------------------------------------------------------
    @property
    def circuit(self) -> MultiCircuit:
        return self.multiverse.current_model

    @circuit.setter
    def circuit(self, val: MultiCircuit) -> None:
        # Rebuild the entire MultiVerse so the root node's data matches the new grid
        self.multiverse = MultiVerse(current_model=val)
        self.ui.activeScenarioLabel.setText(f"Current: {val.name}")

    def get_selected_scenario_index(self) -> QModelIndex | None:
        """
        Get the currently selected QModelIndex from the tree view.

        :return: QModelIndex if a node is selected, None otherwise
        """
        selection_model = self.ui.multiverseTreeView.selectionModel()
        if selection_model is None:
            return None

        selected_indexes = selection_model.selectedIndexes()
        if len(selected_indexes) > 0:
            return selected_indexes[0]
        else:
            return None

    def get_selected_scenario_node(self) -> ScenarioNode | None:
        """
        Get the currently selected ScenarioNode from the tree view.

        :return: ScenarioNode if a node is selected, None otherwise
        """
        index: QModelIndex | None = self.get_selected_scenario_index()
        if index is not None:
            return self.scenario_tree_model.get_node(index)
        else:
            return None

    def prompt_scenario_name(self, title: str = "Scenario Name", default_name: str = "New Scenario") -> str | None:
        """
        Prompt the user to enter a scenario name using a dialog.

        :param title: Dialog title
        :param default_name: Default name to display in the input field
        :return: Entered name if accepted, None if cancelled
        """
        text: str = ""
        ok: bool = False

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            title,
            "Enter scenario name:",
            QtWidgets.QLineEdit.EchoMode.Normal,
            default_name
        )

        if ok:
            if text.strip() != "":
                return text.strip()
            else:
                warning_msg("Scenario name cannot be empty", title)
                return None
        else:
            return None

    def show_scenario_tree_context_menu(self, pos: QPoint) -> None:
        """
        Display context menu for scenario tree operations.

        :param pos: Relative click position
        """
        context_menu: QtWidgets.QMenu = QtWidgets.QMenu(parent=self.ui.multiverseTreeView)

        # Get the selected index to determine which actions to enable
        selected_index: QModelIndex | None = self.get_selected_scenario_index()
        has_selection: bool = selected_index is not None and selected_index.isValid()

        # Add child scenario - only available if a node is selected
        if has_selection:
            # Set as the current scenario - only available if a node is selected
            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Set as current scenario"),
                icon_path=":/Icons/icons/schematic.png",
                function_ptr=self.set_as_current_scenario
            )

            # Rename scenario - only available if a node is selected
            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Rename scenario"),
                icon_path=":/Icons/icons/edit.png",
                function_ptr=self.rename_scenario
            )

            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Commit scenario"),
                icon_path=":/Icons/icons/save.png",
                function_ptr=self.commit_scenario
            )

            # Separator
            context_menu.addSeparator()

            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Add child scenario"),
                icon_path=":/Icons/icons/plus.png",
                function_ptr=self.add_child_scenario
            )

            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Merge children into scenario"),
                icon_path=":/Icons/icons/fusion.png",
                function_ptr=self.merge_children_into_scenario
            )

            # Separator before delete
            context_menu.addSeparator()

            # Remove scenario - only available if a node is selected
            gf.add_menu_entry(
                menu=context_menu,
                text=self.tr("Remove scenario"),
                icon_path=":/Icons/icons/minus.png",
                function_ptr=self.remove_scenario
            )

            # Convert the global position to the local position of the tree view
            mapped_pos: QPoint = self.ui.multiverseTreeView.viewport().mapToGlobal(pos)
            context_menu.exec(mapped_pos)
        else:
            self.show_warning_toast("Select a scenario...")

    # def add_root_scenario(self) -> None:
    #     """
    #     Add a new root scenario to the multiverse.
    #     Prompts the user for a scenario name and creates a new MultiCircuit.
    #     """
    #     scenario_name: str | None = self.prompt_scenario_name(
    #         title="Add Root Scenario",
    #         default_name=f"Scenario {self.multiverse.roots_number() + 1}"
    #     )
    #
    #     if scenario_name is not None:
    #         # Create a new MultiCircuit as a copy of the current model
    #         new_circuit: MultiCircuit = self.circuit.copy()
    #         new_circuit.name = scenario_name
    #
    #         # Add the root node through the model
    #         node: ScenarioNode = self.scenario_tree_model.append_root(data=new_circuit)
    #
    #         self.show_info_toast(f"Root scenario '{scenario_name}' added")
    #     else:
    #         # User cancelled the operation
    #         pass

    def add_child_scenario(self) -> None:
        """
        Add a child scenario to the selected scenario node.
        The child starts as a copy of the parent's composed circuit (delta chain applied).
        """
        parent_index: QModelIndex | None = self.get_selected_scenario_index()

        if parent_index is None or not parent_index.isValid():
            warning_msg("Please select a parent scenario first", "Add Child Scenario")
            return

        parent_node: ScenarioNode | None = self.scenario_tree_model.get_node(parent_index)

        if parent_node is None:
            warning_msg("Invalid parent scenario selected", "Add Child Scenario")
            return

        # Count existing children for default naming
        child_count: int = parent_node.child_count()
        scenario_name: str | None = self.prompt_scenario_name(
            title="Add Child Scenario",
            default_name=f"{parent_node.circuit.name} - Child {child_count + 1}"
        )

        if scenario_name is not None:
            # The child must inherit the latest parent state, including diagrams.
            # Commit first so parent-owned node storage reflects any pending edits.
            self.multiverse.commit_current()

            # Non-root nodes store a delta, not a full circuit.
            # A brand-new child starts with an empty delta (no changes from parent yet).
            initial_delta: MultiCircuit = MultiCircuit(name=scenario_name)

            # Add the child node through the model
            node: ScenarioNode = self.scenario_tree_model.append_child(
                parent_index=parent_index,
                data=initial_delta
            )

            # Activate the new child immediately
            circuit: MultiCircuit = self.multiverse.activate_scenario(node.node_id)
            self.scenario_tree_model.refresh_data()
            self.ui.activeScenarioLabel.setText(f"Current: {circuit.name}")
            self.reload_diagrams_for_active_scenario()
            self.update_date_dependent_combos()
            self.view_objects_data()
            self.update_available_results()

            # Expand the parent node to show the new child
            self.ui.multiverseTreeView.expand(parent_index)

            # Select the newly created child in the tree
            child_index: QModelIndex = self.scenario_tree_model.index(
                row=node.row(),
                column=0,
                parent=parent_index,
            )
            if child_index.isValid():
                self.ui.multiverseTreeView.setCurrentIndex(child_index)
                self.ui.multiverseTreeView.selectionModel().select(
                    child_index,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                self.ui.multiverseTreeView.scrollTo(child_index)

            self.show_info_toast(f"Child scenario '{scenario_name}' added and activated")
        else:
            # User cancelled the operation
            pass

    def remove_scenario(self) -> None:
        """
        Remove the selected scenario node and its subtree.
        Asks for confirmation before removing.
        """
        selected_index: QModelIndex | None = self.get_selected_scenario_index()

        if selected_index is None or not selected_index.isValid():
            warning_msg("Please select a scenario to remove", "Remove Scenario")
            return

        node: ScenarioNode | None = self.scenario_tree_model.get_node(selected_index)

        if node is None:
            warning_msg("Invalid scenario selected", "Remove Scenario")
            return

        circuit: MultiCircuit = node.circuit
        child_count: int = node.child_count()

        # Build confirmation message
        message: str = f"Are you sure you want to remove scenario '{circuit.name}'?"
        if child_count > 0:
            message += f"\n\nThis will also remove {child_count} child scenario(s)."

        ok: bool = yes_no_question(message, "Remove Scenario")

        if ok:
            # Deletion always falls back to the parent node, or to the first remaining root
            # when a non-last root is deleted. Capture that target before mutating the tree.
            fallback_node: ScenarioNode | None = node.parent
            if fallback_node is None:
                remaining_roots = [root for root in self.multiverse.root_nodes if root is not node]
                fallback_node = remaining_roots[0] if remaining_roots else None

            # Remove the node through the model
            try:
                success: bool = self.scenario_tree_model.remove_node(selected_index)
            except ValueError as exc:
                warning_msg(str(exc), "Remove Scenario")
                return

            if success:
                # Keep the tree selection and the active circuit views aligned with the
                # scenario that survived the deletion.
                if fallback_node is not None:
                    fallback_index = self.scenario_tree_model.index_for_node(fallback_node)
                    if fallback_index.isValid():
                        self.ui.multiverseTreeView.setCurrentIndex(fallback_index)
                        self.ui.multiverseTreeView.selectionModel().select(
                            fallback_index,
                            QItemSelectionModel.SelectionFlag.ClearAndSelect
                            | QItemSelectionModel.SelectionFlag.Rows,
                        )
                        self.ui.multiverseTreeView.scrollTo(fallback_index)

                self.ui.activeScenarioLabel.setText(f"Current: {self.multiverse.current_model.name}")
                self.reload_diagrams_for_active_scenario()
                self.update_date_dependent_combos()
                self.view_objects_data()
                self.update_available_results()
                self.show_info_toast(f"Scenario '{circuit.name}' removed")
            else:
                warning_msg("Failed to remove scenario", "Remove Scenario")
        else:
            # User cancelled the operation
            pass

    def merge_children_into_scenario(self) -> None:
        """
        Merge all direct child scenarios into the selected scenario.
        The selected node keeps the merged result and any grandchildren are
        rebased directly under it.
        """
        selected_index: QModelIndex | None = self.get_selected_scenario_index()

        if selected_index is None or not selected_index.isValid():
            warning_msg("Please select a scenario to merge into", "Merge Children")
            return

        node: ScenarioNode | None = self.scenario_tree_model.get_node(selected_index)

        if node is None:
            warning_msg("Invalid scenario selected", "Merge Children")
            return

        child_count: int = node.child_count()
        if child_count == 0:
            self.show_warning_toast(f"Scenario '{node.circuit.name}' has no child scenarios")
            return

        ok: bool = yes_no_question(
            f"Merge {child_count} child scenario(s) into '{node.circuit.name}'?\n\n"
            f"This will remove the direct child scenarios after their changes are applied.",
            "Merge Children"
        )

        if not ok:
            return

        success: bool = self.scenario_tree_model.merge_children_into_parent(selected_index)

        if not success:
            warning_msg("Failed to merge child scenarios", "Merge Children")
            return

        merged_circuit: MultiCircuit = self.multiverse.current_model

        # The merge target becomes the active scenario after the children disappear.
        self.ui.activeScenarioLabel.setText(f"Current: {merged_circuit.name}")
        self.reload_diagrams_for_active_scenario()
        self.update_date_dependent_combos()
        self.view_objects_data()
        self.update_available_results()
        parent_index = self.scenario_tree_model.index_for_node(self.multiverse.current_node)
        if parent_index.isValid():
            self.ui.multiverseTreeView.expand(parent_index)
            self.ui.multiverseTreeView.setCurrentIndex(parent_index)
            self.ui.multiverseTreeView.selectionModel().select(
                parent_index,
                QItemSelectionModel.SelectionFlag.ClearAndSelect
                | QItemSelectionModel.SelectionFlag.Rows,
            )
            self.ui.multiverseTreeView.scrollTo(parent_index)

        self.show_info_toast(f"Merged {child_count} child scenario(s) into '{node.circuit.name}'")

    def reload_diagrams_for_active_scenario(self) -> None:
        """
        Rebuild the diagram widgets from the currently active scenario circuit.

        This intentionally avoids assigning through ``self.circuit`` because that setter
        rebuilds the whole MultiVerse.
        """
        self.remove_all_diagrams()

        if self.circuit.has_diagrams():
            self.create_circuit_stored_diagrams()
        else:
            pass

    def rename_scenario(self) -> None:
        """
        Rename the selected scenario node.
        Opens the tree view's inline editor for the selected item.
        """
        selected_index: QModelIndex | None = self.get_selected_scenario_index()

        if selected_index is None or not selected_index.isValid():
            warning_msg("Please select a scenario to rename", "Rename Scenario")
            return

        # Use the tree view's built-in editing capability
        self.ui.multiverseTreeView.edit(selected_index)

    def commit_scenario(self) -> None:
        """
        Commit the currently active scenario node, persisting its edits into the stored
        node representation.
        """
        selected_index: QModelIndex | None = self.get_selected_scenario_index()

        if selected_index is None or not selected_index.isValid():
            warning_msg("Please select a scenario to commit", "Commit Scenario")
            return

        node: ScenarioNode | None = self.scenario_tree_model.get_node(selected_index)

        if node is None:
            warning_msg("Invalid scenario selected", "Commit Scenario")
            return

        if node is not self.multiverse.current_node:
            warning_msg("Only the current scenario can be committed. Activate it first.", "Commit Scenario")
            return

        self.multiverse.commit_current()
        self.scenario_tree_model.refresh_data()
        self.show_info_toast(f"Scenario '{node.circuit.name}' committed")

    def set_as_current_scenario(self) -> None:
        """
        Set the selected scenario as the current working scenario.
        Commits any unsaved edits on the current scenario first, then activates the selected one.
        """
        selected_index: QModelIndex | None = self.get_selected_scenario_index()

        if selected_index is None or not selected_index.isValid():
            warning_msg("Please select a scenario to set as current", "Set Current Scenario")
            return

        node: ScenarioNode | None = self.scenario_tree_model.get_node(selected_index)

        if node is None:
            warning_msg("Invalid scenario selected", "Set Current Scenario")
            return

        if node is self.multiverse.current_node:
            self.show_warning_toast(f"'{node.circuit.name}' is already the active scenario")
            return

        circuit: MultiCircuit = self.multiverse.activate_scenario(node.node_id)

        # set the session drivers
        self.session.drivers = node.drivers

        # Refresh counts: commit_current() may have updated the previous node's delta
        self.scenario_tree_model.refresh_data()

        # Update the UI label
        self.ui.activeScenarioLabel.setText(f"Current: {circuit.name}")

        self.reload_diagrams_for_active_scenario()

        # Update other UI elements that depend on the circuit
        self.update_date_dependent_combos()
        self.view_objects_data()
        self.update_available_results()

        self.show_info_toast(f"Current scenario set to '{circuit.name}'")
