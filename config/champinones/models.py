"""
models.py — CDT Real Oruro - Sistema de Gestión
Definición de todos los modelos del sistema con validadores bolivianos.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
import uuid


# ─────────────────────────────────────────────
#  VALIDADORES BOLIVIANOS
# ─────────────────────────────────────────────

validate_ci = RegexValidator(
    regex=r'^\d{5,8}$',
    message=_('La CI debe tener entre 5 y 8 dígitos numéricos.'),
)

validate_complemento = RegexValidator(
    regex=r'^[A-Za-z0-9]{2}$',
    message=_('El complemento debe tener exactamente 2 caracteres alfanuméricos (ej: 1A, 3C).'),
)

validate_celular = RegexValidator(
    regex=r'^[678]\d{7}$',
    message=_('El celular debe tener 8 dígitos y comenzar con 6, 7 u 8.'),
)


# ─────────────────────────────────────────────
#  CHOICES
# ─────────────────────────────────────────────

class DepartamentoExtension(models.TextChoices):
    LP = 'LP', _('La Paz')
    CB = 'CB', _('Cochabamba')
    SC = 'SC', _('Santa Cruz')
    OR = 'OR', _('Oruro')
    PT = 'PT', _('Potosí')
    CH = 'CH', _('Chuquisaca')
    TJ = 'TJ', _('Tarija')
    BE = 'BE', _('Beni')
    PD = 'PD', _('Pando')


class RolUsuario(models.TextChoices):
    ADMIN      = 'ADMIN',    _('Administrador')
    PERSONAL   = 'PERSONAL', _('Personal')
    MIEMBRO_VIP = 'VIP',     _('Miembro VIP')


class EstadoMiembro(models.TextChoices):
    ACTIVO   = 'ACTIVO',   _('Activo')
    INACTIVO = 'INACTIVO', _('Inactivo')
    SUSPENDIDO = 'SUSPENDIDO', _('Suspendido')


class EstadoCierre(models.TextChoices):
    ABIERTO  = 'ABIERTO',  _('Abierto')
    CERRADO  = 'CERRADO',  _('Cerrado')


# ─────────────────────────────────────────────
#  USUARIO PERSONALIZADO  (HU4 / HU8 / HU9)
# ─────────────────────────────────────────────

class Usuario(AbstractUser):
    """
    Extiende AbstractUser con un campo de rol para diferenciar
    entre Administrador, Personal y Miembro VIP.
    """
    rol = models.CharField(
        max_length=10,
        choices=RolUsuario.choices,
        default=RolUsuario.PERSONAL,
        verbose_name=_('Rol'),
    )

    class Meta:
        verbose_name        = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering            = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    # ── Helpers de rol ──────────────────────
    @property
    def es_admin(self):
        return self.rol == RolUsuario.ADMIN or self.is_superuser

    @property
    def es_personal(self):
        return self.rol == RolUsuario.PERSONAL

    @property
    def es_vip(self):
        return self.rol == RolUsuario.MIEMBRO_VIP


# ─────────────────────────────────────────────
#  MIEMBRO VIP  (HU1 / HU6 / HU7)
# ─────────────────────────────────────────────

class MiembroVIP(models.Model):
    """
    Almacena los datos del socio/miembro VIP con CI boliviana,
    saldo en BOB y estado de membresía.
    """
    # Vinculación opcional a cuenta de sistema
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='miembro_vip',
        verbose_name=_('Cuenta de usuario'),
    )

    # ── Identificación boliviana ─────────────
    ci = models.CharField(
        max_length=8,
        validators=[validate_ci],
        verbose_name=_('Cédula de Identidad'),
    )
    complemento = models.CharField(
        max_length=2,
        blank=True,
        validators=[validate_complemento],
        verbose_name=_('Complemento CI'),
        help_text=_('Solo si existe duplicidad (ej: 1A, 3C).'),
    )
    extension = models.CharField(
        max_length=2,
        choices=DepartamentoExtension.choices,
        verbose_name=_('Extensión (Departamento)'),
    )

    # ── Datos personales ────────────────────
    nombre_completo = models.CharField(
        max_length=150,
        verbose_name=_('Nombre Completo'),
    )
    correo = models.EmailField(
        unique=True,
        verbose_name=_('Correo Electrónico'),
    )
    celular = models.CharField(
        max_length=8,
        validators=[validate_celular],
        verbose_name=_('Celular'),
    )

    # ── Saldo y estado ──────────────────────
    saldo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Saldo (BOB)'),
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoMiembro.choices,
        default=EstadoMiembro.ACTIVO,
        verbose_name=_('Estado'),
    )
    fecha_registro = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Fecha de Registro'),
    )

    class Meta:
        verbose_name        = _('Miembro VIP')
        verbose_name_plural = _('Miembros VIP')
        ordering            = ['-fecha_registro']
        # Unicidad: CI + complemento + extensión forman la identidad completa
        constraints = [
            models.UniqueConstraint(
                fields=['ci', 'complemento', 'extension'],
                name='unique_ci_complemento_extension',
            )
        ]

    def __str__(self):
        comp = f'-{self.complemento}' if self.complemento else ''
        return f'{self.nombre_completo} ({self.ci}{comp} {self.extension})'

    @property
    def ci_completo(self):
        comp = f'-{self.complemento}' if self.complemento else ''
        return f'{self.ci}{comp} {self.extension}'


# ─────────────────────────────────────────────
#  TRANSACCIÓN / RECARGA  (HU2 / HU3)
# ─────────────────────────────────────────────

class Recarga(models.Model):
    """
    Historial de recargas de saldo para miembros VIP.
    Cada recarga suma al saldo actual del miembro.
    """

    class EstadoRecarga(models.TextChoices):
        PENDIENTE = 'PENDIENTE', _('Pendiente')
        APROBADA  = 'APROBADA',  _('Aprobada')
        RECHAZADA = 'RECHAZADA', _('Rechazada')

    class MetodoPago(models.TextChoices):
        EFECTIVO      = 'EFECTIVO',      _('Efectivo')
        TRANSFERENCIA = 'TRANSFERENCIA', _('Transferencia Bancaria')
        QR            = 'QR',            _('Pago por QR')

    miembro = models.ForeignKey(
        MiembroVIP,
        on_delete=models.PROTECT,
        related_name='recargas',
        verbose_name=_('Miembro VIP'),
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(10)],   # Mínimo 10 BOB
        verbose_name=_('Monto (BOB)'),
    )
    metodo_pago = models.CharField(
        max_length=15,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name=_('Método de Pago'),
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoRecarga.choices,
        default=EstadoRecarga.PENDIENTE,
        verbose_name=_('Estado'),
    )
    procesado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recargas_procesadas',
        verbose_name=_('Procesado por'),
    )
    fecha_solicitud = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Fecha de Solicitud'),
    )
    fecha_procesado = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Fecha de Procesamiento'),
    )
    notas = models.TextField(
        blank=True,
        verbose_name=_('Notas'),
    )

    class Meta:
        verbose_name        = _('Recarga')
        verbose_name_plural = _('Recargas')
        ordering            = ['-fecha_solicitud']

    def __str__(self):
        return f'Recarga {self.monto} BOB → {self.miembro} ({self.get_estado_display()})'


# ─────────────────────────────────────────────
#  EVENTO / PARTIDO  (HU10)
# ─────────────────────────────────────────────

class Evento(models.Model):
    """
    Representa un partido o evento deportivo con capacidad
    y precio base en Bolivianos.
    """

    class EstadoEvento(models.TextChoices):
        PROGRAMADO = 'PROGRAMADO', _('Programado')
        EN_CURSO   = 'EN_CURSO',   _('En Curso')
        FINALIZADO = 'FINALIZADO', _('Finalizado')
        CANCELADO  = 'CANCELADO',  _('Cancelado')

    nombre = models.CharField(
        max_length=200,
        verbose_name=_('Nombre del Evento'),
    )
    equipo_local = models.CharField(
        max_length=100,
        verbose_name=_('Equipo Local'),
    )
    equipo_visitante = models.CharField(
        max_length=100,
        verbose_name=_('Equipo Visitante'),
    )
    fecha = models.DateField(
        verbose_name=_('Fecha'),
    )
    hora = models.TimeField(
        verbose_name=_('Hora'),
    )
    precio_base = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Precio Base (BOB)'),
    )
    capacidad_total = models.PositiveIntegerField(
        verbose_name=_('Capacidad Total'),
    )
    capacidad_disponible = models.PositiveIntegerField(
        verbose_name=_('Capacidad Disponible'),
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoEvento.choices,
        default=EstadoEvento.PROGRAMADO,
        verbose_name=_('Estado'),
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
    )
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='eventos_creados',
        verbose_name=_('Creado por'),
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _('Evento')
        verbose_name_plural = _('Eventos')
        ordering            = ['fecha', 'hora']

    def __str__(self):
        return f'{self.equipo_local} vs {self.equipo_visitante} — {self.fecha}'

    @property
    def agotado(self):
        return self.capacidad_disponible <= 0

    SECTOR_MULTIPLIERS = {
        'GENERAL': Decimal('1.00'),
        'PREFERENTE': Decimal('1.25'),
        'VIP': Decimal('1.50'),
        'PALCO': Decimal('2.00'),
    }

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que los campos tengan valores antes de compararlos
        if self.capacidad_disponible is not None and self.capacidad_total is not None:
            if self.capacidad_disponible > self.capacidad_total:
                raise ValidationError(
                    _('La capacidad disponible no puede superar la capacidad total.')
                )

    def actualizar_precios_por_sector(self):
        from .models import EventoSector
        base = Decimal(str(self.precio_base))
        for sector, multiplier in self.SECTOR_MULTIPLIERS.items():
            precio = (base * multiplier).quantize(Decimal('0.01'))
            EventoSector.objects.update_or_create(
                evento=self,
                sector=sector,
                defaults={'precio': precio}
            )

    def save(self, *args, **kwargs):
        if self._state.adding and self.capacidad_disponible is None:
            self.capacidad_disponible = self.capacidad_total
        super().save(*args, **kwargs)
        try:
            self.actualizar_precios_por_sector()
        except Exception:
            pass


class EventoSector(models.Model):
    """
    Precios por sector para cada evento. Se crea automáticamente al crear un Evento
    usando multiplicadores sobre `Evento.precio_base`.
    """
    class Sector(models.TextChoices):
        GENERAL    = 'GENERAL',    _('General')
        PREFERENTE = 'PREFERENTE', _('Preferente')
        VIP        = 'VIP',        _('VIP')
        PALCO      = 'PALCO',      _('Palco')

    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='precios_sector',
        verbose_name=_('Evento'),
    )
    sector = models.CharField(
        max_length=12,
        choices=Sector.choices,
        verbose_name=_('Sector'),
    )
    precio = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Precio (BOB)'),
    )

    class Meta:
        verbose_name = _('Precio por Sector')
        verbose_name_plural = _('Precios por Sector')
        unique_together = ('evento', 'sector')

    def __str__(self):
        return f'{self.evento} — {self.get_sector_display()}: {self.precio} BOB'


# ─────────────────────────────────────────────
#  BOLETO / VENTA  (HU10 / HU11)
# ─────────────────────────────────────────────

def generar_codigo_boleto():
    """Genera un código único de 12 caracteres en mayúsculas."""
    return uuid.uuid4().hex[:12].upper()


class Boleto(models.Model):
    """
    Representa la venta de un boleto para un evento.
    El miembro VIP es opcional (venta sin carnet).
    Incluye información completa de facturación y auditoría.
    """

    class SectorAsiento(models.TextChoices):
        GENERAL   = 'GENERAL',   _('General')
        PREFERENTE = 'PREFERENTE', _('Preferente')
        VIP       = 'VIP',       _('VIP')
        PALCO     = 'PALCO',     _('Palco')

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name='boletos',
        verbose_name=_('Evento'),
    )
    miembro_vip = models.ForeignKey(
        MiembroVIP,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='boletos',
        verbose_name=_('Miembro VIP'),
    )
    vendido_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='boletos_vendidos',
        verbose_name=_('Vendido por'),
    )
    sector = models.CharField(
        max_length=12,
        choices=SectorAsiento.choices,
        default=SectorAsiento.GENERAL,
        verbose_name=_('Sector'),
    )
    precio_pagado = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Precio Pagado (BOB)'),
    )
    codigo = models.CharField(
        max_length=12,
        unique=True,
        default=generar_codigo_boleto,
        editable=False,
        verbose_name=_('Código Único'),
    )
    # ── CAMPOS DE FACTURA MEJORADA ──────────
    numero_factura = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Número de Factura'),
        help_text=_('Generado automáticamente'),
        blank=True,
        null=True,
    )
    subtotal = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Subtotal (BOB)'),
    )
    impuesto_iva = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('IVA 13% (BOB)'),
    )
    descuento = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Descuento (BOB)'),
    )
    total_factura = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        editable=False,
        verbose_name=_('Total Factura (BOB)'),
        default=0.00,
    )
    # ── AUDITORÍA Y MÉTODOS DE PAGO ────────
    fecha_compra = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Fecha de Compra'),
    )
    pago_con_saldo_vip = models.BooleanField(
        default=False,
        verbose_name=_('Pagado con Saldo VIP'),
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('EFECTIVO', _('Efectivo')),
            ('TARJETA', _('Tarjeta')),
            ('SALDO_VIP', _('Saldo VIP')),
            ('OTRO', _('Otro')),
        ],
        default='EFECTIVO',
        verbose_name=_('Método de Pago'),
    )
    referencia_pago = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Referencia de Pago (transacción, talón, etc.)'),
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name=_('Observaciones'),
    )

    class Meta:
        verbose_name        = _('Boleto')
        verbose_name_plural = _('Boletos')
        ordering            = ['-fecha_compra']

    def __str__(self):
        return f'Boleto #{self.codigo} — {self.evento}'

    def generar_numero_factura(self):
        """Genera número de factura único: FCT-YYYYMMDD-NNNNNN"""
        from datetime import datetime
        hoy = datetime.now().strftime('%Y%m%d')
        numero_secuencial = str(Boleto.objects.filter(
            fecha_compra__date=timezone.now().date()
        ).count() + 1).zfill(6)
        return f'FCT-{hoy}-{numero_secuencial}'

    def save(self, *args, **kwargs):
        """Calcula automáticamente impuestos y totales antes de guardar."""
        if not self.numero_factura:
            self.numero_factura = self.generar_numero_factura()
        
        # Calcular subtotal si no está definido
        if not self.subtotal or self.subtotal == 0:
            self.subtotal = self.precio_pagado
        
        # IVA al 13% (Bolivia)
        self.impuesto_iva = Decimal(str(self.subtotal)) * Decimal('0.13')
        
        # Total = Subtotal + IVA - Descuentos
        self.total_factura = (Decimal(str(self.subtotal)) + 
                             Decimal(str(self.impuesto_iva)) - 
                             Decimal(str(self.descuento)))
        
        super().save(*args, **kwargs)

    def get_detalles_factura(self):
        """
        Retorna un diccionario con todos los detalles de factura.
        Incluye QR en formato base64.
        """
        import base64
        import io

        try:
            import qrcode
            from qrcode.constants import ERROR_CORRECT_M

            qr = qrcode.QRCode(
                version=None,
                error_correction=ERROR_CORRECT_M,
                box_size=8,
                border=2,
            )

            qr.add_data(self.codigo)
            qr.make(fit=True)

            img = qr.make_image(
                fill_color="#0f2a5f",
                back_color="white"
            )

            buf = io.BytesIO()
            img.save(buf, format='PNG')

            qr_b64 = base64.b64encode(
                buf.getvalue()
            ).decode('ascii')

            qr_data = f"data:image/png;base64,{qr_b64}"

        except ImportError:
            qr_data = ""

        return {
            'numero_factura': self.numero_factura or self.generar_numero_factura(),

            'codigo_boleto': self.codigo,
            'codigo': self.codigo,  # alias útil para JS

            'fecha': self.fecha_compra.strftime('%d/%m/%Y'),
            'hora': self.fecha_compra.strftime('%H:%M:%S'),

            'evento': str(self.evento),
            'equipo_local': self.evento.equipo_local,
            'equipo_visitante': self.evento.equipo_visitante,

            'fecha_evento': self.evento.fecha.strftime('%d/%m/%Y'),
            'hora_evento': self.evento.hora.strftime('%H:%M'),

            'sector': self.get_sector_display(),

            'subtotal': f'{self.subtotal:.2f}',
            'iva_13': f'{self.impuesto_iva:.2f}',
            'descuento': f'{self.descuento:.2f}',
            'total': f'{self.total_factura:.2f}',

            'precio': f'{self.precio_pagado:.2f}',
            'precio_pagado': f'{self.precio_pagado:.2f}',
            'compra': self.fecha_compra.strftime('%d/%m/%Y %H:%M:%S'),

            'cliente': (
                self.miembro_vip.nombre_completo
                if self.miembro_vip
                else 'Público General'
            ),

            'miembro': (
                self.miembro_vip.nombre_completo
                if self.miembro_vip
                else 'Público General'
            ),

            'ci': (
                self.miembro_vip.ci_completo
                if self.miembro_vip
                else '—'
            ),

            'ci_cliente': (
                self.miembro_vip.ci_completo
                if self.miembro_vip
                else 'N/A'
            ),

            'vendido_por': (
                self.vendido_por.get_full_name()
                if self.vendido_por
                else 'Sistema'
            ),

            'metodo_pago': self.get_metodo_pago_display(),
            'referencia_pago': self.referencia_pago or 'N/A',

            # NUEVO
            'qr': qr_data,
            'qr_disponible': bool(qr_data),
        }

# ─────────────────────────────────────────────
#  CIERRE DE CAJA  (HU5)
# ─────────────────────────────────────────────

class CierreCaja(models.Model):
    """
    Registro del cierre de caja diario.
    El total recaudado se calcula automáticamente desde las vistas.
    """
    fecha = models.DateField(
        unique=True,
        verbose_name=_('Fecha'),
    )
    total_ventas_boletos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Total por Venta de Boletos (BOB)'),
    )
    total_recargas = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Total por Recargas (BOB)'),
    )
    total_recaudado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Total Recaudado (BOB)'),
    )
    cantidad_boletos = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Cantidad de Boletos Vendidos'),
    )
    cantidad_recargas = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Cantidad de Recargas Procesadas'),
    )
    usuario_cierre = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='cierres_caja',
        verbose_name=_('Cerrado por'),
    )
    estado = models.CharField(
        max_length=8,
        choices=EstadoCierre.choices,
        default=EstadoCierre.ABIERTO,
        verbose_name=_('Estado'),
    )
    notas = models.TextField(
        blank=True,
        verbose_name=_('Notas del Cierre'),
    )
    fecha_cierre = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Fecha y Hora del Cierre'),
    )

    class Meta:
        verbose_name        = _('Cierre de Caja')
        verbose_name_plural = _('Cierres de Caja')
        ordering            = ['-fecha']

    def __str__(self):
        return f'Cierre {self.fecha} — {self.total_recaudado} BOB ({self.get_estado_display()})'


# ─────────────────────────────────────────────
#  APERTURA DE CAJA  (HU5)
# ─────────────────────────────────────────────

class AperturaCaja(models.Model):
    """
    Registro de apertura de caja diaria.
    Permite rastrear quién abre la caja y con cuánto dinero inicial.
    """
    fecha = models.DateField(
        unique=True,
        verbose_name=_('Fecha'),
    )
    usuario_apertura = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='aperturas_caja',
        verbose_name=_('Abierto por'),
    )
    monto_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name=_('Monto Inicial (BOB)'),
    )
    fecha_apertura = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Fecha y Hora de Apertura'),
    )
    notas = models.TextField(
        blank=True,
        verbose_name=_('Notas de Apertura'),
    )

    class Meta:
        verbose_name        = _('Apertura de Caja')
        verbose_name_plural = _('Aperturas de Caja')
        ordering            = ['-fecha']

    def __str__(self):
        return f'Apertura {self.fecha} por {self.usuario_apertura} — {self.monto_inicial} BOB'
