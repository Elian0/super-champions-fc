"""
forms.py — CDT Real Oruro - Sistema de Gestión
ModelForms con validaciones bolivianas para CI, celular y moneda.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .models import (
    Usuario, MiembroVIP, Recarga, Evento, Boleto, CierreCaja,
    DepartamentoExtension, RolUsuario,
)


# ─────────────────────────────────────────────
#  MIXIN: Estilos Bootstrap / CSS personalizado
# ─────────────────────────────────────────────

class StyledFormMixin:
    """
    Aplica las clases CSS del diseño HTML estático a todos
    los widgets del formulario de forma automática.
    """
    FIELD_CSS = 'form-input'

    def apply_styles(self):
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {self.FIELD_CSS}'.strip()
            # Placeholder en español si no existe
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label or field_name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


# ─────────────────────────────────────────────
#  AUTENTICACIÓN  (HU4 / HU8)
# ─────────────────────────────────────────────

class LoginForm(StyledFormMixin, AuthenticationForm):
    """
    Formulario de inicio de sesión.
    Conectar con: {% block content %} en login.html → <form method="post">
    """
    username = forms.CharField(
        label=_('Usuario'),
        widget=forms.TextInput(attrs={'placeholder': 'usuario@correo.com', 'autofocus': True}),
    )
    password = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )


# ─────────────────────────────────────────────
#  USUARIOS / PERSONAL  (HU9)
# ─────────────────────────────────────────────

class CrearPersonalForm(StyledFormMixin, UserCreationForm):
    """
    Crea una cuenta de Personal o Administrador.
    Solo accesible por el Administrador.
    Conectar con: page-usuarios → modal de creación en el HTML.
    """
    first_name = forms.CharField(label=_('Nombre'), max_length=60)
    last_name  = forms.CharField(label=_('Apellido'), max_length=60)
    email      = forms.EmailField(label=_('Correo'))
    rol        = forms.ChoiceField(
        label=_('Rol'),
        choices=[
            (RolUsuario.PERSONAL, _('Personal')),
            (RolUsuario.ADMIN,    _('Administrador')),
        ],
    )

    class Meta:
        model  = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'password1', 'password2')

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if rol not in (RolUsuario.PERSONAL, RolUsuario.ADMIN):
            raise ValidationError(_('Rol inválido para personal del sistema.'))
        return rol


class EditarPersonalForm(StyledFormMixin, forms.ModelForm):
    """
    Editar datos de un usuario personal (sin cambiar contraseña aquí).
    """
    class Meta:
        model  = Usuario
        fields = ('first_name', 'last_name', 'email', 'rol', 'is_active')
        labels = {
            'first_name': _('Nombre'),
            'last_name':  _('Apellido'),
            'email':      _('Correo'),
            'rol':        _('Rol'),
            'is_active':  _('Cuenta activa'),
        }

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if rol == RolUsuario.MIEMBRO_VIP:
            raise ValidationError(
                _('No puedes asignar el rol VIP directamente desde aquí. '
                  'Usa el módulo de Miembros VIP.')
            )
        return rol


# ─────────────────────────────────────────────
#  REGISTRO VIP PÚBLICO  (HU1)
# ─────────────────────────────────────────────

class RegistroVIPPublicoForm(StyledFormMixin, forms.Form):
    """
    Formulario de auto-registro para un nuevo Miembro VIP
    desde la página pública de login.
    Conectar con: #register-form en el HTML.
    """
    nombre_completo = forms.CharField(
        label=_('Nombre Completo'), max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre completo'}),
    )
    ci = forms.CharField(
        label=_('CI'), max_length=8,
        widget=forms.TextInput(attrs={'placeholder': '12345678'}),
    )
    complemento = forms.CharField(
        label=_('Complemento'), max_length=2, required=False,
        widget=forms.TextInput(attrs={'placeholder': '1A'}),
    )
    extension = forms.ChoiceField(
        label=_('Extensión'),
        choices=[('', '-- Dpto --')] + list(DepartamentoExtension.choices),
    )
    celular = forms.CharField(
        label=_('Celular'), max_length=8,
        widget=forms.TextInput(attrs={'placeholder': '7xxxxxxx'}),
    )
    correo = forms.EmailField(
        label=_('Correo Electrónico'),
        widget=forms.EmailInput(attrs={'placeholder': 'tu@correo.com'}),
    )
    password = forms.CharField(
        label=_('Contraseña'), min_length=6,
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 6 caracteres'}),
    )
    password2 = forms.CharField(
        label=_('Confirmar Contraseña'), min_length=6,
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña'}),
    )

    # ── Validaciones bolivianas ──────────────

    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '').strip()
        if not ci.isdigit() or not (5 <= len(ci) <= 8):
            raise ValidationError(_('La CI debe tener entre 5 y 8 dígitos numéricos.'))
        return ci

    def clean_complemento(self):
        comp = self.cleaned_data.get('complemento', '').strip().upper()
        if comp and (len(comp) != 2 or not comp.isalnum()):
            raise ValidationError(
                _('El complemento debe ser exactamente 2 caracteres alfanuméricos.')
            )
        return comp

    def clean_celular(self):
        cel = self.cleaned_data.get('celular', '').strip()
        if not cel.isdigit() or len(cel) != 8 or cel[0] not in '678':
            raise ValidationError(
                _('El celular debe tener 8 dígitos y comenzar con 6, 7 u 8.')
            )
        return cel

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').lower()
        if Usuario.objects.filter(email=correo).exists():
            raise ValidationError(_('Ya existe una cuenta con este correo.'))
        if MiembroVIP.objects.filter(correo=correo).exists():
            raise ValidationError(_('Este correo ya está registrado como Miembro VIP.'))
        return correo

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', _('Las contraseñas no coinciden.'))

        # Unicidad CI + complemento + extensión
        ci        = cleaned.get('ci')
        comp      = cleaned.get('complemento', '')
        extension = cleaned.get('extension')
        if ci and extension:
            if MiembroVIP.objects.filter(ci=ci, complemento=comp, extension=extension).exists():
                raise ValidationError(
                    _('Ya existe un miembro registrado con esa CI y extensión.')
                )
        return cleaned


# ─────────────────────────────────────────────
#  CRUD MIEMBRO VIP  (HU1 / HU6 / HU7)
# ─────────────────────────────────────────────

class MiembroVIPForm(StyledFormMixin, forms.ModelForm):
    """
    Formulario de gestión de Miembros VIP para personal/admin.
    Conectar con: #page-miembros → modal de crear/editar.
    """
    class Meta:
        model  = MiembroVIP
        fields = (
            'nombre_completo', 'ci', 'complemento', 'extension',
            'correo', 'celular', 'saldo', 'estado',
        )
        labels = {
            'nombre_completo': _('Nombre Completo'),
            'ci':              _('Cédula de Identidad'),
            'complemento':     _('Complemento CI'),
            'extension':       _('Extensión (Depto.)'),
            'correo':          _('Correo Electrónico'),
            'celular':         _('Celular'),
            'saldo':           _('Saldo Inicial (BOB)'),
            'estado':          _('Estado'),
        }
        widgets = {
            'ci':          forms.TextInput(attrs={'placeholder': '12345678'}),
            'complemento': forms.TextInput(attrs={'placeholder': '1A (opcional)'}),
            'celular':     forms.TextInput(attrs={'placeholder': '7xxxxxxx'}),
            'correo':      forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
        }

    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '').strip()
        if not ci.isdigit() or not (5 <= len(ci) <= 8):
            raise ValidationError(_('La CI debe tener entre 5 y 8 dígitos numéricos.'))
        return ci

    def clean_complemento(self):
        comp = self.cleaned_data.get('complemento', '').strip().upper()
        if comp and (len(comp) != 2 or not comp.isalnum()):
            raise ValidationError(
                _('El complemento debe ser exactamente 2 caracteres alfanuméricos.')
            )
        return comp

    def clean_celular(self):
        cel = self.cleaned_data.get('celular', '').strip()
        if not cel.isdigit() or len(cel) != 8 or cel[0] not in '678':
            raise ValidationError(
                _('El celular debe tener 8 dígitos y comenzar con 6, 7 u 8.')
            )
        return cel

    def clean_saldo(self):
        saldo = self.cleaned_data.get('saldo')
        if saldo is not None and saldo < Decimal('0.00'):
            raise ValidationError(_('El saldo no puede ser negativo.'))
        return saldo

    def clean(self):
        cleaned = super().clean()
        ci        = cleaned.get('ci')
        comp      = cleaned.get('complemento', '')
        extension = cleaned.get('extension')
        if ci and extension:
            qs = MiembroVIP.objects.filter(ci=ci, complemento=comp, extension=extension)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    _('Ya existe un miembro con esa CI y extensión.')
                )
        return cleaned


# ─────────────────────────────────────────────
#  RECARGA DE SALDO  (HU2 / HU3)
# ─────────────────────────────────────────────

class RecargaForm(StyledFormMixin, forms.ModelForm):
    """
    Formulario para que el personal procese una recarga VIP.
    Conectar con: #page-miembros → sección recargas pendientes.
    """
    class Meta:
        model  = Recarga
        fields = ('miembro', 'monto', 'metodo_pago', 'notas')
        labels = {
            'miembro':     _('Miembro VIP'),
            'monto':       _('Monto (BOB)'),
            'metodo_pago': _('Método de Pago'),
            'notas':       _('Notas'),
        }
        widgets = {
            'monto': forms.NumberInput(attrs={
                'placeholder': 'Ej: 50.00', 'step': '0.01', 'min': '10',
            }),
            'notas': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None and monto < Decimal('10.00'):
            raise ValidationError(_('El monto mínimo de recarga es 10 BOB.'))
        return monto


class AprobarRecargaForm(StyledFormMixin, forms.Form):
    """
    Formulario simple para aprobar/rechazar una recarga pendiente.
    """
    ACCION_CHOICES = [
        ('APROBADA',  _('Aprobar')),
        ('RECHAZADA', _('Rechazar')),
    ]
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        label=_('Acción'),
        widget=forms.Select(),
    )
    notas = forms.CharField(
        required=False,
        label=_('Motivo / Notas'),
        widget=forms.Textarea(attrs={'rows': 2}),
    )


# ─────────────────────────────────────────────
#  EVENTO / PARTIDO  (HU10)
# ─────────────────────────────────────────────

class EventoForm(StyledFormMixin, forms.ModelForm):
    """
    Formulario de creación/edición de eventos deportivos.
    Conectar con: #page-partidos → modal de nuevo partido.
    """
    class Meta:
        model  = Evento
        fields = (
            'nombre', 'equipo_local', 'equipo_visitante',
            'fecha', 'hora', 'precio_base',
            'capacidad_total', 'estado', 'descripcion',
        )
        labels = {
            'nombre':            _('Nombre del Evento'),
            'equipo_local':      _('Equipo Local'),
            'equipo_visitante':  _('Equipo Visitante'),
            'fecha':             _('Fecha'),
            'hora':              _('Hora'),
            'precio_base':       _('Precio Base (BOB)'),
            'capacidad_total':   _('Capacidad Total'),
            'estado':            _('Estado'),
            'descripcion':       _('Descripción (opcional)'),
        }
        widgets = {
            'fecha':       forms.DateInput(attrs={'type': 'date'}),
            'hora':        forms.TimeInput(attrs={'type': 'time'}),
            'precio_base': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': 'Ej: 30.00'}),
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        capacidad = cleaned.get('capacidad_total')
        if capacidad is not None and capacidad <= 0:
            self.add_error('capacidad_total', _('La capacidad debe ser mayor a cero.'))
        precio = cleaned.get('precio_base')
        if precio is not None and precio < Decimal('0.00'):
            self.add_error('precio_base', _('El precio no puede ser negativo.'))
        return cleaned

    def save(self, commit=True):
        evento = super().save(commit=False)
        # Al crear, la capacidad disponible es igual a la total
        if not evento.pk:
            evento.capacidad_disponible = evento.capacidad_total
        if commit:
            evento.save()
            try:
                evento.actualizar_precios_por_sector()
            except Exception:
                # No bloquear la creación del evento si por alguna razón falla
                pass
        return evento


# ─────────────────────────────────────────────
#  VENTA DE BOLETO  (HU11)
# ─────────────────────────────────────────────

class VentaBoletoForm(StyledFormMixin, forms.ModelForm):
    """
    Formulario de venta de boleto para el personal.
    Conectar con: #page-ventas → modal de nueva venta.
    La validación de saldo y capacidad se realiza en la vista.
    """
    class Meta:
        model  = Boleto
        fields = ('evento', 'miembro_vip', 'sector', 'precio_pagado')
        labels = {
            'evento':        _('Evento / Partido'),
            'miembro_vip':   _('Miembro VIP (opcional)'),
            'sector':        _('Sector'),
            'precio_pagado': _('Precio (BOB)'),
        }
        widgets = {
            'precio_pagado': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'placeholder': 'Precio en BOB',
            }),
        }

    def clean_precio_pagado(self):
        precio = self.cleaned_data.get('precio_pagado')
        if precio is not None and precio < Decimal('0.00'):
            raise ValidationError(_('El precio no puede ser negativo.'))
        return precio

    def clean(self):
        cleaned = super().clean()
        evento  = cleaned.get('evento')
        if evento and evento.agotado:
            raise ValidationError(
                _(f'El evento "{evento}" está agotado. No hay capacidad disponible.')
            )
        return cleaned


# ─────────────────────────────────────────────
#  CIERRE DE CAJA  (HU5)
# ─────────────────────────────────────────────

class CierreCajaForm(StyledFormMixin, forms.ModelForm):
    """
    Formulario de confirmación de cierre de caja.
    Los totales se calculan automáticamente en la vista.
    Conectar con: #page-reportes → sección de cierre de caja.
    """
    class Meta:
        model  = CierreCaja
        fields = ('notas',)
        labels = {'notas': _('Notas del Cierre')}
        widgets = {'notas': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones...'})}
