# Super Champiñones FC — Sistema de Gestión

Backend Django completo para gestión de Miembros VIP, venta de boletos y administración deportiva en Bolivia.

## Requisitos
- Python 3.10+
- Django 4.x+ (`pip install django`)

## Instalación rápida

```bash
# 1. Clonar / descomprimir el proyecto
cd super_champinones_fc/

# 2. Instalar dependencias
pip install django

# 3. Aplicar migraciones
python manage.py migrate

# 4. Cargar datos de demo (opcional)
python manage.py loaddata fixtures/demo.json
# O ejecutar el seed manual:
python manage.py shell < seed.py

# 5. Iniciar servidor
python manage.py runserver
```

Abre: http://127.0.0.1:8000

## Cuentas de Demo

| Rol           | Usuario                     | Contraseña |
|---------------|-----------------------------|------------|
| Administrador | admin@champinones.bo        | admin123   |
| Personal      | personal@champinones.bo     | admin123   |
| Miembro VIP   | socio@champinones.bo        | vip123     |

## Módulos y URLs

| Módulo               | URL                      | Rol requerido   |
|----------------------|--------------------------|-----------------|
| Login                | `/`                      | Público         |
| Registro VIP         | `/registro/`             | Público         |
| Dashboard            | `/dashboard/`            | Personal/Admin  |
| Miembros VIP         | `/miembros/`             | Personal/Admin  |
| Partidos/Eventos     | `/partidos/`             | Personal/Admin  |
| Ventas/Boletos       | `/ventas/`               | Personal/Admin  |
| Recargas             | `/recargas/procesar/`    | Personal/Admin  |
| Usuarios/Personal    | `/usuarios/`             | Admin           |
| Cierre de Caja       | `/reportes/cierre/`      | Admin           |
| Portal VIP           | `/vip/`                  | Miembro VIP     |
| Admin Django         | `/admin/`                | Superuser       |

## Validaciones Bolivianas Implementadas

- **CI:** 5 a 8 dígitos numéricos + complemento opcional (2 alnum) + extensión (LP, CB, SC, OR, PT, CH, TJ, BE, PD)
- **Celular:** exactamente 8 dígitos, comienza con 6, 7 u 8
- **Moneda:** `DecimalField(max_digits=10, decimal_places=2)` en Bolivianos (BOB)

## Estructura del Proyecto

```
config/
├── config/
│   ├── settings.py      ← Configuración (TIME_ZONE=America/La_Paz)
│   └── urls.py          ← Rutas raíz
├── champinones/
│   ├── models.py        ← 6 modelos con validadores bolivianos
│   ├── forms.py         ← 9 formularios ModelForm
│   ├── views.py         ← CBVs + funciones con RBAC
│   ├── urls.py          ← 25 rutas semánticas
│   ├── admin.py         ← Panel de administración
│   └── templates/
│       ├── base.html            ← CSS completo del diseño
│       ├── accounts/login.html  ← Login + Registro VIP
│       ├── portal/              ← Vistas de Personal/Admin
│       └── vip/portal.html      ← Portal del Miembro VIP
├── db.sqlite3           ← Base de datos SQLite
└── manage.py
```

## Para Producción
- Cambiar `SECRET_KEY` en `settings.py`
- Configurar `DEBUG = False`
- Migrar a PostgreSQL: `pip install psycopg2`
- Configurar `ALLOWED_HOSTS`
- Ejecutar `python manage.py collectstatic`
