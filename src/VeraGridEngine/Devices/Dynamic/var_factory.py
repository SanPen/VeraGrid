# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

from typing import Union, List, Dict, Any, Tuple
import uuid

from VeraGridEngine.Devices.Parents.editable_device import EditableDevice
from VeraGridEngine.enumerations import DeviceType, VarPowerFlowReferenceType
from VeraGridEngine.Utils.Symbolic.symbolic import Var, Const, SharedVarReferenceType


def _new_uid() -> int:
    """
    Generate one fresh integer uid.

    :return: New unique integer identifier.
    """
    return uuid.uuid4().int

class Connection:
    """
    Lightweight saved description of one propagated variable connection.
    """
    __slots__ = (
        'non_mutable_uid',
        'name',
        'uid'
    )
    def __init__(self,
                 non_mutable_uid: int,
                 name: str,
                 uid: int) -> None:
        """
        Store the identity required to restore one detached variable.

        :param non_mutable_uid: Stable uid of the connected variable.
        :param name: Variable name to restore after disconnection.
        :param uid: Mutable uid to restore after disconnection.
        :return: None.
        """

        # Preserve the stable symbolic identity used to match the connection
        # entry during later remove operations.
        self.non_mutable_uid = non_mutable_uid
        # Preserve the pre-connection variable name so the symbolic variable
        # returns to its original label when the edge is removed.
        self.name = name
        # Preserve the pre-connection uid so the symbolic variable returns to
        # the exact original identity when the edge is removed.
        self.uid = uid


