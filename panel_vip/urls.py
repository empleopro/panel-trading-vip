from django.urls import path
from . import views

urlpatterns = [
    # 1. Vistas principales del Panel
    path('', views.inicio_panel, name='inicio_panel'),
    path('pago/', views.pagina_pago, name='pagina_pago'), 
    
    # 2. Vistas de Sesión (Para los usuarios que vienen de TikTok)
    path('login/', views.vista_login, name='login'),
    path('registro/', views.vista_registro, name='registro'),
    
    # 3. Webhooks (Las "puertas traseras" automáticas)
    path('webhook/mt5/', views.recibir_senal, name='recibir_senal'),
    path('webhook/pagopar/', views.notificacion_pagopar, name='notificacion_pagopar'),
]