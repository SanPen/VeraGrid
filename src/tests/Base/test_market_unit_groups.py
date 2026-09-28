import numpy as np
import VeraGridEngine.Devices as dev
from VeraGridEngine.Devices.assets import Assets
from VeraGridEngine.enumerations import DeviceType
import VeraGridEngine as vg


def test_market_unit_groups_assets():
    a = Assets()

    # Initial state
    assert a.market_unit_groups == []
    assert a.get_market_unit_groups() == []
    assert a.get_market_unit_group_number() == 0
    assert a.get_market_unit_groups_number() == 0
    assert len(a.get_market_unit_group_names()) == 0

    # Adding groups
    grp1 = dev.MarketUnitsGroup(name="Group 1", category="Cat A")
    grp2 = dev.MarketUnitsGroup(name="Group 2", category="Cat B")

    a.add_market_unit_group(grp1)
    a.add_element(grp2)

    assert a.get_market_unit_group_number() == 2
    assert a.get_market_unit_groups_number() == 2
    assert len(a.market_unit_groups) == 2
    assert list(a.get_market_unit_group_names()) == ["Group 1", "Group 2"]
    assert list(a.get_market_unit_groups_names()) == ["Group 1", "Group 2"]

    # get_elements_by_type
    assert a.get_elements_by_type(DeviceType.MarketUnitsGroupDevice) == [grp1, grp2]

    # set_elements_list_by_type
    grp3 = dev.MarketUnitsGroup(name="Group 3", category="Cat C")
    a.set_elements_list_by_type(DeviceType.MarketUnitsGroupDevice, [grp3])
    assert a.get_market_unit_groups() == [grp3]
    assert a.market_unit_groups == [grp3]

    # MarketUnit integration and group linkage
    mu1 = dev.MarketUnit(name="MU 1", group=grp3)
    mu2 = dev.MarketUnit(name="MU 2", group=None)
    a.add_element(mu1)
    a.add_market_unit(mu2)

    assert mu1 in a.market_units
    assert mu2 in a.market_units

    # Grouping queries
    by_groups = a.get_market_units_by_groups()
    assert len(by_groups) == 1
    assert by_groups[0][0] is grp3
    assert by_groups[0][1] == [mu1]

    by_groups_idx = a.get_market_units_by_groups_index_dict()
    assert by_groups_idx == {0: [mu1]}

    by_groups_dict = a.get_market_unit_group_dict()
    assert by_groups_dict == {grp3.idtag: [mu1]}

    # get_dictionary_of_lists
    template_mug, deps_mug = a.get_dictionary_of_lists(DeviceType.MarketUnitsGroupDevice)
    assert template_mug.device_type == DeviceType.MarketUnitsGroupDevice
    assert deps_mug == {}

    template_mu, deps_mu = a.get_dictionary_of_lists(DeviceType.MarketUnitDevice)
    assert template_mu.device_type == DeviceType.MarketUnitDevice
    assert DeviceType.FacilityDevice in deps_mu
    assert deps_mu[DeviceType.FacilityDevice] == []
    assert DeviceType.MarketUnitsGroupDevice in deps_mu
    assert deps_mu[DeviceType.MarketUnitsGroupDevice] == [grp3]

    template_investment, deps_investment = a.get_dictionary_of_lists(DeviceType.InvestmentDevice)
    assert template_investment.device_type == DeviceType.InvestmentDevice
    assert DeviceType.BusDevice in deps_investment
    for branch_device_type in [
            DeviceType.LineDevice,
            DeviceType.DCLineDevice,
            DeviceType.Transformer2WDevice,
            DeviceType.Transformer3WDevice,
            DeviceType.TransformerNwDevice,
            DeviceType.WindingDevice,
            DeviceType.HVDCLineDevice,
            DeviceType.VscDevice,
            DeviceType.UpfcDevice,
            DeviceType.SeriesReactanceDevice,
            DeviceType.SwitchDevice,
    ]:
        assert branch_device_type in deps_investment
    for injection_device_type in a.get_injections_device_types():
        assert injection_device_type in deps_investment

    # template_objects_dict
    assert any(isinstance(x, dev.MarketUnitsGroup) for x in a.template_objects_dict["Market"])

    # delete_market_unit_group unbinds reference from market unit
    a.delete_element(grp3)
    assert len(a.market_unit_groups) == 0
    assert mu1.group is None


def test_market_unit_groups_multi_circuit():
    mc = vg.MultiCircuit()
    assert hasattr(mc, "market_unit_groups")

    grp = dev.MarketUnitsGroup(name="MUG")
    mc.add_element(grp)
    assert len(mc.market_unit_groups) == 1
    assert mc.get_elements_by_type(DeviceType.MarketUnitsGroupDevice)[0].name == "MUG"

    # item_types, template_items, get_all_elements_iter
    assert DeviceType.MarketUnitsGroupDevice in list(mc.item_types())
    assert DeviceType.MarketUnitsGroupDevice in [t.device_type for t in mc.template_items()]
    assert grp in list(mc.get_all_elements_iter())
