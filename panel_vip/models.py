from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# TABLA 1: Control de Clientes y Pagos
class PerfilSuscripcion(models.Model):
    ESTADOS = [
        ('PRUEBA', '15 Días Gratis'),
        ('PENDIENTE', 'Esperando Comprobante QR'),
        ('ACTIVO', 'Suscripción Pagada'),
        ('VENCIDO', 'Acceso Bloqueado'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PRUEBA')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_fin_acceso = models.DateTimeField(null=True, blank=True)

    def verificar_acceso(self):
        ahora = timezone.now()
        
        # Si pagó y aún tiene tiempo
        if self.estado == 'ACTIVO' and self.fecha_fin_acceso and self.fecha_fin_acceso > ahora:
            return True
            
        # Si está en su prueba (CAMBIADO A 2 MINUTOS PARA TESTEO)
        if self.estado == 'PRUEBA':
            fin_prueba = self.fecha_registro + timedelta(minutes=2)
            if ahora <= fin_prueba:
                return True
            else:
                self.estado = 'VENCIDO'
                self.save()
                return False
                
        return False

    def __str__(self):
        return f"{self.usuario.username} - {self.estado}"


# TABLA 2: Las señales que manda tu bot (Oro, Nasdaq, etc.)
class SenalTrading(models.Model):
    TIPOS = [
        ('BUY', 'Compra'),
        ('SELL', 'Venta'),
    ]
    
    RESULTADOS = [
        ('EN_CURSO', 'En Curso ⏳'),
        ('GANANCIA', 'Ganancia (TP) ✅'),
        ('PERDIDA', 'Pérdida (SL) ❌'),
        ('BE', 'Break Even 🛡️'),
    ]
    
    activo = models.CharField(max_length=20, help_text="Ej: XAUUSD, US30")
    tipo = models.CharField(max_length=10, choices=TIPOS)
    precio_entrada = models.DecimalField(max_digits=10, decimal_places=5)
    sl = models.DecimalField(max_digits=10, decimal_places=5, verbose_name="Stop Loss")
    tp = models.DecimalField(max_digits=10, decimal_places=5, verbose_name="Take Profit")
    
    riesgo_pips = models.IntegerField(null=True, blank=True, help_text="Pips de SL (Ej: 50)")
    beneficio_pips = models.IntegerField(null=True, blank=True, help_text="Pips de TP (Ej: 150)")
    
    # LA COLUMNA NUEVA PARA EL RESULTADO FINAL:
    resultado = models.CharField(max_length=20, choices=RESULTADOS, default='EN_CURSO')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} {self.activo} - {self.get_resultado_display()}"