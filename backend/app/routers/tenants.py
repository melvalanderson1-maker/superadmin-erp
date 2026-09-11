import asyncio
import secrets

import httpx
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

    datos_tenant = payload.model_dump()
    if not datos_tenant.get("dominio"):
        datos_tenant["dominio"] = f"pendiente-{payload.slug}.local"

    tenant = m.Tenant(**datos_tenant, estado=m.EstadoTenantEnum.provisionando)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    coolify = CoolifyService()

    try:
        # 1. Base de datos
        res_db = await coolify.crear_base_datos(tenant.slug)
        db_uuid = res_db.get("uuid")

        database_url_raw = (
            res_db.get("internal_db_url")
            or res_db.get("postgres_url")
            or res_db.get("connection_url")
        )
        if not database_url_raw:
            raise RuntimeError(f"Coolify no devolvió una URL de conexión para la BD. Respuesta cruda: {res_db}")

        database_url = database_url_raw
        for prefijo_viejo in ("postgres://", "postgresql://"):
            if database_url.startswith(prefijo_viejo):
                database_url = "postgresql+psycopg2://" + database_url[len(prefijo_viejo):]
                break

        secret_key = secrets.token_urlsafe(32)
        bootstrap_secret = secrets.token_urlsafe(24)

        # 2. Backend — se crea y despliega PRIMERO, para conocer su dominio real
        res_backend = await coolify.crear_backend(tenant.slug, "", database_url)
        backend_uuid = res_backend.get("uuid")

        await coolify.set_env_var(backend_uuid, "DATABASE_URL", database_url)
        await coolify.set_env_var(backend_uuid, "SECRET_KEY", secret_key)
        await coolify.set_env_var(backend_uuid, "BOOTSTRAP_SECRET", bootstrap_secret)
        await coolify.set_env_var(backend_uuid, "EMPRESA_NOMBRE", tenant.nombre_comercial)
        await coolify.set_env_var(backend_uuid, "EMPRESA_SLUG", tenant.slug)
        await coolify.set_env_var(backend_uuid, "EMPRESA_COLOR_PRIMARIO", tenant.color_primario)
        await coolify.set_env_var(backend_uuid, "EMPRESA_COLOR_SECUNDARIO", tenant.color_secundario)
        await coolify.set_env_var(backend_uuid, "LICENCIA_TENANT_ID", tenant.slug)
        await coolify.set_env_var(
            backend_uuid, "LICENCIA_ENDPOINT", f"{settings.DOMINIO_BASE}/tenants/estado"
        )
        await coolify.set_env_var(backend_uuid, "LICENCIA_VERIFICAR", "true")

        await coolify.deploy(backend_uuid)

        info_backend = await coolify.obtener_aplicacion(backend_uuid)
        dominio_backend = info_backend.get("fqdn", "").replace("https://", "").replace("http://", "").strip(",")
        url_backend = f"https://{dominio_backend}" if dominio_backend else None

        # 2b. Esperamos a que el backend TERMINE de compilar y responda /health
        # antes de lanzar el build del frontend. Dos "npm run build" a la vez
        # revientan la memoria del servidor y el build muere sin log (exit 255).
        backend_listo = False
        if url_backend:
            async with httpx.AsyncClient(timeout=10) as client:
                for _ in range(18):
                    try:
                        resp = await client.get(f"{url_backend}/health")
                        if resp.status_code == 200:
                            backend_listo = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(5)

        # 3. Frontend — recién ahora, con el build del backend ya liberado
        res_frontend = await coolify.crear_frontend(tenant.slug, "")
        frontend_uuid = res_frontend.get("uuid")
        await coolify.set_env_var(frontend_uuid, "API_URL", url_backend or "")
        await coolify.deploy(frontend_uuid)

        # Damos tiempo a que el build del frontend termine antes de tocar
        # el backend otra vez (paso 4) — un build a la vez, siempre.
        await asyncio.sleep(45)

        info_frontend = await coolify.obtener_aplicacion(frontend_uuid)
        dominio_real = info_frontend.get("fqdn", "").replace("https://", "").replace("http://", "").strip(",")
        if dominio_real:
            tenant.dominio = dominio_real

        # 4. Actualizamos el backend con el dominio real del frontend (para CORS) y redeploy
        if dominio_real:
            await coolify.set_env_var(backend_uuid, "EMPRESA_DOMINIO", dominio_real)
            await coolify.set_env_var(backend_uuid, "CORS_ORIGINS", f"https://{dominio_real}")
            await coolify.redeploy(backend_uuid)

        # 5. Re-confirmar /health después del redeploy de CORS
        backend_listo = False
        if url_backend:
            async with httpx.AsyncClient(timeout=10) as client:
                for _ in range(10):
                    try:
                        resp = await client.get(f"{url_backend}/health")
                        if resp.status_code == 200:
                            backend_listo = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(5)

        # 6. Crear el primer usuario admin de esa instancia (una sola vez, vía bootstrap)
        password_admin = secrets.token_urlsafe(10)
        correo_admin = f"admin@{tenant.slug}.com"

        if backend_listo and url_backend:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{url_backend}/setup/admin-inicial",
                    json={
                        "clave_bootstrap": bootstrap_secret,
                        "nombre": "Administrador",
                        "correo": correo_admin,
                        "password": password_admin,
                    },
                )
                resp.raise_for_status()

            tenant.admin_correo_generado = correo_admin
            tenant.admin_password_generada = password_admin

        tenant.coolify_app_uuid = frontend_uuid
        tenant.backend_uuid = backend_uuid
        tenant.coolify_db_uuid = db_uuid
        tenant.dominio_backend = dominio_backend
        tenant.estado = m.EstadoTenantEnum.activo

        db.add(m.HistorialProvisionamiento(
            id_tenant=tenant.id, accion="crear", resultado="exito",
            detalle=f"backend={backend_uuid}, frontend={frontend_uuid}, db={db_uuid}, admin_creado={backend_listo}",
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
        if tenant.backend_uuid:
            await coolify.pausar(tenant.backend_uuid)
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
        if tenant.backend_uuid:
            await coolify.reanudar(tenant.backend_uuid)
        tenant.estado = m.EstadoTenantEnum.activo
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="reanudar", resultado="exito"))
    except Exception as e:
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="reanudar", resultado="error", detalle=str(e)))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{id_tenant}/redeploy", response_model=s.TenantOut)
async def redeploy_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    coolify = CoolifyService()
    try:
        if tenant.backend_uuid:
            await coolify.redeploy(tenant.backend_uuid)
        if tenant.coolify_app_uuid:
            await coolify.redeploy(tenant.coolify_app_uuid)

        tenant.estado = m.EstadoTenantEnum.activo
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="redeploy", resultado="exito"))
    except Exception as e:
        db.add(m.HistorialProvisionamiento(id_tenant=tenant.id, accion="redeploy", resultado="error", detalle=str(e)))

    db.commit()
    db.refresh(tenant)
    return tenant


@router.delete("/{id_tenant}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")

    coolify = CoolifyService()

    if tenant.backend_uuid:
        try:
            await coolify.eliminar_aplicacion(tenant.backend_uuid)
        except Exception:
            pass

    if tenant.coolify_app_uuid:
        try:
            await coolify.eliminar_aplicacion(tenant.coolify_app_uuid)
        except Exception:
            pass

    if tenant.coolify_db_uuid:
        try:
            await coolify.eliminar_base_datos(tenant.coolify_db_uuid)
        except Exception:
            pass

    db.delete(tenant)
    db.commit()


@router.get("/{id_tenant}/historial")
def historial_tenant(id_tenant: int, db: Session = Depends(get_db)):
    registros = (
        db.query(m.HistorialProvisionamiento)
        .filter(m.HistorialProvisionamiento.id_tenant == id_tenant)
        .order_by(m.HistorialProvisionamiento.created_at.desc())
        .all()
    )
    return [
        {"accion": r.accion, "resultado": r.resultado, "detalle": r.detalle, "fecha": r.created_at}
        for r in registros
    ]


@router.get("/{id_tenant}", response_model=s.TenantOut)
def obtener_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


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