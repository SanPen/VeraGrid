# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import zipfile
from io import BytesIO
from datetime import datetime, timezone
from uuid import uuid4
from rdflib import OWL
from rdflib.graph import Graph
from rdflib.namespace import RDF, RDFS
from typing import List

import json
import os
from VeraGridEngine.IO.cim.cgmes.cgmes_circuit import CgmesCircuit
from VeraGridEngine.IO.cim.cgmes.rdfs_serializations import RDFS_serialization_2_4_15, RDFS_serialization_3_0_0
from VeraGridEngine.IO.cim.cgmes.rdfs_infos import RDFS_INFO_2_4_15, RDFS_INFO_3_0_0
from VeraGridEngine.IO.cim.cgmes.cgmes_enums import CgmesProfileType
from VeraGridEngine.enumerations import CGMESVersions
import xml.etree.ElementTree as Et
import xml.dom.minidom
from enum import Enum


def get_available_cgmes_profiles(cgmes_version: CGMESVersions):
    if cgmes_version == CGMESVersions.v2_4_15:
        return {
            "EQ": ["http://entsoe.eu/CIM/EquipmentCore/3/1",
                   "http://entsoe.eu/CIM/EquipmentShortCircuit/3/1",
                   "http://entsoe.eu/CIM/EquipmentOperation/3/1"],
            "SSH": ["http://entsoe.eu/CIM/SteadyStateHypothesis/1/1"],
            "TP": ["http://entsoe.eu/CIM/Topology/4/1"],
            "SV": ["http://entsoe.eu/CIM/StateVariables/4/1"],
            "GL": ["http://entsoe.eu/CIM/GeographicalLocation/2/1"]
        }
    elif cgmes_version == CGMESVersions.v3_0_0:
        return {
            "EQ": ["http://iec.ch/TC57/ns/CIM/CoreEquipment-EU/3.0"],
            "EQ_BD": ["http://iec.ch/TC57/ns/CIM/EquipmentBoundary-EU/3.0"],
            "OP": ["http://iec.ch/TC57/ns/CIM/Operation-EU/3.0"],
            "SC": ["http://iec.ch/TC57/ns/CIM/ShortCircuit-EU/3.0"],
            "SSH": ["http://iec.ch/TC57/ns/CIM/SteadyStateHypothesis-EU/3.0"],
            "TP": ["http://iec.ch/TC57/ns/CIM/Topology-EU/3.0"],
            "TP_BD": ["http://iec.ch/TC57/ns/CIM/TopologyBoundary-EU/3.0"],
            "SV": ["http://iec.ch/TC57/ns/CIM/StateVariables-EU/3.0"],
            "GL": ["http://iec.ch/TC57/ns/CIM/GeographicalLocation-EU/3.0"],
            "CO": ["https://ap.cim4.eu/Contingency/2.3"]
        }
    else:
        print(f"CGMES Version not suported {cgmes_version.value}")
        return dict()


