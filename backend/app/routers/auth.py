from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verificar_password, crear_access_token
from app.models import models as m
from app.schemas import schemas as s

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=s.TokenResponse)
def login(payload: s.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(m.AdminUsuario).filter(m.AdminUsuario.correo == payload.correo).first()
    if not usuario or not verificar_password(payload.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    if not usuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    token = crear_access_token({"sub": str(usuario.id)})
    return {"access_token": token}