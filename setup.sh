#!/bin/bash

# ============================================================================
# Super Champiñones FC - Instalador Automático para Linux/Mac
# Ejecutar con: bash setup.sh
# ============================================================================

clear

echo ""
echo "============================================================================"
echo "    ⚽ Super Champiñones FC — Sistema de Gestión de Boletos"
echo "    Instalador Automático para Linux/Mac"
echo "============================================================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 no está instalado"
    echo ""
    echo "Por favor instala Python 3 usando:"
    echo "  macOS:  brew install python3"
    echo "  Linux:  sudo apt install python3 python3-venv"
    echo ""
    exit 1
fi

echo "✓ Python detectado"
python3 --version
echo ""

# Navegar a la carpeta de configuración
cd config
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se encontró la carpeta 'config'"
    exit 1
fi

echo ""
echo "[PASO 1/5] Creando Virtual Environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ ERROR: No se pudo crear el virtual environment"
        exit 1
    fi
    echo "✓ Virtual Environment creado"
else
    echo "✓ Virtual Environment ya existe"
fi
echo ""

echo "[PASO 2/5] Activando Virtual Environment..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se pudo activar el virtual environment"
    exit 1
fi
echo "✓ Virtual Environment activado"
echo ""

echo "[PASO 3/5] Instalando dependencias..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se pudieron instalar las dependencias"
    exit 1
fi
echo "✓ Dependencias instaladas correctamente"
echo ""

echo "[PASO 4/5] Aplicando migraciones de base de datos..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ ERROR: No se pudieron aplicar las migraciones"
    exit 1
fi
echo "✓ Base de datos configurada"
echo ""

echo "[PASO 5/5] Cargando datos de demostración..."
python manage.py shell < seed.py
if [ $? -ne 0 ]; then
    echo "⚠ ADVERTENCIA: No se pudieron cargar los datos de demostración"
    echo "Pero el proyecto está funcional"
fi
echo "✓ Datos de demostración cargados"
echo ""

echo "============================================================================"
echo "✅ INSTALACIÓN COMPLETADA CON ÉXITO"
echo "============================================================================"
echo ""
echo "📋 CREDENCIALES DE PRUEBA:"
echo ""
echo "   Admin:"
echo "     Usuario: admin@champinones.bo"
echo "     Contraseña: admin123"
echo ""
echo "   Personal:"
echo "     Usuario: personal@champinones.bo"
echo "     Contraseña: admin123"
echo ""
echo "   Miembro VIP:"
echo "     Usuario: socio@champinones.bo"
echo "     Contraseña: vip123"
echo ""
echo "============================================================================"
echo ""
echo "Para iniciar el servidor:"
echo "   1. Abre una nueva terminal"
echo "   2. Navega a esta carpeta (config)"
echo "   3. Ejecuta: source .venv/bin/activate"
echo "   4. Luego: python manage.py runserver"
echo "   5. Abre: http://127.0.0.1:8000"
echo ""
echo "============================================================================"
echo ""
