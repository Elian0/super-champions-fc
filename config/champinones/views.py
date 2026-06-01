"""
views.py — Super Champiñones FC
Vistas con lógica de negocio, RBAC y manejo de errores.
Todas las respuestas JSON son compatibles con el frontend HTML existente.
"""

import json
import logging
from decimal import Decimal
from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import (
    AprobarRecargaForm, CierreCajaForm, CrearPersonalForm,
    EditarPersonalForm, EventoForm, LoginForm, MiembroVIPForm,
    RecargaForm, RegistroVIPPublicoForm, VentaBoletoForm,
)
from .models import (
    Boleto, CierreCaja, EstadoCierre, Evento, MiembroVIP, Recarga,
    RolUsuario, Usuario, AperturaCaja,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  HELPERS DE RBAC
# ─────────────────────────────────────────────

def es_admin(user):
    return user.is_authenticated and (user.es_admin or user.is_superuser)


def es_personal_o_admin(user):
    return user.is_authenticated and user.rol in (RolUsuario.ADMIN, RolUsuario.PERSONAL)


def es_miembro_vip(user):
    return user.is_authenticated and user.rol == RolUsuario.MIEMBRO_VIP


class AdminRequired(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin: solo Administradores."""
    def test_func(self):
        return self.request.user.es_admin


class PersonalOAdminRequired(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin: Personal y Administradores."""
    def test_func(self):
        return es_personal_o_admin(self.request.user)


def json_error(msg, status=400):
    return JsonResponse({'ok': False, 'error': str(msg)}, status=status)


def json_ok(data=None, **kwargs):
    payload = {'ok': True}
    if data:
        payload.update(data)
    payload.update(kwargs)
    return JsonResponse(payload)


# ─────────────────────────────────────────────
#  HU4 / HU8 — AUTENTICACIÓN
# ─────────────────────────────────────────────

class LoginView(View):
    """
    HU4 / HU8 — Login con diferenciación de rol.
    GET  → renderiza login.html
    POST → autentica y redirige según rol

    ── Integración HTML ──
    Archivo: login.html (extraído del HTML estático, sección #login-page)
    Reemplazar:
      <form ... onclick="doLogin()">
    por:
      <form method="post" action="{% url 'login' %}">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn-main">Iniciar Sesión</button>
      </form>
    Mostrar errores:
      {% if form.errors %}<div class="login-error" style="display:flex;">{{ form.non_field_errors }}</div>{% endif %}
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return _redirigir_por_rol(request.user)
        form = LoginForm(request)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            logger.info('Login exitoso: %s (%s)', user.username, user.rol)
            return _redirigir_por_rol(user)
        logger.warning('Login fallido desde IP: %s', request.META.get('REMOTE_ADDR'))
        return render(request, self.template_name, {'form': form}, status=401)


def _redirigir_por_rol(user):
    """Redirige al dashboard correcto según el rol del usuario."""
    if user.es_admin or user.es_personal:
        return redirect('dashboard')
    if user.es_vip:
        return redirect('vip_portal')
    return redirect('login')


@login_required
def logout_view(request):
    """
    HU8 — Cerrar sesión.
    Vincular al botón: <a href="{% url 'logout' %}">⬅ Salir</a>
    """
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('login')


class RegistroVIPView(View):
    """
    HU1 — Auto-registro público de Miembro VIP.
    POST → crea MiembroVIP + Usuario y retorna JSON.

    ── Integración HTML ──
    Sección: #register-form en el HTML estático.
    Reemplazar onclick="doRegisterVip()" por submit con fetch:
      fetch("{% url 'registro_vip' %}", {method:'POST', body: formData, headers:{'X-CSRFToken': csrfToken}})
    """
    template_name = 'accounts/login.html'

    def get(self, request):
        return render(request, self.template_name, {
            'reg_form': RegistroVIPPublicoForm(),
            'show_register': True,
        })

    def post(self, request):
        form = RegistroVIPPublicoForm(request.POST)
        if not form.is_valid():
            errors = '; '.join([str(v[0]) for v in form.errors.values()])
            return render(request, self.template_name, {
                'reg_form': form,
                'reg_errors': errors,
                'show_register': True,
            })

        cd = form.cleaned_data
        try:
            with transaction.atomic():
                user = Usuario.objects.create_user(
                    username=cd['correo'],
                    email=cd['correo'],
                    password=cd['password'],
                    first_name=cd['nombre_completo'].split()[0],
                    last_name=' '.join(cd['nombre_completo'].split()[1:]),
                    rol=RolUsuario.MIEMBRO_VIP,
                )
                miembro = MiembroVIP.objects.create(
                    usuario=user,
                    nombre_completo=cd['nombre_completo'],
                    ci=cd['ci'],
                    complemento=cd['complemento'],
                    extension=cd['extension'],
                    correo=cd['correo'],
                    celular=cd['celular'],
                )
            login(request, user)
            logger.info('Nuevo Miembro VIP registrado: %s', miembro)
            return json_ok(redirect_url='/vip/')
        except Exception as exc:
            logger.error('Error al registrar VIP: %s', exc)
            return json_error(_('Error interno al crear la cuenta. Intenta de nuevo.'), 500)


# ─────────────────────────────────────────────
#  DASHBOARD PRINCIPAL
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def dashboard(request):
    """
    Vista principal del sistema de gestión.
    Organiza información por secciones y separa partidos por estado.
    ── Integración HTML ──
    Archivo: dashboard.html (sección #page-dashboard del HTML estático)
    Variables de contexto:
      {{ stats.boletos_hoy }}  → id="stat-ventas"
      {{ stats.vips_activos }} → id="stat-vips"
      {{ stats.ingresos_hoy }} → id="stat-ingresos"
      {{ stats.total_partidos }} → id="stat-partidos"
      {{ partidos_programados }}, {{ partidos_en_curso }}, {{ partidos_finalizados }}
      {% for v in ultimas_ventas %}...{% endfor %}    → tbody#dash-ventas-tbody
      {% for r in recargas_pendientes %}...{% endfor %} → tbody#dash-recargas-tbody
    """
    hoy = date.today()

    boletos_hoy  = Boleto.objects.filter(fecha_compra__date=hoy)
    recargas_hoy = Recarga.objects.filter(
        fecha_solicitud__date=hoy,
        estado=Recarga.EstadoRecarga.APROBADA,
    )
    recargas_pendientes = Recarga.objects.filter(
        estado=Recarga.EstadoRecarga.PENDIENTE
    ).select_related('miembro')

    stats = {
        'boletos_hoy':      boletos_hoy.count(),
        'vips_activos':     MiembroVIP.objects.filter(estado='ACTIVO').count(),
        'ingresos_hoy':     boletos_hoy.aggregate(t=Sum('precio_pagado'))['t'] or Decimal('0'),
        'total_partidos':   Evento.objects.exclude(estado='CANCELADO').count(),
    }

    # Separar partidos por estado
    partidos_programados = Evento.objects.filter(
        estado=Evento.EstadoEvento.PROGRAMADO,
        fecha__gte=hoy
    ).order_by('fecha')[:10]
    
    partidos_en_curso = Evento.objects.filter(
        estado=Evento.EstadoEvento.EN_CURSO
    ).order_by('-fecha')[:5]
    
    partidos_finalizados = Evento.objects.filter(
        estado=Evento.EstadoEvento.FINALIZADO
    ).order_by('-fecha')[:5]

    context = {
        'stats':               stats,
        'partidos_programados': partidos_programados,
        'partidos_en_curso':   partidos_en_curso,
        'partidos_finalizados': partidos_finalizados,
        'ultimas_ventas':      Boleto.objects.select_related('evento', 'miembro_vip').order_by('-fecha_compra')[:8],
        'recargas_pendientes': recargas_pendientes[:10],
        'es_admin':            request.user.es_admin,
    }
    return render(request, 'portal/dashboard.html', context)


# ─────────────────────────────────────────────
#  HU1 / HU6 / HU7 — CRUD MIEMBROS VIP
# ─────────────────────────────────────────────

class MiembroListView(PersonalOAdminRequired, ListView):
    """
    HU6 — Listar Miembros VIP con búsqueda.
    ── Integración HTML ──
    Archivo: miembros.html (sección #page-miembros)
    {% for m in miembros %}
      <tr>
        <td>{{ m.ci_completo }}</td>
        <td>{{ m.nombre_completo }}</td>
        <td>{{ m.celular }}</td>
        <td>{{ m.saldo }} Bs</td>
        <td><span class="badge badge-green">{{ m.get_estado_display }}</span></td>
        <td class="action-btns">
          <a href="{% url 'miembro_editar' m.pk %}" class="btn btn-sm btn-primary">Editar</a>
          <a href="{% url 'miembro_eliminar' m.pk %}" class="btn btn-sm btn-danger">Eliminar</a>
        </td>
      </tr>
    {% empty %}
      <tr><td colspan="6">No hay miembros registrados.</td></tr>
    {% endfor %}
    """
    model               = MiembroVIP
    template_name       = 'portal/miembros.html'
    context_object_name = 'miembros'
    paginate_by         = 20

    def get_queryset(self):
        qs = MiembroVIP.objects.all()
        q  = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(nombre_completo__icontains=q) |
                Q(ci__icontains=q) |
                Q(correo__icontains=q) |
                Q(celular__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form']     = MiembroVIPForm()
        ctx['es_admin'] = self.request.user.es_admin
        return ctx


class MiembroCreateView(PersonalOAdminRequired, CreateView):
    """
    HU1 — Crear nuevo Miembro VIP.
    ── Integración HTML ──
    Modal de creación en #page-miembros.
    <form method="post" action="{% url 'miembro_crear' %}">
      {% csrf_token %}
      {{ form.as_p }}
      <button type="submit" class="btn btn-primary">Guardar</button>
    </form>
    """
    model         = MiembroVIP
    form_class    = MiembroVIPForm
    template_name = 'portal/miembro_form.html'

    def form_valid(self, form):
        messages.success(self.request, _('Miembro VIP creado correctamente.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Corrige los errores del formulario.'))
        return super().form_invalid(form)

    def get_success_url(self):
        return '/miembros/'


class MiembroUpdateView(PersonalOAdminRequired, UpdateView):
    """
    HU7 — Editar Miembro VIP.
    """
    model         = MiembroVIP
    form_class    = MiembroVIPForm
    template_name = 'portal/miembro_form.html'

    def form_valid(self, form):
        messages.success(self.request, _('Miembro VIP actualizado.'))
        return super().form_valid(form)

    def get_success_url(self):
        return '/miembros/'


class MiembroDeleteView(AdminRequired, DeleteView):
    """
    HU7 — Eliminar Miembro VIP (solo Admin).
    ── Integración HTML ──
    <form method="post" action="{% url 'miembro_eliminar' m.pk %}">
      {% csrf_token %}
      <button type="submit" class="btn btn-danger">Confirmar Eliminación</button>
    </form>
    """
    model         = MiembroVIP
    template_name = 'portal/miembro_confirm_delete.html'
    success_url   = '/miembros/'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        logger.info('Miembro VIP eliminado: %s por %s', obj, request.user)
        messages.success(request, _(f'Miembro "{obj.nombre_completo}" eliminado.'))
        return super().delete(request, *args, **kwargs)


# ─────────────────────────────────────────────
#  HU2 / HU3 — RECARGA Y RECIBO
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def recarga_crear(request):
    """
    HU2 — Procesar recarga de saldo para un Miembro VIP.
    POST JSON: {"miembro": id, "monto": 50.00, "metodo_pago": "EFECTIVO"}

    ── Integración HTML ──
    Sección: recargas en #page-miembros.
    El JS llama a este endpoint vía fetch y actualiza el saldo mostrado.
    """
    if request.method != 'POST':
        return json_error(_('Método no permitido.'), 405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    form = RecargaForm(data)
    if not form.is_valid():
        return json_error(form.errors)

    try:
        with transaction.atomic():
            recarga = form.save(commit=False)
            recarga.procesado_por = request.user
            recarga.estado        = Recarga.EstadoRecarga.APROBADA
            recarga.fecha_procesado = timezone.now()
            recarga.save()

            # Sumar saldo al miembro
            miembro = recarga.miembro
            miembro.saldo += recarga.monto
            miembro.save(update_fields=['saldo'])

            logger.info(
                'Recarga %s BOB → %s procesada por %s',
                recarga.monto, miembro, request.user
            )

        return json_ok(
            recibo={
                'id':              recarga.pk,
                'miembro':         miembro.nombre_completo,
                'ci':              miembro.ci_completo,
                'monto':           str(recarga.monto),
                'metodo_pago':     recarga.get_metodo_pago_display(),
                'fecha':           recarga.fecha_procesado.strftime('%d/%m/%Y %H:%M'),
                'saldo_nuevo':     str(miembro.saldo),
                'procesado_por':   request.user.get_full_name() or request.user.username,
            }
        )
    except Exception as exc:
        logger.error('Error en recarga: %s', exc)
        return json_error(_('Error interno al procesar la recarga.'), 500)


@login_required
@user_passes_test(es_personal_o_admin)
def recarga_aprobar(request, pk):
    """
    HU2 — Aprobar o rechazar una recarga pendiente.
    PATCH JSON: {"accion": "APROBADA"|"RECHAZADA", "notas": "..."}
    """
    recarga = get_object_or_404(Recarga, pk=pk, estado=Recarga.EstadoRecarga.PENDIENTE)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    form = AprobarRecargaForm(data)
    if not form.is_valid():
        return json_error(form.errors)

    accion = form.cleaned_data['accion']

    try:
        with transaction.atomic():
            recarga.estado          = accion
            recarga.procesado_por   = request.user
            recarga.fecha_procesado = timezone.now()
            recarga.notas           = form.cleaned_data.get('notas', '')
            recarga.save()

            if accion == Recarga.EstadoRecarga.APROBADA:
                recarga.miembro.saldo += recarga.monto
                recarga.miembro.save(update_fields=['saldo'])

        return json_ok(estado=accion, saldo_nuevo=str(recarga.miembro.saldo))
    except Exception as exc:
        logger.error('Error al aprobar recarga %s: %s', pk, exc)
        return json_error(_('Error al procesar la acción.'), 500)


# ─────────────────────────────────────────────
#  HU9 — CRUD PERSONAL (solo Admin)
# ─────────────────────────────────────────────

class PersonalListView(AdminRequired, ListView):
    """
    HU9 — Lista de usuarios Personal/Admin.
    ── Integración HTML ──
    Archivo: usuarios.html (sección #page-usuarios)
    {% for u in usuarios %}
      <tr>
        <td>{{ u.get_full_name }}</td>
        <td>{{ u.email }}</td>
        <td><span class="badge badge-blue">{{ u.get_rol_display }}</span></td>
        <td>{% if u.is_active %}<span class="badge badge-green">Activo</span>{% else %}Inactivo{% endif %}</td>
        <td class="action-btns">
          <a href="{% url 'personal_editar' u.pk %}" class="btn btn-sm btn-primary">Editar</a>
          <a href="{% url 'personal_eliminar' u.pk %}" class="btn btn-sm btn-danger">Eliminar</a>
        </td>
      </tr>
    {% endfor %}
    """
    model               = Usuario
    template_name       = 'portal/usuarios.html'
    context_object_name = 'usuarios'

    def get_queryset(self):
        return Usuario.objects.filter(
            rol__in=[RolUsuario.ADMIN, RolUsuario.PERSONAL]
        ).order_by('first_name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = CrearPersonalForm()
        return ctx


class PersonalCreateView(AdminRequired, CreateView):
    """HU9 — Crear usuario Personal o Admin."""
    model         = Usuario
    form_class    = CrearPersonalForm
    template_name = 'portal/usuario_form.html'
    success_url   = '/usuarios/'

    def form_valid(self, form):
        messages.success(self.request, _('Usuario creado correctamente.'))
        logger.info('Usuario creado: %s por %s', form.instance, self.request.user)
        return super().form_valid(form)


class PersonalUpdateView(AdminRequired, UpdateView):
    """HU9 — Editar usuario Personal."""
    model         = Usuario
    form_class    = EditarPersonalForm
    template_name = 'portal/usuario_form.html'
    success_url   = '/usuarios/'

    def form_valid(self, form):
        messages.success(self.request, _('Usuario actualizado.'))
        return super().form_valid(form)


class PersonalDeleteView(AdminRequired, DeleteView):
    """HU9 — Eliminar usuario Personal (no puede eliminar su propia cuenta)."""
    model         = Usuario
    template_name = 'portal/usuario_confirm_delete.html'
    success_url   = '/usuarios/'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.pk == request.user.pk:
            messages.error(request, _('No puedes eliminar tu propia cuenta.'))
            return redirect('personal_lista')
        return super().dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────────
#  HU10 — EVENTOS / PARTIDOS
# ─────────────────────────────────────────────

class EventoListView(PersonalOAdminRequired, ListView):
    """
    HU10 — Listar eventos.
    ── Integración HTML ──
    Archivo: partidos.html (sección #page-partidos)
    {% for e in eventos %}
      <div class="partido-card">
        <div class="partido-card-header">
          <span class="partido-date">{{ e.fecha }} {{ e.hora }}</span>
          <span class="badge {% if e.agotado %}badge-red{% else %}badge-green{% endif %}">
            {% if e.agotado %}Agotado{% else %}{{ e.capacidad_disponible }} disponibles{% endif %}
          </span>
        </div>
        <div class="partido-body">
          <div class="team-block"><div class="team-name">{{ e.equipo_local }}</div></div>
          <span class="vs-badge">VS</span>
          <div class="team-block"><div class="team-name">{{ e.equipo_visitante }}</div></div>
        </div>
        <div class="partido-footer">
          <span>{{ e.precio_base }} Bs</span>
          <a href="{% url 'venta_crear' %}?evento={{ e.pk }}" class="btn btn-sm btn-success">🎟 Vender</a>
        </div>
      </div>
    {% endfor %}
    """
    model               = Evento
    template_name       = 'portal/partidos.html'
    context_object_name = 'eventos'

    def get_queryset(self):
        return Evento.objects.exclude(estado='CANCELADO').order_by('fecha', 'hora')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Separar partidos por estado para mejor visualización
        ctx['partidos_programados'] = Evento.objects.filter(
            estado=Evento.EstadoEvento.PROGRAMADO
        ).order_by('fecha', 'hora')
        
        ctx['partidos_en_curso'] = Evento.objects.filter(
            estado=Evento.EstadoEvento.EN_CURSO
        ).order_by('-fecha', '-hora')
        
        ctx['partidos_finalizados'] = Evento.objects.filter(
            estado=Evento.EstadoEvento.FINALIZADO
        ).order_by('-fecha', '-hora')
        
        ctx['form']     = EventoForm()
        ctx['es_admin'] = self.request.user.es_admin
        return ctx


class EventoCreateView(PersonalOAdminRequired, CreateView):
    """HU10 — Crear evento/partido."""
    model         = Evento
    form_class    = EventoForm
    template_name = 'portal/partido_form.html'
    success_url   = '/partidos/'

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, _('Evento creado correctamente.'))
        return super().form_valid(form)


class EventoUpdateView(PersonalOAdminRequired, UpdateView):
    """HU10 — Editar evento."""
    model         = Evento
    form_class    = EventoForm
    template_name = 'portal/partido_form.html'
    success_url   = '/partidos/'


class EventoDeleteView(AdminRequired, DeleteView):
    """HU10 — Eliminar evento (solo Admin)."""
    model       = Evento
    success_url = '/partidos/'
    template_name = 'portal/partido_confirm_delete.html'


@login_required
@user_passes_test(es_personal_o_admin)
def evento_cambiar_estado(request, pk):
    """
    Endpoint AJAX para cambiar estado del evento rápidamente.
    POST JSON: {"nuevo_estado": "PROGRAMADO"|"EN_VENTA"|"JUGANDO"|"FINALIZADO"|"CANCELADO"}
    
    Retorna JSON con confirmación.
    """
    evento = get_object_or_404(Evento, pk=pk)
    
    if request.method != 'POST':
        return json_error(_('Método no permitido.'), 405)
    
    try:
        data = json.loads(request.body)
        nuevo_estado = data.get('nuevo_estado')
    except (json.JSONDecodeError, KeyError):
        return json_error(_('Datos inválidos.'))
    
    # Validar que el estado sea válido
    estados_validos = dict(Evento.EstadoEvento.choices)
    if nuevo_estado not in estados_validos:
        return json_error(_(f'Estado "{nuevo_estado}" no válido.'))
    
    try:
        evento.estado = nuevo_estado
        evento.save(update_fields=['estado'])
        
        logger.info('Estado de evento %s cambiado a %s por %s', evento.pk, nuevo_estado, request.user)
        
        return json_ok(
            evento_id=evento.pk,
            nuevo_estado=nuevo_estado,
            estado_display=evento.get_estado_display(),
            mensaje=_('Estado actualizado exitosamente.')
        )
    except Exception as exc:
        logger.error('Error al cambiar estado de evento: %s', exc)
        return json_error(_('Error al actualizar el estado.'), 500)


@login_required
@user_passes_test(es_personal_o_admin)
def evento_boletos_lista(request, pk):
    """
    Vista para ver/listar todos los boletos vendidos de un evento.
    GET /partidos/<id>/boletos/ → HTML con tabla de boletos
    GET /partidos/<id>/boletos/?formato=csv → CSV descargable
    GET /partidos/<id>/boletos/?formato=pdf → PDF (requiere reportlab)
    """
    evento = get_object_or_404(Evento, pk=pk)
    boletos = Boleto.objects.filter(evento=evento).select_related(
        'miembro_vip', 'vendido_por'
    ).order_by('-fecha_compra')
    
    # Estadísticas
    stats = {
        'total_boletos': boletos.count(),
        'total_ingresos': boletos.aggregate(Sum('precio_pagado'))['precio_pagado__sum'] or Decimal('0'),
        'boletos_vip': boletos.filter(pago_con_saldo_vip=True).count(),
        'boletos_efectivo': boletos.filter(pago_con_saldo_vip=False).count(),
    }
    
    # Verificar si pide formato CSV o PDF
    formato = request.GET.get('formato', 'html')
    
    if formato == 'csv':
        # Generar CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Código Boleto', 'Número Factura', 'Cliente', 'CI', 
            'Sector', 'Precio (BOB)', 'Método Pago', 'Fecha Compra', 'Vendido por'
        ])
        for boleto in boletos:
            writer.writerow([
                boleto.codigo,
                boleto.numero_factura or 'N/A',
                boleto.miembro_vip.nombre_completo if boleto.miembro_vip else 'General',
                boleto.miembro_vip.ci_completo if boleto.miembro_vip else 'N/A',
                boleto.get_sector_display(),
                f"{boleto.precio_pagado:.2f}",
                boleto.get_metodo_pago_display(),
                boleto.fecha_compra.strftime('%d/%m/%Y %H:%M'),
                boleto.vendido_por.get_full_name() if boleto.vendido_por else 'Sistema',
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="boletos_{evento.pk}_{date.today()}.csv"'
        return response
    
    context = {
        'evento': evento,
        'boletos': boletos,
        'stats': stats,
    }
    
    return render(request, 'portal/evento_boletos.html', context)


# ─────────────────────────────────────────────
#  HU11 — VENTA DE BOLETOS
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def venta_crear(request):
    """
    HU11 — Proceso de venta de boleto.

    Lógica:
    1. Obtiene precio automáticamente del evento (precio_base).
    2. Verifica que el evento tenga capacidad disponible.
    3. Si hay Miembro VIP, verifica saldo suficiente.
    4. Descuenta saldo del VIP (si aplica) y reduce capacidad del evento.
    5. Crea el boleto y retorna los datos del recibo.

    ── Integración HTML ──
    Modal: #page-ventas → openModalVenta() en JS.
    POST a este endpoint con JSON o form-data.
    Respuesta: JSON con datos del boleto para renderizar ticket.
    """
    if request.method == 'GET':
        evento_id = request.GET.get('evento')
        # Obtener evento para mostrar su precio
        evento = None
        if evento_id:
            evento = Evento.objects.filter(pk=evento_id).first()
        form = VentaBoletoForm(initial={'evento': evento_id} if evento_id else {})
        return render(request, 'portal/venta_form.html', {'form': form, 'evento': evento})

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, Exception):
        data = request.POST

    form = VentaBoletoForm(data)
    if not form.is_valid():
        return json_error(form.errors)

    evento     = form.cleaned_data['evento']
    miembro    = form.cleaned_data.get('miembro_vip')
    # Usar precio por sector si existe, si no usar precio_pagado o precio_base
    precio     = form.cleaned_data.get('precio_pagado')
    sector     = form.cleaned_data.get('sector')
    if not precio:
        # Intentar obtener precio desde EventoSector
        try:
            from .models import EventoSector
            es = EventoSector.objects.filter(evento=evento, sector=sector).first()
            if es:
                precio = es.precio
        except Exception:
            precio = None
    if not precio:
        precio = evento.precio_base
    pago_vip   = False

    try:
        with transaction.atomic():
            # ── Validación: capacidad ──────────────
            evento_lock = Evento.objects.select_for_update().get(pk=evento.pk)
            if evento_lock.agotado:
                return json_error(
                    f'El evento "{evento_lock}" está agotado (capacidad 0).', 409
                )

            # ── Validación: saldo VIP ──────────────
            if miembro:
                miembro_lock = MiembroVIP.objects.select_for_update().get(pk=miembro.pk)
                if miembro_lock.saldo < precio:
                    return json_error(
                        f'Saldo insuficiente. Saldo actual: {miembro_lock.saldo} BOB, '
                        f'Precio: {precio} BOB.',
                        402,
                    )
                miembro_lock.saldo -= precio
                miembro_lock.save(update_fields=['saldo'])
                pago_vip = True

            # ── Reducir capacidad ─────────────────
            evento_lock.capacidad_disponible -= 1
            evento_lock.save(update_fields=['capacidad_disponible'])

            # ── Crear boleto ──────────────────────
            boleto = Boleto.objects.create(
                evento           = evento_lock,
                miembro_vip      = miembro if miembro else None,
                vendido_por      = request.user,
                sector           = form.cleaned_data['sector'],
                precio_pagado    = precio,
                subtotal         = precio,
                pago_con_saldo_vip = pago_vip,
                metodo_pago      = 'SALDO_VIP' if pago_vip else 'EFECTIVO',
            )

        logger.info('Boleto %s vendido por %s (Factura: %s)', boleto.codigo, request.user, boleto.numero_factura)

        # Obtener detalles completos de factura
        factura = boleto.get_detalles_factura()

        return json_ok(
            boleto=factura,
            exito=True,
            mensaje='Boleto vendido exitosamente',
        )
    except Exception as exc:
        logger.error('Error en venta de boleto: %s', exc, exc_info=True)
        return json_error(_('Error interno al procesar la venta.'), 500)



@login_required
@user_passes_test(es_personal_o_admin)
def venta_sector_precio(request):
    """API: retorna el precio configurado para un evento y sector.

    GET params: ?evento=<id>&sector=GENERAL
    """
    evento_id = request.GET.get('evento')
    sector = request.GET.get('sector')
    if not evento_id or not sector:
        return json_error('Parámetros insuficientes (evento, sector).', 400)
    try:
        es = Evento.objects.filter(pk=evento_id).first()
        if not es:
            return json_error('Evento no encontrado.', 404)
        from .models import EventoSector
        precio_obj = EventoSector.objects.filter(evento=es, sector=sector).first()
        if precio_obj:
            return json_ok(precio=str(precio_obj.precio))
        # fallback: precio_base
        return json_ok(precio=str(es.precio_base))
    except Exception as exc:
        logger.error('Error obteniendo precio por sector: %s', exc, exc_info=True)
        return json_error('Error interno', 500)





# ─────────────────────────────────────────────
#  HU5 — CIERRE DE CAJA
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def cierre_caja(request):
    """
    HU5 — Calcular y cerrar la caja del día actual.

    Lógica automática:
    - Suma todos los boletos vendidos hoy.
    - Suma todas las recargas aprobadas hoy.
    - Previene doble cierre (estado CERRADO).

    ── Integración HTML ──
    Archivo: reportes.html (sección #page-reportes)
    Context:
      {{ resumen.total_boletos }}   → Total por boletos del día
      {{ resumen.total_recargas }}  → Total por recargas del día
      {{ resumen.total_general }}   → Total general
      {{ resumen.cantidad_boletos }}
      {{ resumen.cantidad_recargas }}
      {% if cierre_hoy %}
        <div>Caja cerrada a las {{ cierre_hoy.fecha_cierre }}</div>
      {% else %}
        <form method="post" action="{% url 'cierre_caja' %}">...</form>
      {% endif %}
    """
    hoy = date.today()

    # Verificar si ya existe cierre para hoy
    cierre_existente = CierreCaja.objects.filter(
        fecha=hoy, estado=EstadoCierre.CERRADO
    ).first()

    # Calcular totales del día
    boletos_hoy  = Boleto.objects.filter(fecha_compra__date=hoy)
    recargas_hoy = Recarga.objects.filter(
        fecha_solicitud__date=hoy,
        estado=Recarga.EstadoRecarga.APROBADA,
    )

    agg_boletos  = boletos_hoy.aggregate(total=Sum('precio_pagado'), cant=Count('pk'))
    agg_recargas = recargas_hoy.aggregate(total=Sum('monto'), cant=Count('pk'))

    total_boletos  = agg_boletos['total']  or Decimal('0')
    total_recargas = agg_recargas['total'] or Decimal('0')
    cant_boletos   = agg_boletos['cant']   or 0
    cant_recargas  = agg_recargas['cant']  or 0

    resumen = {
        'fecha':             hoy,
        'total_boletos':     total_boletos,
        'total_recargas':    total_recargas,
        'total_general':     total_boletos + total_recargas,
        'cantidad_boletos':  cant_boletos,
        'cantidad_recargas': cant_recargas,
        'detalle_boletos':   boletos_hoy.select_related('evento', 'miembro_vip'),
        'detalle_recargas':  recargas_hoy.select_related('miembro'),
    }

    if request.method == 'POST':
        if cierre_existente:
            return json_error('La caja del día de hoy ya fue cerrada.', 409)

        form = CierreCajaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    cierre, created = CierreCaja.objects.get_or_create(
                        fecha=hoy,
                        defaults={'usuario_cierre': request.user},
                    )
                    cierre.total_ventas_boletos = total_boletos
                    cierre.total_recargas       = total_recargas
                    cierre.total_recaudado      = total_boletos + total_recargas
                    cierre.cantidad_boletos     = cant_boletos
                    cierre.cantidad_recargas    = cant_recargas
                    cierre.notas                = form.cleaned_data.get('notas', '')
                    cierre.estado               = EstadoCierre.CERRADO
                    cierre.fecha_cierre         = timezone.now()
                    cierre.usuario_cierre       = request.user
                    cierre.save()

                logger.info('Cierre de caja realizado por %s — Total: %s BOB',
                            request.user, cierre.total_recaudado)

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json_ok(
                        total=str(cierre.total_recaudado),
                        fecha=str(cierre.fecha),
                        hora=cierre.fecha_cierre.strftime('%H:%M'),
                    )
                messages.success(
                    request,
                    f'Cierre de caja realizado. Total: {cierre.total_recaudado} BOB.'
                )
                return redirect('cierre_caja')
            except Exception as exc:
                logger.error('Error en cierre de caja: %s', exc, exc_info=True)
                return json_error('Error al cerrar la caja.', 500)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = []
            for field, messages in form.errors.items():
                for message in messages:
                    errors.append(f'{field}: {message}' if field != '__all__' else str(message))
            return json_error(' '.join(errors) or 'Datos inválidos.', 400)

        return render(request, 'portal/reportes.html', {
            'form': form, 'resumen': resumen, 'cierre_hoy': cierre_existente,
        })

    form = CierreCajaForm()
    historial = CierreCaja.objects.order_by('-fecha')[:10]

    return render(request, 'portal/reportes.html', {
        'form':             form,
        'resumen':          resumen,
        'cierre_hoy':       cierre_existente,
        'historial_cierres': historial,
    })


@login_required
@user_passes_test(es_personal_o_admin)
def apertura_caja(request):
    """
    GET: Muestra formulario de apertura de caja.
    POST: Registra la apertura de caja con monto inicial.
    """
    hoy = date.today()
    apertura_existente = AperturaCaja.objects.filter(fecha=hoy).first()
    cierre_hoy = CierreCaja.objects.filter(fecha=hoy, estado=EstadoCierre.CERRADO).first()
    
    if request.method == 'POST':
        if apertura_existente:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error('La caja ya fue abierta hoy.', 409)
            messages.warning(request, 'La caja ya fue abierta hoy.')
            return redirect('apertura_caja')
        if cierre_hoy:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error('La caja ya fue cerrada hoy. No se puede abrir nuevamente.', 409)
            messages.warning(request, 'La caja ya fue cerrada hoy. No se puede abrir nuevamente.')
            return redirect('apertura_caja')
        
        try:
            monto = request.POST.get('monto_inicial', '0')
            notas = request.POST.get('notas', '')
            
            apertura = AperturaCaja.objects.create(
                fecha=hoy,
                usuario_apertura=request.user,
                monto_inicial=Decimal(monto),
                notas=notas,
            )
            
            logger.info('Caja abierta por %s con monto inicial %s BOB',
                       request.user, monto)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_ok(
                    apertura_id=apertura.pk,
                    usuario=apertura.usuario_apertura.get_full_name(),
                    monto=str(apertura.monto_inicial),
                    fecha=apertura.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
                )
            
            messages.success(request, f'Caja abierta con {monto} BOB.')
            return redirect('apertura_caja')
        
        except Exception as exc:
            logger.error('Error en apertura de caja: %s', exc)
            return json_error('Error al abrir la caja.', 500)
    
    return render(request, 'portal/apertura_caja.html', {
        'apertura_hoy': apertura_existente,
        'cierre_hoy': cierre_hoy,
    })


# ─────────────────────────────────────────────
#  PORTAL VIP
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_miembro_vip)
def vip_portal(request):
    """
    Portal del Miembro VIP: ver saldo, partidos, mis boletos.
    ── Integración HTML ──
    Archivo: vip_portal.html (sección #vip-portal del HTML estático)
    Context:
      {{ miembro.nombre_completo }}  → vip-nombre
      {{ miembro.saldo }}            → saldo-display
      {% for e in eventos %}...{% endfor %} → vip-partidos-grid
      {% for b in mis_boletos %}...{% endfor %} → vip-boletos-list
    """
    try:
        miembro = request.user.miembro_vip
    except MiembroVIP.DoesNotExist:
        logout(request)
        return redirect('login')

    eventos = Evento.objects.filter(
        estado=Evento.EstadoEvento.PROGRAMADO,
        fecha__gte=date.today(),
    ).order_by('fecha')

    mis_boletos = Boleto.objects.filter(
        miembro_vip=miembro
    ).select_related('evento').order_by('-fecha_compra')

    return render(request, 'vip/portal.html', {
        'miembro':     miembro,
        'eventos':     eventos,
        'mis_boletos': mis_boletos,
    })


@login_required
@user_passes_test(es_miembro_vip)
def vip_solicitar_recarga(request):
    """
    VIP solicita recarga → queda pendiente para que el personal apruebe.
    POST JSON: {"monto": 50.00, "metodo_pago": "QR"}
    """
    if request.method != 'POST':
        return json_error(_('Método no permitido.'), 405)

    try:
        miembro = request.user.miembro_vip
    except MiembroVIP.DoesNotExist:
        return json_error(_('Miembro VIP no encontrado.'), 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    monto_raw = data.get('monto')
    metodo    = data.get('metodo_pago', Recarga.MetodoPago.EFECTIVO)

    try:
        monto = Decimal(str(monto_raw))
        if monto < Decimal('10'):
            return json_error(_('El monto mínimo es 10 BOB.'))
    except Exception:
        return json_error(_('Monto inválido.'))

    # Evitar solicitudes duplicadas pendientes
    if Recarga.objects.filter(miembro=miembro, estado=Recarga.EstadoRecarga.PENDIENTE).exists():
        return json_error(_('Ya tienes una solicitud de recarga pendiente. Espera que sea procesada.'), 409)

    recarga = Recarga.objects.create(
        miembro    = miembro,
        monto      = monto,
        metodo_pago = metodo,
        estado     = Recarga.EstadoRecarga.PENDIENTE,
    )

    return json_ok(id=recarga.pk, estado=recarga.estado)


@login_required
@user_passes_test(es_miembro_vip)
def vip_comprar_boleto(request):
    """
    HU11 (portal VIP) — El miembro compra un boleto descontando de su saldo.
    POST JSON: {"evento_id": 1, "sector": "VIP"}
    """
    if request.method != 'POST':
        return json_error(_('Método no permitido.'), 405)

    try:
        miembro = request.user.miembro_vip
    except MiembroVIP.DoesNotExist:
        return json_error(_('Miembro VIP no encontrado.'), 404)

    try:
        data     = json.loads(request.body)
        evento   = get_object_or_404(Evento, pk=data['evento_id'])
        sector   = data.get('sector', Boleto.SectorAsiento.GENERAL)
        precio   = evento.precio_base
    except (KeyError, json.JSONDecodeError) as exc:
        return json_error(_(f'Datos inválidos: {exc}'))

    try:
        with transaction.atomic():
            evento_lock  = Evento.objects.select_for_update().get(pk=evento.pk)
            miembro_lock = MiembroVIP.objects.select_for_update().get(pk=miembro.pk)

            if evento_lock.agotado:
                return json_error(_('El evento está agotado.'), 409)

            if miembro_lock.saldo < precio:
                return json_error(
                    _(f'Saldo insuficiente ({miembro_lock.saldo} BOB). '
                      f'Precio del boleto: {precio} BOB.'), 402
                )

            miembro_lock.saldo -= precio
            miembro_lock.save(update_fields=['saldo'])

            evento_lock.capacidad_disponible -= 1
            evento_lock.save(update_fields=['capacidad_disponible'])

            boleto = Boleto.objects.create(
                evento             = evento_lock,
                miembro_vip        = miembro_lock,
                sector             = sector,
                precio_pagado      = precio,
                pago_con_saldo_vip = True,
            )

        return json_ok(
            boleto={
                'codigo':         boleto.codigo,
                'evento':         str(evento_lock),
                'equipo_local':   evento_lock.equipo_local,
                'equipo_visitante': evento_lock.equipo_visitante,
                'fecha':          evento_lock.fecha.strftime('%d/%m/%Y'),
                'sector':         boleto.get_sector_display(),
                'precio':         str(boleto.precio_pagado),
                'saldo_restante': str(miembro_lock.saldo),
                'fecha_compra':   boleto.fecha_compra.strftime('%d/%m/%Y %H:%M'),
            }
        )
    except Exception as exc:
        logger.error('Error en compra VIP: %s', exc, exc_info=True)
        return json_error(_('Error al procesar la compra.'), 500)


# ─────────────────────────────────────────────
#  API: DATOS PARA DASHBOARD (AJAX)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def api_stats(request):
    """
    Endpoint JSON para refrescar estadísticas del dashboard sin recargar página.
    GET /api/stats/ → JSON con totales del día.
    ── Integración HTML ──
    Llamar desde JS:
      fetch("{% url 'api_stats' %}").then(r=>r.json()).then(data=>{
        document.getElementById('stat-ventas').textContent = data.boletos_hoy;
        document.getElementById('stat-vips').textContent   = data.vips_activos;
        document.getElementById('stat-ingresos').textContent = data.ingresos_hoy;
      });
    """
    hoy = date.today()
    boletos_hoy = Boleto.objects.filter(fecha_compra__date=hoy)
    return json_ok(
        boletos_hoy     = boletos_hoy.count(),
        ingresos_hoy    = str(boletos_hoy.aggregate(t=Sum('precio_pagado'))['t'] or 0),
        vips_activos    = MiembroVIP.objects.filter(estado='ACTIVO').count(),
        total_partidos  = Evento.objects.exclude(estado='CANCELADO').count(),
        recargas_pendientes = Recarga.objects.filter(estado='PENDIENTE').count(),
    )



class VentaListView(PersonalOAdminRequired, ListView):
    model               = Boleto
    template_name       = 'portal/ventas.html'
    context_object_name = 'boletos'
    paginate_by         = 25

    def get_queryset(self):
        return Boleto.objects.select_related(
            'evento', 'miembro_vip', 'vendido_por'
        ).order_by('-fecha_compra')

    def get_context_data(self, **kwargs):
        from .models import EstadoMiembro
        ctx = super().get_context_data(**kwargs)
        ctx['eventos_disponibles'] = Evento.objects.filter(
            estado=Evento.EstadoEvento.PROGRAMADO,
            fecha__gte=date.today(),
        ).order_by('fecha')
        ctx['miembros_activos'] = MiembroVIP.objects.filter(
            estado=EstadoMiembro.ACTIVO
        ).order_by('nombre_completo')
        ctx['user'] = self.request.user
        return ctx


@login_required
@user_passes_test(es_personal_o_admin)
def factura_ver(request, pk):
    """
    Genera y muestra la factura en HTML para impresión/descarga.
    GET /factura/<id>/ → HTML de factura profesional.
    
    Para PDF, agregar ?formato=pdf y usar reportlab:
      pip install reportlab
    """
    boleto = get_object_or_404(Boleto, pk=pk)
    
    factura = boleto.get_detalles_factura()
    
    # Información de la empresa (Super Champiñones FC)
    empresa = {
        'nombre': 'Super Champiñones FC',
        'nit': '1234567890',  # Reemplazar con NIT real
        'actividad': 'Club Deportivo',
        'direccion': 'La Paz, Bolivia',
        'telefono': '+591 2 XXXXXXX',
    }
    
    context = {
        'factura': factura,
        'empresa': empresa,
        'boleto': boleto,
    }
    
    return render(request, 'portal/factura.html', context)


# ─────────────────────────────────────────────
#  PRUEBA DE MANEJADORES DE ERROR (DEBUG)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(es_personal_o_admin)
def prueba_errores(request):
    """
    Página de prueba para simular diferentes códigos de error.
    Disponible solo en modo DEBUG y para personal/admin.
    """
    return render(request, 'portal/prueba_errores.html')


@login_required
@user_passes_test(es_personal_o_admin)
def test_error(request, codigo):
    """
    Simula diferentes códigos de error para probar los manejadores.
    GET /test-error/400/ → Simula error 400
    GET /test-error/403/ → Simula error 403
    GET /test-error/404/ → Simula error 404
    GET /test-error/500/ → Simula error 500
    GET /test-error/503/ → Simula error 503
    """
    logger.info(f'Simulando error {codigo}')
    
    if codigo == 400:
        # Bad Request
        from django.core.exceptions import SuspiciousOperation
        raise SuspiciousOperation('Simulación: Solicitud Incorrecta')
    
    elif codigo == 403:
        # Forbidden
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('Simulación: Acceso Prohibido')
    
    elif codigo == 404:
        # Not Found
        from django.http import Http404
        raise Http404('Simulación: Página No Encontrada')
    
    elif codigo == 500:
        # Internal Server Error
        raise Exception('Simulación: Error Interno del Servidor')
    
    elif codigo == 503:
        # Service Unavailable
        from django.http import HttpResponse
        return HttpResponse('Service Unavailable', status=503)
    
    else:
        return json_error(f'Código de error no reconocido: {codigo}', 400)
