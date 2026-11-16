# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import traceback

import numpy as np

import pandas as pd

# import pandapower
# import pypowsybl
# from pypowsybl import PyPowsyblError
# from pypowsybl.network import Network

from collections.abc import Sequence
from VeraGridEngine.basic_structures import Logger

IDENTIFIER_COLUMN_NAME = "uuid"
# empty_net = pandapower.create_empty_network()
EXPECTED_COLUMNS: dict[str, list[str]] = {}
logger = Logger()


def catch_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.add_warning(
                f"An unexpected exception occurred in function {func.__name__}: {e}",
            )

    return wrapper


def drop_irrelevant_columns(
        element_table: pd.DataFrame, element_type: str
) -> pd.DataFrame:
    if element_type not in EXPECTED_COLUMNS:
        # keep all columns if in doubt
        return element_table
    expected_columns = EXPECTED_COLUMNS[element_type]
    columns_to_keep = list(set(element_table.columns).intersection(expected_columns))
    return element_table.loc[:, columns_to_keep].reset_index(drop=True)


@catch_exceptions
def create_switches(
        pandapower_net: "pandapower.pandapowerNet", powsybl_net: "Network"
) -> None:
    """

    Parameters
    ----------
    pandapower_net
    powsybl_net

    Returns
    -------
    kind (DISCONNECTOR, BREAKER) --> type (CB, LBS, DS)
    open --> not closed
    retained
    voltage_level_id
    bus_breaker_bus1_id
    bus_breaker_bus2_id
    node1 --> bus
    node2 --> element + et
    fictitious

    missing:
    in_ka
    """
    switches = powsybl_net.get_switches(all_attributes=True)
    if switches.empty:
        # add identifier column
        pandapower_net["switch"] = pandapower_net["switch"].reindex(
            columns=[*pandapower_net["switch"].columns.tolist(), IDENTIFIER_COLUMN_NAME]
        )
        return

    set_index_as_column(switches)

    translation_switch_types = {
        "BREAKER": "CB",
        "DISCONNECTOR": "DS",
        "LOAD_BREAK_SWITCH": "LBS",
    }

    switches["closed"] = ~switches["open"].values
    switches["type"] = switches["kind"].map(
        lambda switch_type: translation_switch_types.get(switch_type, "")
    )
    switches["z_ohm"] = 0.001

    # assign_buses_and_elements_switches(pandapower_net, powsybl_net, switches)
    switches_with_assigned_buses = create_and_match_buses_for_switches(
        pandapower_net, powsybl_net
    )
    switches_without_connections = ~switches[IDENTIFIER_COLUMN_NAME].isin(
        switches_with_assigned_buses[IDENTIFIER_COLUMN_NAME]
    )

    # switches_without_connections = set(switches.index.values).difference(
    #     switches_with_assigned_buses[IDENTIFIER_COLUMN_NAME].values
    # )

    if len(switches_without_connections) > 0:
        print(f"For {len(switches_without_connections)} no connections were assigned.")
    switches = pd.merge(
        switches_with_assigned_buses,
        switches,
        how="inner",
        on=IDENTIFIER_COLUMN_NAME,
    )

    # if not switches.loc[:, ["bus_breaker_bus1_id", "bus_breaker_bus2_id"]].isna().all(axis=None):
    #     bus_breaker_mask = ~switches.loc[:, ["bus_breaker_bus1_id", "bus_breaker_bus2_id"]].isna().any(axis=1).values
    #     switches_bus_breaker = switches.loc[bus_breaker_mask, :]
    # ToDo: no powerflow results for switches in powsybl
    pandapower_net.switch = drop_irrelevant_columns(switches, "switch")


