# Módulo BI — Documentación técnica para el equipo backend

> **Proyecto:** MAJESA · **Área:** Business Intelligence
> **Autor:** Jherson Sanchez · **Fecha:** 2026-06-12
>
> Este documento describe qué hace el módulo BI, qué archivos contiene,
> y qué archivos fuera de `app/bi/` fueron modificados y por qué.

---

## 1. Qué es el módulo BI

El módulo BI es un conjunto de **7 endpoints** dentro del backend FastAPI que
alimentan el dashboard de Business Intelligence. El módulo:

- Calcula métricas de negocio (margen por producto, picos de venta por hora,
  recomendaciones de compra, señales de precio, alertas de insumos compartidos)
- Las calcula **una vez al día** (ETL nocturno a las 2 am Colombia)
- Las almacena en tablas de resumen (`bi.resumen_*`) dentro de un esquema
  separado `bi` en la misma base de datos Neon
- Los endpoints GET solo hacen `SELECT *` a esas tablas — sin lógica pesada

---

## 2. Estructura de la carpeta `app/bi/`

```
app/bi/                     ← TODO el código BI vive aquí
├── __init__.py             ← paquete Python (vacío)
├── models.py               ← 10 clases SQLAlchemy (4 fact + 6 summary tables)
├── schemas.py              ← 8 modelos Pydantic (contratos JSON de los endpoints)
├── repo.py                 ← 6 funciones de lectura (SELECT a tablas resumen)
├── etl_service.py          ← ETL procesar_dia(): 4 KPIs + 6 rebuilds + webhook
├── service.py              ← capa de orquestación entre router y repo/ETL
├── router.py               ← 7 endpoints (6 GET + 1 POST protegido)
└── ruff.toml               ← linter estricto solo para esta carpeta (PEP 257)
```

**Regla:** solo el equipo BI modifica archivos dentro de `app/bi/`.
Todos los archivos llevan un header que lo indica.

---

## 3. Endpoints expuestos

| Método | Ruta | Qué devuelve |
|--------|------|-------------|
| GET | `/api/v1/bi/ranking-productos` | Ranking de productos por margen y volumen (30 días) |
| GET | `/api/v1/bi/heatmap` | Promedios de venta por hora y día de semana (90 días) |
| GET | `/api/v1/bi/recomendacion-compra` | Recomendación de compra por insumo activo |
| GET | `/api/v1/bi/senales-precio` | Productos con margen bajo y volumen alto |
| GET | `/api/v1/bi/testeo-productos` | Serie diaria de productos nuevos (60 días) |
| GET | `/api/v1/bi/warnings-insumo` | Alertas de insumo compartido con margen bajo |
| POST | `/api/v1/bi/procesar-dia` | Dispara el ETL (protegido con `X-Cron-Secret`) |

---

## 4. Archivos modificados FUERA de `app/bi/` — justificación

Estos son los **únicos** archivos que se tocaron fuera de la carpeta BI.
Cada cambio es mínimo y necesario para que el módulo funcione dentro
de la arquitectura FastAPI existente.

### 4.1 `app/main.py` — 2 cambios

**Cambio 1 — Fix de imports faltantes (preexistente, no es de BI):**
```python
# Se agregaron imports que faltaban y hacían que la app no arrancara:
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
```
*Sin esto, la app crasheaba al iniciar. El bug existía antes del módulo BI.*

**Cambio 2 — Registro del router BI:**
```python
from app.bi import router as bi_router
# ...
app.include_router(bi_router.router, prefix=_V1)
```
*Sin esto, FastAPI no conoce los endpoints BI. Es una línea de import y
una línea de registro — el mismo patrón que usan todos los demás routers.*

### 4.2 `app/config.py` — 2 variables nuevas

```python
# ── Módulo BI ─────────────────────────────────────────────
VERCEL_REVALIDATE_URL: str = "not-configured"
REVALIDATE_SECRET: str = "not-configured"
```
*El ETL necesita estas variables para notificar al frontend (Vercel) que
purgue su caché cuando las métricas se actualizan. Los valores por defecto
son `"not-configured"` — no rompen nada si no están en el `.env`.*

### 4.3 `app/models/__init__.py` — 1 línea

```python
import app.bi.models as _bi_models  # noqa: F401, E402
```
*Sin esta línea, Alembic no ve las tablas `bi.*` en los modelos. Cuando
cualquier compañero corra `alembic revision --autogenerate`, propondría
borrar todas las tablas BI porque no las encuentra. Esta línea lo previene.
No importa lógica, no crea dependencias, solo hace visibles los modelos.*

### 4.4 `migrations/versions/` — 2 archivos nuevos

**`2c4001937e5e_merge_heads_before_bi_schema.py`:**
*Merge de los dos heads de Alembic que existían (`7d3f406e43b4` y
`abf4a4a8d52a`) — ambos con `down_revision = None`. Sin este merge,
no se podía encadenar una nueva migración. El problema era preexistente.*

