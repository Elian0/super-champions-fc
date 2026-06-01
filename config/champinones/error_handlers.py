"""
error_handlers.py — Manejador centralizado de errores
Proporciona páginas de error profesionales en lugar de pantallas amarillas
"""

import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  ERROR 400 — Solicitud Incorrecta
# ─────────────────────────────────────────────

def error_400(request, exception=None):
    """Maneja errores 400 (Bad Request)"""
    logger.warning('Error 400 - Solicitud incorrecta desde %s', request.META.get('REMOTE_ADDR'))
    
    context = {
        'titulo': '⚠️ Solicitud Incorrecta',
        'codigo': '400',
        'mensaje': 'La solicitud no fue válida. Por favor, verifica los datos e intenta de nuevo.',
        'detalles': 'Parece que hay un problema con tu solicitud.',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Bad Request', 'codigo': 400}, status=400)
    
    return render(request, 'errores/error.html', context, status=400)


# ─────────────────────────────────────────────
#  ERROR 403 — Acceso Prohibido
# ─────────────────────────────────────────────

def error_403(request, exception=None):
    """Maneja errores 403 (Forbidden)"""
    logger.warning('Error 403 - Acceso prohibido para %s desde %s', 
                   request.user.username if request.user.is_authenticated else 'Anónimo',
                   request.META.get('REMOTE_ADDR'))
    
    context = {
        'titulo': '🚫 Acceso Prohibido',
        'codigo': '403',
        'mensaje': 'No tienes permiso para acceder a este recurso.',
        'detalles': 'Si crees que es un error, contacta al administrador.',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Forbidden', 'codigo': 403}, status=403)
    
    return render(request, 'errores/error.html', context, status=403)


# ─────────────────────────────────────────────
#  ERROR 404 — No Encontrado
# ─────────────────────────────────────────────

def error_404(request, exception=None):
    """Maneja errores 404 (Not Found)"""
    logger.info('Error 404 - Recurso no encontrado: %s', request.path)
    
    context = {
        'titulo': '🔍 Página No Encontrada',
        'codigo': '404',
        'mensaje': 'Lo sentimos, la página que buscas no existe.',
        'detalles': f'Ruta: {request.path}',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Not Found', 'codigo': 404}, status=404)
    
    return render(request, 'errores/error.html', context, status=404)


# ─────────────────────────────────────────────
#  ERROR 500 — Error Interno del Servidor
# ─────────────────────────────────────────────

def error_500(request):
    """Maneja errores 500 (Internal Server Error)"""
    logger.error('Error 500 - Error interno del servidor', extra={
        'request_method': request.method,
        'request_path': request.path,
        'user': request.user.username if request.user.is_authenticated else 'Anónimo',
        'ip': request.META.get('REMOTE_ADDR'),
    }, exc_info=True)
    
    context = {
        'titulo': '💥 Error Interno del Servidor',
        'codigo': '500',
        'mensaje': 'Algo salió mal en el servidor. Nuestro equipo ha sido notificado.',
        'detalles': 'Por favor, intenta de nuevo más tarde.',
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': 'Internal Server Error',
            'codigo': 500,
            'mensaje': 'Error interno del servidor'
        }, status=500)
    
    return render(request, 'errores/error.html', context, status=500)


# ─────────────────────────────────────────────
#  ERROR 502 — Bad Gateway
# ─────────────────────────────────────────────

def error_502(request):
    """Maneja errores 502 (Bad Gateway)"""
    logger.error('Error 502 - Bad Gateway')
    
    context = {
        'titulo': '🌐 Error de Puerta de Enlace',
        'codigo': '502',
        'mensaje': 'Hay un problema con la comunicación del servidor.',
        'detalles': 'Por favor, intenta de nuevo en unos minutos.',
    }
    
    return render(request, 'errores/error.html', context, status=502)


# ─────────────────────────────────────────────
#  ERROR 503 — Servicio No Disponible
# ─────────────────────────────────────────────

def error_503(request):
    """Maneja errores 503 (Service Unavailable)"""
    logger.error('Error 503 - Servicio no disponible')
    
    context = {
        'titulo': '🔧 Servicio No Disponible',
        'codigo': '503',
        'mensaje': 'El servidor está en mantenimiento.',
        'detalles': 'Esperamos estar de vuelta pronto. Intenta de nuevo más tarde.',
    }
    
    return render(request, 'errores/error.html', context, status=503)
