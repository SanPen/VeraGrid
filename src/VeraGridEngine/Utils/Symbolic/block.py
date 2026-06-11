# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import copy
import uuid
from typing import List, Dict, Any, Tuple

from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, _expr_to_dict, _dict_to_expr, BinOp, UnOp, Func, Func2, Comparison
from VeraGridEngine.Devices.Diagrams.block_diagram import BlockDiagram
from VeraGridEngine.enumerations import VarPowerFlowReferenceType, ParamPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.compare_expressions_structure import equivalent_systems
from VeraGridEngine.Utils.Symbolic.variable_alignment_engine import align_variables


def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int

def set_parameter(blk: Block, var_name: str, new_value: float):

    for var, expr in blk.event_dict.items():
        if var.name == var_name:
            if isinstance(expr, Const):
                expr.value = new_value
            else:
                blk.event_dict[var] = Const(new_value)


    for var, expr in blk.mode_dict.items():
        if var.name == var_name:
            if isinstance(expr, Const):
                expr.value = new_value
            else:
                blk.mode_dict[var] = Const(new_value)


    # check parameters dict
    for var, const in blk.parameters.items():
        if var.name == var_name:
            if isinstance(const, Const):
                const.value = new_value
            else:
                blk.parameters[var] = Const(new_value)




