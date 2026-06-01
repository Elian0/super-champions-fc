"""
seed.py — Datos de demostración para Super Champiñones FC
Ejecutar con: python manage.py shell < seed.py
"""
from champinones.models import Usuario, RolUsuario, MiembroVIP, Evento
from decimal import Decimal
from datetime import date, time

print("Creando usuarios de demo...")
if not Usuario.objects.filter(username='admin@champinones.bo').exists():
    Usuario.objects.create_superuser(username='admin@champinones.bo', email='admin@champinones.bo', password='admin123', first_name='Carlos', last_name='Mamani', rol=RolUsuario.ADMIN)
    print("  ✓ Admin: admin@champinones.bo / admin123")

if not Usuario.objects.filter(username='personal@champinones.bo').exists():
    Usuario.objects.create_user(username='personal@champinones.bo', email='personal@champinones.bo', password='admin123', first_name='Ana', last_name='López', rol=RolUsuario.PERSONAL)
    print("  ✓ Personal: personal@champinones.bo / admin123")

if not Usuario.objects.filter(username='socio@champinones.bo').exists():
    vip_user = Usuario.objects.create_user(username='socio@champinones.bo', email='socio@champinones.bo', password='vip123', first_name='Roberto', last_name='Quispe', rol=RolUsuario.MIEMBRO_VIP)
    MiembroVIP.objects.create(usuario=vip_user, nombre_completo='Roberto Quispe Flores', ci='7845123', extension='LP', correo='socio@champinones.bo', celular='76543210', saldo=Decimal('250.00'))
    print("  ✓ VIP: socio@champinones.bo / vip123")

print("Creando partidos de demo...")
admin = Usuario.objects.get(username='admin@champinones.bo')
if not Evento.objects.exists():
    Evento.objects.create(nombre='Copa Bolivia 2025 — Semifinal', equipo_local='Super Champiñones FC', equipo_visitante='Bolívar', fecha=date(2025,8,15), hora=time(20,0), precio_base=Decimal('30.00'), capacidad_total=500, capacidad_disponible=492, creado_por=admin)
    Evento.objects.create(nombre='Liga Profesional — Jornada 18', equipo_local='Super Champiñones FC', equipo_visitante='The Strongest', fecha=date(2025,8,22), hora=time(18,30), precio_base=Decimal('20.00'), capacidad_total=350, capacidad_disponible=350, creado_por=admin)
    Evento.objects.create(nombre='Torneo Clausura — Final', equipo_local='Super Champiñones FC', equipo_visitante='Wilstermann', fecha=date(2025,9,5), hora=time(21,0), precio_base=Decimal('50.00'), capacidad_total=200, capacidad_disponible=200, creado_por=admin)
    print("  ✓ 3 partidos creados")

print("\n✅ Seed completado. Abre http://127.0.0.1:8000")
