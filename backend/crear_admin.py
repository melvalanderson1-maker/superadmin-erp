from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import models as m

db = SessionLocal()
admin = m.AdminUsuario(
    nombre="Admin",
    correo="admin@tudominio.com",
    password_hash=hash_password("Admin123!"),
)
db.add(admin)
db.commit()
print("Admin creado:", admin.correo)
db.close()