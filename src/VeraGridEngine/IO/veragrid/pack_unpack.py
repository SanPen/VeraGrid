# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.  
# SPDX-License-Identifier: MPL-2.0
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Dict, Union, List, Tuple, Any, Callable
import pandas as pd
import numpy as np
from enum import EnumMeta as EnumType
from VeraGridEngine.basic_structures import Logger
from VeraGridEngine.Devices.multi_circuit import MultiCircuit
import VeraGridEngine.Devices as devices
from VeraGridEngine.Devices.Parents.editable_device import GCProp, EditableDevice
from VeraGridEngine.Devices.Profiles import AnyProfile
from VeraGridEngine.Utils.Symbolic.symbolic_io import BlockSaver, BlockParser, Block
from VeraGridEngine.Utils.procedural_logic import ProceduralLogicCodec
from VeraGridEngine.Devices.types import ALL_DEV_TYPES, VERAGRID_FILE_TYPE
from VeraGridEngine.Devices.Diagrams.base_diagram import copy_diagrams
from VeraGridEngine.enumerations import (DiagramType, DeviceType, SubObjectType, TapPhaseControl, TapModuleControl,
                                         ContingencyOperationTypes)

ProfileDictionary = Dict[str, bool | int | str | dict[str, dict[int, Any | None] | dict[Any, Any]] | Any]

ModelDictionary = Dict[str, object]


def get_objects_dictionary() -> Dict[str, ALL_DEV_TYPES]:
    """
    creates a dictionary with the types and the circuit objects
    :return: Dictionary instance
    """

    # this list must be sorted in dependency order so that the
    # loading algorithm is able to find the object substitutions

    return {
        'modelling_authority': devices.ModellingAuthority(),

        'area': devices.Area(),
        'zone': devices.Zone(),

        'country': devices.Country(),
        'community': devices.Community(),
        'region': devices.Region(),
        'municipality': devices.Municipality(),

        'owner': devices.Owner(),

        'substation': devices.Substation(),
        'voltage_level': devices.VoltageLevel(),

        'technology': devices.Technology(),

        'fuel': devices.Fuel(),

        'emission': devices.EmissionGas(),

        'facility': devices.Facility(),

        'market_unit': devices.MarketUnit(),

        'rms_model_template': devices.RmsModelTemplate(),
        'emt_model_template': devices.EmtModelTemplate(),
        'fmu_template': devices.FmuTemplate(),

        'bus': devices.Bus(),

        'bus_bar': devices.BusBar(),

        'load': devices.Load(),

        'static_generator': devices.StaticGenerator(),

        'battery': devices.Battery(),

        'generator': devices.Generator(),

        'shunt': devices.Shunt(),

        'linear_shunt': devices.ControllableShunt(),

        'external_grid': devices.ExternalGrid(),

        'current_injection': devices.CurrentInjection(),

        'wires': devices.Wire(),
        'overhead_line_types': devices.OverheadLineType(),
        'underground_cable_types': devices.UndergroundLineType(),
        'sequence_line_types': devices.SequenceLineType(),
        'transformer_types': devices.TransformerType(),

        'branch_group': devices.BranchGroup(),

        'branch': devices.Branch(),
        'transformer2w': devices.Transformer2W(),

        'windings': devices.Winding(),
        'transformer3w': devices.Transformer3W(),
        'transformernw': devices.TransformerNW(),

        'line': devices.Line(),
        'dc_line': devices.DcLine(),

        'hvdc': devices.HvdcLine(),

        'vsc': devices.VSC(),
        'upfc': devices.UPFC(),

        'series_reactance': devices.SeriesReactance(),

        'switch': devices.Switch(),

        'contingency_group': devices.ContingencyGroup(),
        'contingency': devices.Contingency(),
        'short_circuit_definition': devices.ShortCircuitEvent(),

        'remedial_action_group': devices.RemedialActionGroup(),
        'remedial_action': devices.RemedialAction(),

        'investments_group': devices.InvestmentsGroup(),
        'investment': devices.Investment(),

        'rms_event_group': devices.RmsEventsGroup(),
        'rms_event': devices.RmsEvent(),

        'emt_event_group': devices.EmtEventsGroup(),
        'emt_event': devices.EmtEvent(),

        'dynamic_plot': devices.DynamicPlot(),
        'dynamic_plot_entry': devices.DynamicPlotEntry(),

        'fluid_node': devices.FluidNode(),
        'fluid_path': devices.FluidPath(),
        'fluid_turbine': devices.FluidTurbine(),
        'fluid_pump': devices.FluidPump(),
        'fluid_p2x': devices.FluidP2x(),

        'pi_measurement': devices.PiMeasurement(),
        'qi_measurement': devices.QiMeasurement(),
        'pf_measurement': devices.PfMeasurement(),
        'qf_measurement': devices.QfMeasurement(),
        'if_measurement': devices.IfMeasurement(),
        'pt_measurement': devices.PtMeasurement(),
        'qt_measurement': devices.QtMeasurement(),
        'it_measurement': devices.ItMeasurement(),
        'vm_measurement': devices.VmMeasurement(),
        'va_measurement': devices.VaMeasurement(),
        'pg_measurement': devices.PgMeasurement(),
        'qg_measurement': devices.QgMeasurement(),

        'control_pc': devices.ControlPc(),
    }


_FMU_CONFIG_PROPERTY_NAMES: Tuple[str, ...] = (
    "rms_fmu_import_config",
    "emt_fmu_import_config",
    "rms_fmu_me_import_config",
    "emt_fmu_me_import_config",
    "serialized_config",
)


def _to_project_relative_fmu_config(config_text: str, project_directory: Path | None) -> str:
    """
    Rewrite the stored FMU path in one serialized configuration as a project-relative path.

    :param config_text: Serialized FMU configuration payload.
    :param project_directory: Directory containing the VeraGrid project file.
    :return: Serialized configuration with a relative FMU path when possible.
    """

    if project_directory is None:
        return config_text
    else:
        stripped_text: str = config_text.strip()
        if len(stripped_text) == 0:
            return config_text
        else:
            payload: dict[str, Any] = json.loads(stripped_text)
            fmu_path_text = payload.get("fmu_path", None)
            if isinstance(fmu_path_text, str):
                fmu_path = Path(fmu_path_text)
                if fmu_path.is_absolute():
                    try:
                        payload["fmu_path"] = os.path.relpath(str(fmu_path), start=str(project_directory))
                    except ValueError:
                        payload["fmu_path"] = fmu_path_text
                else:
                    pass
            else:
                pass
            return json.dumps(payload, sort_keys=True)


def _resolve_project_fmu_config(config_text: str, project_directory: Path | None) -> str:
    """
    Rewrite the stored FMU path in one serialized configuration as an absolute runtime path.

    :param config_text: Serialized FMU configuration payload.
    :param project_directory: Directory containing the VeraGrid project file.
    :return: Serialized configuration with a resolved absolute FMU path when possible.
    """

    if project_directory is None:
        return config_text
    else:
        stripped_text: str = config_text.strip()
        if len(stripped_text) == 0:
            return config_text
        else:
            payload: dict[str, Any] = json.loads(stripped_text)
            fmu_path_text = payload.get("fmu_path", None)
            if isinstance(fmu_path_text, str):
                fmu_path = Path(fmu_path_text)
                if fmu_path.is_absolute():
                    pass
                else:
                    payload["fmu_path"] = str((project_directory / fmu_path).resolve())
            else:
                pass
            return json.dumps(payload, sort_keys=True)


def _resolve_circuit_fmu_paths(circuit: MultiCircuit, project_directory: Path | None) -> None:
    """
    Resolve stored FMU configuration paths for every element in the circuit.

    :param circuit: Parsed circuit instance.
    :param project_directory: Directory containing the VeraGrid project file.
    :return: None.
    """

    if project_directory is None:
        return
    else:
        elm: ALL_DEV_TYPES
        for elm in circuit.get_all_elements_iter():
            property_name: str
            for property_name in _FMU_CONFIG_PROPERTY_NAMES:
                if property_name in elm.registered_properties:
                    current_value = elm.get_snapshot_value_by_name(property_name)
                    if isinstance(current_value, str):
                        elm.set_snapshot_value(property_name,
                                               _resolve_project_fmu_config(current_value, project_directory))
                    else:
                        pass
                else:
                    pass


def _to_project_relative_path(path_text: str, project_directory: Path | None) -> str:
    """
    Convert one absolute filesystem path into a project-relative path when possible.

    :param path_text: Original path text.
    :param project_directory: Directory containing the VeraGrid project file.
    :return: Relative path when conversion is possible.
    """

    if project_directory is None:
        return path_text
    else:
        normalized_text: str = str(path_text).strip()
        if len(normalized_text) == 0:
            return path_text
        else:
            candidate = Path(normalized_text)
            if candidate.is_absolute():
                try:
                    return os.path.relpath(str(candidate), start=str(project_directory))
                except ValueError:
                    return path_text
            else:
                return path_text


