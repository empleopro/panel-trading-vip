from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_panel, name='inicio_panel'),
    path('pago/', views.pagina_pago, name='pagina_pago'), 
    
    # --- LA RUTA NUEVA DEL BOTÓN ---
    path('checkout-pagopar/', views.generar_pago_pagopar, name='checkout_pagopar'),
    
    path('login/', views.vista_login, name='login'),
    path('registro/', views.vista_registro, name='registro'),
    
    path('webhook/mt5/', views.recibir_senal, name='recibir_senal'),
    path('webhook/pagopar/', views.notificacion_pagopar, name='notificacion_pagopar'),
]