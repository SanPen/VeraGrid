"""Perfect transposition must reach the actual branch matrices, not just the catalogue."""
import numpy as np
import pytest
import VeraGridEngine.api as vge
from VeraGridEngine.IO.dgs.dgs_objects import TypTow
from VeraGridEngine.IO.dgs.dgs_to_veragrid import convert_dgs_to_overhead_line_type_geometrical_parameters


@pytest.mark.parametrize('earth_wire', (False, True))
def test_transposed_tower_matrices_and_roundtrip(earth_wire, tmp_path):
    grid = vge.MultiCircuit()
    wire = vge.Wire(r=0.12, diameter=22)
    grid.add_wire(wire)
    tower = vge.OverheadLineType(Vnom=132)
    for phase, xy in enumerate(((-4, 18), (0, 15), (3, 12)), 1):
        tower.add_wire_relationship(wire, *xy, phase=phase)
    if earth_wire:
        tower.add_wire_relationship(wire, 0, 24, phase=0)
    tower.compute()
    z, y = tower.z_abc.copy(), tower.y_abc.copy()
    tower.transposed = True
    tower.compute()
    # Analytical equal self/mutual values; the earth-wire contribution is retained.
    expected_z = np.full((3, 3), (z.sum() - np.trace(z)) / 6, dtype=complex)
    np.fill_diagonal(expected_z, np.trace(z) / 3)
    expected_y = np.full((3, 3), (y.sum() - np.trace(y)) / 6, dtype=complex)
    np.fill_diagonal(expected_y, np.trace(y) / 3)
    np.testing.assert_allclose(tower.z_abc, expected_z, atol=1e-13)
    np.testing.assert_allclose(tower.y_abc, expected_y, atol=1e-16)
    np.testing.assert_allclose(tower.z_seq - np.diag(np.diag(tower.z_seq)), 0, atol=1e-13)
    np.testing.assert_allclose(tower.get_ys(1, 100, 10, 132).values[1:, 1:],
                               np.linalg.inv(expected_z * 10 / (132**2 / 100)))
    grid.add_overhead_line(tower)
    path = str(tmp_path / 'transposed.veragrid')
    vge.save_file(grid, path)
    restored = vge.open_file(path).overhead_line_types[0]
    assert restored.transposed
    restored.compute()
    np.testing.assert_allclose(restored.z_nabc, tower.z_nabc)
    np.testing.assert_allclose(restored.y_nabc, tower.y_nabc)
    tower.transposed = False
    tower.compute()
    np.testing.assert_allclose(tower.z_abc, z)
    np.testing.assert_allclose(tower.y_abc, y)


def test_dgs_transposition_is_explicit_and_defaults_to_none():
    source = TypTow.parse_line('tower;3', {'FID': 0, 'iTransMode': 1})
    tower = convert_dgs_to_overhead_line_type_geometrical_parameters(source, {}, {}, 50)
    assert tower.transposed
    assert not convert_dgs_to_overhead_line_type_geometrical_parameters(TypTow(), {}, {}, 50).transposed
    for mode, circuits in ((1, 1), (2, 1), (3, 2)):
        source.iTransMode, source.nlcir = mode, circuits
        with pytest.raises(ValueError, match='unsupported TypTow transposition'):
            convert_dgs_to_overhead_line_type_geometrical_parameters(source, {}, {}, 50)