def create_and_match_buses_for_switches(pandapower_net, powsybl_net) -> pd.DataFrame:
    """

    Parameters
    ----------
    pandapower_net
    powsybl_net

    Returns
    -------

    pandapower only allows two types of switches: bus-bus switches and bus-element switches.
    In the first case, a switch is connected to two pandapower-buses, in the second case, a switch is connected to a
    pandapower-bus and an element from another pandapower-net-table. Only lines 2w-transformers and 3w-transformers are
    allowed as elements for a bus-element-switch.

    powsybl models switches differently:
    The connections between switches and elements are defined by nodes. Either switches share nodes with other switches
    or elements or they share a connection via another node.

    There are three cases:
    1. A switch shares a node with an element.
        a. In this case, if the element is a transformer or a line, the element-index
        will be referenced in the column 'element' of table switch and the element type in the column 'et'.
        b. If the element is not a transformer or a line, we need to create a new bus between the element and the
        switch.
        The index of this new bus will then be referenced in the column 'element' and the entry in column 'et' will
        be 'b'.
    2. Two switches share a node. In this case, we need to create a new bus between the switches. It will be referenced
    in either the 'bus'- or the 'element'-column.
    3. The nodes of two switches have an internal connection via another node. In this case, for each of these nodes not
    directly referenced by any switch, we create a new bus. The new bus will be referenced by the switches in either the
    'bus'- or the 'element'-column.

    """

    try:
        from pypowsybl import PyPowsyblError
    except ImportError:
        return

    new_columns = ["bus", "element", "et", IDENTIFIER_COLUMN_NAME]
    all_switches = pd.DataFrame(columns=new_columns)
    elements_connected_to_switches = pd.DataFrame(columns=["type", "bus_id", "side"])

    # check wether we have a node-breaker- or a bus-breaker-topology:
    voltage_levels = powsybl_net.get_voltage_levels().index.values
    node_breaker_topology = True
    if len(voltage_levels) > 0:
        try:
            _ = powsybl_net.get_node_breaker_topology(voltage_levels[0])
        except PyPowsyblError:
            node_breaker_topology = False

    for _, voltage_level in powsybl_net.get_voltage_levels().iterrows():
        if node_breaker_topology:
            all_switches = (
                create_and_match_buses_for_switches_per_voltage_level_node_breaker(
                    all_switches, pandapower_net, powsybl_net, voltage_level
                )
            )
        else:
            all_switches, elements_connected_to_switches = (
                create_and_match_buses_for_switches_per_voltage_level_bus_breaker(
                    all_switches,
                    elements_connected_to_switches,
                    pandapower_net,
                    powsybl_net,
                    voltage_level,
                )
            )
    if node_breaker_topology:
        connect_elements_to_switches_node_breaker(all_switches, pandapower_net)
    else:
        connect_elements_to_switches_bus_breaker(
            all_switches, elements_connected_to_switches, pandapower_net
        )

    # check validity of switches:
    for column in ["element", "bus"]:
        if all_switches.loc[:, column].isna().any():
            subset_with_nan_entries = all_switches.loc[
                all_switches.loc[:, column].isna()
            ]
            print(
                f"The following {subset_with_nan_entries.shape[0]} switches have a nan-entry in column"
                f" '{column}': {subset_with_nan_entries[IDENTIFIER_COLUMN_NAME].values}."
            )
        else:
            all_switches = all_switches.astype({column: int})

    return all_switches


