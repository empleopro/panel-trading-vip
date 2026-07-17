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

# 1. VISTA DEL PANEL (Protegida)
@login_required(login_url='/login/')
def inicio_panel(request):
    perfil, created = PerfilSuscripcion.objects.get_or_create(usuario=request.user)
    
    if not perfil.verificar_acceso():
        return redirect('pagina_pago')
        
    senales = SenalTrading.objects.all().order_by('-fecha_creacion')[:10]
    return render(request, 'panel.html', {'senales': senales})

# 2. VISTA DE LA PÁGINA DE PAGO (Protegida)
@login_required(login_url='/login/')
def pagina_pago(request):
    perfil = PerfilSuscripcion.objects.get(usuario=request.user)
    return render(request, 'pago.html', {'perfil': perfil, 'error_pago': None})

# 3. VISTA DE INICIO DE SESIÓN
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
            error = 'Usuario o contraseña incorrectos. Intentá de nuevo.'
            
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
            error = 'Ese nombre de usuario ya está en uso. Elegí otro.'
            
    return render(request, 'registro.html', {'error': error})

# 5. WEBHOOK PARA RECIBIR SEÑALES DEL BOT
@csrf_exempt
def recibir_senal(request):
    if request.method == 'POST':
        try:
            simbolo = request.POST.get('simbolo', 'XAUUSD')
            tipo = request.POST.get('tipo', 'BUY')
            precio = request.POST.get('precio', 0)
            sl = request.POST.get('sl', 0)
            tp = request.POST.get('tp', 0)
            
            SenalTrading.objects.create(
                activo=simbolo,         
                tipo=tipo,              
                precio_entrada=precio,  
                sl=sl,                  
                tp=tp                   
            )
            return JsonResponse({'status': 'ok', 'mensaje': 'Señal guardada'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

# 6. WEBHOOK PARA RECIBIR PAGOS DE PAGOPAR
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
            
            return JsonResponse({'status': 'pendiente'})
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=500)
    return JsonResponse({'status': 'error'}, status=400)

# 7. BOTÓN: GENERAR LINK DE PAGOPAR Y REDIRIGIR
@login_required(login_url='/login/')
def generar_pago_pagopar(request):
    public_key = "bbf20284bb1e86aa4cd15bf76251b11a"
    private_key = "6d5adfcf2bc5499b4b756e672a1a4792"
    
    pedido_id = f"{request.user.id}-{int(timezone.now().timestamp())}"
    monto_str = "120000" 
    
    cadena = f"{private_key}{pedido_id}{monto_str}"
    token_seguridad = hashlib.sha1(cadena.encode('utf-8')).hexdigest()
    
    fecha_maxima = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
    
    datos_pedido = {
        "token": token_seguridad,
        "public_key": public_key,
        "monto_total": 120000,
        "tipo_pedido": "VENTA-COMERCIO",
        "id_pedido_comercio": pedido_id,   
        "fecha_maxima_pago": fecha_maxima, 
        "comprador": {
            "ruc": "", 
            "email": "cliente@vip.com",
            "ciudad": 1,
            "nombre": request.user.username if request.user.username else "Cliente",
            "telefono": "0981000000",
            "direccion": "",
            "documento": "4444444",
            "coordenadas": "",
            "razon_social": request.user.username if request.user.username else "Cliente",
            "tipo_documento": "CI",
            "direccion_referencia": ""
        },
        "compras_items": [   
            {
                "public_key": public_key, # <--- ACÁ ESTÁ EL CAMBIO NUEVO
                "nombre_articulo": "Acceso VIP 30 Dias",
                "cantidad": 1,
                "precio_total_articulo": 120000,
                "vendedor_telefono": "", 
                "vendedor_direccion": "", 
                "vendedor_direccion_referencia": "",
                "vendedor_ruc": "", 
                "proveedor": "Panel VIP", 
                "ciudad": 1, 
                "categoria": 1,
                "peso": 0, 
                "longitud": 0, 
                "ancho": 0, 
                "alto": 0, 
                "url_imagen": ""
            }
        ],
        "descripciones": [
            {
                "monto": 120000, 
                "descripcion": "Suscripcion VIP"
            }
        ]
    }
    
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        respuesta = requests.post("https://api.pagopar.com/api/comercios/1.1/iniciar-transaccion", json=datos_pedido, headers=headers)
        resultado = respuesta.json()
        
        if resultado.get('respuesta') == True:
            hash_pago = resultado['resultado'][0]['data']
            return redirect(f"https://www.pagopar.com/pagos/{hash_pago}")
        else:
            error_real = resultado.get('resultado', 'Error desconocido')
            return render(request, 'pago.html', {'error_pago': f'Pagopar dice: {error_real}'})
            
    except Exception as e:
        return render(request, 'pago.html', {'error_pago': f'Error de conexión: {str(e)}'})