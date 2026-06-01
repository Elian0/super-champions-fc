# ⚽ Super Champiñones FC — Sistema de Gestión de Boletos

Sistema profesional de gestión de ventas de boletos para eventos deportivos, con control de inventario, reportes y portal VIP.

![Django](https://img.shields.io/badge/Django-5.2.7-blue?logo=django)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![SQLite](https://img.shields.io/badge/SQLite-3-green?logo=sqlite)
![License](https://img.shields.io/badge/License-Propietaria-red)

---

## 🚀 Instalación Rápida

### 1. Clonar o descargar el proyecto

```bash
git clone https://github.com/tuusuario/super_champinones_fc.git
cd super_champinones_fc
```

### 2. Ejecutar instalador

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
bash setup.sh
```

El instalador hará todo automáticamente en 5 pasos.

---

## 📋 Características Principales

### 🎟️ Ventas de Boletos
- Venta rápida con precios automáticos
- Facturación profesional con IVA
- Múltiples sectores de asiento
- Métodos de pago: Efectivo, Tarjeta, Saldo VIP

### 📊 Gestión de Eventos
- Crear partidos con capacidad y precio
- Cambiar estado en tiempo real
- Separación visual por estado (Programado, En Curso, Finalizado)
- Visualización clara sin confusión

### 💰 Control de Caja
- **Apertura de Caja**: Registra empleado y monto inicial
- **Cierre de Caja**: Resumen diario de recaudaciones
- Historial de aperturas y cierres
- Diferencias automáticas

### 👥 Miembros VIP
- Saldo virtual para compras
- Solicitudes de recarga
- Portal personal
- Historial de transacciones

### 📈 Reportes
- Ventas por día
- Ingreso por evento
- Detalles de boletos
- Exportar a CSV

### 🔒 Seguridad
- Autenticación de usuarios
- Control de roles (Admin, Personal, VIP)
- Manejo profesional de errores
- Registro de todas las operaciones

---

## 🔑 Credenciales de Prueba

| Rol | Usuario | Contraseña |
|-----|---------|-----------|
| **Admin** | admin@champinones.bo | admin123 |
| **Personal** | personal@champinones.bo | admin123 |
| **VIP** | socio@champinones.bo | vip123 |

---

## 📁 Estructura del Proyecto

```
super_champinones_fc/
├── setup.bat                    ← Instalador Windows
├── setup.sh                     ← Instalador Linux/Mac
├── INSTALL.md                   ← Guía de instalación
├── README.md                    ← Este archivo
├── seed.py                      ← Datos de demostración
│
├── config/
│   ├── manage.py                ← Gestor Django
│   ├── requirements.txt          ← Dependencias
│   ├── config-setup.py           ← Herramienta de configuración
│   ├── db.sqlite3               ← Base de datos
│   │
│   ├── settings.py              ← Configuración Django
│   ├── urls.py                  ← Rutas principales
│   ├── wsgi.py                  ← Producción
│   └── asgi.py                  ← WebSockets
│
└── champinones/                 ← Aplicación principal
    ├── models.py                ← Modelos de datos
    ├── views.py                 ← Lógica de negocio
    ├── urls.py                  ← Rutas internas
    ├── forms.py                 ← Formularios
    ├── admin.py                 ← Panel admin
    ├── tests.py                 ← Tests
    │
    ├── migrations/              ← Historial de BD
    │
    └── templates/
        ├── base.html            ← Template base
        └── portal/
            ├── dashboard.html   ← Panel principal
            ├── partidos.html    ← Gestión de eventos
            ├── ventas.html      ← Historial de ventas
            ├── apertura_caja.html ← Apertura de caja
            └── ...
```

---

## 🛠️ Stack Tecnológico

- **Backend**: Django 5.2.7
- **Base de Datos**: SQLite3
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Python**: 3.13+
- **Autenticación**: Django Auth + Custom Roles
- **Exportación**: CSV

---

## 🚀 Iniciar Servidor

Después de instalar:

```bash
# 1. Navega a la carpeta config
cd config

# 2. Activa virtual environment (opcional, ya está activo)
# Windows:
.venv\Scripts\activate

# Mac/Linux:
source .venv/bin/activate

# 3. Inicia servidor
python manage.py runserver

# 4. Abre en navegador
# http://127.0.0.1:8000
```

---

## 📖 Uso del Sistema

### 1. Abrir Caja (Inicio del Día)
- Ir a: `Reportes → Apertura de Caja`
- Ingresar monto inicial
- Sistema registra automáticamente empleado y hora

### 2. Vender Boleto
- Click en `Nueva Venta`
- Seleccionar evento (precio automático)
- Seleccionar cliente (opcional)
- Confirmar compra

### 3. Ver Eventos
- Ir a: `Partidos`
- Partidos organizados por estado:
  - 📅 Programados
  - 🔴 En Curso
  - ✅ Finalizados

### 4. Cambiar Estado de Evento
- Click en botón `⚡ Estado`
- Seleccionar nuevo estado
- Cambio instantáneo

### 5. Cerrar Caja (Final del Día)
- Ir a: `Reportes → Cierre de Caja`
- Sistema calcula automáticamente totales
- Registra diferencias si las hay

---

## ⚙️ Configuración Rápida

Para cambiar configuraciones sin editar archivos:

```bash
cd config
python config-setup.py
```

Opciones:
1. Ver estado del proyecto
2. Cambiar DEBUG mode
3. Generar nueva SECRET_KEY
4. Limpiar y recrear BD
5. Ver info del servidor
6. Recargar datos de demo

---

## 📱 Responsive Design

El sistema funciona en:
- ✓ Desktop (Full)
- ✓ Tablet (Optimizado)
- ✓ Mobile (Funcional)

---

## 🔐 Seguridad

- ✓ CSRF protection
- ✓ SQL Injection prevention (ORM Django)
- ✓ XSS protection
- ✓ Autenticación requerida
- ✓ Control de roles
- ✓ Manejo de errores personalizado
- ✓ Logging de operaciones

---

## 🐛 Solución de Problemas

### Error: "Python no está instalado"
→ Ver [INSTALL.md](INSTALL.md) sección "Requisitos Previos"

### Error: "ModuleNotFoundError: No module named 'django'"
→ Verifica que el virtual environment esté activo

### Error: "No se puede acceder a .venv"
→ Ejecuta terminal como Administrador

### Error en base de datos
→ Ejecuta: `python manage.py migrate --run-syncdb`

---

## 📞 Soporte

- **Email**: soporte@champinones.bo
- **Teléfono**: +591 2 XXXXXXX
- **Ubicación**: La Paz, Bolivia

---

## 📝 Notas de Versión

### v2.0 (2026-05-29)
- ✨ Sistema de apertura de caja
- ✨ Separación de eventos por estado
- ✨ Precios automáticos en ventas
- 🐛 Arreglado error UnboundLocalError
- 📊 Mejor visualización de dashboard

### v1.0 (2026-05-01)
- Lanzamiento inicial del proyecto

---

## 📄 Licencia

© 2026 **Super Champiñones FC**. Todos los derechos reservados.

Este software es propiedad de Super Champiñones FC y no puede ser distribuido, modificado o utilizado sin permiso explícito.

---

## 🙏 Créditos

Desarrollado por el equipo técnico de Super Champiñones FC.

---

## 🎯 Roadmap Futuro

- [ ] Interfaz móvil nativa
- [ ] Integración con POS
- [ ] Reportes PDF avanzados
- [ ] Multi-idioma
- [ ] Sincronización en la nube
- [ ] Análisis con IA
- [ ] App para smartphones

---

**Última actualización**: 29/05/2026

¡Gracias por usar Super Champiñones FC! ⚽
