from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TenantCreate(BaseModel):
    nombre_comercial: str
    slug: str
    dominio: str
    color_primario: str = "#1d4ed8"
    color_secundario: str = "#0f172a"
    logo_url: Optional[str] = None
    id_plan: Optional[int] = None


class TenantOut(ORMBase):
    id: int
    nombre_comercial: str
    slug: str
    dominio: str
    color_primario: str
    color_secundario: str
    logo_url: Optional[str] = None
    id_plan: Optional[int] = None
    estado: str
    fecha_vencimiento: Optional[date] = None
    created_at: datetime
    coolify_app_uuid: Optional[str] = None
    backend_uuid: Optional[str] = None


class TenantEstadoOut(BaseModel):
    """Lo que consulta el ERP de cada cliente para saber si sigue activo."""
    slug: str
    estado: str
    fecha_vencimiento: Optional[date] = None
    activo: bool