def get_multiverse_node_metadata(metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract the per-node metadata dictionary from a multiverse metadata payload.

    Newer files wrap node records under ``nodes`` and may include top-level metadata such as
    ``active_node_id``. Older files store the node records directly at the top level.
    """
    # New-format multiverse metadata is a small envelope:
    # {
    #     "active_node_id": ...,
    #     "nodes": {
    #         <node_id>: {...},
    #         ...
    #     }
    # }
    # In that case, only the nested ``nodes`` mapping contains per-node records.
    nodes = metadata.get("nodes", None)

    # Accept the new wrapped format only if the value really is the node dictionary.
    # This avoids accidentally treating malformed metadata as valid node content.
    if isinstance(nodes, dict):
        return nodes

    # Older files predate the metadata envelope and store the node records directly at
    # the top level. Returning ``metadata`` as-is keeps the loader backward compatible.
    return metadata


def order_multiverse_records(metadata: Dict[str, Dict[str, int | float]] | Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return multiverse metadata records in a parent-before-child order.

    The multiverse payloads must be parsed in dependency order because child delta payloads
    may reference objects inherited from their parent composed scenario.
    """
    node_metadata = get_multiverse_node_metadata(metadata)

    pending_records: Dict[int, Dict[str, Any]] = {
        int(node_id): dict(record) for node_id, record in node_metadata.items()
    }
    ordered_records: List[Dict[str, Any]] = list()

    while pending_records:
        progressed = False

        for pending_node_id in list(pending_records.keys()):
            record = pending_records[pending_node_id]
            parent_id_raw = record["parent_id"]
            parent_id = None if parent_id_raw is None else int(parent_id_raw)

            if parent_id is not None and parent_id in pending_records:
                continue

            ordered_records.append(record)
            del pending_records[pending_node_id]
            progressed = True

        if not progressed:
            unresolved = ", ".join(str(node_id) for node_id in pending_records.keys())
            raise ValueError(f"Could not resolve multiverse metadata dependency order for nodes: {unresolved}")

    return ordered_records


def gather_model_as_data_frames(circuit: MultiCircuit,
                                logger: Logger = Logger(),
                                legacy: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Pack the circuit information into tables (DataFrames)
    :param circuit: MultiCircuit instance
    :param logger: Logger instance
    :param legacy: Generate the legacy object DataFrames
    :return: dictionary of DataFrames
    """
    dfs = dict()

    # get the master time profile
    time_profile = circuit.time_profile
    nt = circuit.get_time_number()

    ########################################################################################################
    # declare objects to iterate  name: [sample object, list of objects, headers]
    ########################################################################################################
    object_types = get_objects_dictionary()

    # forget abut the Branch object when saving, now we have lines and transformers separated in their own lists
    del object_types['branch']

    ########################################################################################################
    # generic object iteration
    ########################################################################################################
    if legacy:

        # configuration ################################################################################################
        obj = list()
        obj.append(['BaseMVA', circuit.Sbase])
        obj.append(['Version', 5])
        obj.append(['Name', str(circuit.name)])
        obj.append(['Comments', str(circuit.comments)])
        obj.append(['idtag', str(circuit.idtag)])

        # increase the model version
        circuit.model_version += 1

        obj.append(['ModelVersion', str(circuit.model_version)])
        obj.append(['UserName', str(circuit.user_name)])
        obj.append(['program', 'VeraGrid'])

        dfs['config'] = pd.DataFrame(data=obj, columns=['Property', 'Value'], dtype=str)

        for object_type_name, object_sample in object_types.items():

            headers = object_sample.registered_properties.keys()

            lists_of_objects: List[ALL_DEV_TYPES] = circuit.get_elements_by_type(object_sample.device_type)

            obj = list()
            profiles = dict()
            object_idtags = list()
            if len(lists_of_objects) > 0:

                for k, elm in enumerate(lists_of_objects):

                    # get the object normal information
                    obj.append(elm.get_save_data())
                    object_idtags.append(elm.idtag)

                    if time_profile is not None:

                        if nt > 0:

                            elm.ensure_profiles_exist(time_profile)

                            for property_name, profile_property in object_sample.properties_with_profile.items():

                                # get the array
                                profile = elm.get_profile(magnitude=property_name)

                                if profile_property not in profiles.keys():
                                    # create the profile
                                    try:
                                        profiles[profile_property] = np.zeros(shape=(nt, len(lists_of_objects)),
                                                                              dtype=profile.dtype)
                                    except TypeError:
                                        logger.add_warning("Profile packed as object", device_class=str(profile.dtype))
                                        profiles[profile_property] = np.zeros(shape=(nt, len(lists_of_objects)),
                                                                              dtype=object)

                                # copy the object profile to the array of profiles
                                profiles[profile_property][:, k] = profile.toarray()

                # convert the objects' list to an array
                dta = np.array(obj)
            else:
                # declare an empty array
                dta = np.zeros((0, len(headers)))

            # declare the DataFrames for the normal data
            dfs[object_type_name] = pd.DataFrame(data=dta, columns=list(headers))

            # create the profiles' DataFrames
            for prop, data in profiles.items():
                dfs[object_type_name + '_' + prop] = pd.DataFrame(data=data, columns=object_idtags, index=time_profile)

        # towers and wires ---------------------------------------------------------------------------------------------
        # because each tower contains a reference to a number of wires, these relations need to be stored as well
        associations = list()
        for tower in circuit.overhead_line_types:
            for wire in tower.wires_in_tower.data:
                associations.append([tower.name, wire.name, wire.xpos, wire.ypos, wire.phase])

        dfs['tower_wires'] = pd.DataFrame(data=associations,
                                          columns=['tower_name', 'wire_name', 'xpos', 'ypos', 'phase'])

        # Time ---------------------------------------------------------------------------------------------------------

        if circuit.time_profile is not None:
            if isinstance(circuit.time_profile, pd.DatetimeIndex):
                time_df = pd.DataFrame(data=circuit.time_profile.values, columns=['Time'])
            else:
                time_df = pd.DataFrame(data=circuit.time_profile, columns=['Time'])
            dfs['time'] = time_df

    return dfs


def profile_todict(profile: AnyProfile) -> ProfileDictionary:
    """
    Get a dictionary representation of the profile
    :return:
    """
    s = profile.size()

    if s > 0:
        if profile.is_sparse:
            return {
                'is_sparse': True,
                'size': s,
                'default': profile.sparse_array.default_value,
                'sparse_data': {
                    'map': profile.sparse_array.get_map()
                }
            }
        else:
            return {
                'is_sparse': False,
                'size': s,
                'default': profile.default_value,
                'dense_data': profile.dense_array.tolist(),
            }
    else:
        return {
            'is_sparse': True,
            'size': s,
            'default': profile.default_value if profile.sparse_array is None else profile.sparse_array.default_value,
            'sparse_data': {
                'map': dict()
            }
        }


def profile_todict_idtag(profile: AnyProfile) -> ProfileDictionary:
    """
    Get a dictionary representation of the profile
    :return:
    """
    default = profile.default_value.idtag if hasattr(profile.default_value, 'idtag') else "None"

    if profile.is_sparse:
        return {
            'is_sparse': profile.is_sparse,
            'size': profile.size(),
            'default': default,
            'sparse_data': {
                'map': {key: val.idtag if hasattr(val, 'idtag') else None
                        for key, val in profile.sparse_array.get_map().items()}
                if profile.sparse_array is not None else dict()
            }
        }
    else:
        return {
            'is_sparse': profile.is_sparse,
            'size': profile.size(),
            'default': default,
            'dense_data': [e.idtag if hasattr(e, 'idtag') else None for e in profile.dense_array]
            if profile.dense_array is not None else list(),
        }


def profile_todict_str(profile: AnyProfile) -> ProfileDictionary:
    """
    Get a dictionary representation of the profile
    :return:
    """
    s = profile.size()

    if s > 0:
        if profile.is_sparse:
            return {
                'is_sparse': True,
                'size': s,
                'default': str(profile.default_value),
                'sparse_data': {
                    'map': {key: str(val) for key, val in profile.sparse_array.get_map().items()}
                }
            }
        else:
            return {
                'is_sparse': False,
                'size': s,
                'default': str(profile.default_value),
                'dense_data': [str(e) for e in profile.dense_array],
            }
    else:
        # empty profile
        return {
            'is_sparse': True,
            'size': s,
            'default': str(profile.default_value),
            'sparse_data': {
                'map': dict()
            }
        }


def cast_profile_value(
        profile: AnyProfile,
        value: Any,
        collection: Union[None, Dict[str, Any]] = None,
) -> Any:
    """
    Convert serialized profile payloads into the concrete type required by ``profile``.

    :param profile: Typed profile that will receive the value.
    :param value: Serialized raw value.
    :param collection: Optional idtag-to-object dictionary for device references.
    :return: Converted value.
    """
    if value is None or value == "None":
        return None

    if collection is not None:
        return collection.get(value, None)

    if isinstance(profile.dtype, DeviceType):
        return value

    if isinstance(profile.dtype, EnumType):
        return profile.dtype(value)

    if profile.dtype == bool:
        if isinstance(value, str):
            low = value.strip().lower()
            if low in {"true", "1"}:
                return True
            if low in {"false", "0"}:
                return False
        return bool(value)

    if profile.dtype == int:
        return int(value)

    if profile.dtype == float:
        return float(value)

    if profile.dtype == str:
        return str(value)

    return value


def get_profile_from_dict(profile: AnyProfile,
                          data: Dict[str, Any | Dict[str, Any]],
                          collection: Union[None, Dict[str, Any]] = None):
    """
    Create a profile from JSON declarative data.
    :param profile: Profile object to fill in
    :param data: JSON profile declaration.
    :param collection: if the collection is provided, it will be used to convert idtags into objects
    :return: None
    """
    raw_default_value = data['default']
    is_sparse = bool(data['is_sparse'])

    try:
        default_value: Any = cast_profile_value(profile=profile, value=raw_default_value, collection=collection)
    except (TypeError, ValueError):
        default_value = profile.default_value

    if isinstance(profile.dtype, DeviceType) and default_value == "None":
        default_value = profile.default_value

    if is_sparse:
        sp_data = data['sparse_data']

        if collection is None:
            map_data = {
                int(key): cast_profile_value(profile=profile, value=val, collection=collection)
                for key, val in sp_data['map'].items()
            }
        else:
            map_data = {
                int(key): cast_profile_value(profile=profile, value=val, collection=collection)
                for key, val in sp_data['map'].items()
            }

        profile.create_sparse(default_value=default_value,
                              size=data['size'], map_data=map_data)
    else:

        if collection is None:
            arr = [cast_profile_value(profile=profile, value=i, collection=collection) for i in data['dense_data']]
        else:
            arr = [cast_profile_value(profile=profile, value=i, collection=collection) for i in data['dense_data']]
        profile.set(np.array(arr))

    # mark as initialized
    profile.set_initialized()


def veragrid_object_to_json(elm: ALL_DEV_TYPES,
                            block_saver: BlockSaver,
                            project_directory: Path | None = None) -> Dict[str, str]:
    """

    :param elm:
    :param block_saver:
    :param project_directory: Directory used to store portable FMU paths.
    :return:
    """

    data = dict()
    for name, prop in elm.registered_properties.items():
        obj = elm.get_snapshot_value(prop=prop)

        if prop.tpe in [str, float, int, bool]:
            if name in _FMU_CONFIG_PROPERTY_NAMES and isinstance(obj, str):
                data[name] = _to_project_relative_fmu_config(obj, project_directory)
            else:
                if name == "fmu_relative_path" and isinstance(obj, str):
                    data[name] = _to_project_relative_path(obj, project_directory)
                else:
                    data[name] = obj

            if prop.has_profile():
                data[name + '_prof'] = profile_todict(elm.get_profile_by_prop(prop=prop))

        elif prop.tpe == SubObjectType.MergeInformation:
            data[name] = obj.to_dict()

        elif prop.tpe == SubObjectType.GeneratorQCurve:
            data[name] = obj.to_list()

        elif prop.tpe == SubObjectType.LineLocations:
            data[name] = obj.to_list()

        elif prop.tpe == SubObjectType.ImpedanceTripletList:
            data[name] = obj.to_list()

        elif prop.tpe == SubObjectType.ListOfWires:
            data[name] = obj.to_list()

        elif prop.tpe == SubObjectType.TapChanger:
            data[name] = obj.to_dict()

        elif prop.tpe == SubObjectType.Associations:
            data[name] = obj.to_dict()

        elif prop.tpe == SubObjectType.AdmittanceMatrix:
            data[name] = obj.to_dict()

        elif prop.tpe == SubObjectType.DaeBlockType:
            block_saver.save_block(blk=obj, main=True)
            if isinstance(obj, Block):
                data[name] = obj.uid
            else:
                raise ValueError("must be a block")

        elif prop.tpe == SubObjectType.VarType:
            if obj is not None:
                # Persist the physical variable identity. The mutable UID can
                # be shared by every variable connected to the same signal.
                data[name] = obj.non_mutable_uid
            else:
                # Persistent dynamic plot entries may keep unresolved legacy Var
                # hints as ``None`` while semantic fields remain the canonical
                # binding identity.
                data[name] = None

        elif prop.tpe == SubObjectType.ConstType:
            if obj is not None:
                data[name] = obj.uid
            else:
                data[name] = None

        elif prop.tpe == SubObjectType.Array:
            data[name] = list(obj)

        else:
            # if the object is not of a primary type, get the idtag instead
            if obj is None:
                data[name] = None
            else:
                if isinstance(obj, EditableDevice):
                    data[name] = obj.idtag

                    if prop.has_profile():
                        data[name + '_prof'] = profile_todict_idtag(elm.get_profile_by_prop(prop=prop))
                    else:
                        pass
                else:
                    # some data types might not have the idtag, ten just use the str method
                    data[name] = str(obj)

                    if prop.has_profile():
                        data[name + '_prof'] = profile_todict_str(elm.get_profile_by_prop(prop=prop))
                    else:
                        pass

    return data


def gather_model_as_jsons(circuit: MultiCircuit,
                          project_directory: Path | None = None) -> ModelDictionary:
    """
    Transform a ``MultiCircuit`` into a collection of JSON records.
    :param circuit:
    :param project_directory:
    :return:
    """

    if circuit.has_time_series:
        circuit.ensure_profiles_exist()

    data: ModelDictionary = dict()

    block_saver = BlockSaver(circuit.var_factory)

    # declare objects to iterate  name: [sample object, list of objects, headers]
    object_types = get_objects_dictionary()

    del object_types['branch']

    # generic object iteration
    for object_type_name, object_sample in object_types.items():

        object_json = list()

        lists_of_objects = circuit.get_elements_by_type(object_sample.device_type)

        if len(lists_of_objects) > 0:

            for k, elm in enumerate(lists_of_objects):
                obj_data = veragrid_object_to_json(elm, block_saver=block_saver, project_directory=project_directory)
                object_json.append(obj_data)

        data[object_type_name] = object_json

    # time
    unix_time = circuit.get_unix_time()
    if len(unix_time) > 1 and np.all(unix_time == unix_time[0]) and abs(int(unix_time[0])) <= 10:
        raise ValueError(
            f"Refusing to save degenerate master time profile: all {len(unix_time)} unix values are "
            f"{int(unix_time[0])}. This usually means circuit.time_profile was overwritten before saving."
        )

    data['time'] = {'unix': unix_time.tolist(),
                    'prob': list(np.ones(len(unix_time))),
                    'snapshot_unix': circuit.get_snapshot_time_unix()}

    # gather the circuit
    circuit.model_version += 1
    data['circuit'] = circuit.to_dict()

    # At this point I already have the symbolic data stored in block_saver

    return {
        "model_data": data,
        "symbolic_data": {
            "vars": block_saver.get_vars_to_save(),
            "consts": block_saver.get_const_to_save(),
            "diff_vars": block_saver.get_diff_vars_to_save(),
            "shared_references": block_saver.get_shared_references_to_save(),
            "connections": block_saver.get_connections_to_save(),
            "blocks": block_saver.get_blocks(),
            "main_block_uids": block_saver.main_block_uids,
        }
    }


def search_property(template_elm: ALL_DEV_TYPES,
                    old_props_dict: Dict[str, str],
                    property_to_search: str,
                    logger: Logger) -> Union[GCProp, None]:
    """
    Search for a property name in the template object registered properties and their old names
    :param template_elm: Device to loo into
    :param old_props_dict: Dictionary matching the old names with their current counterpart
    :param property_to_search: property name to search
    :param logger: Logger
    :return: GCProp or None if not found
    """
    # search the property in the object headers
    gc_prop = template_elm.registered_properties.get(property_to_search, None)

    if gc_prop is None:
        # The property is not in the headers, so search the legacy-name list.
        current_prop_name = old_props_dict.get(property_to_search, None)

        if current_prop_name:

            logger.add_info('The file property was updated in the data model',
                            device=str(template_elm.device_type),
                            value=property_to_search)

            gc_prop = template_elm.registered_properties.get(current_prop_name, None)
            return gc_prop
        else:
            # A property absent from both registries identifies invalid input.
            logger.add_error('The property does not exist in the registries',
                             device=str(template_elm.device_type),
                             value=property_to_search)
            return None
    else:
        return gc_prop


def look_for_property(elm: ALL_DEV_TYPES, property_name) -> Union[GCProp, None]:
    """

    :param elm:
    :param property_name:
    :return:
    """
    device_property_definition: GCProp = elm.registered_properties.get(property_name, None)

    if device_property_definition:
        # the property of the file exists directly
        return device_property_definition
    else:
        # A missing direct property may still use a legacy property name.
        for name, prop in elm.registered_properties.items():
            if property_name in prop.old_names:
                return prop

        return None  # if we reach here, it wasn't found


def valid_value(val) -> bool:
    """

    :param val:
    :return:
    """
    if isinstance(val, str):
        if val == 'nan':
            return False
        if val == '':
            return False
        if val == 'None':
            return False
    if isinstance(val, float):
        if math.isnan(val):
            return False
        if math.isinf(val):
            return False
    return True


def look_in_collection_by_name(key: str, collection: Dict[str, ALL_DEV_TYPES]) -> Union[ALL_DEV_TYPES, None]:
    """
    Look in a collection for an element by its name instead of by Idtag
    :param key: name of the element
    :param collection: Collection to look into
    :return: Device or None if not found
    """
    for idtag, elm in collection.items():
        if elm.name == key:
            return elm
    return None


class CreatedOnTheFly:
    """
    This class is to pack all those devices that are created "on the fly" to support legacy formats
    """

    def __init__(self) -> None:
        """
        Constructor
        """
        # legacy operations: this is from when area, zone and substation were strings,
        # now we create those objects on the fly
        self.legacy_area_dict: Dict[str, devices.Area] = dict()
        self.legacy_zone_dict: Dict[str, devices.Zone] = dict()
        self.legacy_substation_dict: Dict[str, devices.Substation] = dict()

        self.contingency_groups: List[devices.ContingencyGroup] = list()
        self.contingencies: List[devices.Contingency] = list()

        self.technologies: Dict[str, devices.Technology] = dict()

    def get_create_area(self, property_value):
        """

        :param property_value:
        :return:
        """
        area = self.legacy_area_dict.get(property_value, None)
        if area is None:
            area = devices.Area(name=str(property_value))
            self.legacy_area_dict[property_value] = area
        return area

    def get_create_zone(self, property_value):
        """

        :param property_value:
        :return:
        """
        zone = self.legacy_zone_dict.get(property_value, None)
        if zone is None:
            zone = devices.Zone(name=str(property_value))
            self.legacy_zone_dict[property_value] = zone
        return zone

    def get_create_substation(self, property_value):
        """

        :param property_value:
        :return:
        """
        substation = self.legacy_substation_dict.get(property_value, None)
        if substation is None:
            substation = devices.Substation(name=str(property_value))
            self.legacy_substation_dict[property_value] = substation
        return substation

    def create_contingency(self, elm: ALL_DEV_TYPES):
        """

        :param elm:
        :return:
        """
        con_group = devices.ContingencyGroup(name=elm.name)
        conn = devices.Contingency(device=elm, prop=ContingencyOperationTypes.Active, group=con_group)

        self.contingency_groups.append(con_group)
        self.contingencies.append(conn)

    def create_technology(self, elm: devices.Generator, tech_name: str) -> None:
        """

        :param elm:
        :param tech_name:
        :return:
        """

        tech = self.technologies.get(tech_name, None)

        if tech is None:
            tech = devices.Technology(name=tech_name)
            self.technologies[tech_name] = tech

        elm.technologies.add_object(api_object=tech, val=1.0)


def parse_object_type_from_dataframe(
        main_df: pd.DataFrame,
        template_elm: ALL_DEV_TYPES,
        elements_dict_by_type: Dict[DeviceType, Dict[str, ALL_DEV_TYPES]],
        time_profile: pd.DatetimeIndex,
        object_type_key: str,
        data: Dict[str, Union[float, str, pd.DataFrame]],
        logger: Logger) -> Tuple[List[ALL_DEV_TYPES], Dict[str, ALL_DEV_TYPES], CreatedOnTheFly]:
    """
    Convert a DataFrame to a list of VeraGrid devices
    :param main_df: DataFrame to convert
    :param template_elm: Element to use as template for conversion
    :param elements_dict_by_type: Dictionary of devices grouped by type used to look for referenced objects
                                    elements_dict_by_type[DeviceType][idtag] -> device
    :param time_profile: Master time profile
    :param object_type_key: Object type naming to find the profile
    :param data: Complete data collection to find the profiles
    :param logger: Logger instance
    :return: devices, devices_dict
    """
    # dictionary to be filled with this type of objects
    devices_dict: Dict[str, ALL_DEV_TYPES] = dict()
    devices: List[ALL_DEV_TYPES] = list()

    # legacy operations: this is from when area, zone and substation were strings,
    # now we create those objects on the fly
    on_the_fly = CreatedOnTheFly()

    # parse each object of the dataframe
    for i, row in main_df.iterrows():

        # create device
        idtag = row.get('idtag', None)
        elm = type(template_elm)(idtag=idtag)
        elm.disable_auto_updates()

        # ensure the profiles existence
        if time_profile is None or time_profile is pd.NaT:
            nt = 0
        else:
            nt = len(time_profile)
            if nt > 0:
                elm.ensure_profiles_exist(index=time_profile)

        # parse each property of the row
        for property_name_, property_value in row.items():

            property_name = str(property_name_)

            if property_name != 'idtag':  # idtag was set already
                gc_prop: GCProp = look_for_property(elm=elm, property_name=property_name)
                if gc_prop is not None:

                    if valid_value(property_value):

                        if gc_prop.has_profile():
                            prof = elm.get_profile(magnitude=gc_prop.name)
                            if 0 < nt != prof.size():
                                prof.resize(nt)
                        else:
                            prof = None

                        # the property of the file exists, parse it
                        if isinstance(gc_prop.tpe, DeviceType):

                            # we must look for the reference in elements_dict
                            collection = elements_dict_by_type.get(gc_prop.tpe, None)

                            if collection is not None:
                                ref_idtag = str(property_value)
                                ref_elm = collection.get(ref_idtag, None)

                                if ref_elm is not None:
                                    elm.set_snapshot_value(gc_prop.name, ref_elm)

                                    if gc_prop.has_profile():
                                        prof.fill(ref_elm)

                                else:

                                    # legacy operations: this is from when grids referenced buses by name
                                    if gc_prop.name in ['bus_from', 'bus_to', 'bus']:
                                        ref_elm = look_in_collection_by_name(key=ref_idtag, collection=collection)
                                        if ref_elm is None:
                                            could_not_fix_it = True
                                        else:
                                            could_not_fix_it = False

                                            elm.set_snapshot_value(gc_prop.name, ref_elm)

                                            if gc_prop.has_profile():
                                                prof.fill(ref_elm)
                                    else:
                                        could_not_fix_it = True

                                    if could_not_fix_it:
                                        logger.add_error("Could not locate reference",
                                                         device=row.get('idtag', 'not provided'),
                                                         device_class=template_elm.device_type.value,
                                                         device_property=gc_prop.name,
                                                         value=ref_idtag)
                            else:

                                # legacy operations: this is from when area, zone and substation were strings
                                if gc_prop.name == 'area':

                                    if str(property_value).strip() != '':
                                        area = on_the_fly.get_create_area(property_value=str(property_value))
                                        elm.set_snapshot_value(gc_prop.name, area)

                                elif gc_prop.name == 'zone':

                                    if str(property_value).strip() != '':
                                        zone = on_the_fly.get_create_zone(property_value=str(property_value))
                                        elm.set_snapshot_value(gc_prop.name, zone)

                                elif gc_prop.name == 'substation':

                                    if str(property_value).strip() != '':
                                        substation = on_the_fly.get_create_substation(
                                            property_value=str(property_value))
                                        elm.set_snapshot_value(gc_prop.name, substation)
                                elif gc_prop.name == 'template' and property_value == 'BranchTemplate':
                                    # skip this
                                    pass
                                else:

                                    logger.add_error("No device of the referenced type",
                                                     device=row.get('idtag', 'not provided'),
                                                     device_class=template_elm.device_type.value,
                                                     device_property=gc_prop.name,
                                                     value=property_value)

                        elif isinstance(gc_prop.tpe, SubObjectType):

                            if gc_prop.tpe == SubObjectType.GeneratorQCurve:
                                q_curve: devices.GeneratorQCurve = elm.get_snapshot_value(gc_prop)

                                if isinstance(property_value, str):
                                    q_curve.parse(json.loads(property_value))
                                else:
                                    q_curve.parse(property_value)

                        elif gc_prop.tpe == str:
                            # set the value directly
                            elm.set_snapshot_value(gc_prop.name, str(property_value))

                            if gc_prop.has_profile():
                                prof.fill(str(property_value))

                        elif gc_prop.tpe == float:
                            # set the value directly
                            elm.set_snapshot_value(gc_prop.name, float(property_value))

                            if gc_prop.has_profile():
                                prof.fill(float(property_value))

                        elif gc_prop.tpe == int:
                            # set the value directly
                            elm.set_snapshot_value(gc_prop.name, int(property_value))

                            if gc_prop.has_profile():
                                prof.fill(int(property_value))

                        elif gc_prop.tpe == bool:
                            # set the value directly
                            elm.set_snapshot_value(gc_prop.name, bool(property_value))

                            if gc_prop.has_profile():
                                prof.fill(bool(property_value))

                        elif isinstance(gc_prop.tpe, EnumType):
                            val, ok = set_enum_snapshot_value(elm=elm,
                                                              gc_prop=gc_prop,
                                                              property_value=property_value,
                                                              logger=logger)
                            if ok and gc_prop.has_profile():
                                prof.fill(val)

                        else:
                            raise Exception(f'Unsupported property type: {gc_prop.tpe}')

                    else:
                        # invalid property value
                        pass

                    # search the profiles in the data and assign them
                    if gc_prop.has_profile() and time_profile is not None:

                        # build the profile property file-name to get it from the data
                        profile_key = object_type_key + '_' + gc_prop.profile_name

                        # get the profile DataFrame
                        dfp = data.get(profile_key, None)

                        if dfp is not None:
                            try:
                                elm.set_profile(gc_prop, arr=dfp.values[:, i].astype(gc_prop.tpe))
                            except TypeError:
                                logger.add_error(msg="Cannot set profile value",
                                                 device_property=gc_prop.profile_name,
                                                 device=elm.name)

                        else:
                            skip = False
                            if gc_prop.name == 'bus':
                                skip = True

                            if not skip:
                                logger.add_info(msg='No profile for the property', value=gc_prop.name)

                else:
                    # The property exists under neither its current nor legacy name.
                    skip = False
                    if template_elm.device_type == DeviceType.ShuntDevice:
                        if property_name in ['is_controlled', 'Bmin', 'Bmax', 'Vset']:
                            skip = True

                    if template_elm.device_type == DeviceType.Transformer2WDevice:
                        if property_name == 'control_mode':
                            if "Pf" in property_value:
                                elm.tap_phase_control_mode = TapPhaseControl.Pf
                                skip = True
                            if "Pt" in property_value:
                                elm.tap_phase_control_mode = TapPhaseControl.Pt
                                skip = True
                            if "V" in property_value:
                                elm.tap_module_control_mode = TapModuleControl.Vm
                                elm.regulation_bus = elm.bus_to
                                skip = True
                            if "Qf" in property_value:
                                elm.tap_module_control_mode = TapModuleControl.Qf
                                skip = True
                            if "Qt" in property_value:
                                elm.tap_module_control_mode = TapModuleControl.Qt
                                skip = True
                            if "fixed" in property_value:
                                elm.tap_module_control_mode = TapModuleControl.fixed
                                elm.tap_phase_control_mode = TapPhaseControl.fixed
                                skip = True

                    if property_name == 'contingency_enabled':
                        # this is a branch with the legacy property "contingency_enabled", hence, create a contingency
                        on_the_fly.create_contingency(elm=elm)
                        skip = True

                    elif property_name == 'technology':
                        on_the_fly.create_technology(elm=elm, tech_name=property_value)
                        skip = True

                    if not skip:
                        logger.add_warning("Property in the file is not found in the model",
                                           device=row.get('idtag', 'not provided'),
                                           device_class=template_elm.device_type.value,
                                           device_property=property_name)

        # save the element in the dictionary for later
        devices_dict[elm.idtag] = elm
        devices.append(elm)

    return devices, devices_dict, on_the_fly


def search_property_into_json(json_entry: dict, prop: GCProp):
    """
    Find a property in one JSON entry.
    :param json_entry: JSON declaration for one object.
    :param prop: GCProp
    :return: value or None if not found
    """

    # search for the main property
    property_value = json_entry.get(prop.name, None)

    if property_value is None:

        # if not found, search for an old property
        for p_name in prop.old_names:
            property_value = json_entry.get(p_name, None)
            if property_value is not None:
                return property_value

        # we couldn't find the property or the old names...
        return None

    else:

        # we found the property at first
        return property_value


def set_enum_snapshot_value(elm: ALL_DEV_TYPES,
                            gc_prop: GCProp,
                            property_value: Any,
                            logger: Logger) -> tuple[Any, bool]:
    """
    Set one enum snapshot value, allowing property setters to translate legacy values.
    :return: (typed value, success)
    """
    try:
        val = gc_prop.tpe(property_value)
    except (TypeError, ValueError):
        try:
            elm.set_snapshot_value(gc_prop.name, property_value)
        except (TypeError, ValueError) as e:
            logger.add_error(f'Cannot cast the value to the snapshot',
                             device=elm.name,
                             value=property_value,
                             comment=str(e))
            return property_value, False

        val = elm.get_snapshot_value_by_name(gc_prop.name)
        if not isinstance(val, gc_prop.tpe):
            logger.add_error(f'Cannot cast the value to the snapshot',
                             device=elm.name,
                             value=property_value)
            return property_value, False
    else:
        try:
            elm.set_snapshot_value(gc_prop.name, val)
        except (TypeError, ValueError) as e:
            logger.add_error(f'Cannot set the snapshot',
                             device=elm.name,
                             value=property_value,
                             comment=str(e))
            return property_value, False

    return val, True


def search_and_apply_json_profile(json_entry: Dict[str, Dict[str, Union[str, Union[Any, Dict[str, Any]]]]],
                                  gc_prop: GCProp,
                                  elm: ALL_DEV_TYPES,
                                  property_value: Any,
                                  collection: Union[None, Dict[str, Any]] = None) -> None:
    """
    Find and apply property profiles declared in JSON.
    :param json_entry: JSON entry for one object.
    :param gc_prop: GCProp
    :param elm: THe device to set the profile into
    :param property_value: The snapshot value
    :param collection: if the collection is provided, it will be used to convert idtags into objects
    :return: None
    """
    if gc_prop.has_profile():

        # Resolve the profile from the JSON declaration.
        json_profile = json_entry.get(gc_prop.profile_name, None)

        profile: AnyProfile = elm.get_profile(magnitude=gc_prop.name)

        if json_profile is None:
            # the profile was not found, so we fill it with the default stuff
            profile.fill(property_value)
        else:
            get_profile_from_dict(profile=profile,
                                  data=json_profile,
                                  collection=collection)


def parse_object_type_from_json(template_elm: ALL_DEV_TYPES,
                                data_list: List[Dict[str, Dict[str, str]]],
                                elements_dict_by_type: Dict[DeviceType, Dict[str, ALL_DEV_TYPES]],
                                time_profile: pd.DatetimeIndex,
                                block_parser: BlockParser,
                                logger: Logger):
    """

    :param template_elm:
    :param data_list:
    :param elements_dict_by_type:
    :param time_profile:
    :param block_parser:
    :param logger:
    :return:
    """
    # dictionary to be filled with this type of objects
    devices_dict: Dict[str, ALL_DEV_TYPES] = dict()
    devices: List[ALL_DEV_TYPES] = list()

    for json_entry in data_list:
        idtag = json_entry['idtag']
        elm: ALL_DEV_TYPES = type(template_elm)(idtag=idtag)
        elm.disable_auto_updates()

        # ensure the profiles existence
        if time_profile is not None:
            elm.ensure_profiles_exist(index=time_profile)

        # for property_name_, property_value in json_entry.items():
        for property_name, gc_prop in template_elm.registered_properties.items():

            # Resolve the property from the JSON declaration.
            property_value = search_property_into_json(json_entry=json_entry, prop=gc_prop)

            if property_value is not None:

                if property_name != 'idtag':  # idtag was set already
                    # gc_prop: GCProp = look_for_property(elm=elm, property_name=property_name)

                    if gc_prop is not None:

                        if valid_value(property_value):

                            if isinstance(gc_prop.tpe, DeviceType):

                                if gc_prop.tpe == DeviceType.AnyLineTemplateDevice:
                                    # this is an exception, when dealing with line templates we need to look for
                                    # several types, not only one
                                    seq_templates = elements_dict_by_type.get(DeviceType.OverheadLineTypeDevice, dict())
                                    oh_templates = elements_dict_by_type.get(DeviceType.SequenceLineDevice, dict())
                                    ug_templates = elements_dict_by_type.get(DeviceType.UnderGroundLineDevice, dict())
                                    collection = {**seq_templates, **oh_templates, **ug_templates}

                                elif gc_prop.tpe == DeviceType.BusOrBranch:
                                    bus_dic = elements_dict_by_type.get(DeviceType.BusDevice, None)
                                    lines_dict = elements_dict_by_type.get(DeviceType.LineDevice, None)

                                    if bus_dic is not None and lines_dict is not None:
                                        collection = bus_dic | lines_dict
                                    elif bus_dic is not None and lines_dict is None:
                                        collection = bus_dic
                                    elif bus_dic is None and lines_dict is not None:
                                        collection = bus_dic
                                    else:
                                        collection = None
                                else:
                                    # this is a hyperlink to another object
                                    # we must look for the reference in elements_dict
                                    collection = elements_dict_by_type.get(gc_prop.tpe, None)

                                if collection is not None:
                                    ref_idtag = str(property_value)
                                    ref_elm = collection.get(ref_idtag, None)

                                    if ref_elm is not None:
                                        elm.set_snapshot_value(gc_prop.name, ref_elm)
                                        search_and_apply_json_profile(json_entry=json_entry,
                                                                      gc_prop=gc_prop,
                                                                      elm=elm,
                                                                      property_value=ref_elm,
                                                                      collection=collection)

                                    else:
                                        logger.add_error("Could not locate reference",
                                                         device=elm.idtag,
                                                         device_class=template_elm.device_type.value,
                                                         device_property=gc_prop.name,
                                                         value=ref_idtag)
                                else:
                                    logger.add_error("No device of the referenced type",
                                                     device=elm.idtag,
                                                     device_class=template_elm.device_type.value,
                                                     device_property=gc_prop.name,
                                                     value=property_value)

                            elif isinstance(gc_prop.tpe, SubObjectType):  # this is a hyperlink to another object

                                if gc_prop.tpe == SubObjectType.GeneratorQCurve:

                                    # Fill the curve object from its JSON declaration.
                                    q_curve: devices.GeneratorQCurve = elm.get_snapshot_value(prop=gc_prop)
                                    if isinstance(property_value, str):
                                        q_curve.parse(json.loads(property_value))
                                    else:
                                        q_curve.parse(data=property_value)

                                elif gc_prop.tpe == SubObjectType.LineLocations:

                                    # Fill the line locations from their JSON declaration.
                                    locations_obj: devices.LineLocations = elm.get_snapshot_value(prop=gc_prop)
                                    locations_obj.parse(property_value)

                                elif gc_prop.tpe == SubObjectType.ListOfWires:

                                    # Fill the wire collection from its JSON declaration.
                                    list_of_wires: devices.ListOfWires = elm.get_snapshot_value(prop=gc_prop)
                                    list_of_wires.parse(data=property_value,
                                                        wire_dict=elements_dict_by_type[DeviceType.WireDevice])


                                elif gc_prop.tpe == SubObjectType.ImpedanceTripletList:

                                    # Fill the impedance triplets from their JSON declaration.
                                    impedance_triplet_list: devices.ImpedanceTripletList = elm.get_snapshot_value(
                                        prop=gc_prop)
                                    impedance_triplet_list.parse(data=property_value)

                                elif gc_prop.tpe == SubObjectType.TapChanger:

                                    # Fill the tap changer from its JSON declaration.
                                    tc_obj: devices.TapChanger = elm.get_snapshot_value(prop=gc_prop)
                                    tc_obj.parse(property_value, logger=logger)

                                elif gc_prop.tpe == SubObjectType.Array:

                                    val = np.array(property_value)
                                    elm.set_snapshot_value(gc_prop.name, val)

                                elif gc_prop.tpe == SubObjectType.AdmittanceMatrix:

                                    # Fill the admittance matrix from its JSON declaration.
                                    adm_mat: devices.AdmittanceMatrix = elm.get_snapshot_value(prop=gc_prop)
                                    adm_mat.parse(property_value)

                                elif gc_prop.tpe == SubObjectType.DaeBlockType:

                                    # handle the ModelHost
                                    if isinstance(property_value, dict):

                                        key = property_value.get("model", None)
                                        if key is None:
                                            logger.add_error("Could not locate model", value=property_value)
                                        else:
                                            blk = block_parser.block_dict.get(key, None)
                                            elm.set_snapshot_value(gc_prop.name, blk)
                                    else:
                                        blk = block_parser.block_dict.get(property_value, None)
                                        if blk is None:
                                            logger.add_error("Block not found",
                                                             device=elm.name,
                                                             value=property_value,
                                                             device_class=elm.device_type.value,
                                                             device_property=gc_prop.name
                                                             )
                                        else:
                                            elm.set_snapshot_value(gc_prop.name, blk)


                                elif gc_prop.tpe == SubObjectType.VarType:

                                    # set the value of the property
                                    vl = block_parser.var_factory.get_var(property_value)
                                    elm.set_snapshot_value(gc_prop.name, vl)

                                elif gc_prop.tpe == SubObjectType.ConstType:

                                    # set the value of the property
                                    vl = block_parser.var_factory.get_const(property_value)
                                    elm.set_snapshot_value(gc_prop.name, vl)

                                elif gc_prop.tpe == SubObjectType.Associations:

                                    # get the list of associations
                                    associations = elm.get_snapshot_value(gc_prop)
                                    associations.parse(
                                        data=property_value,
                                        elements_dict=elements_dict_by_type.get(associations.device_type, {}),
                                        logger=logger,
                                        elm_name=elm.name
                                    )

                                elif gc_prop.tpe == SubObjectType.MergeInformation:
                                    # set the value directly
                                    elm.diff_changes.parse(property_value)

                                else:
                                    raise Exception(f"SubObjectType {gc_prop.tpe} not implemented")

                            elif gc_prop.tpe == str:
                                # set the value directly
                                val = str(property_value)
                                elm.set_snapshot_value(gc_prop.name, val)
                                search_and_apply_json_profile(json_entry=json_entry,
                                                              gc_prop=gc_prop,
                                                              elm=elm,
                                                              property_value=val)

                            elif gc_prop.tpe == float:
                                # set the value directly
                                val = float(property_value)
                                elm.set_snapshot_value(gc_prop.name, val)
                                search_and_apply_json_profile(json_entry=json_entry,
                                                              gc_prop=gc_prop,
                                                              elm=elm,
                                                              property_value=val)

                            elif gc_prop.tpe == int:
                                # set the value directly
                                val = int(property_value)
                                elm.set_snapshot_value(gc_prop.name, val)
                                search_and_apply_json_profile(json_entry=json_entry,
                                                              gc_prop=gc_prop,
                                                              elm=elm,
                                                              property_value=val)

                            elif gc_prop.tpe == bool:
                                # set the value directly
                                val = bool(property_value)
                                elm.set_snapshot_value(gc_prop.name, val)
                                search_and_apply_json_profile(json_entry=json_entry,
                                                              gc_prop=gc_prop,
                                                              elm=elm,
                                                              property_value=val)

                            elif isinstance(gc_prop.tpe, EnumType):
                                val, ok = set_enum_snapshot_value(elm=elm,
                                                                  gc_prop=gc_prop,
                                                                  property_value=property_value,
                                                                  logger=logger)
                                if ok:
                                    try:
                                        search_and_apply_json_profile(json_entry=json_entry,
                                                                      gc_prop=gc_prop,
                                                                      elm=elm,
                                                                      property_value=val)

                                    except ValueError as e:
                                        logger.add_error(f'Cannot set the profile',
                                                         device=elm.name,
                                                         value=property_value,
                                                         comment=str(e))

                            else:
                                raise Exception(f'Unsupported property type: {gc_prop.tpe} for {gc_prop.name}')

                        else:
                            # invalid property value
                            pass
                    else:
                        # property not found
                        pass

                else:
                    # the property is idtag
                    pass
            else:
                # The object property was not present in the JSON entry.
                pass

        if template_elm.device_type == DeviceType.Transformer3WDevice:
            for property_name in ('r12', 'r23', 'r31', 'x12', 'x23', 'x31', 'rate1', 'rate2', 'rate3'):
                gc_prop = template_elm.registered_properties[property_name]
                property_value = search_property_into_json(json_entry=json_entry, prop=gc_prop)
                if property_value is not None:
                    elm.set_snapshot_value(gc_prop.name, float(property_value))

        if template_elm.device_type == DeviceType.LineDevice:
            gc_prop = template_elm.registered_properties.get('length', None)
            if gc_prop is not None:
                property_value = search_property_into_json(json_entry=json_entry, prop=gc_prop)
                if property_value is not None and float(property_value) == 0.0:
                    elm._length = 0.0

        # save the element in the dictionary for later
        devices_dict[elm.idtag] = elm
        devices.append(elm)
    return devices, devices_dict


def handle_legacy_jsons(model_data: Dict[str, List],
                        elements_dict_by_type: Dict[DeviceType, Dict],
                        logger: Logger) -> None:
    """
    Handle those legacy structures that were deprecated and removed from VeraGrid's structure
    :param model_data:
    :param elements_dict_by_type:
    :param logger:
    :return:
    """
    gt_data_list = model_data.get("generator_technology", None)
    if gt_data_list is not None:
        for entry in gt_data_list:
            gen_idtag = entry.get('generator', None)
            tech_idtag = entry.get('technology', None)
            proportion = entry.get('proportion', 1.0)
            generator = elements_dict_by_type[DeviceType.GeneratorDevice].get(gen_idtag, None)
            tech = elements_dict_by_type[DeviceType.Technology].get(tech_idtag, None)
            if generator is not None and tech is not None:
                generator.technologies.add_object(api_object=tech, val=proportion)
                logger.add_info("Converted legacy generator technology association",
                                device_class="Generator_technology",
                                value=f"{generator.name} -> {tech.name} at {proportion}")

    gf_data_list = model_data.get("generator_fuel", None)
    if gf_data_list is not None:
        for entry in gf_data_list:
            gen_idtag = entry.get('generator', None)
            fuel_idtag = entry.get('fuel', None)
            rate = entry.get('rate', 1.0)
            generator = elements_dict_by_type[DeviceType.GeneratorDevice].get(gen_idtag, None)
            fuel = elements_dict_by_type[DeviceType.FuelDevice].get(fuel_idtag, None)
            if generator is not None and fuel is not None:
                generator.fuels.add_object(api_object=fuel, val=rate)
                logger.add_info("Converted legacy generator fuel association",
                                device_class="generator_fuel",
                                value=f"{generator.name} -> {fuel.name} at {rate}")

    ge_data_list = model_data.get("generator_emission", None)
    if ge_data_list is not None:
        for entry in ge_data_list:
            gen_idtag = entry.get('generator', None)
            emission_idtag = entry.get('emission', None)
            rate = entry.get('rate', 1.0)
            generator = elements_dict_by_type[DeviceType.GeneratorDevice].get(gen_idtag, None)
            emission = elements_dict_by_type[DeviceType.EmissionGasDevice].get(emission_idtag, None)
            if generator is not None and emission is not None:
                generator.emissions.add_object(api_object=emission, val=rate)
                logger.add_info("Converted legacy generator emission association",
                                device_class="generator_emission",
                                value=f"{generator.name} -> {emission.name} at {rate}")


def parse_veragrid_data(data: VERAGRID_FILE_TYPE,
                        previous_circuit: Union[MultiCircuit, None] = None,
                        project_directory: str | Path | None = None,
                        refine_pointers: bool = True,
                        text_func: Union[Callable, None] = None,
                        progress_func: Union[Callable, None] = None,
                        logger: Logger = Logger()) -> MultiCircuit:
    """
    Interpret data
    :param project_directory: file project directory
    :param refine_pointers: Refine (and possibly delete) the pointer objects such as investments and contingencies?
    :param data: dictionary of data frames and other information
    :param previous_circuit: Optional previous VeraGrid circuit. This is relevant in case of loading grid increments
    :param text_func: text callback function
    :param progress_func: progress callback function
    :param logger: Logger to register events
    :return: MultiCircuit instance
    """
    # create circuit
    circuit = MultiCircuit()

    # Legacy circuit information parsing -------------------------------------------------------------------------------
    if 'name' in data.keys():
        circuit.name = str(data['name'])
        if circuit.name == 'nan':
            circuit.name = ''

    if 'idtag' in data.keys():
        val = str(data['idtag'])
        if val != '':
            circuit.idtag = val
        else:
            logger.add_warning("Had to create a new idtag", value=circuit.idtag)

    # set the base magnitudes
    if 'baseMVA' in data.keys():
        circuit.Sbase = data['baseMVA']

    # Set comments
    if 'Comments' in data.keys():
        circuit.comments = str(data['Comments'])
        if circuit.comments == 'nan':
            circuit.comments = ''

    if 'ModelVersion' in data.keys():
        circuit.model_version = int(data['ModelVersion'])

    if 'UserName' in data.keys():
        circuit.user_name = data['UserName']

    # dictionary of objects to iterate
    template_object_types = get_objects_dictionary()

    # time profile -----------------------------------------------------------------------------------------------------
    if 'time' in data.keys():
        time_df = data['time']
        try:
            circuit.time_profile = pd.to_datetime(time_df.values[:, 0], dayfirst=True, format='mixed')
        except ValueError:
            circuit.time_profile = pd.to_datetime(time_df.values[:, 0], dayfirst=True)
    else:
        circuit.time_profile = None

    # dictionary of dictionaries by element type
    if previous_circuit is None:
        elements_dict_by_type = dict()
    else:
        elements_dict_by_type = previous_circuit.get_all_elements_dict_by_type(add_locations=True, string_keys=False)

    # ------------------------------------------------------------------------------------------------------------------
    # Legacy DataFrame processing
    # for each element type...
    item_count = 0
    n_data_types = len(template_object_types)
    for object_type_key, template_elm in template_object_types.items():

        if text_func is not None:
            text_func(f"Parsing {object_type_key} table data...")

        # try to get the DataFrame
        # Todo: here we should get the data from template_object_types dict, not from data dict
        df = data.get(object_type_key, None)

        if df is not None:

            # fill in the objects
            if df.shape[0] > 0:

                parsed_devices, devices_dict, on_the_fly = parse_object_type_from_dataframe(
                    main_df=df,
                    template_elm=template_elm,
                    elements_dict_by_type=elements_dict_by_type,
                    time_profile=circuit.time_profile,
                    object_type_key=object_type_key,
                    data=data,
                    logger=logger
                )

                # add the elements that were created on the fly...
                for name, on_the_fly_elm in on_the_fly.legacy_area_dict.items():
                    circuit.add_area(obj=on_the_fly_elm)
                for name, on_the_fly_elm in on_the_fly.legacy_zone_dict.items():
                    circuit.add_zone(obj=on_the_fly_elm)
                for name, on_the_fly_elm in on_the_fly.legacy_substation_dict.items():
                    circuit.add_substation(obj=on_the_fly_elm)
                for conn_group in on_the_fly.contingency_groups:
                    circuit.add_contingency_group(obj=conn_group)
                for cont in on_the_fly.contingencies:
                    circuit.add_contingency(obj=cont)
                for tech_name, technology in on_the_fly.technologies.items():
                    circuit.add_technology(obj=technology)

                # set/augment the dictionary per type for later
                prev_dict = elements_dict_by_type.get(template_elm.device_type, dict())
                elements_dict_by_type[template_elm.device_type] = dict(prev_dict, **devices_dict)

                # add the devices to the circuit
                circuit.set_elements_list_by_type(device_type=template_elm.device_type,
                                                  devices=parsed_devices,
                                                  logger=logger)

            else:
                # no objects of this type
                pass
        else:
            # the file does not contain information for the data type (not a problem...)
            pass

        if progress_func is not None:
            progress_func(float(item_count + 1) / float(n_data_types) * 100)

        item_count += 1

    # ------------------------------------------------------------------------------------------------------------------
    # Parse the declarative information stored in JSON ``.model`` files.
    # These files are just .json stored in the model_data inside the zip file

    block_parser = BlockParser(
        var_factory=circuit.var_factory,
        logger=logger,
        procedural_logic_codec=ProceduralLogicCodec(),
    )
    symbolic_data: Dict[str, Any] | None = data.get('symbolic_data', None)
    if symbolic_data is not None:
        if len(symbolic_data) > 0:
            if "shared_references" in symbolic_data:
                block_parser.parse_references(symbolic_data["shared_references"])
            block_parser.parse_consts(symbolic_data["consts"])
            block_parser.parse_vars(symbolic_data["vars"])
            block_parser.parse_diff_vars(symbolic_data["diff_vars"])
            if "connections" in symbolic_data:
                block_parser.parse_connections(symbolic_data["connections"])
            # BlockParser owns compatibility with all historical dynamics
            # containers, including list-based tables, inline children and
            # archives created before main_block_uids existed.
            block_parser.parse_blocks(blocks_data=symbolic_data.get("blocks", dict()),
                                      main_block_uids=symbolic_data.get("main_block_uids", None))
        else:
            pass  # the symbolic data is empty
    else:
        pass  # there is no symbolic data records

    model_data = data.get('model_data', None)
    if model_data is not None:

        if len(model_data) > 0:

            # parse circuit own data
            circuit_data: Dict[str, str | int | float] | None = model_data.get('circuit', None)
            if circuit_data is not None:
                circuit.parse(data=circuit_data)

            # parse time
            tdata = model_data.get('time', None)
            if tdata is not None:
                circuit.set_unix_time(arr=tdata['unix'])

                snapshot_unix_time = tdata.get('snapshot_unix', None)
                if snapshot_unix_time is not None:
                    circuit.set_snapshot_time_unix(val=snapshot_unix_time)

            else:
                logger.add_error(msg=f'The file must have time data regardless of the profiles existence')
                circuit.time_profile = None

            # for each element type...
            item_count = 0
            n_data_types = len(template_object_types)
            for object_type_key, template_elm in template_object_types.items():

                if text_func is not None:
                    text_func(f"Parsing {object_type_key} model data...")

                # query the device type into the data set
                data_list = model_data.get(object_type_key, None)

                if data_list is not None:
                    parsed_devices, devices_dict = parse_object_type_from_json(
                        template_elm=template_elm,
                        data_list=data_list,
                        elements_dict_by_type=elements_dict_by_type,
                        time_profile=circuit.time_profile,
                        block_parser=block_parser,
                        logger=logger
                    )

                    # set/augment the dictionary per type for later
                    prev_dict = elements_dict_by_type.get(template_elm.device_type, dict())
                    prev_dict.update(devices_dict)  # augment prev_dict with devices_dict
                    elements_dict_by_type[template_elm.device_type] = prev_dict

                    # add the devices to the circuit
                    circuit.set_elements_list_by_type(device_type=template_elm.device_type,
                                                      devices=parsed_devices,
                                                      logger=logger)
                else:
                    # Legacy and optional sections should not generate warnings when absent.
                    if object_type_key not in {'branch', 'fmu_template'}:
                        logger.add_warning(msg=f'No data for {object_type_key}')

                if progress_func is not None:
                    progress_func(float(item_count + 1) / float(n_data_types) * 100)

                item_count += 1

            # Handle the legacy objects that may be present in the data bus not declared in the program
            # i.e. generator_technology
            handle_legacy_jsons(model_data=model_data,
                                elements_dict_by_type=elements_dict_by_type,
                                logger=logger)

    # fill in device into pointer devices ------------------------------------------------------------------------------

    to_delete: List[ALL_DEV_TYPES] = list()
    all_elements_dict: Dict[str, ALL_DEV_TYPES] = dict()
    for dtype in [
        DeviceType.PiMeasurementDevice,
        DeviceType.QiMeasurementDevice,
        DeviceType.PfMeasurementDevice,
        DeviceType.QfMeasurementDevice,
        DeviceType.PtMeasurementDevice,
        DeviceType.QtMeasurementDevice,
        DeviceType.PgMeasurementDevice,
        DeviceType.QgMeasurementDevice,
        DeviceType.IfMeasurementDevice,
        DeviceType.ItMeasurementDevice,
        DeviceType.VaMeasurementDevice,
        DeviceType.VmMeasurementDevice,
        DeviceType.ContingencyDevice,
        DeviceType.InvestmentDevice,
        DeviceType.RemedialActionDevice,
        DeviceType.RmsEventDevice,
        DeviceType.EmtEventDevice,
        DeviceType.ShortCircuitEvent
    ]:
        elms = circuit.get_elements_by_type(device_type=dtype)

        for elm in elms:

            if elm.tpe != DeviceType.NoDevice:
                # search in the per-device type dictionary (already created and faster)
                referenced_dict = elements_dict_by_type[elm.tpe]
                referenced_elm = referenced_dict.get(elm.device_idtag, None)
            else:
                # lazy-creation of the all elements dict, takes time to initialize
                if len(all_elements_dict) == 0:
                    all_elements_dict, _ = circuit.get_all_elements_dict()
                referenced_elm = all_elements_dict.get(elm.device_idtag, None)

            if referenced_elm is None:
                to_delete.append(elm)
            else:
                elm.set_device(elm=referenced_elm)

    # Delete pointer elements that refer to missing objects.
    for elm in to_delete:
        circuit.delete_element(elm)
        logger.add_error(msg="Invalid pointer element deleted",
                         device_class=elm.device_type.value,
                         device=elm.name)

    # fill in wires into towers ----------------------------------------------------------------------------------------
    if text_func is not None:
        text_func("Tower wires...")
    if 'tower_wires' in data.keys():
        df = data['tower_wires']

        for i in range(df.shape[0]):
            tower_name = df['tower_name'].values[i]
            wire_name = df['wire_name'].values[i]

            if ((tower_name in elements_dict_by_type[DeviceType.OverheadLineTypeDevice].keys()) and
                    (wire_name in elements_dict_by_type[DeviceType.WireDevice].keys())):
                tower: devices.OverheadLineType = elements_dict_by_type[DeviceType.OverheadLineTypeDevice][tower_name]
                wire: devices.Wire = elements_dict_by_type[DeviceType.WireDevice][wire_name]
                xpos = df['xpos'].values[i]
                ypos = df['ypos'].values[i]
                phase = df['phase'].values[i]
                tower.add_wire_relationship(wire=wire, xpos=xpos, ypos=ypos, phase=phase)
    else:
        pass

    # create diagrams --------------------------------------------------------------------------------------------------
    if text_func is not None:
        text_func("Parsing diagrams...")

    # try to get the list of diagrams
    list_of_diagrams: List[Dict[str, Any]] = data.get('diagrams', None)

    if list_of_diagrams is not None:

        if len(list_of_diagrams):
            obj_dict = circuit.get_all_elements_dict_by_type(add_locations=True)

            for diagram_dict in list_of_diagrams:

                if diagram_dict['type'] in [DiagramType.Schematic.value, "bus-branch"]:
                    diagram = devices.SchematicDiagram()
                    diagram.parse_data(data=diagram_dict, obj_dict=obj_dict, logger=logger)
                    circuit.add_diagram(diagram)

                elif diagram_dict['type'] == DiagramType.SubstationLineMap.value:
                    diagram = devices.MapDiagram()
                    diagram.parse_data(data=diagram_dict, obj_dict=obj_dict, logger=logger)
                    circuit.add_diagram(diagram)
                else:
                    print('unrecognized diagram', diagram_dict['type'])

    if text_func is not None:
        text_func("Done!")

    # search contingencies, investments and remedial actions pointed devices
    # and remove those that point nowhere
    if refine_pointers:
        circuit.refine_pointer_objects(logger=logger)

    if circuit.has_time_series:
        circuit.ensure_profiles_exist()

    resolved_project_directory: Path | None
    if project_directory is None:
        resolved_project_directory = None
    else:
        resolved_project_directory = Path(project_directory)
    _resolve_circuit_fmu_paths(circuit, resolved_project_directory)

    # Enable auto updates internally only after everything has been filled
    for elm in circuit.get_all_elements_iter():
        elm.enable_auto_updates()

    return circuit


def parse_multiverse_data(data: Dict[str, VERAGRID_FILE_TYPE],
                          metadata: Dict[str, Dict[str, int | float] | int | None],
                          text_func: Union[Callable, None] = None,
                          progress_func: Union[Callable, None] = None,
                          logger: Logger = Logger()) -> devices.MultiVerse:
    """

    :param data:
    :param metadata:
    :param text_func:
    :param progress_func:
    :param logger:
    :return:
    """
    mv = devices.MultiVerse(current_model=None)

    diffs_dict: Dict[str, MultiCircuit] = dict()
    diagrams_dict: Dict[str, List[Dict[str, Any]]] = dict()
    composed_by_node_id: Dict[int, MultiCircuit] = dict()

    # IMPORTANT:
    # Multiverse node payloads are not all full circuits.
    #
    # - Root nodes store a full authoritative MultiCircuit.
    # - Non-root nodes store only the electrical delta against their parent.
    #
    # This has two non-obvious effects on loading:
    #
    # 1. Electrical references in child payloads may legitimately point to objects that are
    #    not present in the child's delta payload, because those objects live in the parent /
    #    ancestor composed circuit. Example: a child adds a new line whose bus_to points to a
    #    bus inherited from the parent scenario. If the child payload were parsed in isolation,
    #    that reference would fail with "Could not locate reference".
    #
    # 2. Node-owned diagrams are full scenario diagrams, not diagram deltas. A child diagram may
    #    therefore reference both child-owned and inherited parent-owned API objects. Parsing such
    #    diagrams against the raw child delta payload would also fail.
    #
    # Because of that, multiverse loading must happen in two phases:
    # - First parse the electrical payloads in parent-before-child order, passing the fully composed
    #   parent circuit as previous_circuit so child references to inherited objects can be resolved.
    # - Then, after the tree exists, parse each node's diagrams against that node's full composed
    #   scenario, never against the raw delta payload.
    node_metadata = get_multiverse_node_metadata(metadata)
    ordered_records = order_multiverse_records(metadata)
    all_elements_dict: Dict[str, ALL_DEV_TYPES] = dict()

    for record in ordered_records:
        node_id = int(record["node_id"])
        circuit_idtag = str(record["circuit_idtag"])
        parent_id_raw = record["parent_id"]
        parent_id = None if parent_id_raw is None else int(parent_id_raw)

        multiverse_data = data.get("multiverse", None)
        if multiverse_data is not None:
            model_data = multiverse_data.get(circuit_idtag, None)

            if model_data is not None:
                diagrams_dict[circuit_idtag] = model_data.get("diagrams", list())

                model_without_diagrams = dict(model_data)
                model_without_diagrams["diagrams"] = list()

                previous_circuit = None if parent_id is None else composed_by_node_id[parent_id]

                grid = parse_veragrid_data(data=model_without_diagrams,
                                           previous_circuit=previous_circuit,
                                           refine_pointers=False,
                                           text_func=text_func,
                                           progress_func=progress_func,
                                           logger=logger)

                # we create a dictionary of all the elements in all the scenarios such that finding pointers doesn't fail later
                d, ok = grid.get_all_elements_dict(logger=logger)
                all_elements_dict.update(d)

                grid.idtag = circuit_idtag
                diffs_dict[circuit_idtag] = grid

                if parent_id is None:
                    composed_by_node_id[node_id] = grid.copy()
                else:
                    composed = composed_by_node_id[parent_id].copy()
                    composed.merge_circuit(grid)
                    composed.name = grid.name
                    composed_by_node_id[node_id] = composed
            else:
                # model_data is None
                pass
        else:
            # multiverse is None
            pass

    # Refine pointer in all grids
    for idtag, grid in diffs_dict.items():
        grid.refine_pointer_objects(logger=logger, all_elements_dict=all_elements_dict)

    # Parse the multiverse data
    try:
        mv.parse_json(diffs_dict=diffs_dict, metadata=metadata)
    except ValueError as e:
        logger.add_error(str(e))

    # Parse diagrams only after the multiverse tree exists, so each node can resolve them
    # against its full composed scenario instead of its raw delta payload.
    for record in node_metadata.values():
        node_id = int(record["node_id"])
        circuit_idtag = str(record["circuit_idtag"])
        if mv.check_node(node_id):
            node = mv.get_node(node_id)
            full_circuit = mv.checkout(node)
            obj_dict = full_circuit.get_all_elements_dict_by_type(add_locations=True)
            parsed_diagrams: List[Any] = list()

            for diagram_dict in diagrams_dict.get(circuit_idtag, list()):
                if diagram_dict['type'] in [DiagramType.Schematic.value, "bus-branch"]:
                    diagram = devices.SchematicDiagram()
                    diagram.parse_data(data=diagram_dict, obj_dict=obj_dict, logger=logger)
                    parsed_diagrams.append(diagram)

                elif diagram_dict['type'] == DiagramType.SubstationLineMap.value:
                    diagram = devices.MapDiagram()
                    diagram.parse_data(data=diagram_dict, obj_dict=obj_dict, logger=logger)
                    parsed_diagrams.append(diagram)

            node.diagrams = parsed_diagrams
        else:
            logger.add_error("Node ID not found", value=str(node_id))

    if isinstance(metadata, dict):
        active_node_id_raw: int = metadata.get("active_node_id", -1)
        if mv.current_node is not None and mv.current_model is not None:
            obj_dict = mv.current_model.get_all_elements_dict_by_type(add_locations=True)
            mv.current_model.diagrams = copy_diagrams(diagrams=mv.current_node.diagrams, obj_dict=obj_dict)

        if (active_node_id_raw > -1
                and (mv.current_node is None or mv.current_node.node_id != int(active_node_id_raw))):
            if mv.check_node(active_node_id_raw):
                mv.activate_scenario(int(active_node_id_raw))

    return mv
