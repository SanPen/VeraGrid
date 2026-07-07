import VeraGridEngine.api as vge


def test_transformer_nw_recalculates_windings_from_definition():
    bus_hv = vge.Bus(name="HV Bus", Vnom=110.0)
    bus_mv = vge.Bus(name="MV Bus", Vnom=33.0)
    bus_lv = vge.Bus(name="LV Bus", Vnom=11.0)

    transformer = vge.TransformerNW(name="Transformer NW",
                                    winding_count=3,
                                    buses=[bus_hv, bus_mv, bus_lv])

    design_values = (
        (110.0, 100.0, 120.0, 10.0),
        (33.0, 50.0, 80.0, 12.0),
        (11.0, 20.0, 40.0, 14.0),
    )

    for winding, (voltage, sn, pcu, vsc) in zip(transformer.windings, design_values):
        winding.set_hv_and_lv(HV=voltage, LV=1.0)
        winding.Sn = sn
        winding.rate = sn
        winding.Pcu = pcu
        winding.Vsc = vsc

    transformer.fill_from_design_values(Pfe=30.0, I0=0.4, Sbase=100.0)

    assert transformer.winding_count == 3
    assert transformer.all_connected()

    first_winding = transformer.windings[0]
    other_windings = transformer.windings[1:]

    assert first_winding.R > 0.0
    assert first_winding.X > 0.0
    assert abs(first_winding.G) > 0.0
    assert abs(first_winding.B) > 0.0

    for winding in other_windings:
        assert winding.R > 0.0
        assert winding.X > 0.0
        assert winding.G == 0.0
        assert winding.B == 0.0


def test_assets_add_and_delete_transformer_nw():
    grid = vge.MultiCircuit()

    bus_hv = vge.Bus(name="HV Bus", Vnom=110.0)
    bus_mv = vge.Bus(name="MV Bus", Vnom=33.0)
    grid.add_bus(bus_hv)
    grid.add_bus(bus_mv)

    transformer = vge.TransformerNW(name="Transformer NW",
                                    winding_count=2,
                                    buses=[bus_hv, bus_mv])

    grid.add_transformer_nw(transformer)

    assert transformer in grid.transformers_nw
    assert transformer.bus0 in grid.buses
    for winding in transformer.windings:
        assert winding in grid.windings

    winding_refs = list(transformer.windings)
    grid.delete_transformer_nw(transformer)

    assert transformer not in grid.transformers_nw
    assert transformer.bus0 not in grid.buses
    assert transformer.winding_count == 0
    for winding in winding_refs:
        assert winding not in grid.windings


def test_transformer_nw_constructor_creates_requested_windings():
    transformer = vge.TransformerNW(name="Transformer NW", winding_count=5)

    assert transformer.winding_count == 5
    assert len(transformer.windings) == 5
    assert all(winding.bus_to == transformer.bus0 for winding in transformer.windings)
    assert all(winding.bus_from is None for winding in transformer.windings)


def test_assets_only_add_connected_transformer_nw_windings():
    grid = vge.MultiCircuit()

    bus_hv = vge.Bus(name="HV Bus", Vnom=110.0)
    bus_lv = vge.Bus(name="LV Bus", Vnom=33.0)
    grid.add_bus(bus_hv)
    grid.add_bus(bus_lv)

    transformer = vge.TransformerNW(name="Transformer NW",
                                    winding_count=4,
                                    buses=[bus_hv, None, bus_lv, None])

    grid.add_transformer_nw(transformer)

    assert transformer in grid.transformers_nw
    assert len(grid.windings) == 2
    assert transformer.windings[0] in grid.windings
    assert transformer.windings[2] in grid.windings
    assert transformer.windings[1] not in grid.windings
    assert transformer.windings[3] not in grid.windings
