# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
import hashlib
import uuid as uuidlib
from typing import List, Dict, TypeVar, Any, Sequence, Tuple
from VeraGridEngine.IO.base.units import Unit
from VeraGridEngine.IO.raw.psse_property import PsseProperty


def uuid_from_seed(seed: str):
    """

    :param seed:
    :return:
    """
    m = hashlib.md5()
    m.update(seed.encode('utf-8'))
    return uuidlib.UUID(m.hexdigest()).hex


def format_raw_float(value: float) -> str:
    """
    Format a float in engineering notation with 5 decimals.
    Ensure the formatted string doesn't exceed 8 characters when possible.
    """
    # Attempt engineering format with 5 decimals
    formatted = f"{value:.5E}"

    # Split into mantissa and exponent
    mantissa, exponent = formatted.split("E")
    exponent = int(exponent)

    # Adjust the exponent to a multiple of 3
    eng_exponent = 3 * (exponent // 3)
    eng_mantissa = float(mantissa) * (10 ** (exponent - eng_exponent))

    # Format the result
    result = f"{eng_mantissa:.5f}E{eng_exponent:+03}"

    # Ensure it fits within 8 characters
    if len(result) <= 11:
        return result
    else:
        # Fall back to a shorter general format if too long
        return f"{value:.5g}"


class RawObjectMeta(type):
    """
    Metaclass that builds RAW property schema per class from class-level declarations.
    """

    def __new__(mcs, name, bases, namespace):
        """
        Build class-level schema by aggregating base + local property declarations.
        :param name: Class name
        :param bases: Base classes
        :param namespace: Class namespace
        :return: class object
        """
        cls = super().__new__(mcs, name, bases, namespace)

        aggregated_props: List[PsseProperty] = list()
        for base in bases:
            base_props: Tuple[PsseProperty, ...] = base.__dict__.get("CLASS_PROPERTIES", tuple())
            for prop in base_props:
                aggregated_props.append(prop)

        local_props: Tuple[PsseProperty, ...] = namespace.get("LOCAL_PROPERTIES", tuple())
        for prop in local_props:
            aggregated_props.append(prop)

        cls.CLASS_PROPERTIES = tuple(aggregated_props)
        cls.CLASS_REGISTERED_PROPERTIES = dict()
        for prop in cls.CLASS_PROPERTIES:
            cls.CLASS_REGISTERED_PROPERTIES[prop.property_name] = prop

        return cls


class RawObject(metaclass=RawObjectMeta):
    """
    PSSeObject
    """
    LOCAL_PROPERTIES: Tuple[PsseProperty, ...] = (
        PsseProperty(property_name="idtag",
                     rawx_key="uuid:string",
                     class_type=str,
                     description="Element UUID",
                     unit=Unit()),
    )
    CLASS_REGISTERED_PROPERTIES: Dict[str, PsseProperty] = dict()
    CLASS_PROPERTIES: Tuple[PsseProperty, ...] = tuple()

    """
    PSSeObject
    """

    def __init__(self, class_name):

        self.class_name = class_name

        self.version = 33

        self.idtag = uuidlib.uuid4().hex  # always initialize with random  uuid

        self_cls: type = type(self)
        self.__registered_properties = self_cls.CLASS_REGISTERED_PROPERTIES
        self.__properties = self_cls.CLASS_PROPERTIES

    def get_rdfid(self) -> str:
        """
        Convert the idtag to RDFID
        :return: UUID converted to RDFID
        """
        lenghts = [8, 4, 4, 4, 12]
        chunks = list()
        s = 0
        for l in lenghts:
            a = self.idtag[s:s + l]
            chunks.append(a)
            s += l
        return "-".join(chunks)

    def get_properties(self) -> List[PsseProperty]:
        """
        Get list of properties
        :return: List[PsseProperty]
        """
        return list(self.__registered_properties.values())

    def get_prop_value(self, prop: PsseProperty):
        """
        Get property value
        :param prop:
        :return:
        """
        return object.__getattribute__(self, prop.property_name)

    def get_rawx_dict(self) -> Dict[str, PsseProperty]:
        """
        Get the RAWX property dictionary
        :return: Dict[str, PsseProperty]
        """

        return {value.rawx_key: value
                for key, value in self.__registered_properties.items()}

    def register_property(self,
                          property_name: str,
                          rawx_key: str,
                          class_type: TypeVar | object,
                          unit: Unit = Unit(),
                          denominator_unit: Unit = Unit(),
                          description: str = '',
                          max_chars=None,
                          min_value=-1e20,
                          max_value=1e20,
                          format_rule=None):
        """
        Register property of this object
        :param property_name:
        :param rawx_key:
        :param class_type:
        :param unit:
        :param denominator_unit:
        :param description:
        :param max_chars:
        :param min_value:
        :param max_value:
        :param format_rule: some formatting rule
        """
        raise RuntimeError("RawObject.register_property() is disabled. Use class-level LOCAL_PROPERTIES.")

    def format_raw_line_prop(self, props: List[str]):
        """
        Format a list of property names
        :param props: list of property names
        :return:
        """
        lst = list()
        for p in props:
            if p in self.__registered_properties:
                prop = self.__registered_properties[p]
                val = object.__getattribute__(self, p)
                if prop.class_type == str:
                    lst.append("'" + val + "'")
                else:
                    lst.append(str(val))
        return ", ".join(lst)

    @staticmethod
    def extend_or_curtail(data: List[Any], n: int) -> List[Any]:
        """
        Extends of curtails the input so that it marches what's expected
        :param data: list of values
        :param n: expected number of items
        :return: extended or curtailed data
        """
        if len(data) == n:
            # it's ok
            return data
        elif len(data) < n:
            # extend
            diff = n - len(data)
            extra = [0 for _ in range(diff)]
            return data + extra
        elif len(data) > n:
            # curtail
            return [data[i] for i in range(n)]

    def format_raw_line(self, props: List[str]) -> str:
        """
        Format a list of values
        :param props: list of property names
        :return:
        """
        lst = list()
        for p_name in props:

            prop = self.__registered_properties.get(p_name, None)

            if prop is None:
                raise Exception(f'Raw property {p_name} not found when trying to format it :(')
            else:
                val = object.__getattribute__(self, p_name)

                if prop.class_type == str:
                    str_val = str(val)
                    if prop.max_chars is not None:
                        lst.append(f"'{str_val.ljust(prop.max_chars)}'")
                    else:
                        lst.append(f"'{str_val}'")
                elif prop.class_type == float:
                    if prop.format_rule is None:
                        str_val = format_raw_float(value=val)
                    else:
                        str_val = f"{val:{prop.format_rule}}"
                    if prop.max_chars is not None:
                        lst.append(f"{str_val.rjust(prop.max_chars)}")
                    else:
                        lst.append(f"{str_val.rjust(8)}")

                elif prop.class_type == int:
                    str_val = str(val)
                    if prop.max_chars is not None:
                        lst.append(f"{str_val.rjust(prop.max_chars)}")
                    else:
                        lst.append(f"{str_val.rjust(6)}")

                else:
                    lst.append(str(val))

        return ", ".join(lst)

    def get_raw_line(self, version: int) -> str:
        """
        Get raw line
        :param version: PSSe version
        :return: Raw string representing this object
        """
        return ""

    def get_id(self) -> str:
        """
        Get a PSSe ID
        Each device will implement its own way of generating this
        :return: id
        """
        return ""

    def __str__(self):
        return self.get_id()

    def get_seed(self) -> str:
        """
        Get seed ID
        :return: seed ID
        """
        return self.get_id()

    def get_uuid5(self):
        """
        Generate UUID with the seed given by get_id()
        :return: UUID based on the PSSe seed
        """
        return uuid_from_seed(seed=self.get_seed())

    def set_registered_property_value(self, property_name: str, value: Any) -> bool:
        """
        Set a registered property value using explicit object attribute assignment.

        :param property_name: Registered property name.
        :param value: Value to assign.
        :return: ``True`` when the property exists and was assigned.
        """
        if property_name in self.__registered_properties:
            object.__setattr__(self, property_name, value)
            return True
        else:
            return False

    def get_registered_property_value(self, property_name: str) -> Any:
        """
        Get a registered property value using explicit object attribute access.

        :param property_name: Registered property name.
        :return: Property value.
        :raises KeyError: If the property is not registered.
        """
        if property_name in self.__registered_properties:
            return object.__getattribute__(self, property_name)
        else:
            raise KeyError(property_name)

    def try_parse(self, values: Sequence[Any]) -> None:
        """
        Copy *values* into this object following _ATTR_ORDER.
        Extra elements are ignored; missing ones keep their default.
        """
        for i, val in enumerate(values):
            attr = self.__properties[i].property_name
            self.set_registered_property_value(attr, val)

    def try_parse2(self, values: Sequence[Any], prop_names: Sequence[str]) -> None:
        """
        Copy *values* into this object following _ATTR_ORDER.
        Extra elements are ignored; missing ones keep their default.
        :param values: values to set
        :param prop_names: array of names
        """
        if len(values) <= len(prop_names):
            n = len(values)
        else:
            n = len(prop_names)

        for i in range(n):
            property_name = prop_names[i]
            if property_name in self.__registered_properties:
                self.set_registered_property_value(property_name, values[i])
            else:
                print(f"PSS/e property does not exist :( '{property_name}'")
