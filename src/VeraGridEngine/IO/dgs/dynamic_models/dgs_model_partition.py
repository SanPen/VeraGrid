# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Deterministic ownership and factory wiring for multi-device DGS roots."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.model_interconnections import add_interconnection_block
from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.IO.dgs.dgs_circuit import DgsCircuit
from VeraGridEngine.IO.dgs.dgs_objects import BlkSig
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagramNode, BlockDiagramConnection
from VeraGridEngine.IO.dgs.dgs_to_blocks import DgsDirectRootBuildResult
from VeraGridEngine.IO.dgs.dynamic_models.dgs_native_model_workflow import NativeDgsEquipmentPlan
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import collect_block_vars_by_non_mutable_uid


class DgsModelPartition:
    """Hold one transient import partition, never runtime reference metadata."""

    __slots__ = ("plan", "device", "control", "slots", "template", "runtime_variables")

    def __init__(self, plan: NativeDgsEquipmentPlan, device: DynamicDevice, control: Block,
                 slots: set[str]) -> None:
        """Retain exact source ownership until every model has been instantiated.

        :param plan: Native equipment requirement.
        :param device: Exact destination device.
        :param control: Controller subtree owned by this device.
        :param slots: Assigned source slot identifiers.
        :return: None.
        """
        self.plan: NativeDgsEquipmentPlan = plan
        self.device: DynamicDevice = device
        self.control: Block = control
        self.slots: set[str] = slots
        self.template: RmsModelTemplate | None = None
        self.runtime_variables: dict[int, list[Var]] = dict()


def assign_dgs_slot_owners(direct: DgsDirectRootBuildResult, circuit: DgsCircuit,
                           native_hosts: dict[str, str]) -> dict[str, str]:
    """Trace exact cable dependencies back from native equipment anchors.

    Shared and disconnected blocks choose the lexically smallest source FID.
    No state or controller is copied to satisfy multiple consumers.

    :param direct: Materialized root and direct source slots.
    :param circuit: Authoritative cable rows.
    :param native_hosts: Native slot to physical equipment FID.
    :return: One physical equipment owner per direct slot.
    """
    slots: set[str] = set(entry.slot_id for entry in direct.direct_entries if entry.slot_id is not None)
    successors: dict[str, set[str]] = dict((slot, set()) for slot in slots)
    destinations: dict[str, set[str]] = dict((slot, set()) for slot in slots)
    slot: str
    host: str
    for slot, host in native_hosts.items():
        destinations[slot].add(host)
    cable: BlkSig
    for cable in circuit.blksigs:
        source: str = str(cable.pnodfrom).lstrip('#')
        target: str = str(cable.pnodto).lstrip('#')
        if source in slots and target in slots and int(cable.iconfrom) == 2 and int(cable.iconto) == 1:
            successors[source].add(target)
        else:
            pass
    # Bounded propagation handles feedback cycles without choosing a traversal order.
    iteration: int
    for iteration in range(len(slots)):
        changed: bool = False
        for slot in sorted(slots):
            if slot not in native_hosts:
                before: int = len(destinations[slot])
                for target in successors[slot]:
                    destinations[slot].update(destinations[target])
                changed = changed or len(destinations[slot]) != before
            else:
                pass
        if not changed:
            break
        else:
            pass
    default_host: str = min(native_hosts.values())
    return dict((slot, min(destinations[slot]) if len(destinations[slot]) > 0 else default_host)
                for slot in sorted(slots))


def map_partition_runtime_variables(template: Block, instance: Block) -> dict[int, list[Var]]:
    """Recover cloned port/declaration identities through structural positions.

    :param template: Source partition before materialization.
    :param instance: Its device-owned executable copy.
    :return: Original signal UID to corresponding instantiated variables.
    """
    result: dict[int, list[Var]] = dict()
    original_blocks: list[Block] = template.get_all_blocks()
    instance_blocks: list[Block] = instance.get_all_blocks()
    if len(original_blocks) != len(instance_blocks):
        raise ValueError("DGS partition materialization changed its block hierarchy")
    else:
        pass
    original: Block
    copied: Block
    for original, copied in zip(original_blocks, instance_blocks):
        original_lists: tuple = (original.state_vars, original.algebraic_vars, original.diff_vars,
                                 original.in_vars, original.out_vars, list(original.parameters),
                                 list(original.event_dict), list(original.mode_dict), list(original.boolean_guards))
        copied_lists: tuple = (copied.state_vars, copied.algebraic_vars, copied.diff_vars,
                               copied.in_vars, copied.out_vars, list(copied.parameters),
                               list(copied.event_dict), list(copied.mode_dict), list(copied.boolean_guards))
        source_vars: list[Var]
        copied_vars: list[Var]
        for source_vars, copied_vars in zip(original_lists, copied_lists):
            if len(source_vars) != len(copied_vars):
                raise ValueError("DGS partition materialization changed its variable declarations")
            else:
                pass
            source_var: Var
            copied_var: Var
            for source_var, copied_var in zip(source_vars, copied_vars):
                if source_var.uid not in result:
                    result[source_var.uid] = list()
                else:
                    pass
                if all(variable is not copied_var for variable in result[source_var.uid]):
                    result[source_var.uid].append(copied_var)
                else:
                    pass
    return result


