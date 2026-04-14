from typing import TypeAlias

from VeraGridEngine.Devices.Profiles.profile_bool import ProfileBool
from VeraGridEngine.Devices.Profiles.profile_device import ProfileDevice
from VeraGridEngine.Devices.Profiles.profile_enum import ProfileEnum
from VeraGridEngine.Devices.Profiles.profile_float import ProfileFloat
from VeraGridEngine.Devices.Profiles.profile_int import ProfileInt
from VeraGridEngine.Devices.Profiles.sparse_array_bool import SparseArrayBool
from VeraGridEngine.Devices.Profiles.sparse_array_device import SparseArrayDevice
from VeraGridEngine.Devices.Profiles.sparse_array_enum import SparseArrayEnum
from VeraGridEngine.Devices.Profiles.sparse_array_float import SparseArrayFloat
from VeraGridEngine.Devices.Profiles.sparse_array_int import SparseArrayInt
from VeraGridEngine.Devices.Profiles.type_checks import ProfileDataType, check_if_sparse, check_type

PROFILE_TYPES: TypeAlias = ProfileDataType
AnyProfile: TypeAlias = ProfileFloat | ProfileInt | ProfileBool | ProfileDevice | ProfileEnum
PROFILE_INSTANCE_TYPES = (ProfileFloat, ProfileInt, ProfileBool, ProfileDevice, ProfileEnum)

__all__ = [
    "AnyProfile",
    "PROFILE_TYPES",
    "PROFILE_INSTANCE_TYPES",
    "ProfileBool",
    "ProfileDevice",
    "ProfileEnum",
    "ProfileFloat",
    "ProfileInt",
    "SparseArrayBool",
    "SparseArrayDevice",
    "SparseArrayEnum",
    "SparseArrayFloat",
    "SparseArrayInt",
    "check_if_sparse",
    "check_type",
]
