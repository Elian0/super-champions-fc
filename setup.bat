@echo off
REM ============================================================================
REM Super Champiñones FC - Instalador Automático para Windows
REM Ejecutar con: setup.bat
REM ============================================================================

cls
echo.
echo ============================================================================
echo    ⚽ Super Champiñones FC — Sistema de Gestión de Boletos
echo    Instalador Automático para Windows
echo ============================================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo.
    echo Por favor instala Python desde: https://www.python.org/downloads/
    echo Asegúrate de marcar "Add Python to PATH" durante la instalación
    echo.
    pause
    exit /b 1
)

echo ✓ Python detectado
python --version
echo.

REM Navegar a la carpeta de configuración
cd config
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se encontró la carpeta 'config'
    pause
    exit /b 1
)

echo.
echo [PASO 1/5] Creando Virtual Environment...
if not exist .venv (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ ERROR: No se pudo crear el virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual Environment creado
) else (
    echo ✓ Virtual Environment ya existe
)
echo.

echo [PASO 2/5] Activando Virtual Environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudo activar el virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual Environment activado
echo.

echo [PASO 3/5] Instalando dependencias...
pip install --upgrade pip setuptools wheel >nul
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)
echo ✓ Dependencias instaladas correctamente
echo.

echo [PASO 4/5] Aplicando migraciones de base de datos...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ❌ ERROR: No se pudieron aplicar las migraciones
    pause
    exit /b 1
)
echo ✓ Base de datos configurada
echo.

echo [PASO 5/5] Cargando datos de demostración...
python manage.py shell ^< seed.py
if %errorlevel% neq 0 (
    echo ⚠ ADVERTENCIA: No se pudieron cargar los datos de demostración
    echo Pero el proyecto está funcional
)
echo ✓ Datos de demostración cargados
echo.

echo ============================================================================
echo ✅ INSTALACIÓN COMPLETADA CON ÉXITO
echo ============================================================================
echo.
echo 📋 CREDENCIALES DE PRUEBA:
echo.
echo   Admin:
echo     Usuario: admin@champinones.bo
echo     Contraseña: admin123
echo.
echo   Personal:
echo     Usuario: personal@champinones.bo
echo     Contraseña: admin123
echo.
echo   Miembro VIP:
echo     Usuario: socio@champinones.bo
echo     Contraseña: vip123
echo.
echo ============================================================================
echo.
echo Para iniciar el servidor:
echo   1. Abre una nueva terminal
echo   2. Navega a esta carpeta (config)
echo   3. Ejecuta: python manage.py runserver
echo   4. Abre: http://127.0.0.1:8000
echo.
echo ============================================================================
echo.
pause
