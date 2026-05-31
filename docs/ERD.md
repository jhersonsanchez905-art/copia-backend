erDiagram

  ROL {
    int id_rol PK
    string nombre
    string descripcion
  }

  USUARIO {
    int id_usuario PK
    string clerk_id
    string nombre
    string correo
    int id_rol FK
    boolean activo
    datetime fecha_creacion
  }

  CLIENTE {
    int id_cliente PK
    string nombre
    string apellido
    string telefono
    string correo
    string direccion
    string numero_documento
    datetime fecha_registro
    boolean activo
    string observaciones
  }

  PROVEEDOR {
    int id_proveedor PK
    string nombre
    string contacto
    string telefono
    string correo
    boolean activo
  }

  INSUMO_PROVEEDOR {
    int id_insumo_proveedor PK
    int id_insumo FK
    int id_proveedor FK
    boolean es_principal
    decimal precio_referencia
    int dias_entrega
  }

  MARCA {
    int id_marca PK
    string nombre
  }

  UNIDAD_MEDIDA {
    int id_unidad PK
    string nombre
    string abreviatura
  }

  CLASIFICACION {
    int id_clasificacion PK
    string nombre
    string descripcion
  }

  INSUMO {
    int id_insumo PK
    string nombre
    string presentacion
    int id_unidad FK
    int contador_unidades
    decimal precio
    decimal pct_rendimiento
    decimal precio_real
    decimal precio_por_udm
    int id_clasificacion FK
    int id_marca FK
    decimal stock_actual
    decimal stock_minimo
    decimal stock_maximo
    decimal punto_pedido
    decimal cantidad_a_pedir
    int dias_anticipacion
    string semaforo
    boolean activo
  }

  ORDEN_COMPRA {
    int id_orden PK
    int id_proveedor FK
    int id_usuario FK
    datetime fecha_creacion
    datetime fecha_esperada
    string estado
    string observaciones
  }

  ORDEN_COMPRA_DETALLE {
    int id_detalle PK
    int id_orden FK
    int id_insumo FK
    decimal cantidad_solicitada
    decimal cantidad_recibida
    decimal precio_unitario
    string observacion
  }

  SUBRECETA {
    int id_subreceta PK
    string nombre
    int porciones
    decimal peso_porcion_gr
    decimal costo_total
    decimal stock_actual
    boolean activo
  }

  SUBRECETA_INGREDIENTE {
    int id_subreceta_ing PK
    int id_subreceta FK
    int id_insumo FK
    int id_unidad FK
    decimal cantidad
    decimal costo_unitario
    decimal costo_total
    decimal pct_participacion
  }

  CATEGORIA {
    int id_categoria PK
    string nombre
  }

  PRODUCTO {
    int id_producto PK
    string nombre
    int id_categoria FK
    decimal precio
    int num_porciones
    string url_foto
    decimal pct_prima_real
    boolean activo
    date fecha_lanzamiento
    datetime fecha_modificacion
  }

  RECETA_VERSION {
    int id_receta_version PK
    int id_producto FK
    int version
    boolean vigente
    datetime fecha_creacion
    decimal costo_total
    int tiempo_preparacion_min
    string instrucciones_generales
    string observaciones
  }

  RECETA_PASO {
    int id_paso PK
    int id_receta_version FK
    int numero_paso
    string titulo
    string descripcion
    int tiempo_estimado_min
  }

  RECETA_DETALLE {
    int id_receta_detalle PK
    int id_receta_version FK
    int id_insumo FK
    int id_subreceta FK
    int id_unidad FK
    decimal cantidad
    decimal costo_unitario
    decimal costo_total
    decimal pct_participacion
  }

  METODO_PAGO {
    int id_metodo_pago PK
    string nombre
    boolean requiere_comprobante
    boolean activo
  }

  APERTURA_CAJA {
    int id_apertura PK
    int id_usuario FK
    string turno
    date fecha
    decimal monto_inicial
    datetime hora_apertura
    string observaciones
  }

  CIERRE_CAJA {
    int id_cierre PK
    int id_apertura FK
    int id_usuario FK
    string turno
    date fecha
    decimal total_general
    decimal total_transacciones
    decimal diferencia
    datetime hora_cierre
    string observaciones
  }

  CIERRE_CAJA_DETALLE {
    int id_detalle PK
    int id_cierre FK
    int id_metodo_pago FK
    decimal total_esperado
    decimal total_contado
    decimal diferencia
  }

  VENTA {
    int id_venta PK
    int id_apertura FK
    datetime fecha
    string turno
    int id_usuario FK
    int id_cliente FK
    decimal subtotal
    decimal total
    string estado
  }

  ITEM_VENTA {
    int id_item_venta PK
    int id_venta FK
    int id_producto FK
    int id_receta_version FK
    json receta_snapshot
    int cantidad
    decimal precio_unitario
    decimal subtotal
  }

  PAGO {
    int id_pago PK
    int id_venta FK
    int id_metodo_pago FK
    decimal monto
    string url_comprobante
    string estado_validacion
  }

  FACTURA {
    int id_factura PK
    int id_venta FK
    string numero
    datetime fecha_emision
    decimal total
    string url_pdf
  }

  DEVOLUCION {
    int id_devolucion PK
    int id_venta FK
    int id_item_venta FK
    datetime fecha
    string motivo
    string observacion
    string estado
    boolean reintegra_stock
    int aprobado_por FK
  }

  MOVIMIENTO_INVENTARIO {
    int id_movimiento PK
    int id_insumo FK
    int id_subreceta FK
    string tipo
    decimal cantidad
    string motivo
    string observacion
    boolean afecta_stock
    decimal cantidad_anterior
    decimal cantidad_nueva
    string estado
    int id_venta FK
    int id_orden_compra FK
    int id_usuario FK
    int id_aprobador FK
    datetime fecha
  }

  ALERTA {
    int id_alerta PK
    int id_insumo FK
    string estado
    string semaforo
    decimal cantidad_a_pedir
    int id_orden_compra FK
    datetime fecha_creacion
    datetime fecha_resolucion
  }

  TIPO_CAMPANA {
    int id_tipo_campana PK
    string nombre
    string descripcion
  }

  CANAL {
    int id_canal PK
    string nombre
  }

  CAMPANA {
    int id_campana PK
    string nombre
    string descripcion
    int id_tipo_campana FK
    date fecha_inicio
    date fecha_fin
    int baseline_dias
    decimal presupuesto
    string estado
    int id_usuario FK
    datetime fecha_creacion
  }

  CAMPANA_CANAL {
    int id_campana FK
    int id_canal FK
  }

  CAMPANA_PRODUCTO {
    int id_campana_producto PK
    int id_campana FK
    int id_producto
    decimal descuento_pct
  }

  ROL ||--o{ USUARIO : tiene
  CLIENTE ||--o{ VENTA : realiza
  USUARIO ||--o{ VENTA : registra
  USUARIO ||--o{ MOVIMIENTO_INVENTARIO : registra
  USUARIO ||--o{ MOVIMIENTO_INVENTARIO : aprueba
  USUARIO ||--o{ DEVOLUCION : aprueba
  USUARIO ||--o{ APERTURA_CAJA : abre
  USUARIO ||--o{ CIERRE_CAJA : cierra
  USUARIO ||--o{ ORDEN_COMPRA : genera
  USUARIO ||--o{ CAMPANA : crea

  APERTURA_CAJA ||--|| CIERRE_CAJA : cierra
  APERTURA_CAJA ||--o{ VENTA : agrupa

  CIERRE_CAJA ||--o{ CIERRE_CAJA_DETALLE : desglosa
  METODO_PAGO ||--o{ CIERRE_CAJA_DETALLE : metodo
  METODO_PAGO ||--o{ PAGO : metodo

  CATEGORIA ||--o{ PRODUCTO : clasifica
  CLASIFICACION ||--o{ INSUMO : agrupa
  MARCA ||--o{ INSUMO : pertenece
  UNIDAD_MEDIDA ||--o{ INSUMO : usa
  UNIDAD_MEDIDA ||--o{ SUBRECETA_INGREDIENTE : medida
  UNIDAD_MEDIDA ||--o{ RECETA_DETALLE : medida

  PROVEEDOR ||--o{ INSUMO_PROVEEDOR : registrado_en
  INSUMO ||--o{ INSUMO_PROVEEDOR : tiene
  PROVEEDOR ||--o{ ORDEN_COMPRA : recibe
  ORDEN_COMPRA ||--o{ ORDEN_COMPRA_DETALLE : contiene
  INSUMO ||--o{ ORDEN_COMPRA_DETALLE : solicitado

  SUBRECETA ||--o{ SUBRECETA_INGREDIENTE : contiene
  INSUMO ||--o{ SUBRECETA_INGREDIENTE : ingrediente

  PRODUCTO ||--o{ RECETA_VERSION : tiene
  RECETA_VERSION ||--o{ RECETA_DETALLE : compone
  RECETA_VERSION ||--o{ RECETA_PASO : prepara
  INSUMO ||--o{ RECETA_DETALLE : usa
  SUBRECETA ||--o{ RECETA_DETALLE : reutiliza

  VENTA ||--o{ ITEM_VENTA : incluye
  PRODUCTO ||--o{ ITEM_VENTA : vendido
  RECETA_VERSION ||--o{ ITEM_VENTA : receta_usada
  VENTA ||--o{ PAGO : recibe
  VENTA ||--|| FACTURA : genera
  VENTA ||--o{ DEVOLUCION : tiene
  ITEM_VENTA ||--o{ DEVOLUCION : devuelve

  INSUMO ||--o{ MOVIMIENTO_INVENTARIO : movimiento
  SUBRECETA ||--o{ MOVIMIENTO_INVENTARIO : movimiento
  VENTA ||--o{ MOVIMIENTO_INVENTARIO : origen
  ORDEN_COMPRA ||--o{ MOVIMIENTO_INVENTARIO : origen

  INSUMO ||--o{ ALERTA : genera
  ALERTA ||--o{ ORDEN_COMPRA : dispara

  TIPO_CAMPANA ||--o{ CAMPANA : clasifica
  CAMPANA ||--o{ CAMPANA_CANAL : usa
  CANAL ||--o{ CAMPANA_CANAL : en
  CAMPANA ||--o{ CAMPANA_PRODUCTO : incluye