from django.contrib import admin
from django.urls import path, include
from champinones import error_handlers

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('champinones.urls')),
]

# Manejadores de errores personalizados
handler400 = error_handlers.error_400
handler403 = error_handlers.error_403
handler404 = error_handlers.error_404
handler500 = error_handlers.error_500
