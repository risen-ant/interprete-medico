import hashlib
import json
import os

# Ruta del archivo donde se guardarán las credenciales
USUARIOS_FILE = "usuarios_credenciales.json"

# Asegurar que el archivo exista
if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Función para hashear contraseñas
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Verifica si usuario y contraseña coinciden
def verificar_credenciales(usuario: str, password: str) -> bool:
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)
    if usuario in usuarios:
        return usuarios[usuario]["password_hash"] == hash_password(password)
    return False

# Crea un nuevo usuario (si no existe)
def crear_nuevo_usuario(usuario: str, password: str, email: str = "") -> bool:
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        usuarios = json.load(f)
    if usuario in usuarios:
        return False  # Ya existe

    usuarios[usuario] = {
        "password_hash": hash_password(password),
        "email": email
    }
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
    return True
