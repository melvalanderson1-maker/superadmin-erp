from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models import models as m
from app.schemas import schemas as s
from app.services.coolify_service import CoolifyService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[s.TenantOut])
def listar_tenants(db: Session = Depends(get_db)):
    return db.query(m.Tenant).order_by(m.Tenant.created_at.desc()).all()


@router.post("", response_model=s.TenantOut, status_code=status.HTTP_201_CREATED)
async def crear_tenant(payload: s.TenantCreate, db: Session = Depends(get_db)):
    existe = db.query(m.Tenant).filter(m.Tenant.slug == payload.slug).first()
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tenant con ese slug")

    tenant = m.Tenant(**payload.model_dump(), estado=m.EstadoTenantEnum.provisionando)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    coolify = CoolifyService()
    dominio_publico = tenant.dominio
    dominio_api = f"api.{tenant.dominio}"

    try:
        # 1. Base de datos
        res_db = await coolify.crear_base_datos(tenant.slug)
        db_uuid = res_db.get("uuid")

        # 2. Backend
        res_backend = await coolify.crear_backend(tenant.slug, dominio_api)
        backend_uuid = res_backend.get("uuid")

        # 3. Variables de entorno del backend (identidad de marca + licencia)
        await coolify.set_env_var(backend_uuid, "EMPRESA_NOMBRE", tenant.nombre_comercial)
        await coolify.set_env_var(backend_uuid, "EMPRESA_SLUG", tenant.slug)
        await coolify.set_env_var(backend_uuid, "EMPRESA_DOMINIO", dominio_publico)
        await coolify.set_env_var(backend_uuid, "EMPRESA_COLOR_PRIMARIO", tenant.color_primario)
        await coolify.set_env_var(backend_uuid, "EMPRESA_COLOR_SECUNDARIO", tenant.color_secundario)
        await coolify.set_env_var(backend_uuid, "LICENCIA_TENANT_ID", tenant.slug)
        await coolify.set_env_var(
            backend_uuid, "LICENCIA_ENDPOINT", f"{settings.DOMINIO_BASE}/tenants/estado"
        )
        await coolify.set_env_var(backend_uuid, "LICENCIA_VERIFICAR", "true")

        # 4. Frontend
        res_frontend = await coolify.crear_frontend(tenant.slug, dominio_publico)
        frontend_uuid = res_frontend.get("uuid")

        # 5. Deploy de ambos
        await coolify.deploy(backend_uuid)
        await coolify.deploy(frontend_uuid)

        tenant.coolify_app_uuid = frontend_uuid
        tenant.coolify_db_uuid = db_uuid
        tenant.estado = m.EstadoTenantEnum.activo

        db.add(m.HistorialProvisionamiento(
            id_tenant=tenant.id, accion="crear", resultado="exito",
            detalle=f"backend={backend_uuid}, frontend={frontend_uuid}, db={db_uuid}",
        ))

    except Exception as e:
        tenant.estado = m.EstadoTenantEnum.error
        db.add(m.HistorialProvisionamiento(
            id_tenant=tenant.id, accion="crear", resultado="error", detalle=str(e),
        ))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{id_tenant}/pausar", response_model=s.TenantOut)
async def pausar_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    coolify = CoolifyService()
    try:
        await coolify.pausar(tenant.coolify_app_uuid)
        tenant.estado = m.EstadoTenantEnum.suspendido
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="pausar", resultado="exito"))
    except Exception as e:
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="pausar", resultado="error", detalle=str(e)))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{id_tenant}/reanudar", response_model=s.TenantOut)
async def reanudar_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    coolify = CoolifyService()
    try:
        await coolify.reanudar(tenant.coolify_app_uuid)
        tenant.estado = m.EstadoTenantEnum.activo
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="reanudar", resultado="exito"))
    except Exception as e:
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="reanudar", resultado="error", detalle=str(e)))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/{id_tenant}", response_model=s.TenantOut)
def obtener_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.post("/debug/test-db/{slug_prueba}")
async def debug_test_crear_bd(slug_prueba: str):
    """ENDPOINT TEMPORAL — solo para ver qué devuelve Coolify. Borrar después."""
    coolify = CoolifyService()
    res_db = await coolify.crear_base_datos(slug_prueba)
    return res_db


@router.get("/estado", response_model=s.TenantEstadoOut)
def estado_tenant(slug: str, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    return s.TenantEstadoOut(
        slug=tenant.slug,
        estado=tenant.estado.value,
        fecha_vencimiento=tenant.fecha_vencimiento,
        activo=tenant.estado == m.EstadoTenantEnum.activo,
    )