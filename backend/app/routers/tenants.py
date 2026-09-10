from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[s.TenantOut])
def listar_tenants(db: Session = Depends(get_db)):
    return db.query(m.Tenant).order_by(m.Tenant.created_at.desc()).all()


@router.post("", response_model=s.TenantOut, status_code=status.HTTP_201_CREATED)
def crear_tenant(payload: s.TenantCreate, db: Session = Depends(get_db)):
    existe = db.query(m.Tenant).filter(m.Tenant.slug == payload.slug).first()
    if existe:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tenant con ese slug")

    tenant = m.Tenant(**payload.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    # Fase siguiente: aquí se dispara el aprovisionamiento real en Coolify
    # (crear app + BD + env vars + dominio + deploy)

    return tenant


@router.get("/{id_tenant}", response_model=s.TenantOut)
def obtener_tenant(id_tenant: int, db: Session = Depends(get_db)):
    tenant = db.query(m.Tenant).filter(m.Tenant.id == id_tenant).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


# ---- Endpoint público que consulta el ERP de cada cliente ----
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