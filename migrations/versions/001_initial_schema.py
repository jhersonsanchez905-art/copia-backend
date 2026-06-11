"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-10

Creates schemas pos and mkt with all tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Schemas ───────────────────────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS pos")
    op.execute("CREATE SCHEMA IF NOT EXISTS mkt")

    # ── Enum types ────────────────────────────────────────────────────────────
    estado_orden_compra = postgresql.ENUM(
        "BORRADOR", "ENVIADA", "RECIBIDA_PARCIAL", "RECIBIDA_TOTAL", "CANCELADA",
        name="estadoordencompra",
        schema="pos",
        create_type=False,
    )
    estado_orden_compra.create(op.get_bind(), checkfirst=True)

    # ── Catálogo base (sin dependencias entre sí) ─────────────────────────────
    op.create_table(
        "rol",
        sa.Column("id_rol", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "cliente",
        sa.Column("id_cliente", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("apellido", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("correo", sa.String(), nullable=True),
        sa.Column("direccion", sa.String(), nullable=True),
        sa.Column("numero_documento", sa.String(), nullable=True),
        sa.Column("fecha_registro", sa.DateTime(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "marca",
        sa.Column("id_marca", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        schema="pos",
    )

    op.create_table(
        "unidad_medida",
        sa.Column("id_unidad", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("abreviatura", sa.String(), nullable=False),
        schema="pos",
    )

    op.create_table(
        "clasificacion",
        sa.Column("id_clasificacion", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "categoria",
        sa.Column("id_categoria", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        schema="pos",
    )

    op.create_table(
        "metodo_pago",
        sa.Column("id_metodo_pago", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("requiere_comprobante", sa.Boolean(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "proveedor",
        sa.Column("id_proveedor", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("contacto", sa.String(), nullable=True),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("correo", sa.String(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "servicio_adicional",
        sa.Column("id_servicio", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("valor", sa.Numeric(14, 2), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_servicio_nombre"),
        schema="pos",
    )

    op.create_table(
        "mesa",
        sa.Column("id_mesa", sa.Integer(), primary_key=True, index=True),
        sa.Column("numero", sa.String(10), nullable=False),
        sa.Column("capacidad", sa.Integer(), nullable=False),
        sa.Column("zona", sa.String(60), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="disponible"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("numero", name="uq_mesa_numero"),
        schema="pos",
    )

    # ── usuario (depende de rol) ───────────────────────────────────────────────
    op.create_table(
        "usuario",
        sa.Column("id_usuario", sa.Integer(), primary_key=True, index=True),
        sa.Column("clerk_id", sa.String(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("correo", sa.String(), nullable=False),
        sa.Column("id_rol", sa.Integer(), sa.ForeignKey("pos.rol.id_rol"), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=True),
        schema="pos",
    )

    # ── insumo (depende de unidad_medida, clasificacion, marca) ───────────────
    op.create_table(
        "insumo",
        sa.Column("id_insumo", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("presentacion", sa.String(120), nullable=True),
        sa.Column("id_unidad", sa.Integer(), sa.ForeignKey("pos.unidad_medida.id_unidad"), nullable=False),
        sa.Column("id_clasificacion", sa.Integer(), sa.ForeignKey("pos.clasificacion.id_clasificacion"), nullable=False),
        sa.Column("id_marca", sa.Integer(), sa.ForeignKey("pos.marca.id_marca"), nullable=True),
        sa.Column("contador_unidades", sa.Integer(), nullable=True),
        sa.Column("precio", sa.Numeric(14, 4), nullable=True),
        sa.Column("pct_rendimiento", sa.Numeric(5, 2), nullable=True),
        sa.Column("umbral_minimo", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("stock_minimo", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("stock_maximo", sa.Numeric(12, 4), nullable=True),
        sa.Column("punto_pedido", sa.Numeric(12, 4), nullable=True),
        sa.Column("cantidad_a_pedir", sa.Numeric(12, 4), nullable=True),
        sa.Column("dias_anticipacion", sa.Integer(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_insumo_nombre"),
        schema="pos",
    )

    op.create_table(
        "insumo_proveedor",
        sa.Column("id_insumo_proveedor", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("id_proveedor", sa.Integer(), sa.ForeignKey("pos.proveedor.id_proveedor"), nullable=False),
        sa.Column("es_principal", sa.Boolean(), nullable=True),
        sa.Column("precio_referencia", sa.Numeric(), nullable=True),
        sa.Column("dias_entrega", sa.Integer(), nullable=True),
        schema="pos",
    )

    # ── subreceta ──────────────────────────────────────────────────────────────
    op.create_table(
        "subreceta",
        sa.Column("id_subreceta", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("porciones", sa.Integer(), nullable=True),
        sa.Column("peso_porcion_gr", sa.Numeric(12, 4), nullable=True),
        sa.Column("costo_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("nombre", name="uq_subreceta_nombre"),
        schema="pos",
    )

    op.create_table(
        "subreceta_ingrediente",
        sa.Column("id_subreceta_ing", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_subreceta", sa.Integer(), sa.ForeignKey("pos.subreceta.id_subreceta"), nullable=False),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("id_unidad", sa.Integer(), sa.ForeignKey("pos.unidad_medida.id_unidad"), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("costo_unitario", sa.Numeric(14, 4), nullable=True),
        sa.Column("costo_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("pct_participacion", sa.Numeric(5, 2), nullable=True),
        schema="pos",
    )

    # ── stock (depende de insumo) ──────────────────────────────────────────────
    op.create_table(
        "stock",
        sa.Column("id_stock", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("semaforo", sa.String(10), nullable=False, server_default="verde"),
        sa.Column("ultima_actualizacion", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("id_insumo", name="uq_stock_insumo"),
        schema="pos",
    )

    # ── producto (depende de categoria) ───────────────────────────────────────
    op.create_table(
        "producto",
        sa.Column("id_producto", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("id_categoria", sa.Integer(), sa.ForeignKey("pos.categoria.id_categoria"), nullable=True),
        sa.Column("precio", sa.Numeric(), nullable=False),
        sa.Column("num_porciones", sa.Integer(), nullable=True),
        sa.Column("url_foto", sa.String(), nullable=True),
        sa.Column("pct_prima_real", sa.Numeric(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=True),
        sa.Column("fecha_lanzamiento", sa.Date(), nullable=True),
        sa.Column("fecha_modificacion", sa.DateTime(), nullable=True),
        schema="pos",
    )

    # ── receta_version (depende de producto) ──────────────────────────────────
    op.create_table(
        "receta_version",
        sa.Column("id_receta_version", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_producto", sa.Integer(), sa.ForeignKey("pos.producto.id_producto"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("vigente", sa.Boolean(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("costo_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("tiempo_preparacion_min", sa.Integer(), nullable=True),
        sa.Column("instrucciones_generales", sa.String(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "receta_detalle_insumo",
        sa.Column("id_receta_detalle_insumo", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_receta_version", sa.Integer(), sa.ForeignKey("pos.receta_version.id_receta_version"), nullable=False),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("id_unidad", sa.Integer(), sa.ForeignKey("pos.unidad_medida.id_unidad"), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("costo_unitario", sa.Numeric(14, 4), nullable=True),
        sa.Column("costo_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("pct_participacion", sa.Numeric(5, 2), nullable=True),
        schema="pos",
    )

    op.create_table(
        "receta_detalle_subreceta",
        sa.Column("id_receta_detalle_subreceta", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_receta_version", sa.Integer(), sa.ForeignKey("pos.receta_version.id_receta_version"), nullable=False),
        sa.Column("id_subreceta", sa.Integer(), sa.ForeignKey("pos.subreceta.id_subreceta"), nullable=False),
        sa.Column("id_unidad", sa.Integer(), sa.ForeignKey("pos.unidad_medida.id_unidad"), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("costo_unitario", sa.Numeric(14, 4), nullable=True),
        sa.Column("costo_total", sa.Numeric(14, 4), nullable=True),
        sa.Column("pct_participacion", sa.Numeric(5, 2), nullable=True),
        schema="pos",
    )

    op.create_table(
        "receta_paso",
        sa.Column("id_paso", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_receta_version", sa.Integer(), sa.ForeignKey("pos.receta_version.id_receta_version"), nullable=False),
        sa.Column("numero_paso", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("tiempo_estimado_min", sa.Integer(), nullable=True),
        schema="pos",
    )

    # ── orden_compra (depende de proveedor, usuario) ───────────────────────────
    op.create_table(
        "orden_compra",
        sa.Column("id_orden_compra", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_proveedor", sa.Integer(), sa.ForeignKey("pos.proveedor.id_proveedor"), nullable=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("numero_orden", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("fecha_emision", sa.Date(), nullable=True),
        sa.Column("fecha_entrega_esperada", sa.Date(), nullable=True),
        sa.Column("fecha_recepcion_real", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            postgresql.ENUM(
                "BORRADOR", "ENVIADA", "RECIBIDA_PARCIAL", "RECIBIDA_TOTAL", "CANCELADA",
                name="estadoordencompra",
                schema="pos",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=True),
        sa.Column("impuestos", sa.Numeric(16, 2), nullable=True),
        sa.Column("total", sa.Numeric(16, 2), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "orden_compra_detalle",
        sa.Column("id_detalle", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_orden_compra", sa.Integer(), sa.ForeignKey("pos.orden_compra.id_orden_compra"), nullable=False),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("cantidad_solicitada", sa.Numeric(12, 4), nullable=False),
        sa.Column("cantidad_recibida", sa.Numeric(12, 4), nullable=True),
        sa.Column("precio_unitario", sa.Numeric(14, 4), nullable=True),
        sa.Column("subtotal_linea", sa.Numeric(16, 2), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=True),
        schema="pos",
    )

    # ── reserva (depende de mesa, cliente, usuario) ───────────────────────────
    op.create_table(
        "reserva",
        sa.Column("id_reserva", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_mesa", sa.Integer(), sa.ForeignKey("pos.mesa.id_mesa"), nullable=False),
        sa.Column("id_cliente", sa.Integer(), sa.ForeignKey("pos.cliente.id_cliente"), nullable=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("num_personas", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    # ── pedido (depende de mesa, usuario, reserva) ────────────────────────────
    op.create_table(
        "pedido",
        sa.Column("id_pedido", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_mesa", sa.Integer(), sa.ForeignKey("pos.mesa.id_mesa"), nullable=False),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("id_reserva", sa.Integer(), sa.ForeignKey("pos.reserva.id_reserva"), nullable=True),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="abierto"),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "pedido_item",
        sa.Column("id_pedido_item", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_pedido", sa.Integer(), sa.ForeignKey("pos.pedido.id_pedido"), nullable=False),
        sa.Column("id_producto", sa.Integer(), sa.ForeignKey("pos.producto.id_producto"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(14, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        schema="pos",
    )

    op.create_table(
        "pedido_servicio",
        sa.Column("id_pedido_servicio", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_pedido", sa.Integer(), sa.ForeignKey("pos.pedido.id_pedido"), nullable=False),
        sa.Column("id_servicio", sa.Integer(), sa.ForeignKey("pos.servicio_adicional.id_servicio"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("valor_unitario", sa.Numeric(14, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    # ── caja (depende de usuario) ──────────────────────────────────────────────
    op.create_table(
        "apertura_caja",
        sa.Column("id_apertura", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("turno", sa.String(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("monto_inicial", sa.Numeric(), nullable=False),
        sa.Column("hora_apertura", sa.DateTime(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "cierre_caja",
        sa.Column("id_cierre", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_apertura", sa.Integer(), sa.ForeignKey("pos.apertura_caja.id_apertura"), nullable=False, unique=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("turno", sa.String(), nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("total_general", sa.Numeric(), nullable=True),
        sa.Column("total_transacciones", sa.Numeric(), nullable=True),
        sa.Column("diferencia", sa.Numeric(), nullable=True),
        sa.Column("hora_cierre", sa.DateTime(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "cierre_caja_detalle",
        sa.Column("id_detalle", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_cierre", sa.Integer(), sa.ForeignKey("pos.cierre_caja.id_cierre"), nullable=False),
        sa.Column("id_metodo_pago", sa.Integer(), sa.ForeignKey("pos.metodo_pago.id_metodo_pago"), nullable=False),
        sa.Column("total_esperado", sa.Numeric(), nullable=True),
        sa.Column("total_contado", sa.Numeric(), nullable=True),
        sa.Column("diferencia", sa.Numeric(), nullable=True),
        schema="pos",
    )

    # ── venta (depende de apertura_caja, pedido, usuario, cliente) ────────────
    op.create_table(
        "venta",
        sa.Column("id_venta", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_apertura", sa.Integer(), sa.ForeignKey("pos.apertura_caja.id_apertura"), nullable=False),
        sa.Column("id_pedido", sa.Integer(), sa.ForeignKey("pos.pedido.id_pedido"), nullable=False, unique=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("id_cliente", sa.Integer(), sa.ForeignKey("pos.cliente.id_cliente"), nullable=True),
        sa.Column("turno", sa.String(20), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="abierta"),
        schema="pos",
    )

    op.create_table(
        "item_venta",
        sa.Column("id_item_venta", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_venta", sa.Integer(), sa.ForeignKey("pos.venta.id_venta"), nullable=False),
        sa.Column("id_producto", sa.Integer(), sa.ForeignKey("pos.producto.id_producto"), nullable=False),
        sa.Column("id_receta_version", sa.Integer(), sa.ForeignKey("pos.receta_version.id_receta_version"), nullable=False),
        sa.Column("receta_snapshot", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(16, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(16, 2), nullable=False),
        schema="pos",
    )

    op.create_table(
        "pago",
        sa.Column("id_pago", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_venta", sa.Integer(), sa.ForeignKey("pos.venta.id_venta"), nullable=False),
        sa.Column("id_metodo_pago", sa.Integer(), sa.ForeignKey("pos.metodo_pago.id_metodo_pago"), nullable=False),
        sa.Column("id_usuario_validacion", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("monto", sa.Numeric(16, 2), nullable=False),
        sa.Column("url_comprobante", sa.String(), nullable=True),
        sa.Column("estado_validacion", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("fecha_validacion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    op.create_table(
        "factura",
        sa.Column("id_factura", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_venta", sa.Integer(), sa.ForeignKey("pos.venta.id_venta"), nullable=False, unique=True),
        sa.Column("numero", sa.String(), nullable=False, unique=True),
        sa.Column("fecha_emision", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total", sa.Numeric(16, 2), nullable=False),
        sa.Column("url_pdf", sa.String(), nullable=True),
        schema="pos",
    )

    op.create_table(
        "devolucion",
        sa.Column("id_devolucion", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_venta", sa.Integer(), sa.ForeignKey("pos.venta.id_venta"), nullable=False),
        sa.Column("id_item_venta", sa.Integer(), sa.ForeignKey("pos.item_venta.id_item_venta"), nullable=False),
        sa.Column("id_aprobador", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("observacion", sa.String(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("reintegra_stock", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    # ── inventario (depende de insumo, venta, orden_compra, usuario) ──────────
    op.create_table(
        "movimiento_inventario",
        sa.Column("id_movimiento", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("cantidad_anterior", sa.Numeric(12, 4), nullable=False),
        sa.Column("cantidad_nueva", sa.Numeric(12, 4), nullable=False),
        sa.Column("motivo", sa.String(), nullable=True),
        sa.Column("observacion", sa.String(), nullable=True),
        sa.Column("id_venta", sa.Integer(), sa.ForeignKey("pos.venta.id_venta"), nullable=True),
        sa.Column("id_orden_compra", sa.Integer(), sa.ForeignKey("pos.orden_compra.id_orden_compra"), nullable=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        schema="pos",
    )

    op.create_table(
        "alerta",
        sa.Column("id_alerta", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="stock_bajo"),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activa"),
        sa.Column("semaforo", sa.String(10), nullable=False),
        sa.Column("cantidad_a_pedir", sa.Numeric(12, 4), nullable=True),
        sa.Column("id_orden_compra", sa.Integer(), sa.ForeignKey("pos.orden_compra.id_orden_compra"), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    op.create_table(
        "ajuste_inventario",
        sa.Column("id_ajuste", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("id_usuario_solicita", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=False),
        sa.Column("id_usuario_aprueba", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("observacion", sa.String(), nullable=True),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("fecha_solicitud", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    op.create_table(
        "alerta_perecible",
        sa.Column("id_alerta_perecible", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_insumo", sa.Integer(), sa.ForeignKey("pos.insumo.id_insumo"), nullable=False),
        sa.Column("id_stock", sa.Integer(), sa.ForeignKey("pos.stock.id_stock"), nullable=False),
        sa.Column("fecha_ingreso", sa.Date(), nullable=False),
        sa.Column("dias_en_inventario", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="activa"),
        sa.Column("accion_sugerida", sa.String(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fecha_resolucion", sa.DateTime(timezone=True), nullable=True),
        schema="pos",
    )

    # ── auditoria (depende de usuario) ────────────────────────────────────────
    op.create_table(
        "auditoria",
        sa.Column("id_auditoria", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("entidad", sa.String(60), nullable=False),
        sa.Column("id_registro", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="exitoso"),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        schema="pos",
    )

    # ── Schema mkt ────────────────────────────────────────────────────────────
    op.create_table(
        "tipo_campana",
        sa.Column("id_tipo_campana", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        schema="mkt",
    )

    op.create_table(
        "canal",
        sa.Column("id_canal", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        schema="mkt",
    )

    op.create_table(
        "campana",
        sa.Column("id_campana", sa.Integer(), primary_key=True, index=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("id_tipo_campana", sa.Integer(), sa.ForeignKey("mkt.tipo_campana.id_tipo_campana"), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("baseline_dias", sa.Integer(), nullable=True),
        sa.Column("presupuesto", sa.Numeric(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("id_usuario", sa.Integer(), sa.ForeignKey("pos.usuario.id_usuario"), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=True),
        schema="mkt",
    )

    op.create_table(
        "campana_canal",
        sa.Column("id_campana", sa.Integer(), sa.ForeignKey("mkt.campana.id_campana"), primary_key=True),
        sa.Column("id_canal", sa.Integer(), sa.ForeignKey("mkt.canal.id_canal"), primary_key=True),
        schema="mkt",
    )

    op.create_table(
        "campana_producto",
        sa.Column("id_campana_producto", sa.Integer(), primary_key=True, index=True),
        sa.Column("id_campana", sa.Integer(), sa.ForeignKey("mkt.campana.id_campana"), nullable=True),
        sa.Column("id_producto", sa.Integer(), nullable=True),
        sa.Column("descuento_pct", sa.Numeric(), nullable=True),
        schema="mkt",
    )


def downgrade() -> None:
    # mkt
    op.drop_table("campana_producto", schema="mkt")
    op.drop_table("campana_canal", schema="mkt")
    op.drop_table("campana", schema="mkt")
    op.drop_table("canal", schema="mkt")
    op.drop_table("tipo_campana", schema="mkt")

    # pos — inverse order
    op.drop_table("auditoria", schema="pos")
    op.drop_table("alerta_perecible", schema="pos")
    op.drop_table("ajuste_inventario", schema="pos")
    op.drop_table("alerta", schema="pos")
    op.drop_table("movimiento_inventario", schema="pos")
    op.drop_table("devolucion", schema="pos")
    op.drop_table("factura", schema="pos")
    op.drop_table("pago", schema="pos")
    op.drop_table("item_venta", schema="pos")
    op.drop_table("venta", schema="pos")
    op.drop_table("cierre_caja_detalle", schema="pos")
    op.drop_table("cierre_caja", schema="pos")
    op.drop_table("apertura_caja", schema="pos")
    op.drop_table("pedido_servicio", schema="pos")
    op.drop_table("pedido_item", schema="pos")
    op.drop_table("pedido", schema="pos")
    op.drop_table("reserva", schema="pos")
    op.drop_table("orden_compra_detalle", schema="pos")
    op.drop_table("orden_compra", schema="pos")
    op.drop_table("receta_paso", schema="pos")
    op.drop_table("receta_detalle_subreceta", schema="pos")
    op.drop_table("receta_detalle_insumo", schema="pos")
    op.drop_table("receta_version", schema="pos")
    op.drop_table("producto", schema="pos")
    op.drop_table("stock", schema="pos")
    op.drop_table("subreceta_ingrediente", schema="pos")
    op.drop_table("subreceta", schema="pos")
    op.drop_table("insumo_proveedor", schema="pos")
    op.drop_table("insumo", schema="pos")
    op.drop_table("usuario", schema="pos")
    op.drop_table("proveedor", schema="pos")
    op.drop_table("servicio_adicional", schema="pos")
    op.drop_table("mesa", schema="pos")
    op.drop_table("metodo_pago", schema="pos")
    op.drop_table("categoria", schema="pos")
    op.drop_table("clasificacion", schema="pos")
    op.drop_table("unidad_medida", schema="pos")
    op.drop_table("marca", schema="pos")
    op.drop_table("cliente", schema="pos")
    op.drop_table("rol", schema="pos")

    op.execute("DROP TYPE IF EXISTS pos.estadoordencompra")
    op.execute("DROP SCHEMA IF EXISTS mkt")
    op.execute("DROP SCHEMA IF EXISTS pos")
