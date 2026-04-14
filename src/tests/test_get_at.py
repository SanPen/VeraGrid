import numpy as np
import inspect
from VeraGridEngine.Devices.Injections.load import Load
from VeraGridEngine.Devices.Injections.generator import Generator
from VeraGridEngine.Devices.Injections.shunt import ShuntParent
from VeraGridEngine.enumerations import DeviceType, BuildStatus, HvdcControlType, TapPhaseControl, TapModuleControl
from VeraGridEngine.Devices.Parents.injection_parent import InjectionParent
from VeraGridEngine.Devices.Parents.branch_parent import BranchParent
from VeraGridEngine.Devices.Parents.generator_parent import GeneratorParent
from VeraGridEngine.Devices.Parents.controllable_branch_parent import ControllableBranchParent
from VeraGridEngine.Devices.Branches.hvdc_line import HvdcLine


def test_load_getters_match_profiles():
    """
    Test that all get_*_at(t_idx) functions in Load return the expected values
    from their corresponding profiles and base attributes.
    """

    # Create a dummy load with some nonzero base values
    load = Load(
        G=1.0, B=2.0, Ir=3.0, Ii=4.0,
        G1=1.1, B1=2.1, Ir1=3.1, Ii1=4.1,
        G2=1.2, B2=2.2, Ir2=3.2, Ii2=4.2,
        G3=1.3, B3=2.3, Ir3=3.3, Ii3=4.3,
        Pl0=5.0, Ql0=6.0
    )

    # Create simple time-dependent profiles
    n_steps = 5

    for prof_name in dir(load):
        if prof_name.endswith('_prof') and isinstance(getattr(load, prof_name), type(load._G_prof)):
            prof = getattr(load, prof_name)
            prof.set(arr=np.linspace(0, 10, n_steps))

    # Mapping between attribute, profile, and getter
    # Each getter must correspond to the correct profile and base attribute
    mappings = {
        'Ir': load.get_Ir_at,
        'Ir1': load.get_Ir1_at,
        'Ir2': load.get_Ir2_at,
        'Ir3': load.get_Ir3_at,
        'Ii': load.get_Ii_at,
        'Ii1': load.get_Ii1_at,
        'Ii2': load.get_Ii2_at,
        'Ii3': load.get_Ii3_at,
        'G': load.get_G_at,
        'G1': load.get_G1_at,
        'G2': load.get_G2_at,
        'G3': load.get_G3_at,
        'B': load.get_B_at,
        'B1': load.get_B1_at,
        'B2': load.get_B2_at,
        'B3': load.get_B3_at,
    }

    # Run consistency checks
    for attr, getter in mappings.items():
        prof = getattr(load, f"{attr}_prof")
        base_val = getattr(load, attr)
        for t_idx in [None, 0, 2, n_steps - 1]:
            expected = base_val if t_idx is None else prof.toarray()[t_idx]
            result = getter(t_idx)
            assert np.isclose(result, expected), (
                f"Getter {getter.__name__} returned {result}, expected {expected} "
                f"for t={t_idx} ({attr})"
            )

    # Check complex-valued getters
    assert np.isclose(load.get_I_at(0), complex(load.get_Ir_at(0), load.get_Ii_at(0)))
    assert np.isclose(load.get_I1_at(1), complex(load.get_Ir1_at(1), load.get_Ii1_at(1)))
    assert np.isclose(load.get_Y2_at(2), complex(load.get_G2_at(2), load.get_B2_at(2)))
    assert np.isclose(load.get_Y3_conj_at(3), complex(load.get_G3_at(3), -load.get_B3_at(3)))

    print("✅ All get_*_at(t_idx) functions correctly match their profiles and attributes.")


