"""
Unit tests for _build_snapshot in venta_service.
Verifies that the snapshot dict is correctly structured for any recipe version.
"""
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.venta_service import _build_snapshot


def _insumo(id, id_insumo, cantidad, id_unidad):
    d = MagicMock()
    d.id_receta_detalle_insumo = id
    d.id_insumo = id_insumo
    d.cantidad = Decimal(str(cantidad))
    d.id_unidad = id_unidad
    return d


def _subreceta(id, id_subreceta, cantidad, id_unidad):
    d = MagicMock()
    d.id_receta_detalle_subreceta = id
    d.id_subreceta = id_subreceta
    d.cantidad = Decimal(str(cantidad))
    d.id_unidad = id_unidad
    return d


def _version(id_receta_version=1, version=1, insumos=None, subrecetas=None):
    v = MagicMock()
    v.id_receta_version = id_receta_version
    v.version = version
    v.detalles_insumo = insumos or []
    v.detalles_subreceta = subrecetas or []
    return v


def test_snapshot_top_level_keys():
    snap = _build_snapshot(_version())
    assert "id_receta_version" in snap
    assert "version" in snap
    assert "detalles_insumo" in snap
    assert "detalles_subreceta" in snap


def test_snapshot_correct_ids():
    v = _version(id_receta_version=7, version=3)
    snap = _build_snapshot(v)
    assert snap["id_receta_version"] == 7
    assert snap["version"] == 3


def test_snapshot_empty_recipe():
    snap = _build_snapshot(_version())
    assert snap["detalles_insumo"] == []
    assert snap["detalles_subreceta"] == []


def test_snapshot_insumo_fields():
    v = _version(insumos=[_insumo(id=1, id_insumo=10, cantidad="0.500", id_unidad=3)])
    snap = _build_snapshot(v)
    row = snap["detalles_insumo"][0]
    assert row["id_receta_detalle_insumo"] == 1
    assert row["id_insumo"] == 10
    assert row["id_unidad"] == 3


def test_snapshot_cantidad_serialized_as_string():
    v = _version(insumos=[_insumo(1, 10, "0.75", 2)])
    snap = _build_snapshot(v)
    assert isinstance(snap["detalles_insumo"][0]["cantidad"], str)
    assert snap["detalles_insumo"][0]["cantidad"] == "0.75"


def test_snapshot_subreceta_fields():
    v = _version(subrecetas=[_subreceta(id=2, id_subreceta=5, cantidad="2.0", id_unidad=1)])
    snap = _build_snapshot(v)
    row = snap["detalles_subreceta"][0]
    assert row["id_receta_detalle_subreceta"] == 2
    assert row["id_subreceta"] == 5
    assert row["cantidad"] == "2.0"


def test_snapshot_multiple_insumos_count():
    insumos = [_insumo(i, i * 10, "1.0", 1) for i in range(1, 5)]
    snap = _build_snapshot(_version(insumos=insumos))
    assert len(snap["detalles_insumo"]) == 4


def test_snapshot_mixed_insumos_and_subrecetas():
    v = _version(
        insumos=[_insumo(1, 10, "1.0", 1), _insumo(2, 20, "0.5", 1)],
        subrecetas=[_subreceta(3, 5, "1.0", 2)],
    )
    snap = _build_snapshot(v)
    assert len(snap["detalles_insumo"]) == 2
    assert len(snap["detalles_subreceta"]) == 1