class Block:
    """
    Class representing a Block
    """

    def __init__(self,
                 state_vars: List[Var] | None = None,
                 state_eqs: List[Expr] | None = None,
                 algebraic_vars: List[Var] | None = None,
                 algebraic_eqs: List[Expr] | None = None,
                 inequalities: List[Expr | Comparison] | None = None,
                 diff_vars: List[Var] | None = None,
                 reformulated_vars: List[Var] | None = None,
                 differential_eqs: List[Expr] | None = None,
                 parameters: Dict[Var, Const] | None = None,
                 init_values: Dict[Var, Const] | None = None,
                 init_eqs: Dict[Var, Expr] | None = None,
                 diff_init_eqs: Dict[Var, Expr] | None = None,
                 discrete_eqs: Dict[Var, Expr] | None = None,
                 children: List["Block"] | None = None,
                 in_vars: List[Var] | None = None,
                 out_vars: List[Var] | None = None,
                 event_dict: Dict[Var, Expr] | None = None,
                 mode_dict: Dict[Var, Expr] | None = None,
                 boolean_guards: Dict[Var, Expr | Comparison] | None = None,
                 procedural_logic: List[Any] | None = None,
                 external_mapping: Dict[VarPowerFlowReferenceType, Var] | None = None,
                 api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var] | None = None,
                 is_decomposable: bool = True,
                 name: str = "",
                 uid: int | None = None):
        """
        This represents a group of equations or a group of blocks

        :param algebraic_vars: List of non-differential variables (AKA algebraic)
        :param algebraic_eqs: List of equations that provide values for the algebraic variables
        :param state_vars: List of differential variables (AKA state variables)
        :param state_eqs: List of equations that provide values for the state variables
        :param children: List of other blocks to be flattened later into this block
        :param in_vars: List of variables from other blocks that we use here
        :param out_vars: List of variables that already exist in algebraic_vars or state_vars that we want to expose
        :param init_eqs: List of equations that help initializing the block variables (algebraic and state)
        :param diff_init_eqs: List of equations that help initializing the block derivatives of state variables
         :param event_dict: Dictionary of parameters that can change during the simulations
         :param procedural_logic: List of runtime procedural logic objects attached to the block
         :param external_mapping: Dictionary of vars that are related to the Power flow initialization
         :param name: name of the block
         """

        self.name: str = name

        self.uid: int = _new_uid() if uid is None else uid

        self.is_decomposable = is_decomposable
        self.tpe_uid: int | None =  None
        self.vars_glob_name2uid: Dict[str, int] = dict()

        self.state_vars: List[Var] = list() if state_vars is None else state_vars
        self.state_eqs: List[Expr] = list() if state_eqs is None else state_eqs

        self.algebraic_vars: List[Var] = list() if algebraic_vars is None else algebraic_vars
        self.algebraic_eqs: List[Expr] = list() if algebraic_eqs is None else algebraic_eqs
        self.inequalities: List[Expr | Comparison] = list() if inequalities is None else inequalities

        self.diff_vars: List[Var] = list() if diff_vars is None else diff_vars
        self.reformulated_vars: List[Var] = list() if reformulated_vars is None else reformulated_vars
        self.differential_eqs: List[Expr] = list() if differential_eqs is None else differential_eqs

        # initialization
        self.init_eqs: Dict[Var, Expr] = dict() if init_eqs is None else init_eqs
        self.diff_init_eqs: Dict[Var, Expr] = dict() if diff_init_eqs is None else diff_init_eqs

        # vars to make this recursive
        self.children: List["Block"] = list() if children is None else children

        self.in_vars: List[Var] = list() if in_vars is None else in_vars
        self.out_vars: List[Var] = list() if out_vars is None else out_vars

        self.parameters: Dict[Var, Const] = dict() if parameters is None else parameters

        self.discrete_eqs: Dict[Var, Expr] = dict() if discrete_eqs is None else discrete_eqs
        self.external_mapping: Dict[VarPowerFlowReferenceType, Var | None] = (dict()
                                                                               if external_mapping is None
                                                                               else external_mapping)

        self.api_obj_mapping: Dict[ParamPowerFlowReferenceType, Var] = (dict()
                                                                         if api_obj_mapping is None
                                                                         else api_obj_mapping)
        # initialization
        self.init_values: Dict[Var, Const] = dict() if init_values is None else init_values

        self.var_mapping = {v.name: v for v in self.algebraic_vars}

        # Dictionary of Variables and their Expressions that appear due to an event
        # this is the dictionary of "parameters" that may change and their equations
        self.event_dict: Dict[Var, Expr | Const] = dict() if event_dict is None else event_dict
        self.mode_dict: Dict[Var, Expr | Const] = dict() if mode_dict is None else mode_dict
        self.boolean_guards: Dict[Var, Expr | Comparison] = dict() if boolean_guards is None else boolean_guards
        self.procedural_logic: List[Any] = list() if procedural_logic is None else procedural_logic

        self._diagram: BlockDiagram = BlockDiagram()

    @property
    def diagram(self) -> BlockDiagram:
        """

        :return:
        """
        return self._diagram

    @diagram.setter
    def diagram(self, val: BlockDiagram | Dict[str, Any]):

        if isinstance(val, BlockDiagram):
            self._diagram = val
        elif isinstance(val, dict):
            diagram = BlockDiagram()

            self._diagram = diagram
        else:
            raise ValueError(f"Cannot set diagram with {val}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Get dictionary representation of this block
        :return: Dictionary
        """
        return {
            "name": self.name,
            "uid": self.uid,

            "state_vars": [_expr_to_dict(v) for v in self.state_vars],
            "algebraic_vars": [_expr_to_dict(v) for v in self.algebraic_vars],
            "diff_vars": [_expr_to_dict(v) for v in self.diff_vars],
            "reformulated_vars": [_expr_to_dict(v) for v in self.reformulated_vars],

            "in_vars": [_expr_to_dict(v) for v in self.in_vars],
            "out_vars": [_expr_to_dict(v) for v in self.out_vars],

            "state_eqs": [_expr_to_dict(e) for e in self.state_eqs],
            "algebraic_eqs": [_expr_to_dict(e) for e in self.algebraic_eqs],
            "inequalities": [_expr_to_dict(e) for e in self.inequalities],
            "differential_eqs": [_expr_to_dict(e) for e in self.differential_eqs],

            "init_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_eqs.items()
            },

            "diff_init_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.diff_init_eqs.items()
            },

            "event_dict": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.event_dict.items()
            },

            "mode_dict": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.mode_dict.items()
            },

            "boolean_guards": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.boolean_guards.items()
            },

            "procedural_logic": self._procedural_logic_to_dict(),

            "parameters": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.parameters.items()
            },

            "init_values": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_values.items()
            },

            "external_mapping": {
                k: _expr_to_dict(v) if v is not None else None
                for k, v in self.external_mapping.items()
            },

            "api_obj_mapping": {
                k.value: _expr_to_dict(v) if v is not None else None
                for k, v in self.api_obj_mapping.items()
            },

            "discrete_eqs": {
                k.uid: {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.discrete_eqs.items()
            },

            "children": [child.to_dict() for child in self.children],

            "diagram": self.diagram.to_dict(),
        }

    @staticmethod
    def parse(data: Dict[str, Any]) -> "Block":
        """
        Parse the dictionary representation of a block
        :param data:
        :return:
        """
        block = Block(
            state_vars=[_dict_to_expr(data=v) for v in data["state_vars"]],
            state_eqs=[_dict_to_expr(data=e) for e in data["state_eqs"]],
            algebraic_vars=[_dict_to_expr(data=v) for v in data["algebraic_vars"]],
            algebraic_eqs=[_dict_to_expr(data=e) for e in data["algebraic_eqs"]],
            inequalities=[_dict_to_expr(data=e) for e in data.get("inequalities", [])],
            diff_vars=[_dict_to_expr(data=v) for v in data["diff_vars"]],
            reformulated_vars=[_dict_to_expr(data=v) for v in data["reformulated_vars"]],
            differential_eqs=[_dict_to_expr(data=e) for e in data["differential_eqs"]],
            parameters={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data["parameters"].values()
            },
            init_values={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data["init_values"].values()
            },
            init_eqs={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data["init_eqs"].values()
            },
            diff_init_eqs={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data["diff_init_eqs"].values()
            },
            discrete_eqs={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data.get("discrete_eqs", {}).values()
            },
            children=[
                Block.parse(child_data)
                for child_data in data["children"]
            ],
            in_vars=[_dict_to_expr(data=v) for v in data["in_vars"]],
            out_vars=[_dict_to_expr(data=v) for v in data["out_vars"]],
            event_dict={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data["event_dict"].values()
            },
            mode_dict={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data.get("mode_dict", {}).values()
            },
            boolean_guards={
                _dict_to_expr(data=item["key"]): _dict_to_expr(data=item["value"])
                for item in data.get("boolean_guards", {}).values()
            },
            procedural_logic=Block._procedural_logic_from_dict(data.get("procedural_logic", [])),
            external_mapping={
                VarPowerFlowReferenceType(k): (_dict_to_expr(v) if v is not None else None)
                for k, v in data["external_mapping"].items()
            },
            api_obj_mapping={
                ParamPowerFlowReferenceType(k): (_dict_to_expr(v) if v is not None else None)
                for k, v in data["api_obj_mapping"].items()
            },
            name=data["name"],
            uid=data["uid"]
        )

        # Fill the diagram
        block.diagram.parse(data.get("diagram", {}))

        return block

    def copy(self) -> "Block":
        """
        Deep-copy this block while preserving symbolic UIDs.

        :return: Copied block.
        """
        return copy.deepcopy(self)


    def _procedural_logic_to_dict(self) -> List[Dict[str, Any]]:
        """
        Serialize block-attached procedural logic.

        :return: Serialized procedural logic entries.
        """
        from VeraGridEngine.Utils.procedural_logic import procedural_logic_to_dict
        return procedural_logic_to_dict(self.procedural_logic)

    @staticmethod
    def _procedural_logic_from_dict(data: List[Dict[str, Any]]) -> List[Any]:
        """
        Deserialize block-attached procedural logic.

        :param data: Serialized logic entries.
        :return: Procedural logic objects.
        """
        from VeraGridEngine.Utils.procedural_logic import procedural_logic_from_dict

        if len(data) == 0:
            return list()
        else:
            pass

        if isinstance(data[0], dict):
            return procedural_logic_from_dict(data)
        else:
            return list(data)

    def __deepcopy__(self, memo: Dict[int, Any]) -> "Block":
        """
        Copy the block preserving shared symbolic references inside the block graph.

        :param memo: Standard deepcopy memo table.
        :return: Copied block.
        """
        if id(self) in memo:
            return memo[id(self)]
        else:
            result: Block = Block.__new__(Block)
            memo[id(self)] = result

            result.name = copy.deepcopy(self.name, memo)
            result.uid = copy.deepcopy(self.uid, memo)
            result.vars_glob_name2uid = copy.deepcopy(self.vars_glob_name2uid, memo)
            result.state_vars = copy.deepcopy(self.state_vars, memo)
            result.state_eqs = copy.deepcopy(self.state_eqs, memo)
            result.algebraic_vars = copy.deepcopy(self.algebraic_vars, memo)
            result.algebraic_eqs = copy.deepcopy(self.algebraic_eqs, memo)
            result.inequalities = copy.deepcopy(self.inequalities, memo)
            result.diff_vars = copy.deepcopy(self.diff_vars, memo)
            result.reformulated_vars = copy.deepcopy(self.reformulated_vars, memo)
            result.differential_eqs = copy.deepcopy(self.differential_eqs, memo)
            result.init_eqs = copy.deepcopy(self.init_eqs, memo)
            result.diff_init_eqs = copy.deepcopy(self.diff_init_eqs, memo)
            result.children = copy.deepcopy(self.children, memo)
            result.in_vars = copy.deepcopy(self.in_vars, memo)
            result.out_vars = copy.deepcopy(self.out_vars, memo)
            result.parameters = copy.deepcopy(self.parameters, memo)
            result.discrete_eqs = copy.deepcopy(self.discrete_eqs, memo)
            result.external_mapping = copy.deepcopy(self.external_mapping, memo)
            result.api_obj_mapping = copy.deepcopy(self.api_obj_mapping, memo)
            result.init_values = copy.deepcopy(self.init_values, memo)
            result.var_mapping = copy.deepcopy(self.var_mapping, memo)
            result.event_dict = copy.deepcopy(self.event_dict, memo)
            result.mode_dict = copy.deepcopy(self.mode_dict, memo)
            result.boolean_guards = copy.deepcopy(self.boolean_guards, memo)
            result.procedural_logic = copy.deepcopy(self.procedural_logic, memo)
            result._diagram = copy.deepcopy(self._diagram, memo)

            extra_key: str
            extra_value: Any
            for extra_key, extra_value in self.__dict__.items():
                if extra_key in result.__dict__:
                    pass
                else:
                    setattr(result, extra_key, copy.deepcopy(extra_value, memo))
            return result

    def compare(self, block2: Block) -> bool:
        """
        Compare two blocks.
        :param block2:
        :return:
        """
        dict1 = self.to_dict()
        dict2 = block2.to_dict()
        return dict1 == dict2

    def get_all_equations_list(self):
        equations_list: List[Expr] = list()
        equations_list.extend(self.state_eqs)
        equations_list.extend(self.algebraic_eqs)
        equations_list.extend(self.differential_eqs)
        return equations_list


    def __eq__(self, other: Block) -> bool:
        x = self.compare(other)
        return x

    # def set_const(self, ref: ParamPowerFlowReferenceType, val: Const):
    #
    #     self.parameters[self.api_obj_mapping[ref]] = val



    def set_parameter_in_model(self, var_name: str, new_value: float):
        """
        updates parameter value given a name and a value

        :param var_name:
        :param new_value:
        :return:
        """

        set_parameter(self, var_name, new_value)
        if self.children:
            for child in self.children:
                child.set_parameter_in_model(var_name, new_value)


    def check_empty(self) -> bool:
        """
        check if a block is an empty block
        :return:
        :rtype: bool
        """
        return (
                not self.state_vars and
                not self.state_eqs and
                not self.algebraic_vars and
                not self.algebraic_eqs and
                not self.inequalities and
                not self.diff_vars and
                not self.reformulated_vars and
                not self.differential_eqs and
                not self.parameters and
                not self.init_values and
                not self.init_eqs and
                not self.diff_init_eqs and
                not self.children and
                not self.in_vars and
                not self.out_vars and
                not self.event_dict and
                not self.mode_dict and
                not self.boolean_guards and
                not self.procedural_logic and
                not self.external_mapping and
                not self.api_obj_mapping and
                not self.name
        )

    def empty(self) -> bool:
        """
        check if a model is empty
        :return:
        """
        if not self.children:
            empty = self.check_empty()
            if empty:
                return empty
        else:
            empty = self.check_empty()
            if not empty:
                return empty

            for child in self.children:
                child.empty()

        return False

    def E(self, d: VarPowerFlowReferenceType) -> Var:
        """

        returns the value of the external mapping corresponding to the VarPowerFlowReferenceType

        :param d:
        :return:
        """
        return self.external_mapping[d]

    def V(self, d: str) -> Var:
        """

        :param d:
        :return:
        """
        return self.var_mapping[d]

    def add(self, val: Block):
        """
        Add another block to children of the model
        :param val: Block
        """
        self.children.append(val)

    def remove(self, val: Block):
        """
        Remove a block from block children
        :param val: Block
        """
        self.children.remove(val)

    def check_valid_init_method(self):

        explicit = True
        for lst in [self.state_vars, self.algebraic_vars]:
            for var in lst:
                if self.init_eqs[var] is None:
                    explicit = False
                # if self.init_values[var] is None:
                #     self.init_values[var] = Const(0)
        return explicit


    def get_all_blocks(self) -> List[Block]:
        """
        Depth-first collection of all *primitive* Blocks.
        """

        flat: List[Block] = [self]
        for el in self.children:
            flat.extend(el.get_all_blocks())

        return flat

    def merge_incoming_block(self, block: Block):
        block.unify_blocks()
        self.algebraic_vars.extend(block.algebraic_vars)
        self.algebraic_eqs.extend(block.algebraic_eqs)
        self.inequalities.extend(block.inequalities)
        self.state_vars.extend(block.state_vars)
        self.state_eqs.extend(block.state_eqs)
        self.diff_vars.extend(block.diff_vars)
        self.reformulated_vars.extend(block.reformulated_vars)
        self.external_mapping.update(block.external_mapping)
        for event_param, eq in block.event_dict.items():
            self.event_dict[event_param] = eq

        for mode_param, eq in block.mode_dict.items():
            self.mode_dict[mode_param] = eq

        for bool_var, guard in block.boolean_guards.items():
            self.boolean_guards[bool_var] = guard

        for param, const in block.parameters.items():
            self.parameters[param] = const

        for var, init_eq in block.init_eqs.items():
            self.init_eqs[var] = init_eq

        for diffvar, diff_init_eq in block.diff_init_eqs.items():
            self.diff_init_eqs[diffvar] = diff_init_eq


    def unify_blocks(self):
        """
        This function collects all variables and equations of a block, returns a flat block
        Returns
        -------
        Union[None, VeraGridEngine.Utils.Symbolic.block.Block]
        """
        mdl_placeholder = Block()
        list_blocks = self.get_all_blocks()
        for b in self.get_all_blocks():
            mdl_placeholder.algebraic_vars.extend(b.algebraic_vars)
            mdl_placeholder.algebraic_eqs.extend(b.algebraic_eqs)
            mdl_placeholder.inequalities.extend(b.inequalities)
            mdl_placeholder.state_vars.extend(b.state_vars)
            mdl_placeholder.state_eqs.extend(b.state_eqs)
            mdl_placeholder.diff_vars.extend(b.diff_vars)
            mdl_placeholder.differential_eqs.extend(b.differential_eqs)
            mdl_placeholder.reformulated_vars.extend(b.reformulated_vars)
            mdl_placeholder.external_mapping.update(b.external_mapping)
            mdl_placeholder.api_obj_mapping.update(b.api_obj_mapping)
            for event_param, eq in b.event_dict.items():
                mdl_placeholder.event_dict[event_param] = eq

            for mode_param, eq in b.mode_dict.items():
                mdl_placeholder.mode_dict[mode_param] = eq

            for bool_var, guard in b.boolean_guards.items():
                mdl_placeholder.boolean_guards[bool_var] = guard

            for param, const in b.parameters.items():
                mdl_placeholder.parameters[param] = const

            for var, init_eq in b.init_eqs.items():
                mdl_placeholder.init_eqs[var] = init_eq

            for var, init_val in b.init_values.items():
                mdl_placeholder.init_values[var] = init_val

            for diffvar, diff_init_eq in b.diff_init_eqs.items():
                mdl_placeholder.diff_init_eqs[diffvar] = diff_init_eq

            mdl_placeholder.procedural_logic.extend(b.procedural_logic)

        self.algebraic_vars = mdl_placeholder.algebraic_vars
        self.algebraic_eqs = mdl_placeholder.algebraic_eqs
        self.inequalities = mdl_placeholder.inequalities
        self.state_vars = mdl_placeholder.state_vars
        self.state_eqs = mdl_placeholder.state_eqs
        self.diff_vars = mdl_placeholder.diff_vars
        self.differential_eqs = mdl_placeholder.differential_eqs
        self.event_dict = mdl_placeholder.event_dict
        self.mode_dict = mdl_placeholder.mode_dict
        self.boolean_guards = mdl_placeholder.boolean_guards
        self.parameters = mdl_placeholder.parameters
        self.init_eqs = mdl_placeholder.init_eqs
        self.diff_init_eqs = mdl_placeholder.diff_init_eqs
        self.reformulated_vars = mdl_placeholder.reformulated_vars
        self.external_mapping = mdl_placeholder.external_mapping
        self.api_obj_mapping = mdl_placeholder.api_obj_mapping
        self.procedural_logic = mdl_placeholder.procedural_logic
        self.children = list()

    def get_vars(self) -> List[Var]:
        """
        returns variables of the flat block
        :return: List[Var]
        """
        vars_list = list()
        variables_lists = [self.algebraic_vars, self.state_vars, self.diff_vars]
        for lst in variables_lists:
            for var in lst:
                vars_list.append(var)

        return vars_list

    def get_all_vars(self):
        """
        returns all the variables of a block
        :return:
        """
        variables: List[Var] = list()
        all_blocks = self.get_all_blocks()
        for blk in all_blocks:
            variables.extend(blk.algebraic_vars)
            variables.extend(blk.state_vars)
            variables.extend(blk.diff_vars)
        return variables

    def update_variables(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        this function changes the variable old for the variable new in the block variables
        :param old:
        :type old:
        :param new:
        :type new:
        :return:
        :rtype:
        """

        for lst in [self.state_vars, self.algebraic_vars, self.diff_vars]:
            for i, var in enumerate(lst):
                if var.uid == old.uid:
                    lst[i]=new




    def update_equations(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        this function changes the variable old for the variable new in the block equations
        :param old:
        :param new:
        :return:
        """
        init_eqs_new = dict()
        diff_init_eqs_new = dict()
        event_dict_new = dict()
        mode_dict_new = dict()
        boolean_guards_new = dict()

        for i, eq in enumerate(self.algebraic_eqs):
            new_equ = eq.subs({old: new})
            self.algebraic_eqs[i] = new_equ
        for i, eq in enumerate(self.inequalities):
            new_equ = eq.subs({old: new})
            self.inequalities[i] = new_equ
        for i, eq in enumerate(self.state_eqs):
            new_equ = eq.subs({old: new})
            self.state_eqs[i] = new_equ
        for i, eq in enumerate(self.differential_eqs):
            new_equ = eq.subs({old: new})
            self.differential_eqs[i] = new_equ
        for var, expr in self.init_eqs.items():
            new_expr = expr.subs({old: new})
            if var is old:
                init_eqs_new.update({new: new_expr})
            else:
                init_eqs_new.update({var: new_expr})

        self.init_eqs = init_eqs_new

        for var, expr in self.diff_init_eqs.items():
            new_expr = expr.subs({old: new})
            if var is old:
                diff_init_eqs_new.update({new: new_expr})
            else:
                diff_init_eqs_new.update({var: new_expr})

        self.diff_init_eqs = diff_init_eqs_new

        for var, expr in self.event_dict.items():
            new_expr = expr.subs({old: new})
            if var is old:
                event_dict_new.update({new: new_expr})
            else:
                event_dict_new.update({var: new_expr})

        self.event_dict = event_dict_new

        for var, expr in self.mode_dict.items():
            new_expr = expr.subs({old: new})
            if var is old:
                mode_dict_new.update({new: new_expr})
            else:
                mode_dict_new.update({var: new_expr})
        self.mode_dict = mode_dict_new

        for var, expr in self.boolean_guards.items():
            new_expr = expr.subs({old: new})
            if var is old:
                boolean_guards_new.update({new: new_expr})
            else:
                boolean_guards_new.update({var: new_expr})
        self.boolean_guards = boolean_guards_new

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is old:
                self.external_mapping.update({var_pf_ref: new})

        if self.procedural_logic:
            from VeraGridEngine.Utils.procedural_logic import clone_procedural_logic_entries
            self.procedural_logic = clone_procedural_logic_entries(self.procedural_logic,
                                                                   var_mapping={old: new, old.name: new})

    def update_model(self, old: Var | Expr, new: Var | Expr) -> None:
        """
        Replace variables
        :param old:
        :param new:
        :return:
        """
        self.update_equations(old, new)
        self.update_variables(old, new)
        if self.children:
            for child in self.children:
                child.update_model(old, new)

    def update_variables_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables in the block variable lists in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        uid_mapping: Dict[int, Var] = dict((old_var.uid, new_var) for old_var, new_var in var_mapping.items())
        lst: List[Var]
        i: int
        var: Var

        for lst in [self.state_vars, self.algebraic_vars, self.diff_vars]:
            for i, var in enumerate(lst):
                if var.uid in uid_mapping:
                    lst[i] = uid_mapping[var.uid]
                else:
                    pass

    def update_equations_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables in block equations and mappings in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        uid_mapping: Dict[int, Var] = dict((old_var.uid, new_var) for old_var, new_var in var_mapping.items())
        init_eqs_new: Dict[Var, Expr] = dict()
        diff_init_eqs_new: Dict[Var, Expr] = dict()
        event_dict_new: Dict[Var, Expr] = dict()
        mode_dict_new: Dict[Var, Expr] = dict()
        boolean_guards_new: Dict[Var, Expr | Comparison] = dict()
        external_mapping_new: Dict[VarPowerFlowReferenceType, Var | None] = dict()
        procedural_var_mapping: Dict[Expr | str, Expr] = dict()
        i: int
        eq: Expr
        var: Var
        expr: Expr
        new_var: Var | None
        var_pf_ref: VarPowerFlowReferenceType
        mdl_var: Var | None

        for old_var, replacement_var in var_mapping.items():
            procedural_var_mapping[old_var] = replacement_var
            procedural_var_mapping[old_var.name] = replacement_var

        for i, eq in enumerate(self.algebraic_eqs):
            self.algebraic_eqs[i] = eq.subs(var_mapping)
        for i, eq in enumerate(self.inequalities):
            self.inequalities[i] = eq.subs(var_mapping)
        for i, eq in enumerate(self.state_eqs):
            self.state_eqs[i] = eq.subs(var_mapping)
        for i, eq in enumerate(self.differential_eqs):
            self.differential_eqs[i] = eq.subs(var_mapping)

        for var, expr in self.init_eqs.items():
            new_var = uid_mapping.get(var.uid, None)
            init_eqs_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.init_eqs = init_eqs_new

        for var, expr in self.diff_init_eqs.items():
            new_var = uid_mapping.get(var.uid, None)
            diff_init_eqs_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.diff_init_eqs = diff_init_eqs_new

        for var, expr in self.event_dict.items():
            new_var = uid_mapping.get(var.uid, None)
            event_dict_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.event_dict = event_dict_new

        for var, expr in self.mode_dict.items():
            new_var = uid_mapping.get(var.uid, None)
            mode_dict_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.mode_dict = mode_dict_new

        for var, expr in self.boolean_guards.items():
            new_var = uid_mapping.get(var.uid, None)
            boolean_guards_new[var if new_var is None else new_var] = expr.subs(var_mapping)
        self.boolean_guards = boolean_guards_new

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is None:
                external_mapping_new[var_pf_ref] = None
            elif mdl_var.uid in uid_mapping:
                external_mapping_new[var_pf_ref] = uid_mapping[mdl_var.uid]
            else:
                external_mapping_new[var_pf_ref] = mdl_var
        self.external_mapping = external_mapping_new

        if self.procedural_logic:
            from VeraGridEngine.Utils.procedural_logic import clone_procedural_logic_entries
            self.procedural_logic = clone_procedural_logic_entries(
                self.procedural_logic,
                var_mapping=procedural_var_mapping,
            )
        else:
            pass

    def update_model_bulk(self, var_mapping: Dict[Var, Var]) -> None:
        """
        Replace several variables across the block hierarchy in one pass.

        :param var_mapping: Old-to-new variable mapping.
        :return: None.
        """
        self.update_equations_bulk(var_mapping)
        self.update_variables_bulk(var_mapping)
        if self.children:
            for child in self.children:
                child.update_model_bulk(var_mapping)
        else:
            pass

    def can_use_bulk_connect_update(self, pairs: List[Tuple[Var, Var]]) -> bool:
        """
        Return whether one connection batch can be substituted safely in one pass.

        Bulk substitution is used only when the old and new variable sets are
        both unique and disjoint. If the mappings overlap, the original
        sequential behaviour is preserved because the substitution order can be
        semantically relevant.

        :param pairs: Connection pairs ``(old_var, new_var)``.
        :return: ``True`` when the fast bulk path is safe.
        """
        old_uids: List[int] = list()
        new_uids: List[int] = list()
        var_to_subs: Var
        incoming_var: Var

        if len(pairs) <= 1:
            return False
        else:
            pass

        for var_to_subs, incoming_var in pairs:
            old_uids.append(var_to_subs.uid)
            new_uids.append(incoming_var.uid)

        if len(set(old_uids)) != len(pairs) or len(set(new_uids)) != len(pairs):
            return False
        else:
            pass

        if len(set(old_uids).intersection(set(new_uids))) > 0:
            return False
        else:
            return True

    def connect(self, vars_to_subs: List[Var], incoming_vars: List[Var]):
        """
        Function to connect two blocks by variables sharing
        """
        # here we just change uid and name of the vars_to_subs
        pairs: List[Tuple[Var, Var]] = list(zip(vars_to_subs, incoming_vars))
        can_use_bulk_update: bool = self.can_use_bulk_connect_update(pairs)
        var_to_subs: Var
        incoming_var: Var

        # if can_use_bulk_update:
        #     self.update_model_bulk(dict(pairs))
        # else:
        for var_to_subs, incoming_var in pairs:
            self.update_model(var_to_subs, incoming_var)
            # var_to_subs.uid = incoming_var.uid
            # var_to_subs.name = incoming_var.name

    def find_var_in_equations(self,var: Var) -> bool:
        """
        find a var in the equations of a block
        :param var:
        :return:
        """

        for i, eq in enumerate(self.algebraic_eqs):
            if eq.contains_var:
                return True

        for i, eq in enumerate(self.state_eqs):
            if eq.contains_var:
                return True

        for i, eq in enumerate(self.differential_eqs):
            if eq.contains_var:
                return True

        for var, eq in self.init_eqs.items():
            if eq.contains_var:
                return True

        for var, eq in self.diff_init_eqs.items():
            if eq.contains_var:
                return True

        for var, eq in self.event_dict.items():
            if eq.contains_var:
                return True

        for var, eq in self.mode_dict.items():
            if eq.contains_var:
                return True

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is var:
               return True

        return False

        # add procedural logic here

    def find_var_in_block(self, var: Var) -> bool:
        """
        Replace variables
        :param var:
        :return:
        """
        if self.find_var_in_equations(var):
            return True
        if self.children:
            for child in self.children:
                if child.find_var_in_block(var):
                    return True

        return False

    def is_eq_decomposable(self) -> bool:

        if self.children:
            return False
        if not (bool(self.algebraic_eqs) or bool(self.state_eqs)):
            return False
        if not self.is_decomposable:
            return False
        return True

def find_connections(mdl1: Block, mdl2: Block) -> tuple[List[tuple[Var, Var]], List[tuple[Var, Var]]]:
    """
    find connections between the two blocks by vars searching
    :return:
    :rtype:
    """

    # connect inputs mdl2 with outputs mdl1
    pairs = [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        outp.shared_ref == inpt.shared_ref and outp.shared_ref is not None and inpt.shared_ref is not None and outp.uid == inpt.uid
    ]

    power_flow_pairs =  [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        outp.ref == inpt.ref and outp.ref is not None and inpt.ref is not None and outp.uid == inpt.uid
    ]


    return pairs, power_flow_pairs

def find_connections_pf(mdl1: Block, mdl2: Block) -> List[tuple[Var, Var]]:
    """
    find connections between the two blocks by vars searching
    :return:
    :rtype:
    """

    power_flow_pairs =  [
        (outp, inpt)
        for outp in mdl1.out_vars
        for inpt in mdl2.in_vars
        if
        outp.ref == inpt.ref and outp.ref is not None and inpt.ref is not None and outp.uid == inpt.uid
    ]


    return power_flow_pairs

def find_name_in_block(name: str, block: Block) -> Var | None:
    """

    :param name:
    :param block:
    :return:
    """
    for lst in [block.in_vars, block.out_vars, block.algebraic_vars, block.state_vars, block.diff_vars]:
        for var in lst:
            if name == var.name:
                return var

    for block_child in block.children:
        result = find_name_in_block(name, block_child)
        if result is not None:  # found in a child
            return result

    return None


def build_name_to_var_lookup(block: Block) -> Dict[str, Var]:
    """
    Build one variable lookup table by symbolic name for a block hierarchy.

    The first occurrence of each name is preserved, matching the effective
    search order of ``find_name_in_block()`` while avoiding repeated recursive
    scans when many variables must be resolved from the same block.

    :param block: Root block to inspect.
    :return: Name-to-variable lookup.
    """
    lookup: Dict[str, Var] = dict()
    var_lists: List[List[Var]] = list([
        block.in_vars,
        block.out_vars,
        block.algebraic_vars,
        block.state_vars,
        block.diff_vars,
    ])
    var_list: List[Var]
    var_obj: Var
    child_block: Block
    child_lookup: Dict[str, Var]

    for var_list in var_lists:
        for var_obj in var_list:
            if var_obj.name in lookup:
                pass
            else:
                lookup[var_obj.name] = var_obj

    for var_obj in block.event_dict.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for var_obj in block.mode_dict.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for var_obj in block.boolean_guards.keys():
        if var_obj.name in lookup:
            pass
        else:
            lookup[var_obj.name] = var_obj

    for child_block in block.children:
        child_lookup = build_name_to_var_lookup(child_block)
        for child_name, child_var in child_lookup.items():
            if child_name in lookup:
                pass
            else:
                lookup[child_name] = child_var

    return lookup

def _get_var_attribute_mapping(block: Block) -> Dict[int, str]:
    """Build a mapping from variable uid to attribute name for a block."""
    mapping = {}
    for var in block.state_vars:
        mapping[var.uid] = "state_vars"
    for var in block.algebraic_vars:
        mapping[var.uid] = "algebraic_vars"
    for var in block.diff_vars:
        mapping[var.uid] = "diff_vars"
    for var in block.reformulated_vars:
        mapping[var.uid] = "reformulated_vars"
    for var in block.parameters:
        mapping[var.uid] = "parameters"
    for var in block.event_dict:
        mapping[var.uid] = "event_dict"
    for var in block.in_vars:
        mapping[var.uid] = "in_vars"
    return mapping

def variables_in_corresponding_attributes(blocks: List[Block], variables_mappings: List[Dict[int, int]]) -> bool:
    """
    Check if corresponding variables are located in corresponding attributes of n blocks.

    For each pair (blocks[i], blocks[j]) with variables_mappings[k] (where k corresponds to the pair),
    and for every pair (uid1, uid2) in variables_mapping:
    - If the variable with uid1 is in blocks[i].state_vars, the variable with uid2 must be in blocks[j].state_vars
    - And so on for all attribute types

    The order of variables within each attribute does not matter.

    :param blocks: List of n blocks to check
    :param variables_mappings: List of Dict mappings from block i to block j for each pair comparison
    :return: True if all corresponding variables are in corresponding attributes for all pairs
    """
    if len(blocks) < 2:
        return True

    attr_maps = [_get_var_attribute_mapping(block) for block in blocks]

    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            mapping_idx = sum(range(len(blocks) - 1, len(blocks) - 1 - (j - i), -1)) + (j - i - 1)
            if mapping_idx >= len(variables_mappings):
                continue
            variables_mapping = variables_mappings[mapping_idx]

            attr_map_i = attr_maps[i]
            attr_map_j = attr_maps[j]

            for uid_i, uid_j in variables_mapping.items():
                attr_i = attr_map_i.get(uid_i)
                attr_j = attr_map_j.get(uid_j)
                if attr_i != attr_j:
                    return False

    return True

def _get_pair_index(i: int, j: int, n: int) -> int:
    """Get the index in variables_mappings list for the pair (i, j)."""
    idx = 0
    for x in range(n):
        for y in range(x + 1, n):
            if x == i and y == j:
                return idx
            idx += 1
    return -1

def compare_n_blocks_structurally(blocks: List[Block]) -> Tuple[Dict[int, List[int]], Dict[int, List[int]]]:
    """
    Compare n blocks structurally and group equivalent blocks by their uid.

    Two blocks are considered structurally equivalent if:
    1. Their unified equation systems are equivalent
    2. Variables can be aligned between them
    3. Corresponding variables are located in corresponding attributes

    :param blocks: List of n blocks to compare
    :return: Tuple of:
        - Dict with new uid (uuid.uuid4().int) as keys and lists of equivalent block uids as values
        - Dict with variable uid as keys and lists of equivalent variable uids as values
    """
    if len(blocks) == 0:
        return {}, {}

    if len(blocks) == 1:
        return {blocks[0].uid: []}, {}

    n = len(blocks)
    equivalence_classes = []
    equivalence_alignments = []
    processed = [False] * n

    for i in range(n):
        if not processed[i]:
            current_group = [blocks[i].uid]
            processed[i] = True
            current_alignments = {}

            for j in range(i + 1, n):
                if not processed[j]:

                    block_i_copy = blocks[i].copy()
                    block_i_copy.unify_blocks()
                    block_j_copy = blocks[j].copy()
                    block_j_copy.unify_blocks()

                    block_i_eqs = block_i_copy.get_all_equations_list()
                    block_j_eqs = block_j_copy.get_all_equations_list()

                    if equivalent_systems(block_i_eqs, block_j_eqs):

                        variables_alignment = align_variables(block_i_eqs, block_j_eqs)
                        if variables_alignment:

                            variables_mappings = [variables_alignment]
                            if variables_in_corresponding_attributes([block_i_copy, block_j_copy], variables_mappings):

                                current_group.append(blocks[j].uid)
                                processed[j] = True
                                current_alignments[j] = variables_alignment

            equivalence_classes.append(current_group)
            equivalence_alignments.append((i, current_alignments))

    model_result = {}
    for eq_class in equivalence_classes:
        model_result[eq_class[0]] = eq_class[1:]

    var_result = {}
    for ref_idx, alignments in equivalence_alignments:
        if not alignments:
            continue
        first_alignment = next(iter(alignments.values()))
        for ref_var_uid in first_alignment:
            equivalent_uids = []
            for alignment in alignments.values():
                equivalent_uids.append(alignment[ref_var_uid])
            var_result[ref_var_uid] = equivalent_uids

    return model_result, var_result
#
# def compare_n_blocks_structurally(blocks: List[Block]) -> Dict[int, List[int]]:
#     """
#     Compare n blocks structurally and group equivalent blocks by their uid.
#
#     Two blocks are considered structurally equivalent if:
#     1. Their unified equation systems are equivalent
#     2. Variables can be aligned between them
#     3. Corresponding variables are located in corresponding attributes
#
#     :param blocks: List of n blocks to compare
#     :return: Dict with new uid (uuid.uuid4().int) as keys and lists of equivalent block uids as values
#     """
#     if len(blocks) == 0:
#         return {}
#
#     if len(blocks) == 1:
#         new_uid = _new_uid()
#         return {new_uid: [blocks[0].uid]}
#
#     n = len(blocks)
#     equivalence_classes = []
#     processed = [False] * n
#
#     for i in range(n):
#         if processed[i]:
#             continue
#
#         current_group = [blocks[i].uid]
#         processed[i] = True
#
#         for j in range(i + 1, n):
#             if processed[j]:
#                 continue
#
#             block_i_copy = blocks[i].copy()
#             block_i_copy.unify_blocks()
#             block_j_copy = blocks[j].copy()
#             block_j_copy.unify_blocks()
#
#             block_i_eqs = block_i_copy.get_all_equations_list()
#             block_j_eqs = block_j_copy.get_all_equations_list()
#
#             if not equivalent_systems(block_i_eqs, block_j_eqs):
#                 continue
#
#             variables_alignment = align_variables(block_i_eqs, block_j_eqs)
#             if not variables_alignment:
#                 continue
#
#             variables_mappings = [variables_alignment]
#             if not variables_in_corresponding_attributes([block_i_copy, block_j_copy], variables_mappings):
#                 continue
#
#             current_group.append(blocks[j].uid)
#             processed[j] = True
#
#         equivalence_classes.append(current_group)
#
#     result = {}
#     for eq_class in equivalence_classes:
#         new_uid = _new_uid()
#         result[new_uid] = eq_class
#
#     return result

def compare_blocks_structurally(block1: Block, block2: Block) -> bool:
    block1_compare = block1.copy().unify_blocks()
    block2_compare = block2.copy().unify_blocks()

    block1_eqs = block1.get_all_equations_list()
    block2_eqs = block2.get_all_equations_list()

    if equivalent_systems(block1_eqs, block2_eqs):
        variables_alignment = align_variables(block1_eqs, block2_eqs)
        if variables_in_corresponding_attributes([block1_compare, block2_compare], [variables_alignment]):
            print("blocks are equivalent")
            return True
    return False

    return True