def connect_elements_to_switches_bus_breaker(
        all_switches: pd.DataFrame,
        elements_connected_to_switches: pd.DataFrame,
        pandapower_net: "pandapower.pandapowerNet",
):
    # 1. map bus-breaker-ids to bus-indices
    bus_breaker_id_to_bus_index = {
        bus_id: bus_int
        for bus_int, bus_id in pandapower_net.bus[IDENTIFIER_COLUMN_NAME]
        .to_dict()
        .items()
    }

    elements_connected_to_switches["bus_int"] = elements_connected_to_switches[
        "bus_id"
    ].map(bus_breaker_id_to_bus_index)
    powsybl_table_name_to_pandapower_table_name = {
        "TWO_WINDINGS_TRANSFORMER": "trafo",
        "THREE_WINDINGS_TRANSFORMER": "trafo3w",
        "DANGLING_LINE": "line",
        "LINE": "line",
        "LOAD": "load",
        "SHUNT_COMPENSATOR": "shunt",
    }

    for powsybl_table_name in elements_connected_to_switches["type"].unique():
        if powsybl_table_name not in powsybl_table_name_to_pandapower_table_name:
            continue
        pandapower_table_name = powsybl_table_name_to_pandapower_table_name[
            powsybl_table_name
        ]

        if pandapower_table_name == "trafo":
            side_to_bus = {"ONE": "hv_bus", "TWO": "lv_bus"}
        elif pandapower_table_name == "trafo3w":
            side_to_bus = {"ONE": "hv_bus", "TWO": "mv_bus", "THREE": "lv_bus"}
        elif pandapower_table_name == "line":
            side_to_bus = {"ONE": "from_bus", "TWO": "to_bus"}
        else:
            side_to_bus = {"": "bus"}

        subset_of_elements = elements_connected_to_switches.query(
            "type==@powsybl_table_name"
        )
        if powsybl_table_name == "DANGLING_LINE":
            element_id_to_int = subset_of_elements["bus_int"].to_dict()
            new_from_buses = pandapower_net.line["dangling_line1_id"].map(
                element_id_to_int
            )
            new_to_buses = pandapower_net.line["dangling_line2_id"].map(
                element_id_to_int
            )
            pandapower_net.line.update(
                {"from_bus": new_from_buses, "to_bus": new_to_buses}
            )
            continue
        for side in subset_of_elements["side"].unique():
            side_subset = subset_of_elements.query("side==@side")
            new_buses = pandapower_net[pandapower_table_name][
                IDENTIFIER_COLUMN_NAME
            ].map(side_subset["bus_int"].to_dict())
            pandapower_net[pandapower_table_name].update({side_to_bus[side]: new_buses})

    all_switches["et"] = "b"

    def drop_irrelevant_columns(
            element_table: pd.DataFrame, element_type: str
    ) -> pd.DataFrame:
        if element_type not in EXPECTED_COLUMNS:
            # keep all columns if in doubt
            return element_table
        expected_columns = EXPECTED_COLUMNS[element_type]
        columns_to_keep = list(set(element_table.columns).intersection(expected_columns))
        return element_table.loc[:, columns_to_keep].reset_index(drop=True)


def find_voltage_levels(
        element_table: pd.DataFrame, powsybl_net: "Network"
) -> pd.DataFrame:

    try:
        from pypowsybl import PyPowsyblError
    except ImportError:
        return


    if "voltage_level_id" not in element_table.columns:
        raise PyPowsyblError(
            "Column voltage_level_id is not defined in provided element-table!"
        )

    voltage_levels_of_elements = powsybl_net.get_voltage_levels()[
        ["nominal_v", "high_voltage_limit", "low_voltage_limit"]
    ]
    element_table = pd.merge(
        element_table,
        voltage_levels_of_elements,
        left_on="voltage_level_id",
        right_index=True,
        how="inner",  # voltage levels should all be present in "voltage_levels"
        suffixes=("", "_vl"),
    )

    element_table = element_table.rename(
        columns={
            "nominal_v": "vn_kv",
            "high_voltage_limit": "max_vm_pu",
            "low_voltage_limit": "min_vm_pu",
        }
    )

    element_table["max_vm_pu"] = element_table["max_vm_pu"].fillna(
        element_table["vn_kv"] * 1.1, inplace=False
    )
    element_table["min_vm_pu"] = element_table["min_vm_pu"].fillna(
        element_table["vn_kv"] * 0.9, inplace=False
    )
    return element_table


def set_index_as_column(dataframe):
    dataframe[IDENTIFIER_COLUMN_NAME] = dataframe.index.values