class VarFactory(EditableDevice):
    """
    VarFactory
    """

    __slots__ = (
        '_var_dict',
        '_const_dict',
        '_diff_var_dict',
        '_vars_info',
        '_references_dict',
        '_vars_references_dict',
        '_vars_connected_dict',

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
        self._vars_info: Dict[Any, List[Var]] = dict()
        self._references_dict: Dict[str, SharedVarReferenceType] = dict()
        self._vars_references_dict: Dict[int, List[Var]] = dict()
        self._vars_connected_dict = dict()
        # self._vars_connected_dict: Dict[int, Dict[str, List[Var] | Dict[int, str] | Dict[int, int]]] = dict()

    @property
    def vars_info(self) -> Dict[Any, List[Var]]:
        return self._vars_info

    def get_vars_to_save(self,
                         dev:Any,
                         names: List[str]) -> List[Var]:
        """
        this function returns a list of variables which names are in names
        :param dev:
        :type dev:
        :param names:
        :type names:
        :return:
        :rtype:
        """
        return [v for v in self._vars_info[dev] if v.name in names]

    def add_var(self,
                name: str,
                reference: VarPowerFlowReferenceType | None = None,
                network_conn: bool = False,
                shared_reference: str | None | SharedVarReferenceType = None,
                non_mutable_uid: int | None = None,
                uid: int | None = None,

                diff_var: Var | None = None,
                base_var: Var | None = None) -> Var:
        """
        Adds a ver to the class
        :param name:
        :param shared_reference:
        :param reference:
        :param network_conn:
        :param non_mutable_uid:
        :param uid:
        :param diff_var:
        :param base_var:
        :return:
        """

        if isinstance(shared_reference, str):
            if shared_reference not in self._references_dict:
                self.create_reference(shared_reference)
                self._vars_references_dict[self._references_dict[shared_reference].uid] = list()

            v = Var(name=name, shared_reference=self._references_dict[shared_reference], reference=reference, network_conn=network_conn, non_mutable_uid=non_mutable_uid, uid=uid,
                    diff_var=None, base_var=None)
            self.save_var_in_vars_references_dict(v, shared_reference)
            self._var_dict[v.non_mutable_uid] = v
            return v
        else:
            v = Var(name=name, reference=reference, network_conn=network_conn, shared_reference=shared_reference, uid=uid,
                    diff_var=None, base_var=None)
            if shared_reference is not None:
                self.save_var_in_vars_references_dict(v, shared_reference.name)
            self._var_dict[v.non_mutable_uid] = v
            return v

    def add_shared_ref_to_var(self, v: Var, shared_reference: str | SharedVarReferenceType):

        if isinstance(shared_reference, str):
            if shared_reference not in self._references_dict:
                self.create_reference(shared_reference)
                self._vars_references_dict[self._references_dict[shared_reference].uid] = list()

            v.shared_ref = self._references_dict[shared_reference]
            self.save_var_in_vars_references_dict(v, shared_reference)

        else:
            v.shared_ref = shared_reference
            if shared_reference is not None:
                self.save_var_in_vars_references_dict(v, shared_reference.name)



    def save_var_in_vars_references_dict(self, var:Var, reference:str):
        self._vars_references_dict[self._references_dict[reference].uid].append(var)

    def create_reference(self, reference_name: str):
        self._references_dict[reference_name] = SharedVarReferenceType(name=reference_name)


    def get_var(self, uid: int) -> Var | None:
        """
        Gets a Var from the class
        :param uid:
        :return:
        """
        if uid is not None:
            return self._var_dict[uid]
        else:
            return None

    def add_diff_var(self,
                     name: str,
                     reference: VarPowerFlowReferenceType | None = None,
                     network_conn: bool = False,
                     shared_reference: str | None | SharedVarReferenceType = None,
                     non_mutable_uid: int | None = None,
                     uid: int | None = None,
                     diff_var: Var | None = None,
                     base_var: Var | None = None) -> Var:
        """
        Adds a Diff ver to the class
        :param name:
        :param shared_reference:
        :param non_mutable_uid:
        :param network_conn:
        :param uid:
        :param diff_var:
        :param base_var:
        :return:
        """
        if isinstance(shared_reference, str):
            if shared_reference not in self._references_dict:
                self.create_reference(shared_reference)
                self._vars_references_dict[self._references_dict[shared_reference].uid] = list()

            v = Var(name=name, shared_reference=self._references_dict[shared_reference], reference=reference, network_conn=network_conn, uid=uid, diff_var=diff_var, base_var=base_var)
            self.save_var_in_vars_references_dict(v, shared_reference)
            self._var_dict[v.non_mutable_uid] = v
            self._diff_var_dict[v.non_mutable_uid] = v
            return v
        else:
            v = Var(name=name, reference=reference, network_conn=network_conn, shared_reference=shared_reference, uid=uid, diff_var=diff_var, base_var=base_var)
            self._diff_var_dict[v.non_mutable_uid] = v
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

    def connect_variables_by_uid(self,
                                 var_to_subs_non_mutable_uid: int,
                                 incoming_var_uid: int,
                                 incoming_var_name: str,
                                 visited_non_mutable_uids: set[int] | None = None) -> None:
        """
        Propagate one incoming variable identity through the saved connection graph.

        The connection registry can contain cycles when editor-side EMT models
        reconnect root mapping vars that already alias back into the same live
        symbolic chain. Track visited stable uids during one propagation walk so
        the alias update remains finite even when the graph contains loops.

        :param var_to_subs_non_mutable_uid: Stable uid of the variable to rewrite.
        :param incoming_var_uid: Mutable uid that should be propagated.
        :param incoming_var_name: Variable name that should be propagated.
        :param visited_non_mutable_uids: Stable uids already processed in this walk.
        :return: None.
        """
        next_visited_non_mutable_uids: set[int]
        connection: Connection

        if visited_non_mutable_uids is None:
            next_visited_non_mutable_uids = set()
        else:
            next_visited_non_mutable_uids = visited_non_mutable_uids

        if var_to_subs_non_mutable_uid in next_visited_non_mutable_uids:
            return
        else:
            next_visited_non_mutable_uids.add(var_to_subs_non_mutable_uid)

        if var_to_subs_non_mutable_uid in self._var_dict:
            self._var_dict[var_to_subs_non_mutable_uid].uid = incoming_var_uid
            self._var_dict[var_to_subs_non_mutable_uid].name = incoming_var_name
        elif var_to_subs_non_mutable_uid in self._diff_var_dict:
            # Differential variables are stored in the dedicated diff-variable
            # registry. Updating the wrong dictionary leaves the propagated
            # symbolic identity stale and breaks later validation against the
            # live bus variables.
            self._diff_var_dict[var_to_subs_non_mutable_uid].uid = incoming_var_uid
            self._diff_var_dict[var_to_subs_non_mutable_uid].name = incoming_var_name
        else:
            pass

        # recursitity for previous connected vars
        if var_to_subs_non_mutable_uid in self._vars_connected_dict:
            for connection in self._vars_connected_dict[var_to_subs_non_mutable_uid]:
                self.connect_variables_by_uid(connection.non_mutable_uid,
                                              incoming_var_uid,
                                              incoming_var_name,
                                              next_visited_non_mutable_uids)
        else:
            pass

    def add_connection(self, var_to_subs: Var, incoming_var: Var):

        if not incoming_var.non_mutable_uid in self._vars_connected_dict:
            self._vars_connected_dict[incoming_var.non_mutable_uid] = list()

        connection = Connection(var_to_subs.non_mutable_uid, var_to_subs.name, var_to_subs.uid)
        self._vars_connected_dict[incoming_var.non_mutable_uid].append(connection)

        self.connect_variables_by_uid(connection.non_mutable_uid, incoming_var.uid, incoming_var.name)

    def remove_connection(self, var_to_disconnect: Var, outgoing_var: Var) -> None:
        """
        Remove one saved variable connection if it still exists.

        :param var_to_disconnect: Variable that should be detached from the outgoing source.
        :param outgoing_var: Source variable that owns the propagated connection list.
        :return: None.
        """
        connections: List[Connection] | None = self._vars_connected_dict.get(outgoing_var.non_mutable_uid, None)
        connection_index: int
        connection: Connection

        # The editor can request a connection removal after the backing
        # connection registry was already pruned by a previous editor action.
        # In that case there is nothing left to remove and the state is already
        # consistent, so the function must exit quietly.
        if connections is None:
            return
        else:
            pass

        for connection_index, connection in enumerate(connections):
            # Restore the disconnected variable identity before removing the
            # propagated connection record so downstream references stop using
            # the outgoing variable metadata.
            if connection.non_mutable_uid == var_to_disconnect.non_mutable_uid:
                self.connect_variables_by_uid(connection.non_mutable_uid, connection.uid, connection.name)
                del connections[connection_index]

                # Drop the now-empty registry entry to keep the connection map
                # aligned with the actual set of active propagated links.
                if len(connections) == 0:
                    del self._vars_connected_dict[outgoing_var.non_mutable_uid]
                else:
                    pass
                return
            else:
                pass

        # No matching propagated connection was present. The requested state is
        # therefore already reached and no extra action is necessary.
        return

    def add_connections(self, vars_to_subs: List[Var], incoming_vars: List[Var]):
        pairs: List[Tuple[Var, Var]] = list(zip(vars_to_subs, incoming_vars))
        var_to_subs: Var
        incoming_var: Var
        for var_to_subs, incoming_var in pairs:
            self.add_connection(var_to_subs, incoming_var)


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

    def get_references_dict(self) -> Dict[str, SharedVarReferenceType]:
        """

        :return:
        :rtype:
        """
        return self._references_dict

    def get_connections_dict(self) -> Dict[int, List[Connection]]:
        """

        :return:
        :rtype:
        """
        return self._vars_connected_dict

    def get_unique_template_name(self, name: str) -> str:
        """Return one template name that does not collide with existing symbols.

        Some EMT builders reserve their symbolic namespace at the template level
        before any variables are created. When the requested name is still free,
        this helper returns it unchanged. Otherwise it appends an integer suffix.

        :param name: Requested template name.
        :return: Collision-free template name.
        """
        existing_names = set(v.name for v in self._var_dict.values())
        existing_names.update(v.name for v in self._diff_var_dict.values())

        if name not in existing_names:
            return name
        else:
            index: int = 1
            candidate: str = f"{name}_{index}"

            while candidate in existing_names:
                index += 1
                candidate = f"{name}_{index}"

            return candidate

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
            data_tpe: Any = data.get("type", None)
            if data_tpe != "Var":
                continue
            else:
                pass

            # Older persisted symbolic models may not store the power-flow
            # reference field, so keep loading those files by defaulting to None.
            key_ref = None
            ref_data_dict: Any = data.get("shared_ref", None)
            if ref_data_dict is not None:
                ref_data_name = ref_data_dict.get("name", None)
                ref_data_uid = ref_data_dict.get("uid", None)
                key_ref: SharedVarReferenceType | None

                if ref_data_name is not None and ref_data_uid is not None:
                    if ref_data_name not in self._references_dict:
                        key_ref = SharedVarReferenceType(ref_data_name, ref_data_uid)
                        if key_ref is not None:
                            self._references_dict[ref_data_name] = key_ref
                    else:
                        key_ref = self._references_dict[ref_data_name]
                else:
                    key_ref = None

            ref_power_flow_data: Any = data.get("ref", None)
            key_power_flow_ref: VarPowerFlowReferenceType | None

            if ref_power_flow_data is not None:
                key_power_flow_ref = VarPowerFlowReferenceType(ref_power_flow_data)
            else:
                key_power_flow_ref = None

            # obj = Var(name=data["name"], uid=data["uid"], shared_reference=key_ref, reference=key_power_flow_ref, non_mutable_uid=data["non_mutable_uid"])
            obj_name: Any = data.get("name", "")
            obj_uid: Any = data.get("uid", None)
            obj_non_mutable_uid: Any = data.get("non_mutable_uid", None)

            # Legacy symbolic entries can miss one of the identity keys. Reuse
            # the surviving identifier so the rest of the dynamic block payload
            # can still be reconstructed.
            if obj_uid is None and obj_non_mutable_uid is None:
                continue
            else:
                pass

            if obj_uid is None:
                obj_uid = obj_non_mutable_uid
            else:
                pass

            if obj_non_mutable_uid is None:
                obj_non_mutable_uid = obj_uid
            else:
                pass

            obj = Var(name=obj_name, uid=obj_uid, shared_reference=key_ref, reference=key_power_flow_ref,
                      non_mutable_uid=obj_non_mutable_uid)
            if ref_data_dict is not None:
                ref_data_uid = ref_data_dict.get("uid", None)
                if ref_data_uid is not None:
                    if ref_data_uid in self._vars_references_dict:
                        self._vars_references_dict[ref_data_uid].append(obj)
                    else:
                        self._vars_references_dict[ref_data_uid] = list()
                        self._vars_references_dict[ref_data_uid].append(obj)

            # at this point we can store the object
            obj_dict[obj.non_mutable_uid] = obj

        self._var_dict = obj_dict

    def parse_diff_var_dict(self,
                            data_list: List[Dict[str, Any]]) -> None:
        """
        Parse persisted differential symbolic variables into the factory.

        The loader must rebuild each differential variable using the exact
        symbolic metadata stored in the ``.veragrid`` payload. In particular,
        the power-flow reference has to be converted back to the
        ``VarPowerFlowReferenceType`` enum so downstream EMT connection logic
        can distinguish branch terminal references such as ``vf_A`` and
        ``vt_A`` from bus references such as ``v_A``.

        :param data_list: Serialized differential variable records.
        :return: None.
        """
        obj_dict: Dict[int, Var | Const | Var] = dict()
        for data in data_list:
            data_tpe: Any = data.get("type", None)
            if data_tpe != "DiffVar":
                continue
            else:
                pass

            """
            lst.append({
                    "type": "DiffVar",
                    "name": expr.name,
                    "uid": expr.uid,
                    "base_var": _expr_to_dict(expr=expr.base_var, obj_dict=obj_dict),
                })
            """
            # Recover the base variable first because differential variables
            # are linked to the already reconstructed algebraic/differential
            # chain. This preserves the original derivative hierarchy.
            base_var_uid: Any = data.get("base_var", None)
            if base_var_uid in self._var_dict.keys():
                base_var = self._var_dict[base_var_uid]
            elif base_var_uid in self._diff_var_dict.keys():
                base_var = self._diff_var_dict[base_var_uid]
            elif base_var_uid in obj_dict.keys():
                base_var = obj_dict[base_var_uid]
            else:
                continue

            # Older persisted symbolic models may not store the power-flow
            # reference field on differential variables either.
            key_ref: SharedVarReferenceType | None = None
            ref_data_dict: Any = data.get("shared_ref", None)
            if ref_data_dict is not None:
                ref_data_name = ref_data_dict.get("name", None)
                ref_data_uid = ref_data_dict.get("uid", None)

                if ref_data_name is not None and ref_data_uid is not None:
                    if ref_data_name not in self._references_dict:
                        key_ref = SharedVarReferenceType(ref_data_name, ref_data_uid)
                        if key_ref is not None:
                            self._references_dict[ref_data_name] = key_ref
                        else:
                            pass
                    else:
                        key_ref = self._references_dict[ref_data_name]
                else:
                    key_ref = None
            else:
                pass

            # Convert the persisted textual reference back to the enum object.
            # Keeping the enum identity is required so EMT topology validation
            # can still recognize branch-side references after reopening files.
            reference_power_flow_data: Any = data.get("ref", None)
            reference_power_flow: VarPowerFlowReferenceType | None
            if reference_power_flow_data is not None:
                reference_power_flow = VarPowerFlowReferenceType(reference_power_flow_data)
            else:
                reference_power_flow = None

            obj_name: Any = data.get("name", "")
            obj_uid: Any = data.get("uid", None)
            if obj_uid is None:
                obj_uid = data.get("non_mutable_uid", None)
            else:
                pass

            if obj_uid is None:
                continue
            else:
                pass

            obj = Var(name=obj_name,
                      uid=obj_uid,
                      base_var=base_var,
                      shared_reference=key_ref,
                      reference=reference_power_flow)

            if ref_data_dict is not None:
                ref_data_uid = ref_data_dict.get("uid", None)
                if ref_data_uid is not None:
                    if ref_data_uid in self._vars_references_dict:
                        self._vars_references_dict[ref_data_uid].append(obj)
                    else:
                        self._vars_references_dict[ref_data_uid] = list()
                        self._vars_references_dict[ref_data_uid].append(obj)
                else:
                    pass
            else:
                pass

            # at this point we can store the object
            obj_dict[obj.non_mutable_uid] = obj

        self._diff_var_dict = obj_dict

   

    def parse_references_dict(self, datalist: List[Dict[str, Any]]):
        """
        Parse references list into _references_dict and _vars_references_dict.

        :param datalist: List of dicts with "type", "name", "uid" for share_reference.
        :return:
        """
        for data in datalist:
            if data["type"] == "share_reference":
                ref = SharedVarReferenceType(name=data["name"], uid=data["uid"])
                self._references_dict[data["name"]] = ref
                self._vars_references_dict[ref.uid] = list()

    def parse_connections_dict(self, datalist: Dict[int, List[Any]]) -> None:
        """
        Parse serialized connections and replay their runtime alias state.

        The saved connection table stores the graph that links one incoming
        variable to one or more substituted variables through their stable
        non-mutable identities. Rebuilding only the graph is not sufficient for
        the runtime symbolic system, because fresh GUI-created models also apply
        UID/name aliasing immediately when the connection is created. The load
        path must therefore reconstruct the graph first and then replay the same
        alias propagation so reopened symbolic models behave like newly created
        ones.

        :param datalist: List of dicts with block_uid -> list of connection dicts.
        :return: None.
        """
        uid_key: int
        connections_list: List[Any]
        conn_data: Any
        for uid, connections_list in datalist.items():
            uid_key = int(uid)

            if uid_key not in self._vars_connected_dict:
                self._vars_connected_dict[uid_key] = list()
            else:
                pass

            for conn_data in connections_list:
                conn_tpe: Any = conn_data.get("type", None)
                if conn_tpe == "Connection":
                    conn_non_mutable_uid: Any = conn_data.get("non_mutable_uid", None)
                    conn_name: Any = conn_data.get("name", "")
                    conn_uid: Any = conn_data.get("uid", None)
                    if conn_non_mutable_uid is None or conn_uid is None:
                        continue
                    else:
                        pass

                    conn: Connection = Connection(
                        non_mutable_uid=conn_non_mutable_uid,
                        name=conn_name,
                        uid=conn_uid
                    )
                    self._vars_connected_dict[uid_key].append(conn)
                else:
                    pass

        # Replay the alias propagation only after the full graph has been
        # reconstructed. This mirrors the live connection workflow while also
        # ensuring recursive downstream links can be traversed during replay.
        incoming_non_mutable_uid: int
        connection_list: List[Connection]
        connection: Connection
        for incoming_non_mutable_uid, connection_list in self._vars_connected_dict.items():
            if incoming_non_mutable_uid in self._var_dict:
                incoming_var: Var = self._var_dict[incoming_non_mutable_uid]
            elif incoming_non_mutable_uid in self._diff_var_dict:
                incoming_var = self._diff_var_dict[incoming_non_mutable_uid]
            else:
                incoming_var = None

            if incoming_var is not None:
                for connection in connection_list:
                    self.connect_variables_by_uid(
                        connection.non_mutable_uid,
                        incoming_var.uid,
                        incoming_var.name,
                    )
            else:
                pass

    def register_var(self, dev:Any, var:Var):

        """
        Associate a variable with a device
        :param dev: Device
        :param var: Variable
        """

        var_list = self._vars_info.get(dev, None)

        if var_list is None:
            self._vars_info[dev] = [var]
        else:
            var_list.append(var)

    def find_var_or_diff_var(self, var_uid: int | None):
        if var_uid in self.get_vars_dict():
            return self.get_var(var_uid)
        elif var_uid in self.get_diff_var_dict():
            return self.get_diff_var(var_uid)
        elif var_uid is None:
            return None
        else:
            raise ValueError(f"Var with uid:{var_uid} not added in VarFactory as var or diff_var.")
