# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import uuid
from typing import List, Dict
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, Expr, _expr_to_dict, _dict_to_expr
from VeraGridEngine.enumerations import VarPowerFlowRefferenceType, ParamPowerFlowRefferenceType


def _new_uid() -> int:
    """
    Generate a fresh UUID‑v4 string.
    :return: UUIDv4 in integer format
    """
    return uuid.uuid4().int



class Block:
    """
    Class representing a Block
    """

    def __init__(self,
                 state_vars: List[Var] | None = None,
                 state_eqs: List[Expr] | None = None,
                 algebraic_vars: List[Var] | None = None,
                 algebraic_eqs: List[Expr] | None = None,
                 diff_vars: List[Var] | None = None,
                 reformulated_vars: List[Var] | None = None,
                 differential_eqs: List[Expr] | None = None,
                 parameters: Dict[Var, Const] | None = None,
                 alter_params: List[Var] | None = None,
                 init_values: Dict[Var, Const] | None = None,
                 init_eqs: Dict[Var, Expr] | None = None,
                 diff_init_eqs: Dict[Var, Expr] | None = None,
                 discrete_eqs: Dict[Var, Expr] | None = None,
                 children: List["Block"] | None = None,
                 in_vars: List[Var] | None = None,
                 out_vars: List[Var] | None = None,
                 event_dict: Dict[Var, Expr] | None = None,
                 external_mapping: Dict[VarPowerFlowRefferenceType, Var] | None = None,
                 api_obj_mapping: Dict[ParamPowerFlowRefferenceType, Var] | None = None,
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
        :param external_mapping: Dictionary of vars that are related to the Power flow initialization
        :param name: name of the block
        """

        self.name: str = name

        self.uid: int = _new_uid() if uid is None else uid
        self.vars_glob_name2uid: Dict[str, int] = dict()

        self.state_vars: List[Var] = list() if state_vars is None else state_vars
        self.state_eqs: List[Expr] = list() if state_eqs is None else state_eqs

        self.algebraic_vars: List[Var] = list() if algebraic_vars is None else algebraic_vars
        self.algebraic_eqs: List[Expr] = list() if algebraic_eqs is None else algebraic_eqs

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

        self.alter_params: List[Var] = list() if alter_params is None else alter_params
        self.discrete_eqs: Dict[Var, Expr] = dict() if discrete_eqs is None else discrete_eqs
        self.external_mapping: Dict[VarPowerFlowRefferenceType, Var|None] = (dict()
                                                                        if external_mapping is None
                                                                        else external_mapping)

        self.api_obj_mapping: Dict[ParamPowerFlowRefferenceType, Var] = (dict()
                                                                         if api_obj_mapping is None
                                                                         else api_obj_mapping)
        # initialization
        self.init_values: Dict[Var, Const] = dict() if init_values is None else init_values

        self.var_mapping = {v.name: v for v in self.algebraic_vars}

        # Dictionary of Variables and their Expressions that appear due to an event
        # this is the dictionary of "parameters" that may change and their equations
        self.event_dict: Dict[Var, Expr | Const] = dict() if event_dict is None else event_dict

    def to_dict(self) -> dict:
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
            "differential_eqs": [_expr_to_dict(e) for e in self.differential_eqs],


            "init_eqs": {
                str(k.uid): {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_eqs.items()
            },

            "diff_init_eqs": {
                str(k.uid): {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.diff_init_eqs.items()
            },

            "event_dict": {
                str(k.uid): {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.event_dict.items()
            },

            "parameters": {
                str(k.uid): {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.parameters.items()
            },

            "init_values": {
                str(k.uid): {
                    "key": _expr_to_dict(k),
                    "value": _expr_to_dict(v),
                }
                for k, v in self.init_values.items()
            },


            "external_mapping": {
                k: _expr_to_dict(v)
                for k, v in self.external_mapping.items()
            },

            "api_obj_mapping": {
                k: _expr_to_dict(v)
                for k, v in self.api_obj_mapping.items()
            },


            "children": [child.to_dict() for child in self.children]
        }

    @staticmethod
    def parse(data: dict) -> "Block":

        block = Block(
            name=data["name"],
            uid=data["uid"]
        )


        block.state_vars = [_dict_to_expr(v) for v in data["state_vars"]]
        block.algebraic_vars = [_dict_to_expr(v) for v in data["algebraic_vars"]]
        block.diff_vars = [_dict_to_expr(v) for v in data["diff_vars"]]
        block.reformulated_vars = [
            _dict_to_expr(v) for v in data["reformulated_vars"]
        ]

        block.in_vars = [_dict_to_expr(v) for v in data["in_vars"]]
        block.out_vars = [_dict_to_expr(v) for v in data["out_vars"]]


        block.state_eqs = [_dict_to_expr(e) for e in data["state_eqs"]]
        block.algebraic_eqs = [_dict_to_expr(e) for e in data["algebraic_eqs"]]
        block.differential_eqs = [
            _dict_to_expr(e) for e in data["differential_eqs"]
        ]


        block.init_eqs = {
            _dict_to_expr(item["key"]): _dict_to_expr(item["value"])
            for item in data["init_eqs"].values()
        }

        block.diff_init_eqs = {
            _dict_to_expr(item["key"]): _dict_to_expr(item["value"])
            for item in data["diff_init_eqs"].values()
        }

        block.event_dict = {
            _dict_to_expr(item["key"]): _dict_to_expr(item["value"])
            for item in data["event_dict"].values()
        }

        block.parameters = {
            _dict_to_expr(item["key"]): _dict_to_expr(item["value"])
            for item in data["parameters"].values()
        }

        block.init_values = {
            _dict_to_expr(item["key"]): _dict_to_expr(item["value"])
            for item in data["init_values"].values()
        }


        block.external_mapping = {
            k: _dict_to_expr(v)
            for k, v in data["external_mapping"].items()
        }

        block.api_obj_mapping = {
            k: _dict_to_expr(v)
            for k, v in data["api_obj_mapping"].items()
        }


        block.children = [
            Block.parse(child_data)
            for child_data in data["children"]
        ]

        return block

    def deep_copy(self) -> "Block":
        """
        Deep copy preserving UIDs.
        Completely structural clone using to_dict + parse.
        """
        return Block.parse(self.to_dict())

    def compare(self, block2: Block):
        dict1 = self.to_dict()
        dict2 = block2.to_dict()
        return dict1 == dict2


    def set_parameter_in_model(self, var_name: str, new_value: float):
        """
        updates parameter value given a name and a value

        :param var_name:
        :param new_value:
        :return:
        """
        found = 0

        for var, expr in self.event_dict.items():
            if var.name == var_name:
                if isinstance(expr, Const):
                    expr.value = new_value
                else:
                    self.event_dict[var] = Const(new_value)
                found += 1

        # check parameters dict
        for var, const in self.parameters.items():
            if var.name == var_name:
                if isinstance(const, Const):
                    const.value = new_value
                else:
                    self.parameters[var] = Const(new_value)
                found += 1
        if found == 0:
            raise ValueError(f"Parameter {var_name} not found in model")
        elif found >1:
            raise ValueError(f"Could not set value because several parameters with name {var_name} where found in the model")

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
                not self.diff_vars and
                not self.reformulated_vars and
                not self.differential_eqs and
                not self.parameters and
                not self.alter_params and
                not self.init_values and
                not self.init_eqs and
                not self.diff_init_eqs and
                not self.children and
                not self.in_vars and
                not self.out_vars and
                not self.event_dict and
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

    def E(self, d: VarPowerFlowRefferenceType) -> Var:
        """

        returns the value of the external mapping corresponding to the VarPowerFlowRefferenceType

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

    def get_all_blocks(self) -> List[Block]:
        """
        Depth-first collection of all *primitive* Blocks.
        """

        flat: List[Block] = [self]
        for el in self.children:
            flat.extend(el.get_all_blocks())

        return flat

    def unify_blocks(self):
        """
        This function collects all variables and equations of a block, returns a flat block
        Returns
        -------
        Union[None, VeraGridEngine.Utils.Symbolic.block.Block]
        """
        mdl_placeholder = Block()
        for b in self.get_all_blocks():
            mdl_placeholder.algebraic_vars.extend(b.algebraic_vars)
            mdl_placeholder.algebraic_eqs.extend(b.algebraic_eqs)
            mdl_placeholder.state_vars.extend(b.state_vars)
            mdl_placeholder.state_eqs.extend(b.state_eqs)
            mdl_placeholder.diff_vars.extend(b.diff_vars)
            mdl_placeholder.reformulated_vars.extend(b.reformulated_vars)
            mdl_placeholder.external_mapping.update(b.external_mapping)
            for event_param, eq in b.event_dict.items():
                mdl_placeholder.event_dict[event_param] = eq

            for param, const in b.parameters.items():
                mdl_placeholder.parameters[param] = const

            for var, init_eq in b.init_eqs.items():
                mdl_placeholder.init_eqs[var] = init_eq

            for diffvar, diff_init_eq in b.diff_init_eqs.items():
                mdl_placeholder.diff_init_eqs[diffvar] = diff_init_eq
        self.algebraic_vars = mdl_placeholder.algebraic_vars
        self.algebraic_eqs = mdl_placeholder.algebraic_eqs
        self.state_vars = mdl_placeholder.state_vars
        self.state_eqs = mdl_placeholder.state_eqs
        self.diff_vars = mdl_placeholder.diff_vars
        self.event_dict = mdl_placeholder.event_dict
        self.parameters = mdl_placeholder.parameters
        self.init_eqs = mdl_placeholder.init_eqs
        self.diff_init_eqs = mdl_placeholder.diff_init_eqs
        self.reformulated_vars = mdl_placeholder.reformulated_vars
        self.external_mapping = mdl_placeholder.external_mapping
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

    def  update_equations(self, old, new):
        """
        this function changes the variable old for the variable new in a block
        :param old:
        :param new:
        :return:
        """
        init_eqs_new = dict()
        diff_init_eqs_new = dict()
        event_dict_new = dict()

        for i, eq in enumerate(self.algebraic_eqs):
            new_equ = eq.subs({old: new})
            self.algebraic_eqs[i] = new_equ
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

        for var_pf_ref, mdl_var in self.external_mapping.items():
            if mdl_var is old:
                self.external_mapping.update({var_pf_ref: new})

    def update_model(self, old, new):
        """<
        :param old:
        :param new:
        :return:
        """
        self.update_equations(old, new)
        if self.children:
            for child in self.children:
                child.update_model(old, new)

    def connect(self, vars_to_subs: List[Var], incoming_vars: List[Var]):
        """
        Function to connect two blocks by variables sharing
        """



        for var_to_subs, incoming_var in zip(vars_to_subs, incoming_vars):
            self.update_model(var_to_subs, incoming_var)


def find_name_in_block(name: str, block: Block) -> Var | None:
    for lst in [block.algebraic_vars, block.state_vars]:
        for var in lst:
            if name == var.name:
                return var

    for block_child in block.children:
        result = find_name_in_block(name, block_child)
        if result is not None:  # found in a child
            return result

    return None




