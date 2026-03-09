# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, List, Dict, Any

from VeraGridEngine import VarPowerFlowRefferenceType
from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const


class VarFactory(EditableDevice):
    """
    VarFactory
    """

    __slots__ = (
        '_var_dict',
        '_const_dict',
        '_diff_var_dict'

    )

    def __init__(self,
                 idtag: Union[str, None] = "",
                 name: str = "Var Factory",
                 code: str = "",
                 comment: str = "") -> None:
        """
        VarFactory
        :param idtag: String. Element unique identifier
        :param name: String. Contingency name
        :param code: String. Contingency code name
        :param comment: Comment
        """

        EditableDevice.__init__(self,
                                idtag=idtag,
                                code=code,
                                name=name,
                                device_type=DeviceType.VarFactory,
                                comment=comment)

        self._var_dict: Dict[int, Var] = dict()
        self._const_dict: Dict[int, Const] = dict()
        self._diff_var_dict: Dict[int, Var] = dict()

    def add_var(self,
                name: str,
                ref: VarPowerFlowRefferenceType | None = None,
                uid: int | None = None) -> Var:
        """
        Adds a ver to the class
        :param name:
        :param ref:
        :param uid:
        :return:
        """
        v = Var(name=name, reference=ref, uid=uid, diff_var=None, base_var=None)
        self._var_dict[v.uid] = v
        return v

    def get_var(self, uid: int) -> Var:
        """
        Gets a Var from the class
        :param uid:
        :return:
        """
        return self._var_dict[uid]

    def add_diff_var(self,
                     name: str,
                     uid: int | None = None,
                     diff_var: Var | None = None,
                     base_var: Var | None = None) -> Var:
        """
        Adds a Diff ver to the class
        :param name:
        :param uid:
        :param diff_var:
        :param base_var:
        :return:
        """
        v = Var(name=name, uid=uid, diff_var=diff_var, base_var=base_var)
        self._diff_var_dict[v.uid] = v
        return v

    def get_diff_var(self, uid: int) -> Var:
        """
        Gets a Diff Var from the class
        :param uid:
        :return:
        """
        return self._diff_var_dict[uid]

    def add_const(self,
                  value: float | None = None,
                  uid: int | None = None,
                  name: str = "")-> Const:
        """
        Adds a Cont to the class
        :param value:
        :param uid:
        :param name:
        :return:
        """
        v = Const(value=value, uid=uid, name=name)
        self._const_dict[v.uid] = v
        return v

    def get_const(self, uid: int) -> Const:
        """
        Gets a Cont from the class
        :param uid:
        :return:
        """
        return self._const_dict[uid]

    def get_const_dict(self) -> Dict[int, Const]:
        """

        :return:
        """
        return self._const_dict

    def get_vars_dict(self) -> Dict[int, Var]:
        """

        :return:
        """
        return self._var_dict

    def get_diff_var_dict(self) -> Dict[int, Var]:
        """

        :return:
        """
        return self._diff_var_dict

    def parse_const_dict(self, data_list: List[Dict[str, Any]]):
        """

        :param data_list:
        :return:
        """
        obj_dict: Dict[int, Const] = dict()
        for data in data_list:

            t = data["type"]
            if t == "Const":
                if data.get("kind") == "complex":
                    arr = data["value"]
                    obj = Const(value=complex(arr[0], arr[1]),
                                uid=data["uid"])
                else:
                    obj = Const(value=data["value"],
                                uid=data["uid"])

            else:
                raise ValueError(f"Unhandled symbolic primitive {t}")

            # at this point we can store the object
            obj_dict[obj.uid] = obj

        self._const_dict = obj_dict

    def parse_var_dict(self, data_list: List[Dict[str, Any]]):
        """

        :param data_list:
        :return:
        """
        obj_dict: Dict[int, Var] = dict()
        for data in data_list:
            assert data["type"] == "Var"

            obj = Var(name=data["name"], uid=data["uid"])

            # at this point we can store the object
            obj_dict[obj.uid] = obj

        self._var_dict =  obj_dict

    def parse_diff_var_dict(self,
            data_list: List[Dict[str, Any]]):
        """

        :param data_list:
        :param var_dict: dictionary of vars
        :param diff_var_dict: dictionary of diffVars
        :return:
        """
        obj_dict: Dict[int, Var | Const | Var] = dict()
        for data in data_list:
            assert data["type"] == "DiffVar"

            """
            lst.append({
                    "type": "DiffVar",
                    "name": expr.name,
                    "uid": expr.uid,
                    "base_var": _expr_to_dict(expr=expr.base_var, obj_dict=obj_dict),
                })
            """
            if data["base_var"] in self._var_dict.keys():
                base_var = self._var_dict[data["base_var"]]
            elif data["base_var"] in self._diff_var_dict.keys():
                base_var = self._diff_var_dict[data["base_var"]]
            else:
                base_var = obj_dict[data["base_var"]]

            obj = Var(name=data["name"],
                      uid=data["uid"],
                      base_var=base_var)

            # at this point we can store the object
            obj_dict[obj.uid] = obj

        self._diff_var_dict = obj_dict
