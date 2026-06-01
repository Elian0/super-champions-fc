#!/usr/bin/env python
"""
config-setup.py — Configuración rápida de Super Champiñones FC
Permite cambiar configuraciones sin editar archivos directamente
Usar: python config-setup.py
"""

import os
import sys

def main():
    print("\n" + "="*70)
    print("⚽ Super Champiñones FC — Configuración Rápida")
    print("="*70 + "\n")
    
    print("Opciones disponibles:\n")
    print("1. Ver estado actual del proyecto")
    print("2. Cambiar DEBUG mode (Seguridad)")
    print("3. Cambiar SECRET_KEY")
    print("4. Limpiar base de datos y recrearla")
    print("5. Ver información del servidor")
    print("6. Volver a cargar datos de demo")
    print("0. Salir\n")
    
    choice = input("Selecciona una opción (0-6): ").strip()
    
    if choice == '1':
        status()
    elif choice == '2':
        change_debug()
    elif choice == '3':
        change_secret_key()
    elif choice == '4':
        reset_database()
    elif choice == '5':
        server_info()
    elif choice == '6':
        reload_seed()
    elif choice == '0':
        print("\n✓ Saliendo...\n")
        sys.exit(0)
    else:
        print("\n❌ Opción no válida\n")
        main()

def status():
    print("\n" + "="*70)
    print("📊 Estado del Proyecto")
    print("="*70 + "\n")
    
    os.chdir('config')
    
    # Check Python version
    import sys
    print(f"✓ Python: {sys.version}")
    
    # Check Django
    try:
        import django
        print(f"✓ Django: {django.VERSION}")
    except ImportError:
        print("❌ Django no instalado")
    
    # Check database
    if os.path.exists('db.sqlite3'):
        size = os.path.getsize('db.sqlite3')
        print(f"✓ Base de datos: {size} bytes")
    else:
        print("❌ Base de datos no encontrada")
    
    # Check .venv
    if os.path.exists('.venv'):
        print("✓ Virtual Environment: Presente")
    else:
        print("⚠ Virtual Environment: No encontrado")
    
    print("\n" + "="*70 + "\n")
    input("Presiona Enter para continuar...")
    main()

def change_debug():
    print("\n" + "="*70)
    print("🔐 Cambiar DEBUG Mode")
    print("="*70 + "\n")
    
    print("DEBUG = True   → Muestra errores detallados (DESARROLLO)")
    print("DEBUG = False  → Oculta errores (PRODUCCIÓN)\n")
    
    debug_mode = input("¿Habilitar DEBUG? (s/n): ").strip().lower()
    
    if debug_mode == 's':
        value = 'True'
        print("✓ DEBUG habilitado (Desarrollo)")
    else:
        value = 'False'
        print("✓ DEBUG deshabilitado (Producción)")
    
    os.chdir('config')
    update_settings('DEBUG', value)
    print("✓ Configuración actualizada\n")
    
    input("Presiona Enter para continuar...")
    main()

def change_secret_key():
    print("\n" + "="*70)
    print("🔑 Cambiar SECRET_KEY")
    print("="*70 + "\n")
    
    from django.core.management.utils import get_random_secret_key
    new_key = get_random_secret_key()
    
    print(f"Nueva SECRET_KEY generada:\n{new_key}\n")
    
    confirm = input("¿Confirmar cambio? (s/n): ").strip().lower()
    
    if confirm == 's':
        os.chdir('config')
        update_settings('SECRET_KEY', f"'{new_key}'")
        print("✓ SECRET_KEY actualizada\n")
    else:
        print("Operación cancelada\n")
    
    input("Presiona Enter para continuar...")
    main()

def reset_database():
    print("\n" + "="*70)
    print("⚠️  LIMPIAR BASE DE DATOS")
    print("="*70 + "\n")
    
    print("ADVERTENCIA: Esto eliminará TODOS los datos del proyecto")
    print("Incluye: usuarios, partidos, boletos, todo.\n")
    
    confirm = input("¿Estás seguro? Escribe 'CONFIRMAR': ").strip()
    
    if confirm == 'CONFIRMAR':
        os.chdir('config')
        os.system('python manage.py migrate --run-syncdb')
        os.system('python manage.py shell < seed.py')
        print("\n✓ Base de datos reiniciada con datos de demo\n")
    else:
        print("Operación cancelada\n")
    
    input("Presiona Enter para continuar...")
    main()

def reload_seed():
    print("\n" + "="*70)
    print("🌱 Recargar Datos de Demo")
    print("="*70 + "\n")
    
    os.chdir('config')
    os.system('python manage.py shell < seed.py')
    print("\n✓ Datos de demo reincorporados\n")
    
    input("Presiona Enter para continuar...")
    main()

def server_info():
    print("\n" + "="*70)
    print("🌐 Información del Servidor")
    print("="*70 + "\n")
    
    print("URL local:    http://127.0.0.1:8000")
    print("Puerto:       8000")
    print("Ambiente:     Desarrollo\n")
    
    print("Para iniciar el servidor:")
    print("  1. Abre terminal en carpeta 'config'")
    print("  2. Ejecuta: python manage.py runserver")
    print("  3. Abre en navegador: http://127.0.0.1:8000\n")
    
    print("Para detener: Presiona Ctrl+C\n")
    
    input("Presiona Enter para continuar...")
    main()

def update_settings(key, value):
    """Actualiza un valor en settings.py"""
    settings_path = 'config/settings.py'
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar y reemplazar
    import re
    pattern = f"{key}\\s*=\\s*[^\\n]*"
    new_line = f"{key} = {value}"
    
    new_content = re.sub(pattern, new_line, content)
    
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
