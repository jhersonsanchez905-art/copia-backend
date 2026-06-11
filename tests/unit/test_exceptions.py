"""
Unit tests for domain exception classes.
Verifies codes, messages, and inheritance hierarchy.
"""
from app.exceptions import (
    AjustePendienteError,
    InsumoInsuficienteError,
    MajesaError,
    PermisoDenegadoError,
    VentaNoEncontradaError,
)


def test_majesa_error_default_code():
    err = MajesaError("algo salió mal")
    assert err.message == "algo salió mal"
    assert err.code == 400


def test_majesa_error_custom_code():
    err = MajesaError("no encontrado", 404)
    assert err.code == 404
    assert err.message == "no encontrado"


def test_majesa_error_is_exception():
    assert issubclass(MajesaError, Exception)


def test_insumo_insuficiente_inherits_majesa():
    err = InsumoInsuficienteError("stock bajo", 422)
    assert isinstance(err, MajesaError)
    assert err.code == 422


def test_venta_no_encontrada_includes_id():
    err = VentaNoEncontradaError(42)
    assert "42" in err.message
    assert err.code == 404


def test_venta_no_encontrada_different_ids():
    assert "1" in VentaNoEncontradaError(1).message
    assert "999" in VentaNoEncontradaError(999).message


def test_permiso_denegado_code():
    err = PermisoDenegadoError()
    assert err.code == 403


def test_permiso_denegado_inherits_majesa():
    assert isinstance(PermisoDenegadoError(), MajesaError)


def test_ajuste_pendiente_inherits_majesa():
    err = AjustePendienteError("hay ajuste pendiente aprobación")
    assert isinstance(err, MajesaError)


def test_all_subclasses_are_catchable_as_majesa():
    errors = [
        InsumoInsuficienteError("x", 400),
        VentaNoEncontradaError(1),
        PermisoDenegadoError(),
        AjustePendienteError("y"),
    ]
    for err in errors:
        assert isinstance(err, MajesaError)
        assert isinstance(err, Exception)