class CimExporter:
    def __init__(self, cgmes_circuit: CgmesCircuit, profiles_to_export: List[CgmesProfileType], one_file_per_profile: bool):
        self.cgmes_circuit = cgmes_circuit

        self.profiles_to_export = profiles_to_export
        self.one_file_per_profile = one_file_per_profile
        self.export_OP = False
        self.export_SC = False

        current_directory = os.path.dirname(__file__)

        rdf_serialization = Graph()

        if cgmes_circuit.cgmes_version == CGMESVersions.v2_4_15:
            rdf_serialization.parse(data=RDFS_serialization_2_4_15, format="ttl")

            if CgmesProfileType.OP in profiles_to_export:
                self.export_OP = True
            if CgmesProfileType.SC in profiles_to_export:
                self.export_SC = True

            self.namespaces = {
                "xmlns:cim": "http://iec.ch/TC57/2013/CIM-schema-cim16#",
                "xmlns:md": "http://iec.ch/TC57/61970-552/ModelDescription/1#",
                "xmlns:entsoe": "http://entsoe.eu/CIM/SchemaExtension/3/1#",
                "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            }
            self.profile_uris = get_available_cgmes_profiles(cgmes_version=cgmes_circuit.cgmes_version)

            self.enum_dict = dict()
            self.about_dict = dict()
            for s_i, p_i, o_i in rdf_serialization.triples((None, RDF.type, RDFS.Class)):
                if str(s_i).split("#")[1] == "RdfEnum":
                    enum_list_dict = dict()
                    for s, p, o in rdf_serialization.triples((s_i, OWL.members, None)):
                        enum_list_dict[str(o).split("#")[-1]] = str(o)
                    if str(s_i).split("#")[0] == "http://entsoe.eu/CIM/EquipmentCore/3/1":
                        self.enum_dict["EQ"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/StateVariables/4/1":
                        self.enum_dict["SV"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/SteadyStateHypothesis/1/1":
                        self.enum_dict["SSH"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/Topology/4/1":
                        self.enum_dict["TP"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/GeographicalLocation/2/1":
                        self.enum_dict["GL"] = enum_list_dict
                if str(s_i).split("#")[1] == "RdfAbout":
                    about_list = list()
                    for s, p, o in rdf_serialization.triples((s_i, OWL.members, None)):
                        about_list.append(str(o).split("#")[-1])
                    if str(s_i).split("#")[0] == "http://entsoe.eu/CIM/EquipmentCore/3/1":
                        self.about_dict["EQ"] = about_list
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/StateVariables/4/1":
                        self.about_dict["SV"] = about_list
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/SteadyStateHypothesis/1/1":
                        self.about_dict["SSH"] = about_list
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/Topology/4/1":
                        self.about_dict["TP"] = about_list
                    elif str(s_i).split("#")[0] == "http://entsoe.eu/CIM/GeographicalLocation/2/1":
                        self.about_dict["GL"] = about_list

            self.class_filters = {}
            json_dict = json.loads(RDFS_INFO_2_4_15)
        elif cgmes_circuit.cgmes_version == CGMESVersions.v3_0_0:
            rdf_serialization.parse(data=RDFS_serialization_3_0_0, format="ttl")

            self.namespaces = {
                "xmlns:cim": "http://iec.ch/TC57/CIM100#",
                "xmlns:md": "http://iec.ch/TC57/61970-552/ModelDescription/1#",
                "xmlns:eu": "http://iec.ch/TC57/CIM100-European#",
                "xmlns:rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            }
            self.profile_uris = get_available_cgmes_profiles(cgmes_version=cgmes_circuit.cgmes_version)

            self.enum_dict = dict()
            self.about_dict = dict()
            for s_i, p_i, o_i in rdf_serialization.triples((None, RDF.type, RDFS.Class)):
                if str(s_i).split("#")[1] == "RdfEnum":
                    enum_list_dict = dict()
                    for s, p, o in rdf_serialization.triples((s_i, OWL.members, None)):
                        enum_list_dict[str(o).split("#")[-1]] = str(o)
                    if str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/CoreEquipment-EU/3.0":
                        self.enum_dict["EQ"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/StateVariables-EU/3.0":
                        self.enum_dict["SV"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/SteadyStateHypothesis-EU/3.0":
                        self.enum_dict["SSH"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/Topology-EU/3.0":
                        self.enum_dict["TP"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/ShortCircuit-EU/3.0":
                        self.enum_dict["SC"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/Operation-EU/3.0":
                        self.enum_dict["OP"] = enum_list_dict
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/GeographicalLocation-EU/3.0":
                        self.enum_dict["GL"] = enum_list_dict
                if str(s_i).split("#")[1] == "RdfAbout":
                    about_list = list()
                    for s, p, o in rdf_serialization.triples((s_i, OWL.members, None)):
                        about_list.append(str(o).split("#")[-1])
                    if str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/CoreEquipment-EU/3.0":
                        self.about_dict["EQ"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/StateVariables-EU/3.0":
                        self.about_dict["SV"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/SteadyStateHypothesis-EU/3.0":
                        self.about_dict["SSH"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/Topology-EU/3.0":
                        self.about_dict["TP"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/ShortCircuit-EU/3.0":
                        self.about_dict["SC"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/Operation-EU/3.0":
                        self.about_dict["OP"] = about_list
                    elif str(s_i).split("#")[0] == "http://iec.ch/TC57/ns/CIM/GeographicalLocation-EU/3.0":
                        self.about_dict["GL"] = about_list

            self.class_filters = {}
            json_dict = json.loads(RDFS_INFO_3_0_0)
        else:
            raise ValueError(f"CGMES format not supported {cgmes_circuit.cgmes_version}")

        for class_name in self.cgmes_circuit.classes:
            self.class_filters[class_name] = {}
        for i, prop_name in enumerate(json_dict['Property-AttributeAssociation']):
            if json_dict["Class Name"][i] in self.cgmes_circuit.classes:
                p_key = str(prop_name).split('.')[-1]
                if p_key not in self.class_filters[json_dict["Class Name"][i]]:
                    temp_dict = {
                        "Profile": json_dict['ProfileKeyword'][i].strip('[]').split(','),
                        "ClassFullName": json_dict["Class"][i],
                        "Property-AttributeAssociationFull": json_dict["Property-AttributeAssociation"][i],
                        "Type": json_dict["Type"][i]
                    }
                    self.class_filters[json_dict["Class Name"][i]][p_key] = temp_dict
                else:
                    new_prof = json_dict['ProfileKeyword'][i].strip('[]').split(',')
                    self.class_filters[json_dict["Class Name"][i]][p_key]["Profile"].extend(new_prof)

    def export(self, file_name):
        fname = os.path.basename(file_name)
        fpath = os.path.dirname(file_name)
        name, extension = os.path.splitext(fname)

        profiles_to_export = []
        for prof_enum in self.profiles_to_export:
            if self.cgmes_circuit.cgmes_version == CGMESVersions.v2_4_15:
                if prof_enum.value not in ["OP", "SC"]:
                    profiles_to_export.append(prof_enum.value)
            elif self.cgmes_circuit.cgmes_version == CGMESVersions.v3_0_0:
                profiles_to_export.append(prof_enum.value)
            else:
                raise ValueError(f"Unrecognized CGMES version {self.cgmes_circuit.cgmes_version}")

        if self.one_file_per_profile:
            i = 1
            for prof in profiles_to_export:
                formated_name = f"{name}_{prof}_001{extension}"
                xml_formated_name = f"{name}_{prof}_001.xml"
                split_name = name.split('_')
                if split_name.__len__() == 5:
                    formated_name = f"{split_name[0]}_{split_name[1]}_{split_name[2]}_{prof}_{split_name[4]}{extension}"
                    xml_formated_name = f"{split_name[0]}_{split_name[1]}_{split_name[2]}_{prof}_{split_name[4]}.xml"
                with zipfile.ZipFile(os.path.join(fpath, formated_name), 'w', zipfile.ZIP_DEFLATED) as f_zip_ptr:
                    self.cgmes_circuit.emit_text(f"Export {prof} profile file")
                    self.cgmes_circuit.emit_progress(i / profiles_to_export.__len__() * 100)
                    i += 1
                    with BytesIO() as buffer:
                        self.serialize(stream=buffer, profile=prof)
                        f_zip_ptr.writestr(xml_formated_name, buffer.getvalue())
        else:
            i = 1
            with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as f_zip_ptr:
                for prof in profiles_to_export:
                    self.cgmes_circuit.emit_text(f"Export {prof} profile file")
                    self.cgmes_circuit.emit_progress(i / profiles_to_export.__len__() * 100)
                    formated_name = f"{name}_{prof}_001.xml"
                    split_name = name.split('_')
                    if split_name.__len__() == 5:
                        formated_name = f"{split_name[0]}_{split_name[1]}_{split_name[2]}_{prof}_{split_name[4]}.xml"
                    i += 1
                    with BytesIO() as buffer:
                        self.serialize(stream=buffer, profile=prof)
                        f_zip_ptr.writestr(formated_name, buffer.getvalue())

    def serialize(self, stream, profile):
        if not self.supports_profile(profile):
            raise NotImplementedError("Unsupported CGMES profile to export: " + profile)

        root = Et.Element("rdf:RDF", self.namespaces)
        full_model_elements = self.generate_full_model_elements(profile)
        root.extend(full_model_elements)
        other_elements = self.generate_other_elements(profile)
        root.extend(other_elements)

        # Convert ElementTree to string
        xml_str = Et.tostring(root, encoding="utf-8", method="xml")

        # Write the XML declaration manually
        xml_declaration = b'<?xml version="1.0" encoding="utf-8"?>\n'
        stream.write(xml_declaration)

        # Parse the XML string and prettify it
        dom = xml.dom.minidom.parseString(xml_str)
        xml_str_pretty = dom.toprettyxml(indent="  ", encoding="utf-8")

        # Write the prettified XML content (excluding the XML declaration) to the stream
        xml_content = xml_str_pretty.decode("utf-8").split("\n")[1:]  # Exclude the XML declaration
        stream.write("\n".join(xml_content).encode("utf-8"))

        stream.seek(0)

    def supports_profile(self, profile):
        if profile in self.profile_uris:
            return True
        else:
            return False

    def is_in_profile(self, instance_profiles, model_profile):
        if isinstance(instance_profiles, list):
            for profile in instance_profiles:
                if profile in self.profile_uris[model_profile]:
                    return True
        else:
            if instance_profiles in self.profile_uris[model_profile]:
                return True
        return False

    def generate_full_model_elements(self, profile):
        full_model_elements = list()
        filter_props = {"scenarioTime": "str",
                        "created": "str",
                        "version": "str",
                        "profile": "str",
                        "modelingAuthoritySet": "str",
                        "DependentOn": "Association",
                        "longDependentOnPF": "str",
                        "Supersedes": "str",
                        "description": "str"}

        selected_instance = None
        for instance in self.cgmes_circuit.cgmes_assets.FullModel_list:
            instance_profiles = getattr(instance, "profile", None)
            if self.is_in_profile(instance_profiles=instance_profiles, model_profile=profile):
                selected_instance = instance
                break
            else:
                pass
        if selected_instance is None:
            if len(self.cgmes_circuit.cgmes_assets.FullModel_list) > 0:
                selected_instance = self.cgmes_circuit.cgmes_assets.FullModel_list[0]
            else:
                selected_instance = None
        else:
            pass

        full_model_rdfid = str(uuid4())
        if selected_instance is not None:
            full_model_rdfid = selected_instance.rdfid
        else:
            pass
        element = Et.Element("md:FullModel", {"rdf:about": "urn:uuid:" + full_model_rdfid})

        for attr_name in filter_props.keys():
            child = Et.Element(f"md:Model.{attr_name}")
            attr_value = None
            if selected_instance is not None:
                attr_value = getattr(selected_instance, attr_name, None)
            else:
                attr_value = None

            if attr_name == "profile":
                target_profile_uris = self.profile_uris.get(profile, list())
                for target_profile_uri in target_profile_uris:
                    child = Et.Element(f"md:Model.{attr_name}")
                    child.text = str(target_profile_uri)
                    element.append(child)
                continue
            else:
                pass

            if attr_name == "created":
                if attr_value is None:
                    attr_value = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    pass
            elif attr_name == "scenarioTime":
                if attr_value is None:
                    attr_value = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    pass
            elif attr_name == "version":
                if attr_value is None:
                    attr_value = "1"
                elif isinstance(attr_value, int):
                    attr_value = str(attr_value)
                else:
                    attr_value_str = str(attr_value)
                    if attr_value_str.isdigit():
                        attr_value = attr_value_str
                    else:
                        self.cgmes_circuit.logger.add_warning(
                            msg="Coerced non-numeric FullModel.version during export",
                            device=full_model_rdfid,
                            device_class="FullModel",
                            device_property="version",
                            value=attr_value_str,
                            expected_value="numeric string"
                        )
                        attr_value = "1"
            else:
                pass

            if attr_value is None:
                if attr_name in ["description", "Supersedes", "longDependentOnPF"]:
                    child.text = ""
                    element.append(child)
                else:
                    pass
                continue
            else:
                pass

            if filter_props.get(attr_name) == "Association":
                if isinstance(attr_value, list):
                    for v in attr_value:
                        if v is None:
                            pass
                        else:
                            token = str(v)
                            if token.startswith("urn:uuid:"):
                                resource_value = token
                            else:
                                resource_value = "urn:uuid:" + token
                            child = Et.Element(f"md:Model.{attr_name}")
                            child.attrib = {"rdf:resource": resource_value}
                            element.append(child)
                    continue
                else:
                    token = str(attr_value)
                    if token.startswith("urn:uuid:"):
                        child.attrib = {"rdf:resource": token}
                    else:
                        child.attrib = {"rdf:resource": "urn:uuid:" + token}
                    element.append(child)
            else:
                if isinstance(attr_value, list):
                    for v in attr_value:
                        child = Et.Element(f"md:Model.{attr_name}")
                        child.text = str(v)
                        element.append(child)
                    continue
                else:
                    child.text = str(attr_value)
                    element.append(child)
        full_model_elements.append(element)
        return full_model_elements

    @staticmethod
    def in_profile(filters, profile):
        for k, v in filters.items():
            if profile in v["Profile"]:
                return True
        return False

    def attr_in_profile(self, attr_filters: dict, profile):
        if profile in attr_filters["Profile"]:
            return True
        else:
            if self.cgmes_circuit.cgmes_version == CGMESVersions.v2_4_15 and profile == "EQ":
                if self.export_OP:
                    if "OP" in attr_filters["Profile"]:
                        return True
                if self.export_SC:
                    if "SC" in attr_filters["Profile"]:
                        return True
        return False

    def generate_other_elements(self, profile):
        other_elements = []
        core_profiles = {"EQ", "OP", "SC", "SSH", "TP", "SV", "GL", "DY", "DL", "EQ_BD", "TP_BD"}
        for class_name, filters in self.class_filters.items():
            objects = self.cgmes_circuit.get_objects_list(elm_type=class_name)
            use_declared_property_fallback = False
            if self.in_profile(filters, profile):
                pass
            else:
                if len(filters) == 0 and profile not in core_profiles:
                    use_declared_property_fallback = True
                else:
                    continue
            for obj in objects:
                if self.about_dict.get(profile) is not None and class_name in self.about_dict.get(profile):
                    element = Et.Element("cim:" + class_name, {"rdf:about": "#_" + obj.rdfid})
                else:
                    element = Et.Element("cim:" + class_name, {"rdf:ID": "_" + obj.rdfid})
                has_child = False
                for attr_name in obj.get_declared_property_names():
                    attr_value = obj.get_declared_property_value(prop_name=attr_name)
                    if attr_value is None:
                        continue
                    if use_declared_property_fallback:
                        declared_property = obj.declared_properties.get(attr_name, None)
                        if declared_property is None or attr_name == "mRID":
                            continue
                        declared_profiles = declared_property.profiles
                        profile_matches = False
                        for declared_profile in declared_profiles:
                            if declared_profile.value == profile:
                                profile_matches = True
                            else:
                                pass
                        if profile_matches:
                            pass
                        else:
                            continue
                        prop_text = "cim:" + class_name + "." + attr_name
                        if isinstance(attr_value, list):
                            attr_type = "Association"
                        elif hasattr(attr_value, "rdfid"):
                            attr_type = "Association"
                        elif isinstance(attr_value, Enum):
                            attr_type = "Enumeration"
                        else:
                            attr_type = "Attribute"
                    else:
                        if attr_name not in filters or attr_name == "mRID":
                            continue
                        attr_filters = filters[attr_name]
                        if not self.attr_in_profile(attr_filters, profile):
                            continue
                        attr_type = attr_filters["Type"]
                        prop_split = str(attr_filters["Property-AttributeAssociationFull"]).split('#')
                        if prop_split[0] == "http://entsoe.eu/CIM/SchemaExtension/3/1":
                            prop_text = "entsoe:" + prop_split[-1]
                        elif prop_split[0] == "http://iec.ch/TC57/CIM100-European":
                            prop_text = "eu:" + prop_split[-1]
                        else:
                            prop_text = "cim:" + prop_split[-1]
                    child = Et.Element(prop_text)
                    if attr_type == "Association":
                        if isinstance(attr_value, list):
                            for v in attr_value:
                                if v is not None and hasattr(v, "rdfid") and v.rdfid is not None:
                                    child = Et.Element(prop_text)
                                    child.attrib = {"rdf:resource": "#_" + v.rdfid}
                                    element.append(child)
                                    has_child = True
                                else:
                                    pass
                            continue
                        else:
                            if attr_value is not None and hasattr(attr_value, "rdfid") and attr_value.rdfid is not None:
                                child.attrib = {"rdf:resource": "#_" + attr_value.rdfid}
                            else:
                                continue
                    elif attr_type == "Enumeration":
                        if use_declared_property_fallback:
                            enum_value = str(attr_value)
                            if enum_value.startswith("http://") or enum_value.startswith("https://"):
                                child.attrib = {"rdf:resource": enum_value}
                            else:
                                child.text = enum_value
                        else:
                            enum_dict_key = profile
                            enum_dict_value = self.enum_dict.get(enum_dict_key)
                            enum_value = enum_dict_value.get(str(attr_value))
                            if enum_value is not None:
                                child.attrib = {"rdf:resource": enum_value}
                            else:
                                continue
                    elif attr_type == "Attribute":
                        if isinstance(attr_value, bool):
                            attr_value = str(attr_value).lower()
                        if isinstance(attr_value, list):
                            for v in attr_value:
                                child = Et.Element(prop_text)
                                child.text = str(v)
                                element.append(child)
                                has_child = True
                            continue
                        else:
                            child.text = str(attr_value)
                    element.append(child)
                    has_child = True
                if has_child:
                    other_elements.append(element)
        return other_elements
