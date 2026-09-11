import enum
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Numeric, Date, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EstadoTenantEnum(str, enum.Enum):
    provisionando = "provisionando"
    activo = "activo"
    suspendido = "suspendido"
    cancelado = "cancelado"
    error = "error"


class Plan(Base):
    __tablename__ = "planes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    precio_mensual = Column(Numeric(10, 2))
    max_proyectos = Column(Integer)
    max_usuarios = Column(Integer)
    activo = Column(Boolean, nullable=False, default=True)


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    nombre_comercial = Column(String(150), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    dominio = Column(String(200), nullable=False, unique=True)
    color_primario = Column(String(10), default="#1d4ed8")
    color_secundario = Column(String(10), default="#0f172a")
    logo_url = Column(String(300))
    id_plan = Column(Integer, ForeignKey("planes.id"))
    estado = Column(SAEnum(EstadoTenantEnum, name="estado_tenant_enum"), nullable=False, default=EstadoTenantEnum.provisionando)

    coolify_app_uuid = Column(String(100))   # frontend
    backend_uuid = Column(String(100))       # backend
    coolify_db_uuid = Column(String(100))

    db_host = Column(String(200))
    db_nombre = Column(String(100))
    db_usuario = Column(String(100))
    db_password = Column(String(200))

    fecha_vencimiento = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    plan = relationship("Plan")
    historial = relationship("HistorialProvisionamiento", back_populates="tenant")


class HistorialProvisionamiento(Base):
    __tablename__ = "historial_provisionamiento"

    id = Column(BigInteger, primary_key=True)
    id_tenant = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    accion = Column(String(50), nullable=False)
    resultado = Column(String(20), nullable=False)
    detalle = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="historial")


class AdminUsuario(Base):
    __tablename__ = "admin_usuarios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), nullable=False)
    correo = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())