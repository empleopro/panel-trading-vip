from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_panel, name='inicio_panel'),
    path('pago/', views.pagina_pago, name='pago_qr'),
]