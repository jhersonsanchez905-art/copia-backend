"""
__init__.py
Exporta todos los modelos del paquete app.models.
"""
# ruff: noqa: F401
# catálogos base — sin dependencias externas
from app.models.catalogo import (
    Rol,
    Usuario,
    Cliente,
    Marca,
    UnidadMedida,
    Clasificacion,
    Categoria,
    MetodoPago,
)
 
from app.models.proveedor import (
    Proveedor,
    InsumoProveedor,
)
 
# insumos — depende de catálogos y proveedor
from app.models.insumo import (
    Insumo,
    Subreceta,
    SubrecetaIngrediente,
)
 
# stock — depende de insumo
from app.models.stock import Stock
 
# producto y receta — depende de catálogos e insumo
from app.models.producto import Producto
 
from app.models.receta import (
    RecetaVersion,
    RecetaDetalleInsumo,
    RecetaDetalleSubreceta,
    RecetaPaso,
)
 
# orden de compra — depende de insumo y proveedor
from app.models.orden_compra import (
    EstadoOrdenCompra,
    OrdenCompra,
    OrdenCompraDetalle,
)
 
# mesa, reserva y pedido — depende de producto y usuario
from app.models.mesa import Mesa, Reserva
 
from app.models.servicio_adicional import ServicioAdicional
 
from app.models.pedido import Pedido, PedidoItem, PedidoServicio
 
# caja — depende de usuario
from app.models.caja import (
    AperturaCaja,
    CierreCaja,
    CierreCajaDetalle,
)
 
# venta — depende de pedido, caja, producto y receta
from app.models.venta import (
    Venta,
    ItemVenta,
    Pago,
    Factura,
    Devolucion,
)
 
# inventario — depende de insumo, venta y orden de compra
from app.models.inventario import (
    MovimientoInventario,
    Alerta,
)
 
from app.models.ajuste_inventario import AjusteInventario
from app.models.alerta_perecible import AlertaPerecible
 
# campañas — depende de producto y usuario
from app.models.campanas import (
    TipoCampana,
    Canal,
    Campana,
    CampanaCanal,
    CampanaProducto,
)
 
# auditoría — depende de usuario, va al final
from app.models.auditoria import Auditoria








