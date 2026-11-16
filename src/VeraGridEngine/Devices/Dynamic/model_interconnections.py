"""Create interconnection ports using the existing VarFactory connection graph."""
from __future__ import annotations

from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Devices.Parents.dynamic_parent import DynamicDevice
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Var
from VeraGridEngine.Utils.Symbolic.symbolic_io import duplicate_var_uid
from VeraGridEngine.enumerations import BlockType


def get_interconnection_variables(device: DynamicDevice) -> list[Var]:
    """Collect selectable variables from the device-owned RMS block hierarchy.

    :param device: Static device supplying its dynamic variables.
    :return: Unique variables in declaration order.
    """
    variables: list[Var] = list()
    seen: set[int] = set()
    block: Block
    for block in device.rms_model.get_all_blocks():
        collection: list[Var]
        for collection in (block.state_vars, block.algebraic_vars, block.diff_vars,
                           list(block.parameters), list(block.event_dict), list(block.mode_dict),
                           block.in_vars, block.out_vars):
            variable: Var
            for variable in collection:
                if variable.non_mutable_uid not in seen:
                    seen.add(variable.non_mutable_uid)
                    variables.append(variable)
                else:
                    pass
    return variables


def add_interconnection_block(root: Block, var_factory: VarFactory, device: DynamicDevice | None,
                              variables: list[Var], x: float = 0.0, y: float = 0.0) -> Block:
    """Create a measurement-like output block and its diagram node without Qt.

    Outputs reuse the source UIDs through ordinary factory connections. They
    introduce no equations or states and need no runtime resolution phase.

    :param root: Receiving model container.
    :param var_factory: Factory owning the receiver's working variables.
    :param device: Source device, absent for an unconfigured library item.
    :param variables: Selected variables from the source model.
    :param x: Initial diagram x coordinate.
    :param y: Initial diagram y coordinate.
    :return: Child block registered in the model and its diagram.
    """
    block: Block = Block(name="Interconnection" if device is None else f"Interconnection: {device.name}",
                         is_decomposable=False)
    known_variables: dict[int, Var] = dict(var_factory.get_vars_dict())
    known_variables.update(var_factory.get_diff_var_dict())
    source: Var
    for source in variables:
        # Register an isolated source copy when working in the editor factory.
        # Keeping its stable identity lets the existing connection graph survive
        # editor acceptance and ordinary template materialization.
        incoming: Var | None = duplicate_var_uid(var_factory, known_variables, source)
        if incoming is None:
            raise ValueError("Interconnection source cannot be empty")
        else:
            pass
        output: Var = var_factory.add_var(name=source.name, reference=source.ref)
        var_factory.add_network_connection(var_to_subs=output, incoming_var=incoming)
        block.out_vars.append(output)
    root.add(block)
    root.diagram.add_node(name=block.name, x=x, y=y, tpe=BlockType.INTERCONNECTION.name,
                          device_uid=block.uid, api_object_name="" if device is None else device.idtag)
    return block
