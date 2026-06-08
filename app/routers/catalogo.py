"""
app/routers/catalogo.py
Endpoints REST para los catálogos base del sistema POS.
Autor: charlykj
Issue: #38
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.services.catalogo_service import (
    RolService, UsuarioService, ClienteService, MarcaService,
    UnidadMedidaService, ClasificacionService, CategoriaService, MetodoPagoService
)
from app.schemas.catalogo_schema import (
    RolCreate, RolOut,
    UsuarioCreate, UsuarioUpdate, UsuarioOut,
    ClienteCreate, ClienteUpdate, ClienteOut,
    MarcaCreate, MarcaOut,
    UnidadMedidaCreate, UnidadMedidaOut,
    ClasificacionCreate, ClasificacionOut,
    CategoriaCreate, CategoriaOut,
    MetodoPagoCreate, MetodoPagoOut
)

router = APIRouter(tags=["Catálogos"])

# --- Roles ---
@router.get("/roles", response_model=List[RolOut])
async def listar_roles(db: AsyncSession = Depends(get_db)):
    return await RolService(db).listar()

@router.get("/roles/{id_rol}", response_model=RolOut)
async def obtener_rol(id_rol: int, db: AsyncSession = Depends(get_db)):
    obj = await RolService(db).obtener(id_rol)
    if not obj:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return obj

@router.post("/roles", response_model=RolOut, status_code=201)
async def crear_rol(data: RolCreate, db: AsyncSession = Depends(get_db)):
    return await RolService(db).crear(data)

@router.delete("/roles/{id_rol}", status_code=204)
async def eliminar_rol(id_rol: int, db: AsyncSession = Depends(get_db)):
    if not await RolService(db).eliminar(id_rol):
        raise HTTPException(status_code=404, detail="Rol no encontrado")

# --- Usuarios ---
@router.get("/usuarios", response_model=List[UsuarioOut])
async def listar_usuarios(db: AsyncSession = Depends(get_db)):
    return await UsuarioService(db).listar()

@router.get("/usuarios/{id_usuario}", response_model=UsuarioOut)
async def obtener_usuario(id_usuario: int, db: AsyncSession = Depends(get_db)):
    obj = await UsuarioService(db).obtener(id_usuario)
    if not obj:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return obj

@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
async def crear_usuario(data: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    return await UsuarioService(db).crear(data)

@router.put("/usuarios/{id_usuario}", response_model=UsuarioOut)
async def actualizar_usuario(id_usuario: int, data: UsuarioUpdate, db: AsyncSession = Depends(get_db)):
    obj = await UsuarioService(db).actualizar(id_usuario, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return obj

@router.delete("/usuarios/{id_usuario}", status_code=204)
async def eliminar_usuario(id_usuario: int, db: AsyncSession = Depends(get_db)):
    if not await UsuarioService(db).eliminar(id_usuario):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

# --- Clientes ---
@router.get("/clientes", response_model=List[ClienteOut])
async def listar_clientes(db: AsyncSession = Depends(get_db)):
    return await ClienteService(db).listar()

@router.get("/clientes/{id_cliente}", response_model=ClienteOut)
async def obtener_cliente(id_cliente: int, db: AsyncSession = Depends(get_db)):
    obj = await ClienteService(db).obtener(id_cliente)
    if not obj:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return obj

@router.post("/clientes", response_model=ClienteOut, status_code=201)
async def crear_cliente(data: ClienteCreate, db: AsyncSession = Depends(get_db)):
    return await ClienteService(db).crear(data)

@router.put("/clientes/{id_cliente}", response_model=ClienteOut)
async def actualizar_cliente(id_cliente: int, data: ClienteUpdate, db: AsyncSession = Depends(get_db)):
    obj = await ClienteService(db).actualizar(id_cliente, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return obj

@router.delete("/clientes/{id_cliente}", status_code=204)
async def eliminar_cliente(id_cliente: int, db: AsyncSession = Depends(get_db)):
    if not await ClienteService(db).eliminar(id_cliente):
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

# --- Marcas ---
@router.get("/marcas", response_model=List[MarcaOut])
async def listar_marcas(db: AsyncSession = Depends(get_db)):
    return await MarcaService(db).listar()

@router.post("/marcas", response_model=MarcaOut, status_code=201)
async def crear_marca(data: MarcaCreate, db: AsyncSession = Depends(get_db)):
    return await MarcaService(db).crear(data)

@router.delete("/marcas/{id_marca}", status_code=204)
async def eliminar_marca(id_marca: int, db: AsyncSession = Depends(get_db)):
    if not await MarcaService(db).eliminar(id_marca):
        raise HTTPException(status_code=404, detail="Marca no encontrada")

# --- Unidades de Medida ---
@router.get("/unidades-medida", response_model=List[UnidadMedidaOut])
async def listar_unidades(db: AsyncSession = Depends(get_db)):
    return await UnidadMedidaService(db).listar()

@router.post("/unidades-medida", response_model=UnidadMedidaOut, status_code=201)
async def crear_unidad(data: UnidadMedidaCreate, db: AsyncSession = Depends(get_db)):
    return await UnidadMedidaService(db).crear(data)

@router.delete("/unidades-medida/{id_unidad}", status_code=204)
async def eliminar_unidad(id_unidad: int, db: AsyncSession = Depends(get_db)):
    if not await UnidadMedidaService(db).eliminar(id_unidad):
        raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")

# --- Clasificaciones ---
@router.get("/clasificaciones", response_model=List[ClasificacionOut])
async def listar_clasificaciones(db: AsyncSession = Depends(get_db)):
    return await ClasificacionService(db).listar()

@router.post("/clasificaciones", response_model=ClasificacionOut, status_code=201)
async def crear_clasificacion(data: ClasificacionCreate, db: AsyncSession = Depends(get_db)):
    return await ClasificacionService(db).crear(data)

@router.delete("/clasificaciones/{id_clasificacion}", status_code=204)
async def eliminar_clasificacion(id_clasificacion: int, db: AsyncSession = Depends(get_db)):
    if not await ClasificacionService(db).eliminar(id_clasificacion):
        raise HTTPException(status_code=404, detail="Clasificación no encontrada")

# --- Categorías ---
@router.get("/categorias", response_model=List[CategoriaOut])
async def listar_categorias(db: AsyncSession = Depends(get_db)):
    return await CategoriaService(db).listar()

@router.post("/categorias", response_model=CategoriaOut, status_code=201)
async def crear_categoria(data: CategoriaCreate, db: AsyncSession = Depends(get_db)):
    return await CategoriaService(db).crear(data)

@router.delete("/categorias/{id_categoria}", status_code=204)
async def eliminar_categoria(id_categoria: int, db: AsyncSession = Depends(get_db)):
    if not await CategoriaService(db).eliminar(id_categoria):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

# --- Métodos de Pago ---
@router.get("/metodos-pago", response_model=List[MetodoPagoOut])
async def listar_metodos_pago(db: AsyncSession = Depends(get_db)):
    return await MetodoPagoService(db).listar()

@router.post("/metodos-pago", response_model=MetodoPagoOut, status_code=201)
async def crear_metodo_pago(data: MetodoPagoCreate, db: AsyncSession = Depends(get_db)):
    return await MetodoPagoService(db).crear(data)

@router.delete("/metodos-pago/{id_metodo_pago}", status_code=204)
async def eliminar_metodo_pago(id_metodo_pago: int, db: AsyncSession = Depends(get_db)):
    if not await MetodoPagoService(db).eliminar(id_metodo_pago):
        raise HTTPException(status_code=404, detail="Método de pago no encontrado")