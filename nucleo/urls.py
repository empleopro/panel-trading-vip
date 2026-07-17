from django.contrib import admin
from django.urls import path, include
from panel_vip import views  # Importamos las vistas de tu panel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('panel_vip.urls')),
    path('login/', views.vista_login, name='login'),          # La puerta para usuarios registrados
    path('registro/', views.vista_registro, name='registro'), # La landing page para TikTok
    # --- NUEVA PUERTA SECRETA PARA EL BOT ---
    path('webhook/mt5/', views.recibir_senal, name='recibir_senal'),
]