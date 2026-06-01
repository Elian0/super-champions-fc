from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, MiembroVIP, Recarga, Evento, Boleto, CierreCaja

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ('username', 'email', 'get_full_name', 'rol', 'is_active')
    list_filter   = ('rol', 'is_active')
    fieldsets     = UserAdmin.fieldsets + (('Rol', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Rol', {'fields': ('rol',)}),)

@admin.register(MiembroVIP)
class MiembroVIPAdmin(admin.ModelAdmin):
    list_display  = ('nombre_completo', 'ci_completo', 'celular', 'saldo', 'estado', 'fecha_registro')
    list_filter   = ('estado', 'extension')
    search_fields = ('nombre_completo', 'ci', 'correo', 'celular')
    readonly_fields = ('fecha_registro',)

@admin.register(Recarga)
class RecargaAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'monto', 'metodo_pago', 'estado', 'procesado_por', 'fecha_solicitud')
    list_filter  = ('estado', 'metodo_pago')
    readonly_fields = ('fecha_solicitud',)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'equipo_local', 'equipo_visitante', 'fecha', 'precio_base', 'capacidad_disponible', 'estado')
    list_filter  = ('estado',)
    search_fields = ('nombre', 'equipo_local', 'equipo_visitante')

@admin.register(Boleto)
class BoletoAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'evento', 'miembro_vip', 'sector', 'precio_pagado', 'fecha_compra')
    list_filter   = ('sector', 'pago_con_saldo_vip')
    search_fields = ('codigo',)
    readonly_fields = ('codigo', 'fecha_compra')

@admin.register(CierreCaja)
class CierreCajaAdmin(admin.ModelAdmin):
    list_display    = ('fecha', 'total_recaudado', 'cantidad_boletos', 'cantidad_recargas', 'estado', 'usuario_cierre')
    readonly_fields = ('total_recaudado', 'total_ventas_boletos', 'total_recargas', 'fecha_cierre')
