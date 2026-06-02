"""
urls.py — CDT Real Oruro - Sistema de Gestión
Enrutamiento semántico de todas las vistas del sistema.
"""

from django.urls import path
from . import views

# ─────────────────────────────────────────────
#  AUTENTICACIÓN  (HU4 / HU8)
# ─────────────────────────────────────────────
auth_patterns = [
    path('',           views.LoginView.as_view(),  name='login'),
    path('logout/',    views.logout_view,           name='logout'),
    path('registro/',  views.RegistroVIPView.as_view(), name='registro_vip'),
]

# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
dashboard_patterns = [
    path('dashboard/',   views.dashboard,    name='dashboard'),
    path('api/stats/',   views.api_stats,    name='api_stats'),
]

# ─────────────────────────────────────────────
#  MIEMBROS VIP  (HU1 / HU6 / HU7)
# ─────────────────────────────────────────────
miembro_patterns = [
    path('miembros/',                    views.MiembroListView.as_view(),   name='miembro_lista'),
    path('miembros/nuevo/',              views.MiembroCreateView.as_view(), name='miembro_crear'),
    path('miembros/<int:pk>/editar/',    views.MiembroUpdateView.as_view(), name='miembro_editar'),
    path('miembros/<int:pk>/eliminar/',  views.MiembroDeleteView.as_view(), name='miembro_eliminar'),
]

# ─────────────────────────────────────────────
#  RECARGAS  (HU2 / HU3)
# ─────────────────────────────────────────────
recarga_patterns = [
    path('recargas/procesar/',           views.recarga_crear,          name='recarga_crear'),
    path('recargas/<int:pk>/aprobar/',   views.recarga_aprobar,        name='recarga_aprobar'),
]

# ─────────────────────────────────────────────
#  PERSONAL / USUARIOS  (HU9)
# ─────────────────────────────────────────────
personal_patterns = [
    path('usuarios/',                    views.PersonalListView.as_view(),   name='personal_lista'),
    path('usuarios/nuevo/',              views.PersonalCreateView.as_view(), name='personal_crear'),
    path('usuarios/<int:pk>/editar/',    views.PersonalUpdateView.as_view(), name='personal_editar'),
    path('usuarios/<int:pk>/eliminar/',  views.PersonalDeleteView.as_view(), name='personal_eliminar'),
]

# ─────────────────────────────────────────────
#  EVENTOS / PARTIDOS  (HU10)
# ─────────────────────────────────────────────
evento_patterns = [
    path('partidos/',                    views.EventoListView.as_view(),   name='evento_lista'),
    path('partidos/nuevo/',              views.EventoCreateView.as_view(), name='evento_crear'),
    path('partidos/<int:pk>/editar/',    views.EventoUpdateView.as_view(), name='evento_editar'),
    path('partidos/<int:pk>/eliminar/',  views.EventoDeleteView.as_view(), name='evento_eliminar'),
    path('partidos/<int:pk>/cambiar-estado/', views.evento_cambiar_estado, name='evento_cambiar_estado'),
    path('partidos/<int:pk>/boletos/',   views.evento_boletos_lista,      name='evento_boletos_lista'),
]

# ─────────────────────────────────────────────
#  VENTAS / BOLETOS  (HU11)
# ─────────────────────────────────────────────
venta_patterns = [
    path('ventas/',               views.VentaListView.as_view(), name='venta_lista'),
    path('ventas/nueva/',         views.venta_crear,             name='venta_crear'),
    path('ventas/precio-sector/',  views.venta_sector_precio,     name='venta_sector_precio'),
    path('facturas/<int:pk>/',    views.factura_ver,             name='factura_ver'),
]

# ─────────────────────────────────────────────
#  CIERRE DE CAJA  (HU5)
# ─────────────────────────────────────────────
caja_patterns = [
    path('reportes/apertura/', views.apertura_caja,  name='apertura_caja'),
    path('reportes/cierre/',   views.cierre_caja,    name='cierre_caja'),
]

# ─────────────────────────────────────────────
#  PORTAL VIP
# ─────────────────────────────────────────────
vip_patterns = [
    path('vip/',                     views.vip_portal,            name='vip_portal'),
    path('vip/recargar/',            views.vip_solicitar_recarga, name='vip_recargar'),
    path('vip/comprar/',             views.vip_comprar_boleto,    name='vip_comprar'),
]

# ─────────────────────────────────────────────
#  PRUEBA DE ERRORES (DEBUG)
# ─────────────────────────────────────────────
debug_patterns = [
    path('prueba-errores/',        views.prueba_errores,        name='prueba_errores'),
    path('test-error/<int:codigo>/', views.test_error,          name='test_error'),
]

# ─────────────────────────────────────────────
#  URLPATTERNS COMPLETO
# ─────────────────────────────────────────────
urlpatterns = (
    auth_patterns
    + dashboard_patterns
    + miembro_patterns
    + recarga_patterns
    + personal_patterns
    + evento_patterns
    + venta_patterns
    + caja_patterns
    + vip_patterns
    + debug_patterns
)