def test_generator_getters_match_profiles():
    """
    Test that all get_*_at(t_idx) functions in Generator return the expected
    values from their associated attributes and profiles.
    """

    # Instantiate a generator with nonzero values
    gen = Generator(
        P=10.0, power_factor=0.9, vset=1.01,
        Qmin=-50.0, Qmax=60.0, Cost0=5.0, Cost2=0.1
    )

    # Time steps
    n_steps = 5
    time_indices = np.arange(n_steps)

    # Fill all profile arrays with linearly increasing data
    for name, attr in inspect.getmembers(gen):
        if name.endswith("_prof") and hasattr(attr, "set"):
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Dynamically find all methods named get_*_at
    get_methods = [
        (name, method)
        for name, method in inspect.getmembers(gen, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    for name, method in get_methods:
        # Example: get_Pf_at -> Pf, Pf_prof
        base = name[len("get_"): -len("_at")]
        attr_name = base
        prof_name = f"{base}_prof"

        # Skip special or computed getters without base profile
        if not hasattr(gen, attr_name) or not hasattr(gen, prof_name):
            continue

        attr_value = getattr(gen, attr_name)
        prof_value = getattr(gen, prof_name)

        # Run checks for None (base value) and all time indices
        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_value if t_idx is None else prof_value.toarray()[t_idx]
            result = method(t_idx)
            assert np.isclose(
                result, expected
            ), f"{name}({t_idx}) returned {result}, expected {expected}"

    print("✅ All Generator.get_*_at(t_idx) methods correctly match their profiles and attributes.")


def test_shuntparent_getters_match_profiles():
    """
    Test that all get_*_at(t_idx) functions in ShuntParent return the expected
    values from their corresponding attributes and profiles.
    """

    # Create a dummy shunt parent with some arbitrary nonzero values
    shunt = ShuntParent(
        name="TestShunt",
        idtag=None,
        code="",
        bus=None,
        active=True,
        G=1.0, G1=1.1, G2=1.2, G3=1.3,
        B=2.0, B1=2.1, B2=2.2, B3=2.3,
        G0=0.5, B0=0.6,
        Cost=0.0,
        mttf=0.0,
        mttr=0.0,
        capex=0.0,
        opex=0.0,
        build_status=BuildStatus.Commissioned,
        device_type=DeviceType.ShuntDevice,
    )

    # Define simple time steps and fill all *_prof with numeric sequences
    n_steps = 5
    for name, attr in inspect.getmembers(shunt):
        if name.endswith("_prof") and hasattr(attr, "set"):
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Automatically discover all getters named get_*_at
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(shunt, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    # Run through each getter and verify that it matches its profile
    for name, method in getter_methods:
        base = name[len("get_"): -len("_at")]  # e.g., 'G', 'B', 'Ga', ...
        attr_name = base
        prof_name = f"{base}_prof"

        # Skip complex-valued getters (we'll test those separately)
        if name in ["get_Y_at", "get_Ya_at", "get_Yb_at", "get_Yc_at"]:
            continue

        if hasattr(shunt, attr_name) and hasattr(shunt, prof_name):
            attr_val = getattr(shunt, attr_name)
            prof_obj = getattr(shunt, prof_name)
            arr = prof_obj.toarray()

            for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
                expected = attr_val if t_idx is None else arr[t_idx]
                result = method(t_idx)
                assert np.isclose(result, expected), (
                    f"{name}({t_idx}) returned {result}, expected {expected}"
                )

    # Check complex getters (Y, Ya, Yb, Yc)
    for yname, parts in {
        "get_Y_at": ("G", "B"),
        "get_Ya_at": ("Ga", "Ba"),
        "get_Yb_at": ("Gb", "Bb"),
        "get_Yc_at": ("Gc", "Bc"),
    }.items():
        g_attr, b_attr = parts
        g = getattr(shunt, f"get_{g_attr}_at")(0)
        b = getattr(shunt, f"get_{b_attr}_at")(0)
        y_complex = getattr(shunt, yname)(0)
        assert np.isclose(y_complex, complex(g, b)), f"{yname} mismatch"

    print("✅ All ShuntParent.get_*_at(t_idx) functions match their attributes and profiles correctly.")


def test_injectionparent_getters_match_profiles():
    """
    Ensure that all get_*_at(t_idx) methods in InjectionParent return the correct
    values from their associated attributes and profiles.
    """

    # Create a dummy InjectionParent (we can pass None for bus)
    inj = InjectionParent(
        name="TestInjection",
        idtag=None,
        code="",
        bus=None,
        active=True,
        Cost=100.0,
        mttf=10.0,
        mttr=5.0,
        capex=200.0,
        opex=50.0,
        build_status=BuildStatus.Commissioned,
        device_type=DeviceType.LoadDevice
    )

    # Prepare synthetic time series data
    n_steps = 5
    for name, attr in inspect.getmembers(inj):
        if name.endswith("_prof") and hasattr(attr, "set"):
            # Replace each profile with a deterministic numeric series
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Automatically discover all getter methods following get_*_at naming pattern
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(inj, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    # Loop through each discovered getter
    for name, method in getter_methods:
        base = name[len("get_"): -len("_at")]  # e.g. "Cost", "active", "shift_key"
        attr_name = base
        prof_name = f"{base}_prof"

        if not (hasattr(inj, attr_name) and hasattr(inj, prof_name)):
            continue

        attr_value = getattr(inj, attr_name)
        prof_obj = getattr(inj, prof_name)
        arr = prof_obj.toarray()

        # Check both None (base value) and numeric time indices
        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_value if t_idx is None else arr[t_idx]
            result = method(t_idx)
            assert np.isclose(result, expected), (
                f"{name}({t_idx}) returned {result}, expected {expected}"
            )

    print("✅ All InjectionParent.get_*_at(t_idx) methods match their profiles and attributes correctly.")


def test_branchparent_getters_match_profiles():
    """
    Verify that all get_*_at(t_idx) methods in BranchParent return the correct
    values from their corresponding base attributes and profiles.
    """

    # Create a dummy branch with realistic nonzero values
    branch = BranchParent(
        name="TestBranch",
        idtag=None,
        code="",
        bus_from=None,
        bus_to=None,
        active=True,
        reducible=True,
        rate=100.0,
        contingency_factor=0.9,
        protection_rating_factor=0.8,
        contingency_enabled=True,
        monitor_loading=False,
        mttf=1000.0,
        mttr=20.0,
        build_status=BuildStatus.Commissioned,
        capex=200.0,
        opex=10.0,
        cost=50.0,
        temp_base=25.0,
        temp_oper=50.0,
        alpha=0.004,
        device_type=DeviceType.LineDevice,
        color="#ff0000"
    )

    # Fill all profiles with linearly increasing data for deterministic checks
    n_steps = 5
    for name, attr in inspect.getmembers(branch):
        if name.endswith("_prof") and hasattr(attr, "set"):
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Dynamically find all get_*_at methods
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(branch, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    # Test each getter for t_idx = None and specific numeric indices
    for name, method in getter_methods:
        base_name = name[len("get_"): -len("_at")]
        attr_name = base_name
        prof_name = f"{base_name}_prof"

        # Skip getters without matching attribute/profile pair
        if not (hasattr(branch, attr_name) and hasattr(branch, prof_name)):
            continue

        attr_val = getattr(branch, attr_name)
        prof_obj = getattr(branch, prof_name)
        arr = prof_obj.toarray()

        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_val if t_idx is None else arr[t_idx]
            result = method(t_idx)
            assert np.isclose(
                result, expected
            ), f"{name}({t_idx}) returned {result}, expected {expected}"

    print("✅ All BranchParent.get_*_at(t_idx) methods match their profiles and attributes correctly.")


def test_generatorparent_getters_match_profiles():
    """
    Verify that all get_*_at(t_idx) methods in GeneratorParent return the correct
    values from their associated attributes and profiles.
    """

    # Create a dummy GeneratorParent with deterministic attributes
    gen = GeneratorParent(
        name="TestGen",
        idtag=None,
        code="",
        bus=None,
        control_bus=None,
        active=True,
        P=100.0,
        Pmin=10.0,
        Pmax=150.0,
        Cost=25.0,
        mttf=1000.0,
        mttr=10.0,
        capex=500.0,
        opex=20.0,
        srap_enabled=True,
        build_status=BuildStatus.Commissioned,
        device_type=DeviceType.GeneratorDevice
    )

    # Fill all *_prof with predictable data
    n_steps = 5
    for name, attr in inspect.getmembers(gen):
        if name.endswith("_prof") and hasattr(attr, "set"):
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Automatically find all get_*_at methods
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(gen, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    # Check each getter result against base value and profile
    for name, method in getter_methods:
        base = name[len("get_"): -len("_at")]
        attr_name = base
        prof_name = f"{base}_prof"

        # Skip if missing attribute/profile pair
        if not (hasattr(gen, attr_name) and hasattr(gen, prof_name)):
            continue

        attr_val = getattr(gen, attr_name)
        prof_obj = getattr(gen, prof_name)
        arr = prof_obj.toarray()

        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_val if t_idx is None else arr[t_idx]
            result = method(t_idx)
            assert np.isclose(result, expected), (
                f"{name}({t_idx}) returned {result}, expected {expected}"
            )

    print("✅ All GeneratorParent.get_*_at(t_idx) methods correctly match their profiles and attributes.")


def test_hvdcline_getters_match_profiles():
    """
    Verify that all get_*_at(t_idx) methods in HvdcLine return the correct
    values from their attributes and profiles.
    """

    hvdc = HvdcLine(
        name="TestHVDC",
        bus_from=None,
        bus_to=None,
        active=True,
        rate=500.0,
        Pset=100.0,
        r=0.05,
        loss_factor=0.01,
        Vset_f=1.0,
        Vset_t=1.0,
        length=100.0,
        angle_droop=0.5,
        mttf=1000.0,
        mttr=5.0,
        capex=1000000.0,
        opex=5000.0,
        contingency_factor=1.2,
        protection_rating_factor=1.4,
        build_status=BuildStatus.Commissioned,
        control_mode=HvdcControlType.type_1_Pset,
        dc_link_voltage=200.0
    )

    # Fill all *_prof attributes with known numeric sequences
    n_steps = 5
    for name, attr in inspect.getmembers(hvdc):
        if name.endswith("_prof") and hasattr(attr, "set"):
            attr.set(arr=np.linspace(1.0, 10.0, n_steps))

    # Find all get_*_at() methods dynamically
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(hvdc, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    for name, method in getter_methods:
        base = name[len("get_"): -len("_at")]
        attr_name = base
        prof_name = f"{base}_prof"

        # Skip getters without a matching attribute/profile pair
        if not (hasattr(hvdc, attr_name) and hasattr(hvdc, prof_name)):
            continue

        attr_val = getattr(hvdc, attr_name)
        prof_obj = getattr(hvdc, prof_name)
        arr = prof_obj.toarray()

        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_val if t_idx is None else arr[t_idx]
            result = method(t_idx)
            assert np.isclose(
                result, expected
            ), f"{name}({t_idx}) returned {result}, expected {expected}"

    print("✅ All HvdcLine.get_*_at(t_idx) methods correctly match their profiles and attributes.")


def test_controllablebranchparent_getters_match_profiles():
    """
    Ensure all get_*_at(t_idx) methods in ControllableBranchParent correctly
    return values from their associated base attributes and profiles.
    """

    # Create a minimal controllable branch
    branch = ControllableBranchParent(
        bus_from=None,
        bus_to=None,
        name="TestTransformer",
        idtag=None,
        code="",
        active=True,
        reducible=False,
        rate=100.0,
        r=0.01,
        x=0.05,
        g=0.0,
        b=0.0,
        tap_module=1.0,
        tap_module_max=1.1,
        tap_module_min=0.9,
        tap_phase=0.0,
        tap_phase_max=0.1,
        tap_phase_min=-0.1,
        tolerance=0.1,
        vset=1.0,
        Pset=10.0,
        Qset=5.0,
        regulation_branch=None,
        regulation_bus=None,
        temp_base=25.0,
        temp_oper=30.0,
        alpha=0.004,
        tap_module_control_mode=TapModuleControl.fixed,
        tap_phase_control_mode=TapPhaseControl.fixed,
        contingency_factor=1.0,
        protection_rating_factor=1.2,
        contingency_enabled=True,
        monitor_loading=False,
        r0=0.02, x0=0.06, g0=0.0, b0=0.0,
        r2=0.02, x2=0.06, g2=0.0, b2=0.0,
        cost=100.0,
        mttf=1000.0,
        mttr=10.0,
        capex=5000.0,
        opex=100.0,
        build_status=BuildStatus.Commissioned,
        device_type=DeviceType.Transformer2WDevice,
    )

    # Assign predictable profiles
    n_steps = 5
    for name, attr in inspect.getmembers(branch):
        if name.endswith("_prof") and hasattr(attr, "set"):
            # Create a simple numeric sequence for predictable testing
            if attr.dtype == float:
                attr.set(arr=np.linspace(1.0, 10.0, n_steps))
            elif attr.dtype == bool:
                attr.set(arr=np.array([True, False, True, True, False]))
            elif attr.dtype == TapModuleControl:
                attr.set(arr=np.array([TapModuleControl.fixed,
                                       TapModuleControl.Qf,
                                       TapModuleControl.Qt,
                                       TapModuleControl.Vm,
                                       TapModuleControl.fixed]))
            elif attr.dtype == TapPhaseControl:
                attr.set(arr=np.array([TapPhaseControl.fixed,
                                       TapPhaseControl.Pf,
                                       TapPhaseControl.Pt,
                                       TapPhaseControl.Pf,
                                       TapPhaseControl.fixed]))
            else:
                # For enum or other data types, set a repeating pattern
                raise Exception("Unhandled data type")

    # Discover all get_*_at methods
    getter_methods = [
        (name, method)
        for name, method in inspect.getmembers(branch, predicate=inspect.ismethod)
        if name.startswith("get_") and name.endswith("_at")
    ]

    for name, method in getter_methods:
        base = name[len("get_") : -len("_at")]
        attr_name = base
        prof_name = f"{base}_prof"

        # Skip missing pairs
        if not (hasattr(branch, attr_name) and hasattr(branch, prof_name)):
            continue

        attr_val = getattr(branch, attr_name)
        prof_obj = getattr(branch, prof_name)
        arr = prof_obj.toarray()

        # Check both None and valid time indices
        for t_idx in [None, 0, n_steps // 2, n_steps - 1]:
            expected = attr_val if t_idx is None else arr[t_idx]
            result = method(t_idx)
            assert (
                result == expected or np.isclose(result, expected)
            ), f"{name}({t_idx}) returned {result}, expected {expected}"

    print("✅ All ControllableBranchParent.get_*_at(t_idx) methods are consistent with their profiles.")