**`686e54a3d226_create_bi_schema_fact_and_summary_tables.py`:**
*Crea el esquema `bi` con 4 tablas de hechos y 6 tablas de resumen.
`upgrade()` ejecuta el DDL completo. `downgrade()` hace
`DROP SCHEMA bi CASCADE`. Sin FK hacia `pos.*` — desacoplamiento
deliberado para que el histórico BI sobreviva cambios en el POS.*

### 4.5 `requirements.txt` — 1 dependencia

```
tzdata==2026.2    # required on Windows for ZoneInfo timezone support
```
*Python en Windows no incluye datos de zonas horarias. Sin este paquete,
`ZoneInfo("America/Bogota")` falla. En Linux (Render) no se necesita
pero no causa daño.*

### 4.6 `.pre-commit-config.yaml` — archivo nuevo en raíz

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.7
    hooks:
      - id: ruff
        files: ^app/bi/
      - id: ruff-format
        files: ^app/bi/
```
*Hook de pre-commit que solo revisa archivos dentro de `app/bi/`.
No afecta el código de backend. Es provisional mientras se monta
el pipeline oficial de CI/CD.*

---

## 5. Tablas creadas en la base de datos (esquema `bi`)

### Tablas de hechos (el ETL escribe aquí cada noche)

| Tabla | Grano | Alimenta |
|-------|-------|----------|
| `bi.kpi_producto_dia` | 1 fila = 1 producto × 1 día | Ranking, señales, testeo |
| `bi.kpi_venta_hora_dia` | 1 fila = 1 hora × 1 día | Heatmap |
| `bi.kpi_insumo_dia` | 1 fila = 1 insumo × 1 día | Recomendación de compra |
| `bi.kpi_consumo_insumo_producto_dia` | 1 fila = 1 insumo × 1 producto × 1 día | Warning insumo |

### Tablas de resumen (los endpoints leen de aquí)

| Tabla | Fuente | Ventana |
|-------|--------|---------|
| `bi.resumen_ranking_producto` | kpi_producto_dia | 30 días |
| `bi.resumen_heatmap_hora_dia` | kpi_venta_hora_dia | 90 días |
| `bi.resumen_recomendacion_compra` | kpi_insumo_dia + pos.stock | 28 días |
| `bi.resumen_senal_precio` | kpi_producto_dia | 30 días |
| `bi.resumen_testeo_producto` | kpi_producto_dia + pos.producto | 60 días |
| `bi.resumen_warning_insumo` | kpi_consumo + ranking | 30 días |

---

## 6. Fórmulas de costeo aplicadas (decisiones validadas)

El costo se recalcula desde los insumos de cada receta:

```
costo_por_unidad_insumo = (precio / COALESCE(NULLIF(contador_unidades, 0), 1))
                          * 100.0 / pct_rendimiento
```

Donde:
- `precio` = precio bruto de compra por presentación (confirmado por Suley)
- `contador_unidades` = unidades base por presentación (normaliza a unidad de receta)
- `pct_rendimiento` = porcentaje aprovechable, escala 0–100 (confirmado en el código:
  `Insumo.precio_real = precio / (pct_rendimiento / 100)`)
- `venta.fecha` está en **UTC puro** → se convierte a Colombia con `AT TIME ZONE`
- `stock` es 1:1 con insumo (`UNIQUE(id_insumo)`) → LEFT JOIN directo, sin SUM
- Consumo = movimientos `tipo = 'salida'`, cantidad **NETA**

---

## 7. Cómo funciona el ETL diario

```
07:00 UTC (2:00 am Colombia)
    └─ Cron externo → POST /api/v1/bi/procesar-dia
        Header: X-Cron-Secret: {CRON_SECRET}
        Body:   {} (default: ayer en hora Colombia)

El ETL ejecuta 6 pasos en una transacción:
    1. Upsert kpi_producto_dia   (margen con costo real recalculado)
    2. Upsert kpi_venta_hora_dia (hora local Colombia)
    3. Upsert kpi_insumo_dia     (stock + consumo del día)
    4. Upsert kpi_consumo_insumo_producto_dia (explosión de receta)
    5. Rebuild 6 tablas resumen  (DELETE + INSERT en transacción)
    6. Webhook a Vercel          (purga de caché, best-effort)

Si falla → rollback automático. Idempotente: se puede re-ejecutar.
```

---

## 8. Reglas de trabajo para el futuro

- Todo cambio al módulo BI va en **rama `feature/bi-*`** con **PR a develop**
- Todo archivo en `app/bi/` pasa por **ruff check + ruff format** antes del commit
  (el pre-commit hook lo hace automáticamente)
- Estándares: **PEP 257** (docstrings Google style), complejidad máxima 10,
  naming conventions, imports ordenados
- Conventional commits en inglés: `feat(bi):`, `fix(bi):`, `chore(bi):`