def connect_dgs_partitions(parts: list[DgsModelPartition], factory: VarFactory) -> None:
    """Replace cross-partition wires by normal UID-propagating interconnection items.

    :param parts: All instantiated partitions of the same source root.
    :param factory: Shared circuit variable/connection registry.
    :return: None.
    """
    owners: dict[int, DgsModelPartition] = dict()
    part: DgsModelPartition
    for part in parts:
        if part.template is None:
            raise ValueError("DGS partition has no template")
        else:
            pass
        part.runtime_variables = map_partition_runtime_variables(part.template.block, part.device.rms_model)
        block: Block
        for block in part.template.block.get_all_blocks():
            collection: list[Var]
            for collection in (block.state_vars, block.algebraic_vars, block.diff_vars,
                               list(block.parameters), list(block.event_dict), list(block.mode_dict),
                               list(block.boolean_guards)):
                variable: Var
                for variable in collection:
                    previous: DgsModelPartition | None = owners.get(variable.uid, None)
                    if previous is not None and previous is not part:
                        raise ValueError(f"DGS variable has multiple partition owners: {variable.name}")
                    else:
                        owners[variable.uid] = part
    for part in parts:
        grouped: dict[str, list[int]] = dict()
        referenced: dict[int, Var] = collect_block_vars_by_non_mutable_uid(part.template.block)
        for variable in referenced.values():
            producer: DgsModelPartition | None = owners.get(variable.uid, None)
            if producer is not None and producer is not part:
                if producer.device.idtag not in grouped:
                    grouped[producer.device.idtag] = list()
                else:
                    pass
                if variable.uid not in grouped[producer.device.idtag]:
                    grouped[producer.device.idtag].append(variable.uid)
                else:
                    pass
            else:
                pass
        source_id: str
        uid: int
        output: Var
        for source_id in sorted(grouped):
            producer = next(candidate for candidate in parts if candidate.device.idtag == source_id)
            signal_uids: list[int] = grouped[source_id]
            sources: list[Var] = list(producer.runtime_variables[uid][0] for uid in signal_uids)
            item: Block = add_interconnection_block(part.device.rms_model, factory, producer.device,
                                                    sources, -250.0, float(len(part.device.rms_model.children) * 80))
            for uid, output in zip(signal_uids, item.out_vars):
                targets: list[Var] | None = part.runtime_variables.get(uid, None)
                if targets is None:
                    raise ValueError(f"DGS crossing signal has no executable port: uid={uid}")
                else:
                    for target in targets:
                        factory.add_connection(var_to_subs=target, incoming_var=output)


def copy_partition_diagrams(template: Block, instance: Block) -> None:
    """Translate diagram block identities after ordinary symbolic duplication.

    :param template: Canonical source hierarchy.
    :param instance: Instantiated hierarchy with newly allocated block UIDs.
    :return: None.
    """
    originals: list[Block] = template.get_all_blocks()
    instances: list[Block] = instance.get_all_blocks()
    block_uids: dict[int, int] = dict((old.uid, new.uid) for old, new in zip(originals, instances))
    original: Block
    copied: Block
    for original, copied in zip(originals, instances):
        copied.diagram = original.diagram.copy()
        remapped_nodes: dict[int, BlockDiagramNode] = dict()
        uid: int
        node: BlockDiagramNode
        for uid, node in copied.diagram.node_data.items():
            node.device_uid = block_uids.get(node.device_uid, node.device_uid)
            remapped_nodes[block_uids.get(uid, uid)] = node
        copied.diagram.node_data = remapped_nodes
        edge: BlockDiagramConnection
        for edge in copied.diagram.con_data.values():
            edge.from_uid = block_uids.get(edge.from_uid, edge.from_uid)
            edge.to_uid = block_uids.get(edge.to_uid, edge.to_uid)


def build_partition_diagram_connections(root: Block) -> None:
    """Draw local and interconnection cables from their final symbolic UIDs.

    :param root: Completed partition with one node per direct child.
    :return: None.
    """
    producers: dict[int, tuple[Block, int]] = dict()
    child: Block
    index: int
    variable: Var
    for child in root.children:
        for index, variable in enumerate(child.out_vars):
            if variable.uid not in producers:
                producers[variable.uid] = (child, index)
            else:
                pass
    root.diagram.con_data = dict()
    for child in root.children:
        for index, variable in enumerate(child.in_vars):
            producer: tuple[Block, int] | None = producers.get(variable.uid, None)
            if producer is not None and producer[0] is not child:
                root.diagram.add_branch(connectionitem_uid=len(root.diagram.con_data) + 1,
                    device_uid_from=producer[0].uid, device_uid_to=child.uid,
                    port_number_from=producer[1], port_number_to=index)
            else:
                pass