def create_and_match_buses_for_switches_per_voltage_level_bus_breaker(
        all_switches: pd.DataFrame,
        elements_connected_to_switches: pd.DataFrame,
        pandapower_net: "pandapower.pandapowerNet",
        powsybl_net: "pypowsybl.network.Network",
        voltage_level: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    bb = powsybl_net.get_bus_breaker_topology(voltage_level.name)

    if bb.switches.empty:
        return all_switches, elements_connected_to_switches
    # create all switches in voltage-level and buses connected to them:
    buses = set(bb.switches.loc[:, ["bus1_id", "bus2_id"]].values.ravel())
    highest_bus_index = pandapower_net.bus.index.max()
    new_buses, highest_bus_index = create_new_buses(list(buses), highest_bus_index)
    new_buses_dict = new_buses["mapped_bus"].to_dict()
    switches_vl = initialise_new_columns(bb.switches)
    switches_vl["bus"] = switches_vl["bus1_id"].map(new_buses_dict)
    switches_vl["element"] = switches_vl["bus2_id"].map(new_buses_dict)

    all_switches = pd.concat([all_switches, switches_vl], axis=0)
    elements_connected_to_switches = pd.concat(
        [elements_connected_to_switches, bb.elements], axis=0
    )
    # add new buses to pandapower-net:
    add_new_buses_to_pandapower_net(
        new_buses, pandapower_net, voltage_level, assign_id_column_if_not_set=True
    )
    return all_switches, elements_connected_to_switches


def create_and_match_buses_for_switches_per_voltage_level_node_breaker(
        all_switches: pd.DataFrame,
        pandapower_net: "pandapower.pandapowerNet",
        powsybl_net: "pypowsybl.network.Network",
        voltage_level: pd.Series,
) -> pd.DataFrame:
    nb = powsybl_net.get_node_breaker_topology(voltage_level.name)

    # create all switches and buses:
    all_nodes_connected_to_switches = set(
        nb.switches.loc[:, ["node1", "node2"]].values.ravel()
    )
    all_nodes_in_internal_connections = set(
        nb.internal_connections.loc[:, ["node1", "node2"]].values.ravel()
    )
    # we need to create a bus for every node connected to a switch except for those in internal-connections; here we
    # create a bus for each internal connection (to not end up with two buses between two switches)
    highest_bus_index = pandapower_net.bus.index.max()
    new_buses, highest_bus_index = create_new_buses(
        list(
            all_nodes_connected_to_switches.difference(
                all_nodes_in_internal_connections
            )
        ),
        highest_bus_index,
    )
    nodes_to_buses = new_buses["mapped_bus"].to_dict()

    map_nodes_to_elements = nb.nodes.loc[
        nb.nodes.connectable_id != "", "connectable_id"
    ].to_dict()

    if not nb.internal_connections.empty:
        # topology might look like this:
        # nb.switches: id       node1   node2
        #              switch1  20      21
        #              switch2  36      37
        # nb.nodes: node    connectable_id
        #           ...
        #           38      element
        # nb.internal_connections: node1   node2
        #                          21      8
        #                          36      8
        #                          37      9
        #                          38      9
        # 20 switch1 21 8 36 switch2 37 9 38 element
        # for each switch-switch-connection or switch-element-connection we only want to model one bus.
        # but the following model is also possible:
        # 20 switch1 21 switch2 37 element
        # in this case internal_connections would be empty.
        all_nodes_connected_to_elements = nb.nodes.query(
            "connectable_id!=''"
        ).index.tolist()
        all_nodes_only_in_internal_connections = (
            all_nodes_in_internal_connections.difference(
                all_nodes_connected_to_switches.union(all_nodes_connected_to_elements)
            )
        )

        new_buses_internal_connections, highest_bus_index = create_new_buses(
            list(all_nodes_only_in_internal_connections), highest_bus_index
        )
        nodes_to_buses = new_buses_internal_connections["mapped_bus"].to_dict()
        new_buses = pd.concat(
            [new_buses, new_buses_internal_connections], axis=0
        )  # ToDo: FutureWarning
        # map new buses to internal connections to also map buses to node2
        internal_connections_mapped_to_bus = nb.internal_connections
        internal_connections_mapped_to_bus["mapped_bus"] = (
            internal_connections_mapped_to_bus["node1"].map(nodes_to_buses)
        )
        buses_mapped_to_node2 = internal_connections_mapped_to_bus["node2"].map(
            nodes_to_buses
        )
        internal_connections_mapped_to_bus.update({"mapped_bus": buses_mapped_to_node2})

        nodes_to_buses.update(
            {
                **internal_connections_mapped_to_bus.set_index("node1")[
                    "mapped_bus"
                ].to_dict(),
                **internal_connections_mapped_to_bus.set_index("node2")[
                    "mapped_bus"
                ].to_dict(),
            }
        )
        # elements might have nodes which are either directly referenced by switches or are connected via
        # internal-connections to a switch. In the following we assume that node2 in internal-nodes is always the
        # "internal node" which is not referenced by any elements but only referenced in internal_connections.
        # direct references: map node1 to connectable-id

        nb.internal_connections["connectable_id"] = nb.internal_connections[
            "node1"
        ].map(nb.nodes["connectable_id"])
        # indirect references: map connectable-id to every row which has the same node2 as the connectable-id
        nb.internal_connections.update(
            {
                "connectable_id": nb.internal_connections["node2"].map(
                    nb.internal_connections.set_index("node2")[
                        "connectable_id"
                    ].to_dict()
                )
            }
        )

        map_nodes_to_elements.update(
            nb.internal_connections.set_index("node1")["connectable_id"].to_dict()
        )

    # match buses with switches:
    switches_vl = initialise_new_columns(nb.switches)
    switches_vl["bus"] = switches_vl["node1"].map(nodes_to_buses)
    switches_vl["element"] = switches_vl["node2"].map(nodes_to_buses)

    switches_vl["connectable_id1"] = switches_vl["node1"].map(map_nodes_to_elements)
    switches_vl["connectable_id2"] = switches_vl["node2"].map(map_nodes_to_elements)

    all_switches = pd.concat([all_switches, switches_vl], axis=0)
    # add new buses to pandapower-net:
    add_new_buses_to_pandapower_net(
        new_buses, pandapower_net, voltage_level, assign_id_column_if_not_set=True
    )

    return all_switches


def connect_elements_to_switches_node_breaker(
        all_switches: pd.DataFrame, pandapower_net: "pandapower.pandapowerNet"
):
    conn1_to_bus = (
        all_switches.loc[
            np.all(
                [
                    all_switches.connectable_id1 != "",
                    ~all_switches.connectable_id1.isna(),
                ],
                axis=0,
            )
        ]
        .set_index("connectable_id1")["bus"]
        .to_dict()
    )
    conn2_to_bus = (
        all_switches.loc[
            np.all(
                [
                    all_switches.connectable_id2 != "",
                    ~all_switches.connectable_id2.isna(),
                ],
                axis=0,
            )
        ]
        .set_index("connectable_id2")["element"]
        .to_dict()
    )
    unique_keys = conn1_to_bus.keys() | conn2_to_bus.keys()
    # all elements which are referenced in both dicts are elements of type trafo/trafo3w or line (or other elements
    # with two ends)
    conn_to_bus = {
        k: v
        for conn_to_bus in [conn1_to_bus, conn2_to_bus]
        for k, v in conn_to_bus.items()
        if k in unique_keys
    }

    bus_target_column = "bus"
    for table in ["load", "gen", "sgen", "ext_grid", "busbarsection", "shunt"]:
        if (
                table not in pandapower_net
                or IDENTIFIER_COLUMN_NAME not in pandapower_net[table].columns
        ):
            continue
        new_buses = pandapower_net[table][IDENTIFIER_COLUMN_NAME].map(conn_to_bus)
        # update leaves orignal value when the corresponding entry in new_buses is nan
        pandapower_net[table].update({bus_target_column: new_buses})

    for table, element_type in [("trafo", "t"), ("trafo3w", "t3"), ("line", "l")]:
        if (
                table not in pandapower_net
                or IDENTIFIER_COLUMN_NAME not in pandapower_net[table].columns
        ):
            continue
        # These elements can be connected by referencing the element-index in column 'element' and  setting the correct
        # element-type in column 'et'. For these elements, the created buses can be removed again, they are not needed.
        id_to_index = {
            v: k
            for k, v in pandapower_net[table][IDENTIFIER_COLUMN_NAME].to_dict().items()
        }
        new_bus_entry = all_switches["connectable_id1"].map(id_to_index)
        new_element_entry = all_switches["connectable_id2"].map(id_to_index)
        # switch entries in bus and element-col and their connectable-ids if the entry is in new_bus_entry
        switch_bus_element = ~new_bus_entry.isna()
        all_switches.loc[
            switch_bus_element,
            ["bus", "element", "connectable_id1", "connectable_id2", "node1", "node2"],
        ] = all_switches.loc[
            switch_bus_element,
            ["element", "bus", "connectable_id2", "connectable_id1", "node2", "node1"],
        ]
        new_element_entry.update(new_bus_entry)
        old_buses = all_switches.loc[~new_element_entry.isna(), "element"].to_list()
        all_switches.update({"element": new_element_entry})
        all_switches.loc[~new_element_entry.isna(), "et"] = element_type
        pandapower_net["bus"].drop(index=old_buses, inplace=True, errors="ignore")
        if "res_bus" in pandapower_net:
            pandapower_net["res_bus"].drop(
                index=old_buses, inplace=True, errors="ignore"
            )
    all_switches["et"] = all_switches["et"].fillna("b")


def initialise_new_columns(switches):
    switches["element"] = np.nan
    switches["bus"] = np.nan
    switches["et"] = np.nan
    switches[IDENTIFIER_COLUMN_NAME] = switches.index.values
    return switches.astype({"element": "object", "bus": "object", "et": "object"})


def create_new_buses(
        nodes: Sequence, highest_bus_index: int
) -> tuple[pd.DataFrame, int]:
    buses = pd.DataFrame(
        index=list(nodes),
        columns=["mapped_bus"],
        data=np.arange(len(nodes)).astype(int) + highest_bus_index + 1,
    )
    if buses.empty:
        return buses, highest_bus_index
    return buses, buses.index.max()


def add_new_buses_to_pandapower_net(
        new_buses,
        pandapower_net,
        voltage_level: pd.Series,
        assign_id_column_if_not_set=True,
):
    if new_buses.empty:
        return
    # add new buses to pandapower-network:
    new_buses["name"] = [
        f"{voltage_level.name}_{n}" if not isinstance(n, str) else n
        for n in new_buses.index.values
    ]
    # new_buses can either contain a list of nodes or a list of bus-breaker-ids
    if assign_id_column_if_not_set:
        new_buses[IDENTIFIER_COLUMN_NAME] = new_buses["name"]

    new_buses.set_index("mapped_bus", inplace=True)
    new_buses["vn_kv"] = voltage_level["nominal_v"]
    new_buses["in_service"] = True
    pandapower_net.bus = pd.concat([pandapower_net.bus, new_buses], axis=0)
    if "res_bus" in pandapower_net and not pandapower_net["res_bus"].empty:
        pandapower_net.res_bus = pd.concat(
            [
                pandapower_net.res_bus,
                pd.DataFrame(
                    index=new_buses.index, columns=pandapower_net.res_bus.columns
                ),
            ],
            axis=0,
        )
