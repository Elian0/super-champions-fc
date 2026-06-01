# 🔧 Instalación de Super Champiñones FC

## Instalación Rápida (Recomendado)

### Para Windows 🪟
```bash
setup.bat
```

### Para Linux/Mac 🍎
```bash
bash setup.sh
```

---

## ¿Qué hace el instalador?

El script automatiza estos 5 pasos:

1. **Crea Virtual Environment** - Aislamiento de dependencias Python
2. **Instala Dependencias** - Descarga todas las librerías necesarias
3. **Configura Base de Datos** - Aplica migraciones automáticas
4. **Carga Datos de Demo** - Crea usuarios y partidos de prueba
5. **Muestra Credenciales** - Te da los datos para iniciar sesión

---

## Requisitos Previos

### Python 3.10+

**Windows:**
- Descargar desde: https://www.python.org/downloads/
- **IMPORTANTE**: Marcar "Add Python to PATH" durante instalación
- Verificar instalación:
  ```bash
  python --version
  ```

**Mac:**
```bash
brew install python3
python3 --version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-dev
python3 --version
```

---

## Instalación Manual (Si prefieres)

Si el script no funciona, puedes instalar manualmente:

```bash
# 1. Navega a la carpeta config
cd config

# 2. Crea el virtual environment
python3 -m venv .venv

# 3. Activa el virtual environment
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# 4. Instala dependencias
pip install -r requirements.txt

# 5. Aplica migraciones
python manage.py migrate

# 6. Carga datos de demo
python manage.py shell < seed.py

# 7. Inicia el servidor
python manage.py runserver
```

---

## Credenciales de Prueba

Después de la instalación, puedes usar:

| Rol | Usuario | Contraseña | Acceso |
|-----|---------|-----------|--------|
| **Admin** | admin@champinones.bo | admin123 | Control total |
| **Personal** | personal@champinones.bo | admin123 | Ventas y reportes |
| **VIP** | socio@champinones.bo | vip123 | Portal VIP |

---

## ¿Por qué se activa el Virtual Environment automáticamente?

Cuando ejecutas el comando:
```powershell
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\user\Documents\boletos\super_champinones_fc\config\.venv\Scripts\Activate.ps1)
```

Se activa porque:
1. **VS Code** lo ejecuta automáticamente al abrir una terminal en la carpeta
2. Esto es una **característica de seguridad** - evita accidentes con proyectos
3. **No afecta nada** - es seguro y recomendado

---

## Iniciar el Servidor Después

Una vez instalado:

```bash
# 1. Abre terminal en la carpeta 'config'
cd config

# 2. Activa virtual environment (si no está activo)
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# 3. Inicia el servidor
python manage.py runserver

# 4. Abre en el navegador:
# http://127.0.0.1:8000
```

---

## Solución de Problemas

### Error: "Python no está instalado"
- Asegúrate de instalar Python desde https://www.python.org
- **IMPORTANTE**: Marca "Add Python to PATH"
- Reinicia la terminal después de instalar

### Error: "No se puede acceder a .venv"
- En Windows, abre terminal como Administrador:
  - Click derecho → "Ejecutar como administrador"
  - Luego ejecuta `setup.bat`

### Error: "No se encontró la carpeta config"
- Asegúrate de ejecutar el script **desde la raíz del proyecto**
- La estructura debe ser:
  ```
  super_champinones_fc/
    ├── setup.bat
    ├── setup.sh
    ├── config/
    │   ├── .venv/
    │   ├── manage.py
    │   └── requirements.txt
    └── champinones/
  ```

### Error en migraciones
Si falla la migración, intenta:
```bash
python manage.py migrate --run-syncdb
```

---

## Estructura del Proyecto

```
super_champinones_fc/
├── setup.bat              ← Instalador para Windows
├── setup.sh               ← Instalador para Linux/Mac
├── INSTALL.md             ← Este archivo
├── README.md              ← Documentación del proyecto
├── seed.py                ← Datos de demostración
├── db.sqlite3             ← Base de datos
├── manage.py              ← Gestor de Django
│
├── config/                ← Configuración Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── requirements.txt   ← Dependencias Python
│   └── .venv/             ← Virtual Environment
│
└── champinones/           ← Aplicación principal
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── templates/
    ├── static/
    └── migrations/
```

---

## Desactivar Virtual Environment

Para salir del virtual environment:

```bash
deactivate
```

---

## Contacto y Soporte

- 📧 Email: soporte@champinones.bo
- 📞 Teléfono: +591 2 XXXXXXX
- 🐛 Reportar bugs: [Crear issue en GitHub]

---

## Licencia

© 2026 Super Champiñones FC. Todos los derechos reservados.
