import numpy as np
import pandas as pd

from VeraGridEngine.Devices.assets import Assets


def test_get_unix_time_round_trip_resolution_independent():
    """
    get_unix_time must return correct epoch seconds regardless of the
    datetime64 resolution pandas chose for the time profile (ns vs us).
    We noticed the pandas version may create conflicts.
    """
    epoch = np.array([0, 3600, 7200, 1_700_000_000], dtype=np.int64)

    for unit in ("ns", "us"):
        a = Assets()
        a.time_profile = pd.to_datetime(epoch, unit="s").as_unit(unit)
        assert a.time_profile.dtype == np.dtype(f"datetime64[{unit}]")
        np.testing.assert_array_equal(a.get_unix_time(), epoch)


if __name__ == "__main__":
    test_get_unix_time_round_trip_resolution_independent()
    print("ok")
