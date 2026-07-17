from django.contrib import admin
from .models import PerfilSuscripcion, SenalTrading

class SenalTradingAdmin(admin.ModelAdmin):
    list_display = ('activo', 'tipo', 'precio_entrada', 'riesgo_pips', 'beneficio_pips', 'fecha_creacion')
    list_filter = ('activo', 'tipo')

class PerfilSuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'estado', 'fecha_registro', 'fecha_fin_acceso')
    list_filter = ('estado',)

admin.site.register(PerfilSuscripcion, PerfilSuscripcionAdmin)
admin.site.register(SenalTrading, SenalTradingAdmin)