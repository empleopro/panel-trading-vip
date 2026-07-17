import os
import json
import hashlib
import requests
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SenalTrading, PerfilSuscripcion

# 1. VISTA DEL PANEL
@login_required(login_url='/login/')
def inicio_panel(request):
    perfil, created = PerfilSuscripcion.objects.get_or_create(usuario=request.user)
    if not perfil.verificar_acceso():
        return redirect('pagina_pago')
    senales = SenalTrading.objects.all().order_by('-fecha_creacion')[:10]
    return render(request, 'panel.html', {'senales': senales})

# 2. VISTA DE PAGO
@login_required(login_url='/login/')
def pagina_pago(request):
    perfil, created = PerfilSuscripcion.objects.get_or_create(usuario=request.user)
    return render(request, 'pago.html', {'perfil': perfil})

# 3. VISTA DE LOGIN
def vista_login(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('username')
        contra = request.POST.get('password')
        user = authenticate(request, username=usuario, password=contra)
        if user is not None:
            login(request, user)
            return redirect('inicio_panel')
        else:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login.html', {'error': error})

# 4. VISTA DE REGISTRO
def vista_registro(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('username')
        contra = request.POST.get('password')
        try:
            user = User.objects.create_user(username=usuario, password=contra)
            PerfilSuscripcion.objects.create(usuario=user)
            login(request, user)
            return redirect('inicio_panel')
        except IntegrityError:
            error = 'Usuario ya existe.'
    return render(request, 'registro.html', {'error': error})

# 5. WEBHOOK SEÑALES
@csrf_exempt
def recibir_senal(request):
    if request.method == 'POST':
        try:
            simbolo = request.POST.get('simbolo', 'XAUUSD')
            tipo = request.POST.get('tipo', 'BUY')
            precio = request.POST.get('precio', 0)
            sl = request.POST.get('sl', 0)
            tp = request.POST.get('tp', 0)
            SenalTrading.objects.create(activo=simbolo, tipo=tipo, precio_entrada=precio, sl=sl, tp=tp)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

# 6. WEBHOOK PAGOPAR
@csrf_exempt
def notificacion_pagopar(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            estado = data.get('estado')
            id_pedido = data.get('id_pedido')
            user_id = id_pedido.split('-')[0]
            if estado == 'pagado':
                usuario = User.objects.get(id=user_id)
                perfil = PerfilSuscripcion.objects.get(usuario=usuario)
                perfil.estado = 'ACTIVO'
                perfil.fecha_fin_acceso = timezone.now() + timedelta(days=30)
                perfil.save()
            return JsonResponse({'status': 'ok'})
        except Exception:
            return JsonResponse({'status': 'error'}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

# 7. GENERAR PAGO
@login_required(login_url='/login/')
def generar_pago_pagopar(request):
    public_key = "bbf20284bb1e86aa4cd15bf76251b11a"
    private_key = "6d5adfcf2bc5499b4b756e672a1a4792"
    pedido_id = f"{request.user.id}-{int(timezone.now().timestamp())}"
    monto = 120000
    
    cadena = f"{private_key}{pedido_id}{monto}"
    token_seguridad = hashlib.sha1(cadena.encode('utf-8')).hexdigest()
    
    datos_pedido = {
        "token": token_seguridad,
        "public_key": public_key,
        "monto_total": monto,
        "tipo_pedido": "VENTA-COMERCIO",
        "id_pedido_comercio": pedido_id,
        "comprador": {
            "ruc": "4444444-4",
            "email": "cliente@vip.com",
            "nombre": request.user.username,
            "telefono": "0981000000",
            "documento": "4444444",
            "tipo_documento": "CI",
            "ciudad": "Itaugua"
        },
        "compras_items": [
            {
                "public_key": public_key,
                "nombre_articulo": "Acceso VIP 30 Dias",
                "cantidad": 1,
                "precio_total_articulo": monto,
                "ciudad": "Itaugua",
                "vendedor_direccion": "Itaugua",
                "categoria": "1"
            }
        ]
    }
    
    try:
        response = requests.post("https://api.pagopar.com/api/comercios/1.1/iniciar-transaccion", json=datos_pedido)
        resultado = response.json()
        if resultado.get('respuesta') == True:
            hash_pago = resultado['resultado'][0]['data']
            return redirect(f"https://www.pagopar.com/pagos/{hash_pago}")
        else:
            return JsonResponse({'error': str(resultado)})
    except Exception as e:
        return JsonResponse({'error': str(e)})