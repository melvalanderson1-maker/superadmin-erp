import getpass

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import models as m

nombre = input("Nombre del admin: ").strip()
correo = input("Correo del admin: ").strip()
password = getpass.getpass("Contraseña del admin: ")

db = SessionLocal()
existente = db.query(m.AdminUsuario).filter(m.AdminUsuario.correo == correo).first()
if existente:
    print("Ya existe un admin con ese correo:", correo)
else:
    admin = m.AdminUsuario(
        nombre=nombre,
        correo=correo,
        password_hash=hash_password(password),
    )
    db.add(admin)
    db.commit()
    print("Admin creado:", admin.correo)
db.close()