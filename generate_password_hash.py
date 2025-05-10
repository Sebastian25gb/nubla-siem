from passlib.context import CryptContext

# Configuración para hashear contraseñas (igual que en security.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generar el hash de la contraseña "yourpassword"
password = "yourpassword"
hashed_password = pwd_context.hash(password)
print(hashed_password)